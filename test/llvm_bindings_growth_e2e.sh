#!/bin/bash
# Growing SSA bindings must preserve names and leave the struct registry intact.
set -euo pipefail
cd "$(dirname "$0")/.."
compiler=${COMPILER:-./out/lang}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT

{
    echo 'include "std/core.lang"'
    echo 'struct Pair { left i64; right i64; }'
    echo 'func large() i64 {'
    for ((i = 0; i < 700; i++)); do
        printf '    var v%d i64 = %d;\n' "$i" "$i"
    done
    echo '    return v0 + v256 + v512 + v699;'
    echo '}'
    cat <<'LANG'
func fields() i64 {
    var pair *Pair = alloc(16);
    pair.left = 10;
    pair.right = 32;
    return pair.left + pair.right;
}
func main(argc i64, argv **u8) i64 {
    if large() != 1467 { return 1; }
    if fields() != 42 { return 2; }
    return 0;
}
LANG
} >"$tmp/large.lang"

# The saved-AST path allocates codegen registries differently from source input.
LANGBE=llvm "$compiler" --emit-exe-ast "$tmp/large.lang" -o "$tmp/large.ast" >/dev/null
for mode in source ast; do
    if [ "$mode" = source ]; then
        args=("$tmp/large.lang")
    else
        args=("$tmp/large.ast" --from-ast)
    fi
    LANGBE=llvm "$compiler" "${args[@]}" -o "$tmp/$mode.ll" >/dev/null
    clang -O0 "$tmp/$mode.ll" -o "$tmp/$mode" 2>"$tmp/clang.err"
    "$tmp/$mode"
done
echo 'PASS LLVM binding growth (700 locals, source and saved AST, retained names, later struct access)'
