#!/bin/bash
set -euo pipefail
lane=$(cd .. && pwd)
mkdir -p "$lane/scratch"
if [ ! -f "$lane/tools/manifest.json" ]; then
  python3 examples/dsl-compare/install.py --tools "$lane/tools"
fi
work=$(mktemp -d "$lane/scratch/a3.XXXXXXXX")
mkdir -p "$work/release" "$work/download" "$work/evidence" "$work/scratch"
python3 scripts/package_sdk.py --output "$work/release"
archive=$(printf '%s\n' "$work"/release/*.tar.xz)
curl --fail --silent --show-error "file://$archive" -o "$work/download/sdk.tar.xz"
cmp "$archive" "$work/download/sdk.tar.xz"
tar -xJf "$work/download/sdk.tar.xz" -C "$work/download"
sdk=$(printf '%s\n' "$work"/download/lang-*-x86_64-linux)
python3 examples/dsl-compare/run.py --tools "$lane/tools" --sdk "$sdk" --report "$work/evidence/compare.json"
python3 examples/dsl-compare/check.py report --relocate --report "$work/evidence/compare.json"
JOBS=2 python3 -B test/reader_author/rill_bootstrap.py --case integration --evidence "$work/rill"
printf 'Evidence: %s\n' "$work"
