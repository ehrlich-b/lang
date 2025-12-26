# 0007 - AST Introspection

**Date:** 2025-12-25

## What landed

Added compile-time AST introspection to the macro system:

- `ast_to_string(expr)` - converts AST node to string representation at compile time
- `$@name` - unquote-string syntax to splice string values as string literals

Now you can write macros that know the text of their arguments:

```lang
macro get_name(expr) {
    var s *u8 = ast_to_string(expr);
    return ${ $@s };
}

var name *u8 = get_name(x + y);  // name = "(x + y)"
```

## The journey

This was trickier than expected. Several bugs:

1. **memcmp returns true on match, not 0** - I wrote `memcmp(...) == 0` like C, but our memcmp returns bool (1 for match). Spent a while debugging why ast_to_string wasn't being recognized.

2. **STRING_EXPR values include quotes** - The codegen's `write_ascii_string` expects strings WITH surrounding quotes (it strips them). But `ast_to_string` returned raw strings. Had to wrap the result in quotes when creating STRING_EXPR from `$@`.

3. **String literals in macros need interp support** - The interpreter didn't handle NODE_STRING_EXPR, so `var s = "hello"` in macro bodies returned 0.

## Thoughts

The macro system is getting real. We can now do things like:
- Assert macros that print the failing condition
- Debug macros that show "expr = value"
- Code generation with meaningful names

Next up: examples gallery to show off what's possible. Then Phase 3 (reader macros) for truly custom syntax.

The fixed point still passes. This compiler continues to eat itself successfully.
