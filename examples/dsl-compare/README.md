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
production language implementation.

All generated inputs and build products are reproducible from these sources.
No generated parser or downloaded tool is checked in. The default report path in
the command above is `../evidence/compare.json`.

The report names its command transcript relative to the report directory. Retain
those two files together; validation does not need the original build directory:

```sh
nice -n 10 python3 examples/dsl-compare/check.py report --relocate --report ../evidence/compare.json
```
