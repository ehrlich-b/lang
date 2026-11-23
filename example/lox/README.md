# Lox reader

Lox lowers to native Lang functions through a generated grammar and the shared
AST builders. Lexical resolution gives each local a fixed environment distance.
The embedded runtime supplies boxed values, shared closure frames, fields, bound
methods and superclass lookup.

## Build and run

From the repository root, with Clang, LLVM `lli`, libc and Python 3 available:

```sh
make build
LANGBE=llvm ./out/lang_next compiler lox example/lox/lox.lang \
  --runtime example/lox/runtime.lang -o out/loxc
example/lox/run.sh example/lox/test/classes.lox
env JOBS=2 make verify VERIFY_CASE=lox
```

The runner reports source-located errors with a caret. Exit 65 means the source
failed to compile. Exit 70 means execution reached a Lox runtime error. Set
`LOXC` to use a different minted compiler.

## Score

In a writable Crafting Interpreters checkout at
`4a840f70f69c6ddd17cfef4f6964f8e1bcd8c3d4`, build the reference with `make clox`.
From this repository, run:

```sh
make lox-score LOX_SUITE=/path/to/craftinginterpreters
```

The scorer requires clox to pass all 246 cases, then scores the same cases
against the Lang runner. The measured Lang score is 235/246, up from 58/246,
with zero crashes and zero unlocated rejections.

## Borders

- The runner uses LLVM and system libc. The measured profile is Linux x86-64.
- The compiler reports the first parse or semantic error. Some clox fixtures
  expect multiple errors after recovery or exact wording from its Pratt parser.
- Native functions have a 64-frame call limit including the script. Parser
  work and nesting follow the shared toolkit budget. Native code has different
  limits from clox's bytecode chunks, constants, locals and upvalue tables.
- Boxed values and captured frames live for the process lifetime. Long-running
  allocation-heavy programs can grow memory.
