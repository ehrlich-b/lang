#!/usr/bin/env python3
"""Count physical nonblank, non-comment code lines in both implementations."""
import argparse
from pathlib import Path
import re

READER = Path("example/kaleidoscope")
LEXICAL = ("lex.lang", "libc.lang")
# Keep string and character literals intact. Replace comments with whitespace
# and their original newlines so mixed code/comment lines still count.
TOKENS = re.compile(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|//[^\n]*|/\*.*?\*/''', re.S)


def lines(text):
    code = TOKENS.sub(lambda m: m[1] or " " + "\n" * m[0].count("\n"), text)
    return sum(bool(line.strip()) for line in code.splitlines())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    args = parser.parse_args()
    reader_text = (READER / "kaleidoscope.lang").read_text()
    declarations, sections = reader_text.split("// Lowering\n", 1)
    lowering, grammar = sections.split("// Grammar\n", 1)
    counts = {
        "Lexical profile": sum(lines((READER / name).read_text()) for name in LEXICAL),
        "Grammar": lines(grammar),
        "Lowering": lines(declarations) + lines(lowering),
        "Runtime": lines((READER / "runtime.c").read_text()),
    }
    total = sum(counts.values())
    scoped = total - counts["Lexical profile"]
    reference = lines((args.reference / "Chapter7/toy.cpp").read_text())
    for part, count in counts.items():
        print(f"{part}: {count}")
    print(f"Reader total with lexical profile: {total}")
    print(f"Grammar, lowering and runtime: {scoped}/{reference} ({scoped / reference:.1%})")
    if 3 * scoped > reference:
        raise SystemExit(f"Reader exceeds the one-third line budget of {reference // 3}")


if __name__ == "__main__":
    main()
