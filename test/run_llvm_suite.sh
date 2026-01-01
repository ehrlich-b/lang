#!/bin/bash
# Test the LLVM backend on the test suite

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

# Portable timeout (GNU timeout on Linux, gtimeout on Mac, or none)
do_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then
        timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then
        gtimeout "$secs" "$@"
    else
        "$@"  # No timeout available
    fi
}

# Use COMPILER from environment, or default to ./out/lang
COMPILER=${COMPILER:-./out/lang}
passed=0
failed=0

for f in test/suite/*.lang; do
    name=$(basename "$f" .lang)

    # Check for //ignore marker
    if head -1 "$f" | grep -q '//ignore'; then
        echo "SKIP $name (ignored)"
        continue
    fi

    # Check for platform-specific markers
    if head -3 "$f" | grep -q '//linux'; then
        if [ "$LANGOS" != "linux" ]; then
            echo "SKIP $name (linux only)"
            continue
        fi
    fi
    if head -3 "$f" | grep -q '//macos'; then
        if [ "$LANGOS" != "macos" ]; then
            echo "SKIP $name (macos only)"
            continue
        fi
    fi

    expected=$(head -1 "$f" | grep -o '[0-9]*')

    # Compile to LLVM IR, then run
    # Use clang for tests marked //clang (inline asm), lli (interpreter) for rest
    if LANGBE=llvm $COMPILER "$f" -o out/test_$name.ll 2>/dev/null; then
        if head -3 "$f" | grep -q '//clang'; then
            clang -O0 out/test_$name.ll -o out/test_$name 2>/dev/null
            ./out/test_$name >/dev/null 2>&1
            result=$?
        else
            do_timeout 1 lli out/test_$name.ll >/dev/null 2>&1
            result=$?
        fi
        if [ "$result" = "$expected" ]; then
            echo "PASS $name"
            passed=$((passed + 1))
        else
            echo "FAIL $name (expected $expected, got $result)"
            failed=$((failed + 1))
        fi
    else
        echo "FAIL $name (compile error)"
        failed=$((failed + 1))
    fi
done

echo ""
echo "Passed: $passed / $((passed + failed))"
if [ $failed -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "FAILED: $failed tests failed"
    exit 1
fi
