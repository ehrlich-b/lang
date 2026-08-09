#!/bin/bash
set -e
cd "$(dirname "$0")/.."

COMPILER=${COMPILER:-./out/lang}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

LANGBE=wasm LANGOS=wasm "$COMPILER" test/direct_wasm_e2e.lang -o "$tmp/direct.wasm"

set +e
node test/wasm_host.js "$tmp/direct.wasm"
status=$?
set -e

if [ "$status" -ne 42 ]; then
    echo "direct wasm test failed: expected 42, got $status" >&2
    exit 1
fi

echo "direct wasm: passed"
