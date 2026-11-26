#!/usr/bin/env python3
"""Measure a minted Tariff compiler and the native program it produces."""

import argparse
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/dsl-compare"
TIMING = re.compile(r"Native phase (\d+) nanoseconds (\d+) exit 0")


def timed(argv, cwd, env, stdout=subprocess.DEVNULL):
    start = time.monotonic()
    with tempfile.TemporaryFile() as stderr:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
        _, status, usage = os.wait4(proc.pid, 0)
        elapsed = time.monotonic() - start
        proc.returncode = os.waitstatus_to_exitcode(status)
        stderr.seek(0)
        diagnostic = stderr.read().decode(errors="replace")
    rss = usage.ru_maxrss / (1048576 if sys.platform == "darwin" else 1024)
    return elapsed, rss, proc.returncode, diagnostic


def generate(path, lines):
    with path.open("w") as out:
        out.write("fn compute(n) {\nlet x = n;\n")
        for _ in range(lines - 4):
            out.write("x = x + 1;\n")
        out.write("return x;\n}\n")


def build(root, work, clang, env, base):
    compiler = root / "out/lang_next"
    source = root / "examples/dsl-compare/lang/tariff.lang"
    if base:
        subprocess.run(["make", "build"], cwd=root, env=env, check=True)
        # The historical example contains its CLI main in the reader source.
        # Mint only its reader implementation so the compiler can supply main.
        implementation, separator, _ = source.read_text().partition("\nfunc main(")
        if not separator:
            raise RuntimeError(f"Cannot locate the base Tariff CLI in {source}")
        reader = work / "base-reader.lang"
        reader.write_text(implementation + "\n")
        frontend = work / "base-frontend"
        ir = work / "base-frontend.ll"
        subprocess.run([compiler, source, "-o", ir], cwd=root, env=env, check=True)
        subprocess.run([clang, "-O2", ir, "-o", frontend], cwd=root, env=env, check=True)
    else:
        reader = source.with_name("reader.lang")
        frontend = None
    minted = work / ("base-tariff" if base else "tariff")
    entry = "tariff_read" if base else "tariff"
    subprocess.run([compiler, "compiler", entry, reader, "-o", minted],
                   cwd=root, env=env, check=True)
    return compiler, minted, frontend


def compile_program(root, work, minted, source, lines, clang, env, base):
    flag = [] if base else ["--trusted-reader"]
    ir = work / "program.ll"
    program = work / "program"
    harness = root / "examples/dsl-compare/harness.c"

    # Compile and link the exact minted output before running any phase probes.
    start = time.monotonic()
    emission = timed([minted, *flag, source, "--emit=llvm", "-o", ir], root, env)
    link = None
    if emission[2] == 0:
        link = timed([clang, "-O2", ir, harness, "-o", program], root, env)
    elapsed = time.monotonic() - start

    status = link[2] if link else emission[2]
    peak = max(emission[1], link[1]) if link else emission[1]
    if status == 0:
        answer = subprocess.check_output([program, "4"], text=True, cwd=root, env=env)
        if answer != f"{lines}\n":
            raise RuntimeError(f"Expected {lines}, got {answer!r}")
        print(f"argument 4 => {answer.strip()}", flush=True)
    return emission, link, (elapsed, peak, status, "")


def probe_reader(root, work, tools, source, env, base, sample):
    compiler, minted, frontend = tools
    emission, link, total = sample
    if base:
        ast = work / "base-program.ast"
        with ast.open("wb") as output:
            front = timed([frontend, source], root, env, output)
        lower = None
        if front[2] == 0:
            lower = timed([compiler, "--from-ast", ast, "--ast-source", source,
                           "-o", work / "base-lowered.ll"], root, env)
    else:
        front = timed([minted, "--trusted-reader", source, "--check-reader"], root, env)
        phases = {int(n): int(ns) / 1e9 for n, ns in TIMING.findall(emission[3])}
        lower = None
        if emission[2] == 0:
            front = (phases[3], *front[1:])
            lower = (phases[4], emission[1], 0, "")
    for label, sample in (("frontend", front), ("backend", lower),
                          ("link", link), ("minted", emission)):
        if sample is not None and sample[2]:
            print(f"{label} exit {sample[2]}: {sample[3].strip()}", flush=True)
    if front[2] or lower is None or lower[2]:
        total = (total[0], total[1], total[2] or 1, total[3])
    return front, lower, link, total


def summarize(label, lines, samples):
    print(f"{label} {lines:,} lines ({len(samples)} runs)", flush=True)
    for index, name in enumerate(("frontend", "backend", "link", "source-to-native")):
        available = [sample[index] for sample in samples if sample[index] is not None]
        if not available:
            print(f"  {name:17} unavailable")
            continue
        seconds = statistics.median(sample[0] for sample in available)
        mib = statistics.median(sample[1] for sample in available)
        status = "pass" if all(sample[2] == 0 for sample in available) else "failed"
        print(f"  {name:17} {seconds:8.3f} s {mib:8.1f} MiB  {status}", flush=True)
    return (
        statistics.median(sample[3][0] for sample in samples),
        statistics.median(sample[3][1] for sample in samples),
        all(sample[3][2] == 0 for sample in samples),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--lines", type=int, nargs="+", default=(100_000, 1_000_000))
    parser.add_argument("--runs", type=int)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--assert-scale", action="store_true")
    args = parser.parse_args()
    if (args.runs is not None and args.runs < 1) or any(n < 4 for n in args.lines):
        parser.error("positive runs and at least four source lines are required")
    if args.assert_scale and (not args.base or 100_000 not in args.lines):
        parser.error("--assert-scale requires a base checkout and the 100,000-line input")
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("LANG_HOST_MAX_", "LANG_PARSER_MAX_"))}
    env.update(TMPDIR=str(work), LANGBE="llvm", LANG_TEST_TIMINGS="1")
    base_env = env | {"LANG_PARSER_MAX_WORK": "10000000"}
    print(subprocess.check_output([args.clang, "--version"], text=True).splitlines()[0])
    print("Peak MiB from wait4. Native backend peak includes the resident frontend AST.")
    if args.base:
        print("Base recognition uses LANG_PARSER_MAX_WORK=10000000; candidate uses defaults.")
    current = build(ROOT, work, args.clang, env, False)
    arms = [(ROOT, current, env, False)]
    if args.base:
        base_root = args.base.resolve()
        base = build(base_root, work, args.clang, base_env, True)
        arms.insert(0, (base_root, base, base_env, True))
        print("Paired source-to-native runs alternate order; phase probes follow each pair.")
    success = True
    for lines in args.lines:
        source = work / f"{lines}.tariff"
        generate(source, lines)
        count = args.runs if args.runs is not None else (5 if lines == 100_000 else 1)
        samples = {False: [], True: []}
        for run in range(count):
            order = arms if run % 2 == 0 else reversed(arms)
            pair = []
            for root, tools, arm_env, is_base in order:
                _, minted, _ = tools
                sample = compile_program(root, work, minted, source, lines, args.clang, arm_env, is_base)
                pair.append((root, tools, arm_env, is_base, sample))
            for root, tools, arm_env, is_base, sample in pair:
                samples[is_base].append(probe_reader(root, work, tools, source, arm_env, is_base, sample))
        reference = summarize("Base", lines, samples[True]) if args.base else None
        result = summarize("Current", lines, samples[False])
        success &= result[2]
        if reference and lines == 100_000 and args.assert_scale:
            ratio_time, ratio_rss = result[0] / reference[0], result[1] / reference[1]
            print(f"Time ratio {ratio_time:.2%}, peak RSS ratio {ratio_rss:.2%}", flush=True)
            success &= (reference[2] and ratio_time <= 0.50 and ratio_rss <= 0.30
                        and result[1] <= 320)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
