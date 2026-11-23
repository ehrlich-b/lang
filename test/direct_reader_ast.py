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


def check_tariff_cli_and_sdk_mint(work, compiler, env):
    consumer = work / "consumer"
    consumer.mkdir()
    original = ROOT / TARIFF / "lang/tariff.lang"
    source = ROOT / TARIFF / "fixtures/benchmark.tariff"
    harness = ROOT / TARIFF / "harness.c"
    cli = consumer / "tariff.lang"
    cli.write_bytes(original.read_bytes())
    call(consumer, compiler, env, "tariff.lang", "-o", "frontend.ll")
    call(consumer, "clang", env, "-O2", "frontend.ll", "-o", "frontend")
    (consumer / "program.ast").write_bytes(call(consumer, "./frontend", env, source))
    call(consumer, compiler, env, "--from-ast", "program.ast", "--ast-source", source,
         "-o", "program.ll")
    call(consumer, "clang", env, "-O2", "program.ll", harness, "-o", "program")
    assert call(consumer, "./program", env, "2000000") == b"6000002995045\n"
    print("PASS copied Tariff CLI emits AST that links and runs")

    # The SDK's consumer replaces the CLI main with a reader declaration.
    body, separator, _ = original.read_text().partition("\nfunc main(")
    assert separator, original
    cli.write_text(body + "\nreader tariff(text *u8) *u8 { return tariff_read(text); }\n")
    call(consumer, compiler, env, "compiler", "tariff", "tariff.lang", "-o", "tariffc")
    call(consumer, "./tariffc", env, source, "-o", "minted.ll")
    call(consumer, "clang", env, "-O2", "minted.ll", harness, "-o", "minted")
    assert call(consumer, "./minted", env, "2000000") == b"6000002995045\n"
    print("PASS existing SDK Tariff adaptation mints a working compiler")


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

    malformed = work / "missing-open-brace.tariff"
    malformed.write_text("fn compute(n) return n;\n")
    expected = b"expected '{', found return @14:20"
    for command in ([compiler, "read", reader, malformed],
                    [minted, "--trusted-reader", "--check-reader", malformed]):
        failure = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        assert failure.returncode == 1 and not failure.stdout, failure
        assert expected in failure.stderr, failure.stderr
    print("PASS Tariff diagnoses a missing opening brace on both AST paths")


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
    for fixture in sorted((ROOT / EXAMPLE / "scheme").glob("*.scm")):
        if fixture.name != "refusal.scm":
            source = work / (fixture.stem + ".scheme")
            source.write_bytes(fixture.read_bytes())
            yield EXAMPLE / "scheme/scheme.lang", source
    for name in ("arithmetic.lua", "false.lua"):
        yield EXAMPLE / "lua/lua.lang", ROOT / "test/lua" / name
    tree = work / "tree-reader.lang"
    tree.write_text('include "std/parser_reader.lang"\ninclude "example/tree/tree.lang"\n')
    yield tree, ROOT / "test/pnode_dump_source.pdebug"


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
        check_tariff_cli_and_sdk_mint(work, args.compiler.resolve(), env)
        check_direct(work, args.compiler.resolve(), env)


if __name__ == "__main__":
    main()
