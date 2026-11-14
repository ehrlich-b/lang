# Borders

Zig has no current reader or AIR importer.
See [Zig status](../ZIG-STATUS.md) for the history.

One small probe per feature, measured separately on each target. A pass describes that probe, not full language compatibility.
LLVM x86-64 uses clang at `-O0`; LLVM-to-Wasm uses clang/wasm-ld and the shipped Node host; direct Wasm uses the same host.
macOS arm64 was not executed on this host.

| Reader | Feature | LLVM x86-64 | LLVM-to-Wasm | Direct Wasm | macOS arm64 |
| --- | --- | --- | --- | --- | --- |
| lang | integers | [supported](../test/borders/cases/lang_integers.lang) | [supported](../test/borders/cases/lang_integers.lang) | [supported](../test/borders/cases/lang_integers.lang) | not-run-here |
| lang | floats | [supported](../test/borders/cases/lang_floats.lang) | [supported](../test/borders/cases/lang_floats.lang) | [supported](../test/borders/cases/lang_floats.lang) | not-run-here |
| lang | strings | [supported](../test/borders/cases/lang_strings.lang) | [supported](../test/borders/cases/lang_strings.lang) | [supported](../test/borders/cases/lang_strings.lang) | not-run-here |
| lang | functions | [supported](../test/borders/cases/lang_functions.lang) | [supported](../test/borders/cases/lang_functions.lang) | [supported](../test/borders/cases/lang_functions.lang) | not-run-here |
| lang | closures | [supported](../test/borders/cases/lang_closures.lang) | [supported](../test/borders/cases/lang_closures.lang) | [rejected](../test/borders/cases/lang_closures.lang) | not-run-here |
| lang | structs | [supported](../test/borders/cases/lang_structs.lang) | [supported](../test/borders/cases/lang_structs.lang) | [rejected](../test/borders/cases/lang_structs.lang) | not-run-here |
| lang | arrays | [supported](../test/borders/cases/lang_arrays.lang) | [supported](../test/borders/cases/lang_arrays.lang) | [rejected](../test/borders/cases/lang_arrays.lang) | not-run-here |
| lang | control_flow | [supported](../test/borders/cases/lang_control_flow.lang) | [supported](../test/borders/cases/lang_control_flow.lang) | [supported](../test/borders/cases/lang_control_flow.lang) | not-run-here |
| lang | recursion | [supported](../test/borders/cases/lang_recursion.lang) | [supported](../test/borders/cases/lang_recursion.lang) | [supported](../test/borders/cases/lang_recursion.lang) | not-run-here |
| lang | effects | [supported](../test/borders/cases/lang_effects.lang) | [rejected](../test/borders/cases/lang_effects.lang) | [rejected](../test/borders/cases/lang_effects.lang) | not-run-here |
| lang | cross_reader_call | [supported](../test/borders/cases/lang_cross_reader_call.lang) | [supported](../test/borders/cases/lang_cross_reader_call.lang) | [supported](../test/borders/cases/lang_cross_reader_call.lang) | not-run-here |
| lang | error_location | [supported](../test/borders/cases/lang_error_location.lang) | [supported](../test/borders/cases/lang_error_location.lang) | [supported](../test/borders/cases/lang_error_location.lang) | not-run-here |
| minipy | integers | [supported](../test/borders/cases/minipy_integers.lang) | [supported](../test/borders/cases/minipy_integers.lang) | [supported](../test/borders/cases/minipy_integers.lang) | not-run-here |
| minipy | floats | [rejected](../test/borders/cases/minipy_floats.lang) | [rejected](../test/borders/cases/minipy_floats.lang) | [rejected](../test/borders/cases/minipy_floats.lang) | not-run-here |
| minipy | strings | [rejected](../test/borders/cases/minipy_strings.lang) | [rejected](../test/borders/cases/minipy_strings.lang) | [rejected](../test/borders/cases/minipy_strings.lang) | not-run-here |
| minipy | functions | [supported](../test/borders/cases/minipy_functions.lang) | [supported](../test/borders/cases/minipy_functions.lang) | [supported](../test/borders/cases/minipy_functions.lang) | not-run-here |
| minipy | closures | [rejected](../test/borders/cases/minipy_closures.lang) | [rejected](../test/borders/cases/minipy_closures.lang) | [rejected](../test/borders/cases/minipy_closures.lang) | not-run-here |
| minipy | structs | [rejected](../test/borders/cases/minipy_structs.lang) | [rejected](../test/borders/cases/minipy_structs.lang) | [rejected](../test/borders/cases/minipy_structs.lang) | not-run-here |
| minipy | arrays | [rejected](../test/borders/cases/minipy_arrays.lang) | [rejected](../test/borders/cases/minipy_arrays.lang) | [rejected](../test/borders/cases/minipy_arrays.lang) | not-run-here |
| minipy | control_flow | [supported](../test/borders/cases/minipy_control_flow.lang) | [supported](../test/borders/cases/minipy_control_flow.lang) | [supported](../test/borders/cases/minipy_control_flow.lang) | not-run-here |
| minipy | recursion | [supported](../test/borders/cases/minipy_recursion.lang) | [supported](../test/borders/cases/minipy_recursion.lang) | [supported](../test/borders/cases/minipy_recursion.lang) | not-run-here |
| minipy | effects | [rejected](../test/borders/cases/minipy_effects.lang) | [rejected](../test/borders/cases/minipy_effects.lang) | [rejected](../test/borders/cases/minipy_effects.lang) | not-run-here |
| minipy | cross_reader_call | [supported](../test/borders/cases/minipy_cross_reader_call.lang) | [supported](../test/borders/cases/minipy_cross_reader_call.lang) | [supported](../test/borders/cases/minipy_cross_reader_call.lang) | not-run-here |
| minipy | error_location | [wrong](../test/borders/bugs/minipy_error_location_llvm.lang) | [wrong](../test/borders/bugs/minipy_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/minipy_error_location_wasm.lang) | not-run-here |
| minilisp | integers | [supported](../test/borders/cases/minilisp_integers.lang) | [supported](../test/borders/cases/minilisp_integers.lang) | [supported](../test/borders/cases/minilisp_integers.lang) | not-run-here |
| minilisp | floats | [wrong](../test/borders/bugs/minilisp_floats_llvm.lang) | [wrong](../test/borders/bugs/minilisp_floats_llvm-wasm.lang) | [wrong](../test/borders/bugs/minilisp_floats_wasm.lang) | not-run-here |
| minilisp | strings | [wrong](../test/borders/bugs/minilisp_strings_llvm.lang) | [wrong](../test/borders/bugs/minilisp_strings_llvm-wasm.lang) | [wrong](../test/borders/bugs/minilisp_strings_wasm.lang) | not-run-here |
| minilisp | functions | [supported](../test/borders/cases/minilisp_functions.lang) | [supported](../test/borders/cases/minilisp_functions.lang) | [supported](../test/borders/cases/minilisp_functions.lang) | not-run-here |
| minilisp | closures | [supported](../test/borders/cases/minilisp_closures.lang) | [supported](../test/borders/cases/minilisp_closures.lang) | [rejected](../test/borders/cases/minilisp_closures.lang) | not-run-here |
| minilisp | structs | [rejected](../test/borders/cases/minilisp_structs.lang) | [rejected](../test/borders/cases/minilisp_structs.lang) | [rejected](../test/borders/cases/minilisp_structs.lang) | not-run-here |
| minilisp | arrays | [rejected](../test/borders/cases/minilisp_arrays.lang) | [rejected](../test/borders/cases/minilisp_arrays.lang) | [rejected](../test/borders/cases/minilisp_arrays.lang) | not-run-here |
| minilisp | control_flow | [supported](../test/borders/cases/minilisp_control_flow.lang) | [supported](../test/borders/cases/minilisp_control_flow.lang) | [rejected](../test/borders/cases/minilisp_control_flow.lang) | not-run-here |
| minilisp | recursion | [supported](../test/borders/cases/minilisp_recursion.lang) | [supported](../test/borders/cases/minilisp_recursion.lang) | [supported](../test/borders/cases/minilisp_recursion.lang) | not-run-here |
| minilisp | effects | [rejected](../test/borders/cases/minilisp_effects.lang) | [rejected](../test/borders/cases/minilisp_effects.lang) | [rejected](../test/borders/cases/minilisp_effects.lang) | not-run-here |
| minilisp | cross_reader_call | [supported](../test/borders/cases/minilisp_cross_reader_call.lang) | [supported](../test/borders/cases/minilisp_cross_reader_call.lang) | [supported](../test/borders/cases/minilisp_cross_reader_call.lang) | not-run-here |
| minilisp | error_location | [wrong](../test/borders/bugs/minilisp_error_location_llvm.lang) | [wrong](../test/borders/bugs/minilisp_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/minilisp_error_location_wasm.lang) | not-run-here |
| c | integers | [supported](../test/borders/cases/c_integers.lang) | [supported](../test/borders/cases/c_integers.lang) | [supported](../test/borders/cases/c_integers.lang) | not-run-here |
| c | floats | [rejected](../test/borders/cases/c_floats.lang) | [rejected](../test/borders/cases/c_floats.lang) | [rejected](../test/borders/cases/c_floats.lang) | not-run-here |
| c | strings | [supported](../test/borders/cases/c_strings.lang) | [supported](../test/borders/cases/c_strings.lang) | [supported](../test/borders/cases/c_strings.lang) | not-run-here |
| c | functions | [supported](../test/borders/cases/c_functions.lang) | [supported](../test/borders/cases/c_functions.lang) | [supported](../test/borders/cases/c_functions.lang) | not-run-here |
| c | closures | not-applicable | not-applicable | not-applicable | not-run-here |
| c | structs | [supported](../test/borders/cases/c_structs.lang) | [supported](../test/borders/cases/c_structs.lang) | [rejected](../test/borders/cases/c_structs.lang) | not-run-here |
| c | arrays | [supported](../test/borders/cases/c_arrays.lang) | [supported](../test/borders/cases/c_arrays.lang) | [rejected](../test/borders/cases/c_arrays.lang) | not-run-here |
| c | control_flow | [supported](../test/borders/cases/c_control_flow.lang) | [supported](../test/borders/cases/c_control_flow.lang) | [supported](../test/borders/cases/c_control_flow.lang) | not-run-here |
| c | recursion | [supported](../test/borders/cases/c_recursion.lang) | [supported](../test/borders/cases/c_recursion.lang) | [supported](../test/borders/cases/c_recursion.lang) | not-run-here |
| c | effects | not-applicable | not-applicable | not-applicable | not-run-here |
| c | cross_reader_call | [supported](../test/borders/cases/c_cross_reader_call.lang) | [supported](../test/borders/cases/c_cross_reader_call.lang) | [supported](../test/borders/cases/c_cross_reader_call.lang) | not-run-here |
| c | error_location | [wrong](../test/borders/bugs/c_error_location_llvm.lang) | [wrong](../test/borders/bugs/c_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/c_error_location_wasm.lang) | not-run-here |
| forth | integers | [supported](../test/borders/cases/forth_integers.lang) | [supported](../test/borders/cases/forth_integers.lang) | [supported](../test/borders/cases/forth_integers.lang) | not-run-here |
| forth | floats | [wrong](../test/borders/bugs/forth_floats_llvm.lang) | [wrong](../test/borders/bugs/forth_floats_llvm-wasm.lang) | [wrong](../test/borders/bugs/forth_floats_wasm.lang) | not-run-here |
| forth | strings | [rejected](../test/borders/cases/forth_strings.lang) | [rejected](../test/borders/cases/forth_strings.lang) | [rejected](../test/borders/cases/forth_strings.lang) | not-run-here |
| forth | functions | [supported](../test/borders/cases/forth_functions.lang) | [supported](../test/borders/cases/forth_functions.lang) | [supported](../test/borders/cases/forth_functions.lang) | not-run-here |
| forth | closures | [rejected](../test/borders/cases/forth_closures.lang) | [rejected](../test/borders/cases/forth_closures.lang) | [rejected](../test/borders/cases/forth_closures.lang) | not-run-here |
| forth | structs | [rejected](../test/borders/cases/forth_structs.lang) | [rejected](../test/borders/cases/forth_structs.lang) | [rejected](../test/borders/cases/forth_structs.lang) | not-run-here |
| forth | arrays | [rejected](../test/borders/cases/forth_arrays.lang) | [rejected](../test/borders/cases/forth_arrays.lang) | [rejected](../test/borders/cases/forth_arrays.lang) | not-run-here |
| forth | control_flow | [supported](../test/borders/cases/forth_control_flow.lang) | [supported](../test/borders/cases/forth_control_flow.lang) | [supported](../test/borders/cases/forth_control_flow.lang) | not-run-here |
| forth | recursion | [supported](../test/borders/cases/forth_recursion.lang) | [supported](../test/borders/cases/forth_recursion.lang) | [supported](../test/borders/cases/forth_recursion.lang) | not-run-here |
| forth | effects | [rejected](../test/borders/cases/forth_effects.lang) | [rejected](../test/borders/cases/forth_effects.lang) | [rejected](../test/borders/cases/forth_effects.lang) | not-run-here |
| forth | cross_reader_call | [supported](../test/borders/cases/forth_cross_reader_call.lang) | [supported](../test/borders/cases/forth_cross_reader_call.lang) | [supported](../test/borders/cases/forth_cross_reader_call.lang) | not-run-here |
| forth | error_location | [wrong](../test/borders/bugs/forth_error_location_llvm.lang) | [wrong](../test/borders/bugs/forth_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/forth_error_location_wasm.lang) | not-run-here |
| flow | integers | [supported](../test/borders/cases/flow_integers.lang) | [supported](../test/borders/cases/flow_integers.lang) | [supported](../test/borders/cases/flow_integers.lang) | not-run-here |
| flow | floats | [rejected](../test/borders/cases/flow_floats.lang) | [rejected](../test/borders/cases/flow_floats.lang) | [rejected](../test/borders/cases/flow_floats.lang) | not-run-here |
| flow | strings | [rejected](../test/borders/cases/flow_strings.lang) | [rejected](../test/borders/cases/flow_strings.lang) | [rejected](../test/borders/cases/flow_strings.lang) | not-run-here |
| flow | functions | [supported](../test/borders/cases/flow_functions.lang) | [supported](../test/borders/cases/flow_functions.lang) | [supported](../test/borders/cases/flow_functions.lang) | not-run-here |
| flow | closures | [rejected](../test/borders/cases/flow_closures.lang) | [rejected](../test/borders/cases/flow_closures.lang) | [rejected](../test/borders/cases/flow_closures.lang) | not-run-here |
| flow | structs | [rejected](../test/borders/cases/flow_structs.lang) | [rejected](../test/borders/cases/flow_structs.lang) | [rejected](../test/borders/cases/flow_structs.lang) | not-run-here |
| flow | arrays | [rejected](../test/borders/cases/flow_arrays.lang) | [rejected](../test/borders/cases/flow_arrays.lang) | [rejected](../test/borders/cases/flow_arrays.lang) | not-run-here |
| flow | control_flow | [supported](../test/borders/cases/flow_control_flow.lang) | [supported](../test/borders/cases/flow_control_flow.lang) | [supported](../test/borders/cases/flow_control_flow.lang) | not-run-here |
| flow | recursion | [supported](../test/borders/cases/flow_recursion.lang) | [supported](../test/borders/cases/flow_recursion.lang) | [supported](../test/borders/cases/flow_recursion.lang) | not-run-here |
| flow | effects | [supported](../test/borders/cases/flow_effects.lang) | [rejected](../test/borders/cases/flow_effects.lang) | [rejected](../test/borders/cases/flow_effects.lang) | not-run-here |
| flow | cross_reader_call | [supported](../test/borders/cases/flow_cross_reader_call.lang) | [supported](../test/borders/cases/flow_cross_reader_call.lang) | [supported](../test/borders/cases/flow_cross_reader_call.lang) | not-run-here |
| flow | error_location | [wrong](../test/borders/bugs/flow_error_location_llvm.lang) | [wrong](../test/borders/bugs/flow_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/flow_error_location_wasm.lang) | not-run-here |
| lox | integers | [supported](../test/borders/cases/lox_integers.lang) | [wrong](../test/borders/bugs/lox_integers_llvm-wasm.lang) | [wrong](../test/borders/bugs/lox_integers_wasm.lang) | not-run-here |
| lox | floats | [supported](../test/borders/cases/lox_floats.lang) | [wrong](../test/borders/bugs/lox_floats_llvm-wasm.lang) | [wrong](../test/borders/bugs/lox_floats_wasm.lang) | not-run-here |
| lox | strings | [supported](../test/borders/cases/lox_strings.lang) | [wrong](../test/borders/bugs/lox_strings_llvm-wasm.lang) | [wrong](../test/borders/bugs/lox_strings_wasm.lang) | not-run-here |
| lox | functions | [supported](../test/borders/cases/lox_functions.lang) | [wrong](../test/borders/bugs/lox_functions_llvm-wasm.lang) | [wrong](../test/borders/bugs/lox_functions_wasm.lang) | not-run-here |
| lox | closures | [supported](../test/borders/cases/lox_closures.lang) | [wrong](../test/borders/bugs/lox_closures_llvm-wasm.lang) | [wrong](../test/borders/bugs/lox_closures_wasm.lang) | not-run-here |
| lox | structs | [rejected](../test/borders/cases/lox_structs.lang) | [rejected](../test/borders/cases/lox_structs.lang) | [rejected](../test/borders/cases/lox_structs.lang) | not-run-here |
| lox | arrays | [rejected](../test/borders/cases/lox_arrays.lang) | [rejected](../test/borders/cases/lox_arrays.lang) | [rejected](../test/borders/cases/lox_arrays.lang) | not-run-here |
| lox | control_flow | [rejected](../test/borders/cases/lox_control_flow.lang) | [rejected](../test/borders/cases/lox_control_flow.lang) | [rejected](../test/borders/cases/lox_control_flow.lang) | not-run-here |
| lox | recursion | [rejected](../test/borders/cases/lox_recursion.lang) | [rejected](../test/borders/cases/lox_recursion.lang) | [rejected](../test/borders/cases/lox_recursion.lang) | not-run-here |
| lox | effects | not-applicable | not-applicable | not-applicable | not-run-here |
| lox | cross_reader_call | [wrong](../test/borders/bugs/lox_cross_reader_call_llvm.lang) | [wrong](../test/borders/bugs/lox_cross_reader_call_llvm-wasm.lang) | [wrong](../test/borders/bugs/lox_cross_reader_call_wasm.lang) | not-run-here |
| lox | error_location | [supported](../test/borders/cases/lox_error_location.lang) | [supported](../test/borders/cases/lox_error_location.lang) | [supported](../test/borders/cases/lox_error_location.lang) | not-run-here |
| lua | integers | [supported](../test/borders/cases/lua_integers.lang) | [supported](../test/borders/cases/lua_integers.lang) | [supported](../test/borders/cases/lua_integers.lang) | not-run-here |
| lua | floats | [rejected](../test/borders/cases/lua_floats.lang) | [rejected](../test/borders/cases/lua_floats.lang) | [rejected](../test/borders/cases/lua_floats.lang) | not-run-here |
| lua | strings | [rejected](../test/borders/cases/lua_strings.lang) | [rejected](../test/borders/cases/lua_strings.lang) | [rejected](../test/borders/cases/lua_strings.lang) | not-run-here |
| lua | functions | [rejected](../test/borders/cases/lua_functions.lang) | [rejected](../test/borders/cases/lua_functions.lang) | [rejected](../test/borders/cases/lua_functions.lang) | not-run-here |
| lua | closures | [rejected](../test/borders/cases/lua_closures.lang) | [rejected](../test/borders/cases/lua_closures.lang) | [rejected](../test/borders/cases/lua_closures.lang) | not-run-here |
| lua | structs | [rejected](../test/borders/cases/lua_structs.lang) | [rejected](../test/borders/cases/lua_structs.lang) | [rejected](../test/borders/cases/lua_structs.lang) | not-run-here |
| lua | arrays | [rejected](../test/borders/cases/lua_arrays.lang) | [rejected](../test/borders/cases/lua_arrays.lang) | [rejected](../test/borders/cases/lua_arrays.lang) | not-run-here |
| lua | control_flow | [rejected](../test/borders/cases/lua_control_flow.lang) | [rejected](../test/borders/cases/lua_control_flow.lang) | [rejected](../test/borders/cases/lua_control_flow.lang) | not-run-here |
| lua | recursion | [rejected](../test/borders/cases/lua_recursion.lang) | [rejected](../test/borders/cases/lua_recursion.lang) | [rejected](../test/borders/cases/lua_recursion.lang) | not-run-here |
| lua | effects | [rejected](../test/borders/cases/lua_effects.lang) | [rejected](../test/borders/cases/lua_effects.lang) | [rejected](../test/borders/cases/lua_effects.lang) | not-run-here |
| lua | cross_reader_call | [rejected](../test/borders/cases/lua_cross_reader_call.lang) | [rejected](../test/borders/cases/lua_cross_reader_call.lang) | [rejected](../test/borders/cases/lua_cross_reader_call.lang) | not-run-here |
| lua | error_location | [wrong](../test/borders/bugs/lua_error_location_llvm.lang) | [wrong](../test/borders/bugs/lua_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/lua_error_location_wasm.lang) | not-run-here |
| tiny | integers | [supported](../test/borders/cases/tiny_integers.lang) | [supported](../test/borders/cases/tiny_integers.lang) | [supported](../test/borders/cases/tiny_integers.lang) | not-run-here |
| tiny | floats | not-applicable | not-applicable | not-applicable | not-run-here |
| tiny | strings | [rejected](../test/borders/cases/tiny_strings.lang) | [rejected](../test/borders/cases/tiny_strings.lang) | [rejected](../test/borders/cases/tiny_strings.lang) | not-run-here |
| tiny | functions | [rejected](../test/borders/cases/tiny_functions.lang) | [rejected](../test/borders/cases/tiny_functions.lang) | [rejected](../test/borders/cases/tiny_functions.lang) | not-run-here |
| tiny | closures | [rejected](../test/borders/cases/tiny_closures.lang) | [rejected](../test/borders/cases/tiny_closures.lang) | [rejected](../test/borders/cases/tiny_closures.lang) | not-run-here |
| tiny | structs | [rejected](../test/borders/cases/tiny_structs.lang) | [rejected](../test/borders/cases/tiny_structs.lang) | [rejected](../test/borders/cases/tiny_structs.lang) | not-run-here |
| tiny | arrays | [rejected](../test/borders/cases/tiny_arrays.lang) | [rejected](../test/borders/cases/tiny_arrays.lang) | [rejected](../test/borders/cases/tiny_arrays.lang) | not-run-here |
| tiny | control_flow | [rejected](../test/borders/cases/tiny_control_flow.lang) | [rejected](../test/borders/cases/tiny_control_flow.lang) | [rejected](../test/borders/cases/tiny_control_flow.lang) | not-run-here |
| tiny | recursion | [rejected](../test/borders/cases/tiny_recursion.lang) | [rejected](../test/borders/cases/tiny_recursion.lang) | [rejected](../test/borders/cases/tiny_recursion.lang) | not-run-here |
| tiny | effects | [rejected](../test/borders/cases/tiny_effects.lang) | [rejected](../test/borders/cases/tiny_effects.lang) | [rejected](../test/borders/cases/tiny_effects.lang) | not-run-here |
| tiny | cross_reader_call | [rejected](../test/borders/cases/tiny_cross_reader_call.lang) | [rejected](../test/borders/cases/tiny_cross_reader_call.lang) | [rejected](../test/borders/cases/tiny_cross_reader_call.lang) | not-run-here |
| tiny | error_location | [wrong](../test/borders/bugs/tiny_error_location_llvm.lang) | [wrong](../test/borders/bugs/tiny_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/tiny_error_location_wasm.lang) | not-run-here |
| calc | integers | [supported](../test/borders/cases/calc_integers.lang) | [supported](../test/borders/cases/calc_integers.lang) | [supported](../test/borders/cases/calc_integers.lang) | not-run-here |
| calc | floats | [rejected](../test/borders/cases/calc_floats.lang) | [rejected](../test/borders/cases/calc_floats.lang) | [rejected](../test/borders/cases/calc_floats.lang) | not-run-here |
| calc | strings | [rejected](../test/borders/cases/calc_strings.lang) | [rejected](../test/borders/cases/calc_strings.lang) | [rejected](../test/borders/cases/calc_strings.lang) | not-run-here |
| calc | functions | [rejected](../test/borders/cases/calc_functions.lang) | [rejected](../test/borders/cases/calc_functions.lang) | [rejected](../test/borders/cases/calc_functions.lang) | not-run-here |
| calc | closures | [rejected](../test/borders/cases/calc_closures.lang) | [rejected](../test/borders/cases/calc_closures.lang) | [rejected](../test/borders/cases/calc_closures.lang) | not-run-here |
| calc | structs | [rejected](../test/borders/cases/calc_structs.lang) | [rejected](../test/borders/cases/calc_structs.lang) | [rejected](../test/borders/cases/calc_structs.lang) | not-run-here |
| calc | arrays | [rejected](../test/borders/cases/calc_arrays.lang) | [rejected](../test/borders/cases/calc_arrays.lang) | [rejected](../test/borders/cases/calc_arrays.lang) | not-run-here |
| calc | control_flow | [rejected](../test/borders/cases/calc_control_flow.lang) | [rejected](../test/borders/cases/calc_control_flow.lang) | [rejected](../test/borders/cases/calc_control_flow.lang) | not-run-here |
| calc | recursion | [rejected](../test/borders/cases/calc_recursion.lang) | [rejected](../test/borders/cases/calc_recursion.lang) | [rejected](../test/borders/cases/calc_recursion.lang) | not-run-here |
| calc | effects | [rejected](../test/borders/cases/calc_effects.lang) | [rejected](../test/borders/cases/calc_effects.lang) | [rejected](../test/borders/cases/calc_effects.lang) | not-run-here |
| calc | cross_reader_call | [rejected](../test/borders/cases/calc_cross_reader_call.lang) | [rejected](../test/borders/cases/calc_cross_reader_call.lang) | [rejected](../test/borders/cases/calc_cross_reader_call.lang) | not-run-here |
| calc | error_location | [wrong](../test/borders/bugs/calc_error_location_llvm.lang) | [wrong](../test/borders/bugs/calc_error_location_llvm-wasm.lang) | [wrong](../test/borders/bugs/calc_error_location_wasm.lang) | not-run-here |

Totals: not-applicable: 12, rejected: 170, supported: 132, wrong: 46.

Ordinary probes compile, link, and run against explicit exit-code and stdout oracles in `test/borders/probes.json` (usually exit 42; Lox prints a value, Lua asserts). Rejected means compilation or linking failed; wrong means an oracle mismatch; crash includes target traps and timeouts.
Error-location probes intentionally fail compilation: supported requires the expected guest line/column (Lox reports a line). A wrapper-file error alone is wrong. These cells do not claim successful target execution.
See `borders.json` for every command, stage, exit code, source hash, stdout, stderr, and rejection diagnostic. Wrong/crash reproducers and reduction notes live in [bugs](../test/borders/bugs/README.md).

- c/closures: C has no lexical closures in its source language.
- c/effects: C has no algebraic effect syntax; calls to effectful foreign functions are a separate ABI question.
- lox/effects: Lox has no algebraic effects or exceptions in its source language.
- tiny/floats: Tiny exposes only an i64 main result, with no float operations or conversions to observe fractional values.

Regenerate with `COMPILER=out/lang_next python3 -B test/borders/run.py`; check this document with `python3 -B test/borders/render.py`. Filtered runs (`--reader`, `--target`, `--feature`) print fragment results without changing the published grid.
