// lang_ast.zig - AIR→lang AST S-expression emitter
//
// Piggybacks on the C backend: c.zig calls generateLangAst() when LANG_AST
// env var is set, and wraps our []u8 output in its Mir struct.
//
// Output format matches lang kernel's S-expression AST:
//   (func name ((param p1 (type_base i64))) (type_base i64) (block ...))

const std = @import("std");
const Allocator = std.mem.Allocator;
const Air = @import("../Air.zig");
const Zcu = @import("../Zcu.zig");
const InternPool = @import("../InternPool.zig");
const Type = @import("../Type.zig");

const Inst = Air.Inst;

const Error = std.mem.Allocator.Error;

const Function = struct {
    gpa: Allocator,
    air: *const Air,
    ip: *const InternPool,
    out: std.ArrayListUnmanaged(u8),
    indent: u32,
    value_map: std.AutoHashMapUnmanaged(u32, []const u8),
    names: std.ArrayListUnmanaged([]const u8),
    next_temp: u32,

    fn init(air: *const Air, ip: *const InternPool) Function {
        return .{
            .gpa = undefined, // set by caller
            .air = air,
            .ip = ip,
            .out = .empty,
            .indent = 0,
            .value_map = .empty,
            .names = .empty,
            .next_temp = 0,
        };
    }

    fn deinit(f: *Function) void {
        for (f.names.items) |n| f.gpa.free(n);
        f.names.deinit(f.gpa);
        f.value_map.deinit(f.gpa);
        // don't free f.out — caller takes ownership via toOwnedSlice
    }

    // -- output helpers --

    fn print(f: *Function, comptime fmt: []const u8, args: anytype) Error!void {
        try f.out.writer(f.gpa).print(fmt, args);
    }

    fn append(f: *Function, s: []const u8) Error!void {
        try f.out.appendSlice(f.gpa, s);
    }

    fn nl(f: *Function) Error!void {
        try f.out.append(f.gpa, '\n');
        for (0..f.indent) |_| try f.out.appendSlice(f.gpa, "  ");
    }

    // -- name management --

    fn alloc_name(f: *Function, comptime fmt: []const u8, args: anytype) Error![]const u8 {
        const name = try std.fmt.allocPrint(f.gpa, fmt, args);
        try f.names.append(f.gpa, name);
        return name;
    }

    fn temp(f: *Function) Error![]const u8 {
        const n = f.next_temp;
        f.next_temp += 1;
        return f.alloc_name("t{d}", .{n});
    }

    fn inst_name(f: *Function, inst: u32) Error![]const u8 {
        if (f.value_map.get(inst)) |n| return n;
        const n = try f.temp();
        try f.value_map.put(f.gpa, inst, n);
        return n;
    }

    // -- type mapping --

    fn map_type(f: *Function, ty: Type) []const u8 {
        const key = f.ip.indexToKey(ty.toIntern());
        switch (key) {
            .int_type => |info| return map_int(info.bits, info.signedness),
            .ptr_type => return "*u8",
            .simple_type => |st| return switch (st) {
                .void => "void",
                .bool => "bool",
                .usize => "u64",
                .isize => "i64",
                .f32 => "f32",
                .f64 => "f64",
                .noreturn => "void",
                .comptime_int => "i64",
                .comptime_float => "f64",
                else => "i64",
            },
            else => return "i64",
        }
    }

    fn map_int(bits: u16, signedness: std.builtin.Signedness) []const u8 {
        const s = signedness == .signed;
        if (bits <= 8) return if (s) "i8" else "u8";
        if (bits <= 16) return if (s) "i16" else "u16";
        if (bits <= 32) return if (s) "i32" else "u32";
        if (bits <= 64) return if (s) "i64" else "u64";
        if (bits <= 128) return if (s) "i128" else "u128";
        return "i64";
    }

    fn is_unsigned(f: *Function, ty: Type) bool {
        const key = f.ip.indexToKey(ty.toIntern());
        switch (key) {
            .int_type => |info| return info.signedness == .unsigned,
            .ptr_type => return true,
            .simple_type => |st| return switch (st) {
                .usize, .bool => true,
                else => false,
            },
            else => return false,
        }
    }

    // -- operand resolution --

    /// Resolve a ref to a bare name (for bindings, aliasing)
    fn resolve(f: *Function, ref: Inst.Ref) Error![]const u8 {
        if (ref.toIndex()) |idx| {
            return f.inst_name(@intFromEnum(idx));
        }
        if (ref.toInterned()) |ip_idx| {
            return f.resolve_const(ip_idx);
        }
        return "0";
    }

    /// Resolve a ref to an expression: (ident name) or (number N)
    fn resolve_expr(f: *Function, ref: Inst.Ref) Error![]const u8 {
        if (ref.toIndex()) |idx| {
            const name = try f.inst_name(@intFromEnum(idx));
            return f.alloc_name("(ident {s})", .{name});
        }
        if (ref.toInterned()) |ip_idx| {
            return f.resolve_const_expr(ip_idx);
        }
        return "(number 0)";
    }

    fn resolve_const(f: *Function, idx: InternPool.Index) Error![]const u8 {
        const key = f.ip.indexToKey(idx);
        switch (key) {
            .int => |int_val| {
                switch (int_val.storage) {
                    .u64 => |v| return f.alloc_name("{d}", .{v}),
                    .i64 => |v| return f.alloc_name("{d}", .{v}),
                    .big_int => return "0",
                    .lazy_align, .lazy_size => return "0",
                }
            },
            .float => |float_val| {
                switch (float_val.storage) {
                    .f32 => |v| return f.alloc_name("{d:.6}", .{v}),
                    .f64 => |v| return f.alloc_name("{d:.6}", .{v}),
                    else => return "0.0",
                }
            },
            .func => |func_val| {
                const nav = f.ip.getNav(func_val.owner_nav);
                return nav.name.toSlice(f.ip);
            },
            .@"extern" => |ext_val| {
                const nav = f.ip.getNav(ext_val.owner_nav);
                return nav.name.toSlice(f.ip);
            },
            .undef => return "0",
            .ptr => return "nil",
            else => return "0",
        }
    }

    fn resolve_const_expr(f: *Function, idx: InternPool.Index) Error![]const u8 {
        const key = f.ip.indexToKey(idx);
        switch (key) {
            .int => |int_val| {
                switch (int_val.storage) {
                    .u64 => |v| return f.alloc_name("(number {d})", .{v}),
                    .i64 => |v| return f.alloc_name("(number {d})", .{v}),
                    .big_int => return "(number 0)",
                    .lazy_align, .lazy_size => return "(number 0)",
                }
            },
            .float => |float_val| {
                switch (float_val.storage) {
                    .f32 => |v| return f.alloc_name("(number {d:.6})", .{v}),
                    .f64 => |v| return f.alloc_name("(number {d:.6})", .{v}),
                    else => return "(number 0)",
                }
            },
            .func => |func_val| {
                const nav = f.ip.getNav(func_val.owner_nav);
                return nav.name.toSlice(f.ip);
            },
            .@"extern" => |ext_val| {
                const nav = f.ip.getNav(ext_val.owner_nav);
                return nav.name.toSlice(f.ip);
            },
            .undef => return "(number 0)",
            .ptr => return "nil",
            else => return "(number 0)",
        }
    }

    fn type_expr(f: *Function, ty: Type) Error![]const u8 {
        const base = f.map_type(ty);
        return f.alloc_name("(type_base {s})", .{base});
    }

    fn type_of_ref(f: *Function, ref: Inst.Ref) Type {
        return f.air.typeOf(ref, f.ip);
    }

    fn type_of_inst(f: *Function, inst: u32) Type {
        return f.air.typeOfIndex(@enumFromInt(inst), f.ip);
    }

    // -- instruction handlers --

    fn airRet(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const operand = data.un_op;
        try f.nl();
        if (operand == .none) {
            try f.append("(return)");
        } else {
            const val = try f.resolve_expr(operand);
            try f.print("(return {s})", .{val});
        }
    }

    fn airRetVoid(f: *Function) Error!void {
        try f.nl();
        try f.append("(return)");
    }

    fn airBinOp(f: *Function, inst: u32, op: []const u8) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const lhs = try f.resolve_expr(data.bin_op.lhs);
        const rhs = try f.resolve_expr(data.bin_op.rhs);
        const name = try f.inst_name(inst);
        const ty = try f.type_expr(f.type_of_inst(inst));
        try f.nl();
        try f.print("(var {s} {s} (binop {s} {s} {s}))", .{ name, ty, op, lhs, rhs });
    }

    fn airCmpOp(f: *Function, inst: u32, op: []const u8) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const lhs = try f.resolve_expr(data.bin_op.lhs);
        const rhs = try f.resolve_expr(data.bin_op.rhs);
        const name = try f.inst_name(inst);
        const lhs_ty = f.type_of_ref(data.bin_op.lhs);
        const actual_op = if (f.is_unsigned(lhs_ty)) unsigned_cmp(op) else op;
        try f.nl();
        try f.print("(var {s} (type_base bool) (binop {s} {s} {s}))", .{ name, actual_op, lhs, rhs });
    }

    fn unsigned_cmp(op: []const u8) []const u8 {
        if (std.mem.eql(u8, op, "<")) return "ult";
        if (std.mem.eql(u8, op, ">")) return "ugt";
        if (std.mem.eql(u8, op, "<=")) return "ule";
        if (std.mem.eql(u8, op, ">=")) return "uge";
        return op;
    }

    fn airNot(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const val = try f.resolve_expr(data.ty_op.operand);
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} (type_base bool) (unop ! {s}))", .{ name, val });
    }

    fn airUnaryOp(f: *Function, inst: u32, op: []const u8) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const val = try f.resolve_expr(data.un_op);
        const name = try f.inst_name(inst);
        const ty = try f.type_expr(f.type_of_inst(inst));
        try f.nl();
        try f.print("(var {s} {s} (unop {s} {s}))", .{ name, ty, op, val });
    }

    fn airAlloc(f: *Function, inst: u32) Error!void {
        const ty = try f.type_expr(f.type_of_inst(inst));
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} {s} (number 0))", .{ name, ty });
    }

    fn airLoad(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const ptr = try f.resolve(data.ty_op.operand);
        // Alias: loading from a var is just using the var name
        try f.value_map.put(f.gpa, inst, ptr);
    }

    fn airStore(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const ptr = try f.resolve(data.bin_op.lhs);
        const val = try f.resolve_expr(data.bin_op.rhs);
        try f.nl();
        try f.print("(assign (ident {s}) {s})", .{ ptr, val });
    }

    fn airCall(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const pl_op = data.pl_op;
        const extra = f.air.extraData(Air.Call, pl_op.payload);
        const args: []const Inst.Ref = @ptrCast(
            f.air.extra.items[extra.end..][0..extra.data.args_len],
        );
        const callee = try f.resolve(pl_op.operand);
        const name = try f.inst_name(inst);
        const ty = try f.type_expr(f.type_of_inst(inst));
        try f.nl();
        try f.print("(var {s} {s} (call (ident {s})", .{ name, ty, callee });
        for (args) |arg_ref| {
            const arg = try f.resolve_expr(arg_ref);
            try f.print(" {s}", .{arg});
        }
        try f.append("))");
    }

    fn airCondBr(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const pl_op = data.pl_op;
        const extra = f.air.extraData(Air.CondBr, pl_op.payload);
        const cond = try f.resolve_expr(pl_op.operand);
        const then_body: []const Inst.Index = @ptrCast(
            f.air.extra.items[extra.end..][0..extra.data.then_body_len],
        );
        const else_body: []const Inst.Index = @ptrCast(
            f.air.extra.items[extra.end + extra.data.then_body_len ..][0..extra.data.else_body_len],
        );
        try f.nl();
        try f.print("(if {s}", .{cond});
        f.indent += 1;
        try f.nl();
        try f.append("(block");
        f.indent += 1;
        for (then_body) |bi| try f.gen_inst(@intFromEnum(bi));
        f.indent -= 1;
        try f.append(")");
        if (else_body.len > 0) {
            try f.nl();
            try f.append("(block");
            f.indent += 1;
            for (else_body) |bi| try f.gen_inst(@intFromEnum(bi));
            f.indent -= 1;
            try f.append(")");
        }
        f.indent -= 1;
        try f.append(")");
    }

    fn airBlock(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const extra = f.air.extraData(Air.Block, data.ty_pl.payload);
        const body: []const Inst.Index = @ptrCast(
            f.air.extra.items[extra.end..][0..extra.data.body_len],
        );
        try f.nl();
        try f.append("(block");
        f.indent += 1;
        for (body) |bi| try f.gen_inst(@intFromEnum(bi));
        f.indent -= 1;
        try f.append(")");
    }

    fn airBr(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const operand = data.br.operand;
        if (operand != .none) {
            const val = try f.resolve_expr(operand);
            try f.nl();
            try f.print("(break {s})", .{val});
        }
    }

    fn airLoop(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const extra = f.air.extraData(Air.Block, data.ty_pl.payload);
        const body: []const Inst.Index = @ptrCast(
            f.air.extra.items[extra.end..][0..extra.data.body_len],
        );
        try f.nl();
        try f.append("(while (bool true)");
        f.indent += 1;
        for (body) |bi| try f.gen_inst(@intFromEnum(bi));
        f.indent -= 1;
        try f.append(")");
    }

    fn airIntCast(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const val = try f.resolve_expr(data.ty_op.operand);
        const ty = try f.type_expr(f.type_of_inst(inst));
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} {s} (cast {s} {s}))", .{ name, ty, ty, val });
    }

    fn airBitcast(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const val = try f.resolve_expr(data.ty_op.operand);
        const ty = try f.type_expr(f.type_of_inst(inst));
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} {s} (bitcast {s} {s}))", .{ name, ty, ty, val });
    }

    fn airStructFieldPtr(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const extra = f.air.extraData(Air.StructField, data.ty_pl.payload).data;
        const base = try f.resolve_expr(extra.struct_operand);
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} (type_base *u8) (field_ptr {s} {d}))", .{ name, base, extra.field_index });
    }

    fn airStructFieldPtrIndex(f: *Function, inst: u32, index: u8) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const base = try f.resolve_expr(data.ty_op.operand);
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} (type_base *u8) (field_ptr {s} {d}))", .{ name, base, index });
    }

    fn airStructFieldVal(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const extra = f.air.extraData(Air.StructField, data.ty_pl.payload).data;
        const base = try f.resolve_expr(extra.struct_operand);
        const name = try f.inst_name(inst);
        const ty = try f.type_expr(f.type_of_inst(inst));
        try f.nl();
        try f.print("(var {s} {s} (field {s} {d}))", .{ name, ty, base, extra.field_index });
    }

    fn airPtrAdd(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const bin_op = f.air.extraData(Air.Bin, data.ty_pl.payload).data;
        const ptr = try f.resolve_expr(bin_op.lhs);
        const offset = try f.resolve_expr(bin_op.rhs);
        const name = try f.inst_name(inst);
        try f.nl();
        try f.print("(var {s} (type_base *u8) (binop + {s} {s}))", .{ name, ptr, offset });
    }

    fn airDbgInlineBlock(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const extra = f.air.extraData(Air.DbgInlineBlock, data.ty_pl.payload);
        const body: []const Inst.Index = @ptrCast(
            f.air.extra.items[extra.end..][0..extra.data.body_len],
        );
        for (body) |bi| try f.gen_inst(@intFromEnum(bi));
    }

    // -- main dispatch --

    fn gen_inst(f: *Function, inst: u32) Error!void {
        const tag = f.air.instructions.items(.tag)[inst];
        switch (tag) {
            .arg => {}, // handled in generate()
            .ret, .ret_safe, .ret_load => try f.airRet(inst),
            .unreach, .trap => {
                try f.nl();
                try f.append("(call os_exit 1)");
            },

            // arithmetic
            .add, .add_wrap, .add_sat, .add_safe => try f.airBinOp(inst, "+"),
            .sub, .sub_wrap, .sub_sat, .sub_safe => try f.airBinOp(inst, "-"),
            .mul, .mul_wrap, .mul_sat, .mul_safe => try f.airBinOp(inst, "*"),
            .div_trunc, .div_exact, .div_floor => try f.airBinOp(inst, "/"),
            .rem, .mod => try f.airBinOp(inst, "%"),

            // bitwise
            .bit_and => try f.airBinOp(inst, "&"),
            .bit_or => try f.airBinOp(inst, "|"),
            .xor => try f.airBinOp(inst, "^"),
            .shl, .shl_exact, .shl_sat => try f.airBinOp(inst, "<<"),
            .shr, .shr_exact => try f.airBinOp(inst, ">>"),

            // comparisons
            .cmp_eq => try f.airCmpOp(inst, "=="),
            .cmp_neq => try f.airCmpOp(inst, "!="),
            .cmp_lt, .cmp_lt_optimized => try f.airCmpOp(inst, "<"),
            .cmp_gt, .cmp_gt_optimized => try f.airCmpOp(inst, ">"),
            .cmp_lte, .cmp_lte_optimized => try f.airCmpOp(inst, "<="),
            .cmp_gte, .cmp_gte_optimized => try f.airCmpOp(inst, ">="),

            // unary
            .not => try f.airNot(inst),
            .neg, .neg_optimized => try f.airUnaryOp(inst, "-"),

            // memory
            .alloc => try f.airAlloc(inst),
            .load => try f.airLoad(inst),
            .store, .store_safe => try f.airStore(inst),

            // calls
            .call, .call_always_tail, .call_never_tail, .call_never_inline => try f.airCall(inst),

            // control flow
            .cond_br => try f.airCondBr(inst),
            .block => try f.airBlock(inst),
            .br => try f.airBr(inst),
            .loop => try f.airLoop(inst),

            // type conversions
            .intcast, .trunc => try f.airIntCast(inst),
            .bitcast => try f.airBitcast(inst),

            // structs
            .struct_field_ptr => try f.airStructFieldPtr(inst),
            .struct_field_ptr_index_0 => try f.airStructFieldPtrIndex(inst, 0),
            .struct_field_ptr_index_1 => try f.airStructFieldPtrIndex(inst, 1),
            .struct_field_ptr_index_2 => try f.airStructFieldPtrIndex(inst, 2),
            .struct_field_ptr_index_3 => try f.airStructFieldPtrIndex(inst, 3),
            .struct_field_val => try f.airStructFieldVal(inst),
            .ptr_add => try f.airPtrAdd(inst),

            // debug (skip)
            .dbg_stmt, .dbg_var_val, .dbg_var_ptr, .dbg_arg_inline, .dbg_empty_stmt => {},
            .dbg_inline_block => try f.airDbgInlineBlock(inst),

            // everything else: comment
            else => {
                try f.nl();
                try f.print(";; TODO: {s}", .{@tagName(tag)});
            },
        }
    }
};

/// Called from the patched c.zig generate() function.
/// Returns owned S-expression bytes for one function.
pub fn generateLangAst(
    gpa: Allocator,
    zcu: *const Zcu,
    func_index: InternPool.Index,
    air: *const Air,
) Error![]u8 {
    const ip = &zcu.intern_pool;
    var f = Function.init(air, ip);
    f.gpa = gpa;
    defer f.deinit();

    // function name
    const func = zcu.funcInfo(func_index);
    const name = ip.getNav(func.owner_nav).name.toSlice(ip);

    // function type
    const func_ty = ip.indexToFuncType(func.ty).?;
    const ret_ty = Type.fromInterned(func_ty.return_type);
    const ret_str = try f.type_expr(ret_ty);

    // header: (func name ((param arg0 (type_base i64)) ...) (type_base i64)
    try f.print("(func {s} (", .{name});
    const param_types = func_ty.param_types.get(ip);
    for (param_types, 0..) |pty_idx, i| {
        if (i > 0) try f.append(" ");
        const pty = Type.fromInterned(pty_idx);
        const ps = try f.type_expr(pty);
        const pname = try f.alloc_name("arg{d}", .{i});
        try f.print("(param {s} {s})", .{ pname, ps });
    }
    try f.print(") {s}", .{ret_str});
    f.indent += 1;

    // pre-register arg instructions
    var arg_idx: usize = 0;
    const tags = air.instructions.items(.tag);
    for (tags, 0..) |tag, i| {
        if (tag == .arg) {
            const arg_name = try f.alloc_name("arg{d}", .{arg_idx});
            try f.value_map.put(f.gpa, @intCast(i), arg_name);
            arg_idx += 1;
        }
    }

    // body: wrap in (block ...)
    try f.nl();
    try f.append("(block");
    f.indent += 1;
    const main_body = air.getMainBody();
    for (main_body) |inst| try f.gen_inst(@intFromEnum(inst));
    f.indent -= 1;
    try f.append(")");

    f.indent -= 1;
    try f.append(")\n");

    return f.out.toOwnedSlice(f.gpa);
}
