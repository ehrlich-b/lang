#!/bin/bash
# Test the LLVM backend on the test suite
# Optimized with: lli --jit-kind=orc (13x faster) + parallel execution (5x faster)

set -o pipefail

# Cross-platform setup
case "$(uname -s)" in
    Darwin)
        # macOS - find Homebrew LLVM
        if [ -d "/opt/homebrew/opt/llvm/bin" ]; then
            export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
        elif [ -d "/usr/local/opt/llvm/bin" ]; then
            export PATH="/usr/local/opt/llvm/bin:$PATH"
        fi
        export LANGOS=${LANGOS:-macos}
        # Generate OS layer for macOS
        echo 'include "std/os/libc_macos.lang"' > std/os.lang
        ;;
    *)
        export LANGOS=${LANGOS:-linux}
        # Generate OS layer for Linux
        echo 'include "std/os/linux_x86_64.lang"' > std/os.lang
        ;;
esac

# Use COMPILER from environment, or default to ./out/lang
export COMPILER=${COMPILER:-./out/lang}

# Parallel jobs - default to nproc or 8
JOBS=${JOBS:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 8)}

# Portable timeout
do_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then
        timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then
        gtimeout "$secs" "$@"
    else
        "$@"
    fi
}
export -f do_timeout

# Check if lli supports ORC JIT (LLVM 10+)
LLI_JIT_FLAG=""
if lli --help 2>&1 | grep -q 'jit-kind'; then
    LLI_JIT_FLAG="--jit-kind=orc"
fi
export LLI_JIT_FLAG

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
    local outll="$tmpdir/test.ll"
    local outbin="$tmpdir/test"

    # Compile to LLVM IR
    if LANGBE=llvm $COMPILER "$f" -o "$outll" 2>/dev/null; then
        # Use clang for tests marked //clang (inline asm), lli for rest
        if head -3 "$f" | grep -q '//clang'; then
            clang -O0 "$outll" -o "$outbin" 2>/dev/null
            "$outbin" >/dev/null 2>&1
            result=$?
        else
            # Use ORC JIT for ~13x faster interpretation (if available)
            do_timeout 2 lli $LLI_JIT_FLAG "$outll" >/dev/null 2>&1
            result=$?
        fi
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
