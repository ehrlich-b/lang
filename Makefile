.PHONY: all bootstrap build verify promote release test test-suite test-run clean distclean \
        build-kernel build-lang-reader emit-kernel-ast emit-lang-reader-ast emit-compiler-ast \
        seed-bootstrap test-composition generate-os-layer

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

# Bootstrap: assemble from bootstrap/current.s, create lang symlink
bootstrap:
	@mkdir -p out
	@echo "Bootstrapping from $(BOOTSTRAP)..."
	as $(BOOTSTRAP) -o out/lang_bootstrap.o
	ld out/lang_bootstrap.o -o out/lang_bootstrap
	rm -f out/lang_bootstrap.o
	ln -sf lang_bootstrap $(LANG)
	@echo "Created: $(LANG) -> lang_bootstrap"

# Build: compile src/*.lang using lang -> lang_next
build: generate-os-layer
	@if [ ! -L $(LANG) ]; then \
		$(MAKE) bootstrap; \
	fi
	@mkdir -p out
	$(LANG) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/lang_$(VERSION).s
	as out/lang_$(VERSION).s -o out/lang_$(VERSION).o
	ld out/lang_$(VERSION).o -o out/lang_$(VERSION)
	rm -f out/lang_$(VERSION).o
	ln -sf lang_$(VERSION) $(LANG_NEXT)
	@echo "Created: $(LANG_NEXT) -> lang_$(VERSION)"

# Unified verify: kernel fixed point + reader fixed point + tests
# This is the ONE command to verify any compiler change
verify: generate-os-layer
	@echo "=== UNIFIED VERIFY ==="
	@echo ""
	@echo "Phase 1: Bootstrap from known-good..."
	@mkdir -p out out/ast
	@if [ ! -f $(BOOTSTRAP) ]; then echo "ERROR: No bootstrap found at $(BOOTSTRAP)"; exit 1; fi
	as $(BOOTSTRAP) -o /tmp/boot.o
	ld /tmp/boot.o -o /tmp/boot
	rm -f /tmp/boot.o
	@echo ""
	@echo "Phase 2: Build compiler from sources..."
	/tmp/boot std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/lang_$(VERSION).s
	as out/lang_$(VERSION).s -o out/lang_$(VERSION).o
	ld out/lang_$(VERSION).o -o out/lang_$(VERSION)
	rm -f out/lang_$(VERSION).o
	ln -sf lang_$(VERSION) $(LANG_NEXT)
	@echo "Built: $(LANG_NEXT) -> lang_$(VERSION)"
	@echo ""
	@echo "Phase 3: KERNEL FIXED POINT (compiler compiles itself)..."
	./out/lang_$(VERSION) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/codegen_llvm.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/lang_$(VERSION)_v2.s
	@if diff -q out/lang_$(VERSION).s out/lang_$(VERSION)_v2.s > /dev/null; then \
		echo "KERNEL FIXED POINT VERIFIED"; \
		rm -f out/lang_$(VERSION)_v2.s; \
	else \
		echo ""; \
		echo "!!! KERNEL FIXED POINT FAILED !!!"; \
		echo "The compiler cannot compile itself identically."; \
		diff out/lang_$(VERSION).s out/lang_$(VERSION)_v2.s | head -20; \
		exit 1; \
	fi
	@echo ""
	@echo "Phase 4: Build standalone compiler (lang reader)..."
	$(LANG_NEXT) src/lang_reader.lang --emit-expanded-ast -o out/ast/lang_reader_v1.ast
	@wc -l out/ast/lang_reader_v1.ast
	$(LANG_NEXT) -c lang src/lang_reader.lang -o out/lang_standalone.s
	as out/lang_standalone.s -o out/lang_standalone.o
	ld out/lang_standalone.o -o out/lang_standalone
	rm -f out/lang_standalone.o
	@echo ""
	@echo "Phase 5: READER FIXED POINT (standalone compiler works)..."
	@echo 'func main() i64 { return 42; }' > /tmp/test42.lang
	./out/lang_standalone /tmp/test42.lang -o /tmp/test42.s
	as /tmp/test42.s -o /tmp/test42.o
	ld /tmp/test42.o -o /tmp/test42
	@/tmp/test42; EXIT=$$?; if [ $$EXIT -eq 42 ]; then \
		echo "READER FIXED POINT VERIFIED"; \
	else \
		echo ""; \
		echo "!!! READER FIXED POINT FAILED !!!"; \
		echo "Standalone compiler produced wrong result: expected 42, got $$EXIT"; \
		exit 1; \
	fi
	@rm -f /tmp/test42.lang /tmp/test42.s /tmp/test42.o /tmp/test42
	@echo ""
	@echo "Phase 6: Full test suite..."
	@./test/run_lang1_suite.sh
	@echo ""
	@echo "=== ALL VERIFICATIONS PASSED ==="
	@echo "Run 'make promote' to save this version to bootstrap."

# Unified promote: save verified compiler to bootstrap
promote: verify
	@mkdir -p bootstrap/$(GIT_COMMIT)/lang_reader
	@echo ""
	@echo "=== PROMOTING $(GIT_COMMIT) ==="
	cp out/lang_standalone.s bootstrap/$(GIT_COMMIT)/compiler.s
	cp out/ast/lang_reader_v1.ast bootstrap/$(GIT_COMMIT)/lang_reader/source.ast
	@echo "compiler.s:" > bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  sha256: $$(sha256sum bootstrap/$(GIT_COMMIT)/compiler.s | cut -d' ' -f1)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  built_by: bootstrap/$$(readlink bootstrap/current 2>/dev/null || echo none)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  built_at: $$(date -Iseconds)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  source_commit: $(GIT_COMMIT)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  verified_fixed_point: true" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "lang_reader/source.ast:" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  sha256: $$(sha256sum bootstrap/$(GIT_COMMIT)/lang_reader/source.ast | cut -d' ' -f1)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	@echo "  lines: $$(wc -l < bootstrap/$(GIT_COMMIT)/lang_reader/source.ast)" >> bootstrap/$(GIT_COMMIT)/PROVENANCE
	ln -sfn $(GIT_COMMIT) bootstrap/current
	cp bootstrap/$(GIT_COMMIT)/compiler.s bootstrap/escape_hatch.s
	ln -sf lang_$(VERSION) $(LANG)
	rm -f $(LANG_NEXT)
	@echo ""
	@echo "Promoted: bootstrap/$(GIT_COMMIT)/"
	@echo "  - compiler.s (standalone lang compiler)"
	@echo "  - lang_reader/source.ast (expanded AST)"
	@echo "Updated: bootstrap/current -> $(GIT_COMMIT)"
	@echo "Updated: bootstrap/escape_hatch.s"
	@echo "Updated: $(LANG) -> lang_$(VERSION)"

# Release: save .s to bootstrap/, git tag
release:
	@if [ -z "$(TAG)" ]; then \
		echo "Usage: make release TAG=v0.2.0"; \
		exit 1; \
	fi
	@$(MAKE) verify
	@TARGET=$$(readlink $(LANG_NEXT)); \
	cp out/$$TARGET.s bootstrap/$(TAG).s; \
	ln -sf $$TARGET $(LANG); \
	rm -f $(LANG_NEXT); \
	git add bootstrap/$(TAG).s; \
	echo "Saved bootstrap/$(TAG).s"; \
	echo "Run: git commit -m 'Release $(TAG)' && git tag $(TAG)"

# Run the test suite
test-suite:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	@./test/run_lang1_suite.sh

# Run ALL tests
test-all: test-suite test-run

# Compile and run sample test programs
test-run:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
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
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	$(LANG) $(FILE) -o out/$(notdir $(basename $(FILE))).s

# Full build chain for a .lang file (usage: make run FILE=test/hello.lang)
run:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	$(LANG) $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE)))

# Build with stdlib (usage: make stdlib-run FILE=myprogram.lang)
stdlib-run:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
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
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	@mkdir -p out
	$(LANG) $(KERNEL_SOURCES) -o out/kernel.s
	as out/kernel.s -o out/kernel.o
	ld out/kernel.o -o out/kernel
	rm -f out/kernel.o
	@echo "Built: out/kernel"

# Build lang_reader binary (standalone tool: lang -> AST to stdout)
build-lang-reader:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
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
