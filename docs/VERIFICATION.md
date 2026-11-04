`make verify` (also `bootstrap-verify`, `llvm-verify`, and `test-bootstrap`)
can reuse a completed local verification from `$XDG_CACHE_HOME/lang/verification`
(default `~/.cache/lang/verification`). Set `LANG_VERIFY_CACHE` to choose another
trusted local directory, including a directory shared by disposable checkouts.
Do not use an untrusted or remotely populated cache.

The identity includes the candidate commit, versioned and new input files,
source and test fixtures, bootstrap roots, executable tool hashes and their
shared libraries, Clang resources, ambient options, host, and the complete
verification command. Missing, interrupted, failed or corrupt records run again.
A per-identity lock admits one executor; a checkout lock protects generated
outputs. Inputs are checked again before publication. Restoring a receipt
restores its generated compiler and fixed-point artifacts and replays its log.
This receipt is for the existing verifier, including its entire LLVM suite and
both fixed points; it does not stand for other integration tests.

The integration baseline runner always sets `LANG_VERIFY_FRESH=1`. Use
`LANG_VERIFY_FRESH=1 make verify` for other integration entry points requiring a new execution.
`make bootstrap` and `make bootstrap-local` always retain their original full
verification, archive and promotion pipeline and never consume these receipts.

`python3 test/perf_gate_receipt.py` checks the receipt protocol using a small fake
executor; `python3 test/perf_gate_receipt.py --benchmark --requests 2` measures
that protocol's execution count and CPU cost. Neither runs the compiler suite
or issues a production verification receipt.
