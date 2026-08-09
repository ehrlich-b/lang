#!/bin/bash
# Build the demo site artifacts: compile each example to wasm and copy its
# source next to it. Run from anywhere; outputs into web/examples/.
set -e
cd "$(dirname "$0")/.."

EXAMPLES="fib mandelbrot polyglot_wasm"
COMPILER=${COMPILER:-./out/lang}
WASM_LDFLAGS="-Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined -Wl,-z,stack-size=8388608"

# Apple clang does not ship the wasm target. Match the test suite's tool lookup
# so deploys behave the same in interactive and escalated environments.
if [ -z "${WASM_CLANG:-}" ]; then
    if [ -x /opt/homebrew/opt/llvm/bin/clang ]; then
        WASM_CLANG=/opt/homebrew/opt/llvm/bin/clang
    elif [ -x /usr/local/opt/llvm/bin/clang ]; then
        WASM_CLANG=/usr/local/opt/llvm/bin/clang
    else
        WASM_CLANG=$(command -v clang)
    fi
fi

# wasm programs build against the generic libc surface (the JS host provides it)
OS_LANG_ORIG=$(cat std/os.lang)
restore_os() { echo "$OS_LANG_ORIG" > std/os.lang; }
trap restore_os EXIT
echo 'include "std/os/libc.lang"' > std/os.lang

mkdir -p web/examples
for e in $EXAMPLES; do
    tmp=$(mktemp -d)
    LANG_CACHE="$tmp/cache" LANGOS=wasm LANGBE=llvm $COMPILER "example/$e.lang" -o "$tmp/$e.ll" >/dev/null
    "$WASM_CLANG" --target=wasm32-unknown-unknown -nostdlib $WASM_LDFLAGS "$tmp/$e.ll" -o "web/examples/$e.wasm"
    cp "example/$e.lang" "web/examples/$e.lang"
    rm -rf "$tmp"
    echo "built web/examples/$e.wasm ($(wc -c < web/examples/$e.wasm | tr -d ' ') bytes)"
done
