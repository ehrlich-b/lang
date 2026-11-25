#!/bin/bash
# Build compiler.wasm, compile a program inside it, then link and run that output.
set -e
cd "$(dirname "$0")/.."

if ! node -e '
    const { createRequire } = require("node:module");
    const { resolve } = require("node:path");
    const requireFromTest = createRequire(resolve("test/lab_reader_deadline.mjs"));
    requireFromTest(process.env.PLAYWRIGHT_MODULE || "playwright");
'; then
    echo 'Browser tests need Playwright. Run npm ci or set NODE_PATH to an existing node_modules directory.' >&2
    exit 1
fi

tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
export LANG_CACHE="$tmp/compiler-cache"

WEB_OUTPUT_DIR="$tmp/web" ./web/build_compiler.sh
node test/compiler_direct_wasm_e2e.js "$tmp/web/compiler.wasm"
LAB_COMPILER_WASM="$tmp/web/compiler.wasm" node test/lab_reader_deadline.mjs
LAB_COMPILER_WASM="$tmp/web/compiler.wasm" node test/lab_program_deadline.mjs
node test/compiler_wasm_e2e.js "$tmp/web/compiler.wasm" "$tmp/output.ll"
node test/editor_e2e.js

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

# Compile the LLVM indexing regressions inside the browser-hosted compiler,
# then validate and execute their emitted IR on the wasm target.
node test/compiler_wasm_pointer_index_e2e.js "$tmp/web/compiler.wasm" "$tmp/pointer-index"
for ir in "$tmp/pointer-index"/*.ll; do
    "$WASM_CLANG" --target=wasm32-unknown-unknown -nostdlib \
        -Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined \
        -Wl,-z,stack-size=8388608 "$ir" -o "$tmp/pointer-index.wasm"
    set +e
    node test/wasm_host.js "$tmp/pointer-index.wasm"
    status=$?
    set -e
    if [ "$status" != 42 ]; then
        echo "FAIL compiler_wasm_pointer_index $(basename "$ir") (expected 42, got $status)"
        exit 1
    fi
done
echo "PASS compiler_wasm_pointer_index_e2e (6 programs)"
