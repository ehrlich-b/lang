.PHONY: all init bootstrap build release test test-suite test-run clean distclean \
        build-kernel build-lang-reader emit-kernel-ast emit-lang-reader-ast emit-compiler-ast \
        seed-bootstrap test-composition generate-os-layer llvm-verify

# Get git info
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_DIRTY := $(shell git diff --quiet 2>/dev/null || echo "-dirty")
VERSION := $(GIT_COMMIT)$(GIT_DIRTY)

# Target selection (environment variables)
# LANGOS: linux (default), macos
# LANGBE: x86 (default for now), llvm (future)
# LANGLIBC: none (default, use raw syscalls), libc (use system libc)
LANGOS ?= linux
LANGBE ?= x86
LANGLIBC ?= none

# OS layer file selection
# LANGLIBC=libc overrides LANGOS selection
ifeq ($(LANGLIBC),libc)
    OS_LAYER := std/os/libc.lang
else ifeq ($(LANGOS),linux)
    OS_LAYER := std/os/linux_x86_64.lang
else ifeq ($(LANGOS),macos)
    OS_LAYER := std/os/macos_arm64.lang
else
    $(error Unknown LANGOS: $(LANGOS). Valid values: linux, macos)
endif

# Bootstrap: prefer new structure (bootstrap/current/compiler.s), fallback to legacy (bootstrap/current.s)
BOOTSTRAP := $(shell if [ -f bootstrap/current/compiler.s ]; then echo bootstrap/current/compiler.s; else echo bootstrap/current.s; fi)

# Compiler paths
LANG := out/lang
LANG_NEXT := out/lang_next

# Default target
all: build

# Generate std/os.lang based on LANGOS
generate-os-layer:
	@echo 'include "$(OS_LAYER)"' > std/os.lang

# Init: assemble from bootstrap/current.s, create lang symlink
# Use this only for initial setup or emergency recovery
init:
	@mkdir -p out
	@echo "Initializing from $(BOOTSTRAP)..."
	as $(BOOTSTRAP) -o out/lang_bootstrap.o
	ld out/lang_bootstrap.o -o out/lang_bootstrap
	rm -f out/lang_bootstrap.o
	ln -sf lang_bootstrap $(LANG)
	@echo "Created: $(LANG) -> lang_bootstrap"

# Build: compile src/*.lang using lang -> lang_next
build: generate-os-layer
	@if [ ! -L $(LANG) ]; then \
		$(MAKE) init; \
	fi
	@mkdir -p out
	$(LANG) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/lang_$(VERSION).s
	as out/lang_$(VERSION).s -o out/lang_$(VERSION).o
	ld out/lang_$(VERSION).o -o out/lang_$(VERSION)
	rm -f out/lang_$(VERSION).o
	ln -sf lang_$(VERSION) $(LANG_NEXT)
	@echo "Created: $(LANG_NEXT) -> lang_$(VERSION)"

# ============================================================
# BOOTSTRAP: The ONE command to verify and promote
# ============================================================
# This implements a rigorous multi-generation verification chain:
#   Stage 1: Root of trust (ctrusted from bootstrap)
#   Stage 2: Generation 1 (kernel1 + lang1 built by trusted)
#   Stage 3: Generation 2 + kernel/AST fixed point checks
#   Stage 4: Validation (x86 + LLVM test suites)
#   Stage 5: Promote (only if all checks pass)
#
# Note: Standalones (lang1, lang2) are built by kernels using -c flag.
# TODO: Add -c support to standalones for full composability.
#
# Run this ONE command. Nothing else. No shortcuts.
bootstrap: generate-os-layer
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║           BOOTSTRAP: VERIFY + PROMOTE                          ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@mkdir -p out out/ast /tmp/bootstrap_verify
	@if [ ! -f $(BOOTSTRAP) ]; then echo "ERROR: No bootstrap found at $(BOOTSTRAP)"; exit 1; fi
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 1: ROOT OF TRUST                                         │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	as $(BOOTSTRAP) -o /tmp/bootstrap_verify/ctrusted.o
	ld /tmp/bootstrap_verify/ctrusted.o -o /tmp/bootstrap_verify/ctrusted
	@echo "Built: ctrusted from $(BOOTSTRAP)"
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 2: GENERATION 1 (Built by Trusted)                       │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	@# Build kernel1 (trusted compiles sources) - this becomes our gen1 compiler
	/tmp/bootstrap_verify/ctrusted std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o /tmp/bootstrap_verify/kernel1.s
	as /tmp/bootstrap_verify/kernel1.s -o /tmp/bootstrap_verify/kernel1.o
	ld /tmp/bootstrap_verify/kernel1.o -o /tmp/bootstrap_verify/kernel1
	@echo "Built: kernel1"
	@# Emit reader AST 1 using kernel1 (has --emit-expanded-ast capability)
	/tmp/bootstrap_verify/kernel1 src/lang_reader.lang --emit-expanded-ast -o /tmp/bootstrap_verify/reader_ast1.ast
	@echo "Emitted: reader_ast1.ast ($$(wc -l < /tmp/bootstrap_verify/reader_ast1.ast) lines)"
	@# Build lang1 (standalone compiler) using kernel1
	/tmp/bootstrap_verify/kernel1 -c lang src/lang_reader.lang -o /tmp/bootstrap_verify/lang1.s
	as /tmp/bootstrap_verify/lang1.s -o /tmp/bootstrap_verify/lang1.o
	ld /tmp/bootstrap_verify/lang1.o -o /tmp/bootstrap_verify/lang1
	@echo "Built: lang1 (generation 1 standalone compiler)"
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 3: GENERATION 2 + KERNEL FIXED POINT                     │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	@# Build kernel2 (lang1 compiles sources)
	/tmp/bootstrap_verify/lang1 std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o /tmp/bootstrap_verify/kernel2.s
	@echo ""
	@echo "Checking KERNEL FIXED POINT (kernel1.s === kernel2.s)..."
	@if diff -q /tmp/bootstrap_verify/kernel1.s /tmp/bootstrap_verify/kernel2.s > /dev/null; then \
		echo "✓ KERNEL FIXED POINT VERIFIED"; \
	else \
		echo ""; \
		echo "!!! KERNEL FIXED POINT FAILED !!!"; \
		echo "kernel1.s and kernel2.s differ:"; \
		diff /tmp/bootstrap_verify/kernel1.s /tmp/bootstrap_verify/kernel2.s | head -20; \
		exit 1; \
	fi
	@# Build kernel2 binary to emit AST (standalones don't support --emit-expanded-ast)
	as /tmp/bootstrap_verify/kernel2.s -o /tmp/bootstrap_verify/kernel2.o
	ld /tmp/bootstrap_verify/kernel2.o -o /tmp/bootstrap_verify/kernel2
	@# Emit reader AST 2 using kernel2 (full compiler with all flags)
	/tmp/bootstrap_verify/kernel2 src/lang_reader.lang --emit-expanded-ast -o /tmp/bootstrap_verify/reader_ast2.ast
	@echo ""
	@echo "Checking AST FIXED POINT (reader_ast1 === reader_ast2)..."
	@if diff -q /tmp/bootstrap_verify/reader_ast1.ast /tmp/bootstrap_verify/reader_ast2.ast > /dev/null; then \
		echo "✓ AST FIXED POINT VERIFIED"; \
	else \
		echo ""; \
		echo "!!! AST FIXED POINT FAILED !!!"; \
		echo "reader_ast1.ast and reader_ast2.ast differ:"; \
		diff /tmp/bootstrap_verify/reader_ast1.ast /tmp/bootstrap_verify/reader_ast2.ast | head -20; \
		exit 1; \
	fi
	@# Build lang2 (standalone from kernel2)
	/tmp/bootstrap_verify/kernel2 -c lang src/lang_reader.lang -o /tmp/bootstrap_verify/lang2.s
	as /tmp/bootstrap_verify/lang2.s -o /tmp/bootstrap_verify/lang2.o
	ld /tmp/bootstrap_verify/lang2.o -o /tmp/bootstrap_verify/lang2
	@echo "Built: lang2 (generation 2 standalone compiler)"
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 4: VALIDATION (Tests with Proven Compiler)               │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	@# Copy proven compiler to out/ for test suite
	@# Note: kernel2 is the fixed-point kernel, lang2 is its standalone
	cp /tmp/bootstrap_verify/kernel2.s out/lang_$(VERSION).s
	cp /tmp/bootstrap_verify/kernel2 out/lang_$(VERSION)
	ln -sf lang_$(VERSION) $(LANG_NEXT)
	cp /tmp/bootstrap_verify/lang2.s out/lang_standalone.s
	cp /tmp/bootstrap_verify/lang2 out/lang_standalone
	cp /tmp/bootstrap_verify/reader_ast1.ast out/ast/lang_reader_v1.ast
	@echo "Running x86 test suite with lang2..."
	@COMPILER=/tmp/bootstrap_verify/lang2 ./test/run_lang1_suite.sh
	@echo ""
	@echo "Building LLVM+libc compilers (Linux and macOS)..."
	@# Build Linux libc compiler
	@echo 'include "std/os/libc.lang"' > std/os.lang
	LANGBE=llvm /tmp/bootstrap_verify/kernel2 std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/llvm_libc_linux.ll
	clang -O2 out/llvm_libc_linux.ll -o out/llvm_libc_linux
	@echo "Built: out/llvm_libc_linux"
	@# Build macOS libc compiler (with LANGOS=macos for correct target triple)
	@echo 'include "std/os/libc_macos.lang"' > std/os.lang
	LANGOS=macos LANGBE=llvm /tmp/bootstrap_verify/kernel2 std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/llvm_libc_macos.ll
	@echo "Built: out/llvm_libc_macos.ll"
	@# Restore default OS layer
	@echo 'include "std/os/linux_x86_64.lang"' > std/os.lang
	@echo ""
	@echo "Running LLVM test suite (with Linux libc compiler)..."
	@COMPILER=./out/llvm_libc_linux ./test/run_llvm_suite.sh
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 5: PROMOTE                                               │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	@mkdir -p bootstrap/$(GIT_COMMIT)/lang_reader
	cp /tmp/bootstrap_verify/kernel2.s bootstrap/$(GIT_COMMIT)/compiler.s
	cp out/llvm_libc_linux.ll bootstrap/$(GIT_COMMIT)/compiler_linux.ll
	cp out/llvm_libc_macos.ll bootstrap/$(GIT_COMMIT)/compiler_macos.ll
	cp /tmp/bootstrap_verify/reader_ast1.ast bootstrap/$(GIT_COMMIT)/lang_reader/source.ast
	@echo "compiler.s:" > bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  sha256: $$(sha256sum bootstrap/$(GIT_COMMIT)/compiler.s | cut -d' ' -f1)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  built_by: bootstrap/$$(readlink bootstrap/current 2>/dev/null || echo none)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  built_at: $$(date -Iseconds)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  source_commit: $(GIT_COMMIT)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  verification:" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "    kernel_fixed_point: true (kernel1.s === kernel2.s)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "    ast_fixed_point: true (reader_ast1 === reader_ast2)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "compiler_linux.ll:" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  sha256: $$(sha256sum bootstrap/$(GIT_COMMIT)/compiler_linux.ll | cut -d' ' -f1)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "compiler_macos.ll:" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  sha256: $$(sha256sum bootstrap/$(GIT_COMMIT)/compiler_macos.ll | cut -d' ' -f1)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "lang_reader/source.ast:" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  sha256: $$(sha256sum bootstrap/$(GIT_COMMIT)/lang_reader/source.ast | cut -d' ' -f1)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  lines: $$(wc -l < bootstrap/$(GIT_COMMIT)/lang_reader/source.ast)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	ln -sfn $(GIT_COMMIT) bootstrap/current
	cp bootstrap/$(GIT_COMMIT)/compiler.s bootstrap/escape_hatch.s
	ln -sf lang_$(VERSION) $(LANG)
	rm -f $(LANG_NEXT)
	@rm -rf /tmp/bootstrap_verify
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                    BOOTSTRAP COMPLETE                          ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║ Fixed Points Verified:                                         ║"
	@echo "║   ✓ kernel1.s === kernel2.s (kernel stable)                    ║"
	@echo "║   ✓ reader_ast1 === reader_ast2 (AST stable)                   ║"
	@echo "║                                                                ║"
	@echo "║ Tests Passed:                                                  ║"
	@echo "║   ✓ x86 test suite                                             ║"
	@echo "║   ✓ LLVM test suite                                            ║"
	@echo "║                                                                ║"
	@echo "║ Promoted: bootstrap/$(GIT_COMMIT)/                             ║"
	@echo "║   - compiler.s (x86, Linux fast path)                          ║"
	@echo "║   - compiler_linux.ll (LLVM, Linux)                            ║"
	@echo "║   - compiler_macos.ll (LLVM, macOS)                            ║"
	@echo "║   - lang_reader/source.ast                                     ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "========================================"
	@echo "YOU MUST COMMIT YOUR CHANGES NOW"
	@echo "  git add -A && git commit -m 'your message'"
	@echo "========================================"

# ============================================================
# LLVM-VERIFY: Mac-only verification without x86 bootstrap
# ============================================================
# Use this on Mac to verify compiler changes work:
#   1. Builds gen1 compiler using LLVM backend
#   2. Builds gen2 compiler using gen1
#   3. Checks LLVM IR fixed point (gen1.ll === gen2.ll)
#   4. Runs full test suite
#
# Requires: ./lang (bootstrap from llvm_libc_macos.ll)
# Usage: make llvm-verify
llvm-verify:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║           LLVM-VERIFY: Mac Bootstrap Verification              ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@if [ ! -f ./lang ]; then \
		echo "ERROR: ./lang not found. Run: clang bootstrap/llvm_libc_macos.ll -o lang"; \
		exit 1; \
	fi
	@mkdir -p out /tmp/llvm_verify
	@# Set up macOS OS layer
	@echo 'include "std/os/libc_macos.lang"' > std/os.lang
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 1: Build gen1 compiler (bootstrap -> gen1)               │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	LANGBE=llvm LANGOS=macos ./lang std/core.lang src/lexer.lang src/parser.lang \
		src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang \
		src/sexpr_reader.lang src/main.lang -o /tmp/llvm_verify/gen1.ll
	clang /tmp/llvm_verify/gen1.ll -o /tmp/llvm_verify/gen1
	@echo "Built: gen1"
	@# Copy to out/lang for reader compilation
	cp /tmp/llvm_verify/gen1 out/lang
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 2: Build gen2 compiler (gen1 -> gen2)                    │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	LANGBE=llvm LANGOS=macos /tmp/llvm_verify/gen1 std/core.lang src/lexer.lang src/parser.lang \
		src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang \
		src/sexpr_reader.lang src/main.lang -o /tmp/llvm_verify/gen2.ll
	@echo ""
	@echo "Checking LLVM IR FIXED POINT (gen1.ll === gen2.ll)..."
	@if diff -q /tmp/llvm_verify/gen1.ll /tmp/llvm_verify/gen2.ll > /dev/null; then \
		echo "✓ LLVM FIXED POINT VERIFIED"; \
	else \
		echo ""; \
		echo "!!! LLVM FIXED POINT FAILED !!!"; \
		echo "gen1.ll and gen2.ll differ:"; \
		diff /tmp/llvm_verify/gen1.ll /tmp/llvm_verify/gen2.ll | head -30; \
		exit 1; \
	fi
	clang /tmp/llvm_verify/gen2.ll -o /tmp/llvm_verify/gen2
	@echo "Built: gen2"
	@echo ""
	@echo "┌────────────────────────────────────────────────────────────────┐"
	@echo "│ STAGE 3: Run test suite                                        │"
	@echo "└────────────────────────────────────────────────────────────────┘"
	@# Ensure out/lang points to verified gen2
	cp /tmp/llvm_verify/gen2 out/lang
	COMPILER=/tmp/llvm_verify/gen2 ./test/run_llvm_suite.sh
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║              LLVM-VERIFY COMPLETE                              ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║ ✓ LLVM fixed point verified (gen1.ll === gen2.ll)              ║"
	@echo "║ ✓ Test suite passed                                            ║"
	@echo "║                                                                ║"
	@echo "║ Verified compiler: out/lang                                    ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"

# Release: run bootstrap + git tag
release:
	@if [ -z "$(TAG)" ]; then \
		echo "Usage: make release TAG=v0.2.0"; \
		exit 1; \
	fi
	@$(MAKE) bootstrap
	@cp bootstrap/current/compiler.s bootstrap/$(TAG).s
	@git add bootstrap/$(TAG).s
	@echo "Saved bootstrap/$(TAG).s"
	@echo "Run: git commit -m 'Release $(TAG)' && git tag $(TAG)"

# Run the test suite
test-suite:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	@./test/run_lang1_suite.sh

# Run ALL tests
test-all: test-suite test-run

# Compile and run sample test programs
test-run:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	@echo "=== hello.lang ===" && \
	$(LANG) test/suite/181_hello.lang -o out/hello.s && \
	as out/hello.s -o out/hello.o && \
	ld out/hello.o -o out/hello && \
	./out/hello && rm -f out/hello.o
	@echo "=== factorial.lang ===" && \
	$(LANG) test/suite/174_factorial.lang -o out/factorial.s && \
	as out/factorial.s -o out/factorial.o && \
	ld out/factorial.o -o out/factorial && \
	./out/factorial && rm -f out/factorial.o

# Compile a .lang file (usage: make compile FILE=test/hello.lang)
compile:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	$(LANG) $(FILE) -o out/$(notdir $(basename $(FILE))).s

# Full build chain for a .lang file (usage: make run FILE=test/hello.lang)
run:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	$(LANG) $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE)))

# Build with stdlib (usage: make stdlib-run FILE=myprogram.lang)
stdlib-run:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	$(LANG) std/core.lang $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE)))

# Run with development compiler (usage: make dev-run FILE=test/suite/188_effect_exception.lang)
dev-run:
	@if [ ! -L $(LANG_NEXT) ]; then echo "Run 'make build' first"; exit 1; fi
	$(LANG_NEXT) $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE))); echo "Exit: $$?"

# Run with dev compiler + stdlib (usage: make dev-stdlib-run FILE=myprogram.lang)
dev-stdlib-run:
	@if [ ! -L $(LANG_NEXT) ]; then echo "Run 'make build' first"; exit 1; fi
	$(LANG_NEXT) std/core.lang $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE))); echo "Exit: $$?"

# Clean: remove non-essential build artifacts
clean:
	rm -f out/*.s out/*.o out/verify.s
	rm -f out/hello out/factorial
	rm -f $(LANG_NEXT)

# Distclean: remove everything in out/
distclean:
	rm -rf out/*

# Show current state
status:
	@echo "Bootstrap: $(BOOTSTRAP) -> $$(readlink $(BOOTSTRAP))"
	@echo "Current commit: $(VERSION)"
	@if [ -L $(LANG) ]; then \
		echo "lang -> $$(readlink $(LANG))"; \
	else \
		echo "lang: not set (run 'make bootstrap')"; \
	fi
	@if [ -L $(LANG_NEXT) ]; then \
		echo "lang_next -> $$(readlink $(LANG_NEXT))"; \
	fi

# ============================================================
# SPLIT ARCHITECTURE: kernel + lang_reader
# ============================================================
#
# The compiler is split into:
#   kernel = AST -> x86 (codegen + sexpr_reader)
#   lang_reader = lang -> AST (lexer + parser + ast_emit)
#
# Composition: kernel -c lang_reader.ast = full lang compiler

# Kernel core (for composition - no main)
# Note: parser.lang needed for AST node accessors used by codegen and sexpr_reader
# Note: limits.lang is included by std/core.lang, don't list explicitly
KERNEL_CORE := std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/sexpr_reader.lang

# Kernel binary sources (core + main for standalone kernel)
KERNEL_SOURCES := $(KERNEL_CORE) src/kernel_main.lang

# Lang reader sources (includes lexer/parser/ast_emit + the reader definition)
# Note: limits.lang is included by std/core.lang, don't list explicitly
LANG_READER_SOURCES := std/core.lang src/lexer.lang src/parser.lang src/ast_emit.lang src/lang_reader.lang

# Compiler entry point (uses reader_transform from reader + generate from kernel)
COMPILER_SOURCES := src/compiler.lang

# Build kernel binary (AST -> x86)
build-kernel:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	@mkdir -p out
	$(LANG) $(KERNEL_SOURCES) -o out/kernel.s
	as out/kernel.s -o out/kernel.o
	ld out/kernel.o -o out/kernel
	rm -f out/kernel.o
	@echo "Built: out/kernel"

# Build lang_reader binary (standalone tool: lang -> AST to stdout)
build-lang-reader:
	@if [ ! -L $(LANG) ]; then $(MAKE) init; fi
	@mkdir -p out
	$(LANG) $(LANG_READER_SOURCES) src/reader_main.lang -o out/lang_reader.s
	as out/lang_reader.s -o out/lang_reader.o
	ld out/lang_reader.o -o out/lang_reader
	rm -f out/lang_reader.o
	@echo "Built: out/lang_reader"

# Emit kernel core AST (for composition - no main)
# Note: requires lang_next which has --emit-ast support
emit-kernel-ast: build
	@mkdir -p out/ast
	$(LANG_NEXT) $(KERNEL_CORE) --emit-ast -o out/ast/kernel.ast
	@echo "Wrote: out/ast/kernel.ast"

# Emit lang_reader AST (for composition - just the reader, deps come from kernel)
emit-lang-reader-ast: build
	@mkdir -p out/ast
	$(LANG_NEXT) src/lang_reader.lang --emit-ast -o out/ast/lang_reader.ast
	@echo "Wrote: out/ast/lang_reader.ast"

# Emit compiler AST (for composition)
emit-compiler-ast: build
	@mkdir -p out/ast
	$(LANG_NEXT) $(COMPILER_SOURCES) --emit-ast -o out/ast/compiler.ast
	@echo "Wrote: out/ast/compiler.ast"

# Seed the bootstrap directory with initial AST files
seed-bootstrap: emit-kernel-ast emit-lang-reader-ast emit-compiler-ast
	@mkdir -p bootstrap/$(GIT_COMMIT)/kernel bootstrap/$(GIT_COMMIT)/lang_reader bootstrap/$(GIT_COMMIT)/compiler
	cp out/ast/kernel.ast bootstrap/$(GIT_COMMIT)/kernel/source.ast
	cp out/ast/lang_reader.ast bootstrap/$(GIT_COMMIT)/lang_reader/source.ast
	cp out/ast/compiler.ast bootstrap/$(GIT_COMMIT)/compiler/source.ast
	@echo "Seeded: bootstrap/$(GIT_COMMIT)/"
	@echo "To activate: ln -sfn $(GIT_COMMIT) bootstrap/current"

# Test composition: kernel -c lang_reader.ast -o lang_composed.s
test-composition: build-kernel emit-kernel-ast emit-lang-reader-ast emit-compiler-ast
	@echo "=== Testing composition: kernel -c lang_reader.ast ==="
	./out/kernel -c out/ast/lang_reader.ast \
		--kernel-ast out/ast/kernel.ast \
		--compiler-ast out/ast/compiler.ast \
		-o out/lang_composed.s
	as out/lang_composed.s -o out/lang_composed.o
	ld out/lang_composed.o -o out/lang_composed
	rm -f out/lang_composed.o
	@echo "Built: out/lang_composed"
	@echo ""
	@echo "Testing composed compiler on hello.lang..."
	./out/lang_composed test/suite/181_hello.lang -o /tmp/hello_composed.s
	as /tmp/hello_composed.s -o /tmp/hello_composed.o
	ld /tmp/hello_composed.o -o /tmp/hello_composed
	@/tmp/hello_composed && echo "SUCCESS: Composed compiler works!"

# Test bootstrap: verify true fixed point
# The fixed point is: A -c lang.lang === B -c lang.lang
# where A = {kernel -c lang.ast} -c lang.lang
# NOT: {kernel -c lang.ast} === A (AST-built vs source-built may differ)
test-bootstrap: test-composition
	@echo ""
	@echo "=== Building first generation: lang_composed -c lang_reader.lang ==="
	./out/lang_composed -c src/lang_reader.lang \
		--kernel-ast out/ast/kernel.ast \
		--compiler-ast out/ast/compiler.ast \
		-o out/lang_bootstrap.s
	as out/lang_bootstrap.s -o out/lang_bootstrap.o
	ld out/lang_bootstrap.o -o out/lang_bootstrap
	rm -f out/lang_bootstrap.o
	@echo "Built: out/lang_bootstrap"
	@echo ""
	@echo "=== Testing fixed point: lang_bootstrap -c lang_reader.lang ==="
	./out/lang_bootstrap -c src/lang_reader.lang \
		--kernel-ast out/ast/kernel.ast \
		--compiler-ast out/ast/compiler.ast \
		-o out/lang_bootstrap2.s
	@if diff -q out/lang_bootstrap.s out/lang_bootstrap2.s > /dev/null; then \
		echo "FIXED POINT ACHIEVED: lang_bootstrap can bootstrap itself!"; \
	else \
		echo "ERROR: Fixed point not reached!"; \
		exit 1; \
	fi

# OLD TARGETS REMOVED - use unified 'make verify' and 'make promote' instead
# The unified verify does both kernel and reader fixed point checks in one command
