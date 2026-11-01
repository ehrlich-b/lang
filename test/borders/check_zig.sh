#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
compiler=${COMPILER:-out/bootstrap_verify/kernel2}
output=$(mktemp)
trap 'rm -f "$output"' EXIT
if "$compiler" read example/c/c.lang test/borders/missing.zig >"$output" 2>&1; then
    echo 'unexpectedly accepted Zig input' >&2
    exit 1
fi
cat "$output"
grep -Fq "reader 'zig' not found" "$output"
# Another absent reader must take the same language-neutral path.
cp test/borders/missing.zig "${output}.unknown"
trap 'rm -f "$output" "${output}.unknown"' EXIT
if "$compiler" read example/c/c.lang "${output}.unknown" >"$output" 2>&1; then
    echo 'unexpectedly accepted unknown input' >&2
    exit 1
fi
grep -Fq "reader 'unknown' not found" "$output"
