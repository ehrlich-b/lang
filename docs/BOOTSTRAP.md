# Bootstrap and trust chain

Lang is self-hosted: the compiler is written in the language it compiles. The
repository preserves generated LLVM IR so a machine with `clang` can recover
the compiler without trusting a separate implementation.

## Root artifacts

```text
bootstrap/current/
├── COMMIT
├── PROVENANCE
├── compiler_linux.ll
├── compiler_macos.ll
└── lang_reader/source.ast
```

`compiler_linux.ll` and `compiler_macos.ll` are the roots of trust for their
platforms. `PROVENANCE` records hashes and the fixed-point checks used to create
them. Older roots live in `bootstrap/archive/` and in GitHub releases named
`bootstrap-<identity>`. The GitHub tag is an artifact label; the archived
`COMMIT` and `PROVENANCE` files are the authoritative identity and hashes,
including for roots built from a not-yet-pushed or dirty source tree.

Recover a runnable compiler with:

```bash
make init
```

Equivalent manual command on macOS:

```bash
clang -O2 bootstrap/current/compiler_macos.ll -o out/lang
```

Use `compiler_linux.ll` on Linux.

## The one promotion command

After any change under `src/`, run:

```bash
make bootstrap
```

The target performs the full chain:

1. Compile the preserved platform LLVM IR into a trusted compiler.
2. Have that compiler build generation 1.
3. Build generations 2 and 3, then require identical LLVM IR.
4. Emit the lang reader AST twice, then require identical AST output.
5. Generate target-specific Linux and macOS LLVM roots, compile each to a
   cross-target object with `clang`, and link the host artifact.
6. Run the LLVM suite with the final compiler.
7. Archive the previous root to a GitHub release and local cache, stage and
   promote the new root with its identity marker last, then atomically replace
   `out/lang` with the tested binary.

Any failure stops promotion. The archive step requires authenticated GitHub
release access and deliberately happens before either `bootstrap/current/` or
the stable `out/lang` changes. Local retention targets ten live directories and
ten compressed archives, but it deletes an old copy only after verifying the
matching archive asset on GitHub; offline/local bootstraps keep extra history.

## What the fixed points prove

The LLVM comparison:

```text
generation 2 compiler IR == generation 3 compiler IR
```

shows that recompiling the compiler no longer changes its output. The reader
AST comparison separately checks the syntax-to-AST half of the split compiler.
The test suite then checks the behavior of the exact host binary that will be
installed. Target-specific version metadata prevents one platform root from
claiming the host platform's OS or architecture.

A fixed point is strong evidence of self-consistency, not proof that the
compiler is bug-free: a stable miscompile can reproduce itself. That is why the
independent preserved IR, cross-platform `clang` checks, provenance hashes, and
behavioral suite all remain part of promotion.

## Safety rules

- Never copy generated files into `bootstrap/current/` manually.
- Never promote after a failed comparison or test.
- Never edit the preserved LLVM IR by hand.
- Keep compiler changes small enough to bootstrap immediately.
- Commit only after the full bootstrap succeeds.

If bootstrap fails, fix the cause and rerun the one command. Do not stitch
together successful fragments from different attempts.

## Recovery

If `out/lang` is missing or broken, rebuild it from the preserved IR:

```bash
make init
make build
```

Then run the suite. If source no longer compiles with the preserved root, use
Git history or a matching artifact in `bootstrap/archive/`; each archive carries
its source commit and hashes in `PROVENANCE`.
