# Lang, flex/Bison, and ANTLR: the same native Tariff DSL

## Decision and scope

Before implementing the three frontends, we chose an integer batch tariff DSL:
pricing rules need named functions, mutable totals, conditionals, and loops.
This exercises a compiler pipeline without needing objects, a garbage collector,
or language-specific changes to Lang's kernel. The design was recorded before
implementation; the executable grammar and fixtures live in
[`examples/dsl-compare`](../examples/dsl-compare/README.md).

The final grammar has 21 ANTLR parser rules (plus four lexer rules), 22 named Lang
rules with a shared precedence table, and 24 Bison nonterminals where optional
lists and statement repetitions are explicit. These express the same syntax.
All values are bounded signed 64-bit integers; overflow, division by zero,
shadowing, undeclared names, duplicate definitions, missing returns, and names
reserved by the C backend are outside the supported subset. Parameters and locals
must have unique names and calls must match their declared signatures. These
restrictions matter: parser generators alone do not supply semantic analysis.
Only decimal integer literals, ASCII identifiers, whitespace, and `//` comments
are part of the language. Leading zeros remain decimal: `010` is 10 and `08`
is 8. Both C emitters strip redundant leading zeros, including in the baseline
versions; a shared native fixture also covers zero and negative literals. Functions may call functions declared later.

## Reproduction and measurement

Use the commands in the example README. The runner starts with a fresh Git clone
of committed HEAD and empty build directories, and records that commit in JSON.
It builds Lang's current compiler from its preserved LLVM bootstrap before
building the generated Tariff frontend. The other arms generate and build their
frontends from their grammar sources. Tool provisioning time is excluded from
clean-to-binary time; source building and parser generation are included.
Lang's extra expanded-AST pass is only for generated LOC accounting and runs
after the sample binary is linked, outside both build and sample compile timers.

The released parser tools are [flex 2.6.4](https://github.com/westes/flex/releases/tag/v2.6.4),
[Bison 3.8.2](https://ftp.gnu.org/gnu/bison/), and
[ANTLR 4.13.2](https://www.antlr.org/download.html). Download hashes and the
Temurin Java 21.0.13+9 maintenance release are pinned in `install.py`.
The Python target uses the matching ANTLR 4.13.2 runtime. [Clang 23.1.5](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.5)
is installed from the current official release archive under the same tools
directory. Existing host prerequisites are Python 3.13, git, make, dpkg-deb,
zstd and the system C headers/linker; no system tool is installed or upgraded.
Extracting LLVM requires the archive's 1 GiB zstd window (`--long=30`). Lang has no comparable
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
The change touched 3 Lang lines (2 added, 1 removed), 9 flex/Bison lines
(5 added, 4 removed), and 4 ANTLR lines (3 added, 1 removed). Lang wins this
small extension because its precedence table already supports remainder.
Five malformed files check a missing semicolon, closing parenthesis, operand,
invalid character, and closing brace. Every frontend must exit 1, emit a diagnostic
to stderr, and emit no partial code. Exact unedited diagnostic text is retained.

## Results and judgment

The executable report is generated outside the checkout at `evidence/compare.json`
(relative to the experiment directory). It contains machine-generated measurements,
all command exit codes and timings, input hashes, native outputs, and errors.
Its command transcript is named relative to the report directory. Keeping the
two files together permits validation after moving the evidence and reclaiming
the original build directory; `check.py report --relocate` exercises this.
The following measured run uses released Clang 23.1.5 for all three arms
(source commit `90481dd`). This historical run included a LOC-only Lang expansion in clean-build time;
that timing is superseded by the corrected runner. Later JSON replays supersede
all host-sensitive timings. Tool provisioning is excluded.

| Measure | Lang | flex/Bison | ANTLR Python target |
|---|---:|---:|---:|
| Hand-written frontend lines | 170 | 138 | 124 |
| Generated frontend lines, all recorded representations | 60,890 | 3,780 | 1,628 |
| Clean source to sample native binary | 10.369 s | 0.300 s | 0.449 s |
| Complete 100,000-line compilation | **rejected** | 0.682 s | 10.325 s |
| Scale lines/second | unavailable | 146,594 | 9,685 |
| Native benchmark median, including startup | 4.50 ms | 3.85 ms | 4.50 ms |
| Native binary bytes | 16,160 | 16,120 | 16,120 |

Lang parsed the large input in 0.72 seconds but rejected its emitted AST at the
backend boundary with `(code ast-nodes)`. Its fixed AST-node quota prevents a
working native scale binary at the default settings. This is a loss, not a
100,000-line successful compile time. No limit was raised and no input lines were
removed. A completed experiment can pass while recording this expected limit;
the failed subprocess exit code, exact error, and missing throughput remain in
the report. Unexpected build failures still fail the experiment.

ANTLR required the least hand-written code and generated footprint. Bison won
clean build and scale compilation. Bison and ANTLR tied binary size; the small
runtime differences are within startup/scheduling noise, so runtime is a
practical tie, not evidence of a better optimizer. Lang requires the fewest
separately installed build dependencies, but pays for a compiler bootstrap from
source. It has no distribution convenience win until that SDK is packaged.

The authoritative released-toolchain run was serial. The earlier Clang 19 pilot
also overlapped a gate run and is retained separately with that qualification;
its timings are excluded from the table. No arm received special flags or
optimizations. The raw fastest runtime is Bison in this run, but the scheduling
spread and tiny native programs do not support a practical runtime winner.

On diagnostics, ANTLR's concise missing-token and lexer messages are my qualitative
choice for these five inputs. Lang supplies columns and byte spans but often
lists a noisy set of speculative expectations. Bison supplies useful token
names and expected tokens, but this frontend does not add column tracking.
These are implementation-level diagnostics, not a ranking of every generator's
potential error recovery.

**I would pick flex/Bison for a new native integer DSL today.** ANTLR is attractive
when parse-tree APIs and its wider tooling ecosystem matter more than this
Python target's compilation speed. I would not pick Lang today for this DSL:
it needs more frontend code, much more generated output, a slower cold build,
and fails this scale case. Its direct shared-AST/native pipeline is useful,
but does not yet outweigh those costs.

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
