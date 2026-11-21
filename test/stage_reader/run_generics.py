#!/usr/bin/env python3
"""Check the native List specializations and the reader's failure location."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path("test/stage_reader")
TYPES = {"i64": ("i64", 8), "u8": ("u8", 1), "struct": ("Pair", 16)}


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


def check_native(compiler, ir, binary, env, kind, opts):
    fixture = FIXTURES / f"list_{kind}.lang"
    element, size = TYPES[kind]
    name = f"List_{element}"
    subprocess.run([compiler, fixture, "-o", ir], cwd=ROOT, env=env,
                   check=True, timeout=60)

    definitions = re.findall(
        rf"^(define [^\n]*@{name}_push\([^\n]*)\n(.*?)^}}", ir.read_text(), re.M | re.S)
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

    clang = os.environ.get("CLANG", "clang")
    for opt in opts:
        subprocess.run([clang, f"-{opt}", ir, "-o", binary], check=True, timeout=60)
        result = subprocess.run([binary], timeout=10)
        if result.returncode != 42:
            raise SystemExit(f"{name} native -{opt} expected exit 42, got {result.returncode}")
        print(f"{name} native -{opt} answered {result.returncode}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--native", action="store_true")
    modes.add_argument("--bad-instantiation", action="store_true")
    parser.add_argument("--type", choices=TYPES)
    parser.add_argument("--opt", choices=("O0", "O2"))
    args = parser.parse_args()
    if args.native and args.type is None:
        parser.error("--native requires --type")
    if args.bad_instantiation and (args.type is not None or args.opt is not None):
        parser.error("--bad-instantiation does not take --type or --opt")

    compiler = Path(os.environ.get("COMPILER", "out/lang_next")).resolve()
    with tempfile.TemporaryDirectory(prefix="lang-generics-") as directory:
        work = Path(directory)
        ir = work / "list.ll"
        env = dict(os.environ, LANGBE="llvm", LANG_CACHE=str(work / "cache"))
        if args.bad_instantiation:
            check_bad_instantiation(compiler, ir, env)
        else:
            opts = (args.opt,) if args.opt else ("O0", "O2")
            check_native(compiler, ir, work / "list", env, args.type, opts)


if __name__ == "__main__":
    main()
