#!/bin/bash
set -e
cd "$(dirname "$0")/.."

COMPILER=${COMPILER:-./out/bootstrap_verify/kernel2}
if [ ! -x "$COMPILER" ]; then
    echo "direct wasm compiler missing: $COMPILER; run make verify first" >&2
    exit 1
fi
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")
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
run_case test/direct_wasm_float_e2e.lang 42
run_case test/suite/260_float_basic.lang 215
run_case test/suite/261_float_composed.lang 100
run_case test/suite/290_pointer_index_floats.lang 42
run_case test/direct_wasm_memory_e2e.lang 176
run_case test/direct_wasm_import_e2e.lang 17
run_case test/direct_wasm_struct_e2e.lang 42
run_case test/direct_wasm_aggregate_layout.lang 42
run_case test/direct_wasm_array_alias.lang 42
run_case test/suite/300_aggregate_values.lang 42
run_case test/suite/250_arrays.lang 150
run_case test/direct_wasm_ast_e2e.lang 40
run_case test/direct_wasm_reader_e2e.lang 40
run_case test/direct_wasm_calc_reader_e2e.lang 40
run_case test/suite/286_local_address_shadows_function.lang 0
run_case test/suite/287_node_origins_index.lang 0
# A declaration reader and an expression reader must expand before reachability.
run_case test/borders/cases/minipy_functions.lang 42
run_case test/borders/cases/minilisp_integers.lang 42

unsupported="$tmp/unsupported.wasm"
if LANGBE=wasm LANGOS=wasm "$COMPILER" test/direct_wasm_aggregate_return_reject.lang -o "$unsupported" \
   >"$tmp/unsupported.out" 2>"$tmp/unsupported.err"; then
    echo "direct wasm unexpectedly accepted an unsupported struct return" >&2
    exit 1
else
    status=$?
    if [ "$status" -ne 1 ]; then
        cat "$tmp/unsupported.err" >&2
        echo "direct wasm struct return rejection exited $status instead of 1" >&2
        exit 1
    fi
fi
if ! grep -q 'struct and array value returns are unsupported' "$tmp/unsupported.err"; then
    cat "$tmp/unsupported.err" >&2
    exit 1
fi
if [ -e "$unsupported" ]; then
    echo "direct wasm left partial output after a compile error" >&2
    exit 1
fi
if ! grep -q '^test/direct_wasm_aggregate_return_reject.lang:2:.*: error:' "$tmp/unsupported.err"; then
    echo "direct wasm error did not preserve source provenance" >&2
    cat "$tmp/unsupported.err" >&2
    exit 1
fi

numeric="$tmp/numeric.wasm"
if LANGBE=wasm LANGOS=wasm "$COMPILER" test/direct_wasm_aggregate_numeric_reject.lang -o "$numeric" \
   >"$tmp/numeric.out" 2>"$tmp/numeric.err"; then
    echo "direct wasm unexpectedly accepted float-to-integer global initialization" >&2
    exit 1
else
    status=$?
    if [ "$status" -ne 1 ]; then
        cat "$tmp/numeric.err" >&2
        echo "direct wasm numeric rejection exited $status instead of 1" >&2
        exit 1
    fi
fi
if [ -e "$numeric" ] || \
   ! grep -q '^test/direct_wasm_aggregate_numeric_reject.lang:2:.*: error:.*float-to-integer global initialization is unsupported' "$tmp/numeric.err"; then
    cat "$tmp/numeric.err" >&2
    echo "direct wasm numeric rejection did not preserve source provenance or left partial output" >&2
    exit 1
fi

if LANGBE=wasm LANGOS=wasm "$COMPILER" test/direct_wasm_float_reject.lang -o "$tmp/float-reject.wasm" >"$tmp/float-reject.out" 2>&1; then
    echo "direct wasm unexpectedly accepted floating remainder" >&2
    exit 1
fi
if [ -e "$tmp/float-reject.wasm" ] || ! grep -q 'unsupported floating operator' "$tmp/float-reject.out"; then
    cat "$tmp/float-reject.out" >&2
    echo "direct wasm floating remainder did not fail closed" >&2
    exit 1
fi

echo "direct wasm: passed"
