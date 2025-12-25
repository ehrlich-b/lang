# language - TODO

## Current Focus
Phase 1: Self-hosting (rewrite compiler in language)

## Milestone Checklist

### Phase 0: Bootstrap Compiler (Go) ✓ COMPLETE
- [x] Finalize syntax decisions (see INITIAL_DESIGN.md)
- [x] Lexer
- [x] Parser
- [x] AST types
- [x] x86-64 code generation
- [x] Hello world compiles and runs
- [x] Compiler can compile a simple program (fibonacci, etc.)
- [x] Test suite (67 tests)
- [x] Standard library (std/core.lang)

### Phase 1: Self-Hosting
- [x] Rewrite lexer in language (src/lexer.lang)
- [x] Rewrite parser in language (src/parser.lang)
- [ ] Rewrite codegen in language
- [ ] Compiler compiles itself (stage 1)
- [ ] Stage 1 compiles itself to identical output (stage 2)

### Phase 2: Macros
- [ ] AST as first-class data
- [ ] Quote syntax `#{ }`
- [ ] Unquote/splice `${ }`
- [ ] `macro` declarations
- [ ] Compile-time evaluation

### Phase 3: Syntax Extensions
- [ ] Reader macros or syntax rules
- [ ] Custom operators
- [ ] DSL demo ("looks like Python")

### Phase 4: Runtime
- [ ] Mark-sweep GC
- [ ] LLVM backend (optional)

## Notes
- 90% that takes half the project, skip the polish
- Stop shortly after MVP
- It can be a mess, but should be legitimately functional
