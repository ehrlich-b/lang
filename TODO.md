# language - TODO

## Current Focus
Low-hanging fruit and polish

## Phase 3: Reader Macros (COMPLETE)
- [x] Design doc (designs/reader_macro_design.md)
- [x] Lexer: `#name{...}` syntax (TOKEN_READER_MACRO)
- [x] Parser: import, reader declarations, reader expressions
- [x] Codegen: reader registry, interpreter builtins
- [x] Interpreter builtins: lang_number, lang_add/sub/mul/div, peek_char, is_digit, is_space
- [x] Lisp-lite example in example/lisp/
- [x] Test: 130_reader_lisp.lang

## Low-Hanging Fruit (Language)
- [ ] Character literals `'a'` (currently use 97)
- [ ] Bitwise operators `& | ^ << >>`
- [ ] Compound assignment `+= -= *= /=`
- [ ] `for` loop sugar
- [ ] `break` / `continue`
- [ ] Type aliases `type Fd = i64`

## Stdlib Additions
- [ ] `memcpy`, `memset`
- [ ] `itoa` (number to string)
- [ ] String builder
- [ ] `read_file` (returns contents as string)

## Phase 2: Macros (COMPLETE)
- [x] Design macro system (see designs/macro_design.md)
- [x] Add lexer tokens ($, ${, $@, macro keyword)
- [x] Add AST nodes (NODE_QUOTE_EXPR, NODE_UNQUOTE_EXPR, NODE_MACRO_DECL)
- [x] Add parser for quote/unquote/macro
- [x] Add macro registry in codegen
- [x] Implement compile-time interpreter
- [x] Implement quote expansion (substitute unquotes)
- [x] Implement macro expansion in gen_call
- [x] Basic macro tests pass (double, square, nested)
- [x] Add --expand-macros debug flag
- [x] Add ast_to_string(expr) compile-time builtin
- [x] Add $@name (unquote-string) to splice strings as literals

## Backlog (Nice to Have)
- [ ] Deduplicate error messages (use map to track seen errors)
- [ ] Floating point types (f32, f64)
- [ ] Struct literals (`Point{x: 1, y: 2}`)
- [ ] Passing/returning structs by value
- [ ] Extensive examples gallery (after language is "final")

## Completed Phases
- Phase 0: Bootstrap Compiler (Go) - archived at archive/boot-go/
- Phase 1: Self-Hosting - compiler writes itself, fixed point reached
- Phase 1.5/1.6: Stdlib (malloc, vec, map) + Structs
- Phase 2: AST Macros (quote/unquote, compile-time interpreter)
- Phase 3: Reader Macros (syntax extensions, #name{...})

## Future Phases
- Phase 4: Swappable GC (written in .lang, user-replaceable like Zig allocators)
- Phase 5: Maybe LLVM backend

## Research / Tooling
- Debug symbols: DWARF, .debug_* sections, gdb support
- Language crash debugging
- Standard tooling integration (valgrind, perf, etc.)
- "Bring your own GC" research

## Notes
- Bootstrap from bootstrap/v0.1.0.s (or stage1-bootstrap.s)
- 90% that takes half the project, skip the polish
