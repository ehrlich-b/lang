#!/bin/bash
# Compatibility oracle: the header operations from the original LLVM worker.
# Scan every field, including skipped inputs, for bounded metadata comparisons.
for f in "$@"; do
    markers=''
    if head -1 "$f" | grep -q '//ignore'; then markers+=i; fi
    if head -3 "$f" | grep -q '//linux'; then markers+=l; fi
    if head -3 "$f" | grep -q '//macos'; then markers+=m; fi
    if head -1 "$f" | grep -q '^// reject: '; then markers+=r; fi
    if head -3 "$f" | grep -q '//clang'; then markers+=c; fi
    expected=$(head -1 "$f" | grep -o '[0-9]*')
    diagnostic=''
    if [[ "$markers" == *r* ]]; then
        diagnostic=$(head -1 "$f" | sed 's@^// reject: @@')
    fi
    printf '%s\0%s\0%s\0%s\0' "$f" "$markers" "$expected" "$diagnostic"
done
