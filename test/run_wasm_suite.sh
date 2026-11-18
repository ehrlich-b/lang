#!/bin/bash
# Test the wasm target: compile each suite test with LANGOS=wasm, link with
# clang/wasm-ld, run under node via test/wasm_host.js, compare exit codes.
#
# Skips: //ignore, //linux, //macos (platform-specific).
# Set TESTS to a space-separated list of fixture paths to run a fragment.
#
# Requires: clang with a wasm32 target, wasm-ld (brew install lld), node.

set -o pipefail
cd "$(dirname "$0")/.." || exit 1

read -r -a tests <<< "${TESTS:-}"

for tool in clang wasm-ld node; do
    if ! command -v "$tool" &>/dev/null; then
        if [ "${#tests[@]}" -gt 0 ]; then
            echo "Cannot run selected Wasm tests: $tool not found" >&2
            exit 1
        fi
        echo "SKIP wasm suite: $tool not found"
        exit 0
    fi
done

# The wasm OS layer is the generic libc surface; the JS host provides it.
# std/os.lang is a generated dispatch file - save and restore the host's.
OS_LANG_ORIG=$(cat std/os.lang) || exit 1
suite_tmp=$(mktemp -d "${TMPDIR:-/tmp}/lang-wasm-suite.XXXXXX") || exit 1
cleanup() {
    printf '%s\n' "$OS_LANG_ORIG" > std/os.lang
    rm -rf "$suite_tmp"
}
trap cleanup EXIT
echo 'include "std/os/libc.lang"' > std/os.lang || exit 1

export COMPILER=${COMPILER:-./out/lang}
export LANGOS=wasm
export LANGBE=llvm
source "$(dirname "${BASH_SOURCE[0]}")/suite_workers.sh"

WASM_LDFLAGS="-Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined -Wl,-z,stack-size=8388608"
export WASM_LDFLAGS

run_one_test() {
    local f=$1 markers=$2 expected=$3 diagnostic=$4
    export LANG_SUITE_WORKER=1 JOBS=1
    local name=$(basename "$f" .lang)

    if [[ "$markers" == *i* ]]; then
        echo "SKIP $name (ignored)"; return 0
    fi
    if [[ "$markers" == *l* || "$markers" == *m* ]]; then
        echo "SKIP $name (platform-specific)"; return 0
    fi

    local tmpdir
    tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX") || return 1
    # Negative fixtures are passes only when compilation rejects with the
    # specified diagnostic; they do not increase the skip inventory.
    if [[ "$markers" == *r* ]]; then
        if LANG_CACHE="$tmpdir/.lang-cache" "$COMPILER" "$f" -o "$tmpdir/rejected.ll" >"$tmpdir/rejected.out" 2>&1; then
            echo "FAIL $name (accepted invalid representation)"; rm -rf "$tmpdir"; return 1
        fi
        if grep -Fq "$diagnostic" "$tmpdir/rejected.out"; then
            echo "PASS $name (rejected unsupported representation)"; rm -rf "$tmpdir"; return 0
        fi
        cat "$tmpdir/rejected.out"
        echo "FAIL $name (wrong rejection)"; rm -rf "$tmpdir"; return 1
    fi

    local outll="$tmpdir/test.ll"
    local outwasm="$tmpdir/test.wasm"

    local cerr="$tmpdir/compile.err"
    if ! LANG_CACHE="$tmpdir/.lang-cache" "$COMPILER" "$f" -o "$outll" >"$cerr" 2>&1; then
        cat "$cerr"
        rm -rf "$tmpdir"; echo "FAIL $name (compile error)"; return 1
    fi
    if ! clang --target=wasm32-unknown-unknown -nostdlib $WASM_LDFLAGS "$outll" -o "$outwasm" >"$cerr" 2>&1; then
        cat "$cerr"
        rm -rf "$tmpdir"; echo "FAIL $name (wasm link error)"; return 1
    fi
    node test/wasm_host.js "$outwasm" >"$cerr" 2>&1
    local result=$?
    if [ "$result" = "$expected" ]; then
        rm -rf "$tmpdir"; echo "PASS $name"; return 0
    else
        cat "$cerr"
        rm -rf "$tmpdir"; echo "FAIL $name (expected $expected, got $result)"; return 1
    fi
}
export -f run_one_test

results_file="$suite_tmp/results"
python3 test/suite_manifest.py -- "${tests[@]}" > "$suite_tmp/manifest" || exit 1
xargs -0 -n4 -P"$JOBS" bash -c 'run_one_test "$@"' _ < "$suite_tmp/manifest" > "$results_file" 2>&1
worker_status=$?

sort -t' ' -k2 "$results_file"
pass=$(grep -c '^PASS' "$results_file")
fail=$(grep -c '^FAIL' "$results_file")
skip=$(grep -c '^SKIP' "$results_file")
echo ""
echo "wasm suite: $pass passed, $fail failed, $skip skipped"
[ "$worker_status" = "0" ] && [ "$fail" = "0" ]
