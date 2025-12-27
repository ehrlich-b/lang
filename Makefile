.PHONY: all bootstrap build verify promote release test test-suite test-run clean distclean

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
	$(LANG) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/main.lang -o out/lang_$(VERSION).s
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
	$(LANG_NEXT) std/core.lang src/lexer.lang src/parser.lang src/codegen.lang src/main.lang -o out/verify.s
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
