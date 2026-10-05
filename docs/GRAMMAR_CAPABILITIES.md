# Language-building capabilities and acceptance

Lang is a self-hosted compiler compiler: a reader recognizes custom source,
constructs the shared typed AST, and reuses native or supported Wasm compilation.
`#parser{}` is its small ordered recursive-descent generator. Bison/yacc and
ANTLR are useful capability benchmarks, but their parsing algorithms and
product boundaries differ. This document records the distinction rather than
claiming interchangeable grammars or feature completeness.

## Recognition and ambiguity

Bison converts annotated context-free grammars to LR or GLR parsers, with
LALR, IELR or canonical LR tables. Its grammar tools report conflicts and can
produce counterexamples; GLR can maintain competing parses. Bison's lexer is
supplied separately. Its precedence/associativity declarations resolve
expression conflicts without requiring Lang's flat-tree lowering convention.
[Bison manual source](https://github.com/akimd/bison/blob/master/doc/bison.texi).

ANTLR generates lexers and parsers, uses adaptive prediction, and rewrites
supported directly left-recursive expression rules into precedence-aware
recognizers. It supplies parse-tree context access, listeners and visitors.
[ANTLR parser rules](https://github.com/antlr/antlr4/blob/master/doc/parser-rules.md),
[left-recursion transformation](https://github.com/antlr/antlr4/blob/master/doc/left-recursion.md),
[ALL(*) technical report](https://www.antlr.org/papers/allstar-techreport.pdf).

Lang's generated alternatives are ordered: the first successful branch wins.
Failed branches and sequences rewind transactionally. A choice that already
succeeded is not globally reconsidered when its caller later fails. For
example, `item = number | number symbol` followed by `file = item eof`
rejects `1 name`; reversing those alternatives accepts it. There is no LR
conflict report, ambiguity witness, parse forest, adaptive ALL(*) prediction,
or packrat memoization. Shared-prefix backtracking can repeat substantial work.

Direct, indirect and nullable-prefix left recursion are diagnosed at the
closing grammar reference. Right recursion is supported. This avoids a crash
from authoring a left-recursive grammar, but it does not expand the generator's
recognition class to Bison's or ANTLR's.

## Coverage matrix

| Capability | Lang's current contract | Benchmark gap |
|---|---|---|
| Token grammar | Rules, ordered alternatives, sequences, groups, `?/*/+`, exact literals, custom token kinds, `eof` | No explicit empty alternative, syntactic predicates, wildcard/complement terminals or nongreedy EBNF |
| Lexing | Shared scanner, configurable line/block comments, reader-supplied token streams with original spans | No generated regular-expression lexer, fragments, channels or mode stack |
| Layout/context | Reader can synthesize NEWLINE/INDENT/DEDENT and classify tokens before parsing | Stateful scanner/preprocessing logic is handwritten |
| Precedence | `std/prec.lang` builds AST using declared left/right levels, prefix operators and assignment | No automatic rewriting of left-recursive expression grammars; postfix/ternary exceptions stay reader-local |
| Ambiguity | Ordered policy is explicit; shared-prefix failures rewind | No analysis or enumeration of competing successful parses |
| Parse tree | Named captures, labeled alternatives, repeated captures, source spans, stderr tree dump | No generated typed context classes or visitor/listener interfaces |
| Grammar errors | Located malformed grammar, duplicate/undefined rule, duplicate capture, nested branch-label conflict, left recursion | No unreachable-rule/FIRST/FOLLOW/conflict-report tooling |
| Source errors | Furthest failing token plus merged expected terminals; byte offset and line/column | No automatic semantic recovery or per-rule diagnostic customization |
| Recovery | Explicit bounded sessions collect snapshots and synchronize at reader-chosen token text/kind | No inferred follow sets or automatic token insertion/deletion |
| Target code | Lower to shared AST; native compiler minting; browser reader→AST→supported Wasm program | Target semantics are restricted by the kernel/backend; a grammar does not add missing runtime behavior |
| Authoring tools | CLI token dump, AST inspection, standalone compiler, browser editable pipeline and saved workspaces | No incremental parser/LSP/debugger or proven large-grammar complexity guarantee |

ANTLR's lexer modes and channels are concrete features beyond changing comment
markers or supplying a token stream.
[ANTLR lexer rules](https://github.com/antlr/antlr4/blob/master/doc/lexer-rules.md).
ANTLR's default recovery includes synchronization and single-token insertion
or deletion; Bison expresses recovery with an `error` token in grammar rules.
Lang's explicit helper provides a narrower policy.
[ANTLR error strategy](https://www.antlr.org/api/Java/org/antlr/v4/runtime/DefaultErrorStrategy.html),
[Bison recovery](https://www.gnu.org/software/bison/manual/html_node/Error-Recovery.html).

## Concrete authoring acceptance

Capabilities count when an author can build and run a language, correct bad
source, and inspect what it produced. These examples define useful tests:

1. **Small complete language.** A new grammar accepts `add 20; add 22;`, captures
   the values, produces shared AST and runs to `42`. A minted compiler does the
   same outside the checkout. `eof` rejects a valid prefix followed by garbage.
   Exact literals such as `'x'`, `'0'` and `'^'` work independently of token kind,
   while empty literals fail at the grammar rather than hiding a recursion trap.
2. **Expressions.** A flat token grammar with a precedence table compiles
   `2 + 3 * 4` to `14`, respects declared right association, and rejects an
   undeclared operator. Prefix and assignment cases have explicit expectations.
3. **Layout.** A supplied token stream drives `<indent>`/`<dedent>` rules while
   real and synthetic tokens retain original source locations. Minipy is the
   working language example, not a claim of Python compatibility.
4. **Grammar correction.** Direct, indirect, nullable-prefix and zero-width EOF
   recursion fail with located diagnostics and no output artifact. The author
   rewrites the expression grammar or uses the precedence toolkit.
5. **Several source errors.** `add ;` then `add word;` produces two independently
   located `expected number` messages. A later good statement is recognized,
   but no partial AST/executable is accepted. Correcting both errors produces
   `42` through the same reader module.
6. **Authoring continuity.** Save, reopen and export a changed reader, source
   and optional runtime; reproduce the same AST, output and diagnostic
   selection. This is a browser journey, beyond a parser unit test.

The focused native and in-browser compiler acceptance harnesses are
[`parser_authoring_e2e.py`](../test/parser_authoring_e2e.py) and
[`parser_authoring_browser.js`](../test/parser_authoring_browser.js). They use
the actual standalone reader and actual compiler.wasm pipeline. The runtime
regression also exercises error caps, synchronization budgets, EOF and
synthetic tokens with equal byte offsets. Broader expression/layout and
save/reopen/export gates are maintained by their existing suites; a passed
focused test alone does not establish those journeys.

## What to invest in next

First, preserve these end-to-end journeys across native and Wasm: a capable
grammar that cannot run its lowered program is an incomplete authoring product.
Next, add inspectable grammar analysis and deliberately scoped lexer facilities
when a real language example requires them. Large-grammar benchmarks should
measure shared-prefix and recursion costs before claiming scalable recognition.
A switch to LR, GLR or adaptive prediction would be an architectural project,
not a notation change or checklist item.
