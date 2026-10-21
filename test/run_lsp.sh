#!/bin/sh
# Q0 validates design examples. Q1..Q4 are future implementation obligations.
set -eu
cd "$(dirname "$0")/.."
if [ "$#" -gt 1 ]; then echo 'usage: test/run_lsp.sh [Q0..Q4]' >&2; exit 2; fi
phase=${1:-Q0}
case "$phase" in
    Q0) exec python3 test/check_lsp_contract.py --phase Q0 ;;
    Q1|Q2|Q3|Q4) exec python3 test/check_lsp_contract.py --phase "$phase" ;;
    *) echo "unknown LSP phase: $phase" >&2; exit 2 ;;
esac
