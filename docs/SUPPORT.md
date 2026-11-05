# Troubleshoot a reader or compiler

Use the documentation in the same checkout as your compiler. Start with
[Building](BUILDING.md), [the reader guide](READERS.md) and
[capability profiles](PROFILES.md). The [borders grid](BORDERS.md) records executed
examples; a supported cell establishes that fixture's behavior, not every
program using the feature. A wrong result is a bug, even if compilation succeeds.

## Identify the failing phase

| Symptom | First check |
| --- | --- |
| Compiler does not start or cannot find standard files | `lang tools`, resource root and build prerequisites |
| A reader fails to build | Helper signatures, included runtime and the reader declaration diagnostic |
| Custom syntax fails | Token at the reported location, grammar expectations and complete input consumption |
| Reading succeeds but compilation fails | Saved shared AST, its source spans and the target profile |
| Program returns a wrong value | Expected output, actual bytes and exit status on a minimal input |
| Browser-only failure | Browser console, host imports, reader phase versus final program phase, and target limits |

Locations use 1-based lines and UTF-8 byte columns. Keep the original input,
including comments, line endings and non-ASCII characters. Readers can retain
custom-source spans through `ast_span`; see [Errors and source locations](READERS.md#errors-and-source-locations).
Do not remove a failing example or call it unsupported solely because it fails.
An unsupported feature should produce a diagnostic that names the limitation.

## Make a reproducible report

Include the following information with a bug report or a local repair task:

- Full checkout commit (`git rev-parse HEAD`) and whether source files changed.
- Operating system, architecture, compiler path and tool versions. Distinguish
  `out/lang`, `out/lang_next`, a generated compiler and a browser compiler.
- Target/backend, optimization level and relevant `LANGBE`, `LANGOS`,
  `LANGLIBC`, `LANG_ROOT` or cache settings. Include only settings needed to
  reproduce the problem; omit credentials and unrelated environment data.
- The smallest reader, source and required runtime that reproduce it, plus the
  exact command and working directory.
- Expected value or output bytes, actual stdout/stderr and exit status. For a
  wrong answer, name the specification or independent reference behind the
  expectation.
- The saved shared AST or generated IR when the failure occurs after reading.
  In the lab, include its versioned workspace export and the failing phase.
- A nearby valid case and whether it still works after the failure or repair.

This information lets a maintainer reproduce a failure without an account,
private machine or access to the original browser session. This guide defines
the report format; it does not promise response times or a hosted support service.

## Verify a repair

Begin with the reduced reproducer and a valid neighbor. Put syntax and runtime
repairs in the reader or runtime; a general compiler defect needs a general
core fixture. Use the freshly built compiler for source changes. Run the
relevant target checks from [Building](BUILDING.md) and the profile's gates
before making a compatibility claim. Preserve unexpected skips and failures
in the report, and distinguish a locally prepared repair from one published
in the compiler users download.
