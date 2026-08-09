#!/bin/bash
set -e
cd "$(dirname "$0")/.."

COMPILER=${COMPILER:-./out/lang}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

run_case() {
    source=$1
    expected=$2
    output="$tmp/$(basename "$source" .lang).wasm"
    LANGBE=wasm LANGOS=wasm "$COMPILER" "$source" -o "$output"

    set +e
    node test/wasm_host.js "$output"
    status=$?
    set -e

    if [ "$status" -ne "$expected" ]; then
        echo "direct wasm test failed for $source: expected $expected, got $status" >&2
        exit 1
    fi
}

run_case test/direct_wasm_e2e.lang 42
run_case test/direct_wasm_memory_e2e.lang 176
run_case test/direct_wasm_import_e2e.lang 17
run_case test/direct_wasm_struct_e2e.lang 42
run_case test/direct_wasm_ast_e2e.lang 40
run_case test/direct_wasm_reader_e2e.lang 40
run_case test/direct_wasm_calc_reader_e2e.lang 40

unsupported="$tmp/unsupported.wasm"
if LANGBE=wasm LANGOS=wasm "$COMPILER" test/suite/250_arrays.lang -o "$unsupported" \
   >"$tmp/unsupported.out" 2>"$tmp/unsupported.err"; then
    echo "direct wasm unexpectedly accepted an unsupported array program" >&2
    exit 1
fi
if [ -e "$unsupported" ]; then
    echo "direct wasm left partial output after a compile error" >&2
    exit 1
fi
if ! grep -q '^test/suite/250_arrays.lang:.*: error:' "$tmp/unsupported.err"; then
    echo "direct wasm error did not preserve source provenance" >&2
    cat "$tmp/unsupported.err" >&2
    exit 1
fi

echo "direct wasm: passed"
