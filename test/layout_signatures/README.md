These fixtures specify parameter admission independently in Lang and handwritten
core. Core is never obtained from compiler AST output. expected.json fixes exits,
layout diagnostics, source coordinates and existing LLVM signature fragments.
The 10^9 nested counts each fit the core reader; their i64 storage needs 8*10^27
bytes, beyond the native signed 64-bit limit. The 65536^2 u8 parameter fits that
limit and exceeds the wasm32 limit (2^32-1).

Array parameters retain integer/address slots. Executed controls include real
array storage at the caller, unused array parameters, an independently linked
extern definition, indirect lambda calls, and scalar/pointer values crossing
calls. They do not qualify array indexing through parameters or a new array ABI.
Spanned core inputs use diagnostic.read; spanless core and Lang lambda nodes
(which the existing parser leaves without an origin) have a plain error prefix.
A negative core count is rejected by the existing integer reader before layout;
the overflow witnesses instead reach layout with individually in-range counts.

Run python3 test/run_layout_signatures.py --compiler PATH --evidence DIRECTORY
and repeat with python3 -O. The evidence directory must be outside the checkout.
The runner uses explicit checks in both Python modes and retains every compiler,
assembler/linker and executable invocation with input and log hashes.
