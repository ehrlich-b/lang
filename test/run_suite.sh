#!/bin/bash
# Test suite runner for language
# Each test file should exit with 0 on success

set -e

COMPILER="./boot/lang0"
SUITE_DIR="test/suite"
OUT_DIR="out/test"

mkdir -p "$OUT_DIR"

# Build compiler first
make build >/dev/null

PASS=0
FAIL=0
TOTAL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Running test suite..."
echo ""

for test_file in "$SUITE_DIR"/*.lang; do
    if [ ! -f "$test_file" ]; then
        continue
    fi

    name=$(basename "$test_file" .lang)
    TOTAL=$((TOTAL + 1))

    # Extract expected exit code from first line comment: // expect: N
    expected=0
    first_line=$(head -1 "$test_file")
    if [[ "$first_line" =~ ^//\ expect:\ ([0-9]+) ]]; then
        expected="${BASH_REMATCH[1]}"
    fi

    # Compile
    if ! $COMPILER "$test_file" -o "$OUT_DIR/$name.s" 2>/dev/null; then
        echo -e "${RED}FAIL${NC} $name - compilation failed"
        FAIL=$((FAIL + 1))
        continue
    fi

    # Assemble
    if ! as "$OUT_DIR/$name.s" -o "$OUT_DIR/$name.o" 2>/dev/null; then
        echo -e "${RED}FAIL${NC} $name - assembly failed"
        FAIL=$((FAIL + 1))
        continue
    fi

    # Link
    if ! ld "$OUT_DIR/$name.o" -o "$OUT_DIR/$name" 2>/dev/null; then
        echo -e "${RED}FAIL${NC} $name - linking failed"
        FAIL=$((FAIL + 1))
        continue
    fi

    # Run and capture exit code
    set +e
    "$OUT_DIR/$name" >/dev/null 2>&1
    actual=$?
    set -e

    if [ "$actual" -eq "$expected" ]; then
        echo -e "${GREEN}PASS${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC} $name - expected exit $expected, got $actual"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "================================"
echo -e "Passed: ${GREEN}$PASS${NC} / $TOTAL"
if [ "$FAIL" -gt 0 ]; then
    echo -e "Failed: ${RED}$FAIL${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
