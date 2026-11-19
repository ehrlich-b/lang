#!/usr/bin/env python3
"""Run all staged List checks by default, including sharing through LLVM-to-Wasm."""

import argparse
from collections import Counter
import os
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path("test/stage_reader")
TYPES = {"i64": ("i64", 8), "u8": ("u8", 1), "struct": ("Pair", 16)}
WASM_TRIPLE = "wasm32-unknown-unknown"


def check_bad_instantiation(compiler, ir, env):
    fixture = FIXTURES / "list_bad.lang"
    request = "#instantiate_list{MissingElement}"
    line = (ROOT / fixture).read_text().splitlines().index(request) + 1
    result = subprocess.run([compiler, fixture, "-o", ir], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=60)
    diagnostic = rf"^{re.escape(str(fixture))}:{line}:\d+: .*cannot instantiate List for MissingElement$"
    if result.returncode == 0 or ir.exists() or not re.search(diagnostic, result.stderr, re.M):
        raise SystemExit(f"expected an instantiation error at {fixture}:{line}\n{result.stderr}")
    print(result.stderr, end="")


def check_list_ir(module, kind):
    element, size = TYPES[kind]
    name = f"List_{element}"
    definitions = re.findall(
        rf"^(define [^\n]*@{name}_push\([^\n]*)\n(.*?)^}}", module, re.M | re.S)
    if len(definitions) != 1:
        raise SystemExit(f"expected one {name}_push definition, found {len(definitions)}")
    signature, body = definitions[0]
    if not re.search(r", i64 %item\.arg\)", signature):
        raise SystemExit(f"unexpected push signature: {signature}")
    if not re.search(rf"\bmul i64 [^\n]+, {size}$", body, re.M):
        raise SystemExit(f"expected {name}_push to scale the slot offset by {size} bytes")
    if kind == "u8" and not re.search(r"\bstore i8 ", body):
        raise SystemExit(f"expected {name}_push to store a byte")
    print(f"{signature} stride={size}", flush=True)


def check_shared_symbols(module):
    counts = Counter(re.findall(r"^define [^\n@]*@(List_\w+_push)\(", module, re.M))
    expected = {f"List_{element}_push": 1 for element, _ in TYPES.values()}
    if counts != expected:
        raise SystemExit(f"expected specialization definitions {expected}, found {dict(counts)}")
    for name in expected:
        print(f"{name}: {counts[name]} definition", flush=True)


def check_lists(compiler, work, env, kind, opts, *, wasm=False, symbols=False):
    fixture = FIXTURES / f"list_{kind}.lang"
    target = "LLVM-to-Wasm" if wasm else "native"
    ir = work / f"{fixture.stem}-{target}.ll"
    compiler_env = dict(env, LANGOS="wasm") if wasm else env
    subprocess.run([compiler, fixture, "-o", ir], cwd=ROOT, env=compiler_env,
                   check=True, timeout=60)

    module = ir.read_text()
    if wasm and f'target triple = "{WASM_TRIPLE}"' not in module.splitlines():
        raise SystemExit(f"expected LLVM IR targeting {WASM_TRIPLE}")
    element_kinds = TYPES if kind == "shared" else (kind,)
    for element_kind in element_kinds:
        check_list_ir(module, element_kind)
    if symbols:
        check_shared_symbols(module)

    name = "lang + minilisp Lists" if kind == "shared" else f"List_{TYPES[kind][0]}"
    clang = os.environ.get("CLANG", "clang")
    if wasm:
        binary = ir.with_suffix(".wasm")
        flags = [f"--target={WASM_TRIPLE}", "-nostdlib", "-Wl,--no-entry",
                 "-Wl,--export-all", "-Wl,--allow-undefined"]
        run = ["node", ROOT / "test/wasm_host.js", binary]
    else:
        binary = ir.with_suffix("")
        flags = []
        run = [binary]
    for opt in opts:
        subprocess.run([clang, f"-{opt}", *flags, ir, "-o", binary], check=True, timeout=60)
        result = subprocess.run(run, timeout=10)
        if result.returncode != 42:
            raise SystemExit(f"{name} {target} -{opt} expected exit 42, got {result.returncode}")
        print(f"{name} {target} -{opt} answered {result.returncode}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--native", action="store_true")
    modes.add_argument("--wasm", action="store_true", help="run the shared fixture through LLVM-to-Wasm")
    modes.add_argument("--bad-instantiation", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--type", choices=TYPES)
    selection.add_argument("--shared", action="store_true", help="run the lang and minilisp fixture")
    parser.add_argument("--opt", choices=("O0", "O2"))
    parser.add_argument("--symbols", action="store_true", help="check all shared List definitions")
    args = parser.parse_args()
    run_all = not (args.native or args.wasm or args.bad_instantiation)
    if run_all and (args.type or args.shared or args.opt or args.symbols):
        parser.error("select a mode to use case or optimization options")
    if args.native and args.type is None and not args.shared:
        parser.error("--native requires --type or --shared")
    if args.wasm and not args.shared:
        parser.error("--wasm requires --shared")
    if args.bad_instantiation and (args.type is not None or args.shared or args.opt is not None):
        parser.error("--bad-instantiation does not take --type, --shared or --opt")
    if args.symbols and not args.shared:
        parser.error("--symbols requires --shared")

    compiler = Path(os.environ.get("COMPILER", "out/lang_next")).resolve()
    opts = (args.opt,) if args.opt else ("O0", "O2")
    with tempfile.TemporaryDirectory(prefix="lang-generics-") as directory:
        work = Path(directory)
        env = dict(os.environ, LANGBE="llvm", LANG_CACHE=str(work / "cache"))
        if run_all:
            for kind in TYPES:
                check_lists(compiler, work, env, kind, opts)
            check_lists(compiler, work, env, "shared", opts, symbols=True)
            check_lists(compiler, work, env, "shared", opts, wasm=True, symbols=True)
        elif not args.bad_instantiation:
            kind = "shared" if args.shared else args.type
            check_lists(compiler, work, env, kind, opts, wasm=args.wasm,
                        symbols=args.symbols or args.wasm)
        if run_all or args.bad_instantiation:
            check_bad_instantiation(compiler, work / "bad.ll", env)


if __name__ == "__main__":
    main()
