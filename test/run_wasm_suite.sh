#!/bin/bash
# Test the wasm target: compile each suite test with LANGOS=wasm, link with
# clang/wasm-ld, run under node via test/wasm_host.js, compare exit codes.
#
# Skips: //ignore, //linux, //macos (platform-specific), //clang (effects -
# wasm has no stack switching, the compiler rejects them by design).
#
# Requires: clang with a wasm32 target, wasm-ld (brew install lld), node.

set -o pipefail
cd "$(dirname "$0")/.."

for tool in clang wasm-ld node; do
    if ! command -v $tool &>/dev/null; then
        echo "SKIP wasm suite: $tool not found"
        exit 0
    fi
done

# The wasm OS layer is the generic libc surface; the JS host provides it.
# std/os.lang is a generated dispatch file - save and restore the host's.
OS_LANG_ORIG=$(cat std/os.lang)
restore_os() { echo "$OS_LANG_ORIG" > std/os.lang; }
trap restore_os EXIT
echo 'include "std/os/libc.lang"' > std/os.lang

export COMPILER=${COMPILER:-./out/lang}
export LANGOS=wasm
export LANGBE=llvm
source "$(dirname "${BASH_SOURCE[0]}")/suite_workers.sh"

WASM_LDFLAGS="-Wl,--no-entry -Wl,--export-all -Wl,--allow-undefined -Wl,-z,stack-size=8388608"
export WASM_LDFLAGS

run_one_test() {
    local f=$1
    export LANG_SUITE_WORKER=1 JOBS=1
    local name=$(basename "$f" .lang)
    local tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/lang-test.XXXXXX")

    if head -1 "$f" | grep -q '//ignore'; then
        echo "SKIP $name (ignored)"; rm -rf "$tmpdir"; return 0
    fi
    if head -3 "$f" | grep -qE '//linux|//macos'; then
        echo "SKIP $name (platform-specific)"; rm -rf "$tmpdir"; return 0
    fi
    if head -3 "$f" | grep -q '//clang'; then
        echo "SKIP $name (effects - unsupported on wasm)"; rm -rf "$tmpdir"; return 0
    fi

    # Negative fixtures are passes only when compilation rejects with the
    # specified diagnostic; they do not increase the skip inventory.
    if head -1 "$f" | grep -q '^// reject: '; then
        local diagnostic=$(head -1 "$f" | sed 's@^// reject: @@')
        if LANGBE=llvm LANG_CACHE="$tmpdir/.lang-cache" $COMPILER "$f" -o "$tmpdir/rejected.ll" >"$tmpdir/rejected.out" 2>&1; then
            echo "FAIL $name (accepted invalid representation)"; rm -rf "$tmpdir"; return 1
        fi
        if grep -Fq "$diagnostic" "$tmpdir/rejected.out"; then
            echo "PASS $name (rejected unsupported representation)"; rm -rf "$tmpdir"; return 0
        fi
        cat "$tmpdir/rejected.out"
        echo "FAIL $name (wrong rejection)"; rm -rf "$tmpdir"; return 1
    fi

    local expected=$(head -1 "$f" | grep -o '[0-9]*')
    local outll="$tmpdir/test.ll"
    local outwasm="$tmpdir/test.wasm"

    local cerr="$tmpdir/compile.err"
    if ! LANG_CACHE="$tmpdir/.lang-cache" $COMPILER "$f" -o "$outll" 2>"$cerr"; then
        if grep -q 'not supported on the wasm target' "$cerr"; then
            rm -rf "$tmpdir"; echo "SKIP $name (effects - unsupported on wasm)"; return 0
        fi
        rm -rf "$tmpdir"; echo "FAIL $name (compile error)"; return 1
    fi
    if ! clang --target=wasm32-unknown-unknown -nostdlib $WASM_LDFLAGS "$outll" -o "$outwasm" 2>/dev/null; then
        rm -rf "$tmpdir"; echo "FAIL $name (wasm link error)"; return 1
    fi
    node test/wasm_host.js "$outwasm" >/dev/null 2>&1
    local result=$?
    rm -rf "$tmpdir"
    if [ "$result" = "$expected" ]; then
        echo "PASS $name"; return 0
    else
        echo "FAIL $name (expected $expected, got $result)"; return 1
    fi
}
export -f run_one_test

results_file=$(mktemp "${TMPDIR:-/tmp}/lang-results.XXXXXX")
if [ "${SEQUENTIAL:-0}" = "1" ]; then
    for f in test/suite/*.lang; do run_one_test "$f"; done > "$results_file" 2>&1
else
    printf '%s\n' test/suite/*.lang | xargs -P"$JOBS" -I{} bash -c 'run_one_test "$@"' _ {} > "$results_file" 2>&1
fi

sort -t' ' -k2 "$results_file"
pass=$(grep -c '^PASS' "$results_file")
fail=$(grep -c '^FAIL' "$results_file")
skip=$(grep -c '^SKIP' "$results_file")
rm -f "$results_file"
echo ""
echo "wasm suite: $pass passed, $fail failed, $skip skipped"
[ "$fail" = "0" ]
