#!/bin/sh
set -eu
suite=${LOX_SUITE:-../craftinginterpreters}
compiler=${COMPILER:-./out/lang_bootstrap}
pin=4a840f70f69c6ddd17cfef4f6964f8e1bcd8c3d4
if [ "$(git -C "$suite" rev-parse HEAD)" != "$pin" ]; then
    echo "Expected Crafting Interpreters $pin" >&2; exit 1
fi
tmp=$(mktemp -d "${TMPDIR:-/tmp}/lox-score.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
python3 test/lox/score.py --suite "$suite" --interpreter "$suite/clox" > "$tmp/clox-score"
tail -1 "$tmp/clox-score"
LANGBE=llvm "$compiler" compiler lox example/lox/lox.lang --runtime example/lox/runtime.lang -o "$tmp/loxc"
cat > "$tmp/lox" <<DRIVER
#!/bin/sh
dir=\$(mktemp -d "\${TMPDIR:-/tmp}/lox-run.XXXXXX")
trap 'rm -rf "\$dir"' EXIT
if ! "$tmp/loxc" "\$1" -o "\$dir/program.ll" >"\$dir/out" 2>"\$dir/err"; then cat "\$dir/err" >&2; exit 65; fi
lli "\$dir/program.ll"
DRIVER
chmod +x "$tmp/lox"
status=0
python3 test/lox/score.py --suite "$suite" --interpreter "$tmp/lox" > "$tmp/lang-score" || status=$?
cat "$tmp/lang-score"
# An incomplete score is expected; malformed or incomplete suite is an error.
[ "$status" -le 1 ] && tail -1 "$tmp/lang-score" | grep -Eq '^TOTAL [0-9]+/246$'
