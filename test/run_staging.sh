#!/bin/sh
# P0 contracts only; source execution phases are not implemented.
set -eu
cd "$(dirname "$0")/.."
phase=${1:-P0}
if [ "$phase" != P0 ]; then echo "unsupported staging phase: $phase" >&2; exit 1; fi
output=${2:-out/staging-p0}
mkdir -p "$output"
python3 test/run_layout_audit.py --output "$output/layout"
python3 test/run_confinement.py --output "$output/confinement"
node test/confinement/wasm.js > "$output/wasm.json"
python3 test/test_conformance_applicability.py
python3 test/check_conformance.py
