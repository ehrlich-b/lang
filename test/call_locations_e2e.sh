#!/bin/bash
# Exact call diagnostics through source, includes, reader AST, and minted compilers.
set -euo pipefail
cd "$(dirname "$0")/.."
compiler=${COMPILER:-./out/lang}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
checks=0

reject() {
    local backend=$1 source=$2 location=$3 message=$4
    shift 4
    local output="$tmp/output-$checks"
    if LANGBE="$backend" LANG_CACHE="$tmp/cache" "$compiler" "$@" -o "$output" \
            >"$tmp/stdout" 2>"$tmp/stderr"; then
        echo "FAIL accepted invalid call in $source ($backend)" >&2
        exit 1
    fi
    test ! -e "$output"
    if ! grep -Fq "$source:$location: error: $message" "$tmp/stderr"; then
        cat "$tmp/stderr" >&2
        echo "FAIL call location in $source ($backend), expected $location" >&2
        exit 1
    fi
    checks=$((checks + 1))
}

cat >"$tmp/few.lang" <<'LANG'
func two(a i64, b i64) i64 { return a + b; }
func main() i64 {
    var total i64 = 0;
    return total + two(
        1
    );
}
LANG
cat >"$tmp/nested.lang" <<'LANG'
func two(a i64, b i64) i64 { return a + b; }
func main() i64 {
    return two(1, two(2));
}
LANG
cat >"$tmp/unknown.lang" <<'LANG'
func id(a i64) i64 { return a; }
func main() i64 {
    return id(1) + absent(2);
}
LANG
cat >"$tmp/extern.lang" <<'LANG'
extern func outside(a i64) i64;
func main() i64 {
    return outside();
}
LANG
cat >"$tmp/included.lang" <<'LANG'
func broken() i64 {
    return two(1);
}
LANG
printf 'include "%s/included.lang"\n' "$tmp" >"$tmp/include.lang"
cat >>"$tmp/include.lang" <<'LANG'
func two(a i64, b i64) i64 { return a + b; }
func main() i64 { return broken(); }
LANG
for backend in llvm wasm; do
    reject "$backend" "$tmp/few.lang" 4:20 "function 'two' takes 2 arguments, called with 1" "$tmp/few.lang"
    reject "$backend" "$tmp/nested.lang" 3:19 "function 'two' takes 2 arguments, called with 1" "$tmp/nested.lang"
    reject "$backend" "$tmp/extern.lang" 3:12 "function 'outside' takes 1 argument, called with 0" "$tmp/extern.lang"
    reject "$backend" "$tmp/included.lang" 2:12 "function 'two' takes 2 arguments, called with 1" "$tmp/include.lang"
    if [ "$backend" = llvm ]; then message="undefined function 'absent'"; else message='unknown function'; fi
    reject "$backend" "$tmp/unknown.lang" 3:20 "$message" "$tmp/unknown.lang"
done

cat >"$tmp/c.c" <<'SOURCE'
int two(int a, int b) { return a + b; }
int main() {
    return 1 + two(1);
}
SOURCE
cat >"$tmp/flow.flow" <<'SOURCE'
func two(a, b) { return a + b; }
func main() {
    return 1 + two(1);
}
SOURCE
cat >"$tmp/minipy.minipy" <<'SOURCE'
def two(a, b):
    return a + b
def main():
    return 1 + two(1)
SOURCE
cat >"$tmp/minilisp.minilisp" <<'SOURCE'
(defun main ()
    (+ 1 (two 2)))
SOURCE
for reader in c flow minipy minilisp; do
    case "$reader" in
        c|flow) location=3:16 ;;
        minipy) location=4:16 ;;
        minilisp) location=2:11 ;;
    esac
    native_args=("example/$reader/$reader.lang" "$tmp/$reader.$reader")
    if [ "$reader" = minilisp ]; then
        native_args=("example/$reader/$reader.lang" example/minilisp/lisp_runtime.lang test/call_location_helper.lang "$tmp/$reader.$reader")
    fi
    reject llvm "$tmp/$reader.$reader" "$location" \
        "function 'two' takes 2 arguments, called with 1" \
        "${native_args[@]}"
    # Saved reader AST keeps the call span through formatting and reloading.
    LANGBE=llvm LANG_CACHE="$tmp/cache" "$compiler" read "example/$reader/$reader.lang" \
        "$tmp/$reader.$reader" -o "$tmp/$reader.ast" >/dev/null
    ast_args=("$tmp/$reader.ast" --from-ast --ast-source "$tmp/$reader.$reader")
    if [ "$reader" = minilisp ]; then ast_args+=(--runtime example/minilisp/lisp_runtime.lang --runtime test/call_location_helper.lang); fi
    for backend in llvm wasm; do
        reject "$backend" "$tmp/$reader.$reader" "$location" \
            "function 'two' takes 2 arguments, called with 1" \
            "${ast_args[@]}"
    done
done

# A minted C compiler has neither the Lang parser nor the reader's build path.
LANGBE=llvm LANG_CACHE="$tmp/cache-build" "$compiler" compiler c example/c/c.lang \
    -o "$tmp/cc" >"$tmp/mint.out" 2>"$tmp/mint.err"
compiler="$tmp/cc"
reject llvm "$tmp/c.c" 3:16 "function 'two' takes 2 arguments, called with 1" "$tmp/c.c"
echo "PASS call locations ($checks rejections; native, direct wasm, four readers, saved AST, minted C)"
