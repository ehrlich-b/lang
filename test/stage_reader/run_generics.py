#!/usr/bin/env python3
"""Compile and run the Lang reader's List specialization as native code."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", required=True)
    parser.add_argument("--type", choices=("i64",), required=True)
    parser.add_argument("--opt", choices=("O0", "O2"), required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    compiler = Path(os.environ.get("COMPILER", "out/lang_next")).resolve()
    fixture = Path(f"test/stage_reader/list_{args.type}.lang")
    name = f"List_{args.type}"
    clang = os.environ.get("CLANG", "clang")
    with tempfile.TemporaryDirectory(prefix="lang-generics-") as directory:
        work = Path(directory)
        ir = work / "list.ll"
        binary = work / "list"
        env = dict(os.environ, LANGBE="llvm", LANG_CACHE=str(work / "cache"))
        subprocess.run([compiler, fixture, "-o", ir], cwd=root, env=env,
                       check=True, timeout=60)

        definitions = re.findall(rf"^define .*@{name}_push\([^\n]*", ir.read_text(), re.M)
        if len(definitions) != 1 or not re.search(r", i64\s", definitions[0]):
            raise SystemExit(f"expected one typed {name}_push definition, found {definitions}")
        print(definitions[0], flush=True)

        subprocess.run([clang, f"-{args.opt}", ir, "-o", binary], check=True, timeout=60)
        result = subprocess.run([binary], timeout=10)
        if result.returncode != 42:
            raise SystemExit(f"expected native exit 42, got {result.returncode}")
        print(f"{name} native -{args.opt} answered {result.returncode}")


if __name__ == "__main__":
    main()
