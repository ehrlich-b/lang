# Devlog 0016: Closure System Hardening

**Date**: 2025-12-28

## The Goal

Continue test hardening sprint, now targeting closures. Created 8 new tests, found and fixed 1 major bug.

## The Bug: Nested Lambda Captures

**Problem**: Nested lambdas couldn't capture variables from enclosing closures.

```lang
func example() i64 {
    var a i64 = 5;
    var b i64 = 3;

    var outer closure() i64 = fn() i64 {
        // Inner lambda tries to use a and b
        var inner closure() i64 = fn() i64 { return a * b; };
        return inner();
    };

    return outer();  // Should return 15, but crashed!
}
```

The inner lambda's body uses `a` and `b`, but they're not locals in the inner scope - they're captures of the outer closure.

**Root Cause**: Two issues:

1. **Capture analysis didn't walk into nested lambdas**. When analyzing outer's captures, the inner lambda body was skipped. So `a` and `b` weren't captured by outer at all.

2. **No parent capture propagation**. Even if outer captured `a` and `b`, the inner lambda had no way to know they existed in outer's closure struct.

**Fix**:

1. Modified `analyze_captures_expr` to walk into nested lambda bodies (instead of skipping):
```lang
} else if k == NODE_LAMBDA_EXPR {
    // Walk into nested lambda to find transitive captures
    analyze_captures_block(lambda_expr_body(expr));
}
```

2. Added parent capture tracking:
```lang
// When processing a nested lambda inside a closure:
cg_parent_captures = cg_closure_captures;
cg_parent_capture_count = cg_closure_capture_count;

// During capture analysis, check parent captures:
var parent_idx = find_in_parent_captures(name, name_len);
if parent_idx >= 0 {
    // Mark as "from parent" with offset = -1
    add_capture(name, name_len, 0 - 1, parent_type);
}
```

3. During closure creation, copies from parent closure:
```lang
if outer_offset == (0 - 1) {
    // Load from parent closure struct
    emit("mov ");
    emit_int(cg_closure_ptr_offset);
    emit("(%rbp), %rcx");
    emit("mov ");
    emit_int(parent_offset);
    emit("(%rcx), %rbx");
}
```

4. Fixed `lambda_has_captures()` to also check parent captures (prevents incorrect double-wrapping).

## New Tests

| Test | Description |
|------|-------------|
| 199_closure_nested_scope | Captures from multiple nested scopes |
| 200_closure_param_capture | Capture function parameters |
| 201_closure_shared_capture | Multiple closures share captured variables |
| 202_closure_in_loop | Closures created inside loops |
| 203_closure_many_captures | Stress test with 10 captures |
| 204_closure_nested_lambda | Lambda inside lambda (the bug!) |
| 205_closure_capture_pointer | Capture pointer and struct pointer |
| 206_closure_in_struct | Store closures in struct fields |

## Status

- 135 tests passing (was 127)
- Fixed point verified
- Major nested closure bug fixed
- Next: sum types edge cases
