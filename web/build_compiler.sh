#!/bin/bash
# Build the self-hosted compiler as a browser-hosted wasm module.
set -e
cd "$(dirname "$0")/.."

if [ -z "${COMPILER:-}" ]; then
    make build
    COMPILER=./out/lang_next
fi
COMPILER_RECEIPT=${COMPILER_RECEIPT:-out/build-receipt.json}
python3 scripts/build_receipt.py web-version --input "$COMPILER_RECEIPT" \
    --compiler "$COMPILER" --output out/web_version_info.lang
WEB_OUTPUT_DIR=${WEB_OUTPUT_DIR:-web}
mkdir -p "$WEB_OUTPUT_DIR"
WASM_LDFLAGS="-Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined -Wl,-z,stack-size=8388608"

if [ -z "${WASM_CLANG:-}" ]; then
    if [ -x /opt/homebrew/opt/llvm/bin/clang ]; then
        WASM_CLANG=/opt/homebrew/opt/llvm/bin/clang
    elif [ -x /usr/local/opt/llvm/bin/clang ]; then
        WASM_CLANG=/usr/local/opt/llvm/bin/clang
    else
        WASM_CLANG=$(command -v clang)
    fi
fi

OS_LANG_ORIG=$(cat std/os.lang)
restore_os() { echo "$OS_LANG_ORIG" > std/os.lang; }
trap restore_os EXIT
echo 'include "std/os/libc.lang"' > std/os.lang

node web/build_stdlib.js "$WEB_OUTPUT_DIR/stdlib.json"

tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")
trap 'restore_os; rm -rf "$tmp"' EXIT
LANGOS=wasm LANGBE=llvm "$COMPILER" \
    std/core.lang out/web_version_info.lang src/lexer.lang src/parser.lang \
    src/codegen.lang src/codegen_llvm.lang src/codegen_wasm.lang src/ast_emit.lang \
    src/sexpr_reader.lang src/compiler_readers_web.lang src/main.lang -o "$tmp/compiler.ll"
"$WASM_CLANG" -O2 --target=wasm32-unknown-unknown -nostdlib $WASM_LDFLAGS \
    "$tmp/compiler.ll" -o "$WEB_OUTPUT_DIR/compiler.wasm"
echo "built $WEB_OUTPUT_DIR/compiler.wasm ($(wc -c < "$WEB_OUTPUT_DIR/compiler.wasm" | tr -d ' ') bytes)"
python3 scripts/build_receipt.py web --input "$COMPILER_RECEIPT" --compiler "$COMPILER" \
    --output "$WEB_OUTPUT_DIR/compiler-receipt.json" --artifact "$WEB_OUTPUT_DIR/compiler.wasm" --artifact "$WEB_OUTPUT_DIR/stdlib.json"
