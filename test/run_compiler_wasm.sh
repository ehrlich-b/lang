#!/bin/bash
# Build compiler.wasm, compile a program inside it, then link and run that output.
set -e
cd "$(dirname "$0")/.."

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

COMPILER=${COMPILER:-./out/lang} ./web/build_compiler.sh
node test/compiler_direct_wasm_e2e.js web/compiler.wasm
node test/compiler_wasm_e2e.js web/compiler.wasm "$tmp/output.ll"

if [ -x /opt/homebrew/opt/llvm/bin/clang ]; then
    WASM_CLANG=/opt/homebrew/opt/llvm/bin/clang
elif [ -x /usr/local/opt/llvm/bin/clang ]; then
    WASM_CLANG=/usr/local/opt/llvm/bin/clang
else
    WASM_CLANG=$(command -v clang)
fi

"$WASM_CLANG" --target=wasm32-unknown-unknown -nostdlib \
    -Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined \
    -Wl,-z,stack-size=8388608 "$tmp/output.ll" -o "$tmp/output.wasm"

set +e
node test/wasm_host.js "$tmp/output.wasm"
status=$?
set -e
if [ "$status" != 98 ]; then
    echo "FAIL compiler_wasm_e2e (expected 98, got $status)"
    exit 1
fi
echo "PASS compiler_wasm_e2e"
