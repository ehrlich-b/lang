# Borders

Zig has no current reader or AIR importer.
See [Zig status](../ZIG-STATUS.md) for the history.

| Reader | Feature | LLVM x86-64 | Direct Wasm | macOS arm64 |
| --- | --- | --- | --- | --- |
| lang | integers | [supported](../test/borders/cases/lang_integers.lang) | [supported](../test/borders/cases/lang_integers.lang) | not-run-here |
| lang | floats | [supported](../test/borders/cases/lang_floats.lang) | [rejected](../test/borders/cases/lang_floats.lang) | not-run-here |
| lang | strings | [supported](../test/borders/cases/lang_strings.lang) | [supported](../test/borders/cases/lang_strings.lang) | not-run-here |
| lang | functions | [supported](../test/borders/cases/lang_functions.lang) | [supported](../test/borders/cases/lang_functions.lang) | not-run-here |
| lang | structs | [supported](../test/borders/cases/lang_structs.lang) | [rejected](../test/borders/cases/lang_structs.lang) | not-run-here |
| minipy | integers | [supported](../test/borders/cases/minipy_integers.lang) | [supported](../test/borders/cases/minipy_integers.lang) | not-run-here |
| minipy | floats | [rejected](../test/borders/cases/minipy_floats.lang) | [rejected](../test/borders/cases/minipy_floats.lang) | not-run-here |
| minipy | strings | [rejected](../test/borders/cases/minipy_strings.lang) | [rejected](../test/borders/cases/minipy_strings.lang) | not-run-here |
| minipy | functions | [supported](../test/borders/cases/minipy_functions.lang) | [supported](../test/borders/cases/minipy_functions.lang) | not-run-here |
| minipy | structs | [rejected](../test/borders/cases/minipy_structs.lang) | [rejected](../test/borders/cases/minipy_structs.lang) | not-run-here |
| minilisp | integers | [supported](../test/borders/cases/minilisp_integers.lang) | [supported](../test/borders/cases/minilisp_integers.lang) | not-run-here |
| minilisp | floats | [wrong](../test/borders/bugs/minilisp_floats_llvm.lang) | [wrong](../test/borders/bugs/minilisp_floats_wasm.lang) | not-run-here |
| minilisp | strings | [wrong](../test/borders/bugs/minilisp_strings_llvm.lang) | [wrong](../test/borders/bugs/minilisp_strings_wasm.lang) | not-run-here |
| minilisp | functions | [supported](../test/borders/cases/minilisp_functions.lang) | [supported](../test/borders/cases/minilisp_functions.lang) | not-run-here |
| minilisp | structs | [rejected](../test/borders/cases/minilisp_structs.lang) | [rejected](../test/borders/cases/minilisp_structs.lang) | not-run-here |

Totals: rejected: 10, supported: 16, wrong: 4.

Each measured result comes from compiling and running its fixture; a rejection is a compiler or linker error. Exit 42 is the expected result. See `borders.json` for diagnostics and exit codes.
