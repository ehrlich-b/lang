#!/bin/bash
set -eu
compiler=${COMPILER:-./out/lang}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lox-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
LANGBE=llvm "$compiler" compiler lox example/lox/lox.lang --runtime example/lox/runtime.lang -o "$tmp/loxc" >"$tmp/build.log" 2>&1 || { cat "$tmp/build.log"; exit 1; }
for name in expressions unary_error numeric_error add_error; do
    "$tmp/loxc" "example/lox/test/$name.lox" -o "$tmp/program.ll" >"$tmp/compile.log" 2>&1 || { cat "$tmp/compile.log"; exit 1; }
    status=0
    lli "$tmp/program.ll" >"$tmp/out" 2>"$tmp/err" || status=$?
    if [ "$name" = expressions ]; then
        test "$status" = 0
        diff -u example/lox/test/expressions.out "$tmp/out"
        test ! -s "$tmp/err"
    else
        test "$status" = 70
        test ! -s "$tmp/out"
        diff -u "example/lox/test/$name.err" "$tmp/err"
    fi
done
if "$tmp/loxc" example/lox/test/syntax_error.lox -o "$tmp/bad.ll" >"$tmp/out" 2>"$tmp/err"; then exit 1; fi
grep -q 'line 2' "$tmp/err"
echo 'PASS lox fixtures'
