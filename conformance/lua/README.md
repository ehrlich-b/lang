# Lua reader experiment

`example/lua/lua.lang` is a Lang reader plugin for a deliberately small Lua
5.4 subset: whole chunks of `assert` calls with comparisons of decimal integers,
unary minus, parentheses, and binary `+`, `-`, and `*`, plus semicolons and
line comments. Operators are evaluated in the generated program, not during
reading. The shared tokenizer currently treats a minus followed immediately by
digits as part of a number, so write binary subtraction with whitespace after
`-`. Long comments, strings, floating-point numbers, variables, calls other
than `assert`, and all other Lua syntax are rejected. The reader rejects long
comment openers conservatively, including those inside line comments.

Build a current compiler (`make verify`) and run the smoke test:

```
python3 conformance/lua/score.py --compiler out/bootstrap_verify/kernel2 --smoke --report ../lua-smoke.json
```

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

# Borders

The shared AST describes explicit typed operations, structures, functions,
loops, conditionals, matches and effects (`src/parser.lang`, `std/ast.lang`).
The gaps below mean there is no direct Lua-semantic node or implicit runtime
contract. They do **not** prove that these features are impossible to implement:
a reader can elaborate them to explicit data structures and target-side runtime
calls. This list is a preliminary analysis, not an exhaustive proof.

* Lua values and coercions: nil/boolean/numbers/byte strings/tables/functions/
  userdata/threads share a dynamic value domain, with Lua truthiness, numeric
  conversion and Lua-specific arithmetic; ordinary AST nodes have explicit
  types and operators. Tagged values, dispatch and checked conversions belong
  in a Lua runtime. Float/decimal/hex literals and integer overflow rules also
  need explicit lowering.
* Tables and metatables: heterogeneous keys, identity, array/hash behavior,
  metamethod dispatch, length, iteration order and weak tables have no direct
  shared-AST representation. They require runtime objects and operations.
* Functions, closures, lexical environments and varargs: closures with shared
  mutable upvalues, dynamic calls, tail calls, varargs and multiple return
  values require a representation and calling convention; one AST call/return
  does not carry Lua's variable-length result adjustment rules. Multiple
  assignment must preserve evaluation order and simultaneous assignment.
* Control and cleanup: `goto`/labels, generic/numeric for loops, to-be-closed
  variables, protected calls/errors and coroutine yield/resume need frontend
  lowering and runtime-defined cleanup, unwinding and resumable state. Lang's
  effects alone do not establish Lua's cleanup or coroutine lifetime semantics.
* Storage and library boundary: Lua's garbage collection, finalizers, weak
  references, environments/globals, modules, standard libraries, debug hooks,
  C API, file/process I/O and binary chunks are runtime/host contracts, not AST
  semantics. Host capabilities differ on Wasm.
* Lua lexing and source semantics: long strings/comments with arbitrary equals
  delimiters, byte escapes, all numeral forms and source diagnostics must be
  implemented by the reader. These are frontend gaps, not AST impossibilities.

The experiment currently implements none of these runtime-dependent features.
