#!/usr/bin/env python3
"""Check cache reuse and staged Lists, including sharing through LLVM-to-Wasm."""

import argparse
from collections import Counter
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path("test/stage_reader")
TYPES = {"i64": ("i64", 8), "u8": ("u8", 1), "struct": ("Pair", 16)}
WASM_TRIPLE = "wasm32-unknown-unknown"
CACHE_FIXTURES = ("list_cache.lang", "list_cache_template.lang", "list_cache_types.lang")


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


def check_list_ir(module, kind, *, stride=None):
    element, size = TYPES[kind]
    if stride is not None:
        size = stride
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


def cache_build(compiler, work, env, label, *, runs, compiles, target=None):
    ir = work / f"{label}.ll"
    if target is not None:
        env = dict(env, LANGOS=target)
    start = time.monotonic()
    result = subprocess.run([compiler, CACHE_FIXTURES[0], "-o", ir], cwd=work, env=env,
                            capture_output=True, text=True, timeout=60)
    seconds = time.monotonic() - start
    starts = Counter(line for line in result.stderr.splitlines() if line.startswith("stage-worker-start "))
    expected = Counter({"stage-worker-start reader-run": runs, "stage-worker-start reader-compile": compiles})
    if result.returncode or +starts != +expected:
        raise SystemExit(f"{label}: expected {dict(+expected)}, saw {dict(starts)}\n{result.stderr}")
    print(f"{label}: seconds={seconds:.6f} worker_starts={sum(starts.values())} "
          f"reader_runs={runs} reader_compiles={compiles}", flush=True)
    return ir


def check_cache(compiler, work, env, *, invalidation=False):
    work = work / "specialization"
    work.mkdir()
    for name in CACHE_FIXTURES:
        shutil.copyfile(ROOT / FIXTURES / name, work / name)
    cache = work / "cache"
    env = dict(env, LANG_CACHE=str(cache), LANG_ROOT=str(ROOT), LANG_TRACE_STAGE_WORKERS="1")
    cold = cache_build(compiler, work, env, "cold", runs=2, compiles=1)
    warm = cache_build(compiler, work, env, "warm", runs=0, compiles=0)
    native_ir = cold.read_bytes()
    if warm.read_bytes() != native_ir:
        raise SystemExit("warm LLVM IR differs from cold IR")
    print(f"byte-identical IR sha256={hashlib.sha256(native_ir).hexdigest()}", flush=True)
    check_list_ir(native_ir.decode(), "u8")
    check_list_ir(native_ir.decode(), "struct", stride=8)

    if not invalidation:
        if directory := os.environ.get("GENERICS_EVIDENCE"):
            evidence = Path(directory)
            evidence.mkdir(parents=True, exist_ok=True)
            for artifact in (cold, warm):
                shutil.copyfile(artifact, evidence / f"specialization-{artifact.name}")
        return

    entries = sorted((cache / "specializations").glob("*.ast"))
    if len(entries) != 2:
        raise SystemExit("expected distinct entries for u8 and Pair")
    # Replay with result entries alone, then damage a single entry in the
    # isolated copy. This exercises a cache hit without any stored executable.
    ast_only = work / "ast-only" / "specializations"
    ast_only.mkdir(parents=True)
    for entry in entries:
        shutil.copyfile(entry, ast_only / entry.name)
    ast_env = dict(env, LANG_CACHE=str(ast_only.parent))
    replay = cache_build(compiler, work, ast_env, "result-only", runs=0, compiles=0)
    if replay.read_bytes() != native_ir:
        raise SystemExit("result-only LLVM IR differs from cold IR")
    (ast_only / entries[0].name).write_bytes(b"incomplete")
    recovered = cache_build(compiler, work, ast_env, "corrupt-entry", runs=1, compiles=1)
    if recovered.read_bytes() != native_ir:
        raise SystemExit("recovered LLVM IR differs from cold IR")

    wasm = cache_build(compiler, work, env, "different-target", runs=2, compiles=0, target="wasm")
    check_list_ir(wasm.read_text(), "struct", stride=4)

    dependency = work / CACHE_FIXTURES[2]
    before = dependency.stat()
    declaration = dependency.read_text()
    dependency.write_text(declaration.replace("item *u8;", "item *u8; tag i64;"))
    os.utime(dependency, ns=(before.st_atime_ns, before.st_mtime_ns))
    changed = cache_build(compiler, work, env, "changed-dependency", runs=2, compiles=1)
    check_list_ir(changed.read_text(), "struct", stride=16)

    failure_cache = work / "failed"
    failure_env = dict(env, LANG_CACHE=str(failure_cache))
    check_bad_instantiation(compiler, work / "bad-cold.ll", failure_env)
    check_bad_instantiation(compiler, work / "bad-retry.ll", failure_env)
    if any(failure_cache.rglob("*.ast")):
        raise SystemExit("failed specialization was published")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--native", action="store_true")
    modes.add_argument("--wasm", action="store_true", help="run the shared fixture through LLVM-to-Wasm")
    modes.add_argument("--bad-instantiation", action="store_true")
    modes.add_argument("--cache-invalidation", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--type", choices=TYPES)
    selection.add_argument("--shared", action="store_true", help="run the lang and minilisp fixture")
    parser.add_argument("--opt", choices=("O0", "O2"))
    parser.add_argument("--symbols", action="store_true", help="check all shared List definitions")
    args = parser.parse_args()
    run_all = not (args.native or args.wasm or args.bad_instantiation or args.cache_invalidation)
    if (run_all or args.cache_invalidation) and (args.type or args.shared or args.opt or args.symbols):
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
        if args.cache_invalidation:
            check_cache(compiler, work, env, invalidation=True)
        elif run_all:
            check_cache(compiler, work, env)
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
