#!/usr/bin/env python3
"""Replay the language-project fragment from committed sources with receipts."""
import argparse
import json
import os
from pathlib import Path
import resource
import re
import shutil
import sys
import uuid

from route import Replay, ROOT, dump, require, sha


class ProjectReplay(Replay):
    def run(self, command, name, cwd, expected=0):
        try:
            return super().run(command, name, cwd, expected)
        finally:
            if self.rows and self.rows[-1]["name"] == name:
                row = self.rows[-1]
                row["environment"].update({key: self.env[key] for key in ("PATH", "MAKEFLAGS")})
                dump(self.evidence / (Path(row["stdout"]).stem + ".json"), row)
                dump(self.evidence / "stages.json", self.rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['manifest'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    old_limit = resource.getrlimit(resource.RLIMIT_AS)[1]
    if old_limit != resource.RLIM_INFINITY:
        ceiling = min(ceiling, old_limit)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('manifest-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('manifest-' + token)
    scratch.mkdir(parents=True)
    replay = ProjectReplay(evidence, scratch)
    replay.env.update(MAKEFLAGS='-j2', PYTHONDONTWRITEBYTECODE='1')
    print(f'evidence: {evidence}', flush=True)
    try:
        status = replay.run(['git', 'status', '--porcelain', '--untracked-files=all'], 'clean', ROOT)
        require(not status.stdout, 'commit the candidate before replaying it')
        head = replay.run(['git', 'rev-parse', 'HEAD'], 'head', ROOT).stdout.decode().strip()
        clone = scratch / 'repo'
        replay.run(['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(clone)], 'clone', ROOT)
        files = replay.run(['git', 'ls-files', '-z'], 'inputs', clone).stdout.decode().split('\0')
        tools = {}
        for name in ('make', 'clang', 'ld', 'python3', 'git'):
            path = Path(shutil.which(name)).resolve()
            tools[name] = {'path': str(path), 'sha256': sha(path)}
        dump(evidence / 'identity.json', {
            'head': head, 'source_sha256': {p: sha(clone / p) for p in files if p and (clone / p).is_file()},
            'tools': tools, 'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Native Linux x86-64 libc and Clang; entry is a guest source file; suffix equals reader name; no OS kernel operations; no fixed points or browser rebuilds'})
        # Separate invocations prevent init/build races under parallel make.
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        fixtures = clone / 'test/reader_author/fixtures/project'
        shipping = clone / 'example/shipping/project.lang-project'
        for path in (shipping, fixtures / 'relative.lang-project', fixtures / 'inert/project.lang-project'):
            replay.env['PATH'], saved_path = '/nonexistent', replay.env['PATH']
            result = replay.run([compiler, 'project', 'check', str(path)], 'check-inert-' + path.parent.name, scratch)
            replay.env['PATH'] = saved_path
            require(result.stdout.startswith(b'Project inputs ') and not result.stderr, 'check must produce only identity')
            require(not (scratch / 'cache').exists(), 'loading a project executed or compiled a reader')
        diagnostics = {
            'suffix': 'source suffix must match', 'reader': 'must declare the named reader',
            'missing-runtime': 'missing input:', 'version': 'unsupported project schema',
            'duplicate': 'duplicate project field', 'duplicate-runtime': 'duplicate project field',
            'missing-field': 'missing project field: backend', 'unknown': 'unknown project field',
            'backend': 'unsupported project backend', 'profile': 'unsupported native profile',
            'toolchain': 'unsupported native toolchain', 'entry': 'entry suffix must match', 'empty': 'empty input',
        }
        for name, message in diagnostics.items():
            path = fixtures / (name + '.lang-project')
            result = replay.run([compiler, 'project', 'check', str(path)], 'reject-' + name, scratch, expected=1)
            require(message.encode() in result.stderr, name + ': missing diagnostic')
            require(re.search(re.escape(str(path).encode()) + rb':\d+:\d+: error:', result.stderr),
                    name + ': missing manifest location')
        # Same-name projects must be isolated by source identities, not reader name.
        outputs = []
        for name, number in [('alpha', 42), ('beta', 7), ('alpha', 42)]:
            manifest = fixtures / name / 'project.lang-project'
            result = replay.run([compiler, 'project', 'read', str(manifest)], 'same-name-' + name, scratch)
            require(f'(number {number})'.encode() in result.stdout and not result.stderr, 'same-name reader collision')
            outputs.append(result.stdout)
        require(outputs[0] == outputs[2] and outputs[0] != outputs[1], 'reader isolation is not stable')
        # File operands remain data even when their paths need source escaping.
        quoted = scratch / 'quoted "project with spaces'
        shutil.copytree(fixtures / 'alpha', quoted)
        result = replay.run([compiler, 'project', 'read', str(quoted / 'project.lang-project')],
                            'quoted-relative-path', scratch)
        require(result.stdout == outputs[0] and not result.stderr, 'quoted path changed reader input')
        # Dependency changes at the same path must change the immutable identity.
        mutable = scratch / 'mutable'
        shutil.copytree(fixtures / 'alpha', mutable)
        (mutable / 'helper.lang').write_text('func helper() i64 { return 42; }\n')
        (mutable / 'reader.lang').write_text('include "' + str(mutable / 'helper.lang') + '"\n'
            'include "std/ast.lang"\nreader same(text *u8) *u8 { return ast_main_i64(ast_int(helper())); }\n')
        manifest = mutable / 'project.lang-project'
        first = replay.run([compiler, 'project', 'check', str(manifest)], 'dependency-before', scratch)
        (mutable / 'helper.lang').write_text('func helper() i64 { return 7; }\n')
        second = replay.run([compiler, 'project', 'check', str(manifest)], 'dependency-after', scratch)
        require(first.stdout != second.stdout, 'transitive source bytes omitted from identity')
        for p in mutable.iterdir():
            if p.is_file(): shutil.copyfile(p, evidence / ('dependency-' + p.name))
        result = replay.run([compiler, 'project', 'read', str(shipping)], 'shipping-read', scratch)
        legacy = replay.run([compiler, 'read', str(clone / 'example/shipping/shipping.lang'),
            str(clone / 'example/shipping/policy.shipping')], 'reader-only-read', scratch)
        require(result.stdout == legacy.stdout and not result.stderr and not legacy.stderr, 'reader-only CLI changed')
        require(b'(binop >=' in result.stdout and b'(ident total)' in result.stdout, 'shipping shared AST lost')
        (evidence / 'policy.ast').write_bytes(result.stdout)
        ast_file = scratch / 'policy.ast'
        ast_file.write_bytes(result.stdout)
        replay.run([compiler, '--from-ast', str(ast_file), '--ast-source', str(clone / 'example/shipping/policy.shipping'),
            '--runtime', str(clone / 'example/shipping/runtime.lang'), '-o', str(scratch / 'policy.ll')], 'saved-ast', scratch)
        # Exercise the inherited AST shape validator without the full integration suite.
        malformed = scratch / 'malformed.ast'
        malformed.write_text('(program (number 1 extra))\n')
        shutil.copyfile(malformed, evidence / malformed.name)
        replay.run([compiler, '--from-ast', str(malformed), '-o', str(scratch / 'bad.ll')], 'reject-malformed-ast', scratch, expected=1)
        minted = scratch / 'shippingc'
        replay.run([compiler, 'project', 'compiler', str(shipping), '-o', str(minted)], 'project-compiler', scratch)
        replay.env['PATH'], saved_path = '/nonexistent', replay.env['PATH']
        replay.run([str(minted), str(clone / 'example/shipping/policy.shipping'), '-o', str(scratch / 'shipping.ll')],
                   'minted-no-tools', scratch)
        replay.env['PATH'] = saved_path
        replay.run(['clang', str(scratch / 'shipping.ll'), '-o', str(scratch / 'shipping')], 'native-link', scratch)
        for total, expected in [('0', b'10\n'), ('99', b'10\n'), ('100', b'0\n'), ('120', b'0\n')]:
            result = replay.run([str(scratch / 'shipping'), total], 'native-' + total, scratch)
            require(result.stdout == expected and not result.stderr, 'shipping runtime behavior changed')
        replay.env['LANGBE'] = 'wasm'
        result = replay.run([compiler, 'project', 'read', str(shipping)], 'reject-backend-conflict', scratch, expected=1)
        require(b'project execution requires' in result.stderr, 'ambient backend silently overrode manifest')
        replay.env['LANGBE'] = 'llvm'
        legacy_compiler = scratch / 'samec'
        replay.run([compiler, 'compiler', 'same', str(fixtures / 'alpha/reader.lang'), '-o', str(legacy_compiler)],
                   'reader-only-compiler', scratch)
        replay.run([str(legacy_compiler), str(fixtures / 'alpha/answer.same'), '-o', str(scratch / 'same.ll')],
                   'reader-only-compile', scratch)
        dump(evidence / 'artifacts.json', {p.name: sha(p) for p in
            (Path(compiler), minted, scratch / 'shipping.ll', scratch / 'shipping', scratch / 'same.ll')})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows)})
        print('PASS manifest: schema, located errors, inert loading, identities, reader isolation, shipping runtime and legacy CLI')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
