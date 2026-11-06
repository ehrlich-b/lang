#!/bin/bash
set -euo pipefail
export LANGBE=llvm LANGOS=linux JOBS=2
root="$PWD"
work=$(mktemp -d "$root/../scratch/generated-export-XXXXXX")
make init
make build
cd "$work"
"$root/out/lang_next" new language parcel
cp "$root/LICENSE" "$work/parcel/LICENSE"
python3 - "$work/parcel/package.json" <<'PY'
import json,sys
json.dump({'schema':1,'runtime_contract':'The generated parcel runtime uses system libc and prints a shipping fee for an integer total.','licenses':[{'component':c,'file':'LICENSE'} for c in ('compiler','reader','runtime')], 'example_runs':[['99'],['100']]},open(sys.argv[1],'w'))
PY
cd "$work/parcel"
"$root/out/lang_next" test --project project.lang-project
"$root/out/lang_next" package --project project.lang-project --metadata package.json -o "$work/kit.tar.gz"
mkdir "$work/relocated"
tar -xzf "$work/kit.tar.gz" -C "$work/relocated"
cd "$work/relocated/kit"
export PATH=/usr/bin:/bin
python3 kit.py verify
python3 kit.py native --clang "$(command -v clang)" --output "$work/result"
test "$("$work/result" 99)" = 10
test "$("$work/result" 100)" = 0
cat receipt.json
