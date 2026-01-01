#!/bin/bash
# Test the self-hosted compiler on the test suite

# Detect platform
case "$(uname -s)" in
    Darwin)
        LANGOS=${LANGOS:-macos}
        ;;
    *)
        LANGOS=${LANGOS:-linux}
        ;;
esac

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

    if $COMPILER "$f" -o out/test_$name.s 2>/dev/null && \
       as out/test_$name.s -o out/test_$name.o 2>/dev/null && \
       ld out/test_$name.o -o out/test_$name 2>/dev/null; then
        ./out/test_$name >/dev/null 2>&1
        result=$?
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
