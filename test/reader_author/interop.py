#!/usr/bin/env python3
"""Prove the shipping/Forth export boundary from committed current sources."""
import argparse
import gzip
import os
from pathlib import Path
import re
import resource
import shutil
import sys
import uuid

from project import ProjectReplay
from route import ROOT, dump, require, sha


def check_direct_ir(text):
    match = re.search(r'define i64 @client_fee\(i64 [^)]*\)[^{]*\{(.*?)\n}', text, re.S)
    require(match is not None, 'missing i64 Forth client definition')
    body = match[1]
    calls = re.findall(r'\bcall\s+([^\n]+)', body)
    require(len(calls) == 1 and re.fullmatch(r'i64 @shipping_cost\(i64 %[^)]+\)', calls[0].strip()),
            'client must call shipping_cost directly with exactly one i64 and no adapter')
    require(re.search(r'define i64 @shipping_cost\(i64 [^)]*\)', text), 'producer signature changed')
    require('inttoptr' not in body and 'ptrtoint' not in body, 'client unexpectedly boxes values')
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['shipping-client'], required=True)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    os.nice(10)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    ceiling = 2 * 1024**3
    hard = resource.getrlimit(resource.RLIMIT_AS)[1]
    if hard != resource.RLIM_INFINITY:
        ceiling = min(ceiling, hard)
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    token = uuid.uuid4().hex
    evidence = (args.evidence or ROOT.parent / 'evidence' / ('shipping-client-' + token)).resolve()
    require(evidence != ROOT and ROOT not in evidence.parents, 'evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=False)
    scratch = ROOT.parent / 'scratch' / ('shipping-client-' + token)
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
            'tools': tools,
            'limits': {'cpus': cpus, 'address_space_bytes': ceiling, 'JOBS': 2, 'MAKEFLAGS': '-j2'},
            'assumptions': 'Linux x86-64 libc/Clang; trusted frontend catalogs; signed whole-unit i64 values; '
                'no OS kernel operations; no fixed points, full suites or web rebuilds'})
        replay.run(['make', 'init'], 'init', clone)
        replay.run(['make', 'build'], 'build-current-sources', clone)
        compiler = str(clone / 'out/lang_next')
        shipping = 'example/shipping/shipping.lang'
        reader = 'example/shipping/client/reader.lang'
        client = 'example/shipping/client/client.shippingforth'
        library = 'example/shipping/client/policy.shippinglib'
        harness = 'example/shipping/client/main.lang'
        fixtures = 'test/reader_author/fixtures/interop/'
        # Retain the two independently produced core fragments, not a synthetic
        # AST assembled by the test runner.
        for source_reader, source, name in [(shipping, library, 'library'), (reader, client, 'client')]:
            result = replay.run([compiler, 'read', source_reader, source], name + '-ast', clone)
            require(not result.stderr, name + ': unexpected reader diagnostic')
            (evidence / (name + '.ast')).write_bytes(result.stdout)
        require(b'(call (ident shipping_cost)' in (evidence / 'client.ast').read_bytes(),
                'Forth must emit a shared core call')
        require(b'(func shipping_cost' in (evidence / 'library.ast').read_bytes() and
                b'(func main' not in (evidence / 'library.ast').read_bytes(), 'library emitted wrong declarations')
        # Existing manifest path uses the same signature-backed definition and
        # retains the standalone shipping entry point.
        result = replay.run([compiler, 'project', 'read', 'example/shipping/project.lang-project'],
                            'original-project-ast', clone)
        require(b'(func main' in result.stdout and b'(func shipping_cost' in result.stdout and not result.stderr,
                'original project reader changed')
        (evidence / 'project.ast').write_bytes(result.stdout)
        answers = []
        for policy, name, cases in [
            (library, 'shipping-client', [('0', 10), ('79', 10), ('80', 10), ('81', 10),
                                        ('99', 10), ('100', 0), ('101', 0), ('120', 0)]),
            (fixtures + 'changed.shippinglib', 'changed-client', [('79', 7), ('80', 0), ('81', 0), ('100', 0)]),
        ]:
            ir = scratch / (name + '.ll')
            binary = scratch / name
            replay.run([compiler, shipping, reader, policy, client, harness, '-o', str(ir)], name + '-llvm', clone)
            body = check_direct_ir(ir.read_text())
            (evidence / (name + '-direct-call.ll')).write_text(body + '\n')
            # Preserve complete IR compactly; the uncompressed link input stays
            # in scratch and its digest is recorded in artifacts.json.
            with gzip.open(evidence / (ir.name + '.gz'), 'wb') as retained:
                retained.write(ir.read_bytes())
            replay.run(['clang', '-O0', str(ir), '-o', str(binary)], name + '-link', clone)
            for total, fee in cases:
                result = replay.run([str(binary), total], name + '-' + total, scratch)
                require(result.stdout == f'{fee}\n'.encode() and not result.stderr,
                        f'{name}({total}): expected exact fee {fee}')
                answers.append({'policy': policy, 'total': total, 'fee': fee})
        # Each refusal goes through native compilation, not just a metadata
        # comparison. A wrong expectation or accidentally accepted export fails
        # this runner; a refused build must not leave a linkable IR artifact.
        negative_cases = [
            ('tagged.taggedparameter', 'parameter representation mismatch'),
            ('tagged.taggedresult', 'result representation mismatch'),
            ('owned.ownedparameter', 'parameter ownership mismatch'),
            ('arity.shippingforth', 'parameter count mismatch'),
            ('missing.shippingforth', 'missing export'),
            ('shadow.shippingforth', 'definition shadows export'),
            ('duplicate.shippingforth', 'duplicate word'),
        ]
        for filename, message in negative_cases:
            output = scratch / (filename + '.ll')
            source = fixtures + filename
            result = replay.run([compiler, shipping, fixtures + 'incompatible.lang', library,
                                 source, harness, '-o', str(output)], 'reject-' + filename.replace('.', '-'), clone, expected=1)
            line, column = {'shadow.shippingforth': (1, 3), 'duplicate.shippingforth': (2, 8)}.get(filename, (1, 8))
            location = f':{line}:{column}:'.encode()
            require(message.encode() in result.stderr and re.search(re.escape(location) + rb'.*' + re.escape(message.encode()), result.stderr),
                    f'{filename}: missing refusal at symbol (line {line}, byte column {column})')
            require(source.encode() in result.stderr, filename + ': missing original source path')
            require(not output.exists(), filename + ': incompatible export emitted native IR')
        # Exercise the very assertion used above in a subprocess. It must fail
        # even under python -O, where ordinary assert statements disappear.
        script = ('from interop import check_direct_ir; '
                  'check_direct_ir("define i64 @client_fee(i64 %x) {\\n ret i64 0\\n}")')
        result = replay.run(['python3', '-B', '-O', '-c', script], 'reject-failed-ir-expectation',
                            clone / 'test/reader_author', expected=1)
        require(b'RuntimeError: client must call shipping_cost directly' in result.stderr,
                'failed IR expectation did not fail the runner')
        for row in replay.rows:
            require(all((evidence / row[key]).is_file() for key in ('stdout', 'stderr')),
                    row['name'] + ': execution receipt points to missing output')
        dump(evidence / 'artifacts.json', {p.name: sha(p) for p in
             [Path(compiler), scratch / 'shipping-client.ll', scratch / 'shipping-client',
              scratch / 'changed-client.ll', scratch / 'changed-client']})
        dump(evidence / 'result.json', {'pass': True, 'head': head, 'observations': len(replay.rows),
             'answers': answers, 'refusals': dict(negative_cases), 'direct_call_checked': True})
        print('PASS shipping-client: shared i64 calls, 80/100 boundaries, changed policy, tagged/ownership refusals and failing expectations')
        return 0
    except Exception as error:
        dump(evidence / 'result.json', {'pass': False, 'error': str(error)})
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
