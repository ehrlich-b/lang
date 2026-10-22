# Compiler diagnostics, version 1

Use `lang compile --diagnostics=json input.lang -o output.ll` for machine-readable
compiler failures. The flag also works with implicit compilation and source AST
emission. Without it, diagnostics keep their human format. No backend semantics,
effects support, or optimization support is added by this transport.

Stderr contains one JSON object per completed diagnostic, separated by newlines
(JSON Lines). Each object has this shape:

```json
{"version":1,"code":"syntax-error","severity":"error","path":"input.lang","span":{"start":27,"end":28},"message":"input.lang:1:28: error: expected ';' after return","truncated":false}
```

`version` identifies this contract. `code` is a stable category; messages retain
human context and may evolve. `severity` is `error`. `path` is the compiler's
source name, usually the input path, or `null` when no source is available.
`span` uses zero-based byte offsets with an exclusive end, relative to that
source's original bytes. An EOF insertion point has equal start/end offsets.
A diagnostic without a known location has `span: null`; consumers must check
before proposing an edit. Code generation uses the closest existing node origin,
which may identify a declaration rather than the entire failing expression.
Codegen spans may also be zero-width anchors; those anchors do not imply a
missing token or an insertion point.

The stable categories are:

| Code | Meaning |
| --- | --- |
| `syntax-error` | A required source construct or token is missing |
| `trailing-input` | Unexpected input at declaration level |
| `lexical-error` | A lexer failure during source tokenization |
| `invalid-utf8` | Invalid source encoding; span marks the sequence's first byte |
| `embedded-nul` | A NUL byte in a source file |
| `unsupported-feature` | A backend explicitly rejects an unsupported feature |
| `codegen-error` | Another error with existing code generation provenance |
| `invalid-option` | An unknown flag or diagnostics mode |
| `unsupported-mode` | JSON transport is unavailable for the requested operation |
| `compiler-error` | Another compiler failure or follow-up explanation |

Host failures retain their existing stable host code, such as `source-depth`
or `byte-limit`. One source failure may produce several records, including
unlocated follow-up explanations. Use located records for repair decisions.

Paths and messages are JSON strings, never interpolated JSON. Quotes,
backslashes and control bytes are escaped, including embedded newlines. Valid
UTF-8 text is preserved. Invalid bytes in diagnostic strings (including OS
filenames) are represented individually as `\u00xx`; do not reinterpret those
strings as filesystem authority. Invalid source bytes are rejected by existing
source admission and do not prevent JSON decoding. Messages are bounded to
1 MiB per diagnostic; `truncated: true` reports any dropped suffix.

A failure exits nonzero. Successful compilation emits no diagnostic records.
Artifacts go to `-o`; status messages remain on stdout. Consumers should capture
stdout and stderr separately and check the exit status. This version rejects
JSON transport for `run`, compiler generation, `read`, `new`, `env`, `tools`,
`--from-ast`, `--dump-tokens`, and `--expand-macros`. Those operations can involve
other processes or non-diagnostic stderr. Unknown flags and modes fail loudly.

`scripts/repair_diagnostic.py COMPILER SOURCE OUTPUT` demonstrates a deliberately
small consumer. On a copy of `test/diagnostics/syntax.lang`, it recognizes the
missing return semicolon, checks the reported byte slice is `}`, inserts `; `,
and recompiles. It validates version, category, severity, path, span bounds and
the expected source bytes before editing. It never evaluates message text.
Run the transport and repair checks with:

```sh
make build
python3 -B test/run_diagnostics_json.py
```

Set `COMPILER` to select another compiler and `DIAGNOSTICS_EVIDENCE_DIR` to retain
captured commands, stdout, stderr, exit codes and the repair result.

The transport uses the internal runtime prefix `___compiler_`; these symbols
are reserved for compiler/runtime use. Ordinary names such as `stderr_write`,
`diagnostic_string` and `diagnostic_json` remain available to user programs.
The standard core includes this transport so shared host failures use the same
encoder without backend-specific callbacks; disabled transport writes stderr
directly and allocates no message buffer.
