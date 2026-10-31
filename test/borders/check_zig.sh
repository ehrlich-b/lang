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
grep -Fq 'Zig input unsupported: no Zig reader or AIR-to-core importer is installed' "$output"
