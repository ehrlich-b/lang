#!/bin/bash
# Test the LLVM backend on the test suite
# Optimized with: lli --jit-kind=orc (13x faster) + parallel execution (5x faster)

set -o pipefail

REPO_ROOT=$(pwd)

# Cross-platform setup
case "$(uname -s)" in
    Darwin)
        # macOS - find Homebrew LLVM
        if [ -d "/opt/homebrew/opt/llvm/bin" ]; then
            export PATH="/opt/homebrew/opt/llvm/bin:$PATH"
        elif [ -d "/usr/local/opt/llvm/bin" ]; then
            export PATH="/usr/local/opt/llvm/bin:$PATH"
        fi
        export LANGOS=${LANGOS:-macos}
        # Generate OS layer for macOS
        echo 'include "std/os/libc_macos.lang"' > std/os.lang
        ;;
    *)
        export LANGOS=${LANGOS:-linux}
        # Generate OS layer for Linux
        echo 'include "std/os/linux_x86_64.lang"' > std/os.lang
        ;;
esac

# Use COMPILER from environment, or default to ./out/lang
export COMPILER=${COMPILER:-./out/lang}

# Parallel jobs - default to nproc or 8
JOBS=${JOBS:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 8)}

# Portable timeout
do_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then
        timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then
        gtimeout "$secs" "$@"
    else
        "$@"
    fi
}
export -f do_timeout

# Check if lli supports ORC JIT (LLVM 10+)
LLI_JIT_FLAG=""
if lli --help 2>&1 | grep -q 'jit-kind'; then
    LLI_JIT_FLAG="--jit-kind=orc"
fi
export LLI_JIT_FLAG

# Run a single test - called by xargs
run_one_test() {
    local f=$1
    local name=$(basename "$f" .lang)
    local tmpdir=$(mktemp -d)

    # Check for //ignore marker
    if head -1 "$f" | grep -q '//ignore'; then
        echo "SKIP $name (ignored)"
        rm -rf "$tmpdir"
        return 0
    fi

    # Check for platform-specific markers
    if head -3 "$f" | grep -q '//linux'; then
        if [ "$LANGOS" != "linux" ]; then
            echo "SKIP $name (linux only)"
            rm -rf "$tmpdir"
            return 0
        fi
    fi
    if head -3 "$f" | grep -q '//macos'; then
        if [ "$LANGOS" != "macos" ]; then
            echo "SKIP $name (macos only)"
            rm -rf "$tmpdir"
            return 0
        fi
    fi

    local expected=$(head -1 "$f" | grep -o '[0-9]*')
    local outll="$tmpdir/test.ll"
    local outbin="$tmpdir/test"

    # Compile to LLVM IR (use per-test cache dir to avoid parallel races)
    if LANG_CACHE="$tmpdir/.lang-cache" LANGBE=llvm $COMPILER "$f" -o "$outll" >/dev/null 2>&1; then
        # Use clang for tests marked //clang (inline asm), lli for rest
        if head -3 "$f" | grep -q '//clang'; then
            clang -O0 "$outll" -o "$outbin" 2>/dev/null
            "$outbin" >/dev/null 2>&1
            result=$?
        else
            # Use ORC JIT for ~13x faster interpretation (if available)
            do_timeout 2 lli $LLI_JIT_FLAG "$outll" >/dev/null 2>&1
            result=$?
        fi
        rm -rf "$tmpdir"
        if [ "$result" = "$expected" ]; then
            echo "PASS $name"
            return 0
        else
            echo "FAIL $name (expected $expected, got $result)"
            return 1
        fi
    else
        rm -rf "$tmpdir"
        echo "FAIL $name (compile error)"
        return 1
    fi
}
export -f run_one_test

# Check for sequential mode
if [ "$SEQUENTIAL" = "1" ]; then
    JOBS=1
fi

# Run tests
results_file=$(mktemp)

if [ "$JOBS" -gt 1 ]; then
    # Parallel execution
    printf '%s\n' test/suite/*.lang | xargs -P"$JOBS" -I{} bash -c 'run_one_test "$@"' _ {} > "$results_file" 2>&1
else
    # Sequential execution (for debugging or SEQUENTIAL=1)
    for f in test/suite/*.lang; do
        run_one_test "$f"
    done > "$results_file" 2>&1
fi

# Reader e2e guards (the crown jewel): build AND run readers whose bodies use
# #parser{}. This nested path (compile_reader_to_executable embedding #parser{}
# output) silently rotted once, and no test/suite/ test covers it -- the others
# build readers via lang()/ast_*, never #parser{} inside a reader.
reader_e2e() {
    local name=$1; local file=$2
    local expected=${3:-0}
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER "$file" -o "$tmp/r.ll" >/dev/null 2>&1; then
        do_timeout 30 lli $LLI_JIT_FLAG "$tmp/r.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = "$expected" ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected $expected, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_e2e reader_tiny_e2e     example/tiny/test_tiny.lang 42
reader_e2e reader_calc_e2e     example/calc/test_calc.lang 20
reader_e2e reader_minilisp_e2e example/minilisp/test_defun.lang
reader_e2e reader_c_e2e         example/c/test_c.lang
reader_e2e reader_forth_e2e     example/forth/test_forth.lang
reader_e2e reader_minipy_e2e    example/minipy/test_minipy.lang

# The order regression also guards wrapper scope: later dependencies belong in
# the reader executable, unrelated host functions do not.
reader_order_wrapper_e2e() {
    local name=reader_order_wrapper_e2e
    local tmp=$(mktemp -d)
    local ok=1
    LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER \
        test/suite/276_reader_declaration_order.lang -o "$tmp/order.ll" \
        >/dev/null 2>&1 || ok=0
    local wrapper="$tmp/.lang-cache/readers/late_order.lang"
    test -f "$wrapper" || ok=0
    grep -Fq "func late_order_emit" "$wrapper" || ok=0
    if grep -Fq "func unrelated_host_helper" "$wrapper"; then ok=0; fi
    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_order_wrapper_e2e

# A build that reports an error must FAIL. It used not to: cg_had_error was set
# in fifteen places and read in none, so the compiler printed the diagnostic,
# wrote its output and exited 0. The reader path is the one that made this
# visible, so that is what this guards.
compile_must_fail() {
    local name=$1
    local tmp=$(mktemp -d)
    cat > "$tmp/bad.lang" <<'BADEOF'
include "std/core.lang"
include "example/minipy/minipy.lang"
#minipy{
def missing_colon(n)
    return n
}
func main() i64 { return 0; }
BADEOF
    if LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER "$tmp/bad.lang" -o "$tmp/bad.ll" >/dev/null 2>&1; then
        echo "FAIL $name" >> "$results_file"
    else
        echo "PASS $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
compile_must_fail compile_error_is_fatal

# Reader authoring errors must be ordinary compiler failures: one diagnostic,
# a nonzero status, and no stale or partial output that looks usable.
reader_authoring_failures_e2e() {
    local name=reader_authoring_failures_e2e
    local tmp=$(mktemp -d)
    local ok=1

    cat > "$tmp/malformed.lang" <<'MALFORMED'
include "std/ast.lang"
reader malformed(text *u8) *u8 {
    var value *u8 = ast_number("42")
    return value;
}
MALFORMED
    LANG_CACHE="$tmp/cache-malformed" LANGBE=llvm $COMPILER \
        "$tmp/malformed.lang" -o "$tmp/malformed.ll" >"$tmp/malformed.out" 2>&1 && ok=0
    test ! -e "$tmp/malformed.ll" || ok=0
    grep -Fq "$tmp/malformed.lang:" "$tmp/malformed.out" || ok=0
    grep -Fq "expected ';'" "$tmp/malformed.out" || ok=0

    cat > "$tmp/unknown-builder.lang" <<'UNKNOWNBUILDER'
include "std/ast.lang"
reader unknown_builder(text *u8) *u8 {
    return ast_builder_that_does_not_exist(text);
}
UNKNOWNBUILDER
    LANG_CACHE="$tmp/cache-builder" LANGBE=llvm $COMPILER \
        "$tmp/unknown-builder.lang" -o "$tmp/unknown-builder.ll" \
        >"$tmp/unknown-builder.out" 2>&1 && ok=0
    test ! -e "$tmp/unknown-builder.ll" || ok=0
    grep -Fq "$tmp/unknown-builder.lang:" "$tmp/unknown-builder.out" || ok=0
    grep -Fq "undefined function 'ast_builder_that_does_not_exist'" \
        "$tmp/unknown-builder.out" || ok=0

    cat > "$tmp/bad-ast-reader.lang" <<'BADASTREADER'
include "std/ast.lang"
reader badast(text *u8) *u8 {
    var body *u8 = ast_block1(ast_return(ast_call0("missing_from_reader_ast")));
    return ast_program1(ast_func("main", ast_vec(), ast_type_i64(), body));
}
BADASTREADER
    printf 'anything\n' > "$tmp/program.badast"
    LANG_CACHE="$tmp/cache-bad-ast" LANGBE=llvm $COMPILER \
        "$tmp/bad-ast-reader.lang" "$tmp/program.badast" -o "$tmp/bad-ast.ll" \
        >"$tmp/bad-ast.out" 2>&1 && ok=0
    test ! -e "$tmp/bad-ast.ll" || ok=0
    grep -Fq "$tmp/program.badast:1:1: error: undefined function 'missing_from_reader_ast'" \
        "$tmp/bad-ast.out" || ok=0

    LANG_CACHE="$tmp/cache-compiler" LANGBE=llvm $COMPILER -c not_a_reader \
        example/tiny/tiny.lang -o "$tmp/not-a-reader.ll" \
        >"$tmp/not-a-reader.out" 2>&1 && ok=0
    test ! -e "$tmp/not-a-reader.ll" || ok=0
    grep -Fq "undefined function 'not_a_reader'" "$tmp/not-a-reader.out" || ok=0

    printf 'nope 42\n' > "$tmp/bad.tiny"
    LANG_CACHE="$tmp/cache-input" LANGBE=llvm $COMPILER \
        example/tiny/tiny.lang "$tmp/bad.tiny" -o "$tmp/bad-reader.ll" \
        >"$tmp/bad-reader.out" 2>&1 && ok=0
    test ! -e "$tmp/bad-reader.ll" || ok=0
    test "$(grep -Fc 'tiny: expected' "$tmp/bad-reader.out")" = 1 || ok=0

    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_authoring_failures_e2e

negative_compile_e2e() {
    local name=$1; local file=$2
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER "$file" \
           -o "$tmp/bad.ll" >/dev/null 2>&1; then
        echo "FAIL $name (compiler accepted invalid source)" >> "$results_file"
    else
        echo "PASS $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
negative_compile_e2e negative_undefined_identifier test/negative/undefined_identifier.lang
negative_compile_e2e negative_missing_return       test/negative/missing_return.lang
negative_compile_e2e negative_capturing_lambda_fn test/negative/capturing_lambda_as_fn.lang
negative_compile_e2e negative_break_outside_loop  test/negative/break_outside_loop.lang
negative_compile_e2e negative_continue_outside_loop test/negative/continue_outside_loop.lang

# Like reader_e2e but compiles with clang and runs the native binary, for readers
# whose output uses algebraic effects (perform/handle/resume) - the inline-asm
# continuation mechanism does not work under the lli JIT, only clang (matching
# the //clang suite tests). The flow DSL is built on effects.
reader_e2e_clang() {
    local name=$1; local file=$2
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER "$file" -o "$tmp/r.ll" >/dev/null 2>&1 \
       && clang -O0 "$tmp/r.ll" -o "$tmp/r" 2>/dev/null \
       && do_timeout 10 "$tmp/r" >/dev/null 2>&1; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_e2e_clang reader_flow_e2e     example/flow/test_flow.lang
reader_e2e_clang reader_polyglot_e2e example/polyglot.lang

# A new reader should begin with one discoverable, safe command. Prove that its
# two files compile and run, and that every refusal preserves the old files
# without leaving the other half of a scaffold behind.
reader_scaffold_e2e() {
    local name=reader_scaffold_e2e
    local tmp=$(mktemp -d)
    local compiler_path=$COMPILER
    case "$compiler_path" in
        /*) ;;
        ./*) compiler_path="$REPO_ROOT/${compiler_path#./}" ;;
        *) compiler_path="$REPO_ROOT/$compiler_path" ;;
    esac
    local ok=1

    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader demo >created.out 2>&1) || ok=0
    test -f "$tmp/demo.lang" && test -f "$tmp/answer.demo" || ok=0
    grep -Fq 'Run: lang run demo.lang answer.demo' "$tmp/created.out" || ok=0
    cp "$tmp/demo.lang" "$tmp/demo.before"
    cp "$tmp/answer.demo" "$tmp/answer.before"

    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader demo >again.out 2>&1) || ok=0
    grep -Fq 'refusing to overwrite demo.lang' "$tmp/again.out" || ok=0
    cmp -s "$tmp/demo.before" "$tmp/demo.lang" || ok=0
    cmp -s "$tmp/answer.before" "$tmp/answer.demo" || ok=0

    printf 'keep me\n' >"$tmp/answer.blocked"
    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader blocked >blocked.out 2>&1) || ok=0
    test ! -e "$tmp/blocked.lang" || ok=0
    grep -Fxq 'keep me' "$tmp/answer.blocked" || ok=0

    printf 'keep me too\n' >"$tmp/taken.lang"
    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader taken >taken.out 2>&1) || ok=0
    test ! -e "$tmp/answer.taken" || ok=0
    grep -Fxq 'keep me too' "$tmp/taken.lang" || ok=0

    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader bad-name >invalid.out 2>&1) || ok=0
    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader reader >keyword.out 2>&1) || ok=0
    test ! -e "$tmp/bad-name.lang" && test ! -e "$tmp/reader.lang" || ok=0
    (cd "$tmp" && ! LANG_ROOT="$tmp/missing" \
        "$compiler_path" new reader orphan >toolkit.out 2>&1) || ok=0
    grep -Fq 'reader toolkit not found' "$tmp/toolkit.out" || ok=0
    test ! -e "$tmp/orphan.lang" && test ! -e "$tmp/answer.orphan" || ok=0
    "$compiler_path" help new >"$tmp/help.out" 2>&1 || ok=0
    grep -Fq 'lang new reader <name>' "$tmp/help.out" || ok=0

    if [ "$ok" = 1 ]; then
        (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
            "$compiler_path" run demo.lang answer.demo >/dev/null 2>&1)
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_scaffold_e2e

# Native authors can stop at the reader boundary, inspect/save its AST, and
# feed that exact artifact back into the kernel without changing semantics.
reader_read_e2e() {
    local name=reader_read_e2e
    local tmp=$(mktemp -d)
    local compiler_path=$COMPILER
    case "$compiler_path" in
        /*) ;;
        ./*) compiler_path="$REPO_ROOT/${compiler_path#./}" ;;
        *) compiler_path="$REPO_ROOT/$compiler_path" ;;
    esac
    local ok=1

    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" \
        "$compiler_path" new reader demo >/dev/null 2>&1) || ok=0
    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read demo.lang answer.demo -o answer.ast >read.out 2>read.err) || ok=0
    grep -Fq 'Wrote answer.ast' "$tmp/read.out" || ok=0
    grep -Fq '(span 7 9 (number 42))' "$tmp/answer.ast" || ok=0
    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read demo.lang answer.demo >answer.stdout.ast 2>stdout.err) || ok=0
    cmp -s "$tmp/answer.ast" "$tmp/answer.stdout.ast" || ok=0
    grep -Fq $'(program\n  (func ' "$tmp/answer.ast" || ok=0

    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read demo.lang answer.demo --compact \
        -o answer.compact.ast >compact.out 2>compact.err) || ok=0
    grep -Fq '(program (func main ' "$tmp/answer.compact.ast" || ok=0
    [ "$(wc -l < "$tmp/answer.compact.ast")" -eq 0 ] || ok=0
    node "$REPO_ROOT/test/format_ast_e2e.js" "$tmp/answer.compact.ast" \
        >"$tmp/answer.browser.ast" 2>"$tmp/browser.err" || ok=0
    cmp -s "$tmp/answer.ast" "$tmp/answer.browser.ast" || ok=0

    cat >"$tmp/passthrough.lang" <<'PASSTHROUGH'
reader passthrough(text *u8) *u8 { return text; }
PASSTHROUGH
    cat >"$tmp/quoted.passthrough" <<'QUOTED_AST'
/* formatting trivia */
( program (func main () (type_base i64) (block
  (expr_stmt (string "paren ) quote: \" slash: \\ newline: \n snowman: ☃"))
  (return (span 0 2 (number 42))))))
QUOTED_AST
    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read passthrough.lang quoted.passthrough --compact \
        -o quoted.compact.ast >/dev/null 2>quoted-compact.err) || ok=0
    cmp -s "$tmp/quoted.passthrough" "$tmp/quoted.compact.ast" || ok=0
    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read passthrough.lang quoted.passthrough \
        -o quoted.ast >/dev/null 2>quoted.err) || ok=0
    grep -Fq '(string "paren ) quote: \" slash: \\ newline: \n snowman: ☃")' \
        "$tmp/quoted.ast" || ok=0
    grep -Fq '(span 0 2 (number 42))' "$tmp/quoted.ast" || ok=0
    node "$REPO_ROOT/test/format_ast_e2e.js" "$tmp/quoted.compact.ast" \
        >"$tmp/quoted.browser.ast" 2>"$tmp/quoted-browser.err" || ok=0
    cmp -s "$tmp/quoted.ast" "$tmp/quoted.browser.ast" || ok=0
    (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANGBE=llvm \
        "$compiler_path" --from-ast quoted.ast --ast-source quoted.passthrough \
        -o quoted.ll >/dev/null 2>quoted-roundtrip.err) || ok=0
    if [ "$ok" = 1 ]; then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/quoted.ll" >/dev/null 2>&1
        [ "$?" = 42 ] || ok=0
    fi

    printf 'keep me\n' >"$tmp/bad.ast"
    printf 'answer nope\n' >"$tmp/bad.demo"
    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read demo.lang bad.demo -o bad.ast >bad.out 2>bad.err) || ok=0
    grep -Fq 'demo:1:8: expected number, found nope' "$tmp/bad.err" || ok=0
    grep -Fq "bad.demo:1:1: error: reader 'demo' exited with status 1" "$tmp/bad.err" || ok=0
    ! grep -Fq 'compilation failed' "$tmp/bad.err" || ok=0
    grep -Fxq 'keep me' "$tmp/bad.ast" || ok=0
    "$compiler_path" help read >"$tmp/help.out" 2>&1 || ok=0
    grep -Fq 'lang read <reader.lang...> <source.ext>' "$tmp/help.out" || ok=0
    grep -Fq -- '--compact preserves' "$tmp/help.out" || ok=0

    if [ "$ok" = 1 ] \
       && (cd "$tmp" && LANG_ROOT="$REPO_ROOT" LANGBE=llvm \
           "$compiler_path" --from-ast answer.ast --ast-source answer.demo \
           -o answer.ll >/dev/null 2>&1); then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/answer.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_read_e2e

# Required captures fail at the lowering boundary with the misspelled label,
# instead of becoming a nil dereference or a later codegen error.
reader_named_capture_diagnostic_e2e() {
    local name=reader_named_capture_diagnostic_e2e
    local tmp=$(mktemp -d)
    local compiler_path=$COMPILER
    case "$compiler_path" in
        /*) ;;
        ./*) compiler_path="$REPO_ROOT/${compiler_path#./}" ;;
        *) compiler_path="$REPO_ROOT/$compiler_path" ;;
    esac
    local ok=1

    cat >"$tmp/missing.lang" <<'MISSING_READER'
include "std/parser_reader.lang"
#parser{
    missing_program = 'answer' value:number
}
reader missing(text *u8) *u8 {
    var tokens *Tokenizer = tok_new(text);
    var tree *PNode = parse_missing_program(tokens);
    if tree == nil || !tok_eof(tokens) { return nil; }
    var typo *PNode = pnode_require(tree, "typo");
    if typo == nil { return nil; }
    return "(program)";
}
MISSING_READER
    printf 'answer 42\n' >"$tmp/answer.missing"
    (cd "$tmp" && ! LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read missing.lang answer.missing \
        >missing.out 2>missing.err) || ok=0
    grep -Fq "reader lowering error: required grammar capture 'typo' is absent" \
        "$tmp/missing.err" || ok=0
    grep -Fq "answer.missing:1:1: error: reader 'missing' exited with status 1" \
        "$tmp/missing.err" || ok=0
    ! grep -Fq 'compilation failed' "$tmp/missing.err" || ok=0

    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_named_capture_diagnostic_e2e

# A successful generated parse can be inspected without contaminating the AST
# stream consumed by snapshots, pipes, or --from-ast.
reader_pnode_dump_e2e() {
    local name=reader_pnode_dump_e2e
    local tmp=$(mktemp -d)
    local compiler_path=$COMPILER
    case "$compiler_path" in
        /*) ;;
        ./*) compiler_path="$REPO_ROOT/${compiler_path#./}" ;;
        *) compiler_path="$REPO_ROOT/$compiler_path" ;;
    esac
    local ok=1

    LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read test/pnode_dump_reader.lang \
        test/pnode_dump_source.pdebug >"$tmp/tree.ast" 2>"$tmp/tree.err" || ok=0
    cmp -s test/pnode_dump.expected "$tmp/tree.err" || ok=0
    grep -Fq '(number 32)' "$tmp/tree.ast" || ok=0
    ! grep -Fq 'capture "left"' "$tmp/tree.ast" || ok=0

    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_pnode_dump_e2e

# Capture labels may surface through rule references. A singular lookup must
# reject two matches rather than silently lowering the first one.
reader_capture_ambiguity_e2e() {
    local name=reader_capture_ambiguity_e2e
    local tmp=$(mktemp -d)
    local compiler_path=$COMPILER
    case "$compiler_path" in
        /*) ;;
        ./*) compiler_path="$REPO_ROOT/${compiler_path#./}" ;;
        *) compiler_path="$REPO_ROOT/$compiler_path" ;;
    esac
    local ok=1

    LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache" LANGBE=llvm \
        "$compiler_path" read test/pnode_ambiguity_reader.lang \
        test/pnode_ambiguity_source.pambiguity \
        >"$tmp/ambiguous.ast" 2>"$tmp/ambiguous.err" && ok=0
    grep -Fxqf test/pnode_ambiguity.expected "$tmp/ambiguous.err" || ok=0
    ! grep -Fq "capture 'value' is absent" "$tmp/ambiguous.err" || ok=0
    ! grep -Fq 'compilation failed' "$tmp/ambiguous.err" || ok=0
    test ! -s "$tmp/ambiguous.ast" || ok=0

    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_capture_ambiguity_e2e

# Grammar author errors belong at the token in #parser{}, not at a later
# undefined generated function or reader-wrapper link step.
parser_grammar_diagnostics_e2e() {
    local name=parser_grammar_diagnostics_e2e
    local tmp=$(mktemp -d)
    local compiler_path=$COMPILER
    case "$compiler_path" in
        /*) ;;
        ./*) compiler_path="$REPO_ROOT/${compiler_path#./}" ;;
        *) compiler_path="$REPO_ROOT/$compiler_path" ;;
    esac
    local ok=1

    cat >"$tmp/missing_equals.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing number
}
BAD_GRAMMAR
    cat >"$tmp/missing_group.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = (number | symbol
}
BAD_GRAMMAR
    cat >"$tmp/unknown_rule.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = missing
}
BAD_GRAMMAR
    cat >"$tmp/duplicate_rule.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = number
    thing = symbol
}
BAD_GRAMMAR
    cat >"$tmp/dangling_capture.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = value:
}
BAD_GRAMMAR
    cat >"$tmp/duplicate_capture.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = value:number value:symbol
}
BAD_GRAMMAR
    cat >"$tmp/branch_duplicate_capture.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = (value:number | symbol) value:number
}
BAD_GRAMMAR
    cat >"$tmp/direct_left_recursion.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = thing number | number
}
BAD_GRAMMAR
    cat >"$tmp/indirect_left_recursion.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    thing = other
    other = thing
}
BAD_GRAMMAR
    cat >"$tmp/nullable_left_recursion.lang" <<'BAD_GRAMMAR'
include "std/parser_reader.lang"
#parser{
    prefix = number?
    thing = prefix thing | number
}
BAD_GRAMMAR

    local cases=(
        "missing_equals|expected '=', found number"
        "missing_group|expected ')', found end of input"
        "unknown_rule|expected defined rule, found missing"
        "duplicate_rule|expected unique rule name, found thing"
        "dangling_capture|expected grammar element after capture, found end of input"
        "duplicate_capture|expected capture name used once per branch, found value"
        "branch_duplicate_capture|expected capture name used once per branch, found value"
        "direct_left_recursion|expected non-left-recursive rule, found thing"
        "indirect_left_recursion|expected non-left-recursive rule, found thing"
        "nullable_left_recursion|expected non-left-recursive rule, found thing"
    )
    local spec case_name expected
    for spec in "${cases[@]}"; do
        case_name=${spec%%|*}
        expected=${spec#*|}
        LANG_ROOT="$REPO_ROOT" LANG_CACHE="$tmp/cache-$case_name" LANGBE=llvm \
            "$compiler_path" "$tmp/$case_name.lang" -o "$tmp/$case_name.ll" \
            >"$tmp/$case_name.out" 2>"$tmp/$case_name.err" && ok=0
        grep -Eq '#parser:[0-9]+:[0-9]+:' "$tmp/$case_name.err" || ok=0
        grep -Fq "$expected" "$tmp/$case_name.err" || ok=0
        test ! -e "$tmp/$case_name.ll" || ok=0
    done

    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
parser_grammar_diagnostics_e2e

# Prove the product claim, not just the macro path: lang turns a reader into a
# compiler, that compiler consumes its own file extension, and its output runs.
compiler_compiler_e2e() {
    local name=compiler_compiler_e2e
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER -c tiny \
           example/tiny/tiny.lang -o "$tmp/tinyc.ll" >/dev/null 2>&1 \
       && clang -O2 "$tmp/tinyc.ll" -o "$tmp/tinyc" >/dev/null 2>&1 \
       && LANGBE=llvm "$tmp/tinyc" example/tiny/answer.tiny \
           -o "$tmp/answer.ll" >/dev/null 2>&1; then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/answer.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
compiler_compiler_e2e

compiler_command_e2e() {
    local name=compiler_command_e2e
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/cache-build" LANGBE=llvm $COMPILER compiler tiny \
           example/tiny/tiny.lang -o "$tmp/tinyc" >/dev/null 2>&1 \
       && LANG_CACHE="$tmp/cache-use" "$tmp/tinyc" example/tiny/answer.tiny \
           -o "$tmp/answer.ll" >/dev/null 2>&1; then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/answer.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
compiler_command_e2e

# The hand-written tiny reader is not representative of the advertised path.
# Guard the smallest reader that uses the built-in parser generator: its
# compile-time grammar machinery must not leak into the compiler it produces.
compiler_parser_reader_e2e() {
    local name=compiler_parser_reader_e2e
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/cache-build" LANGBE=llvm $COMPILER compiler parser_tiny \
           test/compiler_parser_reader.lang -o "$tmp/parser-tinyc" >/dev/null 2>&1 \
       && nm "$tmp/parser-tinyc" >"$tmp/symbols" 2>/dev/null \
       && ! grep -q 'grammar_parse\|rdgen_generate' "$tmp/symbols" \
       && "$tmp/parser-tinyc" --help >"$tmp/help" 2>&1 \
       && grep -q 'parser_tiny - compiler generated by lang' "$tmp/help" \
       && ! "$tmp/parser-tinyc" --bogus >"$tmp/bogus" 2>&1 \
       && grep -q 'unknown option: --bogus' "$tmp/bogus" \
       && ! "$tmp/parser-tinyc" "$REPO_ROOT/test/compiler_parser_reader_bad.ptiny" \
           -o "$tmp/bad.ll" >"$tmp/bad.out" 2>"$tmp/bad.err" \
       && grep -Fq "$REPO_ROOT/test/compiler_parser_reader_bad.ptiny:2:1: error: undefined identifier 'missing'" \
           "$tmp/bad.err" \
       && (cd "$tmp" && LANG_CACHE="$tmp/cache-use" "$tmp/parser-tinyc" \
           "$REPO_ROOT/test/compiler_parser_reader.ptiny" >/dev/null 2>&1); then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/a.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
compiler_parser_reader_e2e

# Prove the shipped generated reader, not only the reduced grammar above.
compiler_c_reader_e2e() {
    local name=compiler_c_reader_e2e
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/cache-build" LANGBE=llvm $COMPILER compiler c \
           example/c/c.lang -o "$tmp/cc" >/dev/null 2>&1 \
       && LANG_CACHE="$tmp/cache-use" "$tmp/cc" test/compiler_c.c \
           -o "$tmp/program.ll" >/dev/null 2>&1; then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/program.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
compiler_c_reader_e2e

# A reader runtime is Lang code, not custom-language input. It must be expanded
# and embedded when the compiler is minted, then available without being named
# again when that compiler consumes a source file.
compiler_minilisp_runtime_e2e() {
    local name=compiler_minilisp_runtime_e2e
    local tmp=$(mktemp -d)
    if LANG_CACHE="$tmp/cache-build" LANGBE=llvm $COMPILER compiler minilisp \
           example/minilisp/minilisp.lang \
           --runtime example/minilisp/lisp_runtime.lang \
           -o "$tmp/minilispc" >/dev/null 2>&1 \
       && (cd "$tmp" && LANG_CACHE="$tmp/cache-use" "$tmp/minilispc" \
           "$REPO_ROOT/test/compiler_minilisp.minilisp" \
           -o "$tmp/program.ll" >/dev/null 2>&1); then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/program.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
compiler_minilisp_runtime_e2e

# --from-ast is the browser reader handoff. Runtime helpers must be parsed as
# Lang and prepended to reader-emitted AST before either backend sees it.
from_ast_runtime_e2e() {
    local name=from_ast_runtime_e2e
    local tmp=$(mktemp -d)
    local result=compile_error
    if LANGBE=llvm $COMPILER test/from_ast_runtime.ast --from-ast \
           --runtime example/minilisp/lisp_runtime.lang \
           -o "$tmp/program.ll" >/dev/null 2>&1; then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/program.ll" >/dev/null 2>&1
        result=$?
    fi
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
from_ast_runtime_e2e

# Reusing a LANG_CACHE must never mean reusing yesterday's reader body. This
# rewrites and recompiles within one timestamp tick to guard content freshness,
# not merely mtime freshness.
reader_cache_refresh_e2e() {
    local name=reader_cache_refresh_e2e
    local tmp=$(mktemp -d)
    cat > "$tmp/probe.lang" <<'PROBE1'
include "std/ast.lang"
reader cache_probe(text *u8) *u8 { return ast_number("41"); }
func main() i64 { return #cache_probe{ignored}; }
PROBE1
    if ! LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER "$tmp/probe.lang" \
            -o "$tmp/first.ll" >/dev/null 2>&1; then
        echo "FAIL $name (first compile error)" >> "$results_file"
        rm -rf "$tmp"
        return
    fi
    do_timeout 10 lli $LLI_JIT_FLAG "$tmp/first.ll" >/dev/null 2>&1
    local first=$?

    cat > "$tmp/probe.lang" <<'PROBE2'
include "std/ast.lang"
reader cache_probe(text *u8) *u8 { return ast_number("42"); }
func main() i64 { return #cache_probe{ignored}; }
PROBE2
    if ! LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER "$tmp/probe.lang" \
            -o "$tmp/second.ll" >/dev/null 2>&1; then
        echo "FAIL $name (second compile error)" >> "$results_file"
        rm -rf "$tmp"
        return
    fi
    do_timeout 10 lli $LLI_JIT_FLAG "$tmp/second.ll" >/dev/null 2>&1
    local second=$?

    if [ "$first" = 41 ] && [ "$second" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 41 then 42, got $first then $second)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_cache_refresh_e2e

# Reader stdin used to truncate silently at 64 KiB. Real source files and their
# generated AST routinely exceed that once a language grows past a toy.
reader_large_input_e2e() {
    local name=reader_large_input_e2e
    local tmp=$(mktemp -d)
    cat > "$tmp/largeio.lang" <<'LARGEIO'
include "std/ast.lang"
reader largeio(text *u8) *u8 {
    if strlen(text) < 70000 {
        eprintln("largeio: input was truncated");
        return nil;
    }
    var body *u8 = ast_block1(ast_return(ast_number("42")));
    return ast_program1(ast_func("main", ast_vec(), ast_type_i64(), body));
}
LARGEIO
    printf '%070000d\n' 0 > "$tmp/program.largeio"

    if LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER \
           "$tmp/largeio.lang" "$tmp/program.largeio" -o "$tmp/out.ll" \
           >/dev/null 2>&1; then
        do_timeout 10 lli $LLI_JIT_FLAG "$tmp/out.ll" >/dev/null 2>&1
        local result=$?
    else
        local result=compile_error
    fi

    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
reader_large_input_e2e

cli_run_e2e() {
    local name=cli_run_e2e
    local tmp=$(mktemp -d)
    LANG_CACHE="$tmp/.lang-cache" LANGBE=llvm $COMPILER run \
        example/tiny/tiny.lang example/tiny/answer.tiny >/dev/null 2>&1
    local result=$?
    if [ "$result" = 42 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name (expected 42, got $result)" >> "$results_file"
    fi
    rm -rf "$tmp"
}
cli_run_e2e

token_dump_e2e() {
    local name=token_dump_e2e
    local output
    if output=$($COMPILER --dump-tokens test/suite/260_float_basic.lang 2>/dev/null) \
       && printf '%s\n' "$output" | grep -Fq "[4:1] func 'func'" \
       && printf '%s\n' "$output" | grep -Fq "FLOAT '1.5'" \
       && printf '%s\n' "$output" | grep -Fq "EOF ''"; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
}
token_dump_e2e

cli_errors_e2e() {
    local name=cli_errors_e2e
    local tmp=$(mktemp -d)
    local ok=1

    $COMPILER --not-a-real-option test/suite/002_return_42.lang \
        >"$tmp/unknown.out" 2>&1 && ok=0
    grep -Fq "unknown option: --not-a-real-option" "$tmp/unknown.out" || ok=0

    $COMPILER test/suite/002_return_42.lang -o >"$tmp/output.out" 2>&1 && ok=0
    grep -Fq -- "-o needs an output path" "$tmp/output.out" || ok=0

    $COMPILER -c >"$tmp/compiler.out" 2>&1 && ok=0
    grep -Fq -- "-c needs a reader function name" "$tmp/compiler.out" || ok=0

    $COMPILER compiler >"$tmp/compiler-command.out" 2>&1 && ok=0
    grep -Fq "compiler needs a reader name" "$tmp/compiler-command.out" || ok=0

    $COMPILER -r tiny >"$tmp/reader.out" 2>&1 && ok=0
    grep -Fq -- "-r needs a reader name and file" "$tmp/reader.out" || ok=0

    $COMPILER --ast-source >"$tmp/ast-source-missing.out" 2>&1 && ok=0
    grep -Fq -- "--ast-source needs a source file" "$tmp/ast-source-missing.out" || ok=0

    $COMPILER --ast-source source.read >"$tmp/ast-source-mode.out" 2>&1 && ok=0
    grep -Fq -- "--ast-source requires --from-ast" "$tmp/ast-source-mode.out" || ok=0

    $COMPILER --runtime runtime.lang >"$tmp/runtime-mode.out" 2>&1 && ok=0
    grep -Fq -- "--runtime requires compiler generation or --from-ast" "$tmp/runtime-mode.out" || ok=0

    if [ "$ok" = 1 ]; then
        echo "PASS $name" >> "$results_file"
    else
        echo "FAIL $name" >> "$results_file"
    fi
    rm -rf "$tmp"
}
cli_errors_e2e

# Count results (grep -c returns 1 if no matches, so handle that)
passed=$(grep -c '^PASS' "$results_file" 2>/dev/null) || passed=0
failed=$(grep -c '^FAIL' "$results_file" 2>/dev/null) || failed=0
skipped=$(grep -c '^SKIP' "$results_file" 2>/dev/null) || skipped=0

# Show results
cat "$results_file"
rm -f "$results_file"

echo ""
echo "Passed: $passed / $((passed + failed))"
if [ "$skipped" -gt 0 ]; then
    echo "Skipped: $skipped"
fi
if [ $failed -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "FAILED: $failed tests failed"
    exit 1
fi
