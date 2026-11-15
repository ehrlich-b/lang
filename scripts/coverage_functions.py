#!/usr/bin/env python3
"""Measure compiler function reach from unoptimized, instrumented emitted IR.

No source maps are needed: emitted symbols retain Lang declaration names.
This measures the compiler, not the programs it compiles. Zero counters mean
unreached by this workload, not proof of dead code. Sizes are LLVM body lines
(excluding blank lines, comments and labels), not native code bytes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    "std/core.lang", "out/version_info.lang", "src/lexer.lang",
    "src/parser.lang", "src/codegen.lang", "src/codegen_llvm.lang",
    "src/codegen_wasm.lang", "src/codegen_c.lang", "src/ast_emit.lang", "src/sexpr_reader.lang",
    "src/compiler_readers_none.lang", "src/main.lang",
]
TOKEN = re.compile(r'''//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[A-Za-z_][A-Za-z_0-9]*|\S''', re.S)


def source_functions(root, sources):
    """Walk only the compiler's input/include closure, ignoring quoted code."""
    seen, functions = set(), {}

    def visit(relative):
        path = (root / relative).resolve()
        relative = path.relative_to(root).as_posix()
        if relative in seen:
            return
        seen.add(relative)
        source = path.read_text()
        tokens = [t for t in TOKEN.finditer(source)
                  if not t.group().startswith(("//", "/*"))]
        for i, token in enumerate(tokens[:-1]):
            word, following = token.group(), tokens[i + 1].group()
            if word == "include" and following.startswith('"'):
                visit(following[1:-1])
            if word == "func" and (i == 0 or tokens[i - 1].group() != "extern"):
                if following in functions:
                    raise ValueError(f"ambiguous source function: {following}")
                functions[following] = {
                    "source": relative,
                    "line": source.count("\n", 0, token.start()) + 1,
                }
    for source in sources:
        visit(source)
    return functions


def ir_functions(ir):
    functions, name, size = {}, None, 0
    for line in ir.splitlines():
        match = re.match(r'^define\b.*@([A-Za-z_][A-Za-z_0-9]*)\(', line)
        if match:
            if name is not None or match[1] in functions:
                raise ValueError("nested or duplicate IR definition")
            name, size = match[1], 0
        elif name is not None:
            body = line.strip()
            if body == "}":
                functions[name], name = size, None
            elif body and not body.startswith(";") and not body.endswith(":"):
                size += 1
    if name is not None or not functions:
        raise ValueError("incomplete or empty IR function inventory")
    return functions


def profile_functions(profile):
    functions, name = {}, None
    for line in profile.splitlines():
        match = re.fullmatch(r'  ([A-Za-z_][A-Za-z_0-9]*):', line)
        if match:
            name = match[1]
        match = re.fullmatch(r'    Block counts: \[([0-9, ]+)\]', line)
        if match:
            if name is None or name in functions:
                raise ValueError("missing or duplicate profile function")
            # IR PGO does not promise entry-first counter ordering. Any positive
            # edge counter establishes reach; summing is NOT a call count.
            functions[name] = any(int(n) > 0 for n in match[1].split(","))
            name = None
    if not functions or name is not None:
        raise ValueError("incomplete or empty IR profile")
    return functions


def summarize(ir, profile, sources):
    sizes, reached = ir_functions(ir), profile_functions(profile)
    if sizes.keys() != reached.keys():
        raise ValueError(f"IR/profile inventory mismatch: missing {sorted(sizes.keys() - reached.keys())}, "
                         f"extra {sorted(reached.keys() - sizes.keys())}")
    missing = sizes.keys() - sources.keys()
    if missing:
        raise ValueError(f"functions without source declarations: {sorted(missing)}")
    per_source, never = {}, []
    for name, size in sizes.items():
        location = sources[name]
        row = per_source.setdefault(location["source"], {"executed": 0, "total": 0})
        row["total"] += 1
        row["executed"] += int(reached[name])
        if not reached[name]:
            never.append(dict(name=name, ir_body_lines=size, **location))
    never.sort(key=lambda f: (-f["ir_body_lines"], f["name"]))
    return {
        "schema": 1,
        "workload": "test/run_llvm_suite.sh",
        "instrumentation": "clang -O0 -fprofile-generate",
        "size_unit": "LLVM body lines excluding blanks, comments and labels",
        "executed": sum(reached.values()),
        "total": len(sizes),
        "per_source": dict(sorted(per_source.items())),
        "never_executed": never,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("out/coverage"))
    parser.add_argument("--log-dir", type=Path, help="defaults to work-dir/logs")
    parser.add_argument("--ir", type=Path, help="use an already verified kernel2.ll instead of running make verify")
    parser.add_argument("--baseline", type=Path, default=Path("test/coverage_baseline.json"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write-baseline", action="store_true")
    mode.add_argument("--check-baseline", action="store_true")
    args = parser.parse_args()
    if socket.gethostname() == "forge":
        raise ValueError("compiler suite must run on a suitable host")
    os.chdir(ROOT)
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    logs = (args.log_dir or work / "logs").resolve()
    logs.mkdir(parents=True, exist_ok=True)
    # A fresh directory prevents stale profiles from inflating reach. Preserve
    # previous measurements rather than cleaning somebody else's artifacts.
    import tempfile
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    # Keep verification and measurement on the same scheduling policy.
    # Both suites retain their existing assertions and execution budgets.
    env = dict(os.environ, JOBS=os.environ.get("JOBS", "2"), SEQUENTIAL="1")

    def run(command, log, run_env=env):
        print("+ " + shlex.join(map(str, command)), flush=True)
        with (logs / log).open("w") as output:
            subprocess.run(list(map(str, command)), env=run_env,
                           stdout=output, stderr=subprocess.STDOUT, check=True)

    if args.ir is None:
        run(["make", "verify"], "verify.log")
    ir_path = (args.ir or Path("out/bootstrap_verify/kernel2.ll")).resolve()
    ir_bytes = ir_path.read_bytes()
    binary = run_dir / "compiler"
    run(["clang", "-O0", "-fprofile-generate", ir_path, "-o", binary], "instrument.log")
    # %p isolates concurrent compiler invocations; %m separates binary images.
    # Reader executables linked by the compiler are not instrumented.
    # An unoptimized compiler must not compete with the neighboring test's
    # two-second JIT budget. Use the suite's existing sequential scheduling;
    # keep every assertion, timeout and skip rule unchanged.
    suite_env = dict(env, SEQUENTIAL="1", COMPILER=str(binary), LANG_CACHE=str(run_dir / "cache"),
                     LLVM_PROFILE_FILE=str(run_dir / "%m-%p.profraw"))
    run(["bash", "test/run_llvm_suite.sh"], "suite.log", suite_env)
    raw = sorted(run_dir.glob("*.profraw"))
    if not raw:
        raise ValueError("suite produced no profiles")
    inputs = run_dir / "profiles.txt"
    inputs.write_text("".join(str(p) + "\n" for p in raw))
    merged = run_dir / "compiler.profdata"
    run(["llvm-profdata", "merge", "--num-threads=2", "--failure-mode=any",
         "--input-files", inputs, "-o", merged], "merge.log")
    run(["llvm-profdata", "show", "--all-functions", "--counts", merged], "profile.txt")
    report = summarize(ir_bytes.decode(), (logs / "profile.txt").read_text(),
                       source_functions(ROOT, SOURCES))
    (logs / "measurement.json").write_text(json.dumps({
        "ir_sha256": hashlib.sha256(ir_bytes).hexdigest(),
        "profiles": len(raw),
        "suite_mode": "sequential",
    }, indent=2) + "\n")
    (logs / "coverage.json").write_text(json.dumps(report, indent=2) + "\n")
    for source, row in report["per_source"].items():
        print(f'{source}: {row["executed"]}/{row["total"]} functions executed')
    print(f'TOTAL: {report["executed"]}/{report["total"]} functions executed; '
          f'{report["total"] - report["executed"]} never executed')
    print("Largest never-executed functions (LLVM body lines):")
    for row in report["never_executed"][:20]:
        print(f'{row["ir_body_lines"]:6} {row["name"]} ({row["source"]}:{row["line"]})')
    if args.write_baseline:
        args.baseline.write_text(json.dumps(report, indent=2) + "\n")
    if args.check_baseline and report != json.loads(args.baseline.read_text()):
        raise ValueError(f"coverage differs from {args.baseline}; inspect the workload before updating")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"coverage: {error}", file=sys.stderr)
        sys.exit(1)
