#!/usr/bin/env python3
"""Bounded scalar parity and printing regressions with real native/Wasm ABIs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMPILER = Path(os.environ.get("COMPILER", ROOT / "out/lang")).resolve()


def command(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True,
                          timeout=30, **kwargs)


def compile_to(source, output, backend, target_os=None):
    result = command([str(COMPILER), str(source), "-o", str(output)],
                     env={**os.environ, "LANGBE": backend,
                          "LANGOS": target_os or ("wasm" if backend == "wasm" else
                          ("macos" if sys.platform == "darwin" else "linux"))})
    assert result.returncode == 0, result.stderr


def wasm_run(path):
    script = """
const fs = require('fs');
const {runLangProgram} = require(process.argv[1]);
runLangProgram(fs.readFileSync(process.argv[2])).then(r => {
    console.log(JSON.stringify({value:String(r.value), exit:r.exit,
                              stdout:r.stdout, stderr:r.stderr}));
}).catch(e => {console.error(e); process.exit(1);});
"""
    result = command(["node", "-e", script, str(ROOT / "web/program_host.js"), str(path)])
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def main():
    receipts = []
    with tempfile.TemporaryDirectory(prefix="lang-direct-numeric-") as temp:
        work = Path(temp)
        shared = ROOT / "test/suite/290_float_wasm_parity.lang"
        boundaries = ROOT / "test/suite/291_float_width_boundaries.lang"
        fixtures = [ROOT / f"test/direct_wasm_numeric_{name}.lang"
                    for name in ("globals", "memory", "shortcircuit", "remainder", "pointer_arithmetic")]
        for source in [shared, boundaries, *fixtures]:
            native_ir = work / f"{source.stem}.ll"
            compile_to(source, native_ir, "llvm")
            for optimization in ("-O0", "-O2"):
                executable = work / f"{source.stem}{optimization}"
                linked = command(["clang", optimization, str(native_ir), "-o", str(executable)])
                assert linked.returncode == 0, linked.stderr
                ran = command([str(executable)])
                assert ran.returncode == 100, (source, optimization, ran.returncode, ran.stderr)
                receipts.append({"case": source.name, "backend": optimization, "value": 100})

        # Expression readers are expanded by the native compiler. Test their
        # actual f32/f64 AST types independently of the direct backend slice.
        for filename in ("287_reader_float_ast.lang", "292_reader_numeric_widths.lang"):
            source = ROOT / "test/suite" / filename
            native_ir = work / f"{source.stem}.ll"
            compile_to(source, native_ir, "llvm")
            for optimization in ("-O0", "-O2"):
                executable = work / f"{source.stem}{optimization}"
                linked = command(["clang", optimization, str(native_ir), "-o", str(executable)])
                assert linked.returncode == 0, linked.stderr
                ran = command([str(executable)])
                assert ran.returncode == 100, (source, optimization, ran.returncode, ran.stderr)
                receipts.append({"case": source.name, "backend": optimization, "value": 100})

        cases = [(shared, 100), (boundaries, 100),
                 (ROOT / "test/suite/260_float_basic.lang", 215),
                 (ROOT / "test/suite/261_float_composed.lang", 100),
                 (ROOT / "test/suite/265_cast_basic.lang", 180)]
        cases += [(source, 100) for source in fixtures]
        for source, expected in cases:
            module = work / f"{source.stem}.wasm"
            compile_to(source, module, "wasm")
            ran = wasm_run(module)
            assert ran["exit"] == (expected & 255) and int(ran["value"]) == expected, (source, ran)
            receipts.append({"case": source.name, "backend": "direct-wasm",
                             "bytes": module.stat().st_size, **ran})

        mixed_output = "mixed 37 -0.30000000000000004 0.30000001192092896\n"
        printing_cases = [
            (ROOT / "test/direct_wasm_numeric_printing.lang", "-12345\n0\n9223372036854775807\n"),
            (ROOT / "test/direct_wasm_numeric_printf.lang", mixed_output),
            (ROOT / "test/native_variadic_printf.lang", "plain\n" + mixed_output),
        ]
        for source, expected_stdout in printing_cases:
            native_ir = work / f"{source.stem}.ll"
            compile_to(source, native_ir, "llvm")
            for optimization in ("-O0", "-O2"):
                executable = work / f"{source.stem}{optimization}"
                linked = command(["clang", optimization, str(native_ir), "-lm", "-o", str(executable)])
                assert linked.returncode == 0, linked.stderr
                ran = command([str(executable)])
                assert ran.returncode == 42 and ran.stdout == expected_stdout, (source, ran)
                receipts.append({"case": source.name, "backend": optimization,
                                 "value": 42, "stdout": ran.stdout})
            if source.name != "native_variadic_printf.lang":
                module = work / f"{source.stem}.wasm"
                compile_to(source, module, "wasm")
                ran = wasm_run(module)
                assert ran["value"] == "42" and ran["stdout"] == expected_stdout, (source, ran)
                receipts.append({"case": source.name, "backend": "direct-wasm", **ran})

        # This mixed signature also exercises LLVM's real wasm32 vararg buffer:
        # pointers/words occupy 8-byte Lang slots and binary32 is promoted first.
        wasm_clang = os.environ.get("WASM_CLANG")
        if not wasm_clang:
            for path in ("/opt/homebrew/opt/llvm/bin/clang", "/usr/local/opt/llvm/bin/clang"):
                if Path(path).is_file():
                    wasm_clang = path
                    break
        wasm_clang = wasm_clang or shutil.which("clang")
        source = ROOT / "test/direct_wasm_numeric_printf.lang"
        llvm_wasm_ir = work / "mixed-llvm-wasm.ll"
        compile_to(source, llvm_wasm_ir, "llvm", target_os="wasm")
        llvm_wasm_module = work / "mixed-llvm.wasm"
        linked = command([wasm_clang, "--target=wasm32-unknown-unknown", "-nostdlib",
                          "-Wl,--no-entry", "-Wl,--export-all", "-Wl,--allow-undefined",
                          str(llvm_wasm_ir), "-o", str(llvm_wasm_module)])
        assert linked.returncode == 0, linked.stderr
        ran = command(["node", str(ROOT / "test/wasm_host.js"), str(llvm_wasm_module)])
        assert ran.returncode == 42 and ran.stdout == mixed_output, ran
        receipts.append({"case": source.name, "backend": "llvm-wasm",
                         "value": 42, "stdout": ran.stdout})

        printed_source = work / "printed.lang"
        printed_source.write_text('''include "std/core.lang"
func echo(value f64) f64 { return -value; }
func main() i64 {
    printf("%.17g\\n", echo(0.30000000000000004));
    printf("%.17g\\n", -0.0);
    return 42;
}
''')
        printed_module = work / "printed.wasm"
        compile_to(printed_source, printed_module, "wasm")
        printed = wasm_run(printed_module)
        assert printed["value"] == "42", printed
        assert printed["stdout"] == "-0.30000000000000004\n-0\n", printed
        receipts.append({"case": "typed-printf-17g", **printed})

        bad_cases = [
            ("bitcast-width", "return bitcast(f32, 1.0);", "equal-width scalar types"),
            ("float-bitwise", "return 1.0 & 2.0;", "unsupported floating operator"),
            ("pointer-float", "var p *u8 = nil; return p + 0.25;", "pointer with a floating operand"),
            ("local-capacity", " ".join(
                "{ " + " ".join(f"var local{i} i64;" for i in range(start, min(start + 512, 1025))) + " }"
                for start in range(0, 1025, 512)) +
             " return 0;", "local limit exceeded"),
            ("string-capacity", " ".join(
                "{ " + " ".join(f'"unique-string-{i}";' for i in range(start, min(start + 1000, 6001))) + " }"
                for start in range(0, 6001, 1000)) +
             " return 0;", "string limit exceeded"),
            ("void-value", "var invalid i64 = no_value(); return invalid;", "void expression cannot be used as a value"),
            ("void-operand", "return 1 + (no_value());", "void expression cannot be used as a value"),
        ]
        for name, body, message in bad_cases:
            source = work / f"bad-{name}.lang"
            source.write_text(f"func main() i64 {{ {body} }} func no_value() void {{ }}\n")
            module = work / f"bad-{name}.wasm"
            rejected = command([str(COMPILER), str(source), "-o", str(module)],
                               env={**os.environ, "LANGBE": "wasm", "LANGOS": "wasm"})
            assert rejected.returncode != 0 and message in rejected.stderr, rejected.stderr
            assert str(source) + ":1:" in rejected.stderr, rejected.stderr
            assert not module.exists(), "failed compile left a partial module"
            receipts.append({"case": name, "rejected": True})

        for name, expression, diagnostic in (
            ("pointer-difference", "p - q", "pointer difference"),
            ("pointer-addition", "p + q", "cannot add two pointers"),
            ("integer-minus-pointer", "1 - p", "cannot subtract a pointer from an integer"),
        ):
            source = work / f"bad-{name}.lang"
            source.write_text(f"func main() i64 {{ var p *f32 = nil; var q *f32 = nil; return {expression}; }}\n")
            for backend, suffix in (("llvm", ".ll"), ("wasm", ".wasm")):
                output = work / f"bad-{name}{suffix}"
                rejected = command([str(COMPILER), str(source), "-o", str(output)],
                                   env={**os.environ, "LANGBE": backend,
                                        "LANGOS": "wasm" if backend == "wasm" else
                                        ("macos" if sys.platform == "darwin" else "linux")})
                assert rejected.returncode != 0 and diagnostic in rejected.stderr, rejected.stderr
                assert str(source) + ":1:" in rejected.stderr, rejected.stderr
                assert not output.exists(), "failed compile left partial output"
                receipts.append({"case": name, "backend": backend, "rejected": True})

        native_bad_calls = [
            ("printf", "extern func printf(fmt *u8, val f64) i64;", "printf()", "requires at least 1 argument"),
            ("open", "extern func open(path *u8, flags i64, mode i64) i64;", 'open("/dev/null")', "requires at least 2 arguments"),
            ("syscall", "", "syscall()", "requires at least 1 argument"),
            ("ordinary-printf", "func printf(value i64) i64 { return value; }", "printf(1, 2)", "takes 1 argument, called with 2"),
        ]
        for name, declaration, call, diagnostic in native_bad_calls:
            source = work / f"bad-native-{name}.lang"
            source.write_text(f"{declaration} func main() i64 {{ return {call}; }}\n")
            output = work / f"bad-native-{name}.ll"
            rejected = command([str(COMPILER), str(source), "-o", str(output)],
                               env={**os.environ, "LANGBE": "llvm",
                                    "LANGOS": "macos" if sys.platform == "darwin" else "linux"})
            assert rejected.returncode != 0 and diagnostic in rejected.stderr, rejected.stderr
            assert str(source) + ":1:" in rejected.stderr, rejected.stderr
            assert not output.exists(), "failed compile left partial LLVM IR"
            receipts.append({"case": f"native-{name}-arity", "rejected": True})

        pointer_global = work / "bad-pointer-global-address.lang"
        pointer_global.write_text("var pointer *u8 = nil; func main() i64 { var slot **u8 = &pointer; return 0; }\n")
        pointer_global_ir = work / "bad-pointer-global-address.ll"
        rejected = command([str(COMPILER), str(pointer_global), "-o", str(pointer_global_ir)],
                           env={**os.environ, "LANGBE": "llvm", "LANGOS": "wasm"})
        assert rejected.returncode != 0 and "LLVM-Wasm pointer global address is unsupported" in rejected.stderr, rejected.stderr
        assert str(pointer_global) + ":1:" in rejected.stderr, rejected.stderr
        assert not pointer_global_ir.exists(), "failed compile left partial LLVM IR"
        receipts.append({"case": "llvm-wasm-pointer-global-address", "rejected": True})

    print(json.dumps({"passed": len(receipts), "receipts": receipts}, indent=2))


if __name__ == "__main__":
    main()
