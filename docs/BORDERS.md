# Borders

Zig has no current reader or AIR importer.
The previous experimental approaches were removed.
A maintained frontend for a defined subset is needed.

See [Zig status](../ZIG-STATUS.md) for the history.

| Reader | Feature | LLVM x86-64 | Wasm |
| --- | --- | --- | --- |
| lang | integers | [supported](../test/borders/cases/lang_integers.lang) | [supported](../test/borders/cases/lang_integers.lang) |
| lang | floats | [supported](../test/borders/cases/lang_floats.lang) | [rejected](../test/borders/cases/lang_floats.lang) |
| lang | strings | [supported](../test/borders/cases/lang_strings.lang) | [supported](../test/borders/cases/lang_strings.lang) |
| lang | functions | [supported](../test/borders/cases/lang_functions.lang) | [supported](../test/borders/cases/lang_functions.lang) |
| lang | structs | [supported](../test/borders/cases/lang_structs.lang) | [rejected](../test/borders/cases/lang_structs.lang) |
| minipy | integers | [supported](../test/borders/cases/minipy_integers.lang) | [supported](../test/borders/cases/minipy_integers.lang) |
| minipy | floats | [rejected](../test/borders/cases/minipy_floats.lang) | [rejected](../test/borders/cases/minipy_floats.lang) |
| minipy | strings | [rejected](../test/borders/cases/minipy_strings.lang) | [rejected](../test/borders/cases/minipy_strings.lang) |
| minipy | functions | [supported](../test/borders/cases/minipy_functions.lang) | [supported](../test/borders/cases/minipy_functions.lang) |
| minipy | structs | [rejected](../test/borders/cases/minipy_structs.lang) | [rejected](../test/borders/cases/minipy_structs.lang) |
| minilisp | integers | [supported](../test/borders/cases/minilisp_integers.lang) | [supported](../test/borders/cases/minilisp_integers.lang) |
| minilisp | floats | [wrong](../test/borders/bugs/minilisp_floats_llvm.lang) | [wrong](../test/borders/bugs/minilisp_floats_wasm.lang) |
| minilisp | strings | [wrong](../test/borders/bugs/minilisp_strings_llvm.lang) | [wrong](../test/borders/bugs/minilisp_strings_wasm.lang) |
| minilisp | functions | [supported](../test/borders/cases/minilisp_functions.lang) | [supported](../test/borders/cases/minilisp_functions.lang) |
| minilisp | structs | [rejected](../test/borders/cases/minilisp_structs.lang) | [rejected](../test/borders/cases/minilisp_structs.lang) |
| Zig | missing reader | [rejected at line 1](../test/borders/missing.zig#L1) | [rejected at line 1](../test/borders/missing.zig#L1) |

Zig is rejected before target selection.

Each result is from compiling and running its fixture; a rejection is a compiler or linker error. Exit 42 is the expected result. See `borders.json` for diagnostics and exit codes.
