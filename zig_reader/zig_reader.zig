// zig_reader.zig — Minimal Zig reader for lang
//
// Reads a tiny subset of Zig and emits lang AST S-expressions to stdout.
// Designed to be capturable: no std imports, extern C only, wrapping arithmetic.
//
// Usage: zig_reader < input.zig > output.ast
//    or: pipe zig source on stdin, get AST on stdout

extern fn read(fd: c_int, buf: [*]u8, count: usize) isize;
extern fn write(fd: c_int, buf: [*]const u8, count: usize) isize;
extern fn malloc(size: usize) ?[*]u8;
extern fn exit(code: c_int) noreturn;

// ========== Output ==========

var out_buf: [1048576]u8 = undefined;
var out_pos: usize = 0;

fn emit(s: [*]const u8, len: usize) void {
    var i: usize = 0;
    while (i < len) : (i +%= 1) {
        if (out_pos < out_buf.len) {
            out_buf[out_pos] = s[i];
            out_pos +%= 1;
        }
    }
}

fn emit1(c: u8) void {
    if (out_pos < out_buf.len) {
        out_buf[out_pos] = c;
        out_pos +%= 1;
    }
}

fn emits(s: [*]const u8) void {
    var i: usize = 0;
    while (s[i] != 0) : (i +%= 1) {
        emit1(s[i]);
    }
}

fn emit_int(v: i64) void {
    if (v < 0) {
        emit1('-');
        emit_int(0 -% v);
        return;
    }
    if (v >= 10) {
        emit_int(@divTrunc(v, 10));
    }
    const digit: u8 = @intCast(@as(u64, @intCast(@rem(v, 10))));
    emit1(digit +% '0');
}

fn flush() void {
    if (out_pos > 0) {
        _ = write(1, &out_buf, out_pos);
        out_pos = 0;
    }
}

// ========== Scratch buffers for expression wrapping ==========
// When parsing binary expressions, we need to wrap left operand:
//   parse left → see op → emit "(binop + " left " " right ")"
// We capture left's output, then re-emit it wrapped.
//
// IMPORTANT: the lang emitter collapses every pointer to *u8 and does not
// scale GEP offsets or match store widths to element type. So only u8 arrays
// work correctly. save_pos and scratch_len hold usize values, which we encode
// as 4-byte little-endian in a flat u8 buffer.

const SCRATCH_SIZE: usize = 8192;
const MAX_SCRATCH: usize = 64; // recursive descent with nested @builtins can stack deep
const SCRATCH_TOTAL: usize = MAX_SCRATCH * SCRATCH_SIZE;

var scratch: [SCRATCH_TOTAL]u8 = undefined;
var scratch_len_buf: [MAX_SCRATCH * 4]u8 = undefined;
var save_pos_buf: [MAX_SCRATCH * 4]u8 = undefined;
var sd: usize = 0; // scratch depth

fn put4(buf: [*]u8, idx: usize, v: usize) void {
    const base = idx *% 4;
    buf[base] = @as(u8, @truncate(v));
    buf[base +% 1] = @as(u8, @truncate(v >> 8));
    buf[base +% 2] = @as(u8, @truncate(v >> 16));
    buf[base +% 3] = @as(u8, @truncate(v >> 24));
}

fn get4(buf: [*]const u8, idx: usize) usize {
    const base = idx *% 4;
    const b0: usize = buf[base];
    const b1: usize = buf[base +% 1];
    const b2: usize = buf[base +% 2];
    const b3: usize = buf[base +% 3];
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
}

fn cap_begin() void {
    put4(&save_pos_buf, sd, out_pos);
    sd +%= 1;
}

fn cap_end() usize {
    sd -%= 1;
    const sp = get4(&save_pos_buf, sd);
    const len = out_pos -% sp;
    const base = sd *% SCRATCH_SIZE;
    var i: usize = 0;
    while (i < len and i < SCRATCH_SIZE) : (i +%= 1) {
        scratch[base +% i] = out_buf[sp +% i];
    }
    put4(&scratch_len_buf, sd, len);
    out_pos = sp; // rewind
    return sd;
}

fn cap_emit(idx: usize) void {
    const base = idx *% SCRATCH_SIZE;
    const len = get4(&scratch_len_buf, idx);
    var i: usize = 0;
    while (i < len) : (i +%= 1) {
        emit1(scratch[base +% i]);
    }
}

// ========== Input ==========

var src: [*]u8 = undefined;
var src_len: usize = 0;
var pos: usize = 0;

fn peek() u8 {
    if (pos >= src_len) return 0;
    return src[pos];
}

fn at(offset: usize) u8 {
    const p = pos +% offset;
    if (p >= src_len) return 0;
    return src[p];
}

fn skip_ws() void {
    while (pos < src_len) {
        const c = src[pos];
        if (c == ' ' or c == '\t' or c == '\n' or c == '\r') {
            pos +%= 1;
        } else if (c == '/' and at(1) == '/') {
            pos +%= 2;
            while (pos < src_len and src[pos] != '\n') pos +%= 1;
        } else break;
    }
}

fn meq(a: [*]const u8, b: [*]const u8, len: usize) bool {
    var i: usize = 0;
    while (i < len) : (i +%= 1) {
        if (a[i] != b[i]) return false;
    }
    return true;
}

fn is_alpha(c: u8) bool {
    return (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or c == '_';
}

fn is_digit(c: u8) bool {
    return c >= '0' and c <= '9';
}

fn is_idc(c: u8) bool {
    return is_alpha(c) or is_digit(c);
}

// ========== Tokenizer ==========

const T_EOF: i64 = 0;
const T_IDENT: i64 = 1;
const T_INT: i64 = 2;
const T_STR: i64 = 3;
const T_FN: i64 = 10;
const T_RETURN: i64 = 11;
const T_VAR: i64 = 12;
const T_CONST: i64 = 13;
const T_WHILE: i64 = 14;
const T_IF: i64 = 15;
const T_ELSE: i64 = 16;
const T_EXPORT: i64 = 17;
const T_EXTERN: i64 = 18;
const T_TRUE: i64 = 19;
const T_FALSE: i64 = 20;
const T_AND: i64 = 21;
const T_OR: i64 = 22;
// Punctuation
const T_LPAREN: i64 = 30;
const T_RPAREN: i64 = 31;
const T_LBRACE: i64 = 32;
const T_RBRACE: i64 = 33;
const T_SEMI: i64 = 34;
const T_COMMA: i64 = 35;
const T_COLON: i64 = 36;
const T_DOT: i64 = 37;
const T_AT: i64 = 38;
const T_UNDER: i64 = 39; // _
const T_LBRACKET: i64 = 40; // [
const T_RBRACKET: i64 = 41; // ]
const T_QMARK: i64 = 42; // ?
// Operators
const T_EQ: i64 = 50;
const T_EQEQ: i64 = 51;
const T_NEQ: i64 = 52;
const T_LT: i64 = 53;
const T_GT: i64 = 54;
const T_LTE: i64 = 55;
const T_GTE: i64 = 56;
const T_PLUS: i64 = 57;
const T_MINUS: i64 = 58;
const T_STAR: i64 = 59;
const T_SLASH: i64 = 60;
const T_PCT: i64 = 61;
const T_PLUSW: i64 = 62;  // +%
const T_MINUSW: i64 = 63; // -%
const T_STARW: i64 = 64;  // *%
const T_PLUSEQ: i64 = 65; // +%=
const T_MINUSEQ: i64 = 66; // -%=
const T_STAREQ: i64 = 67; // *%=

var tt: i64 = 0;      // token type
var ts: usize = 0;    // token start
var tl: usize = 0;    // token length
var tv: i64 = 0;      // token int value

fn next() void {
    skip_ws();
    if (pos >= src_len) { tt = T_EOF; return; }

    ts = pos;
    const c = src[pos];

    // Single char
    if (c == '(') { pos +%= 1; tt = T_LPAREN; tl = 1; return; }
    if (c == ')') { pos +%= 1; tt = T_RPAREN; tl = 1; return; }
    if (c == '{') { pos +%= 1; tt = T_LBRACE; tl = 1; return; }
    if (c == '}') { pos +%= 1; tt = T_RBRACE; tl = 1; return; }
    if (c == ';') { pos +%= 1; tt = T_SEMI; tl = 1; return; }
    if (c == ',') { pos +%= 1; tt = T_COMMA; tl = 1; return; }
    if (c == ':') { pos +%= 1; tt = T_COLON; tl = 1; return; }
    if (c == '@') { pos +%= 1; tt = T_AT; tl = 1; return; }
    if (c == '.') { pos +%= 1; tt = T_DOT; tl = 1; return; }
    if (c == '[') { pos +%= 1; tt = T_LBRACKET; tl = 1; return; }
    if (c == ']') { pos +%= 1; tt = T_RBRACKET; tl = 1; return; }
    if (c == '?') { pos +%= 1; tt = T_QMARK; tl = 1; return; }

    // Two/three char ops
    if (c == '=' and at(1) == '=') { pos +%= 2; tt = T_EQEQ; tl = 2; return; }
    if (c == '=') { pos +%= 1; tt = T_EQ; tl = 1; return; }
    if (c == '!' and at(1) == '=') { pos +%= 2; tt = T_NEQ; tl = 2; return; }
    if (c == '<' and at(1) == '=') { pos +%= 2; tt = T_LTE; tl = 2; return; }
    if (c == '<') { pos +%= 1; tt = T_LT; tl = 1; return; }
    if (c == '>' and at(1) == '=') { pos +%= 2; tt = T_GTE; tl = 2; return; }
    if (c == '>') { pos +%= 1; tt = T_GT; tl = 1; return; }

    // Wrapping/compound ops
    if (c == '+' and at(1) == '%' and at(2) == '=') { pos +%= 3; tt = T_PLUSEQ; tl = 3; return; }
    if (c == '+' and at(1) == '%') { pos +%= 2; tt = T_PLUSW; tl = 2; return; }
    if (c == '-' and at(1) == '%' and at(2) == '=') { pos +%= 3; tt = T_MINUSEQ; tl = 3; return; }
    if (c == '-' and at(1) == '%') { pos +%= 2; tt = T_MINUSW; tl = 2; return; }
    if (c == '*' and at(1) == '%' and at(2) == '=') { pos +%= 3; tt = T_STAREQ; tl = 3; return; }
    if (c == '*' and at(1) == '%') { pos +%= 2; tt = T_STARW; tl = 2; return; }

    if (c == '+') { pos +%= 1; tt = T_PLUS; tl = 1; return; }
    if (c == '-') { pos +%= 1; tt = T_MINUS; tl = 1; return; }
    if (c == '*') { pos +%= 1; tt = T_STAR; tl = 1; return; }
    if (c == '/') { pos +%= 1; tt = T_SLASH; tl = 1; return; }
    if (c == '%') { pos +%= 1; tt = T_PCT; tl = 1; return; }

    // String
    if (c == '"') {
        pos +%= 1;
        ts = pos;
        while (pos < src_len and src[pos] != '"') {
            if (src[pos] == '\\') pos +%= 1;
            pos +%= 1;
        }
        tl = pos -% ts;
        if (pos < src_len) pos +%= 1;
        tt = T_STR;
        return;
    }

    // Number
    if (is_digit(c)) {
        var v: i64 = 0;
        while (pos < src_len and is_digit(src[pos])) {
            v = v *% 10 +% @as(i64, src[pos] -% '0');
            pos +%= 1;
        }
        tt = T_INT;
        tv = v;
        tl = pos -% ts;
        return;
    }

    // Ident / keyword
    if (is_alpha(c)) {
        while (pos < src_len and is_idc(src[pos])) pos +%= 1;
        tl = pos -% ts;
        // Keywords
        if (tl == 2 and src[ts] == 'f' and src[ts +% 1] == 'n') { tt = T_FN; return; }
        if (tl == 2 and src[ts] == 'i' and src[ts +% 1] == 'f') { tt = T_IF; return; }
        if (tl == 2 and src[ts] == 'o' and src[ts +% 1] == 'r') { tt = T_OR; return; }
        if (tl == 3 and meq(src + ts, "var", 3)) { tt = T_VAR; return; }
        if (tl == 3 and meq(src + ts, "and", 3)) { tt = T_AND; return; }
        if (tl == 4 and meq(src + ts, "else", 4)) { tt = T_ELSE; return; }
        if (tl == 4 and meq(src + ts, "true", 4)) { tt = T_TRUE; return; }
        if (tl == 5 and meq(src + ts, "const", 5)) { tt = T_CONST; return; }
        if (tl == 5 and meq(src + ts, "while", 5)) { tt = T_WHILE; return; }
        if (tl == 5 and meq(src + ts, "false", 5)) { tt = T_FALSE; return; }
        if (tl == 6 and meq(src + ts, "return", 6)) { tt = T_RETURN; return; }
        if (tl == 6 and meq(src + ts, "export", 6)) { tt = T_EXPORT; return; }
        if (tl == 6 and meq(src + ts, "extern", 6)) { tt = T_EXTERN; return; }
        if (tl == 1 and src[ts] == '_') { tt = T_UNDER; return; }
        tt = T_IDENT;
        return;
    }

    // Skip unknown
    pos +%= 1;
    next();
}

fn expect(t: i64) void {
    if (tt != t) return; // soft error
    next();
}

fn tok_name() [*]const u8 {
    return src + ts;
}

// ========== Parser ==========

fn parse_type() void {
    // Optional prefix: ?[*]u8, ?*u8
    if (tt == T_QMARK) {
        next();
        parse_type();
        return;
    }
    // Pointer types: [*]const u8, [*]u8, []u8, etc.
    if (tt == T_LBRACKET) {
        next(); // skip [
        // skip to ]
        while (tt != T_RBRACKET and tt != T_EOF) next();
        next(); // skip ]
        // skip 'const' if present
        if (tt == T_CONST) next();
        parse_type(); // element type
        return;
    }
    // *T, *const T
    if (tt == T_STAR) {
        next();
        if (tt == T_CONST) next();
        parse_type(); // element type
        return;
    }
    if (tt == T_IDENT) {
        const s = ts;
        const l = tl;
        next();
        if (l == 3 and meq(src + s, "i64", 3)) { emits("(type_base i64)"); return; }
        if (l == 3 and meq(src + s, "u64", 3)) { emits("(type_base u64)"); return; }
        if (l == 3 and meq(src + s, "i32", 3)) { emits("(type_base i32)"); return; }
        if (l == 3 and meq(src + s, "u32", 3)) { emits("(type_base u32)"); return; }
        if (l == 4 and meq(src + s, "bool", 4)) { emits("(type_base bool)"); return; }
        if (l == 4 and meq(src + s, "void", 4)) { emits("(type_base void)"); return; }
        if (l == 5 and meq(src + s, "c_int", 5)) { emits("(type_base i64)"); return; }
        if (l == 5 and meq(src + s, "usize", 5)) { emits("(type_base i64)"); return; }
        if (l == 5 and meq(src + s, "isize", 5)) { emits("(type_base i64)"); return; }
        emits("(type_base i64)");
        return;
    }
    emits("(type_base i64)");
    next();
}

fn p_primary() void {
    if (tt == T_INT) {
        emits("(number ");
        emit_int(tv);
        emit1(')');
        next();
        return;
    }
    if (tt == T_TRUE) { emits("(number 1)"); next(); return; }
    if (tt == T_FALSE) { emits("(number 0)"); next(); return; }

    if (tt == T_STR) {
        emits("(string \"");
        emit(src + ts, tl);
        emits("\")");
        next();
        // .ptr / .len
        if (tt == T_DOT) {
            next();
            if (tt == T_IDENT and tl == 3 and meq(src + ts, "len", 3)) {
                // Replace the string expr with its length
                // For now, we can't easily retroactively change. Just skip.
                next();
            } else if (tt == T_IDENT and tl == 3 and meq(src + ts, "ptr", 3)) {
                next();
            } else {
                next(); // skip unknown field
            }
        }
        return;
    }

    if (tt == T_LPAREN) {
        next();
        p_expr();
        expect(T_RPAREN);
        return;
    }

    if (tt == T_AT) {
        // Builtin: @rem, @as, @divTrunc, @intCast, @enumFromInt
        next();
        if (tt == T_IDENT) {
            const ns = ts;
            const nl = tl;
            next();
            expect(T_LPAREN);
            if (nl == 3 and meq(src + ns, "rem", 3)) {
                emits("(binop % ");
                p_expr();
                expect(T_COMMA);
                emit1(' ');
                p_expr();
                emit1(')');
            } else if (nl == 8 and meq(src + ns, "divTrunc", 8)) {
                emits("(binop / ");
                p_expr();
                expect(T_COMMA);
                emit1(' ');
                p_expr();
                emit1(')');
            } else if (nl == 2 and meq(src + ns, "as", 2)) {
                // @as(Type, val) → val
                // Skip type + comma
                parse_type();
                expect(T_COMMA);
                p_expr();
            } else if (nl == 7 and meq(src + ns, "intCast", 7)) {
                p_expr();
            } else if (nl == 11 and meq(src + ns, "enumFromInt", 11)) {
                p_expr();
            } else {
                // Unknown builtin — skip to matching paren
                var d: i64 = 1;
                while (d > 0 and tt != T_EOF) {
                    if (tt == T_LPAREN) d +%= 1;
                    if (tt == T_RPAREN) d -%= 1;
                    if (d > 0) next();
                }
                emits("(number 0)");
            }
            expect(T_RPAREN);
            return;
        }
        return;
    }

    if (tt == T_MINUS) {
        next();
        emits("(unop - ");
        p_primary();
        emit1(')');
        return;
    }

    if (tt == T_IDENT) {
        const ns = ts;
        const nl = tl;
        next();
        // undefined → 0
        if (nl == 9 and meq(src + ns, "undefined", 9)) {
            emits("(number 0)");
            return;
        }
        // Function call?
        if (tt == T_LPAREN) {
            next();
            emits("(call (ident ");
            emit(src + ns, nl);
            emit1(')');
            while (tt != T_RPAREN and tt != T_EOF) {
                emit1(' ');
                p_expr();
                if (tt == T_COMMA) next();
            }
            emit1(')');
            expect(T_RPAREN);
            return;
        }
        emits("(ident ");
        emit(src + ns, nl);
        emit1(')');
        return;
    }

    // Fallback
    emits("(number 0)");
    if (tt != T_EOF) next();
}

fn p_mul() void {
    cap_begin();
    p_primary();
    var ci = cap_end();

    while (tt == T_STAR or tt == T_SLASH or tt == T_PCT or tt == T_STARW) {
        const op = tt;
        next();
        cap_begin();
        emits("(binop ");
        if (op == T_STAR or op == T_STARW) emits("* ")
        else if (op == T_SLASH) emits("/ ")
        else emits("% ");
        cap_emit(ci);
        emit1(' ');
        p_primary();
        emit1(')');
        ci = cap_end();
    }
    cap_emit(ci);
}

fn p_add() void {
    cap_begin();
    p_mul();
    var ci = cap_end();

    while (tt == T_PLUS or tt == T_MINUS or tt == T_PLUSW or tt == T_MINUSW) {
        const op = tt;
        next();
        cap_begin();
        emits("(binop ");
        if (op == T_PLUS or op == T_PLUSW) emits("+ ")
        else emits("- ");
        cap_emit(ci);
        emit1(' ');
        p_mul();
        emit1(')');
        ci = cap_end();
    }
    cap_emit(ci);
}

fn p_cmp() void {
    cap_begin();
    p_add();
    const ci = cap_end();

    if (tt == T_EQEQ or tt == T_NEQ or tt == T_LT or tt == T_GT or tt == T_LTE or tt == T_GTE) {
        const op = tt;
        next();
        emits("(binop ");
        if (op == T_EQEQ) emits("== ")
        else if (op == T_NEQ) emits("!= ")
        else if (op == T_LT) emits("< ")
        else if (op == T_GT) emits("> ")
        else if (op == T_LTE) emits("<= ")
        else emits(">= ");
        cap_emit(ci);
        emit1(' ');
        p_add();
        emit1(')');
    } else {
        cap_emit(ci);
    }
}

fn p_and() void {
    cap_begin();
    p_cmp();
    var ci = cap_end();

    while (tt == T_AND) {
        next();
        cap_begin();
        emits("(binop && ");
        cap_emit(ci);
        emit1(' ');
        p_cmp();
        emit1(')');
        ci = cap_end();
    }
    cap_emit(ci);
}

fn p_or() void {
    cap_begin();
    p_and();
    var ci = cap_end();

    while (tt == T_OR) {
        next();
        cap_begin();
        emits("(binop || ");
        cap_emit(ci);
        emit1(' ');
        p_and();
        emit1(')');
        ci = cap_end();
    }
    cap_emit(ci);
}

fn p_expr() void {
    p_or();
}

// ========== Statement parser ==========

fn p_block() void {
    expect(T_LBRACE);
    emits("(block");
    while (tt != T_RBRACE and tt != T_EOF) {
        emit1('\n');
        emits("    ");
        p_stmt();
    }
    emit1(')');
    expect(T_RBRACE);
}

fn p_stmt() void {
    if (tt == T_RETURN) {
        next();
        if (tt == T_SEMI) {
            emits("(return)");
            next();
        } else {
            emits("(return ");
            p_expr();
            emit1(')');
            expect(T_SEMI);
        }
        return;
    }

    if (tt == T_VAR or tt == T_CONST) {
        next();
        const ns = ts;
        const nl = tl;
        expect(T_IDENT);
        expect(T_COLON);
        cap_begin();
        parse_type();
        const ti = cap_end();
        expect(T_EQ);
        emits("(var ");
        emit(src + ns, nl);
        emit1(' ');
        cap_emit(ti);
        emit1(' ');
        p_expr();
        emit1(')');
        expect(T_SEMI);
        return;
    }

    if (tt == T_WHILE) {
        next();
        expect(T_LPAREN);
        emits("(while ");
        p_expr();
        expect(T_RPAREN);
        emit1(' ');
        p_block();
        emit1(')');
        return;
    }

    if (tt == T_IF) {
        next();
        expect(T_LPAREN);
        emits("(if ");
        p_expr();
        expect(T_RPAREN);
        emit1(' ');
        if (tt == T_LBRACE) {
            p_block();
        } else {
            emits("(block ");
            p_stmt();
            emit1(')');
        }
        if (tt == T_ELSE) {
            next();
            emit1(' ');
            if (tt == T_IF) {
                emits("(block ");
                p_stmt(); // else if → wrapped
                emit1(')');
            } else {
                p_block();
            }
        }
        emit1(')');
        return;
    }

    if (tt == T_UNDER) {
        // _ = expr;  (discard)
        next();
        expect(T_EQ);
        emits("(expr_stmt ");
        p_expr();
        emit1(')');
        expect(T_SEMI);
        return;
    }

    if (tt == T_IDENT) {
        const ns = ts;
        const nl = tl;
        next();

        // Assignment
        if (tt == T_EQ) {
            next();
            emits("(assign (ident ");
            emit(src + ns, nl);
            emits(") ");
            p_expr();
            emit1(')');
            expect(T_SEMI);
            return;
        }

        // Compound assignment: +%= -%= *%=
        if (tt == T_PLUSEQ) {
            next();
            emits("(assign (ident ");
            emit(src + ns, nl);
            emits(") (binop + (ident ");
            emit(src + ns, nl);
            emits(") ");
            p_expr();
            emits("))");
            expect(T_SEMI);
            return;
        }
        if (tt == T_MINUSEQ) {
            next();
            emits("(assign (ident ");
            emit(src + ns, nl);
            emits(") (binop - (ident ");
            emit(src + ns, nl);
            emits(") ");
            p_expr();
            emits("))");
            expect(T_SEMI);
            return;
        }
        if (tt == T_STAREQ) {
            next();
            emits("(assign (ident ");
            emit(src + ns, nl);
            emits(") (binop * (ident ");
            emit(src + ns, nl);
            emits(") ");
            p_expr();
            emits("))");
            expect(T_SEMI);
            return;
        }

        // Function call as statement
        if (tt == T_LPAREN) {
            next();
            emits("(expr_stmt (call (ident ");
            emit(src + ns, nl);
            emit1(')');
            while (tt != T_RPAREN and tt != T_EOF) {
                emit1(' ');
                p_expr();
                if (tt == T_COMMA) next();
            }
            emits("))");
            expect(T_RPAREN);
            expect(T_SEMI);
            return;
        }

        // Unknown — skip to semicolon
        while (tt != T_SEMI and tt != T_EOF) next();
        if (tt == T_SEMI) next();
        return;
    }

    // Skip unknown token
    next();
}

// ========== Top-level ==========

fn p_fn_params() void {
    expect(T_LPAREN);
    emit1('(');
    var first: bool = true;
    while (tt != T_RPAREN and tt != T_EOF) {
        if (!first) emit1(' ');
        first = false;
        const ns = ts;
        const nl = tl;
        expect(T_IDENT);
        expect(T_COLON);
        emits("(param ");
        emit(src + ns, nl);
        emit1(' ');
        parse_type();
        emit1(')');
        if (tt == T_COMMA) next();
    }
    emit1(')');
    expect(T_RPAREN);
}

fn p_fn_decl() void {
    // 'fn' already consumed
    const ns = ts;
    const nl = tl;
    expect(T_IDENT);
    emits("(func ");
    emit(src + ns, nl);
    emit1(' ');
    p_fn_params();
    emit1(' ');
    parse_type();
    emit1(' ');
    p_block();
    emits(")\n");
}

fn p_extern_fn() void {
    expect(T_FN);
    const ns = ts;
    const nl = tl;
    expect(T_IDENT);
    emits("(extern_func ");
    emit(src + ns, nl);
    emit1(' ');
    p_fn_params();
    emit1(' ');
    parse_type();
    emits(")\n");
    expect(T_SEMI);
}

fn skip_braces() void {
    var d: i64 = 1;
    next();
    while (d > 0 and tt != T_EOF) {
        if (tt == T_LBRACE) d +%= 1;
        if (tt == T_RBRACE) d -%= 1;
        next();
    }
}

fn p_program() void {
    emits("(program\n");
    while (tt != T_EOF) {
        if (tt == T_FN) {
            next();
            p_fn_decl();
        } else if (tt == T_EXPORT) {
            next();
            if (tt == T_FN) { next(); p_fn_decl(); } else next();
        } else if (tt == T_EXTERN) {
            next();
            p_extern_fn();
        } else if (tt == T_CONST) {
            // Skip top-level const (struct defs, etc.)
            next();
            while (tt != T_SEMI and tt != T_EOF) {
                if (tt == T_LBRACE) { skip_braces(); } else next();
            }
            if (tt == T_SEMI) next();
        } else {
            next();
        }
    }
    emits(")\n");
}

// ========== Main ==========

export fn main() i64 {
    // Read all of stdin into a buffer
    const buf = malloc(4194304) orelse return 1;
    var total: usize = 0;
    while (total < 4194304) {
        const n = read(0, buf + total, 4096);
        if (n <= 0) break;
        total +%= @as(usize, @intCast(n));
    }

    src = buf;
    src_len = total;
    pos = 0;

    next(); // prime first token
    p_program();
    flush();

    return 0;
}
