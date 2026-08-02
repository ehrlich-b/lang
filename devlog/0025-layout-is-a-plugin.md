# 0025: Layout Is a Plugin Too

**Date:** 2026-08-02

## Summary

A fifth language: **minipy**, a Python subset. It's the first one whose block structure isn't written down anywhere in the token stream — it lives in the whitespace to the *left* of each line, which is precisely the part every other reader throws away.

```python
def collatz(n):
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n / 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps
```

Layout is the case people reach for when they want to argue that syntax *can't* be a plugin — that some languages need their own lexer. It doesn't, and the interesting part is why.

## The tokenizer did not have to change

`std/tok.lang` is deliberately whitespace-blind: it skips runs of spaces and newlines without recording them, and the C, minilisp, flow and forth readers all depend on that. The tempting move is to add INDENT/DEDENT to it, and that would have meant a bootstrap plus a new concept in a file four other readers share.

It isn't necessary. A token already carries its byte offset into the source (`tok_start`), and the offside rule needs exactly two facts:

- is this the first token on its line?
- what column does it start at?

Both are recoverable from that offset and the source buffer. So `py_lex` walks the ordinary token stream, recovers the columns, and emits the synthetic `NEWLINE` / `INDENT` / `DEDENT` tokens itself — which is exactly what CPython's tokenizer hands to its parser. Nothing shared was touched, so nothing else could break. **Layout is reader-local.** That's a stronger result than adding it to the tokenizer would have been.

Two nice consequences fall out of doing it over tokens rather than over text. A newline inside `( ... )` continues the line, because the scanner already tracks bracket depth. And a blank or comment-only line can't affect indentation, because after the comment pre-pass it contributes no tokens at all — Python's rule, for free, rather than as a special case.

The `#minipy{ ... }` block also takes its base indent from its own first line rather than assuming column 0, so the block can sit at whatever indentation the host file uses.

## Python's scopes vs lang's scopes

The one real semantic mismatch. Python scopes a name to the whole function no matter which branch assigns it; lang scopes a `var` to its enclosing block. So this, which is ordinary Python, has nowhere to put `s`:

```python
def sign(n):
    if n > 0:
        s = 1
    elif n < 0:
        s = -1
    else:
        s = 0
    return s
```

The reader collects every assigned name while parsing the body and declares them all at the top of the function. Faithful to Python, and it's the kind of thing a reader is *for* — the two languages disagree about scope, and the disagreement is resolved at read time rather than by asking either language to change.

## `continue` decides where the increment goes

`for i in range(...)` desugars to a `while`, and the obvious desugaring is wrong:

```
i = start
while i < limit:
    body
    i = i + step        # <- never runs after a `continue`
```

lang's `continue` jumps to the loop condition, so a bottom increment is skipped and a Python `continue` turns into a hang. Moving the step to the *top* of the body fixes it, at the cost of biasing the initial value by one step:

```
__lim = limit
i = start - step
while 1:
    i = i + step
    if i >= __lim: break
    body
```

Both range bounds are evaluated exactly once, as in Python. The step must be an integer literal, because which way the test points has to be known at read time.

## A variadic polymorphic builtin, lowered

`print` is the one thing needing a runtime, and it needs one because no single lang function can be variadic *and* polymorphic. The reader picks the call from each argument's syntax:

```python
print("primes <=", n, ": count", count)
```

becomes `py_str(...)`, `py_space()`, `py_int(n)`, ... , `py_nl()`. Which call an argument becomes is decided at read time from whether it was quoted. That's a builtin surviving lowering into a language that has neither of the properties it depends on.

## The tokenizer trap, again

`std/tok.lang` folds a `-` straight into a following digit, so `n -1` arrives as `n` and the single number `-1`, with no operator between. Forth's answer was to ban `-5` outright and require `0 5 -`; that isn't an option for a language people expect to write `i-1` in. minipy absorbs a negative-number literal in the additive rule, so `n - 1`, `n- 1`, `n -1` and `n-1` all mean the same thing.

This first showed up as `countdown(3)` returning `3` instead of `321`, because `range(n, 0, -1)` handed the step parser the *text* `-1` and the digit accumulator quietly turned it into `-29`. Loud symptom, silent cause — the usual shape.

`//` needed defusing too: floor division would otherwise be eaten as a lang line comment, taking the rest of the line with it. The comment pre-pass rewrites it to `/ `, which is length-preserving (byte positions *are* the block structure here) and means the same thing when every value is an i64.

## Errors are fatal

minipy refuses to emit a program if it reported a syntax error. That sounds obvious, but it's the opposite of what the surrounding machinery does, and testing it turned up a genuine broken window: the kernel's `cg_had_error` flag is set in **15 places and read in none**. A reader that fails to produce output is diagnosed — `error: reader 'minipy' returned no output` — and then the compile writes its output and exits 0 anyway. Fixed separately; see the next entry.

## Bounds

Every value is an i64, so there are no lists, dicts, string values, or floats — a string literal may only be an argument to `print`. No classes, lambdas, nested defs, closures, default or keyword arguments, imports, or exceptions; only `def` at the top level; `for` iterates `range(...)` only. Statements that would otherwise fall through to something quietly unrelated (`class`, `import`, `lambda`, `try`, `yield`, ...) are rejected by name. Chained comparisons (`a < b < c`) are rejected rather than silently mis-associated as `(a < b) < c`.

## In the polyglot

The polyglot is five languages now, and minipy has the job a scripting language actually has in a system like this one: drive the fast code and format the answer. Every call in `report` leaves the language it's written in.

```python
def report(n):
    lst = collect_primes(n)                    # flow's coroutine -> C -> forth
    count = lisp_to_int(ml_len(lst))           # minilisp, folding a cons list
    total = lisp_to_int(ml_sum(lst))
    print("primes <=", n, ": count", count, "sum", total, "digitsum", digit_sum(total))
    return total                               #                       ^ forth
```

Five surface syntaxes in one native binary, and no two agree on so much as where a block ends: parens, braces, `;`, `then`, and — in minipy — nothing but the column the line starts in.

Suite: 184/184.
