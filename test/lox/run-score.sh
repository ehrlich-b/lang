#!/bin/sh
set -eu
suite=${LOX_SUITE:?Set LOX_SUITE to the pinned checkout with clox built}
compiler=${COMPILER:-./out/lang_next}
pin=4a840f70f69c6ddd17cfef4f6964f8e1bcd8c3d4
if [ "$(git -C "$suite" rev-parse HEAD)" != "$pin" ]; then
    echo "Expected Crafting Interpreters $pin" >&2; exit 1
fi
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lox-score.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
python3 -B test/lox/score.py --suite "$suite" --interpreter "$suite/clox" > "$tmp/clox-score" || {
    cat "$tmp/clox-score"; exit 1;
}
printf 'Reference clox '
tail -1 "$tmp/clox-score"
LANGBE=llvm "$compiler" compiler lox example/lox/lox.lang --runtime example/lox/runtime.lang -o "$tmp/loxc"
LOXC="$tmp/loxc" python3 -B test/lox/score.py --suite "$suite" --interpreter example/lox/run.sh --located --minimum 180
