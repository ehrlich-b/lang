# Problem: --emit-expanded-ast Require Expansion Bug

## Current State (commit 3aba560)
- Bootstrap passes (169/169 tests)
- `make test-composition` FAILS at Step 2

## The Goal
Build composed compilers: `kernel -r lang reader.ast → lang1`

The kernel is built with `--emit-exe-ast` which should expand all includes AND requires into a single AST file that can be compiled with `--embed-self`.

## What We Changed (main.lang)

### Change 1: Added NODE_REQUIRE_DECL handling to expand_collect_decl (lines 222-268)
When processing declarations for --emit-expanded-ast, we now handle `require` the same as `include`:
- Convert module path: "src/lexer" → "src/lexer.lang"
- Check if already in expand_included_map
- If not, read/parse the file and recursively collect its declarations

### Change 2: Pre-populate expand_included_map with input files (lines 1370-1378)
Before processing declarations, we add all command-line input files to expand_included_map:
```lang
var input_count i64 = vec_len(input_files);
var inp_idx i64 = 0;
while inp_idx < input_count {
    var inp_path *u8 = vec_get(input_files, inp_idx);
    map_set(expand_included_map, inp_path, 1);
    inp_idx = inp_idx + 1;
}
```

## The Bug Now
After the changes, kernel.ast is only 5 lines:
```
(program
  (modules "std/core.lang" ... lots of duplicates ...)
  (func ___main ...))
```

All actual declarations (vars, funcs, structs) are MISSING. Only ___main (which is added by build_expanded_program) survives.

## Root Cause Analysis

The problem is the interaction between:
1. How input files are parsed (concatenated and parsed together)
2. How includes work in those files
3. Pre-populating the map

**Key insight**: std/core.lang contains `include "std/os.lang"` at the top. When we process std/core.lang's declarations:
1. First decl is `include "std/os.lang"`
2. We check if "std/os.lang" is in map - NO
3. We add it and try to expand it
4. std/os.lang includes other files...

BUT WAIT - the issue might be different. Let me trace through:

The input files on command line are:
```
std/core.lang src/version_info.lang src/lexer.lang src/parser.lang
src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang
src/sexpr_reader.lang src/main.lang
```

These are all read and concatenated into one source string, then parsed into `prog`.

So `prog` contains declarations from ALL these files mixed together.

When we pre-populate expand_included_map with these paths, we're saying "these files are already processed".

Then when we call expand_collect_decl on each declaration:
- If it's a var/func/struct → add to expand_collected_decls (GOOD)
- If it's an include "X" → check if X in map, expand if not
- If it's a require "Y" → check if Y.lang in map, expand if not

**THE BUG**:
- codegen.lang has `include "src/parser.lang"`
- src/parser.lang is in the input files list
- When we see `include "src/parser.lang"`, we check if "src/parser.lang" is in map
- YES it is! So we skip it entirely
- But we're skipping the INCLUDE DECLARATION, not the content!
- The content from parser.lang is already in prog from direct parsing
- So this should be fine...

Wait, I think I misunderstand. Let me re-read expand_collect_decl:

```lang
if k == NODE_INCLUDE_DECL {
    // Skip if already included
    if map_has(expand_included_map, path_str) {
        return;  // <-- This returns without adding anything!
    }
    // ... expand the include ...
}
```

When we see an include for a file that's already in the map, we `return` without doing anything. This is correct for preventing duplicate expansion.

But the issue is: the declarations from the input files ARE in prog. They're var_decl, func_decl, etc. - NOT include_decl. So they should hit the else branch and be added.

**NEW THEORY**: Maybe the issue is that std/core.lang starts with an include, and something in that expansion chain is wrong?

Let me check std/core.lang structure:
- It has `include "std/os.lang"`
- std/os.lang has OS-specific includes
- Those have the actual libc declarations

When we process std/core.lang's declarations:
1. First decl: `include "std/os.lang"` - not in map, so we expand
2. We read std/os.lang, parse it, call expand_collect_decl recursively on its decls
3. std/os.lang might include std/os/libc_macos.lang
4. That has the actual extern_func declarations for libc

This chain should work...

**WAIT - I FOUND IT!**

Look at expand_collect_decl for NODE_INCLUDE_DECL:
```lang
// Recursively collect declarations
var inc_decls *u8 = program_decls(prog);  // <-- BUG! This should be `prog` from the parsed include!
```

No wait, that's using the local `prog` from the parsed file. Let me check the actual code...

Actually in the code I added for NODE_REQUIRE_DECL, I have:
```lang
var prog *u8 = parse_program();
...
var inc_decls *u8 = program_decls(prog);
```

This shadows the outer `prog` variable! And in the original NODE_INCLUDE_DECL code, it also does:
```lang
var prog *u8 = parse_program();
```

So that should be fine - it's using the local prog from parsing the include file.

**ANOTHER THEORY**: Maybe something is wrong with how parser_tokenize works? If we call parser_tokenize inside expand_collect_decl, it might mess up some global state that affects the outer parsing?

Actually wait - the outer parsing is DONE before we enter expand mode. So that shouldn't matter.

**LET ME CHECK THE SIMPLER CASE**:

What if I remove the pre-population of input files? Then:
- Requires will try to expand files even if content is already in prog
- This causes duplicates (the original problem)

But at least we'd have content!

## The Original Problem (before these changes)
kernel.ast had:
1. All lexer content (from command line)
2. `(require "src/lexer")` nodes from parser.lang and ast_emit.lang (NOT expanded)

When codegen processed this AST with --embed-self:
1. It emitted all lexer content
2. Then saw `(require "src/lexer")` and expanded it again
3. Duplicate TOKEN_EOF!

## Possible Solutions

### Solution A: Don't pre-populate, but filter requires differently
Instead of pre-populating the map, check at require-expansion time if the content is ALREADY in the collected declarations. This is complex.

### Solution B: Remove requires from AST after expansion
After expanding, walk the AST and remove any (require ...) nodes since they're now inlined.

### Solution C: Make codegen smarter about requires
In codegen (not --emit-expanded-ast), track what modules have been processed and skip re-processing. The cg_included_files map should do this, but maybe the key normalization is wrong?

### Solution D: Debug why pre-population breaks things
Add debug output to see exactly what declarations are being collected and why they're missing.

## Files Changed
- `src/main.lang` lines 177-273 (expand_collect_decl function)
- `src/main.lang` lines 1370-1378 (pre-population logic)

## Key Functions to Understand
- `expand_collect_decl(decl)` - Recursively processes declarations, expanding includes/requires
- `build_expanded_program()` - Builds final program from collected declarations + modules node
- `program_decls(prog)` / `program_decl_count(prog)` - Get declarations from parsed program

## Debug Strategy
1. Add print statements in expand_collect_decl to see what decls are being processed
2. Check if decls are actually being added to expand_collected_decls
3. Verify prog has the right declarations before expansion starts

## The Fundamental Tension
- `include` = copy-paste, processed at parse time essentially
- `require` = shared module with visibility boundary

When building an expanded AST for composition:
- We WANT all content inlined (no external file references)
- We DON'T want duplicates
- We need to handle the case where a file is both on command line AND required by another file

The current approach (pre-populate map with input files) assumes that if a file is on the command line, its content is already in prog. But the issue is that the INPUT FILES themselves might have includes that reference OTHER input files, and we're incorrectly skipping those.

Actually no - we're only skipping if the INCLUDE TARGET is in the map. The declarations from input files should still be processed...

## Next Steps
1. Revert the pre-population change
2. Instead, after expanding, REMOVE require nodes from the final AST
3. Or: in codegen's require handling, check if module was already emitted
