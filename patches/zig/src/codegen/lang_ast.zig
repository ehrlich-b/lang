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
    aggregate_elements: std.AutoHashMapUnmanaged(u32, []const Inst.Ref),
    extern_decls: std.ArrayListUnmanaged(u8),
    extern_seen: std.StringHashMapUnmanaged(void),
    names: std.ArrayListUnmanaged([]const u8),
    next_temp: u32,
    current_loop_inst: ?u32 = null,

    fn init(air: *const Air, ip: *const InternPool) Function {
        return .{
            .gpa = undefined, // set by caller
            .air = air,
            .ip = ip,
            .out = .empty,
            .indent = 0,
            .value_map = .empty,
            .aggregate_elements = .empty,
            .extern_decls = .empty,
            .extern_seen = .empty,
            .names = .empty,
            .next_temp = 0,
        };
    }

    fn deinit(f: *Function) void {
        for (f.names.items) |n| f.gpa.free(n);
        f.names.deinit(f.gpa);
        var it = f.aggregate_elements.valueIterator();
        while (it.next()) |v| f.gpa.free(v.*);
        f.aggregate_elements.deinit(f.gpa);
        f.extern_decls.deinit(f.gpa);
        f.extern_seen.deinit(f.gpa);
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
            .enum_tag => |et| return f.resolve_const(et.int),
            .undef => return "0",
            .ptr => |ptr| return f.resolve_ptr_const(ptr, false),
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
            .enum_tag => |et| return f.resolve_const_expr(et.int),
            .undef => return "(number 0)",
            .ptr => |ptr| return f.resolve_ptr_const(ptr, true),
            else => return "(number 0)",
        }
    }

    /// Resolve a pointer constant. For string literals (uav -> aggregate -> bytes),
    /// emit (string "content"). For everything else, emit nil/0.
    fn resolve_ptr_const(f: *Function, ptr: InternPool.Key.Ptr, as_expr: bool) Error![]const u8 {
        switch (ptr.base_addr) {
            .uav => |uav| {
                const uav_key = f.ip.indexToKey(uav.val);
                switch (uav_key) {
                    .aggregate => |agg| {
                        const arr_key = f.ip.indexToKey(agg.ty);
                        switch (arr_key) {
                            .array_type => |at| {
                                switch (agg.storage) {
                                    .bytes => |str| {
                                        const bytes = str.toSlice(at.len, f.ip);
                                        return f.emit_string_literal(bytes);
                                    },
                                    else => {},
                                }
                            },
                            else => {},
                        }
                    },
                    else => {},
                }
            },
            else => {},
        }
        return if (as_expr) "(number 0)" else "nil";
    }

    /// Emit a (string "...") expression with proper escaping
    fn emit_string_literal(f: *Function, bytes: []const u8) Error![]const u8 {
        // Build escaped string for the AST
        var buf = std.ArrayListUnmanaged(u8).empty;
        try buf.appendSlice(f.gpa, "(string \"");
        for (bytes) |c| {
            switch (c) {
                '\n' => try buf.appendSlice(f.gpa, "\\n"),
                '\r' => try buf.appendSlice(f.gpa, "\\r"),
                '\t' => try buf.appendSlice(f.gpa, "\\t"),
                '\\' => try buf.appendSlice(f.gpa, "\\\\"),
                '"' => try buf.appendSlice(f.gpa, "\\\""),
                0 => try buf.appendSlice(f.gpa, "\\0"),
                else => if (c >= 32 and c < 127) {
                    try buf.append(f.gpa, c);
                } else {
                    try buf.writer(f.gpa).print("\\x{x:0>2}", .{c});
                },
            }
        }
        try buf.appendSlice(f.gpa, "\")");
        const result = try buf.toOwnedSlice(f.gpa);
        try f.names.append(f.gpa, result);
        return result;
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
        // alloc returns a pointer; we want the pointee type for the var declaration
        const ptr_ty = f.type_of_inst(inst);
        const key = f.ip.indexToKey(ptr_ty.toIntern());
        const ty = switch (key) {
            .ptr_type => |pt| try f.type_expr(Type.fromInterned(pt.child)),
            else => try f.type_expr(ptr_ty),
        };
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
        // Check if callee is extern and record declaration
        if (pl_op.operand.toInterned()) |ip_idx| {
            const callee_key = f.ip.indexToKey(ip_idx);
            if (callee_key == .@"extern") {
                try f.recordExtern(callee_key.@"extern");
            }
        }
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

    fn recordExtern(f: *Function, ext: InternPool.Key.Extern) Error!void {
        const nav = f.ip.getNav(ext.owner_nav);
        const name = nav.name.toSlice(f.ip);
        if (f.extern_seen.contains(name)) return;
        try f.extern_seen.put(f.gpa, name, {});

        const w = f.extern_decls.writer(f.gpa);
        // Get function type from the extern's type
        if (f.ip.indexToFuncType(ext.ty)) |func_ty| {
            try w.print("(extern_func {s} (", .{name});
            const param_types = func_ty.param_types.get(f.ip);
            for (param_types, 0..) |pty_idx, i| {
                if (i > 0) try w.writeAll(" ");
                const pty = Type.fromInterned(pty_idx);
                const ps = f.map_type(pty);
                try w.print("(param p{d} (type_base {s}))", .{ i, ps });
            }
            const ret_ty = Type.fromInterned(func_ty.return_type);
            const ret_str = f.map_type(ret_ty);
            try w.print(") (type_base {s}))\n", .{ret_str});
        }
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
        // If block produces a non-void value, pre-declare a result variable
        const block_ty = f.type_of_inst(inst);
        const is_void = blk: {
            const key = f.ip.indexToKey(block_ty.toIntern());
            break :blk switch (key) {
                .simple_type => |st| st == .void or st == .noreturn,
                else => false,
            };
        };
        if (is_void) {
            try f.nl();
            try f.append("(block");
            f.indent += 1;
            for (body) |bi| try f.gen_inst(@intFromEnum(bi));
            f.indent -= 1;
            try f.append(")");
        } else {
            const name = try f.inst_name(inst);
            const ty = try f.type_expr(block_ty);
            try f.nl();
            try f.print("(var {s} {s} (number 0))", .{ name, ty });
            try f.nl();
            try f.append("(block");
            f.indent += 1;
            for (body) |bi| try f.gen_inst(@intFromEnum(bi));
            f.indent -= 1;
            try f.append(")");
        }
    }

    fn airBr(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const target = @intFromEnum(data.br.block_inst);
        const operand = data.br.operand;
        // If br carries a value to a non-void block, assign it
        if (operand != .none) {
            const target_ty = f.type_of_inst(target);
            const target_key = f.ip.indexToKey(target_ty.toIntern());
            const target_is_void = switch (target_key) {
                .simple_type => |st| st == .void or st == .noreturn,
                else => false,
            };
            if (!target_is_void) {
                const block_name = try f.inst_name(target);
                const val = try f.resolve_expr(operand);
                try f.nl();
                try f.print("(assign (ident {s}) {s})", .{ block_name, val });
            }
        }
        // Inside a loop: br to a block inside the loop body = continue (omit),
        // br to the loop itself or an outer block = break
        if (f.current_loop_inst) |loop_inst| {
            if (target > loop_inst) {
                // Target block is inside the loop → block-local break, loop continues
                return;
            }
            // Target is the loop or outside → exit the loop
            try f.nl();
            try f.append("(break)");
            return;
        }
        // Not inside a loop — block-local break, omit
    }

    fn airLoop(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const extra = f.air.extraData(Air.Block, data.ty_pl.payload);
        const body: []const Inst.Index = @ptrCast(
            f.air.extra.items[extra.end..][0..extra.data.body_len],
        );
        const saved_loop = f.current_loop_inst;
        f.current_loop_inst = inst;
        defer f.current_loop_inst = saved_loop;
        try f.nl();
        try f.append("(while (number 1)");
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
        // If base was aggregate_init, resolve directly to the element
        if (extra.struct_operand.toIndex()) |base_idx| {
            if (f.aggregate_elements.get(@intFromEnum(base_idx))) |elements| {
                if (extra.field_index < elements.len) {
                    const val = try f.resolve(elements[extra.field_index]);
                    try f.value_map.put(f.gpa, inst, val);
                    return;
                }
            }
        }
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

    fn airSwitchBr(f: *Function, inst: u32) Error!void {
        const sw = f.air.unwrapSwitch(@enumFromInt(inst));
        const cond = try f.resolve_expr(sw.operand);
        var it = sw.iterateCases();
        var depth: u32 = 0;
        while (it.next()) |case| {
            // Build condition: (binop == cond item0) or chain with ||
            // For simplicity, handle single-item cases (most common for enums)
            if (case.items.len == 1 and case.ranges.len == 0) {
                const item_val = try f.resolve_expr(case.items[0]);
                try f.nl();
                try f.print("(if (binop == {s} {s})", .{ cond, item_val });
                f.indent += 1;
                try f.nl();
                try f.append("(block");
                f.indent += 1;
                for (case.body) |bi| try f.gen_inst(@intFromEnum(bi));
                f.indent -= 1;
                try f.append(")");
                f.indent -= 1;
                depth += 1;
            } else {
                // Multi-item or range case: emit first item for now
                if (case.items.len > 0) {
                    const item_val = try f.resolve_expr(case.items[0]);
                    try f.nl();
                    try f.print("(if (binop == {s} {s})", .{ cond, item_val });
                    f.indent += 1;
                    try f.nl();
                    try f.append("(block");
                    f.indent += 1;
                    for (case.body) |bi| try f.gen_inst(@intFromEnum(bi));
                    f.indent -= 1;
                    try f.append(")");
                    f.indent -= 1;
                    depth += 1;
                }
            }
        }
        // Else branch
        const else_body = it.elseBody();
        if (else_body.len > 0) {
            try f.nl();
            try f.append("(block");
            f.indent += 1;
            for (else_body) |bi| try f.gen_inst(@intFromEnum(bi));
            f.indent -= 1;
            try f.append(")");
        }
        // Close all the if-else chains
        for (0..depth) |_| try f.append(")");
    }

    fn airAggregateInit(f: *Function, inst: u32) Error!void {
        const data = f.air.instructions.items(.data)[inst];
        const inst_ty = f.type_of_inst(inst);
        const len: usize = @intCast(f.ip.aggregateTypeLen(inst_ty.toIntern()));
        const elements: []const Inst.Ref = @ptrCast(
            f.air.extra.items[data.ty_pl.payload..][0..len],
        );
        // Store elements so struct_field_val can resolve directly
        const copy = try f.gpa.dupe(Inst.Ref, elements);
        try f.aggregate_elements.put(f.gpa, inst, copy);
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
            .switch_br, .loop_switch_br => try f.airSwitchBr(inst),

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
            .aggregate_init => try f.airAggregateInit(inst),
            .ptr_add => try f.airPtrAdd(inst),

            // loop control
            .repeat => {}, // implicit in lang's while loops

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

    // Prepend extern declarations if any
    if (f.extern_decls.items.len > 0) {
        var result = std.ArrayListUnmanaged(u8).empty;
        try result.appendSlice(f.gpa, f.extern_decls.items);
        try result.appendSlice(f.gpa, "\n");
        try result.appendSlice(f.gpa, f.out.items);
        f.out.deinit(f.gpa);
        f.out = result;
    }

    return f.out.toOwnedSlice(f.gpa);
}
