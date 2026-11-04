# Shared by local suite runners; source before starting any workers.
# Integration hosts may explicitly raise SUITE_CPU_BUDGET as well as JOBS.
# For example: SUITE_CPU_BUDGET=16 JOBS=16 ./test/run_llvm_suite.sh
# Nested invocations remain sequential; this override belongs at the top level.
suite_workers() {
    local budget=${SUITE_CPU_BUDGET:-4} requested=${JOBS:-2}
    case "$budget" in ''|*[!0-9]*|0|0*) echo "SUITE_CPU_BUDGET must be a positive decimal integer" >&2; return 2;; esac
    case "$requested" in ''|*[!0-9]*|0|0*) echo "JOBS must be a positive decimal integer" >&2; return 2;; esac
    # Compare decimal lengths first so arbitrarily large requests cannot wrap.
    if [ ${#budget} -gt 6 ]; then echo "SUITE_CPU_BUDGET is too large" >&2; return 2; fi
    JOBS=$requested
    if [ ${#requested} -gt ${#budget} ] || { [ ${#requested} -eq ${#budget} ] && [[ "$requested" > "$budget" ]]; }; then JOBS=$budget; fi
    if [ "${SEQUENTIAL:-0}" = 1 ] || [ "${LANG_SUITE_WORKER:-0}" = 1 ]; then JOBS=1; fi
    # Every descendant of a pool worker gets one slot, even with explicit JOBS.
    export JOBS
}
suite_workers || exit $?
