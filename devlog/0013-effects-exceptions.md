# 0013: Algebraic Effects - Exceptions MVP

**Date**: 2024-12-27

## Summary

Implemented Phase 5: Algebraic Effects with a working exceptions system. No resume support yet (one-way jumps only), but the foundation is in place.

## What Works

```lang
effect Fail(i64) i64

func might_fail(x i64) i64 {
    if x < 0 { return perform Fail(x); }
    return x * 2;
}

var result i64 = handle { might_fail(0 - 5) } with {
    return(v) => v,
    Fail(e) => 0 - e  // handler receives effect argument
};
// result = 5
```

## Implementation

**Lexer**: Added `effect`, `perform`, `handle`, `with`, `resume` tokens.

**Parser**:
- `effect Name(types) ReturnType` - effect declaration
- `perform Effect(args)` - trigger effect
- `handle { body } with { return(v) => ..., Effect(e) => ... }` - handler

**Codegen**: Uses setjmp/longjmp style:
- Handler saves RBP/RSP and sets jump target address
- `perform` restores RBP/RSP and jumps to handler
- Effect argument passed via global `__effect_value`

## Limitations

- Single handler at a time (no handler stack)
- No resume support (exceptions only, not delimited continuations)
- Effects not type-checked (any perform goes to active handler)

## What's Next

For full algebraic effects with resume:
1. Handler stack for nesting
2. State machine transform (CPS or similar)
3. `resume k(value)` to continue from perform site

But exceptions alone are quite useful for error handling patterns.

## Test

`test/suite/188_effect_exception.lang` - 3 test cases covering normal completion, exception triggered, and exception with value.

## Files Changed

- `src/lexer.lang`: Effect tokens
- `src/parser.lang`: Effect parsing, `buf_eq_str()` helper
- `src/codegen.lang`: Effect registry, handler runtime, codegen
- `src/limits.lang`: `LIMIT_EFFECTS`
- `TODO.md`: Phase 5 status update
