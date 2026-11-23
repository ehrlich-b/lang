#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: LOXC=path/to/loxc $0 program.lox" >&2
    exit 64
fi
loxc=${LOXC:-./out/loxc}
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lox-run.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
status=0
"$loxc" "$1" -o "$tmp/program.ll" >"$tmp/out" 2>"$tmp/err" || status=$?
if [ "$status" -ne 0 ]; then
    # Budget exhaustion exits from the parser host before the reader can emit
    # a snippet. Read the span from the host's structured diagnostic.
    if [ "$status" -eq 1 ] && grep -Eq '\(code parser-(work|depth)-budget\)' "$tmp/err"; then
        if "$loxc" "$1" --diagnostics=json -o "$tmp/program.ll" >"$tmp/out" 2>"$tmp/json"; then
            cat "$tmp/err" >&2
            exit "$status"
        fi
        if python3 -B "$(dirname -- "$0")/budget_diagnostic.py" "$1" "$tmp/json"; then
            exit 65
        fi
    fi
    cat "$tmp/err" >&2
    # The minted host uses a generic failure status for reader diagnostics.
    if [ "$status" -eq 1 ] && grep -Eq ':[0-9]+:[0-9]+: .+ @[0-9]+:[0-9]+$' "$tmp/err"; then
        exit 65
    fi
    exit "$status"
fi
cat "$tmp/err" >&2
lli -O0 "$tmp/program.ll" "$1"
