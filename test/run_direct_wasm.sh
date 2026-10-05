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
run_case test/suite/156_local_array_literal.lang 42
run_case test/suite/250_arrays.lang 150
run_case test/suite/251_array_literals.lang 42
run_case test/suite/252_array_narrow_assignment.lang 42

unsupported="$tmp/unsupported.wasm"
cat > "$tmp/unsupported.lang" <<'SOURCE'
func main() i64 {
    var aggregate [2][2]i64;
    return 0;
}
SOURCE
if LANGBE=wasm LANGOS=wasm "$COMPILER" "$tmp/unsupported.lang" -o "$unsupported" \
   >"$tmp/unsupported.out" 2>"$tmp/unsupported.err"; then
    echo "direct wasm unexpectedly accepted unsupported nested array elements" >&2
    exit 1
fi
if [ -e "$unsupported" ]; then
    echo "direct wasm left partial output after a compile error" >&2
    exit 1
fi
if ! grep -q '^.*unsupported.lang:.*: error:' "$tmp/unsupported.err"; then
    echo "direct wasm error did not preserve source provenance" >&2
    cat "$tmp/unsupported.err" >&2
    exit 1
fi

echo "direct wasm: passed"
