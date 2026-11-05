# Borders reproducers

These are failures of the named probe's oracle, not assertions that the reader
implements the entire feature. Run a single cell with, for example:

```sh
COMPILER=out/lang_next python3 -B test/borders/run.py --reader minilisp --target wasm --feature floats --minimality --verify
```

The full grid records executions of the files linked here, including compiler,
linker and target-runtime failures. The ordinary cases remain available separately.
`minimality.json` binds each current bug to its source hash and records executed
include- and host-declaration-deletion trials. Reader definitions are protected because removing one
changes the language boundary being measured; both readers are protected for a
cross-reader call. Runtime includes are retained only when their deletion changes
the observed failure. Complete host declarations (including `main`) are removed
when their deletion preserves the status, phase, exit code, stdout and stderr.
Preparation repeats both kinds of deletion to a fixed point; `--minimality`
executes every remaining candidate and fails if any preserves that symptom.
Reader bodies remain feature-bearing units rather than being parsed as host code.
Use `--reader NAME --prepare-bugs --output FILE` to reproduce those reductions
without regenerating the whole grid.

The semantic bodies are small feature-preserving units:

- Minilisp floats: one addition of two fractional literals whose sum is 42;
  replacing them by integers tests the ordinary arithmetic control. A single
  `42.0` literal is insufficient: integer truncation would falsely pass it.
- Minilisp strings: one one-character string and a length operation, returning
  the expected length 1 directly. This reduces the previous five-byte string,
  arithmetic bias, and multi-branch assertion. Removing the string or length operation
  ceases to test the string boundary.
- Forth floats: one zero-argument word with two fractional literals and addition.
  The scanner treats the decimal dots as output words; stdout and exit are both
  checked. Whole literals cannot be removed without changing the arithmetic probe.
- Flow error location: one malformed return in one function, with the missing operand
  immediately after `+` at guest line 2, column 22. No effect runtime or host
  `main` is needed: the reader fails before target code generation.
- Lox LLVM-to-Wasm: the smallest feature-bearing print expression/declaration(s)
  for each row. Instantiation fails on the shipped host's missing `strtod` import;
  these are host/runtime borders. A native control distinguishes a reader failure
  from a target host limitation. Functions and closures retain the declarations,
  capture, escape, and call needed to exercise those features.
- Lox cross-reader call: one C function and one Lox call; the native program reports
  an undefined Lox variable despite the C symbol being present. Removing the C
  definition would stop testing interoperability. On LLVM-to-Wasm the missing
  host import is encountered first.
- Lua and calc error locations: one invalid expression with a single bad token.
  They report a general message and a wrapper-file location, not a guest location.

These are minimal with respect to the feature-bearing unit and removable runtime
includes and host declarations, rather than a claim about global byte-minimality
across all spellings.
