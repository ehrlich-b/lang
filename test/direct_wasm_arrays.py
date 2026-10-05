#!/usr/bin/env python3
"""Bounded array parity, rejection and recursive-frame checks with raw receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("test/suite/156_local_array_literal.lang", 42),
    ("test/suite/250_arrays.lang", 150),
    ("test/suite/251_array_literals.lang", 42),
    ("test/suite/252_array_narrow_assignment.lang", 42),
    ("test/direct_wasm_arrays.lang", 42),
    ("test/parser_array_length.lang", 0),
]
BAD_LENGTHS = [
    ("decimal-length", "1.5", "array length must be an integer literal"),
    ("integral-float-length", "15.0", "array length must be an integer literal"),
    ("negative-length", "-1", "array length must be an integer literal"),
    ("symbol-length", "size", "array length must be an integer literal"),
    ("empty-length", "", "array length must be an integer literal"),
    ("overflow-length", "9223372036854775808", "array length exceeds i64 range"),
    ("wraparound-length", "18446744073709551631", "array length exceeds i64 range"),
]
BAD_CASES = [
    ("zero-length", "var a [0]i64;", "length must be between 1 and 8192"),
    ("large-length", "var a [8193]i64;", "length must be between 1 and 8192"),
    ("nested-array", "var a [2][2]i64;", "require scalar or pointer elements"),
    ("long-literal", "var a [1]i64 = [1, 2];", "more elements than its declared length"),
    ("array-copy", "var a [2]i64 = [1]; var b [2]i64 = a;", "initializer must be an array literal"),
    ("array-assignment", "var a [2]i64 = [1]; var b [2]i64 = [2]; a = b;", "whole-array assignment is unsupported"),
    ("float-index", "var a [2]i64 = [1]; return a[0.5];", "index must be an integer"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=os.environ.get("COMPILER", ROOT / "out/lang"))
    parser.add_argument("--browser-compiler", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "out/direct-wasm-arrays")
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "report.json"
    report = {"status": "running", "compiler": str(compiler),
              "compilerSha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
              "receipts": [], "commands": []}

    def command(argv, backend=None):
        env = dict(os.environ)
        if backend:
            env.update(LANGBE=backend, LANGOS="wasm" if backend == "wasm" else
                       ("macos" if sys.platform == "darwin" else "linux"))
        start = time.monotonic()
        result = subprocess.run([str(part) for part in argv], cwd=ROOT,
                                env=env, text=True, capture_output=True, timeout=60)
        report["commands"].append({"argv": [str(part) for part in argv], "backend": backend,
                                   "seconds": time.monotonic() - start,
                                   "exit": result.returncode, "stdout": result.stdout,
                                   "stderr": result.stderr})
        return result

    def compile_to(source, destination, backend):
        result = command([compiler, source, "-o", destination], backend)
        assert result.returncode == 0, result.stderr
        return report["commands"][-1]["seconds"]

    def wasm_run(module, guard=False):
        script = """
const fs = require('fs');
const {runLangProgram} = require(process.argv[1]);
const {checkStackGuard} = require(process.argv[2]);
const bytes = fs.readFileSync(process.argv[3]);
if (!WebAssembly.validate(bytes)) throw new Error('invalid Wasm binary');
const work = process.argv[4] === 'guard' ? checkStackGuard(bytes) :
  runLangProgram(bytes).then(r => ({value:String(r.value), exit:r.exit,
                                  stdout:r.stdout, stderr:r.stderr}));
work.then(r => console.log(JSON.stringify(r)))
  .catch(e => {console.error(e.stack || e); process.exitCode = 1;});
"""
        result = command(["node", "-e", script, ROOT / "web/program_host.js",
                          ROOT / "test/direct_wasm_arrays_browser.js", module,
                          "guard" if guard else "run"])
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    start = time.monotonic()
    try:
        for filename, expected in CASES:
            source = ROOT / filename
            stem = source.stem
            llvm = output / f"{stem}.ll"
            compile_to(source, llvm, "llvm")
            for optimization in ("-O0", "-O2"):
                binary = output / f"{stem}{optimization}"
                linked = command(["clang", optimization, llvm, "-o", binary])
                assert linked.returncode == 0, linked.stderr
                ran = command([binary])
                assert ran.returncode == expected, (filename, optimization, ran.returncode, ran.stderr)
                report["receipts"].append({"case": filename, "backend": optimization,
                                           "value": expected})
            module = output / f"{stem}.wasm"
            elapsed = compile_to(source, module, "wasm")
            ran = wasm_run(module)
            assert int(ran["value"]) == expected and ran["exit"] == expected, (filename, ran)
            report["receipts"].append({"case": filename, "backend": "native-compiler-to-direct-wasm",
                                       "bytes": module.stat().st_size, "compileSeconds": elapsed, **ran})

        for name, body, message in BAD_CASES:
            source = output / f"bad-{name}.lang"
            source.write_text(f"func main() i64 {{ {body} return 42; }}\n")
            module = output / f"bad-{name}.wasm"
            module.write_bytes(b"stale output that must be removed")
            result = command([compiler, source, "-o", module], "wasm")
            assert result.returncode != 0 and message in result.stderr, result.stderr
            assert str(source) + ":1:" in result.stderr, result.stderr
            assert not module.exists(), "failed compile retained stale/partial module"
            report["receipts"].append({"case": name, "rejected": True,
                                       "diagnostic": result.stderr.strip()})

        for name, length, message in BAD_LENGTHS:
            source = output / f"bad-{name}.lang"
            source.write_text(f"func main() i64 {{\n    var a [{length}]i64;\n    return 42;\n}}\n")
            for backend, extension in (("llvm", "ll"), ("wasm", "wasm")):
                destination = output / f"bad-{name}.{extension}"
                destination.unlink(missing_ok=True)
                result = command([compiler, source, "-o", destination], backend)
                assert result.returncode > 0 and message in result.stderr, result.stderr
                assert str(source) + ":2:12:" in result.stderr, result.stderr
                assert not destination.exists(), "invalid extent emitted an artifact"
                report["receipts"].append({"case": name, "backend": backend, "rejected": True,
                                           "diagnostic": result.stderr.strip()})

        # Positive maximum bound: the last omitted literal element is zero.
        maximum = output / "maximum.lang"
        maximum.write_text("func main() i64 { var a [8192]i64 = [42]; return a[0] + a[8191]; }\n")
        maximum_module = output / "maximum.wasm"
        compile_to(maximum, maximum_module, "wasm")
        maximum_result = wasm_run(maximum_module)
        assert maximum_result["value"] == "42", maximum_result
        report["receipts"].append({"case": "maximum-array-bound", **maximum_result,
                                   "bytes": maximum_module.stat().st_size})

        guard = output / "stack-guard.wasm"
        compile_to(ROOT / "test/direct_wasm_array_stack_guard.lang", guard, "wasm")
        report["receipts"].append({"case": "recursive-frame-static-guard", **wasm_run(guard, True)})
        if args.browser_compiler:
            browser = command(["node", ROOT / "test/direct_wasm_arrays_browser.js",
                               args.browser_compiler.resolve()])
            assert browser.returncode == 0, browser.stderr
            report["browser"] = json.loads(browser.stdout)
        report["status"] = "passed"
    except BaseException as error:
        report["status"] = "failed"
        report["failure"] = str(error)
        raise
    finally:
        report["seconds"] = time.monotonic() - start
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"{report['status']}: {len(report['receipts'])} receipts; {report_path}")


if __name__ == "__main__":
    main()
