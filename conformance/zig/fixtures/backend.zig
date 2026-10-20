const builtin = @import("builtin");
comptime {
    if (builtin.zig_backend != .stage2_llvm)
        @compileError("oracle compatibility branch must be stage2_llvm");
    if (builtin.cpu.arch != .x86_64 or builtin.os.tag != .linux)
        @compileError("oracle target must be x86_64 Linux");
    if (builtin.abi != .musl or builtin.object_format != .elf or builtin.link_libc)
        @compileError("oracle ABI must be ELF musl without libc linkage");
}
test "profile branch is frozen" {}
