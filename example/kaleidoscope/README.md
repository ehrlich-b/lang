# Kaleidoscope

A Lang reader for the LLVM tutorial's Chapter 7 language. It emits shared AST
with source spans. Lang lowers the AST to LLVM, and Clang links the program
with the native `putchard` and `printd` runtime.

## Build and run

Run from the repository root with Clang, Python 3 and the libffi development
headers available to `pkg-config`. The commands below use Linux linker flags.

```sh
make kaleidoscope-compiler
out/kaleidoscope/kalc -g test/kaleidoscope/accepted/debug.kal -o out/kaleidoscope/debug.ll
clang -O2 $(pkg-config --cflags libffi) -c example/kaleidoscope/runtime.c -o out/kaleidoscope/runtime.o
clang -O0 -g out/kaleidoscope/debug.ll out/kaleidoscope/runtime.o \
  -rdynamic $(pkg-config --libs libffi) -Wl,--no-as-needed -lm -o out/kaleidoscope/debug
out/kaleidoscope/debug
llvm-dwarfdump --debug-line out/kaleidoscope/debug
llvm-dwarfdump --verify out/kaleidoscope/debug
```

Top-level results and the two tutorial helpers write to stderr. An external
prototype describes a function in the program or a visible host symbol. Host
functions must follow the declared arity and the C ABI with double arguments
and a double result. `-rdynamic` exposes executable symbols to the runtime
and keeping `libm` loaded makes the tutorial's math examples available on
Linux. On macOS, omit `-Wl,--no-as-needed -lm`. Clang writes the debug info to
`out/kaleidoscope/debug.dSYM/Contents/Resources/DWARF/debug`, which is the
input to both `llvm-dwarfdump` commands on macOS.

## Score

Supply a local LLVM `llvmorg-19.1.7` Kaleidoscope suite directory containing
`Chapter7/toy.cpp`, `include/` and `docs/LangImpl0*.rst`. Use Clang++ and
`llvm-config` for the matching LLVM libraries.

```sh
make kaleidoscope-score KALEIDOSCOPE_REF="$LLVM_KALEIDOSCOPE"
make verify VERIFY_CASE=kaleidoscope
python3 -B test/kaleidoscope/count.py "$LLVM_KALEIDOSCOPE"
```

The score is **78/78 matching programs at both `-O0` and `-O2`**, including all
three Chapter 6 Mandelbrot views, and **5/5 matching tutorial rejections**.
The local verify fragment checks 53 original programs and 15 original
rejections. Both checks reported zero reader crashes. Native DWARF verified
at both optimization levels, with unoptimized line rows for every
expression-bearing body line in four functions across two debug fixtures. This includes
a variable on its own line as the target of an assignment.
Grammar, lowering and runtime use 276 lines to Chapter 7's 828, excluding
blank lines and comments in both implementations.

The scorer copies the supplied suite before building. It extracts the tutorial
examples and drops LLVM's REPL prompts and IR dumps from the reference stream. Program output and spacing
remain byte-for-byte comparable, and rejections are compared by outcome.

## Borders

The compiler accepts one complete program per file and checks it before
execution. An error anywhere suppresses evaluation of the file. A declared
host symbol is resolved when called, and an unavailable symbol produces a
runtime error. Native compilation resolves guest definitions across the whole file
after checking calls against the prototypes visible at their source positions.
The reference also has REPL and JIT symbol-lookup behavior when a top-level
expression executes before a later definition or loads a symbol from the host. It bounds recursive
expression parsing to 256 levels. Native debug information covers source
lines and subprograms, with fewer line rows where optimization removes code.
The historical REPL, Chapter 8 object-file tutorial workflow and Chapter 9
variable inspection are outside this compiler's interface.

See [the tutorial map](../../docs/kaleidoscope.md) and [reader friction](FRICTION.md).
