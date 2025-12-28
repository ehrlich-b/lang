# Devlog 0015: Effect System Hardening

**Date**: 2025-12-28

## The Goal

Test hardening sprint, starting with algebraic effects. Found and fixed 3 bugs while adding 8 new tests.

## Bug 1: Handle Block Bodies

**Problem**: Handle body was parsed as single expression only.

```lang
// This should work but didn't:
handle {
    var a i64 = do_effect();
    a + 100;
} with { ... }
```

**Fix**: Changed parser to always parse handle body as statements (like function bodies), and updated codegen to handle `NODE_BLOCK_STMT` for the body.

```lang
// parser.lang - parse handle body as statements
var stmts *u8 = alloc(LIMIT_STMTS_PER_BLOCK * 8);
while !parse_check(TOKEN_RBRACE) && !parse_is_at_end() {
    var stmt *u8 = parse_statement();
    // ...
}

// codegen.lang - handle block body
if node_kind(body) == NODE_BLOCK_STMT {
    gen_stmt(body);
} else {
    gen_expr(body);
}
```

## Bug 2: Zero-Arg Effects

**Problem**: For `effect Read() i64`, the handler `Read(k) => { resume k(val); }` was binding `k` as the value instead of the continuation.

The parser puts the first identifier in the value binding slot. But for zero-arg effects, there IS no value - the identifier should be the continuation.

**Fix**: In codegen, look up the effect declaration to check arity. If zero args and only one binding provided, swap it to be the continuation.

```lang
// Look up effect arity
var eff_decl *u8 = find_effect(eff_name, eff_name_len);
var eff_param_count i64 = effect_decl_param_type_count(eff_decl);

// For zero-arg effects, first binding is actually continuation
if eff_param_count == 0 && k_len == 0 && bind_len > 0 {
    k_ptr = bind_ptr;
    k_len = bind_len;
    bind_ptr = nil;
    bind_len = 0;
}
```

## Bug 3: Multiple Effect Types

**Problem**: Handler only dispatched to first case. Multiple effect types in same handler didn't work.

```lang
handle { use_read_and_write(); } with {
    Read(k) => { resume k(state); },    // Only this ran
    Write(n, k) => { resume k(0); }     // This was never called
}
```

**Fix**: Added effect name tracking and runtime dispatch.

1. Store effect name when performing: `__effect_name_ptr`, `__effect_name_len`
2. In handler, compare performed effect name against each case
3. Jump to matching case body

```asm
# Compare effect name with case name
movq __effect_name_len(%rip), %rax
cmpq $5, %rax                    # "Write" length
jne .Lnext
movq __effect_name_ptr(%rip), %rsi
leaq .str42(%rip), %rdi          # "Write" string
movq $5, %rcx
repe cmpsb
je .Lcase_write                  # Match!
```

## New Tests

| Test | Description |
|------|-------------|
| 191_effect_nested | Block bodies, multiple statements |
| 192_effect_multi_type | Multiple effect types (Read + Write) |
| 193_effect_deep_call | Effect through 3+ call frames (no resume) |
| 194_effect_deep_resume | Resume through deep call frames |
| 195_effect_in_loop | Perform inside while loop |
| 196_effect_handler_func | Handler factored into separate function |
| 197_effect_resume_expr | Resume with complex expressions |
| 198_effect_many_resume | 20 resumes in sequence (stress test) |

## Status

- 127 tests passing (was 119)
- Fixed point verified
- Next: closure edge cases
