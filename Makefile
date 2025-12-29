.PHONY: all bootstrap build verify promote release test test-suite test-run clean distclean \
        build-kernel build-lang-reader emit-kernel-ast emit-lang-reader-ast emit-compiler-ast \
        seed-bootstrap test-composition

# Get git info
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_DIRTY := $(shell git diff --quiet 2>/dev/null || echo "-dirty")
VERSION := $(GIT_COMMIT)$(GIT_DIRTY)

# Bootstrap file
BOOTSTRAP := bootstrap/current.s

# Compiler paths
LANG := out/lang
LANG_NEXT := out/lang_next

# Default target
all: build

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
build:
	@if [ ! -L $(LANG) ]; then \
		$(MAKE) bootstrap; \
	fi
	@mkdir -p out
	$(LANG) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/lang_$(VERSION).s
	as out/lang_$(VERSION).s -o out/lang_$(VERSION).o
	ld out/lang_$(VERSION).o -o out/lang_$(VERSION)
	rm -f out/lang_$(VERSION).o
	ln -sf lang_$(VERSION) $(LANG_NEXT)
	@echo "Created: $(LANG_NEXT) -> lang_$(VERSION)"

# Verify: lang_next compiles src/*.lang, check fixed point, run tests
verify: build
	@if [ ! -L $(LANG_NEXT) ]; then \
		echo "ERROR: No lang_next to verify. Run 'make build' first."; \
		exit 1; \
	fi
	$(LANG_NEXT) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/ast_emit.lang src/sexpr_reader.lang src/main.lang -o out/verify.s
	@if diff -q out/lang_$(VERSION).s out/verify.s > /dev/null; then \
		echo "FIXED POINT VERIFIED: lang_$(VERSION)"; \
		rm -f out/verify.s; \
	else \
		echo "ERROR: Fixed point not reached!"; \
		echo "diff out/lang_$(VERSION).s out/verify.s"; \
		exit 1; \
	fi
	@echo ""
	@echo "Running test suite..."
	@COMPILER=$(LANG_NEXT) ./test/run_lang1_suite.sh

# Promote: update lang symlink and save bootstrap checkpoint
promote: verify
	@TARGET=$$(readlink $(LANG_NEXT)); \
	ln -sf $$TARGET $(LANG); \
	rm -f $(LANG_NEXT); \
	echo "Promoted: $(LANG) -> $$TARGET"; \
	cp out/$$TARGET.s bootstrap/$(GIT_COMMIT).s; \
	ln -sf $(GIT_COMMIT).s bootstrap/current.s; \
	echo "Saved bootstrap: bootstrap/$(GIT_COMMIT).s"

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
KERNEL_CORE := std/core.lang src/limits.lang src/lexer.lang src/parser.lang src/codegen.lang src/sexpr_reader.lang

# Kernel binary sources (core + main for standalone kernel)
KERNEL_SOURCES := $(KERNEL_CORE) src/kernel_main.lang

# Lang reader sources (includes lexer/parser/ast_emit + the reader definition)
LANG_READER_SOURCES := std/core.lang src/limits.lang src/lexer.lang src/parser.lang src/ast_emit.lang src/lang_reader.lang

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
emit-kernel-ast:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	@mkdir -p out/ast
	$(LANG) $(KERNEL_CORE) --emit-ast -o out/ast/kernel.ast
	@echo "Wrote: out/ast/kernel.ast"

# Emit lang_reader AST (for composition - just the reader, deps come from kernel)
emit-lang-reader-ast:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	@mkdir -p out/ast
	$(LANG) src/lang_reader.lang --emit-ast -o out/ast/lang_reader.ast
	@echo "Wrote: out/ast/lang_reader.ast"

# Emit compiler AST (for composition)
emit-compiler-ast:
	@if [ ! -L $(LANG) ]; then $(MAKE) bootstrap; fi
	@mkdir -p out/ast
	$(LANG) $(COMPILER_SOURCES) --emit-ast -o out/ast/compiler.ast
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

# Test bootstrap: lang_composed -c lang_reader.lang should produce identical output
test-bootstrap: test-composition
	@echo ""
	@echo "=== Testing bootstrap: lang_composed -c lang_reader.lang ==="
	./out/lang_composed -c src/lang_reader.lang \
		--kernel-ast out/ast/kernel.ast \
		--compiler-ast out/ast/compiler.ast \
		-o out/lang_bootstrap.s
	@if diff -q out/lang_composed.s out/lang_bootstrap.s > /dev/null; then \
		echo "BOOTSTRAP VERIFIED: lang_composed.s == lang_bootstrap.s"; \
	else \
		echo "ERROR: Bootstrap mismatch!"; \
		exit 1; \
	fi
	@echo ""
	@echo "=== Testing fixed point: lang_bootstrap -c lang_reader.lang ==="
	as out/lang_bootstrap.s -o out/lang_bootstrap.o
	ld out/lang_bootstrap.o -o out/lang_bootstrap
	rm -f out/lang_bootstrap.o
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
