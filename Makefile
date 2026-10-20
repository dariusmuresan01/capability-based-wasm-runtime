# Makefile for the Capability-Based WebAssembly Runtime - Auto-compiles all C tests to WebAssembly

# Default compiler and sysroot (Arch Linux defaults)
# Mac/Windows users can override these via the command line.
CC = clang
SYSROOT ?= /usr/share/wasi-sysroot
CFLAGS = --target=wasm32-wasip1 --sysroot=$(SYSROOT)

# Find all .c files in the tests directory and its subdirectories
SOURCES = $(wildcard tests/*/*.c)

# Define the target .wasm files by replacing the .c extension
TARGETS = $(SOURCES:.c=.wasm)

.PHONY: all clean

# Default rule: compile everything
all: $(TARGETS)

# Generic rule to compile any .c file to a .wasm file in the same directory
%.wasm: %.c
	$(CC) $(CFLAGS) $< -o $@
	@echo "Compiled: $< -> $@"

# Clean up all compiled WebAssembly binaries
clean:
	rm -f $(TARGETS)
	@echo "Cleaned all .wasm files."