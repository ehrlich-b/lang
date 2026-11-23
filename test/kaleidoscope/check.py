#!/usr/bin/env python3
"""Check the native reader and compare it with the pinned Chapter 7 toy."""
import argparse
import difflib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

FIXTURES = Path("test/kaleidoscope")
EXAMPLE = Path("example/kaleidoscope")

# Inclusive RST line ranges in llvmorg-19.1.7. Only guest input is extracted.
TUTORIAL = {
    "01-fibonacci": (1, [(28, 36)]),
    "01-libm": (1, [(45, 49)]),
    "02-recursive-prototype": (2, [(698, 698)]),
    "02-stray-identifier": (2, [(700, 700)]),
    "02-stray-close": (2, [(703, 703)]),
    "02-extern": (2, [(706, 706)]),
    "03-prototype-names": (3, [(416, 417)]),
    "03-sum": (3, [(430, 430)]),
    "03-definitions": (3, [(447, 447), (465, 465)]),
    "03-cosine": (3, [(481, 481), (485, 485)]),
    "04-constant-folding": (4, [(28, 28)]),
    "04-reassociate": (4, [(73, 73)]),
    "04-keep-definition": (4, [(402, 402), (411, 411), (421, 421)]),
    "04-redefine": (4, [(449, 449), (457, 457), (460, 460), (467, 467)]),
    "04-putchard": (4, [(666, 666)]),
    "04-math": (4, [(587, 587), (591, 591), (595, 595), (604, 604), (616, 616)]),
    "05-condition": (5, [(36, 41)]),
    "05-extern-branches": (5, [(184, 186)]),
    "05-print-stars": (5, [(437, 443)]),
    "06-operator-examples": (6, [(55, 77)]),
    "06-sequence": (6, [(460, 460), (464, 464), (466, 466)]),
    "06-density": (6, [(477, 513), (522, 522), (524, 532), (534, 536)]),
    "06-mandelbrot": (
        6, [(477, 513), (522, 522), (524, 532), (549, 559), (575, 586),
            (592, 592), (635, 635), (678, 678)],
    ),
    "07-iterative-fibonacci": (7, [(278, 297)]),
    "07-mutable-parameter": (7, [(623, 634)]),
    "08-average": (8, [(183, 183)]),
    "09-debug-fibonacci": (9, [(40, 46)]),
}
REVIEW_REGRESSIONS = {
    "assignment-bindings", "duplicate-parameters", "extern-changed-arity", "loop-bindings",
}
TUTORIAL_REJECTED = {
    "02-stray-identifier", "02-stray-close", "03-prototype-names", "04-redefine",
}


def run(*args, **kwargs):
    return subprocess.run(args, capture_output=True, timeout=90, **kwargs)


def checked(*args, **kwargs):
    result = run(*args, **kwargs)
    if result.returncode:
        raise RuntimeError(
            f"{shlex.join(map(str, args))} exited {result.returncode}\n"
            f"{result.stdout.decode(errors='replace')}{result.stderr.decode(errors='replace')}"
        )
    return result.stdout


def reference_output(ref, fixture):
    result = run(ref, input=fixture.read_bytes())
    output = re.sub(rb"(?m)^(?:ready> )+", b"", result.stderr)
    rejected = re.search(rb"(?m)^(?:Error:|Duplicate definition of symbol )", output)
    if result.returncode < 0 or (result.returncode != 0 and not rejected):
        raise RuntimeError(f"{fixture}: reference exit {result.returncode}\n{output!r}")
    if rejected:
        return None
    output = re.sub(rb"(?m)^Read extern: declare [^\n]*\n\n", b"", output)
    output = re.sub(rb"(?ms)^Read function definition:.*?^}\n\n", b"", output)
    return result.stdout, output


def difference(actual, expected):
    return "".join(difflib.unified_diff(
        expected.decode(errors="backslashreplace").splitlines(keepends=True),
        actual.decode(errors="backslashreplace").splitlines(keepends=True),
        fromfile="expected", tofile="actual",
    ))


def reject(compiler, fixture, ir, message=""):
    result = run(compiler, "-g", fixture, "-o", ir)
    err = result.stderr.decode(errors="replace")
    assert result.returncode == 1 and not ir.exists(), f"{fixture}: {result.returncode}\n{err}"
    assert not re.search(r"segmentation fault|aborted|LLVM ERROR|verifier", err, re.I), err
    match = re.fullmatch(
        rf"{re.escape(str(fixture))}:(\d+):(\d+): ([^\n]+)\n([^\n]*)\n([^\n]*\^.*)\n?",
        err,
    )
    assert match and message in match[3], err
    lines = fixture.read_text().split("\n")
    source = lines[int(match[1]) - 1]
    assert match[4].strip() == source.strip(), err
    assert match[5].index("^") - (len(match[4]) - len(source)) == int(match[2]) - 1, err
    print(f"reject {fixture.name} at {match[1]}:{match[2]} {match[3]}")


def native(compiler, fixture, work, link_flags):
    ir = work / "guest.ll"
    checked(compiler, "-g", fixture, "-o", ir)
    outputs = []
    binaries = []
    for opt in ("-O0", "-O2"):
        binary = work / opt[1:]
        checked(os.environ.get("CLANG", "clang"), opt, "-g", "-Wno-override-module", ir,
                work / "runtime.o", "-rdynamic", *link_flags, "-o", binary)
        result = run(binary)
        assert result.returncode == 0, f"{fixture} {opt}: {result.returncode}\n{result.stderr!r}"
        outputs.append((result.stdout, result.stderr))
        binaries.append(binary)
    assert outputs[0] == outputs[1], f"{fixture}: -O0 / -O2 output differs\n{difference(outputs[1][1], outputs[0][1])}"
    return outputs[0], binaries


def check_dwarf(fixture, binaries, expected_rows):
    tool = os.environ.get("LLVM_DWARFDUMP", "llvm-dwarfdump")
    for binary in binaries:
        if sys.platform == "darwin":
            binary = Path(f"{binary}.dSYM") / "Contents/Resources/DWARF" / binary.name
        verified = checked(tool, "--verify", binary).decode()
        assert "No errors." in verified, verified
        print(verified, end="")
        table = checked(tool, "--debug-line", binary).decode()
        assert f'name: "{fixture.name}"' in table, table
        if binary.name == "O0":
            rows = {int(n) for n in re.findall(r"(?m)^0x[0-9a-f]+\s+(\d+)\s+\d+\s+1\s", table)}
            # One expression-bearing row per body line, including split operands.
            assert expected_rows <= rows, table
            print(table, end="")


def tutorial_programs(reference, work):
    for name, (chapter, ranges) in TUTORIAL.items():
        path = reference / "docs" / f"LangImpl{chapter:02}.rst"
        lines = path.read_text().splitlines()
        body = [line.strip().removeprefix("ready> ")
                for start, end in ranges for line in lines[start - 1:end]]
        if name == "04-putchard":
            body = [body[0].split("``")[1]]
        dest = work / f"tutorial-{name}.kal"
        dest.write_text("\n".join(body) + "\n")
        yield name, dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "score"))
    parser.add_argument("--compiler", type=Path, required=True, help="minted Kaleidoscope compiler")
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--regressions", action="store_true", help="score the four binding/prototype regressions")
    args = parser.parse_args()
    if args.regressions and args.mode != "score":
        parser.error("--regressions requires score")
    if args.mode == "score" and not args.reference:
        parser.error("score requires --reference")
    args.work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"{args.mode}-", dir=args.work.resolve()) as temp:
        work = Path(temp)
        link_flags = shlex.split(checked("pkg-config", "--libs", "libffi").decode())
        # ELF linkers can drop libm because the guest resolves its functions at runtime.
        if sys.platform == "linux":
            link_flags.extend(("-Wl,--no-as-needed", "-lm"))
        cflags = shlex.split(checked("pkg-config", "--cflags", "libffi").decode())
        checked(os.environ.get("CLANG", "clang"), "-O2", *cflags, "-c", EXAMPLE / "runtime.c",
                "-o", work / "runtime.o")
        expected = json.loads((FIXTURES / "expected.json").read_text())
        fixtures = sorted(FIXTURES.glob("*/*.kal"))
        assert {p.relative_to(FIXTURES).as_posix() for p in fixtures} == expected.keys()
        accepted = [p for p in fixtures if p.parent.name == "accepted"]
        rejected = [p for p in fixtures if p.parent.name == "rejected"]
        assert len(accepted) >= 30 and len(rejected) >= 10
        compiler = args.compiler.resolve()
        if not args.regressions:
            for fixture in rejected:
                reject(compiler, fixture, work / "rejected.ll", expected[fixture.relative_to(FIXTURES).as_posix()])
        if args.mode == "verify":
            for fixture in accepted:
                actual, binaries = native(compiler, fixture, work, link_flags)
                want = expected[fixture.relative_to(FIXTURES).as_posix()].encode()
                assert actual == (b"", want), f"{fixture}:\n{difference(actual[1], want)}"
                if fixture.name == "debug.kal":
                    check_dwarf(fixture, binaries, {2, 3, 5, 6, 8, 10, 11})
                if fixture.name == "debug-assignment.kal":
                    check_dwarf(fixture, binaries, {2, 3})
            print(f"Verified {len(accepted)} original programs at -O0/-O2 and {len(rejected)} located rejections. Crash count 0.")
            return

        reference = work / "reference"
        shutil.copytree(args.reference, reference)
        config = [os.environ.get("LLVM_CONFIG", "llvm-config"), "--cxxflags", "--ldflags",
                  "--system-libs", "--libs", "core", "orcjit", "native"]
        print(shlex.join(config), flush=True)
        flags = shlex.split(checked(*config).decode())
        ref = work / "toy"
        build = [os.environ.get("CXX", "clang++"), reference / "Chapter7/toy.cpp",
                 "-I", reference / "include", *flags, "-rdynamic", "-o", ref]
        print(shlex.join(map(str, build)), flush=True)
        checked(*build)
        programs = [(fixture.name, fixture) for fixture in accepted]
        if args.regressions:
            programs = [(name, fixture) for name, fixture in programs if fixture.stem in REVIEW_REGRESSIONS]
            assert len(programs) == len(REVIEW_REGRESSIONS)
        else:
            programs.extend(tutorial_programs(reference, work))
        matched = 0
        rejections = 0
        for name, fixture in programs:
            want = reference_output(ref, fixture)
            if name in TUTORIAL_REJECTED:
                assert want is None, f"{name}: reference unexpectedly accepted"
                reject(compiler, fixture, work / "rejected.ll")
                rejections += 1
            else:
                assert want is not None, f"{name}: reference unexpectedly rejected"
                actual, _ = native(compiler, fixture, work, link_flags)
                assert actual == want, f"{name}:\n{difference(actual[1], want[1])}"
                if args.regressions:
                    print(f"match {name} at -O0 and -O2\n{want[1].decode()}", end="")
                else:
                    print(f"match {name} ({len(want[1])} stderr bytes)")
                matched += 1
        print(f"Matched {matched}/{len(programs) - rejections} programs at -O0 and -O2.")
        if not args.regressions:
            print(f"Matched {rejections}/{len(TUTORIAL_REJECTED)} tutorial rejections. "
                  f"Verified {len(rejected)} local rejections. Crash count 0.")


if __name__ == "__main__":
    main()
