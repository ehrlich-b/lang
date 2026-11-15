# Tariff: one DSL, three native pipelines

Tariff is a small batch pricing language with functions, local integer variables,
assignment, conditionals, loops, and return statements. See
[the comparison](../../docs/compare-yacc-antlr.md) for the design and limitations.

From the repository root on Debian-compatible Linux x86-64, with
Python 3.13, make, git, dpkg-deb, zstd and a C system toolchain already installed:

```sh
nice -n 10 python3 examples/dsl-compare/install.py --tools ../tools
nice -n 10 python3 examples/dsl-compare/run.py --tools ../tools --report ../evidence/compare.json
```

Commit changes before running. The script clones the committed source into a new,
empty build directory outside this checkout and creates the report and complete
command transcript outside the checkout. Clang 23.1.5 and the parser tools are downloaded from pinned release artifacts.
LLVM's compressed archive is about 1.2 GB and requires a 1 GiB decoder window;
only Clang and its support files are extracted. Tool downloads are hash-pinned and
installed only in the explicit tools directory. Existing downloads must match
their hashes; a failed download is preserved for investigation. The experiment
never installs system packages. `--smoke` runs small native examples (including leading-zero decimal literals), both
versions of the grammar, line comments with LF/CRLF/CR/mixed endings and no final
newline, and all five diagnostic fixtures without the large input.

To reproduce just the diagnostics comparison, commit the candidate and run:

```sh
nice -n 10 python3 -B -m unittest discover -s examples/dsl-compare -p test_check.py -v
nice -n 10 python3 examples/dsl-compare/run.py --tools ../tools --report ../evidence/compare.json --smoke
nice -n 10 python3 examples/dsl-compare/check.py diagnostics --report ../evidence/compare.json --check-doc
```

The scorer validates the committed HEAD, five input hashes, each exit code and
empty stdout against the retained sibling command transcript, then scores file
name, line, column, explicit expected tokens and source line with caret.
`--markdown` renders the documentation's exact scored table and all 15 stderr
messages. These checks work after the temporary build directory is reclaimed;
retain the report and its sibling command transcript. The five equally weighted
yes/no properties measure visible information, not wording quality or recovery.

`lang/` generates a parser with `#parser{}`, lowers to shared AST, and uses Lang's
LLVM backend. `yacc/` generates C with flex and Bison and emits C through a small
rope builder. `antlr/` generates a Python lexer/parser/visitor with ANTLR 4 and
emits C. Each native program links the same C harness with Clang `-O2`, without
LTO. Python runs only at compile time. The ANTLR arm measures that supported
Python target, not ANTLR's C++ or Java targets.

`baseline/` holds the actual compilable sources before adding remainder. It is
built and run too. The final `%` tier binds tighter than `+` and looser than `*`:
`2 + 17 % 3 * 2` is **7**. The benchmark uses bounded signed 64-bit arithmetic;
arguments, identifiers, declarations and returns must obey the portable integer
subset described in the comparison. This is a compiler comparison, not a
production language implementation. The comment fixtures keep their literal bytes
through Git attributes; CR at end of a fixture line is intentional.

All generated inputs and build products are reproducible from these sources.
No generated parser or downloaded tool is checked in. The default report path in
the command above is `../evidence/compare.json`.

The report names its command transcript relative to the report directory. Retain
it with that transcript and `scale.json`; validation does not need the original build directory.
`scale.json` records frontend, backend and native-link seconds, throughput,
verified native execution and peak resident bytes (the maximum of per-command
`wait4` peaks). Every arm has the same 180-second source-to-native deadline and
Clang flags; the runner refuses host-limit overrides when measuring defaults.

Validate all three successful scale pipelines and the relocated evidence:

```sh
nice -n 10 python3 examples/dsl-compare/check.py report --relocate --report ../evidence/compare.json
```

## Versioned SDK arm

After packaging and extracting an SDK from the same committed HEAD, add
`--sdk /absolute/path/lang-<version>-x86_64-linux` to the runner. The report keeps
`lang` (source plus bootstrap) and adds `lang-sdk` (prebuilt compiler). Archive
creation and extraction are tool provisioning, outside all arm timers. Both
Lang arms generate the same Tariff frontend and link with the same `-O2` flags;
LOC-only expansion stays outside the timers. The SDK commit must match the
comparison source commit. No compiler limit is changed by this arm.

Both Lang arms use the frontend's transitive standard-library includes. The
redundant explicit `std/core.lang` CLI input is omitted from both: using an
absolute SDK copy as well as relative includes would duplicate declarations.
