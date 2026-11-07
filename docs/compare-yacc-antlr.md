# Lang, flex/Bison, and ANTLR: the same native Tariff DSL

## Decision and scope

Before implementing the three frontends, we chose an integer batch tariff DSL:
pricing rules need named functions, mutable totals, conditionals, and loops.
This exercises a compiler pipeline without needing objects, a garbage collector,
or language-specific changes to Lang's kernel. The design was recorded before
implementation; the executable grammar and fixtures live in
[`examples/dsl-compare`](../examples/dsl-compare/README.md).

The final grammar has 21 ANTLR parser rules (plus four lexer rules), 22 named Lang
rules with a shared precedence table, and 26 Bison nonterminals where optional
lists and statement repetitions are explicit. These express the same syntax.
All values are bounded signed 64-bit integers; overflow, division by zero,
shadowing, undeclared names, duplicate definitions, missing returns, and names
reserved by the C backend are outside the supported subset. Parameters and locals
must have unique names and calls must match their declared signatures. These
restrictions matter: parser generators alone do not supply semantic analysis.
Only decimal integer literals, ASCII identifiers, whitespace, and `//` comments
are part of the language. Functions may call functions declared later.

## Reproduction and measurement

Use the commands in the example README. The runner starts with a fresh Git clone
of committed HEAD and empty build directories, and records that commit in JSON.
It builds Lang's current compiler from its preserved LLVM bootstrap before
building the generated Tariff frontend. The other arms generate and build their
frontends from their grammar sources. Tool provisioning time is excluded from
clean-to-binary time; source building and parser generation are included.

The released parser tools are [flex 2.6.4](https://github.com/westes/flex/releases/tag/v2.6.4),
[Bison 3.8.2](https://ftp.gnu.org/gnu/bison/), and
[ANTLR 4.13.2](https://www.antlr.org/download.html). Download hashes and the
Temurin Java 21.0.13+9 maintenance release are pinned in `install.py`.
The Python target uses the matching ANTLR 4.13.2 runtime. Clang 19.1.7 and Python
3.13 are existing host prerequisites, not claimed to be the latest LLVM or
Python releases; no system tool is installed or upgraded. Lang has no comparable
released tool distribution here, so its source/seed revision is pinned by Git.

Every arm receives exactly the same fixtures and Clang `-O2` native link flags.
There is no per-arm performance tuning. The final benchmark calls `compute` with
2,000,000 and checks `6000002995045`. Five independent native process runs are
recorded; runtime includes startup and reports the median. Binary bytes include
the same harness and default linker metadata, without stripping or LTO.

The generated scale fixture has exactly 100,000 physical lines, including
99,996 live assignments to one local. The runner measures frontend time and the
complete source-to-native pipeline separately, verifies the native result, and
reports lines/second. A phase has a 180-second deadline; failure or timeout is
reported as such, never converted into a successful speed measurement.

Hand-written counts include all physical lines (comments and blanks) in each
arm's source files; shared harness and experiment tooling are separate. Generated
counts list files individually: Lang emits LLVM and an expanded AST; flex/Bison
emit C and a header; ANTLR emits Python. These are different representations and
line formatting conventions, so generated LOC is a footprint, not productivity.
The sample's emitted AST/C and backend LLVM counts are also recorded. The Lang
compiler's own implementation and installed library sources are dependencies,
not hand-written code for this DSL, just as parser generator implementations are.

Both earlier and final grammars are built. Both must compile the baseline fixture
and return 14; the earlier grammar must reject `%`. The final grammar must return
7 for the unusual precedence probe and pass the associativity/unary probe.
Actual unified diffs and added+removed physical line counts are included in JSON.
Five malformed files check a missing semicolon, closing parenthesis, operand,
invalid character, and closing brace. Every frontend must exit 1, emit a diagnostic
to stderr, and emit no partial code. Exact unedited diagnostic text is retained.

## Results and judgment

The executable report is generated outside the checkout at `evidence/compare.json`
(relative to the experiment directory). It contains machine-generated measurements,
all command exit codes and timings, input hashes, native outputs, and errors.
Results and the final choice are documented after the measured run.

Lang already has useful [reader documentation](READERS.md), grammar validation,
a precedence service, and an editor/LSP. The comparison must not claim those are
absent. Bison has a much larger established manual, grammar conflict reports and
counterexamples, mature C build integration and a long-lived ecosystem. ANTLR
has a broad grammar collection, multiple supported targets, parse-tree tooling,
and IDE plugins listed on its download page. Lang lacks comparable depth of
third-party grammars, IDE grammar tooling, ecosystem, and grammar diagnostics;
its existing checks are a start, not feature parity.

The top three things Lang needs to win are: (1) a versioned, packaged native
compiler/reader SDK so creating a language does not rebuild the compiler;
(2) a faster, bounded parser/lowering pipeline with reusable semantic analysis and
less generated AST/LLVM overhead; (3) documentation, grammar inspection and IDE
support with a larger set of maintained real-world readers. This small experiment
does not establish bootstrap correctness, general language expressiveness, or
performance against ANTLR's other targets. The registered compiler gate separately
checks Lang's bootstrap fixed points.
