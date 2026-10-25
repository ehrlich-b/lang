#!/usr/bin/env python3
"""Check independently specified locations for indirect f32 assignment rejections."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/indirect_f32_spans'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, default=ROOT / 'out/bootstrap_verify/kernel2')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    base = args.evidence.resolve()
    if base == ROOT or ROOT in base.parents:
        parser.error('evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='indirect-f32-spans-', dir=base))
    compiler = args.compiler.resolve()
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(out / 'cache'))
    for key in ('LANG_ROOT', 'LANG_LAYOUT_PROFILE'):
        env.pop(key, None)
    report = dict(python_optimized=not __debug__, compiler=str(compiler),
                  compiler_sha256=digest(compiler), inputs={str(p.relative_to(ROOT)): digest(p)
                  for p in [ROOT / 'src/codegen_llvm.lang', Path(__file__).resolve(), *sorted(FIXTURES.iterdir())] if p.is_file()},
                  commands=[], failures=[])
    expected = json.loads((FIXTURES / 'expected.json').read_text())
    for name, case in expected.items():
        source = FIXTURES / name
        module = out / (name + '.ll')
        command = [str(compiler), str(source)]
        diagnostic_source = FIXTURES / case['source'] if case['source'] else source
        if source.suffix == '.ast':
            command += ['--from-ast']
            if case['source'] == 'diagnostic.read':
                command += ['--ast-source', str(diagnostic_source)]
        command += ['-o', str(module)]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60)
        stdout, stderr = out / (name + '.stdout'), out / (name + '.stderr')
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        row = dict(argv=command, cwd=str(ROOT), exit_code=result.returncode,
                   inputs={str(p): digest(p) for p in {compiler, source, diagnostic_source}},
                   stdout=str(stdout), stdout_sha256=digest(stdout),
                   stderr=str(stderr), stderr_sha256=digest(stderr),
                   module=str(module), module_bytes=module.stat().st_size if module.exists() else None,
                   module_sha256=digest(module) if module.exists() else None)
        report['commands'].append(row)
        errors = []
        if result.returncode != 1:
            errors.append(f'exit {result.returncode}, expected 1')
        if module.exists() and module.stat().st_size != 0:
            errors.append('rejection left a nonempty output module')
        text = result.stderr.decode(errors='replace')
        if 'invalid_span' in case:
            if f"(code {case['invalid_span']})" not in text or 'numeric:' in text:
                errors.append('span was not rejected before numeric lowering')
        else:
            location = case['location']
            prefix = f'{diagnostic_source}:{location[0]}:{location[1]}: ' if location else f'{diagnostic_source}: '
            message = prefix + 'error: numeric: ' + case['diagnostic']
            if text.splitlines() != [message]:
                errors.append(f'expected {message!r}, got {text!r}')
        row['expected'] = case
        if errors:
            report['failures'].append(dict(input=name, errors=errors))
        print(f'{name}: {"FAIL" if errors else "PASS"}')
    report['status'] = 'FAIL' if report['failures'] else 'PASS'
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Indirect f32 spans: {report["status"]} ({len(report["commands"])} checks); {out}')
    for failure in report['failures']:
        print(json.dumps(failure), file=sys.stderr)
    return 1 if report['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
