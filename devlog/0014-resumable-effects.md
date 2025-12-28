# Devlog 0014: Resumable Effects

**Date**: 2025-12-28

## The Feature

Added `resume k(value)` support to algebraic effects. Handlers can now catch effect invocations and resume them:

```lang
effect Yield(i64) i64

func gen() i64 {
    var x i64 = perform Yield(1);  // x gets resume value
    x = perform Yield(2);
    return x + 100;
}

func main() i64 {
    var result i64 = handle { gen() } with {
        return(v) => v,
        Yield(n, k) => {
            total = total + n;
            resume k(n * 10);  // resume with n*10
        }
    };
    // result = 120 (second resume with 20, plus 100)
}
```

## The Bug

Single yields worked. Multiple yields caused segfaults or infinite loops. GDB showed `rip = 0x2a` - we were executing the effect value (42) as code.

The culprit: stack frame collision.

When `perform` jumped to the handler, we restored both handler's `rbp` AND `rsp`. The handler's rsp was set before calling the effectful function. So when the handler did push/pop for expression evaluation, it wrote to the same memory location as the effectful function's return address.

```
main's stack:
  -16(%rbp): effect value local
  -24(%rbp): continuation local
  -32(%rbp): bottom of main's locals
  -40(%rbp): gen's return address  <-- OVERWRITTEN by handler's push!

gen's stack:
  return addr at gen's rbp + 8 = main's rbp - 40
```

Handler push wrote to `main_rsp - 8 = main_rbp - 40`, exactly where gen's return address lived.

## The Fix

One line removed:

```lang
// Before (broken):
emit_line("    movq __handler_rbp(%rip), %rbp");
emit_line("    movq __handler_rsp(%rip), %rsp");  // THIS LINE

// After (fixed):
emit_line("    movq __handler_rbp(%rip), %rbp");
// Don't restore rsp - keep it at effectful function's stack
```

By only restoring handler's rbp (needed to access handler's locals), but keeping rsp at the effectful function's stack position, push/pop in the handler uses memory below gen's frame instead of overwriting gen's return address.

## Lessons

1. **Stack frame diagrams save hours.** Drawing out exactly what's at each address revealed the collision immediately.

2. **GDB's register dump is gold.** Seeing `rip = 0x2a = 42` (the effect value) instantly told us the return address was corrupted with effect data.

3. **Resumable continuations are subtle.** We're essentially maintaining two interleaved stack frames (handler and effectful function) that must not collide.

## Status

- 119 tests passing
- Fixed point verified
- Phase 5 algebraic effects complete
- Next: test hardening sprint before kernel split
