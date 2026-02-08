#!/bin/bash
# Extract lang AST S-expressions from patched Zig -ofmt=c output.
# Picks up (func ...) and (extern_func ...) forms, wraps in (program ...).
#
# Usage: ./scripts/extract-zig-ast.sh input.c > output.ast

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <zig-c-output>" >&2
    exit 1
fi

input="$1"

if [ ! -f "$input" ]; then
    echo "Error: file not found: $input" >&2
    exit 1
fi

echo "(program"
# Strip "static " prefix from non-exported functions, then extract S-expressions
sed 's/^static (func /(func /' "$input" | \
    awk '/^\(func |^\(extern_func /{found=1} found{print} /^$/ && found{found=0}'
echo ")"
