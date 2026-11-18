#!/usr/bin/env python3
"""Check staged layout against Clang and run target-specialized reader output."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).with_name("types.json")
TARGETS = (
    ("linux", "x86_64-linux-gnu", "x86_64-unknown-linux-gnu"),
    ("macos", "aarch64-apple-darwin", "arm64-apple-macosx"),
    ("wasm", "wasm32-unknown-unknown", "wasm32-unknown-unknown"),
)


def fixtures():
    spec = json.loads(FIXTURE.read_text())
    types = [(name, name) for name, _ in spec["scalars"]]
    types.extend((name, name) for name, _ in spec["structs"])
    types.extend(spec["compound"])
    assert len({name for name, _ in types}) >= 40
    c_decls = [f"typedef {c} {name};" for name, c in spec["scalars"]]
    lang_decls = []
    for name, fields in spec["structs"]:
        c_fields = " ".join(f"{c};" for _, _, c in fields)
        lang_fields = " ".join(f"{field} {lang};" for field, lang, _ in fields)
        c_decls.append(f"typedef struct {name} {{ {c_fields} }} {name};")
        lang_decls.append(f"struct {name} {{ {lang_fields} }}")

    measurements = []
    for index, (lang, c) in enumerate(types):
        measurements.extend((
            (f"size_{index}", f"stage_sizeof(types, {json.dumps(lang)})", f"sizeof({c})"),
            (f"align_{index}", f"stage_alignof(types, {json.dumps(lang)})", f"_Alignof({c})"),
        ))
    for struct, fields in spec["structs"]:
        for field, _, _ in fields:
            measurements.append((
                f"offset_{struct}_{field}",
                f'stage_field_offset(types, "{struct}", "{field}")',
                f"__builtin_offsetof({struct}, {field})",
            ))

    lang = ['include "test/stage_reader/reflection.lang"', 'reader reflect(text *u8) *u8 {',
            f'    var types *u8 = stage_types({json.dumps(" ".join(lang_decls))});',
            '    if streq(text, "bad-field") { stage_field_offset(types, "Node", "missing"); }',
            '    var decls *u8 = ast_vec();',
            '    reflection_constant(decls, "output_target", reflection_target_id());']
    lang.extend(f'    reflection_constant(decls, "{name}", {expr});' for name, expr, _ in measurements)
    lang.extend(('    return ast_program(decls);', '}', '#reflect{probe}',
                 'func main() i64 { return output_target(); }'))
    c = [*c_decls, "const unsigned long long layout[] = {"]
    c.extend(f"    {expr}," for _, _, expr in measurements)
    c.append("};")
    return "\n".join(lang) + "\n", "\n".join(c) + "\n", [name for name, _, _ in measurements], len(types)


def run(argv, env):
    proc = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, f"{argv}\n{proc.stdout}{proc.stderr}"
    return proc.stdout


def reader_values(ir):
    return {name: int(value) for name, value in re.findall(
        r"^define [^\n@]*i64 @(\w+)\(\) [^{]*\{[^}]*?\bret i64 (-?\d+)\s*\}",
        ir, re.MULTILINE)}


def binary_identity(path):
    stat = path.stat()
    return stat.st_ino, stat.st_mtime_ns


def check_layout(compiler):
    lang, c, labels, ntypes = fixtures()
    with tempfile.TemporaryDirectory(prefix="stage-reflection-") as temporary:
        root = Path(temporary)
        source = root / "reflection.lang"
        source.write_text(lang)
        cache = root / "cache"
        worker = cache / "readers/reflect"
        identity = None
        for target_id, (os_name, target, llvm_triple) in enumerate(TARGETS, 1):
            env = dict(os.environ, LANGBE="llvm", LANGOS=os_name, LANG_CACHE=str(cache),
                       LANG_STAGE_FRESH_COMPILER="0", LANG_STAGE_OUTPUT_TARGET="invalid-inherited-target")
            c_file = root / f"{target}.c"
            c_file.write_text(c)
            oracle = run(["clang", f"--target={target}", "-std=c11",
                          "-S", "-emit-llvm", str(c_file), "-o", "-"], env)
            array = re.search(r"^@layout = [^\n]*constant \[\d+ x i64\] \[([^\n]+)\]", oracle, re.MULTILINE)
            assert array, oracle
            expected = [int(value) for value in re.findall(r"i64 (\d+)", array.group(1))]
            assert len(expected) == len(labels)
            output = root / f"{target}.ll"
            run([str(compiler), str(source), "-o", str(output)], env)
            ir = output.read_text()
            assert f'target triple = "{llvm_triple}"' in ir
            values = reader_values(ir)
            assert values.pop("output_target", None) == target_id, (target, "reader target identity")
            values = {name: value for name, value in values.items()
                      if name.startswith(("size_", "align_", "offset_"))}
            assert set(values) == set(labels), (target, set(labels) - set(values), set(values) - set(labels))
            for name, value in zip(labels, expected):
                assert values[name] == value, f"{target} {name}: reader={values[name]}, Clang={value}"
            if identity is None:
                identity = binary_identity(worker)
            assert binary_identity(worker) == identity, "reader was rebuilt for a different output target"
            print(f"PASS {target}: {ntypes} types, {len(labels)} measurements, target triple, arch and OS")

        # The direct backend must select Wasm even if LANGOS says Linux.
        direct = dict(env, LANGBE="wasm", LANGOS="linux")
        output = root / "direct.wasm"
        run([str(compiler), str(source), "-o", str(output)], direct)
        runtime = ("const bytes = require('node:fs').readFileSync(process.argv[1]);"
                   "const module = new WebAssembly.Module(bytes);"
                   "console.log(String(new WebAssembly.Instance(module).exports.main()));")
        assert run(["node", "-e", runtime, str(output)], direct).strip() == "3"
        assert binary_identity(worker) == identity
        print("PASS direct Wasm output selection and target-independent native reader cache")

        framed = dict(env, LANG_CACHE=str(root / "framed-cache"),
                      LANG_STAGE_FRESH_COMPILER="1", LANG_STAGE_CONTROLLED_FIXTURES="1")
        output = root / "framed.ll"
        run([str(compiler), str(source), "-o", str(output)], framed)
        assert reader_values(output.read_text()) == reader_values(ir)
        print("PASS a cold framed native reader returns the same Wasm32 measurements")

        source.write_text(lang.replace("#reflect{probe}", "#reflect{bad-field}"))
        rejected = root / "bad.ll"
        proc = subprocess.run([str(compiler), str(source), "-o", str(rejected)], cwd=ROOT,
                              env=env, capture_output=True, text=True, timeout=60)
        assert proc.returncode != 0 and "stage-error: field" in proc.stderr, proc.stderr
        assert not rejected.exists()
        print("PASS unknown fields fail before output is published")


def check_native_wasm(compiler):
    source = Path(__file__).with_name("native_wasm.lang").resolve()
    native_target = TARGETS[1 if sys.platform == "darwin" else 0]
    with tempfile.TemporaryDirectory(prefix="stage-reflection-e2e-") as temporary:
        root = Path(temporary)
        env = dict(os.environ, LANGBE="llvm", LANG_CACHE=str(root / "cache"),
                   LANG_STAGE_FRESH_COMPILER="0")
        for (os_name, target, llvm_triple), bits in ((native_target, 64), (TARGETS[2], 32)):
            ir_path = root / f"{target}.ll"
            run([str(compiler), str(source), "-o", str(ir_path)], dict(env, LANGOS=os_name))
            ir = ir_path.read_text()
            assert f'target triple = "{llvm_triple}"' in ir
            reader_ir = re.search(r"^define [^\n@]*i64 @read_answer\([^\n]*\) [^{]*\{([^}]+)\}",
                                  ir, re.MULTILINE)
            assert reader_ir, f"{target}: missing reader-generated read_answer"
            # Inspect the generated function so target header differences alone
            # cannot satisfy the check. Follow the address to exclude spills.
            body = reader_ir.group(1)
            address = re.search(rf"^ *(%\w+) = getelementptr i{bits}, .* i64 0$", body, re.MULTILINE)
            assert address, f"{target}: expected an i{bits} word address\n{body}"
            load = re.search(rf"^ *%\w+ = load i{bits}, i{bits}\* {address[1]}(?:,.*)?$", body, re.MULTILINE)
            assert load, f"{target}: expected an i{bits} word load\n{body}"

            binary = root / ("answer.wasm" if os_name == "wasm" else "answer")
            flags = []
            command = [str(binary)]
            if os_name == "wasm":
                flags = [f"--target={target}", "-nostdlib", "-Wl,--no-entry", "-Wl,--export=main"]
                command = ["node", "test/wasm_host.js", str(binary)]
            run(["clang", *flags, str(ir_path), "-o", str(binary)], env)
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
            assert result.returncode == 42, f"{target}: exit {result.returncode}\n{result.stdout}{result.stderr}"
            runtime = "Node" if os_name == "wasm" else "native"
            print(f"PASS {target}: {load[0].strip()} ({runtime} answer 42)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("all", "layout", "native-wasm"), default="all")
    args = parser.parse_args()
    compiler = Path(os.environ.get("COMPILER", ROOT / "out/lang_next")).absolute()
    if args.case in ("all", "layout"):
        check_layout(compiler)
    if args.case in ("all", "native-wasm"):
        check_native_wasm(compiler)


if __name__ == "__main__":
    main()
