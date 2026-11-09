#!/bin/bash
set -euo pipefail
lane=$(cd .. && pwd)
mkdir -p "$lane/scratch"
work=$(mktemp -d "$lane/scratch/a8.XXXXXXXX")
git clone --quiet --no-local . "$work/repo"
git -C "$work/repo" checkout --quiet --detach "$(git rev-parse HEAD)"
cd "$work/repo"
JOBS=2 make bootstrap PUBLISH_BOOTSTRAP=0
COMPILER="$PWD/out/lang" ./test/run_llvm_suite.sh
COMPILER="$PWD/out/lang" python3 test/run_effects_safety.py
COMPILER="$PWD/out/lang" ./test/run_wasm_suite.sh
