#!/bin/sh
# P0 audits and P1 controlled-fixture compile/call workers.
set -eu
cd "$(dirname "$0")/.."
phase=${1:-P0}
if [ "$phase" = P1 ]; then
    if [ -z "${COMPILER:-}" ]; then
        make build
        COMPILER=out/lang_next
        export COMPILER
    fi
    exec python3 test/run_stage_workers.py
fi
if [ "$phase" != P0 ]; then echo "unsupported staging phase: $phase" >&2; exit 1; fi
output=${2:-out/staging-p0}
mkdir -p "$output"
python3 test/run_layout_audit.py --output "$output/layout"
python3 test/run_confinement.py --output "$output/confinement"
node test/confinement/wasm.js > "$output/wasm.json"
python3 test/test_conformance_applicability.py
python3 test/check_conformance.py
