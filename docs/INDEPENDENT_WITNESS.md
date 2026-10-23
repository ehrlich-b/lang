# Independent core witness

After committing the candidate, run `make bootstrap-verify JOBS=2`, then:

```
python3 scripts/check_shared_witness.py --evidence ../evidence/witness
python3 scripts/check_shared_witness.py --controls-only --evidence ../evidence/controls
python3 -O scripts/check_shared_witness.py --controls-only --evidence ../evidence/optimized
```

Evidence must be outside the checkout. Qualification requires native Linux
x86-64. Three labelled legs execute the same frozen `expected.json` vectors at
O0 and O2: Lang, handwritten core, and generated round trip. `program.ast` is
handwritten, passed directly to `--from-ast`, and never an emitter destination.
Only the third leg uses `--emit-expanded-ast`, into a fresh evidence directory.
The checker binds tracked fixture bytes to HEAD, hashes direct inputs before
commands and again at completion, and records argv, cwd, exit codes, output
hashes, modules, vectors and results. Reader contracts remain frozen separately.

The expected vectors were specified independently of either reader: reduce
both u8 operands and their sum modulo 256 (255+1 gives 0, 128+255 gives 127,
(2^64-1)+2 gives 1). Signed i8 comparison interprets 128 as -128 and 255 as -1;
127 is positive. Unsigned u64 comparison places 2^63 above 2^63-1 and 2^64-1
above 0 and 1. The byte array sum is 10+20+12=42. Zero-length, nested, f32 and
f64 storage declarations exercise allocation, but the sum does not measure
those sizes. The retained C layout oracle independently checks sizes, alignment,
strides, unsupported types and wasm32 layout constants.

`rejections.json` specifies handwritten inputs, diagnostics, supplied spans and
expected diagnostic locations. In `diagnostic.read`, [4,7) is `bad`, line 2,
column 3. Invalid numeric operations preserve that span. The current layout
rejection of `[0]void` loses the declaration span and reports line 1, column 1;
the checker records and verifies that limitation. Counts 2^63, 2^64-1 and nested
2^32 counts reject in the core parser with `span-overflow`; negative counts use
`invalid-span-number`. These are current parser diagnostics, not proof that
layout accepted those counts. Lang's signed-count rejection is checked under
its own diagnostic. No equal-message claim is made across readers. Every
rejection must exit nonzero, identify its origin and leave no nonempty module.
Malformed operators, negative spans and out-of-range spans also reject loudly.

Controls run even with `--controls-only`: replace handwritten `add_wrap` with
`sub_wrap`, or change the first expected result to 1. Both actually compile,
link and execute at O0/O2; the same comparator must observe wrong answers.
The report retains all mismatches. A span control moves the numeric diagnostic
to column 2 and refuses the original column-3 expectation. Receipt controls
reject stale revisions, substituted compilers, changed source and artifact
hashes under ordinary and optimized Python. The reader-local duplicate control
remains active. Explicit checks keep all controls effective under Python `-O`.

Existing storage, numeric and Lang decimal-f32 checks remain active; the separate
f32 literal checker is retained unchanged. Decimal core tokens, full aggregate
layout/ABI and native arm64 execution remain unqualified. Global f32 aggregate
and nonliteral element lowering are outside this witness qualification.
