# Follow a shipping policy through lowering

The existing [shipping source](../example/shipping/policy.shipping) sets a base
fee of 10 and an inclusive free-shipping threshold of 100. Its path is:

```text
policy.shipping → actual tokenizer → generated grammar tree
                → shipping reader's shared AST → LLVM + project runtime
                → Clang and system linker → native executable
```

The [grammar and reader](../example/shipping/shipping.lang) expose distinct
decisions. Grammar captures `settings`, `name` and `value`, preserving half-open
UTF-8 byte spans. The reader checks known names, duplicates, required settings
and decimal range. It elaborates the constants into `shipping_cost(total: i64)`:
return 0 when `total >= 100`, otherwise return 10. These are frontend semantics;
the shared compiler sees ordinary functions, integers, comparison and calls.

Core inspection shows calls to `shipping_total` and `shipping_print`. The
[project manifest](../example/shipping/project.lang-project) explicitly selects
the [runtime](../example/shipping/runtime.lang), which includes `std/core.lang`.
LLVM inspection includes that implementation; Clang and the system linker
produce a Linux x86-64 executable with its platform and libc dependencies.
The reader runs as a trusted native build program. This establishes neither a
runtime-free implementation nor a bootstrap proof.

With the reviewed PM input repository available at `sources/pm-inputs`, run from
the checkout root:

```bash
nice -n 10 python3 -B test/reader_author/lowering_walkthrough.py --replay --repo . --inputs sources/pm-inputs
nice -n 10 python3 -B test/reader_author/lowering_walkthrough.py --selftest --repo . --inputs sources/pm-inputs
```

The fragment builds current sources, uses existing `inspect` commands, compares
core inspection with `read`, links the inspected LLVM and requires literal
stdout `10\n`, `0\n`, `0\n` for totals 99, 100 and 101. The existing unknown-setting
fixture must produce a located error and empty core/LLVM stdout. It also rejects
changed inputs, forged native results and missing evidence in separate copies.
Both modes replay these small cases and run the evidence mutations.

The default external output directory is `../evidence/lowering-walkthrough/`;
override it with `--evidence DIR`. `WALKTHROUGH.md` maps six observations to exact
retained source lines and artifacts. `trace.json`, `commands.jsonl` and
`result.json` bind them to the product commit, frozen input hashes, raw argv,
exit status and stdout/stderr. `check.py` is a copy of the committed fragment.
No new reader or shared core rule is introduced.
