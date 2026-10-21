# Catch the spark contract

This is preparation for `bf-f02-w2`, whose existing owner retains the playable
scene and source navigation work. The deliverable here is an executable contract;
the playable scene is pending. The machine-readable authority is
[`game-contract.json`](../game-contract.json).

The selected path is direct Wasm using the existing `web/program_host.js` and
`web/compiler_host.js`. The source pin and roadmap SHA-256 are in the contract.
The native compiler emits the example, and the Wasm-hosted compiler independently
compiles that source and both negative examples. Node executes the existing host
functions and WebAssembly engine for these probes. A real browser interaction
and rendering are still consumer work; no Chromium execution is claimed.

The five-cell board starts at x=0, with one spark at x=3. `a` moves left, `d`
moves right, and `.` waits; positions clamp to 0..4. Touching the spark sets the
score to one for the rest of the replay. There is no random seed, wall clock,
effect, foreign callback, array or scheduler. Input is at most sixteen ASCII
commands. A trailing newline in the input fixture is file framing and is removed
by the replay driver. Each turn emits a line with its index, position and score.
The final line is `caught` or `seek`. Invalid commands and overlong inputs exit 2.

Direct Wasm exports `main`, linear memory and the heap base; it does not export
a persistent tick callback. For the first scene, the owner can keep at most
sixteen commands in JavaScript and call `runLangProgram(bytes, undefined, prefix)`
with a fresh instance after each key press. Render the last state line. The
six-prefix test proves this bounded event strategy without changing the compiler
or introducing a second runtime. Reset clears the prefix. After sixteen turns,
offer reset; do not silently drop or invent inputs. A persistent simulation or
animation loop would need a separate target contract.

After a sanctioned bootstrap has supplied `out/lang`, replay from the repository
root; the module is written outside the checkout:

```sh
LANGBE=wasm LANGOS=wasm ./out/lang example/game/spark.lang -o ../spark.wasm && node test/game_replay.js ../spark.wasm
```

An optional second argument to the replay driver is a freshly built
`compiler.wasm`; it proves compilation and rejection inside the browser compiler
host as well. The registered compiler-Wasm suite builds that compiler through
`web/build_compiler.sh`, using LLVM and wasm-ld. Generated IR is always compiler
output.

The two negative fixtures are `undefined_move.lang` and `unsupported_board.lang`.
Both must exit 1 and leave no Wasm output. The current direct emitter reports the
enclosing function at 2:1, not the individual bad identifier or declaration. The
consumer must navigate to that real location and display the recorded diagnostic;
it must not invent a more precise span. Existing reader-location tests separately
cover precise reader diagnostics for five reader languages.

The baseline records every registered compiler suite and its complete skip list.
The native effects safety matrix owns all allowed optimizer refusals. No new
skip or compiler behavior is authorized. The preserved bootstrap seed, kernel,
readers and existing tests are unchanged by this contract.

Handoff to the existing `bf-f02-w2` owner: consume this document, the contract,
source, input, expected output and error fixtures from the candidate commit.
Build one local scene and one navigable source failure using the selected path;
retain the stated gates and bounds. This artifact transfers the contract locally
without changing ownership or starting a scene, publication or deployment.
