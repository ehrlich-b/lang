#!/bin/bash
# Build the self-hosted compiler as a browser-hosted wasm module.
set -e
cd "$(dirname "$0")/.."

COMPILER=${COMPILER:-./out/lang}
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

node web/build_stdlib.js

tmp=$(mktemp -d)
trap 'restore_os; rm -rf "$tmp"' EXIT
LANGOS=wasm LANGBE=llvm "$COMPILER" \
    std/core.lang out/version_info.lang src/lexer.lang src/parser.lang \
    src/codegen.lang src/codegen_llvm.lang src/codegen_wasm.lang src/ast_emit.lang \
    src/sexpr_reader.lang src/compiler_readers_web.lang src/main.lang -o "$tmp/compiler.ll"
"$WASM_CLANG" --target=wasm32-unknown-unknown -nostdlib $WASM_LDFLAGS \
    "$tmp/compiler.ll" -o web/compiler.wasm
echo "built web/compiler.wasm ($(wc -c < web/compiler.wasm | tr -d ' ') bytes)"
