.PHONY: all build test test-run test-suite test-all test-stdlib clean

# Default target
all: build

# Run ALL tests (suite + sample programs + stdlib)
test-all: build test-suite test-run test-stdlib
	@echo "\n=== All tests complete ==="

# Build the Phase 0 compiler
build:
	cd boot && go build -o lang0

# Show AST for test files
test: build
	@echo "=== hello.lang ==="
	./boot/lang0 test/hello.lang --ast
	@echo "\n=== factorial.lang ==="
	./boot/lang0 test/factorial.lang --ast

# Run the full test suite (67 tests)
test-suite: build
	@./test/run_suite.sh

# Compile and run sample test programs
test-run: build
	@mkdir -p out
	@echo "=== hello.lang ===" && \
	./boot/lang0 test/hello.lang -o out/hello.s && \
	as out/hello.s -o out/hello.o && \
	ld out/hello.o -o out/hello && \
	./out/hello
	@echo "=== factorial.lang ===" && \
	./boot/lang0 test/factorial.lang -o out/factorial.s && \
	as out/factorial.s -o out/factorial.o && \
	ld out/factorial.o -o out/factorial && \
	./out/factorial

# Clean build artifacts
clean:
	rm -f boot/lang0
	rm -rf out/*

# Compile a .lang file to assembly (usage: make compile FILE=test/hello.lang)
compile: build
	@mkdir -p out
	./boot/lang0 $(FILE) -o out/$(notdir $(basename $(FILE))).s

# Full build chain for a .lang file (usage: make run FILE=test/hello.lang)
run: build
	@mkdir -p out
	./boot/lang0 $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE)))

# Show generated assembly
asm: build
	@mkdir -p out
	./boot/lang0 $(FILE) -o out/$(notdir $(basename $(FILE))).s
	cat out/$(notdir $(basename $(FILE))).s

# Build with stdlib (usage: make stdlib-run FILE=myprogram.lang)
stdlib-run: build
	@mkdir -p out
	./boot/lang0 std/core.lang $(FILE) -o out/$(notdir $(basename $(FILE))).s
	as out/$(notdir $(basename $(FILE))).s -o out/$(notdir $(basename $(FILE))).o
	ld out/$(notdir $(basename $(FILE))).o -o out/$(notdir $(basename $(FILE)))
	./out/$(notdir $(basename $(FILE)))

# Test stdlib with sample program
test-stdlib: build
	@mkdir -p out
	@echo "=== stdlib_test.lang ==="
	@./boot/lang0 std/core.lang test/stdlib_test.lang -o out/stdlib_test.s && \
	as out/stdlib_test.s -o out/stdlib_test.o && \
	ld out/stdlib_test.o -o out/stdlib_test && \
	./out/stdlib_test
