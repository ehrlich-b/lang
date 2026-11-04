#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 REPOSITORY" >&2
    exit 2
fi
repo=$(cd "$1" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/source"
ln -s "$repo" "$tmp/source/lang"
# Extract the documented commands from the checked-out README, substituting
# only the clone source so this also works without network access.
README_SOURCE="$(cd "$(dirname "$0")/.." && pwd)/README.md" REPO_SOURCE="$tmp/source/lang" python3 - "$tmp/first-run.sh" <<'PY'
import os
import pathlib
import shlex
import sys

readme = pathlib.Path(os.environ['README_SOURCE']).read_text()
block = readme.split('## First run\n', 1)[1].split('```bash\n', 1)[1].split('\n```', 1)[0]
url = 'https://gitlab.com/ehrlich-b/lang'
if block.count(url) != 1:
    raise SystemExit('Expected exactly one clone URL in the first-run block')
pathlib.Path(sys.argv[1]).write_text("trap 'status=$?; [ \"$status\" -eq 42 ] || exit \"$status\"' ERR\n" + block.replace(url, shlex.quote(os.environ['REPO_SOURCE'])) + '\n')
PY
cd "$tmp"
bash first-run.sh | tee output.log
test "$(tail -n 1 output.log)" = 42
