# Frozen C conformance contracts

C1, C2 and C3 are mandatory manifests frozen before candidate implementation.
Selection uses a fixed hash ordering of pinned upstream paths, independent of
candidate successes. Each manifest requires 100% of its cases at O0 and O2 on
both targets, plus its raw floor. Higher manifests contain the lower manifests.
No candidate-only skip or replacement can discharge a mandatory case. These are
future gates, not current C-subset passes or ISO certification.

GCC 15.2.0 is pinned to commit 5115c7e447fc07457443df874bf57840e8316d5f.
Its gcc/testsuite/gcc.c-torture tree has 1,890 execution sources (1,677 direct,
213 IEEE), 1,988 compile-only and one unsorted source. Source counts are not
DejaGnu invocation counts. Pin all support files from that tree and GCC's
DejaGnu harness at the same commit. Verify git blob identities before running.
Base reference flags are -std=gnu11 and the selected optimization; case dg-options,
dg-additional-options, .x, effective-target, xfail and option matrices take
precedence exactly as in upstream. Preserve directives verbatim. Unresolved
conditions are unqualified, not successful skips. GNU extensions remain a
separate reported category; gnu11 is deliberately an extension dialect.

c-testsuite is pinned to 5c7275656d751de0e68b2d340a95b5681858ed07, 220
single-exec sources. Standard tags select c89/c99/c11 reference flags; the one
untagged source, 00216.c, uses GNU empty structs, range designators and
zero-length arrays and is explicitly classified as gnu99. Match combined
stdout/stderr to the pinned .expected bytes and require exit zero. Preserve TAP
reporting. Library/cpp requirements remain visible tags, not silent exclusions.

Publish per target and optimization: selected, attempted, execution pass,
compile-only pass, failure, extension, platform skip, expected failure and
unqualified counts. Record every skip's upstream predicate and reference result.
Report raw rates against 220/1890/1988 separately from reference-applicable
rates. Never count compile-only as execution. Freeze a resolved per-platform
reference receipt before implementing that milestone; a source inventory does
not establish applicability. A mandatory platform exclusion leaves its raw gate
incomplete; it cannot shrink the frozen manifest.

C2 additionally requires bidirectional aggregate/union callback ABI, varargs
definitions, volatile, goto and setjmp fixtures. C3 additionally requires every
Lua 5.4.8 production/internal/module C unit, the complete all.lua suite without
_U, internal tests, and mixed native lang/Forth/Lua callbacks on both native
targets. The application requirements do not replace these manifests.

SHA256SUMS locks the mandatory selections and inventory. Any later amendment
must be explicit, independently justified, and published before candidate work.
