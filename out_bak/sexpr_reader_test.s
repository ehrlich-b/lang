.section .data
.str0:
    .ascii "\012\000"
.str1:
    .ascii "\012\000"
.str2:
    .ascii "-\000"
.str3:
    .ascii "0\000"
.str4:
    .ascii "-\000"
.str5:
    .ascii "0\000"
.str6:
    .ascii "number\000"
.str7:
    .ascii "number\000"
.str8:
    .ascii "symbol\000"
.str9:
    .ascii "symbol\000"
.str10:
    .ascii "string\000"
.str11:
    .ascii "string\000"
.str12:
    .ascii "ident\000"
.str13:
    .ascii "ident\000"
.str14:
    .ascii "operator\000"
.str15:
    .ascii "operator\000"
.str16:
    .ascii "    \000"
.str17:
    .ascii "struct PNode {\000"
.str18:
    .ascii "    kind i64;\000"
.str19:
    .ascii "    text *u8;\000"
.str20:
    .ascii "    children *u8;\000"
.str21:
    .ascii "}\000"
.str22:
    .ascii "func pnode_new(kind i64) *PNode {\000"
.str23:
    .ascii "    var n *PNode = alloc(24);\000"
.str24:
    .ascii "    n.kind = kind;\000"
.str25:
    .ascii "    n.text = nil;\000"
.str26:
    .ascii "    n.children = nil;\000"
.str27:
    .ascii "    return n;\000"
.str28:
    .ascii "}\000"
.str29:
    .ascii "func pnode_atom(kind i64, text *u8) *PNode {\000"
.str30:
    .ascii "    var n *PNode = pnode_new(kind);\000"
.str31:
    .ascii "    n.text = text;\000"
.str32:
    .ascii "    return n;\000"
.str33:
    .ascii "}\000"
.str34:
    .ascii "func pnode_list(children *u8) *PNode {\000"
.str35:
    .ascii "    var n *PNode = pnode_new(4);\000"
.str36:
    .ascii "    n.children = children;\000"
.str37:
    .ascii "    return n;\000"
.str38:
    .ascii "}\000"
.str39:
    .ascii "if tok_kind(t) == \000"
.str40:
    .ascii "TOK_LPAREN\000"
.str41:
    .ascii "TOK_RPAREN\000"
.str42:
    .ascii "TOK_LBRACKET\000"
.str43:
    .ascii "TOK_RBRACKET\000"
.str44:
    .ascii "TOK_LBRACE\000"
.str45:
    .ascii "TOK_RBRACE\000"
.str46:
    .ascii "TOK_PLUS\000"
.str47:
    .ascii "TOK_MINUS\000"
.str48:
    .ascii "TOK_STAR\000"
.str49:
    .ascii "TOK_SLASH\000"
.str50:
    .ascii "TOK_COMMA\000"
.str51:
    .ascii "TOK_DOT\000"
.str52:
    .ascii "TOK_EQ\000"
.str53:
    .ascii " { \000"
.str54:
    .ascii " = pnode_new(0); tok_next(t); }\000"
.str55:
    .ascii "if tok_kind(t) == \000"
.str56:
    .ascii "number\000"
.str57:
    .ascii "TOK_NUMBER\000"
.str58:
    .ascii "symbol\000"
.str59:
    .ascii "TOK_IDENT\000"
.str60:
    .ascii "ident\000"
.str61:
    .ascii "TOK_IDENT\000"
.str62:
    .ascii "string\000"
.str63:
    .ascii "TOK_STRING\000"
.str64:
    .ascii "operator\000"
.str65:
    .ascii "TOK_PLUS || tok_kind(t) == TOK_MINUS || tok_kind(t) == TOK_STAR || tok_kind(t) == TOK_SLASH\000"
.str66:
    .ascii " {\000"
.str67:
    .ascii " = pnode_atom(\000"
.str68:
    .ascii "number\000"
.str69:
    .ascii "1\000"
.str70:
    .ascii "symbol\000"
.str71:
    .ascii "2\000"
.str72:
    .ascii "ident\000"
.str73:
    .ascii "2\000"
.str74:
    .ascii "string\000"
.str75:
    .ascii "3\000"
.str76:
    .ascii "operator\000"
.str77:
    .ascii "5\000"
.str78:
    .ascii ", tok_text(t));\000"
.str79:
    .ascii "tok_next(t);\000"
.str80:
    .ascii "}\000"
.str81:
    .ascii " = parse_\000"
.str82:
    .ascii "(t);\000"
.str83:
    .ascii "var _seq *u8 = vec_new(\000"
.str84:
    .ascii ");\000"
.str85:
    .ascii "var _e0 *PNode = nil;\000"
.str86:
    .ascii "_e0\000"
.str87:
    .ascii "if _e0 == nil { return nil; }\000"
.str88:
    .ascii "if _e\000"
.str89:
    .ascii " != nil { vec_push(_seq, _e\000"
.str90:
    .ascii "); }\000"
.str91:
    .ascii "var _e\000"
.str92:
    .ascii " *PNode = nil;\000"
.str93:
    .ascii " = pnode_list(_seq);\000"
.str94:
    .ascii "if \000"
.str95:
    .ascii " == nil {\000"
.str96:
    .ascii "}\000"
.str97:
    .ascii "var _list *u8 = vec_new(8);\000"
.str98:
    .ascii "var _star_done i64 = 0;\000"
.str99:
    .ascii "while _star_done == 0 {\000"
.str100:
    .ascii "var _item *PNode = nil;\000"
.str101:
    .ascii "_item\000"
.str102:
    .ascii "if _item == nil { _star_done = 1; }\000"
.str103:
    .ascii "if _item != nil { vec_push(_list, _item); }\000"
.str104:
    .ascii "}\000"
.str105:
    .ascii " = pnode_list(_list);\000"
.str106:
    .ascii "var _list *u8 = vec_new(8);\000"
.str107:
    .ascii "var _first *PNode = nil;\000"
.str108:
    .ascii "_first\000"
.str109:
    .ascii "if _first == nil { return nil; }\000"
.str110:
    .ascii "vec_push(_list, _first);\000"
.str111:
    .ascii "var _plus_done i64 = 0;\000"
.str112:
    .ascii "while _plus_done == 0 {\000"
.str113:
    .ascii "var _item *PNode = nil;\000"
.str114:
    .ascii "_item\000"
.str115:
    .ascii "if _item == nil { _plus_done = 1; }\000"
.str116:
    .ascii "if _item != nil { vec_push(_list, _item); }\000"
.str117:
    .ascii "}\000"
.str118:
    .ascii " = pnode_list(_list);\000"
.str119:
    .ascii "func parse_\000"
.str120:
    .ascii "(t *Tokenizer) *PNode {\000"
.str121:
    .ascii "var result *PNode = nil;\000"
.str122:
    .ascii "result\000"
.str123:
    .ascii "return result;\000"
.str124:
    .ascii "}\000"
.str125:
    .ascii "nil\000"
.str126:
    .ascii "nil\000"
.str127:
    .ascii "0\000"
.str128:
    .ascii "0\000"
.str129:
    .ascii "(0 \000"
.str130:
    .ascii " \000"
.str131:
    .ascii ")\000"
.str132:
    .ascii "(\000"
.str133:
    .ascii " \000"
.str134:
    .ascii " \000"
.str135:
    .ascii ")\000"
.str136:
    .ascii "0\000"
.str137:
    .ascii "FAIL: expected 42, got \000"
.str138:
    .ascii "\012\000"
.str139:
    .ascii "FAIL: (+ 1 2) expected 3, got \000"
.str140:
    .ascii "\012\000"
.str141:
    .ascii "FAIL: (- 10 3) expected 7, got \000"
.str142:
    .ascii "\012\000"
.str143:
    .ascii "FAIL: (* 6 7) expected 42, got \000"
.str144:
    .ascii "\012\000"
.str145:
    .ascii "FAIL: (* 2 (+ 3 4)) expected 14, got \000"
.str146:
    .ascii "\012\000"
.str147:
    .ascii "FAIL: (+ (* 2 3) (* 4 5)) expected 26, got \000"
.str148:
    .ascii "\012\000"
.str149:
    .ascii "FAIL: (+ 1 2 3) expected 6, got \000"
.str150:
    .ascii "\012\000"
.str151:
    .ascii "PASS: sexpr_reader_test - all tests passed\012\000"
heap_pos:
    .quad 0
heap_end:
    .quad 0
free_list:
    .quad 0
TOK_EOF:
    .quad 0
TOK_NUMBER:
    .quad 1
TOK_IDENT:
    .quad 2
TOK_STRING:
    .quad 3
TOK_LPAREN:
    .quad 4
TOK_RPAREN:
    .quad 5
TOK_LBRACKET:
    .quad 6
TOK_RBRACKET:
    .quad 7
TOK_LBRACE:
    .quad 8
TOK_RBRACE:
    .quad 9
TOK_PLUS:
    .quad 10
TOK_MINUS:
    .quad 11
TOK_STAR:
    .quad 12
TOK_SLASH:
    .quad 13
TOK_PERCENT:
    .quad 14
TOK_COMMA:
    .quad 15
TOK_COLON:
    .quad 16
TOK_SEMI:
    .quad 17
TOK_DOT:
    .quad 18
TOK_EQ:
    .quad 19
TOK_LT:
    .quad 20
TOK_GT:
    .quad 21
TOK_BANG:
    .quad 22
TOK_AMP:
    .quad 23
TOK_PIPE:
    .quad 24
TOK_UNKNOWN:
    .quad 99
GNODE_RULE:
    .quad 1
GNODE_ALT:
    .quad 2
GNODE_CHOICE:
    .quad 3
GNODE_SEQ:
    .quad 4
GNODE_LITERAL:
    .quad 5
GNODE_TOKTYPE:
    .quad 6
GNODE_REF:
    .quad 7
GNODE_STAR:
    .quad 8
GNODE_PLUS:
    .quad 9
GNODE_OPT:
    .quad 10
PNODE_NUMBER:
    .quad 1
PNODE_SYMBOL:
    .quad 2
PNODE_STRING:
    .quad 3
PNODE_LIST:
    .quad 4
PNODE_NIL:
    .quad 5

.section .text
.globl _start
_start:
    mov (%rsp), %rdi
    lea 8(%rsp), %rsi
    call main
    mov %rax, %rdi
    mov $60, %rax
    syscall

.globl alloc
alloc:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov heap_pos(%rip), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov $0, %rax
    push %rax
    mov $0, %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov $34, %rax
    push %rax
    mov $3, %rax
    push %rax
    mov $67108864, %rax
    push %rax
    mov $0, %rax
    push %rax
    mov $9, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %r10
    pop %r8
    pop %r9
    syscall
    mov %rax, heap_pos(%rip)
    mov heap_pos(%rip), %rax
    push %rax
    mov $67108864, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, heap_end(%rip)
.L2:
    mov heap_pos(%rip), %rax
    mov %rax, -16(%rbp)
    mov heap_pos(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, heap_pos(%rip)
    mov -16(%rbp), %rax
    leave
    ret

.globl malloc
malloc:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L4
    mov $8, %rax
    mov %rax, -8(%rbp)
.L4:
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L6
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -8(%rbp)
.L6:
    xor %rax, %rax
    mov %rax, -24(%rbp)
    mov free_list(%rip), %rax
    mov %rax, -32(%rbp)
.L7:
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L8
    mov -32(%rbp), %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L10
    mov -32(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    mov -56(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -64(%rbp)
    mov -24(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L11
    mov -64(%rbp), %rax
    mov %rax, free_list(%rip)
    jmp .L12
.L11:
    mov -24(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -72(%rbp)
    mov -64(%rbp), %rax
    push %rax
    mov -72(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
.L12:
    mov -32(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret
.L10:
    mov -32(%rbp), %rax
    mov %rax, -24(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -80(%rbp)
    mov -80(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -32(%rbp)
    jmp .L7
.L8:
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -88(%rbp)
    mov -88(%rbp), %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -96(%rbp)
    mov -96(%rbp), %rax
    mov %rax, -104(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -96(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

.globl free
free:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L14
    xor %rax, %rax
    leave
    ret
.L14:
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov free_list(%rip), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
    mov %rax, free_list(%rip)
    xor %rax, %rax
    leave
    ret

.globl vec_new
vec_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $24, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -16(%rbp)
    mov $8, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov $64, %rax
    push %rax
    pop %rdi
    call malloc
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    leave
    ret

.globl vec_len
vec_len:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    leave
    ret

.globl vec_get
vec_get:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    leave
    ret

.globl vec_set
vec_set:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    xor %rax, %rax
    leave
    ret

.globl vec_push
vec_push:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -48(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -56(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -64(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L16
    mov -48(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -72(%rbp)
    mov -72(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -80(%rbp)
    mov $0, %rax
    mov %rax, -88(%rbp)
.L17:
    mov -88(%rbp), %rax
    push %rax
    mov -56(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L18
    mov -64(%rbp), %rax
    push %rax
    mov -88(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -96(%rbp)
    mov -80(%rbp), %rax
    push %rax
    mov -88(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -104(%rbp)
    mov -96(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -104(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -88(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -88(%rbp)
    jmp .L17
.L18:
    mov -64(%rbp), %rax
    push %rax
    pop %rdi
    call free
    mov -72(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -80(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -80(%rbp), %rax
    mov %rax, -64(%rbp)
.L16:
    mov -64(%rbp), %rax
    push %rax
    mov -56(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -112(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -112(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -56(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    xor %rax, %rax
    leave
    ret

.globl vec_free
vec_free:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call free
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call free
    xor %rax, %rax
    leave
    ret

.globl vec_pop
vec_pop:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L20
    mov $0, %rax
    leave
    ret
.L20:
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    mov (%rax), %rax
    leave
    ret

.globl hash_str
hash_str:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $5381, %rax
    mov %rax, -16(%rbp)
.L21:
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L22
    mov -16(%rbp), %rax
    push %rax
    mov $33, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -8(%rbp)
    jmp .L21
.L22:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L24
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -16(%rbp)
.L24:
    mov -16(%rbp), %rax
    leave
    ret

.globl map_new
map_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $32, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -16(%rbp)
    mov $16, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov $128, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $0, %rax
    mov %rax, -48(%rbp)
.L25:
    mov -48(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L26
    mov -40(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    xor %rax, %rax
    push %rax
    mov -56(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -48(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    jmp .L25
.L26:
    mov -8(%rbp), %rax
    push %rax
    mov $24, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -64(%rbp)
    mov $128, %rax
    push %rax
    pop %rdi
    call malloc
    push %rax
    mov -64(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    leave
    ret

.globl map_find_slot
map_find_slot:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -48(%rbp)
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call hash_str
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -56(%rbp)
    mov $0, %rax
    mov %rax, -64(%rbp)
.L27:
    mov -64(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L28
    mov -56(%rbp), %rax
    push %rax
    mov -64(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -72(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov -72(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -80(%rbp)
    mov -80(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -88(%rbp)
    mov -88(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L30
    mov -72(%rbp), %rax
    leave
    ret
.L30:
    mov -16(%rbp), %rax
    push %rax
    mov -88(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L32
    mov -72(%rbp), %rax
    leave
    ret
.L32:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -64(%rbp)
    jmp .L27
.L28:
    mov $0, %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    leave
    ret

.globl map_grow
map_grow:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $24, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -48(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -56(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -64(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -72(%rbp)
    mov -72(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -72(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -80(%rbp)
    mov -72(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -88(%rbp)
    mov $0, %rax
    mov %rax, -96(%rbp)
.L33:
    mov -96(%rbp), %rax
    push %rax
    mov -72(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L34
    mov -80(%rbp), %rax
    push %rax
    mov -96(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -104(%rbp)
    xor %rax, %rax
    push %rax
    mov -104(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -96(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -96(%rbp)
    jmp .L33
.L34:
    mov -80(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -88(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $0, %rax
    mov %rax, -96(%rbp)
.L35:
    mov -96(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L36
    mov -56(%rbp), %rax
    push %rax
    mov -96(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -112(%rbp)
    mov -112(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -120(%rbp)
    mov -120(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L38
    mov -64(%rbp), %rax
    push %rax
    mov -96(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -128(%rbp)
    mov -128(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -136(%rbp)
    mov -120(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call map_find_slot
    mov %rax, -144(%rbp)
    mov -80(%rbp), %rax
    push %rax
    mov -144(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -152(%rbp)
    mov -120(%rbp), %rax
    push %rax
    mov -152(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -88(%rbp), %rax
    push %rax
    mov -144(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -160(%rbp)
    mov -136(%rbp), %rax
    push %rax
    mov -160(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -168(%rbp)
    mov -168(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
.L38:
    mov -96(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -96(%rbp)
    jmp .L35
.L36:
    mov -56(%rbp), %rax
    push %rax
    pop %rdi
    call free
    mov -64(%rbp), %rax
    push %rax
    pop %rdi
    call free
    xor %rax, %rax
    leave
    ret

.globl map_set
map_set:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $24, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -64(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -72(%rbp)
    mov -72(%rbp), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    mov -64(%rbp), %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L40
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call map_grow
.L40:
    mov -48(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -80(%rbp)
    mov -56(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -88(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call map_find_slot
    mov %rax, -96(%rbp)
    mov -80(%rbp), %rax
    push %rax
    mov -96(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -104(%rbp)
    mov -104(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -112(%rbp)
    mov -112(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L42
    mov -16(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -72(%rbp)
    mov -72(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
.L42:
    mov -88(%rbp), %rax
    push %rax
    mov -96(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -120(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -120(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    xor %rax, %rax
    leave
    ret

.globl map_get
map_get:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $24, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -40(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -48(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call map_find_slot
    mov %rax, -56(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov -56(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -64(%rbp)
    mov -64(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -72(%rbp)
    mov -72(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L44
    mov $0, %rax
    leave
    ret
.L44:
    mov -48(%rbp), %rax
    push %rax
    mov -56(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -80(%rbp)
    mov -80(%rbp), %rax
    mov (%rax), %rax
    leave
    ret

.globl map_has
map_has:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -32(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call map_find_slot
    mov %rax, -40(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -56(%rbp)
    mov -56(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L46
    mov $0, %rax
    leave
    ret
.L46:
    mov $1, %rax
    leave
    ret

.globl map_free
map_free:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $24, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call free
    mov -24(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call free
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call free
    xor %rax, %rax
    leave
    ret

.globl str_dup_n
str_dup_n:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L47:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L48
    mov -8(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    jmp .L47
.L48:
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -24(%rbp), %rax
    leave
    ret

.globl map_set_n
map_set_n:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov %rcx, -32(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call str_dup_n
    mov %rax, -40(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call map_set
    xor %rax, %rax
    leave
    ret

.globl map_get_n
map_get_n:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call str_dup_n
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call map_get
    mov %rax, -40(%rbp)
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call free
    mov -40(%rbp), %rax
    leave
    ret

.globl file_open
file_open:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov $420, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    syscall
    leave
    ret

.globl file_read
file_read:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    syscall
    leave
    ret

.globl file_write
file_write:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    syscall
    leave
    ret

.globl file_close
file_close:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $3, %rax
    push %rax
    pop %rax
    pop %rdi
    syscall
    xor %rax, %rax
    leave
    ret

.globl strlen
strlen:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $0, %rax
    mov %rax, -16(%rbp)
.L49:
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L50
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L49
.L50:
    mov -16(%rbp), %rax
    leave
    ret

.globl streq
streq:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
.L51:
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L53
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
.L53:
    test %rax, %rax
    jz .L52
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L55
    mov $0, %rax
    leave
    ret
.L55:
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -8(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L51
.L52:
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L57
    mov $1, %rax
    leave
    ret
.L57:
    mov $0, %rax
    leave
    ret

.globl str_eq_n
str_eq_n:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov %rcx, -32(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L59
    xor %rax, %rax
    leave
    ret
.L59:
    mov $0, %rax
    mov %rax, -40(%rbp)
.L60:
    mov -40(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L61
    mov -8(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L63
    xor %rax, %rax
    leave
    ret
.L63:
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L60
.L61:
    mov $1, %rax
    leave
    ret

.globl str_concat
str_concat:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    mov %rax, -32(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -40(%rbp)
    mov $0, %rax
    mov %rax, -48(%rbp)
.L64:
    mov -48(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L65
    mov -8(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -40(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -48(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    jmp .L64
.L65:
    mov $0, %rax
    mov %rax, -56(%rbp)
.L66:
    mov -56(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L67
    mov -16(%rbp), %rax
    push %rax
    mov -56(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -56(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -56(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    jmp .L66
.L67:
    mov $0, %rax
    push %rax
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -40(%rbp), %rax
    leave
    ret

.globl str_dup
str_dup:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L68:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
    test %rax, %rax
    jz .L69
    mov -8(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    jmp .L68
.L69:
    mov -24(%rbp), %rax
    leave
    ret

.globl print
print:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret

.globl println
println:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call print
    mov $1, %rax
    push %rax
    lea .str0(%rip), %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret

.globl eprint
eprint:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret

.globl eprintln
eprintln:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call eprint
    mov $1, %rax
    push %rax
    lea .str1(%rip), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret

.globl eprint_buf
eprint_buf:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret

.globl eprint_i64
eprint_i64:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L71
    mov $1, %rax
    push %rax
    lea .str2(%rip), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -8(%rbp)
.L71:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L73
    mov $1, %rax
    push %rax
    lea .str3(%rip), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret
.L73:
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
.L74:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L75
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L74
.L75:
.L76:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L77
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -32(%rbp)
    mov $48, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov $1, %rax
    push %rax
    lea -40(%rbp), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -8(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -16(%rbp)
    jmp .L76
.L77:
    xor %rax, %rax
    leave
    ret

.globl exit
exit:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $60, %rax
    push %rax
    pop %rax
    pop %rdi
    syscall
    xor %rax, %rax
    leave
    ret

.globl print_digit
print_digit:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $48, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov $1, %rax
    push %rax
    lea -16(%rbp), %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret

.globl print_int
print_int:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L79
    mov $1, %rax
    push %rax
    lea .str4(%rip), %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -8(%rbp)
.L79:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L81
    mov $1, %rax
    push %rax
    lea .str5(%rip), %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call file_write
    xor %rax, %rax
    leave
    ret
.L81:
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
.L82:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L83
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L82
.L83:
.L84:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L85
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call print_digit
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -8(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -16(%rbp)
    jmp .L84
.L85:
    xor %rax, %rax
    leave
    ret

.globl sb_new
sb_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $24, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -8(%rbp)
    mov $256, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    call alloc
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -8(%rbp), %rax
    leave
    ret

.globl sb_grow
sb_grow:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L87
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -24(%rbp)
.L88:
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L89
    mov -24(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -24(%rbp)
    jmp .L88
.L89:
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
.L90:
    mov -40(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L91
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov (%rax), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L90
.L91:
    mov -32(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
.L87:
    xor %rax, %rax
    leave
    ret

.globl sb_char
sb_char:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_grow
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    xor %rax, %rax
    leave
    ret

.globl sb_str
sb_str:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
.L92:
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L93
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L92
.L93:
    xor %rax, %rax
    leave
    ret

.globl sb_int
sb_int:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L95
    mov $45, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -16(%rbp)
.L95:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L97
    mov $48, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    xor %rax, %rax
    leave
    ret
.L97:
    mov -16(%rbp), %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L98:
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L99
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -24(%rbp)
    jmp .L98
.L99:
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -40(%rbp)
.L100:
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L101
    mov $1, %rax
    mov %rax, -48(%rbp)
    mov $0, %rax
    mov %rax, -56(%rbp)
.L102:
    mov -56(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L103
    mov -48(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -48(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    jmp .L102
.L103:
    mov -16(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -64(%rbp)
    mov $48, %rax
    push %rax
    mov -64(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L100
.L101:
    xor %rax, %rax
    leave
    ret

.globl sb_finish
sb_finish:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -8(%rbp), %rax
    mov (%rax), %rax
    leave
    ret

.globl emit_number
emit_number:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    call sb_new
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_int
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl emit_binop
emit_binop:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    call sb_new
    mov %rax, -32(%rbp)
    mov $40, %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -8(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $32, %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -16(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $32, %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -24(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $41, %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl emit_unary
emit_unary:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    call sb_new
    mov %rax, -24(%rbp)
    mov $40, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -8(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -16(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $41, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl emit_call
emit_call:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    call sb_new
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $40, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
.L104:
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L105
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L107
    mov $44, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $32, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
.L107:
    mov -40(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L104
.L105:
    mov $41, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl emit_string
emit_string:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    call sb_new
    mov %rax, -16(%rbp)
    mov $34, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
.L108:
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L109
    mov -8(%rbp), %rax
    movzbl (%rax), %eax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L110
    mov $92, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $34, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    jmp .L111
.L110:
    mov -24(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L112
    mov $92, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $92, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    jmp .L113
.L112:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L114
    mov $92, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $110, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    jmp .L115
.L114:
    mov -24(%rbp), %rax
    push %rax
    mov $13, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L116
    mov $92, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $114, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    jmp .L117
.L116:
    mov -24(%rbp), %rax
    push %rax
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L118
    mov $92, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov $116, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    jmp .L119
.L118:
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
.L119:
.L117:
.L115:
.L113:
.L111:
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -8(%rbp)
    jmp .L108
.L109:
    mov $34, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl emit_ident
emit_ident:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call str_dup
    leave
    ret

.globl emit_paren
emit_paren:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    call sb_new
    mov %rax, -16(%rbp)
    mov $40, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $41, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl tok_new
tok_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $48, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov TOK_EOF(%rip), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov -16(%rbp), %rax
    leave
    ret

.globl tok_is_digit
tok_is_digit:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $48, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L120
    mov -8(%rbp), %rax
    push %rax
    mov $57, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L120:
    leave
    ret

.globl tok_is_alpha
tok_is_alpha:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $65, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L123
    mov -8(%rbp), %rax
    push %rax
    mov $90, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L123:
    test %rax, %rax
    jnz .L122
    mov -8(%rbp), %rax
    push %rax
    mov $97, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L124
    mov -8(%rbp), %rax
    push %rax
    mov $122, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L124:
.L122:
    test %rax, %rax
    jnz .L121
    mov -8(%rbp), %rax
    push %rax
    mov $95, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L121:
    leave
    ret

.globl tok_is_alnum
tok_is_alnum:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jnz .L125
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
.L125:
    leave
    ret

.globl tok_is_space
tok_is_space:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $32, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jnz .L128
    mov -8(%rbp), %rax
    push %rax
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L128:
    test %rax, %rax
    jnz .L127
    mov -8(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L127:
    test %rax, %rax
    jnz .L126
    mov -8(%rbp), %rax
    push %rax
    mov $13, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L126:
    leave
    ret

.globl tok_peek_char
tok_peek_char:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L130
    mov $0, %rax
    leave
    ret
.L130:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    leave
    ret

.globl tok_peek_char_at
tok_peek_char_at:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L132
    mov $0, %rax
    leave
    ret
.L132:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    leave
    ret

.globl tok_advance_char
tok_advance_char:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L134
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
.L134:
    xor %rax, %rax
    leave
    ret

.globl tok_skip_whitespace
tok_skip_whitespace:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
.L135:
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L137
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_space
.L137:
    test %rax, %rax
    jz .L136
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L135
.L136:
    xor %rax, %rax
    leave
    ret

.globl tok_next
tok_next:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_skip_whitespace
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L139
    mov TOK_EOF(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L139:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $40, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L141
    mov TOK_LPAREN(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L141:
    mov -16(%rbp), %rax
    push %rax
    mov $41, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L143
    mov TOK_RPAREN(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L143:
    mov -16(%rbp), %rax
    push %rax
    mov $91, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L145
    mov TOK_LBRACKET(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L145:
    mov -16(%rbp), %rax
    push %rax
    mov $93, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L147
    mov TOK_RBRACKET(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L147:
    mov -16(%rbp), %rax
    push %rax
    mov $123, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L149
    mov TOK_LBRACE(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L149:
    mov -16(%rbp), %rax
    push %rax
    mov $125, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L151
    mov TOK_RBRACE(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L151:
    mov -16(%rbp), %rax
    push %rax
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L153
    mov TOK_PLUS(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L153:
    mov -16(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L155
    mov TOK_STAR(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L155:
    mov -16(%rbp), %rax
    push %rax
    mov $47, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L157
    mov TOK_SLASH(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L157:
    mov -16(%rbp), %rax
    push %rax
    mov $37, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L159
    mov TOK_PERCENT(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L159:
    mov -16(%rbp), %rax
    push %rax
    mov $44, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L161
    mov TOK_COMMA(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L161:
    mov -16(%rbp), %rax
    push %rax
    mov $58, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L163
    mov TOK_COLON(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L163:
    mov -16(%rbp), %rax
    push %rax
    mov $59, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L165
    mov TOK_SEMI(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L165:
    mov -16(%rbp), %rax
    push %rax
    mov $46, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L167
    mov TOK_DOT(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L167:
    mov -16(%rbp), %rax
    push %rax
    mov $61, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L169
    mov TOK_EQ(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L169:
    mov -16(%rbp), %rax
    push %rax
    mov $60, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L171
    mov TOK_LT(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L171:
    mov -16(%rbp), %rax
    push %rax
    mov $62, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L173
    mov TOK_GT(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L173:
    mov -16(%rbp), %rax
    push %rax
    mov $33, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L175
    mov TOK_BANG(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L175:
    mov -16(%rbp), %rax
    push %rax
    mov $38, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L177
    mov TOK_AMP(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L177:
    mov -16(%rbp), %rax
    push %rax
    mov $124, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L179
    mov TOK_PIPE(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L179:
    mov -16(%rbp), %rax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L181
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call tok_peek_char_at
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L183
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L184:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L185
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L184
.L185:
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov TOK_NUMBER(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L183:
    mov TOK_MINUS(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret
.L181:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L187
.L188:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L189
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L188
.L189:
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov TOK_NUMBER(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L187:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
    test %rax, %rax
    jz .L191
.L192:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_alnum
    test %rax, %rax
    jz .L193
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L192
.L193:
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov TOK_IDENT(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L191:
    mov -16(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L195
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L196:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L198
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
.L198:
    test %rax, %rax
    jz .L197
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L200
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L200:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L196
.L197:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L202
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L202:
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov TOK_STRING(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L195:
    mov -16(%rbp), %rax
    push %rax
    mov $39, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L204
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L205:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L207
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $39, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
.L207:
    test %rax, %rax
    jz .L206
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L209
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L209:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L205
.L206:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    mov $39, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L211
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L211:
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov TOK_STRING(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L204:
    mov TOK_UNKNOWN(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    xor %rax, %rax
    leave
    ret

.globl tok_kind
tok_kind:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov 40(%rax), %rax
    leave
    ret

.globl tok_eof
tok_eof:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov 40(%rax), %rax
    push %rax
    mov TOK_EOF(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    leave
    ret

.globl tok_text_ptr
tok_text_ptr:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

.globl tok_text_len
tok_text_len:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov 32(%rax), %rax
    leave
    ret

.globl tok_text
tok_text:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov 32(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L212:
    mov -32(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L213
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    jmp .L212
.L213:
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
    leave
    ret

.globl tok_number
tok_number:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L216
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L216:
    test %rax, %rax
    jz .L215
    mov $1, %rax
    mov %rax, -32(%rbp)
    mov $1, %rax
    mov %rax, -40(%rbp)
.L215:
    mov $0, %rax
    mov %rax, -48(%rbp)
.L217:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L218
    mov -48(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov $48, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L217
.L218:
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L220
    mov $0, %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    leave
    ret
.L220:
    mov -48(%rbp), %rax
    leave
    ret

.globl tok_string_value
tok_string_value:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov 32(%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
    mov $0, %rax
    mov %rax, -48(%rbp)
.L221:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L222
    mov -16(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    mov %rax, -56(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L225
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
.L225:
    test %rax, %rax
    jz .L224
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    mov %rax, -64(%rbp)
    mov -64(%rbp), %rax
    push %rax
    mov $110, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L226
    mov $10, %rax
    mov %rax, -56(%rbp)
    jmp .L227
.L226:
    mov -64(%rbp), %rax
    push %rax
    mov $114, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L228
    mov $13, %rax
    mov %rax, -56(%rbp)
    jmp .L229
.L228:
    mov -64(%rbp), %rax
    push %rax
    mov $116, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L230
    mov $9, %rax
    mov %rax, -56(%rbp)
    jmp .L231
.L230:
    mov -64(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L232
    mov $34, %rax
    mov %rax, -56(%rbp)
    jmp .L233
.L232:
    mov -64(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L234
    mov $92, %rax
    mov %rax, -56(%rbp)
    jmp .L235
.L234:
    mov -64(%rbp), %rax
    mov %rax, -56(%rbp)
.L235:
.L233:
.L231:
.L229:
.L227:
.L224:
    mov -56(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    jmp .L221
.L222:
    mov $0, %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -32(%rbp), %rax
    leave
    ret

.globl tok_check
tok_check:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov 40(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    leave
    ret

.globl tok_match
tok_match:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov 40(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L237
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
    leave
    ret
.L237:
    xor %rax, %rax
    leave
    ret

.globl tok_expect
tok_expect:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov 40(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L239
    xor %rax, %rax
    leave
    ret
.L239:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
    leave
    ret

.globl gnode_new
gnode_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $40, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    xor %rax, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    xor %rax, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    xor %rax, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -16(%rbp), %rax
    leave
    ret

.globl gnode_with_name
gnode_with_name:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -32(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -24(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -32(%rbp), %rax
    leave
    ret

.globl grammar_new
grammar_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $16, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -8(%rbp)
    mov $8, %rax
    push %rax
    pop %rdi
    call vec_new
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    call map_new
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -8(%rbp), %rax
    leave
    ret

.globl grammar_add_rule
grammar_add_rule:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    mov -16(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call map_set_n
    xor %rax, %rax
    leave
    ret

.globl grammar_get_rule
grammar_get_rule:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call map_get_n
    leave
    ret

.globl gp_new
gp_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $8, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_new
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
    leave
    ret

.globl gp_is_keyword
gp_is_keyword:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_IDENT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L241
    xor %rax, %rax
    leave
    ret
.L241:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_ptr
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_len
    mov %rax, -32(%rbp)
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call strlen
    push %rax
    mov -16(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    leave
    ret

.globl gp_parse_element
gp_parse_element:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    xor %rax, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_STRING(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L242
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_ptr
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_len
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov GNODE_LITERAL(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L243
.L242:
    lea .str6(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L244
    mov $6, %rax
    push %rax
    lea .str7(%rip), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L245
.L244:
    lea .str8(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L246
    mov $6, %rax
    push %rax
    lea .str9(%rip), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L247
.L246:
    lea .str10(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L248
    mov $6, %rax
    push %rax
    lea .str11(%rip), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L249
.L248:
    lea .str12(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L250
    mov $5, %rax
    push %rax
    lea .str13(%rip), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L251
.L250:
    lea .str14(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L252
    mov $8, %rax
    push %rax
    lea .str15(%rip), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L253
.L252:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_IDENT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L254
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text_ptr
    mov %rax, -48(%rbp)
    mov -40(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text_len
    mov %rax, -56(%rbp)
    mov -40(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -64(%rbp)
    mov -40(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, -72(%rbp)
    mov -40(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, -80(%rbp)
    mov -40(%rbp), %rax
    mov 40(%rax), %rax
    mov %rax, -88(%rbp)
    mov -40(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov -40(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_EQ(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L257
    mov -64(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -72(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    mov -80(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -88(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L257:
    mov -56(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    push %rax
    mov GNODE_REF(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call gnode_with_name
    mov %rax, -16(%rbp)
    jmp .L255
.L254:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_LPAREN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L258
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gp_parse_choice
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_RPAREN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L261
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
.L261:
    jmp .L259
.L258:
    xor %rax, %rax
    leave
    ret
.L259:
.L255:
.L253:
.L251:
.L249:
.L247:
.L245:
.L243:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_STAR(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L262
    mov GNODE_STAR(%rip), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -96(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -96(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -96(%rbp), %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L263
.L262:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_PLUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L264
    mov GNODE_PLUS(%rip), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -104(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -104(%rbp), %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L265
.L264:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_UNKNOWN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L267
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_ptr
    mov %rax, -112(%rbp)
    mov -112(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $63, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L269
    mov GNODE_OPT(%rip), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -120(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -120(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -120(%rbp), %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
.L269:
.L267:
.L265:
.L263:
    mov -16(%rbp), %rax
    leave
    ret

.globl gp_parse_seq
gp_parse_seq:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $4, %rax
    push %rax
    pop %rdi
    call vec_new
    mov %rax, -16(%rbp)
    mov $0, %rax
    mov %rax, -24(%rbp)
.L270:
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L271
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gp_parse_element
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L272
    mov $1, %rax
    mov %rax, -24(%rbp)
    jmp .L273
.L272:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L273:
    jmp .L270
.L271:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L275
    xor %rax, %rax
    leave
    ret
.L275:
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L277
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    leave
    ret
.L277:
    mov GNODE_SEQ(%rip), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -48(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    mov -48(%rbp), %rax
    leave
    ret

.globl gp_parse_choice
gp_parse_choice:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $4, %rax
    push %rax
    pop %rdi
    call vec_new
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gp_parse_seq
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L279
    xor %rax, %rax
    leave
    ret
.L279:
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L280:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_PIPE(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L281
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gp_parse_seq
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L283
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L283:
    jmp .L280
.L281:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L285
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    leave
    ret
.L285:
    mov GNODE_CHOICE(%rip), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -40(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    mov -40(%rbp), %rax
    leave
    ret

.globl gp_parse_rule
gp_parse_rule:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_IDENT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L287
    xor %rax, %rax
    leave
    ret
.L287:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_ptr
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_text_len
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_EQ(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L289
    xor %rax, %rax
    leave
    ret
.L289:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gp_parse_choice
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L291
    xor %rax, %rax
    leave
    ret
.L291:
    mov GNODE_RULE(%rip), %rax
    push %rax
    pop %rdi
    call gnode_new
    mov %rax, -40(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -24(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -32(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -40(%rbp), %rax
    leave
    ret

.globl grammar_parse
grammar_parse:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call gp_new
    mov %rax, -16(%rbp)
    call grammar_new
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L292:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_eof
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L294
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L294:
    test %rax, %rax
    jz .L293
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call gp_parse_rule
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L295
    mov $1, %rax
    mov %rax, -32(%rbp)
    jmp .L296
.L295:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call grammar_add_rule
.L296:
    jmp .L292
.L293:
    mov -24(%rbp), %rax
    leave
    ret

.globl rdgen_new
rdgen_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $24, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -16(%rbp)
    call sb_new
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -16(%rbp), %rax
    leave
    ret

.globl rdgen_indent
rdgen_indent:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $0, %rax
    mov %rax, -16(%rbp)
.L297:
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L298
    lea .str16(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L297
.L298:
    xor %rax, %rax
    leave
    ret

.globl rdgen_line
rdgen_line:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $10, %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    xor %rax, %rax
    leave
    ret

.globl rdgen_str
rdgen_str:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret

.globl rdgen_strn
rdgen_strn:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L299:
    mov -32(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L300
    mov -16(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    movzbl (%rax), %eax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    jmp .L299
.L300:
    xor %rax, %rax
    leave
    ret

.globl rdgen_int
rdgen_int:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_int
    xor %rax, %rax
    leave
    ret

.globl rdgen_newline
rdgen_newline:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $10, %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
    xor %rax, %rax
    leave
    ret

.globl rdgen_emit_pnode_struct
rdgen_emit_pnode_struct:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    lea .str17(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str18(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str19(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str20(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str21(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    lea .str22(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str23(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str24(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str25(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str26(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str27(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str28(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    lea .str29(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str30(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str31(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str32(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str33(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    lea .str34(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str35(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str36(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str37(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str38(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    xor %rax, %rax
    leave
    ret

.globl genwork_new
genwork_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov $40, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    xor %rax, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 24(%rcx)
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -24(%rbp), %rax
    leave
    ret

.globl rdgen_gen_expr
rdgen_gen_expr:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L302
    xor %rax, %rax
    leave
    ret
.L302:
    mov $16, %rax
    push %rax
    pop %rdi
    call vec_new
    mov %rax, -32(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L303:
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L304
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call vec_pop
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -48(%rbp)
    mov -40(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -56(%rbp)
    mov -40(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, -64(%rbp)
    mov -48(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -72(%rbp)
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_LITERAL(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L305
    mov -48(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -80(%rbp)
    mov -48(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, -88(%rbp)
    mov -88(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L308
    mov -80(%rbp), %rax
    movzbl (%rax), %eax
    mov %rax, -96(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str39(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -96(%rbp), %rax
    push %rax
    mov $40, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L309
    lea .str40(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L310
.L309:
    mov -96(%rbp), %rax
    push %rax
    mov $41, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L311
    lea .str41(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L312
.L311:
    mov -96(%rbp), %rax
    push %rax
    mov $91, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L313
    lea .str42(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L314
.L313:
    mov -96(%rbp), %rax
    push %rax
    mov $93, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L315
    lea .str43(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L316
.L315:
    mov -96(%rbp), %rax
    push %rax
    mov $123, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L317
    lea .str44(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L318
.L317:
    mov -96(%rbp), %rax
    push %rax
    mov $125, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L319
    lea .str45(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L320
.L319:
    mov -96(%rbp), %rax
    push %rax
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L321
    lea .str46(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L322
.L321:
    mov -96(%rbp), %rax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L323
    lea .str47(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L324
.L323:
    mov -96(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L325
    lea .str48(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L326
.L325:
    mov -96(%rbp), %rax
    push %rax
    mov $47, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L327
    lea .str49(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L328
.L327:
    mov -96(%rbp), %rax
    push %rax
    mov $44, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L329
    lea .str50(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L330
.L329:
    mov -96(%rbp), %rax
    push %rax
    mov $46, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L331
    lea .str51(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L332
.L331:
    mov -96(%rbp), %rax
    push %rax
    mov $61, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L333
    lea .str52(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L334
.L333:
    mov -96(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_int
.L334:
.L332:
.L330:
.L328:
.L326:
.L324:
.L322:
.L320:
.L318:
.L316:
.L314:
.L312:
.L310:
    lea .str53(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str54(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
.L308:
    jmp .L306
.L305:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L335
    mov -48(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -104(%rbp)
    mov -48(%rbp), %rax
    mov 16(%rax), %rax
    mov %rax, -112(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str55(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $6, %rax
    push %rax
    lea .str56(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L337
    lea .str57(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L338
.L337:
    mov $6, %rax
    push %rax
    lea .str58(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L339
    lea .str59(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L340
.L339:
    mov $5, %rax
    push %rax
    lea .str60(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L341
    lea .str61(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L342
.L341:
    mov $6, %rax
    push %rax
    lea .str62(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L343
    lea .str63(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L344
.L343:
    mov $8, %rax
    push %rax
    lea .str64(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L346
    lea .str65(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L346:
.L344:
.L342:
.L340:
.L338:
    lea .str66(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str67(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $6, %rax
    push %rax
    lea .str68(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L347
    lea .str69(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L348
.L347:
    mov $6, %rax
    push %rax
    lea .str70(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L349
    lea .str71(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L350
.L349:
    mov $5, %rax
    push %rax
    lea .str72(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L351
    lea .str73(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L352
.L351:
    mov $6, %rax
    push %rax
    lea .str74(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L353
    lea .str75(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L354
.L353:
    mov $8, %rax
    push %rax
    lea .str76(%rip), %rax
    push %rax
    mov -112(%rbp), %rax
    push %rax
    mov -104(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    call str_eq_n
    test %rax, %rax
    jz .L356
    lea .str77(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L356:
.L354:
.L352:
.L350:
.L348:
    lea .str78(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    lea .str79(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str80(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    jmp .L336
.L335:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_REF(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L357
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str81(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -48(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov -48(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call rdgen_strn
    lea .str82(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    jmp .L358
.L357:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_SEQ(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L359
    mov -48(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, -120(%rbp)
    mov -120(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -128(%rbp)
    mov -64(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L361
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str83(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -128(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_int
    lea .str84(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov -128(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L364
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str85(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov $1, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov $0, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    mov $0, %rax
    push %rax
    mov -120(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -136(%rbp)
    lea .str86(%rip), %rax
    push %rax
    mov -136(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L364:
    jmp .L362
.L361:
    mov -40(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, -144(%rbp)
    mov -144(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L366
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str87(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
.L366:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str88(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -144(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_int
    lea .str89(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -144(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_int
    lea .str90(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov -144(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -144(%rbp)
    mov -144(%rbp), %rax
    push %rax
    mov -128(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L367
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str91(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -144(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_int
    lea .str92(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -144(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 32(%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    mov -144(%rbp), %rax
    push %rax
    mov -120(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -152(%rbp)
    mov $16, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -160(%rbp)
    mov $95, %rax
    push %rax
    mov -160(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $101, %rax
    push %rax
    mov -160(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $48, %rax
    push %rax
    mov -144(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -160(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov $0, %rax
    push %rax
    mov -160(%rbp), %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -160(%rbp), %rax
    push %rax
    mov -152(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    jmp .L368
.L367:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str93(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
.L368:
.L362:
    jmp .L360
.L359:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_CHOICE(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L369
    mov -48(%rbp), %rax
    mov 24(%rax), %rax
    mov %rax, -168(%rbp)
    mov -168(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -176(%rbp)
    mov -64(%rbp), %rax
    push %rax
    mov -176(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L371
    mov -64(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L374
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str94(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str95(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
.L374:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    mov -64(%rbp), %rax
    push %rax
    mov -168(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -184(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov -184(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    jmp .L372
.L371:
    mov -176(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -192(%rbp)
.L375:
    mov -192(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L376
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str96(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -192(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -192(%rbp)
    jmp .L375
.L376:
.L372:
    jmp .L370
.L369:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_STAR(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L377
    mov -48(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, -200(%rbp)
    mov -64(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L379
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str97(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    lea .str98(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str99(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str100(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov $1, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    lea .str101(%rip), %rax
    push %rax
    mov -200(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    jmp .L380
.L379:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L382
    lea .str102(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str103(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str104(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str105(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
.L382:
.L380:
    jmp .L378
.L377:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_PLUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L383
    mov -48(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, -208(%rbp)
    mov -64(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L385
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str106(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    lea .str107(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov $1, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    lea .str108(%rip), %rax
    push %rax
    mov -208(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    jmp .L386
.L385:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L387
    lea .str109(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str110(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str111(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str112(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str113(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov $2, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    lea .str114(%rip), %rax
    push %rax
    mov -208(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    jmp .L388
.L387:
    mov -64(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L390
    lea .str115(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str116(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str117(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str118(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
.L390:
.L388:
.L386:
    jmp .L384
.L383:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_OPT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L392
    mov -48(%rbp), %rax
    mov 32(%rax), %rax
    mov %rax, -216(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov -216(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call genwork_new
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L392:
.L384:
.L378:
.L370:
.L360:
.L358:
.L336:
.L306:
    jmp .L303
.L304:
    xor %rax, %rax
    leave
    ret

.globl rdgen_gen_rule
rdgen_gen_rule:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_indent
    lea .str119(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -16(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov -16(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call rdgen_strn
    lea .str120(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str121(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    lea .str122(%rip), %rax
    push %rax
    mov -16(%rbp), %rax
    mov 32(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call rdgen_gen_expr
    lea .str123(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    lea .str124(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_line
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_newline
    xor %rax, %rax
    leave
    ret

.globl rdgen_generate
rdgen_generate:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_new
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call rdgen_emit_pnode_struct
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
.L393:
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L394
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call rdgen_gen_rule
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L393
.L394:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl pnode_new
pnode_new:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $24, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    xor %rax, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    xor %rax, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -16(%rbp), %rax
    leave
    ret

.globl pnode_atom
pnode_atom:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call pnode_new
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 8(%rcx)
    mov -24(%rbp), %rax
    leave
    ret

.globl pnode_list
pnode_list:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $4, %rax
    push %rax
    pop %rdi
    call pnode_new
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov -16(%rbp), %rax
    leave
    ret

.globl parse_sexp
parse_sexp:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    xor %rax, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_NUMBER(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L396
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    call pnode_atom
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L396:
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L398
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_IDENT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L400
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    pop %rsi
    call pnode_atom
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L400:
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L402
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_PLUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jnz .L407
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_MINUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L407:
    test %rax, %rax
    jnz .L406
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_STAR(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L406:
    test %rax, %rax
    jnz .L405
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_SLASH(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L405:
    test %rax, %rax
    jz .L404
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    mov $5, %rax
    push %rax
    pop %rdi
    pop %rsi
    call pnode_atom
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L404:
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L409
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call parse_list
    mov %rax, -16(%rbp)
.L409:
.L402:
.L398:
    mov -16(%rbp), %rax
    leave
    ret

.globl parse_list
parse_list:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    xor %rax, %rax
    mov %rax, -16(%rbp)
    mov $3, %rax
    push %rax
    pop %rdi
    call vec_new
    mov %rax, -24(%rbp)
    xor %rax, %rax
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_LPAREN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L411
    mov $0, %rax
    push %rax
    pop %rdi
    call pnode_new
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L411:
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L413
    xor %rax, %rax
    leave
    ret
.L413:
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L415
    mov -32(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L415:
    xor %rax, %rax
    mov %rax, -40(%rbp)
    mov $8, %rax
    push %rax
    pop %rdi
    call vec_new
    mov %rax, -48(%rbp)
    mov $0, %rax
    mov %rax, -56(%rbp)
.L416:
    mov -56(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L417
    xor %rax, %rax
    mov %rax, -64(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call parse_sexp
    mov %rax, -64(%rbp)
    mov -64(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L419
    mov $1, %rax
    mov %rax, -56(%rbp)
.L419:
    mov -64(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L421
    mov -64(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L421:
    jmp .L416
.L417:
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    call pnode_list
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L423
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L423:
    xor %rax, %rax
    mov %rax, -72(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_RPAREN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L425
    mov $0, %rax
    push %rax
    pop %rdi
    call pnode_new
    mov %rax, -72(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L425:
    mov -72(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L427
    mov -72(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L427:
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call pnode_list
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    leave
    ret

.globl sexpr_to_lang
sexpr_to_lang:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L429
    lea .str125(%rip), %rax
    leave
    ret
.L429:
    call sb_new
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sexpr_emit
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl sexpr_emit
sexpr_emit:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L431
    lea .str126(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L431:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L433
    mov -16(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L433:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L435
    mov -16(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L435:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L437
    mov -16(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L437:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L439
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L441
    lea .str127(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L441:
    mov $0, %rax
    push %rax
    mov -24(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L443
    lea .str128(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L443:
    mov -40(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -48(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L445
    mov -40(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sexpr_emit
    xor %rax, %rax
    leave
    ret
.L445:
    mov -32(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L447
    lea .str129(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -48(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str130(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    push %rax
    mov -24(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sexpr_emit
    lea .str131(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L447:
    lea .str132(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    push %rax
    mov -24(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sexpr_emit
    mov $2, %rax
    mov %rax, -56(%rbp)
.L448:
    mov -56(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L449
    lea .str133(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -48(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str134(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -56(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sexpr_emit
    mov -56(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    jmp .L448
.L449:
    lea .str135(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L439:
    lea .str136(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $42, %rax
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L451
    lea .str137(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str138(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $1, %rax
    leave
    ret
.L451:
    mov $1, %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L453
    lea .str139(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str140(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $2, %rax
    leave
    ret
.L453:
    mov $10, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L455
    lea .str141(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str142(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $3, %rax
    leave
    ret
.L455:
    mov $6, %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L457
    lea .str143(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str144(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $4, %rax
    leave
    ret
.L457:
    mov $2, %rax
    push %rax
    mov $3, %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov $14, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L459
    lea .str145(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -40(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str146(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $5, %rax
    leave
    ret
.L459:
    mov $2, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    mov $4, %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov $26, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L461
    lea .str147(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str148(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $6, %rax
    leave
    ret
.L461:
    mov $1, %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov $6, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L463
    lea .str149(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -56(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str150(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $7, %rax
    leave
    ret
.L463:
    lea .str151(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $0, %rax
    leave
    ret

