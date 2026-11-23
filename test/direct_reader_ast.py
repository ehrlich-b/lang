#!/usr/bin/env python3
"""Compare direct Tariff lowering with text, and replay reader AST snapshots."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARIFF = Path("examples/dsl-compare")
EXAMPLE = Path("example")


def call(root, compiler, env, *args):
    return subprocess.check_output([compiler, *args], cwd=root, env=env)


def read(root, compiler, env, reader, source, compact=False):
    mode = ("--compact",) if compact else ()
    return call(root, compiler, env, "read", reader, source, *mode)


def snapshot(root, compiler, env, reader, source, work):
    compact = read(root, compiler, env, reader, source, True)
    formatted = read(root, compiler, env, reader, source)
    ast, roundtrip = work / "source.ast", work / "roundtrip.ast"
    ast.write_bytes(compact)
    call(root, compiler, env, "--from-ast", ast, "--ast-source", source,
         "--emit-ast", "-o", roundtrip)
    normalized = roundtrip.read_bytes()
    ast.write_bytes(normalized)
    call(root, compiler, env, "--from-ast", ast, "--emit-ast", "-o", roundtrip)
    assert roundtrip.read_bytes() == normalized, f"unstable AST round trip: {source}"
    return compact, formatted, normalized


def check_direct(work, compiler, env):
    reader = TARIFF / "lang/reader.lang"
    minted = work / "tariff"
    call(ROOT, compiler, env, "compiler", "tariff", reader, "-o", minted)
    for source in sorted((ROOT / TARIFF / "fixtures").rglob("*.tariff")):
        expected = work / "text.ll"
        actual = work / "direct.ll"
        if source.parent.name == "invalid":
            failure = subprocess.run([minted, "--trusted-reader", "--check-reader", source],
                                     cwd=ROOT, env=env, capture_output=True)
            assert failure.returncode == 1 and failure.stderr, source
            continue
        ast = work / "tariff.ast"
        ast.write_bytes(read(ROOT, compiler, env, reader, source, True))
        call(ROOT, compiler, env, "--from-ast", ast, "--ast-source", source, "-o", expected)
        call(ROOT, minted, env, "--trusted-reader", source, "--emit=llvm", "-o", actual)
        assert expected.read_bytes() == actual.read_bytes(), source
    print("PASS Tariff fixtures produce identical LLVM through direct and text AST")


def fixture_cases(work):
    fixtures = [
        ("tiny/tiny.lang", "tiny/answer.tiny"),
        ("tiny/stage.lang", "tiny/answer.tiny"),
        ("calc/calc.lang", "calc/answer.calc"),
        ("lox/lox.lang", "lox/test/expressions.lox"),
        ("lox/lox.lang", "lox/test/functions.lox"),
        ("lox/lox.lang", "lox/test/variables.lox"),
        ("rill/rill.lang", "rill/compiler-module.rill"),
        ("shipping/shipping.lang", "shipping/policy.shipping"),
        ("shipping/shipping.lang", "shipping/client/policy.shippinglib"),
        ("shipping/client/reader.lang", "shipping/client/client.shippingforth"),
    ]
    for reader, source in fixtures:
        yield EXAMPLE / reader, ROOT / EXAMPLE / source
    snippets = [
        ("c/c.lang", "c", "int add(int a, int b) { return a + b; }\n"),
        ("flow/flow.lang", "flow", "gen one(n) { yield n; }\n"),
        ("forth/forth.lang", "forth", ": square ( n -- n2 ) dup * ;\n"),
        ("lua/lua.lang", "lua", "assert(19 + 23 == 42)\n"),
        ("minilisp/minilisp.lang", "minilisp", "(defun add (a b) (+ a b))\n"),
        ("minipy/minipy.lang", "minipy", "def add(a, b):\n    return a + b\n"),
    ]
    for reader, suffix, text in snippets:
        source = work / f"program.{suffix}"
        source.write_text(text)
        yield EXAMPLE / reader, source
    source = work / "program.scheme"
    source.write_bytes((ROOT / EXAMPLE / "scheme/basic.scm").read_bytes())
    yield EXAMPLE / "scheme/scheme.lang", source


def check_text(work, compiler, env, base):
    base_compiler = base / "out/lang_next"
    old_reader = work / "base-tariff.lang"
    source = base / TARIFF / "lang/tariff.lang"
    body = source.read_text().partition("\nfunc main(")[0]
    old_reader.write_text(body + "\nreader tariff(text *u8) *u8 { return tariff_read(text); }\n")
    cases = [(reader, reader, source) for reader, source in fixture_cases(work)]
    cases.extend((old_reader, TARIFF / "lang/reader.lang", source)
                 for source in sorted((ROOT / TARIFF / "fixtures").rglob("*.tariff"))
                 if source.parent.name != "invalid")
    for old, new, source in cases:
        before = snapshot(base, base_compiler, env, old, source, work)
        after = snapshot(ROOT, compiler, env, new, source, work)
        assert before == after, f"snapshot drift: {new} / {source.name}"
        print(f"PASS byte-identical compact, formatted and round-trip AST {new} / {source.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--compiler", type=Path, default=ROOT / "out/lang_next")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="direct-ast-") as directory:
        work = Path(directory)
        env = os.environ | {"LANGBE": "llvm", "TMPDIR": directory,
                            "LANG_CACHE": str(work / "cache")}
        if args.base:
            check_text(work, args.compiler.resolve(), env, args.base.resolve())
        check_direct(work, args.compiler.resolve(), env)


if __name__ == "__main__":
    main()
