# language - TODO

## Current Focus
Phase 1.5: Stabilize foundation before adding features

## Immediate Tasks
- [ ] Implement bootstrap design (see designs/bootstrap_design.md)
- [ ] Update documentation (README, LANG.md) to reflect self-hosting

## Phase 1.5: Stdlib Additions (no language changes)
- [ ] `malloc(size)` / `free(ptr)` - real allocator with free list
- [ ] `vec_new()`, `vec_push()`, `vec_get()`, `vec_set()`, `vec_len()` - dynamic array
- [ ] `map_new()`, `map_set()`, `map_get()`, `map_has()` - hash map
- [ ] `str_concat()`, `str_eq()` - string utilities
- [ ] Refactor compiler to use new stdlib

## Phase 1.6: Structs
- [ ] Implement struct parsing in self-hosted compiler
- [ ] Implement struct codegen (field offsets, access)
- [ ] Refactor compiler to use structs
- [ ] Re-reach fixed point

## Completed

### Phase 0: Bootstrap Compiler (Go) - COMPLETE
- [x] Lexer, parser, AST, codegen
- [x] Test suite (68 tests)
- [x] Standard library (std/core.lang)

### Phase 1: Self-Hosting - COMPLETE
- [x] Rewrite lexer in language (src/lexer.lang)
- [x] Rewrite parser in language (src/parser.lang)
- [x] Rewrite codegen in language (src/codegen.lang)
- [x] Compiler compiles itself (lang1)
- [x] Fixed point reached: lang2.s == lang3.s
- [x] Preserved as stage1-bootstrap.s

## Future Phases
- Phase 2: Macros (AST as data, quote/unquote, compile-time eval)
- Phase 3: Syntax extensions (reader macros, custom operators)
- Phase 4: Runtime (GC, maybe LLVM backend)

## Notes
- Go compiler archived at archive/boot-go/
- Bootstrap from stage1-bootstrap.s (will become bootstrap/v0.1.0.s)
- 90% that takes half the project, skip the polish
