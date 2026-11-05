# Scheme: a target-owned evaluation machine

Build the native compiler from the reader and embedded runtime:

```sh
make init
make generate-os-layer LANGLIBC=libc
LANGBE=llvm out/lang compiler scheme example/scheme/scheme.lang \
  --runtime example/scheme/runtime.lang -o out/schemec
out/schemec example/scheme/basic.scm -o out/basic.ll
clang -O0 out/basic.ll -o out/basic
out/basic
```

`scheme.lang` and `reader.lang` parse the entire input at compiler-build/use
time, consume comments and dotted/quoted data, and emit shared AST constructors
with source spans. The emitted native program constructs immutable code data;
`runtime.lang` evaluates that data in the **target process**. Neither Python nor
Chibi evaluates the submitted Scheme. Python only orchestrates native compilation
and collects target-produced comparisons.

The supported subset includes lexical closures, variadic and dotted parameters,
first-class calls, definitions and mutation, `if`, `begin`, short-circuit `and`
and `or`, `cond` (including `=>`), named `let`, `let*`, `letrec` and `letrec*`.
Pairs, symbols, booleans, vectors as literal data, ASCII strings/characters,
bounded integers, approximate real/rational arithmetic and a selection of list,
number, string and character procedures are implemented. Imports currently select
no additional libraries. Unsupported operations fail rather than returning a
substitute value; this is a partial implementation, not an R7RS claim.

## Shared AST borders and proper tail calls

The shared AST's ordinary call node does not promise constant-stack calls at O0,
including mutual and indirect calls. No Scheme rule or new node was added to the
kernel. Instead the reader chooses a runtime representation whose `sc_eval`
loop replaces the current expression and environment in all implemented tail
positions, including `apply`. Recursive native evaluator calls occur only for
non-tail operands and preceding body expressions. Closures capture heap-owned
lexical environments, which survive tail transfers.

The runtime owns a mark/sweep object pool and an explicit stack of roots pointing
to active evaluator locals. Code, interned symbols and the global environment are
roots. Dead argument lists and call frames are reused. Collection runs at machine
boundaries, with every live intermediate registered. Strings' backing storage is
process-lived; string-heavy unbounded programs need an additional ownership rule.
The root stack is limited to 65,536 entries. Non-tail recursion is not promised
constant space. Cyclic lists are detected by `list?`; arbitrary cyclic printing
and equality remain unsupported.

`tail.scm` executes ten million mutual, indirect calls, alternating ordinary calls
and nested `apply`. `check.py --tail` links the same IR at O0 and O2 and runs each with
a 256 KiB native stack limit. O0 codegen places explicit and short-circuit
boolean temporaries where they occur, so the machine and collector hoist locals
and use short-lived boolean helper frames to avoid accumulating loop allocas.
This is a reader/runtime lowering choice; the compiler is unchanged.

Escaping multi-shot continuations require explicit continuation ownership,
cloning, re-entry and foreign-frame policies absent from the current shared AST.
Executable `call/cc` and `call-with-current-continuation` references are refused
by the reader with line and byte-column; `refusal.scm` demonstrates `3:2`.
Quoted symbols remain data. First-class continuations are deliberately unsupported.

Additional borders: escaped identifiers, quasiquotation evaluation, hygienic macros, `case-lambda`, multiple values, promises,
parameters, exceptions, ports, `eval`, a complete numeric tower (including
arbitrary integers, complex numbers, infinities/NaNs and exact rationals), Unicode
case handling, and complete R7RS libraries are unfinished. Immediate integers use
61 signed bits; overflow semantics are not an R7RS guarantee. Reals use binary64;
rational literals currently become inexact. Runtime type/arity validation and
source attribution beyond the explicit continuation refusal need further work.

Float embedding also exposes AST round-trip limitations: decimal number nodes
are not accepted by this bootstrap's S-expression reader, and floating-point
struct fields/unary negation do not lower correctly. The runtime uses explicit
casts, typed access to a numeric storage slot, and subtraction from float zero.
No compiler behavior or test expectation was changed to accommodate them.

## Scoring and reproducibility

```sh
python3 -B conformance/scheme/score.py --sample 10
```

The fixture copies `tests/r7rs-tests.scm` from Chibi
`f966f15dcce4bfcc33af50d34b70d084afb6750d`; its license is beside it.
`audit.py source` checks the cloned repository identity, original hash, normalized byte equality,
and identity of all datum tokens. Six trailing-whitespace lines outside strings
were trimmed for repository whitespace checks; no test datum changed.
The previous inventory is retained and extended to preserve vectors and offsets.
There are **980 executable `(test expected expr)` forms**, not 989. All nine extra
textual sites are in line/block comments. To preserve the requested 99-slot sample,
the scorer indexes the 989 textual sites, selects offsets 0, N, 2N, ... and counts
commented sites as non-executable failures. It never earns passes for comments.
This conservative denominator is explicit in `results.json`.

Each executable test retains its enclosing form and preceding referenced definitions
in original order, including earlier versions of redefined bindings. Dependency
closure also retains initializers and setup expressions that refer to those globals,
even when the initializer's result binding is unused. References through named
procedures are followed, so an initializer calling a mutating helper is retained.
Earlier tests in retained setup and in the enclosing form evaluate their expected
and actual expressions without emitting extra comparisons. This preserves state
changes without leaving an unbound `test` in the generated program. Static slicing
can over-retain lexical name collisions; reflective dependencies and macro expansion
remain outside this scorer's supported context model.
Expected and actual values execute once in the target, where structural/approximate
numeric comparison produces an attributed PASS/FAIL and test ID. The five-test
fixture checks binding context, stateful expressions and vector round-tripping.
`score-state.scm` adds seven comparisons covering initializer effects, earlier test
mutation, helper calls, redefinitions and quoted continuation data; its first
comparison must FAIL and the remaining six must PASS. `quotation.scm` and
`apply.scm` independently check long-form quoted data and repeated apply dispatch.

Four contexts are batched per compile. A failed batch preserves any completed
reports, then splits unresolved tests down to individual attributed failures.
Generated source, IR, compiler/linker/runtime logs and structured results go to
`--evidence` outside the checkout. The sample is the acceptance measurement;
the all-989 scoreboard is **DEFERRED**. It has not been run.
