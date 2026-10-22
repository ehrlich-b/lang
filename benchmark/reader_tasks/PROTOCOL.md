# Paired comparison protocol

Question: for already supported reader features, what correctness and total
elapsed authoring plus review time does each language require under the same
budget? These packets do not answer that question until a comparison is run.

1. Before any trial, commit the corpus hashes, run the operator's freeze check,
   and record its Git commit, hash list, assignment seed, model/tool versions,
   machine/compiler versions, time budget, and allowed documentation. No model
   trial is part of the corpus handoff. Use only the exported participant packet
   and its pinned toolkit during future trials: the compiler SHA-256 and public
   std/src/docs revision are in toolkit.json; no checkout is required. The operator
   retains the hidden cases and fixed fixtures outside participant access.
2. Assignment order is ascending SHA-256 of `seed/task_id`, with languages within
   each task ordered by SHA-256 of `seed/task_id/language`. This deterministic
   randomization is reproducible across Python versions. Choose a fresh seed
   before work; never search seeds based on performance. Paired languages receive
   the same specification, inputs, budget, hardware, context allowance, and tools.
   Run in fresh sessions with no cross-language solution transfer. Predeclare
   repeats and use a new assignment seed per repeat; preserve every repeat.
3. For every assigned task/language, record one authoring interval and one review
   interval, including failed and abstained tasks. Use a common monotonic clock in
   seconds and sequential, nonoverlapping intervals. Authoring includes reading,
   planning, code generation, editing, tool waits, build failures, retries, local
   testing and final build. Review starts at handoff and includes inspection,
   correction, rebuilding and retesting through the final decision. Setup shared
   by the whole experiment is separately reported and allocated equally; any
   language-specific setup belongs in that language's first authoring interval.
   Unattended fixed fixtures have zero human review, explicitly recorded; their
   preparation/build/test durations are not agent authoring-time estimates.
4. Freeze the final submission and timing ledger before revealing hidden results.
   JSON ledger rows have `id`, `language` (`Lang` or `Python`), `phase` (`authoring`
   or `review`), `start`, `end`. Every cell needs both phases, even if duration is
   zero. Missing, negative, nonfinite, duplicate, or overlapping intervals are
   invalid. An exhausted budget ends the task; record remaining abstentions with
   zero additional time and label the budget exhaustion in the study record.
5. A solution is an argv array of absolute executable/file paths accepting source in its final argument
   and printing exactly one typed JSON response. Use an absolute-path wrapper
   script for flags/inline code; relative argv entries are invalid operator input
   and fail the command before scoring. No shell expansion occurs.
   Build errors, launch errors, crashes, timeouts, invalid JSON/schema, wrong
   output, wrong span, and accepted trailing tokens fail the affected case. A
   null argv is an explicit abstention with zero case/task correctness. Omitting
   an assignment is invalid, never a denominator reduction. Existing pack examples
   and PUBLIC-1 are calibration only and never enter the 20-task denominator.
6. Each invocation has a one-second wall limit, two-second CPU limit, 512 MiB
   address-space limit and 64 KiB per output stream. Inputs are <=4096 UTF-8 bytes,
   no NUL; integers/results fit signed i64. Whitespace/comments are as specified
   in each task. The response span is the whole matched root's half-open byte
   interval, excluding leading/trailing trivia. Rejection is exactly `{ok:false}`.
   Span fields are integers, not booleans, lines, columns, or character counts.
7. Report full-correct tasks / 20, correct cases / 360, failure and abstention
   counts by category, and total authoring plus review seconds for all assigned
   tasks, separately by language. Task score is one only if all its cases pass;
   otherwise zero. Case fraction is a diagnostic, not a replacement for full
   correctness. Show paired differences and every repeat, with uncertainty if
   enough repeats exist; retain failures in the denominator and time totals.
   Never infer productivity improvement from this fixed-fixture dry run or from
   unequal correctness, budgets, environments or hidden-answer exposure.
