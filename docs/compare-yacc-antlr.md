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
is 8. Line comments end at either CR or LF; LF, CRLF, bare CR, mixed
endings, and a final comment without a newline share native fixtures in both
grammar versions. The Lang frontend scans a copy with CR bytes replaced by LF;
its token stream and AST spans still refer to the unchanged original byte offsets.
The flex comment class excludes both bytes, as ANTLR's already does.
Both C emitters strip redundant leading zeros, including in the baseline
versions; a shared native fixture also covers zero and negative literals. Functions may call functions declared later.

## Reproduction and measurement

Use the commands in the example README. The runner starts with a fresh Git clone
of committed HEAD and empty build directories, and records that commit in JSON.
It builds Lang's current compiler from its preserved LLVM bootstrap before
building the generated Tariff frontend. The optional Lang SDK arm starts with
a separately provisioned archive and builds only the Tariff frontend, using the
SDK's resources from an empty working directory. Both Lang arms rely on the
frontend's transitive library includes; neither adds a redundant core-library CLI
input. This avoids absolute/relative include duplication with SDK resources. The other arms generate and build their
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
Extracting LLVM requires the archive's 1 GiB zstd window (`--long=30`). The source arm pins Lang's source/seed revision by Git. The SDK arm uses a local
versioned archive from that same commit; it is not a published download.

Every arm receives exactly the same fixtures and Clang `-O2` native link flags.
There is no per-arm performance tuning. The final benchmark calls `compute` with
2,000,000 and checks `6000002995045`. Five independent native process runs are
recorded; runtime includes startup and reports the median. Binary bytes include
the same harness and default linker metadata, without stripping or LTO.

The generated scale fixture has exactly 100,000 physical lines, including
99,996 live assignments to one local. The runner measures frontend time and the
complete source-to-native pipeline separately, verifies the native result, and
reports lines/second. The complete pipeline has a 180-second deadline; failure or timeout is
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

## Authoring evidence and replay boundaries

The Tariff timings below are scripted compiler replays. They measure machine
work on existing sources, not fresh-agent language authoring. Provisioning,
authoring, frontend construction, source-to-native compilation and native
execution need separate clocks; a missing clock is unmeasured, never zero.

A separate audit of the frozen Harbor configuration trials gives this narrower
view. Harbor's ANTLR arm targets C++, unlike the Tariff Python arm below.

| Harbor measure | Lang trial 1 | Lang trial 2 | Accepted flex/Bison | ANTLR C++ |
|---|---|---|---|---|
| Package provisioning | unmeasured | unmeasured | 0.584583 s | unmeasured |
| Author start to first working sample | unmeasured | unmeasured | 174.448954 s | 170.830682 s |
| Observed failed commands before first sample | 0 | unmeasured | 2 | 0 |
| Retained handwritten language lines | 122 | 122 | 230 | 134 |

Trial 1 retains a first-sample command start but no completion or author-start
clock. Its three cascading failed commands happened after that first success.
Trial 2's final consumer run is a scripted replay: its 0.815359 s frontend and
3.815668 s native-link durations are not authoring time. Its friction report
also describes three earlier failures, whose raw failed runs are absent from
the frozen packet. Zero failures in the final replay cannot establish zero
failures during authoring.

Bison's initial attempt violated its documentation boundary and remains
excluded. The accepted attempt has two failed build commands, including a
build with several C diagnostics; diagnostics do not count as separate attempts.
Bison's setup receipt predates both attempts. ANTLR describes provisioning but
the frozen inputs do not retain its setup receipt. Both measured author
intervals include thinking and builds, under procedural agent isolation;
they are not blinded human measurements. Expected rejection of the eight
invalid fixtures counts as successful validation rather than a failed attempt.

Handwritten language counts include physical blank and comment lines in the
retained frontend sources. Generated parsers, libraries, compiler sources and
supplied inputs are excluded. Build and replay scripts are counted separately:
Bison's original support bytes can be recovered from logged write events,
whereas some ANTLR helper files have only reported counts and remain qualified.
Lang needs its versioned SDK, Clang and a system C toolchain to build; Bison
adds flex, Bison and m4. ANTLR needs its jar, Java, C++ generator/runtime and a
C++17 toolchain. The native Lang and Bison programs need the system C runtime;
the ANTLR program statically links its ANTLR runtime and also uses the system
C/C++ runtime and threading support.

The bounded audit fragment reads the original hash-pinned input packet and
never runs the commands it finds there:

```sh
nice -n 10 python3 -B test/reader_author/metric_audit.py --inputs /path/to/frozen-inputs --case first-working-sample --output /path/to/audit
```

It recomputes the six audit categories: setup boundary, first working sample,
failed attempts, handwritten lines, dependencies and missing timestamps.
The output ledger includes source event references, per-file counts and
compiler/runtime phases. Removing a required first-pass timestamp fails
explicitly; the validator never fills that gap with zero. No new author trial
or scale run is needed to audit these retained observations.

## Results and judgment

The executable report is generated outside the checkout at `evidence/compare.json`
(relative to the experiment directory). It contains machine-generated measurements,
all command exit codes and timings, input hashes, native outputs, and errors.
Its command transcript is named relative to the report directory. Keeping the
two files together permits validation after moving the evidence and reclaiming
the original build directory; `check.py report --relocate` exercises this.
The original source-build run measured **9.596 s** for Lang, **0.350 s** for
Bison and **0.551 s** for ANTLR. Keep those source-build numbers as historical
context. The following serial SDK replay uses released Clang 23.1.5 for every
arm (source/SDK commit `af8667db6c659eb3947c9a4d599af78dc6c14cf1`). The LOC-only expansion is excluded from
clean-build time. Later machine-readable replays supersede these host-sensitive
timings. The documented snapshot is retained as `evidence/documented-compare.json`;
`evidence/compare.json` records the latest committed-head replay. Tool
provisioning, SDK creation and archive extraction are excluded.
No arm receives different optimization flags.

Archive independence is checked separately from these host timings. The SDK
journey copies only the archive into a fresh working directory outside the
checkout, uses `env -i` with an empty HOME and the system and SDK bin paths,
and builds Tariff and a 100,000-line native program. It scans produced files for
the checkout path and records command exit codes and output hashes in
`evidence/sdk-journey.json`; see [archive-only verification](SDK.md#archive-only-verification).
This is a clean-environment and working-directory check, not filesystem or VM
isolation. Archive extraction is excluded from the serial comparison as tool
provisioning.

| Measure | Lang source | Lang SDK | flex/Bison | ANTLR Python target |
|---|---:|---:|---:|---:|
| Hand-written frontend lines | 178 | 178 | 143 | 126 |
| Generated frontend lines, all recorded representations | 59,862 | 59,862 | 3,787 | 1,628 |
| Clean source to sample native binary | 9.345 s | 2.057 s | 0.350 s | 0.445 s |
| Complete 100,000-line compilation | **rejected** | **rejected** | 0.582 s | 10.362 s |
| Scale lines/second | unavailable | unavailable | 171,699 | 9,651 |
| Native benchmark median, including startup | 3.55 ms | 4.92 ms | 3.87 ms | 7.85 ms |
| Native binary bytes | 16,160 | 16,160 | 16,120 | 16,120 |

The SDK missed the **under 2 s** clean-to-sample target in this run: **2.057 s**. This is a measured loss. It removes the
compiler bootstrap from language creation, but building the Tariff frontend
still takes longer than Bison or ANTLR. The generated Lang count changed because
both Lang arms now omit the same redundant core input; this is not a reduction
to the shared compiler's size limits. Both produce the same native result.

The table above is the historical comparison. At `dc228a8`, Lang parsed the
large input but rejected its emitted AST at the backend boundary with
`(code ast-nodes)`. The fixed 1,048,576-element quota was lower than this
program's 2,999,939 textual elements, including reader source-span metadata.
That report correctly recorded a scale loss, with the failed command retained.

### Scale follow-up

The implementation at `7eb872a` raises the default structural fuel to 4,194,304
and makes it configurable through `LANG_HOST_MAX_NODES` (1..16,777,216).
Independent byte, recursive-depth, cumulative-allocation and work accounts
remain enforced. LLVM output grows within the host byte/account limits instead
of failing at a separate 8 MiB buffer. This is an explicit limit change, not an
optimization flag supplied only to Lang. No fixture lines are removed.

The follow-up reruns every arm with the same pinned Clang 23.1.5, `-O2`, inputs,
checks and empty build directories. The runner now records each command's peak
resident bytes with `wait4`, retains successful backend timings and emits
`evidence/scale.json` alongside the comparison and command transcript. Peak
pipeline memory is the maximum phase peak, not a sum. All three native programs
return **100000** for argument 4. The source-to-native deadline is 180 seconds
total, including all phases.

| Follow-up measure | Lang | flex/Bison | ANTLR Python target |
|---|---:|---:|---:|
| Complete 100,000-line compilation | **2.057 s** | 0.584 s | 10.111 s |
| Frontend | 0.774 s | 0.084 s | 9.586 s |
| Shared-AST backend | 0.636 s | included in native step | included in native step |
| Native optimization and link | 0.639 s | 0.499 s | 0.524 s |
| Scale lines/second | 48,616 | 171,238 | 9,890 |
| Peak resident memory | 800.5 MiB | 156.0 MiB | 485.3 MiB |

Lang now beats the historical ANTLR total of 10.465 s and its rerun, and finishes
well inside the deadline. It still loses to the historical Bison 0.635 s and the
Bison rerun. These timings describe an already built frontend compiling the
large input; cold compiler/reader construction remains a separate measure.

The largest avoidable cost after admitting the AST was reader-span location
lookup: the backend spent **47.839 s** before failing at its former LLVM buffer
limit. It rescanned the entire source prefix for every span. Binary search in
the already existing immutable line-start index reduces the successful backend
pilot to **0.567 s** (same Clang 19 development build and same AST/input), while
retaining one-based UTF-8 byte columns. The released-toolchain rerun above
measures the complete successful pipeline. These pilots are diagnostic evidence,
not timings substituted into the comparison table.

The largest remaining phase in the released-toolchain run is the frontend,
0.774 s and 800.5 MiB peak. Its generated parse tree plus string AST, followed by
the backend's second generic parse tree and shared AST, still allocate several
representations per source node. Reaching Bison's order of magnitude needs a
compact or streaming frontend-to-core handoff and less per-node allocation,
plus direct lowering into the backend's validated representation. That crosses
the reader transport/toolkit boundary and needs separate design and profiling;
it is not a safe local change to this example's grammar. The backend emits
10,178,211 LLVM bytes for this fixture, so less generated instruction/text
overhead would also reduce downstream work. Further optimization is not hidden
in per-arm flags.

ANTLR required the least hand-written code and generated footprint. Bison won
clean build and scale compilation. Bison and ANTLR tied binary size; the small
runtime differences are within startup/scheduling noise, so runtime is a
practical tie, not evidence of a better optimizer. Lang requires the fewest
separately installed build dependencies, but pays for a compiler bootstrap from
source. The local SDK now provides that convenience: a language author needs no Lang
checkout or bootstrap seed. Its consumer prerequisites are Clang and the system
C toolchain on compatible Linux x86-64; see [the SDK contract](SDK.md). A local
archive does not establish a public release or cross-platform distribution.

The authoritative released-toolchain run was serial. The earlier Clang 19 pilot
also overlapped a gate run and is retained separately with that qualification;
its timings are excluded from the table. No arm received special flags or
optimizations. The raw fastest runtime is Lang in this run, but the scheduling
spread and tiny native programs do not support a practical runtime winner.

### Diagnostics: five fixtures, five visible properties

On the compiler sources at `e148de1`, the unchanged Tariff frontends score
**Lang 15/25, ANTLR 14/25, flex/Bison 9/25**. This replaces the earlier qualitative
ANTLR verdict with a reproducible count. Each diagnostic earns one point for
naming its input file, giving a line, giving a column, explicitly listing expected
tokens, and showing a source line with a caret. All properties have equal weight;
this measures information present, not whether expectations are minimal or the
reported position is the most helpful one.

The scorer recognizes `label:line[:column]:` headers. A basename or full path
matching the input counts as a file name; the generic `tariff` label does not.
Byte spans alone do not count as line or column. `expected`/`expecting` with a
nonempty token description counts, as does an explicit `missing 'token'` message.
An unexpected token or lexer recognition error alone does not. A caret must
appear directly below an actual input source line (including the empty EOF
line); a standalone caret does not count. These rules are tested with synthetic
positive and negative examples before measuring real output.

Lang's remaining diagnostic losses are plain: **0/5 input file names and 0/5
source lines with carets**. All three frontends use a generic `tariff` label.
The standard library's newer snippet API is opt-in, while this existing Tariff
frontend still calls `tok_print_error`, which emits the compact form. No
frontend was changed to improve its score. Lang also lists speculative operator
alternatives where Bison and ANTLR give a focused missing token; the rubric does
not score that quality difference. ANTLR loses one expected-token point for its
invalid-character lexer error; Bison lacks columns and suppresses expectations
for the closing-brace fixture. These are results for these implementations and
five inputs, not limits on the generators' possible diagnostics or recovery.

Run the smoke and `check.py diagnostics --check-doc` commands in the
[example README](../examples/dsl-compare/README.md) to reproduce the table.
`check.py diagnostics --markdown` generates the block below directly from the
retained report. The validator checks its HEAD and input hashes and matches
every diagnostic's text, exit code and empty stdout against the sibling command
transcript. It also requires the documentation block to match exactly, so later
changes cannot silently leave this scoreboard stale. The existing build and
scale measurements above remain historical; this smoke run measures diagnostics.

<!-- diagnostics:start -->
| Fixture | Arm | File | Line | Column | Expected tokens | Source + caret | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| brace.tariff | lang | no | yes | yes | yes | no | 3/5 |
| brace.tariff | yacc | no | yes | no | no | no | 1/5 |
| brace.tariff | antlr | no | yes | yes | yes | no | 3/5 |
| character.tariff | lang | no | yes | yes | yes | no | 3/5 |
| character.tariff | yacc | no | yes | no | yes | no | 2/5 |
| character.tariff | antlr | no | yes | yes | no | no | 2/5 |
| operand.tariff | lang | no | yes | yes | yes | no | 3/5 |
| operand.tariff | yacc | no | yes | no | yes | no | 2/5 |
| operand.tariff | antlr | no | yes | yes | yes | no | 3/5 |
| parenthesis.tariff | lang | no | yes | yes | yes | no | 3/5 |
| parenthesis.tariff | yacc | no | yes | no | yes | no | 2/5 |
| parenthesis.tariff | antlr | no | yes | yes | yes | no | 3/5 |
| semicolon.tariff | lang | no | yes | yes | yes | no | 3/5 |
| semicolon.tariff | yacc | no | yes | no | yes | no | 2/5 |
| semicolon.tariff | antlr | no | yes | yes | yes | no | 3/5 |

| Arm | Total |
|---|---:|
| lang | 15/25 |
| yacc | 9/25 |
| antlr | 14/25 |

Exact stderr follows; every invocation exits **1** with empty stdout.

**brace.tariff — lang**

```text
tariff:2:1: expected 'let' or symbol or 'if' or 'while' or 'return' or '}', found end of input @55:55
```

**brace.tariff — yacc**

```text
tariff:2: syntax error, unexpected end of file
```

**brace.tariff — antlr**

```text
tariff:2:1: extraneous input '<EOF>' expecting {'}', 'let', 'if', 'while', 'return', ID}
```

**character.tariff — lang**

```text
tariff:1:26: expected '(' or '==' or '!=' or '<' or '>' or '<=' or '>=' or '+' or '-' or '%' or '*' or '/' or ';', found @ @25:26
```

**character.tariff — yacc**

```text
tariff:1: syntax error, unexpected INVALID, expecting ';'
```

**character.tariff — antlr**

```text
tariff:1:26: token recognition error at: '@'
```

**operand.tariff — lang**

```text
tariff:1:28: expected '-' or number or symbol or '(', found ; @27:28
```

**operand.tariff — yacc**

```text
tariff:1: syntax error, unexpected ';', expecting ID or INT or '(' or '-'
```

**operand.tariff — antlr**

```text
tariff:1:28: mismatched input ';' expecting {'(', '-', ID, INT}
```

**parenthesis.tariff — lang**

```text
tariff:1:30: expected '==' or '!=' or '<' or '>' or '<=' or '>=' or '+' or '-' or '%' or '*' or '/' or ')', found ; @29:30
```

**parenthesis.tariff — yacc**

```text
tariff:1: syntax error, unexpected ';', expecting ')'
```

**parenthesis.tariff — antlr**

```text
tariff:1:30: missing ')' at ';'
```

**semicolon.tariff — lang**

```text
tariff:1:27: expected '==' or '!=' or '<' or '>' or '<=' or '>=' or '+' or '-' or '%' or '*' or '/' or ';', found return @26:32
```

**semicolon.tariff — yacc**

```text
tariff:1: syntax error, unexpected RETURN, expecting ';'
```

**semicolon.tariff — antlr**

```text
tariff:1:27: missing ';' at 'return'
```
<!-- diagnostics:end -->

**I would pick flex/Bison for a new native integer DSL today.** ANTLR is attractive
when parse-tree APIs and its wider tooling ecosystem matter more than this
Python target's compilation speed. I would not pick Lang today for this DSL:
it needs more frontend code, much more generated output, a slower cold build,
and higher peak memory. It now passes this scale case and beats the ANTLR
Python target. Its direct shared-AST/native pipeline is useful,
but does not yet outweigh those costs.

Lang already has useful [reader documentation](READERS.md), grammar validation,
a precedence service, and an editor/LSP. The comparison must not claim those are
absent. Bison has a much larger established manual, grammar conflict reports and
counterexamples, mature C build integration and a long-lived ecosystem. ANTLR
has a broad grammar collection, multiple supported targets, parse-tree tooling,
and IDE plugins listed on its download page. Lang lacks comparable depth of
third-party grammars, IDE grammar tooling, ecosystem, and grammar diagnostics;
its existing checks are a start, not feature parity.

The top three things Lang needs to win are: (1) distribution and maintenance of
the versioned compiler/reader SDK beyond this local Linux x86-64 archive;
(2) a faster, bounded parser/lowering pipeline with reusable semantic analysis and
less generated AST/LLVM overhead; (3) documentation, grammar inspection and IDE
support with a larger set of maintained real-world readers. This small experiment
does not establish bootstrap correctness, general language expressiveness, or
performance against ANTLR's other targets. The registered compiler gate separately
checks Lang's bootstrap fixed points.
