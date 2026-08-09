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
