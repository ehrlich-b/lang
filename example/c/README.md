# C reader

The standalone reader builds and runs C translation units on Linux x86-64
with the System V LP64 ABI. It scored **174/220** on the c-testsuite
single-exec corpus, up from **54/220** at the starting revision. All 46
rejections had source diagnostics, with zero crashes or LLVM verifier failures.

## Build and run

From the Lang repository root, with Clang, Make and Python 3 available:

```sh
make c-reader
python3 example/c/driver.py build example/c/fixtures/layout_and_flow.c -o out/sample
./out/sample
```

The driver uses `clang -E` for preprocessing, with local declarations for a
subset of libc headers. It passes the expanded source to `out/c-reader`.
Generated Lang grammars recognize the translation unit. The reader resolves C
types and names, computes layout and lowers to Lang AST. The minted compiler
emits LLVM IR, which Clang links with the native adapter and system libc.
Preprocessor line markers map diagnostics back to the original file, including
local headers. Columns within macro expansions are approximate.

Use `example/c/c.lang` for the existing embedded `#c{…}` reader and its Lang
interop ABI. For standalone C, `example/c/translation_unit.lang` supplies the
`c` reader to the compiler-minting command.

## Score

```sh
make c-score C_TESTSUITE=/path/to/c-testsuite
env JOBS=2 make verify VERIFY_CASE=c-reader
```

Each score row requires native linking, zero exit status and byte-for-byte
stdout equality against the corresponding `.c.expected` file. Both the score
and fixture runners isolate execution in temporary directories and enforce time
limits. The default `make verify` runs the C fixtures on Linux x86-64.

## Language borders

The standalone reader covers the LP64 integer types, integer promotions,
narrowing, pointers, arrays, basic and nested structs, enumerators, file-scope
typedefs, direct calls, scalar casts, `sizeof`, and scalar and braced aggregate
initialization. Loops implement `break` and `continue`, and switch supports
fallthrough between labels at the top level of a braced switch body.

Current borders include unions, bitfields, floating point, wide literals,
function pointers, variadic definitions, general native variadic calls,
aggregate copies and value calls, compound literals, brace elision,
block-scope typedefs and prototypes, variable-length arrays, qualified array
parameters, nested case labels, goto, GNU statement expressions, and C11
generic selection. Qualifiers are parsed with limited semantic enforcement.
The libc headers are the declarations under [include](include), and
`printf` and `sprintf` support integer and pointer arguments through arity 12.
One macro-heavy corpus input exceeds the toolkit's recognition budget.

[FRICTION.md](FRICTION.md) records the accommodations for the toolkit and core.
