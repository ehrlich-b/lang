# Lua reader experiment

`example/lua/lua.lang` is a Lang reader plugin for a deliberately small Lua
5.4 subset: whole chunks of `assert` calls with comparisons of decimal integers,
unary minus, parentheses, and binary `+`, `-`, and `*`, plus semicolons and
line comments with LF, CR, CRLF, or LFCR endings. Operators are evaluated in the generated program, not during
reading. The shared tokenizer currently treats a minus followed immediately by
digits as part of a number, so write binary subtraction with whitespace after
`-`. Long comments, strings, floating-point numbers, variables, calls other
than `assert`, and all other Lua syntax are rejected. The reader rejects long
comment openers conservatively, including those inside line comments.

Build a current compiler (`make verify`) and run the smoke test:

```
python3 conformance/lua/score.py --compiler out/bootstrap_verify/kernel2 --smoke --report ../lua-smoke.json
```

The scorer runs the reader on native LLVM regardless of the target selected
for the generated program or the caller's `LANGBE` and `LANGOS` environment.
When invoking `read` directly, select a native host backend, for example with
`LANGBE=llvm LANGOS=linux` on Linux.

For the official corpus replace `--smoke` with nothing. The included archive is
the unmodified [Lua 5.4.8 official test suite](https://www.lua.org/tests/),
SHA-256 `9581d5a7c39ffbf29b8ccde2709083c380f7bbddbd968dcb15712d2f2e33f4e5`.
Lua is distributed under the [Lua license](https://www.lua.org/license.html).
The scorer reads every `.lua` file in the archive as an independent whole
chunk. It records reader, compiler, link, and execution failures separately
for LLVM and direct Wasm; it does not execute the Lua suite's `all.lua`
harness, provide its libraries or shared state, or treat unsupported files as
skips. Therefore this measures whole-file compatibility under an intentionally
limited host, not individual assertions or a full official harness run.

# Borders: Lua 5.4 versus the shared AST

This inventory covers the language grammar and semantics in the [Lua 5.4
reference manual](https://www.lua.org/manual/5.4/manual.html) sections 2, 3
and 9, compared with the node layouts in `src/parser.lang` and the builder
API in `std/ast.lang`. “No direct node” means the Lua behavior is not
specified by one shared AST node; it does not mean it is impossible to
implement. A reader can lower constructs to ordinary nodes and a Lua runtime.
These are borders of the shared AST, not claims that the current reader
implements the proposed lowerings. The inventory is organized by every grammar
production and the cross-cutting semantic contracts that affect them.

## Grammar inventory

| Lua construct | Shared AST border and required lowering |
| --- | --- |
| chunk, block, `do`, empty statement | Program, function and block nodes provide structure; execute a chunk as a function with an explicit environment and result convention. Empty statements disappear. Chunk loading and external `_ENV` are runtime contracts. |
| names, local declarations and scope | Variables and identifiers exist, but Lua's free-name rewrite through the lexically visible `_ENV`, local visibility and shadowing, and initialization before locals enter scope must be resolved by the reader. `<const>` needs a frontend write check; `<close>` needs the cleanup protocol below. |
| assignment and variable lists | `assign` has one target and value. Evaluate indexed targets and right sides in Lua order, adjust the expression list, then write all destinations; use temporaries so overlapping assignments work. Global and table writes must dispatch through the Lua runtime. |
| calls, statement calls, arguments and method `:` | `call` exists, but dynamic callable values, `__call`, colon receiver evaluation exactly once, argument list adjustment and string/table argument sugar require lowering and runtime dispatch. A call statement discards results. |
| labels and `goto` | There is no general label/goto node; validate Lua's scope restrictions and lower control flow to a state machine or equivalent, including closing variables on exits. Labeled loop breaks are not arbitrary goto. |
| `break`, `return` | Break and single-value return nodes exist. Lua return lists, result adjustment and cleanup on every exit require explicit lowering; preserve tail-call behavior where Lua requires it. |
| `if`/`elseif`/`else`, `while`, `repeat` | If and while nodes provide control flow, but tests need Lua truthiness and possible runtime evaluation. Lower elseif to nested if and repeat to a loop that preserves the body's local scope through its condition. |
| numeric `for` | No Lua numeric-for node: evaluate bounds and step once and implement Lua's integer/float loop rules, conversion, zero-step error, termination and loop-variable scope explicitly. |
| generic `for` | No Lua iterator-for node: adjust the initializer to iterator, state, control and closing values; call the iterator, assign its results and close the fourth value on exit as specified by Lua 5.4. |
| function declarations, local function, function expressions, parameters | Function and lambda nodes exist, but Lua closures are dynamic values with shared mutable upvalues and lexical lifetime. Lower recursive local binding, dotted names and method-definition sugar, and package parameters and captured cells in a runtime calling convention. |
| varargs `...`, expression lists, returns | AST calls and returns do not encode Lua's context-dependent expansion, truncation or nil padding. Represent variable result sequences explicitly, including parentheses suppressing expansion, varargs, the final table list field, calls, assignment and return. |
| nil, booleans, numerals, strings | Literal nodes exist but do not supply a common Lua value domain. Preserve integer versus float and Lua parsing/rounding; Lua strings are arbitrary byte sequences including embedded NUL, not merely C strings. Box values and carry lengths. |
| variable/index/field expressions | AST identifiers, index and field nodes exist; Lua table lookup, absent keys, key normalization and `__index`/`__newindex` behavior require runtime operations. Dot field syntax is a string-key lookup. |
| table constructors and fields | No Lua heterogeneous table constructor node: allocate a Lua table, evaluate and store keyed, named and list fields with Lua's constructor and final-expression expansion rules. Table length and traversal are runtime semantics. |
| unary and binary operators | Generic operator nodes do not specify Lua's type dispatch, coercions, metamethods or errors. Lower arithmetic, floor division, modulo, exponentiation, bitwise operations and shifts, concatenation, length, equality and ordering to Lua operations. `and`/`or` short circuit and return operands, while `not` uses Lua truthiness. Honor Lua precedence and associativity in the reader. |
| parentheses, separators and lexical forms | Grouping and source parsing belong to the reader. Implement Lua comments and long-bracket levels, escapes and byte strings, numeral forms, reserved names and token boundaries. Parentheses can change result count, so they cannot always be discarded before list adjustment. |

## Cross-cutting semantic and host borders

* **Values and operations (manual 2.1, 3.4):** Lua has nil, booleans,
  integer and float numbers, byte strings, tables, functions, userdata and
  threads in one dynamic domain. Lua truthiness, number/string coercion,
  wrapping integer arithmetic, floor division, shifts, equality including
  integer/float comparison, and error conditions require a tagged value and
  Lua operations. AST literals and typed operators alone do not provide these.
* **Tables and metatables (2.1, 2.4):** reference identity, key restrictions
  and normalization, deletion by nil, length borders, raw operations, and
  metamethod lookup and dispatch (including protection and weak-table modes)
  are runtime object contracts. AST index and field access do not imply them.
* **Environments and closures (2.2, 3.2, 3.5):** each free name uses the
  visible `_ENV`; closures share mutable captured locals and outlive scopes.
  Explicit environment objects, upvalue cells and their lifetimes are needed;
  the existence of an AST lambda is not a Lua closure ABI.
* **Errors and closing (2.3, 3.3.8):** arbitrary error objects, protected calls,
  stack unwinding and `<close>` variables need Lua's reverse-order `__close`
  calls on normal and exceptional exits, including error propagation during
  closing. Effects or ordinary returns alone do not establish this protocol.
* **Coroutines (2.6):** thread identity, yield/resume, status and suspended
  stacks across calls need resumable state and a runtime protocol. An effect
  node alone does not promise Lua coroutine behavior or its boundary rules.
* **Memory management (2.5):** reachability, incremental/generational collection,
  weak references, finalization and resurrection require a collector and
  object lifetime policy; no AST node provides Lua's garbage collector.
* **Embedding and libraries (manual 4–6):** C API stack and userdata, debug
  hooks, module loading, binary chunks, standard libraries, I/O and host
  services are runtime/host interfaces rather than syntax nodes. They need
  implementations or explicit host capability limits on LLVM and Wasm.
  They are listed as borders, not as claims that all library functions are
  language constructs or that a different AST node would implement them.

The experiment currently implements none of these runtime-dependent features.
