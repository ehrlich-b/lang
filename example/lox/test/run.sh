#!/bin/bash
set -eu
compiler=${COMPILER:-./out/lang_next}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lox-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
LANGBE=llvm "$compiler" compiler lox example/lox/lox.lang --runtime example/lox/runtime.lang -o "$tmp/loxc"
LOXC="$tmp/loxc" python3 -B example/lox/test/run.py
python3 -B test/lox/test_score.py
