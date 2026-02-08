#!/bin/bash
# End-to-end test for Zig capture pipeline.
# Requires: patched Zig in /tmp/lang-patches-zig-*/zig-out/bin/zig
#           kernel in /tmp/kernel_fresh (or build one)
#
# Usage: ./scripts/test-zig-capture.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXTRACT="$SCRIPT_DIR/extract-zig-ast.sh"

# Find patched Zig
ZIG=$(ls /tmp/lang-patches-zig-*/zig-out/bin/zig 2>/dev/null | head -1)
if [ -z "$ZIG" ]; then
    echo "FAIL: No patched Zig found. Run ./scripts/apply-patches.sh first." >&2
    exit 1
fi

# Find or build kernel
KERNEL="/tmp/kernel_fresh"
if [ ! -f "$KERNEL" ]; then
    echo "Building fresh kernel..."
    LANGBE=llvm LANGOS=macos ./out/lang std/core.lang src/version_info.lang \
        src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang \
        src/ast_emit.lang src/sexpr_reader.lang src/kernel_main.lang -o /tmp/kernel_fresh.ll
    clang -O2 /tmp/kernel_fresh.ll -o "$KERNEL"
fi

PASS=0
FAIL=0
TMPDIR=$(mktemp -d)

run_test() {
    local name="$1"
    local zig_src="$2"
    local expected_exit="$3"
    local expected_output="${4:-}"

    local c_out="$TMPDIR/${name}.c"
    local ast_out="$TMPDIR/${name}.ast"
    local ll_out="$TMPDIR/${name}.ll"
    local bin_out="$TMPDIR/${name}"

    # Compile through patched Zig
    LANG_AST=1 "$ZIG" build-obj "$zig_src" -ofmt=c -target aarch64-macos \
        -femit-bin="$c_out" -OReleaseFast 2>/dev/null || {
        echo "FAIL: $name (zig compile failed)"
        FAIL=$((FAIL + 1))
        return
    }

    # Extract AST
    "$EXTRACT" "$c_out" > "$ast_out" || {
        echo "FAIL: $name (extract failed)"
        FAIL=$((FAIL + 1))
        return
    }

    # Run through kernel
    LANGBE=llvm LANGOS=macos "$KERNEL" "$ast_out" -o "$ll_out" 2>/dev/null || {
        echo "FAIL: $name (kernel failed)"
        FAIL=$((FAIL + 1))
        return
    }

    # Compile LLVM IR
    clang -O2 "$ll_out" -o "$bin_out" 2>/dev/null || {
        echo "FAIL: $name (clang failed)"
        FAIL=$((FAIL + 1))
        return
    }

    # Run and check
    local actual_output actual_exit
    actual_output=$("$bin_out" 2>&1) && actual_exit=0 || actual_exit=$?

    if [ "$actual_exit" -ne "$expected_exit" ]; then
        echo "FAIL: $name (exit $actual_exit, expected $expected_exit)"
        FAIL=$((FAIL + 1))
        return
    fi

    if [ -n "$expected_output" ] && [ "$actual_output" != "$expected_output" ]; then
        echo "FAIL: $name (output mismatch)"
        echo "  expected: $expected_output"
        echo "  actual:   $actual_output"
        FAIL=$((FAIL + 1))
        return
    fi

    echo "PASS: $name"
    PASS=$((PASS + 1))
}

# --- Test cases ---

# 1. Simple arithmetic
cat > "$TMPDIR/arith.zig" << 'EOF'
export fn main() i64 {
    return 30 +% 12;
}
EOF
run_test "arithmetic" "$TMPDIR/arith.zig" 42

# 2. Factorial (while loop)
cat > "$TMPDIR/fact.zig" << 'EOF'
fn factorial(n: i64) i64 {
    var result: i64 = 1;
    var i: i64 = 1;
    while (i <= n) {
        result *%= i;
        i +%= 1;
    }
    return result;
}
export fn main() i64 {
    return factorial(5);
}
EOF
run_test "factorial" "$TMPDIR/fact.zig" 120

# 3. Struct field access
cat > "$TMPDIR/struct.zig" << 'EOF'
const Point = struct { x: i64, y: i64 };
export fn add_points(ax: i64, ay: i64, bx: i64, by: i64) i64 {
    const p = Point{ .x = ax, .y = ay };
    const q = Point{ .x = bx, .y = by };
    return p.x +% q.x +% p.y +% q.y;
}
export fn main() i64 {
    return add_points(10, 20, 30, 40);
}
EOF
run_test "struct" "$TMPDIR/struct.zig" 100

# 4. Enum + switch
cat > "$TMPDIR/switch.zig" << 'EOF'
const Op = enum(i64) { add, sub, mul };
export fn calc(op: i64, a: i64, b: i64) i64 {
    return switch (@as(Op, @enumFromInt(op))) {
        .add => a +% b,
        .sub => a -% b,
        .mul => a *% b,
    };
}
export fn main() i64 {
    const r1 = calc(0, 10, 5);
    const r2 = calc(1, 20, 7);
    const r3 = calc(2, 3, 4);
    return r1 +% r2 +% r3;
}
EOF
run_test "switch" "$TMPDIR/switch.zig" 40

# 5. String literal + extern call
cat > "$TMPDIR/hello.zig" << 'EOF'
extern fn write(fd: c_int, buf: [*]const u8, count: usize) isize;
export fn main() i64 {
    const msg = "Hello, World!\n";
    _ = write(1, msg.ptr, msg.len);
    return 0;
}
EOF
run_test "hello_world" "$TMPDIR/hello.zig" 0 "Hello, World!"

# 6. FizzBuzz (multi-function, strings, control flow)
cat > "$TMPDIR/fizzbuzz.zig" << 'ZIGEOF'
extern fn write(fd: c_int, buf: [*]const u8, count: usize) isize;

fn fizzbuzz_type(n: i64) i64 {
    const div3 = @rem(n, 3) == 0;
    const div5 = @rem(n, 5) == 0;
    if (div3 and div5) return 0;
    if (div3) return 1;
    if (div5) return 2;
    return 3;
}

export fn main() i64 {
    var count: i64 = 0;
    var i: i64 = 1;
    while (i <= 30) {
        const t = fizzbuzz_type(i);
        if (t == 0) {
            _ = write(1, "FizzBuzz\n".ptr, 9);
            count +%= 1;
        } else if (t == 1) {
            _ = write(1, "Fizz\n".ptr, 5);
        } else if (t == 2) {
            _ = write(1, "Buzz\n".ptr, 5);
        }
        i +%= 1;
    }
    return count;
}
ZIGEOF
run_test "fizzbuzz" "$TMPDIR/fizzbuzz.zig" 2

# --- Summary ---
rm -rf "$TMPDIR"
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
