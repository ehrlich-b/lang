#!/bin/bash
# Test the LLVM backend on the test suite

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

    expected=$(head -1 "$f" | grep -o '[0-9]*')

    # Compile to LLVM IR, then use clang
    if LANGBE=llvm $COMPILER "$f" -o out/test_$name.ll 2>/dev/null && \
       clang -O0 out/test_$name.ll -o out/test_$name 2>/dev/null; then
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
fi
