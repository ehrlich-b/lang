#!/bin/bash
# Test the self-hosted compiler on the test suite

LANG1=./out/lang1
passed=0
failed=0

for f in test/suite/*.lang; do
    name=$(basename "$f" .lang)
    expected=$(head -1 "$f" | grep -o '[0-9]*')

    if $LANG1 "$f" -o out/test_$name.s 2>/dev/null && \
       as out/test_$name.s -o out/test_$name.o 2>/dev/null && \
       ld out/test_$name.o -o out/test_$name 2>/dev/null; then
        result=$(./out/test_$name 2>/dev/null; echo $?)
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
