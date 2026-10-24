These handwritten fixtures reject unsupported `[0]void` storage. The expected
locations are specified independently of compiler output. In diagnostic.read,
[4,7) is 2:3, [3,7) is 2:2, [12,17) is 3:5, and [24,27) is 4:7.
Nested and subsequent declarations must report their own origins, including
after successfully emitting another array declaration.
The existing Lang parser assigns local declarations the variable name's
location, and top-level declarations the `var` keyword's location.

With --ast-source, an unwrapped core node receives the reader invocation's
1:1 origin; invocation-fallback.ast checks that this wins over earlier explicit
spans. Without --ast-source, spanless.ast has no provenance and must use the
plain `error:` fallback, without borrowing another declaration's location.
Negative, reversed and outside-source spans must fail before layout runs.

Run `python3 test/run_layout_spans.py --evidence /absolute/external/directory`
after `make bootstrap-verify JOBS=2`. Python -O runs the same explicit checks.
Each rejection must exit 1 and leave no nonempty output module.
