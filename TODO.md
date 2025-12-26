# language - TODO

## Current Focus
Phase 2: Macros - completing the AST-based macro system

## Phase 2: Macros (WORKING)
- [x] Design macro system (see designs/macro_design.md)
- [x] Add lexer tokens ($, ${, $@, macro keyword)
- [x] Add AST nodes (NODE_QUOTE_EXPR, NODE_UNQUOTE_EXPR, NODE_MACRO_DECL)
- [x] Add parser for quote/unquote/macro
- [x] Add macro registry in codegen
- [x] Implement compile-time interpreter
- [x] Implement quote expansion (substitute unquotes)
- [x] Implement macro expansion in gen_call
- [x] Basic macro tests pass (double, square, nested)
- [ ] Add --expand-macros debug flag
- [ ] Write debug(x) macro with ast_to_string
- [ ] Extensive examples gallery with cool macro uses

## Phase 1.5/1.6: COMPLETE
- Stdlib: malloc, free, vec, map, str_concat, str_dup
- Structs: parsing, codegen, field access, pointer-to-struct

## Completed Phases
- Phase 0: Bootstrap Compiler (Go) - archived at archive/boot-go/
- Phase 1: Self-Hosting - compiler writes itself, fixed point reached

## Future Phases
- Phase 3: Syntax extensions (reader macros, custom operators)
- Phase 4: Runtime (GC, maybe LLVM backend)

## Research / Tooling
- Debug symbols: DWARF, .debug_* sections, gdb support
- Language crash debugging
- Standard tooling integration (valgrind, perf, etc.)
- "Bring your own GC" research

## Notes
- Bootstrap from bootstrap/v0.1.0.s (or stage1-bootstrap.s)
- 90% that takes half the project, skip the polish
