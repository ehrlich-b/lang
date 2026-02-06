// lang_ast.zig - AIR→lang AST S-expression codegen backend
//
// This is a Zig compiler backend that emits lang AST (S-expressions) instead
// of machine code. It allows capturing Zig programs as lang AST, which can
// then be compiled through lang's LLVM backend.
//
// Output format matches lang's ast_emit.lang / sexpr_reader.lang format:
//   (func name ((param1 type1) (param2 type2)) ret_type body...)
//
// Integration: Activated by -ofmt=lang-ast flag. Wired through:
//   lib/std/Target.zig    - ObjectFormat.lang_ast
//   lib/std/builtin.zig   - CompilerBackend.stage2_lang_ast
//   src/codegen.zig       - dispatch to this file

const std = @import("std");
const Allocator = std.mem.Allocator;
const Air = @import("../Air.zig");
const Liveness = Air.Liveness;
const Zcu = @import("../Zcu.zig");
const InternPool = @import("../InternPool.zig");
const link = @import("../link.zig");
const Type = @import("../Type.zig");

/// Result of code generation for a single function.
pub const Mir = struct {
    code: []u8,

    pub fn deinit(mir: *Mir, gpa: Allocator) void {
        gpa.free(mir.code);
    }
};

/// Tracks state for generating a single function's S-expression output.
const Function = struct {
    gpa: Allocator,
    air: Air,
    zcu: *Zcu,
    output: std.ArrayList(u8),
    indent: u32,

    /// AIR inst index -> variable name string
    value_map: std.AutoHashMap(Air.InstIndex, []const u8),

    /// Counter for generating temporary variable names
    next_temp: u32,

    /// Counter for generating block labels
    next_block: u32,

    /// Tracks names allocated by this function (for cleanup)
    allocated_names: std.ArrayList([]const u8),

    fn init(gpa: Allocator, air: Air, zcu: *Zcu) Function {
        return .{
            .gpa = gpa,
            .air = air,
            .zcu = zcu,
            .output = std.ArrayList(u8).init(gpa),
            .indent = 0,
            .value_map = std.AutoHashMap(Air.InstIndex, []const u8).init(gpa),
            .next_temp = 0,
            .next_block = 0,
            .allocated_names = std.ArrayList([]const u8).init(gpa),
        };
    }

    fn deinit(f: *Function) void {
        for (f.allocated_names.items) |name| {
            f.gpa.free(name);
        }
        f.allocated_names.deinit();
        f.value_map.deinit();
        f.output.deinit();
    }

    // -----------------------------------------------------------------
    // Output helpers
    // -----------------------------------------------------------------

    fn emit(f: *Function, s: []const u8) !void {
        try f.output.appendSlice(s);
    }

    fn emitByte(f: *Function, b: u8) !void {
        try f.output.append(b);
    }

    fn emitFmt(f: *Function, comptime fmt: []const u8, args: anytype) !void {
        try f.output.writer().print(fmt, args);
    }

    fn emitNewline(f: *Function) !void {
        try f.emitByte('\n');
        var i: u32 = 0;
        while (i < f.indent) : (i += 1) {
            try f.emit("  ");
        }
    }

    // -----------------------------------------------------------------
    // Name management
    // -----------------------------------------------------------------

    fn allocName(f: *Function, comptime fmt: []const u8, args: anytype) ![]const u8 {
        const name = try std.fmt.allocPrint(f.gpa, fmt, args);
        try f.allocated_names.append(name);
        return name;
    }

    fn freshTemp(f: *Function) ![]const u8 {
        const n = f.next_temp;
        f.next_temp += 1;
        return f.allocName("t{d}", .{n});
    }

    fn freshBlock(f: *Function) ![]const u8 {
        const n = f.next_block;
        f.next_block += 1;
        return f.allocName("blk{d}", .{n});
    }

    fn nameForInst(f: *Function, inst: Air.InstIndex) ![]const u8 {
        if (f.value_map.get(inst)) |name| return name;
        const name = try f.freshTemp();
        try f.value_map.put(inst, name);
        return name;
    }

    // -----------------------------------------------------------------
    // Type mapping
    // -----------------------------------------------------------------

    fn mapType(f: *Function, ty: Type) ![]const u8 {
        const ip = &f.zcu.intern_pool;
        const tag = ty.toIntern();
        switch (ip.indexToKey(tag)) {
            .int_type => |int_info| {
                return mapIntType(int_info.bits, int_info.signedness);
            },
            .ptr_type => return "*u8", // simplified pointer representation
            .simple_type => |st| {
                return switch (st) {
                    .void => "void",
                    .bool => "bool",
                    .usize => "u64",
                    .isize => "i64",
                    .f32 => "f32",
                    .f64 => "f64",
                    .noreturn => "void",
                    .u8 => "u8",
                    .i8 => "i8",
                    .u16 => "u16",
                    .i16 => "i16",
                    .u32 => "u32",
                    .i32 => "i32",
                    .u64 => "u64",
                    .i64 => "i64",
                    .u128 => "u128",
                    .i128 => "i128",
                    .comptime_int => "i64",
                    .comptime_float => "f64",
                    else => "i64", // fallback
                };
            },
            .float_type => |float_info| {
                return switch (float_info.bits) {
                    32 => "f32",
                    64 => "f64",
                    else => "f64",
                };
            },
            else => return "i64", // fallback for complex types
        }
    }

    fn mapIntType(bits: u16, signedness: std.builtin.Signedness) []const u8 {
        const is_signed = signedness == .signed;
        if (bits <= 8) return if (is_signed) "i8" else "u8";
        if (bits <= 16) return if (is_signed) "i16" else "u16";
        if (bits <= 32) return if (is_signed) "i32" else "u32";
        if (bits <= 64) return if (is_signed) "i64" else "u64";
        if (bits <= 128) return if (is_signed) "i128" else "u128";
        return "i64"; // fallback
    }

    /// Returns whether a type is unsigned (for comparison instruction selection)
    fn isUnsigned(f: *Function, ty: Type) bool {
        const ip = &f.zcu.intern_pool;
        const tag = ty.toIntern();
        switch (ip.indexToKey(tag)) {
            .int_type => |int_info| return int_info.signedness == .unsigned,
            .ptr_type => return true, // pointers are unsigned for comparison
            .simple_type => |st| {
                return switch (st) {
                    .u8, .u16, .u32, .u64, .u128, .usize => true,
                    .bool => true,
                    else => false,
                };
            },
            else => return false,
        }
    }

    // -----------------------------------------------------------------
    // Operand resolution
    // -----------------------------------------------------------------

    fn resolveInst(f: *Function, ref: Air.Inst.Ref) ![]const u8 {
        if (ref.toIndex()) |inst| {
            return f.nameForInst(inst);
        }
        // It's a constant reference - resolve from intern pool
        return f.resolveConstant(ref);
    }

    fn resolveConstant(f: *Function, ref: Air.Inst.Ref) ![]const u8 {
        const ip = &f.zcu.intern_pool;
        const ip_index = ref.toInterned().?;
        switch (ip.indexToKey(ip_index)) {
            .int => |int_val| {
                const val = switch (int_val.storage) {
                    .u64 => |v| return f.allocName("{d}", .{v}),
                    .i64 => |v| return f.allocName("{d}", .{v}),
                    .big_int => return "0", // simplified
                    .lazy_align, .lazy_size => return "0",
                };
                _ = val;
            },
            .float => |float_val| {
                return switch (float_val.storage) {
                    .f32 => |v| f.allocName("{d:.6}", .{v}),
                    .f64 => |v| f.allocName("{d:.6}", .{v}),
                    else => "0.0",
                };
            },
            .enum_tag => return "0", // simplified enum handling
            .undef => return "0",
            .ptr => return "nil",
            else => return "0",
        }
    }

    // -----------------------------------------------------------------
    // Type resolution for an AIR instruction's result
    // -----------------------------------------------------------------

    fn typeOfInst(f: *Function, inst: Air.InstIndex) Type {
        return f.air.typeOfIndex(inst, f.zcu);
    }

    fn typeOfRef(f: *Function, ref: Air.Inst.Ref) Type {
        return f.air.typeOf(ref, f.zcu);
    }

    // -----------------------------------------------------------------
    // Instruction handlers
    // -----------------------------------------------------------------

    fn airArg(f: *Function, inst: Air.InstIndex) !void {
        const ty = f.typeOfInst(inst);
        const ty_str = try f.mapType(ty);
        // Args are pre-named by generate(); just record the mapping if needed
        const name = try f.nameForInst(inst);
        _ = name;
        _ = ty_str;
    }

    fn airRet(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = data.un_op;
        try f.emitNewline();
        if (operand == .none) {
            try f.emit("(return)");
        } else {
            const val = try f.resolveInst(operand);
            try f.emitFmt("(return {s})", .{val});
        }
    }

    fn airRetVoid(f: *Function) !void {
        try f.emitNewline();
        try f.emit("(return)");
    }

    fn airBinOp(f: *Function, inst: Air.InstIndex, op_str: []const u8) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const bin_op = data.bin_op;
        const lhs = try f.resolveInst(bin_op.lhs);
        const rhs = try f.resolveInst(bin_op.rhs);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} i64 ({s} {s} {s}))", .{ name, op_str, lhs, rhs });
    }

    fn airCmpOp(f: *Function, inst: Air.InstIndex, op_str: []const u8) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const bin_op = data.bin_op;
        const lhs = try f.resolveInst(bin_op.lhs);
        const rhs = try f.resolveInst(bin_op.rhs);
        const name = try f.nameForInst(inst);
        // Check signedness for unsigned comparisons (ult/ugt/ule/uge)
        const lhs_ty = f.typeOfRef(bin_op.lhs);
        const unsigned = f.isUnsigned(lhs_ty);
        const actual_op = if (unsigned) unsignedCmpOp(op_str) else op_str;
        try f.emitNewline();
        try f.emitFmt("(var {s} bool ({s} {s} {s}))", .{ name, actual_op, lhs, rhs });
    }

    fn unsignedCmpOp(op: []const u8) []const u8 {
        if (std.mem.eql(u8, op, "<")) return "ult";
        if (std.mem.eql(u8, op, ">")) return "ugt";
        if (std.mem.eql(u8, op, "<=")) return "ule";
        if (std.mem.eql(u8, op, ">=")) return "uge";
        return op; // == and != are sign-agnostic
    }

    fn airUnaryOp(f: *Function, inst: Air.InstIndex, op_str: []const u8) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = data.un_op;
        const val = try f.resolveInst(operand);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} i64 ({s} {s}))", .{ name, op_str, val });
    }

    fn airNot(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = data.un_op;
        const val = try f.resolveInst(operand);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} bool (! {s}))", .{ name, val });
    }

    fn airAlloc(f: *Function, inst: Air.InstIndex) !void {
        const ty = f.typeOfInst(inst);
        const ty_str = try f.mapType(ty);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} {s})", .{ name, ty_str });
    }

    fn airLoad(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const ptr_operand = data.un_op;
        const ptr = try f.resolveInst(ptr_operand);
        const name = try f.nameForInst(inst);
        // In lang, loading from a var is just using the var name.
        // But if this is a real pointer deref, use *.
        // For now, emit the simple case: just alias the name.
        try f.value_map.put(inst, ptr);
        _ = name;
    }

    fn airStore(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const bin_op = data.bin_op;
        const ptr = try f.resolveInst(bin_op.lhs);
        const val = try f.resolveInst(bin_op.rhs);
        try f.emitNewline();
        try f.emitFmt("(assign {s} {s})", .{ ptr, val });
    }

    fn airCall(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const extra = f.air.extraData(Air.Call, data.pl_op.payload);
        const callee = try f.resolveInst(data.pl_op.operand);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} i64 (call {s}", .{ name, callee });
        for (extra.data.args_len) |arg_ref| {
            const arg = try f.resolveInst(arg_ref);
            try f.emitFmt(" {s}", .{arg});
        }
        try f.emit("))");
    }

    fn airCondBr(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const extra = f.air.extraData(Air.CondBr, data.pl_op.payload);
        const cond = try f.resolveInst(data.pl_op.operand);
        try f.emitNewline();
        try f.emitFmt("(if {s}", .{cond});
        f.indent += 1;
        // Then branch
        try f.emitNewline();
        try f.emit("(block");
        f.indent += 1;
        for (extra.data.then_body) |then_inst| {
            try f.genInst(then_inst);
        }
        f.indent -= 1;
        try f.emit(")");
        // Else branch
        try f.emitNewline();
        try f.emit("(block");
        f.indent += 1;
        for (extra.data.else_body) |else_inst| {
            try f.genInst(else_inst);
        }
        f.indent -= 1;
        try f.emit(")");
        f.indent -= 1;
        try f.emit(")");
    }

    fn airBlock(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const extra = f.air.extraData(Air.Block, data.ty_pl.payload);
        try f.emitNewline();
        try f.emit("(block");
        f.indent += 1;
        for (extra.data.body) |body_inst| {
            try f.genInst(body_inst);
        }
        f.indent -= 1;
        try f.emit(")");
    }

    fn airBr(f: *Function, inst: Air.InstIndex) !void {
        // Branch to block - in lang AST, control flow is structural,
        // so we emit a break with the target block's value if any.
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = data.br.operand;
        if (operand != .none) {
            const val = try f.resolveInst(operand);
            try f.emitNewline();
            try f.emitFmt("(break {s})", .{val});
        }
    }

    fn airLoop(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const extra = f.air.extraData(Air.Block, data.ty_pl.payload);
        try f.emitNewline();
        try f.emit("(while (bool true)");
        f.indent += 1;
        for (extra.data.body) |body_inst| {
            try f.genInst(body_inst);
        }
        f.indent -= 1;
        try f.emit(")");
    }

    fn airSwitchBr(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = try f.resolveInst(data.pl_op.operand);
        try f.emitNewline();
        try f.emitFmt("(match {s}", .{operand});
        // Switch branches are complex - for now emit a placeholder
        // Full implementation will extract case values and bodies from extra data
        try f.emit(" ;; TODO: switch cases)");
    }

    fn airIntCast(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = data.un_op;
        const val = try f.resolveInst(operand);
        const dest_ty = f.typeOfInst(inst);
        const ty_str = try f.mapType(dest_ty);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} {s} (cast (type_base {s}) {s}))", .{ name, ty_str, ty_str, val });
    }

    fn airBitcast(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const operand = data.un_op;
        const val = try f.resolveInst(operand);
        const dest_ty = f.typeOfInst(inst);
        const ty_str = try f.mapType(dest_ty);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} {s} (bitcast (type_base {s}) {s}))", .{ name, ty_str, ty_str, val });
    }

    fn airTrunc(f: *Function, inst: Air.InstIndex) !void {
        // Truncation is just a cast to a smaller type
        return f.airIntCast(inst);
    }

    fn airStructFieldPtr(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const extra = f.air.extraData(Air.StructField, data.ty_pl.payload);
        const base = try f.resolveInst(extra.data.struct_operand);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} *u8 (field_ptr {s} {d}))", .{ name, base, extra.data.field_index });
    }

    fn airStructFieldVal(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const extra = f.air.extraData(Air.StructField, data.ty_pl.payload);
        const base = try f.resolveInst(extra.data.struct_operand);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} i64 (field {s} {d}))", .{ name, base, extra.data.field_index });
    }

    fn airPtrAdd(f: *Function, inst: Air.InstIndex) !void {
        const data = f.air.instructions.items(.data)[@intFromEnum(inst)];
        const bin_op = data.bin_op;
        const ptr = try f.resolveInst(bin_op.lhs);
        const offset = try f.resolveInst(bin_op.rhs);
        const name = try f.nameForInst(inst);
        try f.emitNewline();
        try f.emitFmt("(var {s} *u8 (+ {s} {s}))", .{ name, ptr, offset });
    }

    fn airUnreachable(f: *Function) !void {
        try f.emitNewline();
        try f.emit("(call os_exit 1)");
    }

    fn airDbgStmt(f: *Function) !void {
        // Debug statements are skipped - no output
        _ = f;
    }

    // -----------------------------------------------------------------
    // Main instruction dispatch
    // -----------------------------------------------------------------

    fn genInst(f: *Function, inst: Air.InstIndex) !void {
        const tags = f.air.instructions.items(.tag);
        const tag = tags[@intFromEnum(inst)];
        switch (tag) {
            // Priority 1: Core operations
            .arg => try f.airArg(inst),
            .ret => try f.airRet(inst),
            .ret_node => try f.airRet(inst),
            .ret_safe => try f.airRet(inst),
            .ret_load => try f.airRet(inst),
            .@"unreachable" => try f.airUnreachable(),

            // Arithmetic
            .add, .add_wrap, .add_sat, .add_optimized => try f.airBinOp(inst, "+"),
            .sub, .sub_wrap, .sub_sat, .sub_optimized => try f.airBinOp(inst, "-"),
            .mul, .mul_wrap, .mul_sat, .mul_optimized => try f.airBinOp(inst, "*"),
            .div_trunc, .div_exact, .div_floor => try f.airBinOp(inst, "/"),
            .rem, .mod => try f.airBinOp(inst, "%"),

            // Bitwise
            .bit_and => try f.airBinOp(inst, "&"),
            .bit_or => try f.airBinOp(inst, "|"),
            .xor => try f.airBinOp(inst, "^"),
            .shl, .shl_exact, .shl_sat => try f.airBinOp(inst, "<<"),
            .shr, .shr_exact => try f.airBinOp(inst, ">>"),

            // Comparisons
            .cmp_eq => try f.airCmpOp(inst, "=="),
            .cmp_neq => try f.airCmpOp(inst, "!="),
            .cmp_lt, .cmp_lt_optimized => try f.airCmpOp(inst, "<"),
            .cmp_gt, .cmp_gt_optimized => try f.airCmpOp(inst, ">"),
            .cmp_lte, .cmp_lte_optimized => try f.airCmpOp(inst, "<="),
            .cmp_gte, .cmp_gte_optimized => try f.airCmpOp(inst, ">="),

            // Unary
            .not => try f.airNot(inst),
            .negate, .negate_optimized => try f.airUnaryOp(inst, "-"),

            // Memory
            .alloc => try f.airAlloc(inst),
            .load => try f.airLoad(inst),
            .store => try f.airStore(inst),

            // Function calls
            .call, .call_always_tail, .call_never_tail, .call_never_inline => try f.airCall(inst),

            // Control flow
            .cond_br => try f.airCondBr(inst),
            .block => try f.airBlock(inst),
            .br => try f.airBr(inst),
            .loop => try f.airLoop(inst),
            .switch_br => try f.airSwitchBr(inst),

            // Priority 2: Type conversions
            .intcast, .trunc => try f.airIntCast(inst),
            .bitcast => try f.airBitcast(inst),

            // Priority 3: Memory and structs
            .struct_field_ptr, .struct_field_ptr_index_0, .struct_field_ptr_index_1, .struct_field_ptr_index_2, .struct_field_ptr_index_3 => try f.airStructFieldPtr(inst),
            .struct_field_val => try f.airStructFieldVal(inst),
            .ptr_add => try f.airPtrAdd(inst),

            // Debug (skip)
            .dbg_stmt => try f.airDbgStmt(),
            .dbg_var_val => {},
            .dbg_var_ptr => {},
            .dbg_inline_block => try f.airBlock(inst),
            .dbg_arg_inline => {},

            // Void return
            .ret_implicit => try f.airRetVoid(),

            // Unimplemented - emit comment
            else => {
                try f.emitNewline();
                try f.emitFmt(";; TODO: unhandled AIR tag {d}", .{@intFromEnum(tag)});
            },
        }
    }
};

// =====================================================================
// Public entry point - called by Zig's codegen pipeline
// =====================================================================

pub fn generate(
    lf: *link.File,
    pt: Zcu.PerThread,
    src_loc: Zcu.LazySrcLoc,
    func_index: InternPool.Index,
    air: Air,
    liveness: Liveness,
) CodegenError!Mir {
    _ = lf;
    _ = src_loc;
    _ = liveness;

    const zcu = pt.zcu;
    const gpa = zcu.gpa;
    const ip = &zcu.intern_pool;

    var f = Function.init(gpa, air, zcu);
    defer f.deinit();

    // Get function name
    const func_name = ip.getNav(ip.funcDeclInfo(func_index).owner_nav).name.toSlice(ip);

    // Get function type info
    const func_ty = ip.indexToKey(ip.typeOf(func_index)).func_type;
    const ret_ty_idx = func_ty.return_type;
    const ret_ty = Type.fromInterned(ret_ty_idx);
    const ret_ty_str = try f.mapType(ret_ty);

    // Emit function header: (func name ((param1 type1) ...) ret_type
    try f.emit("(func ");
    try f.emit(func_name);
    try f.emit(" (");

    // Emit parameters
    const param_types = func_ty.param_types.get(ip);
    for (param_types, 0..) |param_ty_idx, i| {
        if (i > 0) try f.emit(" ");
        const param_ty = Type.fromInterned(param_ty_idx);
        const pty_str = try f.mapType(param_ty);
        const param_name = try f.allocName("arg{d}", .{i});
        try f.emitFmt("(param {s} (type_base {s}))", .{ param_name, pty_str });

        // Pre-register arg instructions with their names.
        // AIR arg instructions appear in order at the start of the body.
        // We'll map them as we encounter them.
    }

    try f.emitFmt(") (type_base {s})", .{ret_ty_str});
    f.indent += 1;

    // Map arg instructions to parameter names
    var arg_idx: usize = 0;
    const tags = air.instructions.items(.tag);
    for (tags, 0..) |tag, i| {
        if (tag == .arg) {
            const arg_name = try f.allocName("arg{d}", .{arg_idx});
            try f.value_map.put(@enumFromInt(i), arg_name);
            arg_idx += 1;
        }
    }

    // Generate body
    const main_body = air.getMainBody();
    for (main_body) |inst| {
        try f.genInst(inst);
    }

    f.indent -= 1;
    try f.emit(")");
    try f.emitByte('\n');

    // Transfer ownership of the output buffer
    const code = try f.output.toOwnedSlice();
    return Mir{ .code = code };
}

pub const CodegenError = Allocator.Error || error{
    CodegenFail,
};
