#!/bin/bash
# Build the demo site artifacts: compile each example to wasm and copy its
# source next to it. Run from anywhere; outputs into web/examples/.
set -e
cd "$(dirname "$0")/.."

EXAMPLES="fib mandelbrot polyglot_wasm"
if [ -z "${COMPILER:-}" ]; then
    make build
    COMPILER=./out/lang_next
fi
COMPILER_RECEIPT=${COMPILER_RECEIPT:-out/build-receipt.json}
export COMPILER_RECEIPT
python3 scripts/build_receipt.py check --input "$COMPILER_RECEIPT" --compiler "$COMPILER"
# Publish measured snapshots, the tutorial, and real native compiler traces.
python3 web/generate_borders.py
python3 web/generate_scoreboard.py
python3 web/generate_language_maker.py --compiler "$COMPILER"
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
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")
    LANG_CACHE="$tmp/cache" LANGOS=wasm LANGBE=llvm $COMPILER "example/$e.lang" -o "$tmp/$e.ll" >/dev/null
    "$WASM_CLANG" --target=wasm32-unknown-unknown -nostdlib $WASM_LDFLAGS "$tmp/$e.ll" -o "web/examples/$e.wasm"
    cp "example/$e.lang" "web/examples/$e.lang"
    rm -rf "$tmp"
    echo "built web/examples/$e.wasm ($(wc -c < web/examples/$e.wasm | tr -d ' ') bytes)"
done

COMPILER="$COMPILER" WASM_CLANG="$WASM_CLANG" ./web/build_compiler.sh
python3 scripts/build_receipt.py web --input "$COMPILER_RECEIPT" --compiler "$COMPILER" \
    --output web/receipt.json --artifact web/compiler.wasm --artifact web/stdlib.json \
    --artifact web/examples/fib.wasm --artifact web/examples/fib.lang \
    --artifact web/examples/mandelbrot.wasm --artifact web/examples/mandelbrot.lang \
    --artifact web/examples/polyglot_wasm.wasm --artifact web/examples/polyglot_wasm.lang
