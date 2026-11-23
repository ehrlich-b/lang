#!/usr/bin/env python3
"""Preprocess a C translation unit, run the Lang reader, then link its LLVM IR."""

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import difflib
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MARKER = re.compile(rb'# (\d+) ("(?:[^"\\]|\\.)*")(?: [0-9 ]+)?\s*$')
READER_SPAN = re.compile(r"^(.+?):(\d+):(\d+): (.*?)(?: @\d+:\d+)?$")
HOST_SPAN = re.compile(r"^(.+?):(\d+):(\d+): (?:fatal error: |error: )?(.*)$")
BUDGET_OFFSET = re.compile(r"parser rule .+ grammar @\d+ source (.+) @(\d+)$", re.MULTILINE)
BAD_PROCESS = re.compile(
    r"segmentation fault|stack dump|(?:LLVM|compiler) error:|broken module|"
    r"invalid llvm ir|instruction does not dominate|assertion .* failed|core dumped",
    re.IGNORECASE,
)
TIMEOUT = 10


@dataclass
class Rejection(Exception):
    phase: str
    diagnostic: str
    crash: bool = False
    unexpected: bool = False


def error(path, line, column, message):
    try:
        text = Path(path).read_bytes().split(b"\n")[line - 1]
    except (OSError, IndexError):
        text = b""
    column = max(1, min(column, len(text) + 1))
    padding = "".join("\t" if c == 9 else " " for c in text[:column - 1])
    return (f"{path}:{line}:{column}: {message}\n"
            f"{os.fsdecode(text)}\n{padding}^")


def run(command, directory, timeout=TIMEOUT):
    return subprocess.run(command, cwd=directory, capture_output=True, timeout=timeout)


def preprocess(source, driver, directory):
    result = run(
        [driver, "-E", "-std=gnu11", "-nostdinc", "-isystem", HERE / "include", source],
        directory,
    )
    if result.returncode:
        stderr = os.fsdecode(result.stderr)
        for row in stderr.splitlines():
            match = HOST_SPAN.fullmatch(row)
            if match:
                file, line, column, message = match.groups()
                raise Rejection("preprocess", error(file, int(line), int(column), message))
        raise Rejection("preprocess", error(source, 1, 1, stderr.strip()),
                        result.returncode < 0, True)

    mapping = []
    output = []
    file, number = str(source), 1
    for row in result.stdout.split(b"\n"):
        match = MARKER.fullmatch(row)
        if match:
            number = int(match[1])
            file = ast.literal_eval(os.fsdecode(match[2]))
        else:
            output.append(row)
            mapping.append((file, number, row))
            number += 1
    return b"\n".join(output), mapping


def map_diagnostic(source, mapping, line, column, message):
    if not 1 <= line <= len(mapping):
        return error(source, 1, 1, message)
    file, number, expanded = mapping[line - 1]
    try:
        original = Path(file).read_bytes().split(b"\n")[number - 1]
    except (OSError, IndexError):
        return error(source, 1, 1, f"{file}:{number}: {message}")
    if original != expanded:
        matcher = difflib.SequenceMatcher(None, original, expanded, autojunk=False)
        for op, left, _, start, end in matcher.get_opcodes():
            if start <= column - 1 < end:
                column = left + 1 + (column - 1 - start if op == "equal" else 0)
                break
    return error(file, number, column, message)


def compile_c(args, source, directory, output):
    guest = directory / "translation.c"
    ir = directory / "translation.ll"
    try:
        text, mapping = preprocess(source, args.clang, directory)
        if b"\x00" in text:
            raise Rejection("reader", error(source, 1, 1, "NUL byte in input"))
        guest.write_bytes(text)
        result = run([args.reader, guest, "--emit=llvm", "-o", ir], directory)
        if result.returncode:
            stderr = os.fsdecode(result.stderr)
            crash = result.returncode < 0 or bool(BAD_PROCESS.search(stderr))
            for row in stderr.splitlines():
                match = READER_SPAN.fullmatch(row)
                if match and match[1] in (str(guest), "c"):
                    _, line, column, message = match.groups()
                    raise Rejection("reader", map_diagnostic(source, mapping, int(line), int(column), message),
                                    crash)
            budget = BUDGET_OFFSET.search(stderr)
            if budget and budget[1] == str(guest):
                before = text[:int(budget[2])]
                line = before.count(b"\n") + 1
                column = len(before.rsplit(b"\n", 1)[-1]) + 1
                raise Rejection("reader", map_diagnostic(source, mapping, line, column,
                                                         "parser recognition budget exceeded"),
                                crash)
            raise Rejection("reader", error(source, 1, 1, stderr.strip() or "reader failed"),
                            crash, True)
        result = run([args.clang, "-Wno-override-module", ir, args.runtime, "-o", output], directory)
        if result.returncode:
            stderr = os.fsdecode(result.stderr)
            crash = result.returncode < 0 or bool(BAD_PROCESS.search(stderr))
            message = stderr.strip()
            raise Rejection("link", error(source, 1, 1, message), crash, True)
    except subprocess.TimeoutExpired as exc:
        raise Rejection("timeout", error(source, 1, 1, f"{Path(exc.cmd[0]).name} timed out"),
                        unexpected=True) from exc


def check(args, source, expected):
    with tempfile.TemporaryDirectory(dir=args.work) as temporary:
        directory = Path(temporary)
        output = directory / "program"
        try:
            compile_c(args, source, directory, output)
            if expected is None:
                raise Rejection("fixture", error(source, 1, 1, "rejected fixture compiled"),
                                unexpected=True)
            result = run([output], directory, timeout=3)
            if result.returncode or result.stdout != expected:
                message = (f"native program exited {result.returncode}" if result.returncode else
                           f"stdout mismatch: expected {expected[:120]!r}, got {result.stdout[:120]!r}")
                raise Rejection("execute", error(source, 1, 1, message), result.returncode < 0,
                                True)
            return None
        except subprocess.TimeoutExpired:
            return Rejection("timeout", error(source, 1, 1, "native program timed out"),
                             unexpected=True)
        except Rejection as rejection:
            return rejection


def corpus(args, tests):
    crashes = unexpected = passed = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = pool.map(lambda row: check(args, *row), tests)
        for (source, expected), result in zip(tests, results):
            if result is None:
                passed += 1
                print(f"PASS {source.name}")
            else:
                crashes += result.crash
                missing_span = not any(line.strip() == "^" for line in result.diagnostic.splitlines())
                unsuccessful_fixture = expected is not None and args.mode == "fixtures"
                unexpected += bool(result.unexpected or missing_span or unsuccessful_fixture)
                label = "REJECT" if not result.unexpected else "FAIL"
                print(f"{label} {source.name} [{result.phase}]\n{result.diagnostic}")
    print(f"Score {passed}/{len(tests)}, crashes {crashes}, unexpected failures {unexpected}")
    return int(crashes != 0 or unexpected != 0 or passed < args.minimum)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader", type=lambda p: Path(p).resolve(), default=ROOT / "out/c-reader")
    parser.add_argument("--runtime", type=lambda p: Path(p).resolve(), default=ROOT / "out/c-runtime.o")
    parser.add_argument("--clang", default=os.environ.get("CLANG", "clang"))
    parser.add_argument("--work", type=lambda p: Path(p).resolve(), default=ROOT / "out/c-work")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("source", type=Path)
    build.add_argument("-o", "--output", type=Path, required=True)
    score = subparsers.add_parser("score")
    score.add_argument("suite", type=Path)
    score.add_argument("--jobs", type=int, default=2)
    score.add_argument("--minimum", type=int, default=120)
    fixtures = subparsers.add_parser("fixtures")
    fixtures.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("LANG_CACHE", str(args.work / "cache"))
    os.environ.setdefault("TMPDIR", str(args.work))
    if args.mode == "build":
        with tempfile.TemporaryDirectory(dir=args.work) as temporary:
            directory = Path(temporary)
            try:
                staged = directory / "program"
                compile_c(args, args.source.resolve(), directory, staged)
                args.output.write_bytes(staged.read_bytes())
                args.output.chmod(0o755)
            except Rejection as rejection:
                print(rejection.diagnostic, file=sys.stderr)
                return 1
        return 0
    if args.mode == "score":
        inputs = sorted((args.suite.resolve() / "tests/single-exec").glob("*.c"))
        if len(inputs) != 220:
            parser.error(f"expected 220 single-exec sources, found {len(inputs)}")
        tests = [(p, p.with_suffix(".c.expected").read_bytes()) for p in inputs]
    else:
        inputs = sorted((HERE / "fixtures").glob("*.c"))
        tests = [(p, None if p.stem.startswith("reject_") else p.with_suffix(".expected").read_bytes())
                 for p in inputs]
        args.minimum = sum(expected is not None for _, expected in tests)
        if args.minimum < 1 or len(tests) - args.minimum < 5:
            parser.error("fixtures need at least one successful and five rejected inputs")
    return corpus(args, tests)


if __name__ == "__main__":
    sys.exit(main())
