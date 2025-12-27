#!/bin/bash
# Test standalone compiler generation with -c flag
# This verifies that standalone compilers work without .lang-cache

set -e

echo "=== Standalone Compiler Test ==="

# Use lang_next or lang (whichever exists)
LANG_COMPILER="./out/lang"
if [ -f "./out/lang_next" ]; then
    LANG_COMPILER="./out/lang_next"
fi

# Build the standalone lisp compiler
echo "Building standalone lisp compiler..."
$LANG_COMPILER -c lisp std/core.lang example/lisp/lisp.lang -o /tmp/standalone_lisp.s
as /tmp/standalone_lisp.s -o /tmp/standalone_lisp.o
ld /tmp/standalone_lisp.o -o /tmp/standalone_lisp

# Create a test lisp program
cat > /tmp/test_standalone.lisp << 'EOF'
(defun main (argc argv) 42)
EOF

# Remove .lang-cache to prove we don't need it
rm -rf .lang-cache

# Compile with standalone compiler
echo "Compiling lisp program with standalone compiler..."
/tmp/standalone_lisp /tmp/test_standalone.lisp -o /tmp/test_standalone.s

# Assemble and link
as /tmp/test_standalone.s -o /tmp/test_standalone.o
ld /tmp/test_standalone.o -o /tmp/test_standalone

# Run and check exit code (disable set -e for this)
set +e
/tmp/test_standalone
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -eq 42 ]; then
    echo "PASS: Standalone compiler works (exit code 42)"
    exit 0
else
    echo "FAIL: Expected exit code 42, got $EXIT_CODE"
    exit 1
fi
