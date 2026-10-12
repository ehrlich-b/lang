#!/bin/bash
# Exercise the real archive recipe without compiling or promoting a root.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fixture() {
    local dir="$tmp/$1"
    mkdir -p "$dir/bootstrap/current" "$dir/scratch" "$dir/unrelated"
    printf 'old-root\n' >"$dir/bootstrap/current/COMMIT"
    printf 'preserved\n' >"$dir/bootstrap/current/notes"
    printf 'canary\n' >"$dir/unrelated/keep"
    {
        printf 'VERSION := new-root\nPUBLISH_BOOTSTRAP := 0\nGH := false\narchive:\n'
        awk '/^\t@set -e; OLD_COMMIT=/{copy=1} /^\t@# Stage complete files/{copy=0} copy' "$root/Makefile"
    } >"$dir/Makefile"
}

fixture fresh
make -s -C "$tmp/fresh" archive TMPDIR="$tmp/fresh/scratch" >"$tmp/fresh.log" 2>&1
cmp "$tmp/fresh/bootstrap/current/notes" "$tmp/fresh/bootstrap/archive/old-root/notes"
test -f "$tmp/fresh/unrelated/keep"
# An identical archive is reusable; a conflicting archive must stop.
make -s -C "$tmp/fresh" archive TMPDIR="$tmp/fresh/scratch" >"$tmp/reuse.log" 2>&1
printf 'different\n' >"$tmp/fresh/bootstrap/archive/old-root/notes"
if make -s -C "$tmp/fresh" archive TMPDIR="$tmp/fresh/scratch" >"$tmp/conflict.log" 2>&1; then
    echo 'FAIL bootstrap archive accepted conflicting contents' >&2
    exit 1
fi
grep -Fq 'already contains different files' "$tmp/conflict.log"

fixture blocked
printf 'not a directory\n' >"$tmp/blocked/bootstrap/archive"
if make -s -C "$tmp/blocked" archive TMPDIR="$tmp/blocked/scratch" >"$tmp/blocked.log" 2>&1; then
    echo 'FAIL bootstrap archive ignored a directory creation failure' >&2
    exit 1
fi
test -f "$tmp/blocked/unrelated/keep"
test ! -e "$tmp/blocked/unrelated.tar.gz"

fixture copy-failure
mkdir -p "$tmp/copy-failure/bin"
printf '#!/bin/sh\nexit 1\n' >"$tmp/copy-failure/bin/cp"
chmod +x "$tmp/copy-failure/bin/cp"
if PATH="$tmp/copy-failure/bin:$PATH" make -s -C "$tmp/copy-failure" archive \
        TMPDIR="$tmp/copy-failure/scratch" >"$tmp/copy-failure.log" 2>&1; then
    echo 'FAIL bootstrap archive ignored a copy failure' >&2
    exit 1
fi
test -f "$tmp/copy-failure/unrelated/keep"
echo 'PASS bootstrap archive (fresh clone, reuse, conflict, mkdir failure, copy failure)'
