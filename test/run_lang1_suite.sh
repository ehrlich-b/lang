#!/bin/bash
# Test the self-hosted compiler on the test suite (x86-64 assembly backend)
# Optimized with parallel execution
#
# NOTE: This suite only works on Linux x86-64 (uses as/ld for ELF binaries).
# On macOS, use run_llvm_suite.sh instead.

set -o pipefail

# Detect platform
case "$(uname -s)" in
    Darwin)
        echo "ERROR: run_lang1_suite.sh only works on Linux (uses x86-64 assembly + ELF linking)"
        echo "Use ./test/run_llvm_suite.sh on macOS instead."
        exit 1
        ;;
    *)
        export LANGOS=${LANGOS:-linux}
        ;;
esac

# Use COMPILER from environment, or default to ./out/lang
export COMPILER=${COMPILER:-./out/lang}

# Parallel jobs - default to nproc or 8
JOBS=${JOBS:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 8)}

# Run a single test - called by xargs
run_one_test() {
    local f=$1
    local name=$(basename "$f" .lang)
    local tmpdir=$(mktemp -d)

    # Check for //ignore marker
    if head -1 "$f" | grep -q '//ignore'; then
        echo "SKIP $name (ignored)"
        rm -rf "$tmpdir"
        return 0
    fi

    # Check for platform-specific markers
    if head -3 "$f" | grep -q '//linux'; then
        if [ "$LANGOS" != "linux" ]; then
            echo "SKIP $name (linux only)"
            rm -rf "$tmpdir"
            return 0
        fi
    fi
    if head -3 "$f" | grep -q '//macos'; then
        if [ "$LANGOS" != "macos" ]; then
            echo "SKIP $name (macos only)"
            rm -rf "$tmpdir"
            return 0
        fi
    fi

    local expected=$(head -1 "$f" | grep -o '[0-9]*')
    local outs="$tmpdir/test.s"
    local outo="$tmpdir/test.o"
    local outbin="$tmpdir/test"

    if $COMPILER "$f" -o "$outs" 2>/dev/null && \
       as "$outs" -o "$outo" 2>/dev/null && \
       ld "$outo" -o "$outbin" 2>/dev/null; then
        "$outbin" >/dev/null 2>&1
        result=$?
        rm -rf "$tmpdir"
        if [ "$result" = "$expected" ]; then
            echo "PASS $name"
            return 0
        else
            echo "FAIL $name (expected $expected, got $result)"
            return 1
        fi
    else
        rm -rf "$tmpdir"
        echo "FAIL $name (compile error)"
        return 1
    fi
}
export -f run_one_test

# Check for sequential mode
if [ "$SEQUENTIAL" = "1" ]; then
    JOBS=1
fi

# Run tests
results_file=$(mktemp)

if [ "$JOBS" -gt 1 ]; then
    # Parallel execution
    printf '%s\n' test/suite/*.lang | xargs -P"$JOBS" -I{} bash -c 'run_one_test "$@"' _ {} > "$results_file" 2>&1
else
    # Sequential execution (for debugging or SEQUENTIAL=1)
    for f in test/suite/*.lang; do
        run_one_test "$f"
    done > "$results_file" 2>&1
fi

# Count results (grep -c returns 1 if no matches, so handle that)
passed=$(grep -c '^PASS' "$results_file" 2>/dev/null) || passed=0
failed=$(grep -c '^FAIL' "$results_file" 2>/dev/null) || failed=0
skipped=$(grep -c '^SKIP' "$results_file" 2>/dev/null) || skipped=0

# Show results
cat "$results_file"
rm -f "$results_file"

echo ""
echo "Passed: $passed / $((passed + failed))"
if [ "$skipped" -gt 0 ]; then
    echo "Skipped: $skipped"
fi
if [ $failed -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "FAILED: $failed tests failed"
    exit 1
fi
