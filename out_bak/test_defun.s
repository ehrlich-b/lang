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
    .ascii "TOK_PLUS || tok_kind(t) == TOK_MINUS || tok_kind(t) == TOK_STAR || tok_kind(t) == TOK_SLASH || tok_kind(t) == TOK_PERCENT || tok_kind(t) == TOK_LT || tok_kind(t) == TOK_GT\000"
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
    .ascii "0\000"
.str126:
    .ascii "<\000"
.str127:
    .ascii ">\000"
.str128:
    .ascii "<=\000"
.str129:
    .ascii ">=\000"
.str130:
    .ascii "=\000"
.str131:
    .ascii "!=\000"
.str132:
    .ascii "=\000"
.str133:
    .ascii "==\000"
.str134:
    .ascii "!=\000"
.str135:
    .ascii "!=\000"
.str136:
    .ascii "+\000"
.str137:
    .ascii "-\000"
.str138:
    .ascii "*\000"
.str139:
    .ascii "/\000"
.str140:
    .ascii "%\000"
.str141:
    .ascii "if\000"
.str142:
    .ascii "0\000"
.str143:
    .ascii "0\000"
.str144:
    .ascii "0\000"
.str145:
    .ascii "defun\000"
.str146:
    .ascii "/* defun needs name, params, body */\000"
.str147:
    .ascii "func \000"
.str148:
    .ascii "(\000"
.str149:
    .ascii ", \000"
.str150:
    .ascii " i64\000"
.str151:
    .ascii ") i64 {\012\000"
.str152:
    .ascii "    \000"
.str153:
    .ascii "    return \000"
.str154:
    .ascii ";\012\000"
.str155:
    .ascii "}\012\000"
.str156:
    .ascii "if\000"
.str157:
    .ascii "/* if needs cond, then, else */\000"
.str158:
    .ascii "((\000"
.str159:
    .ascii ") * (\000"
.str160:
    .ascii ") + (!(\000"
.str161:
    .ascii ")) * (\000"
.str162:
    .ascii "))\000"
.str163:
    .ascii "and\000"
.str164:
    .ascii "(\000"
.str165:
    .ascii " && \000"
.str166:
    .ascii ")\000"
.str167:
    .ascii "or\000"
.str168:
    .ascii "(\000"
.str169:
    .ascii " || \000"
.str170:
    .ascii ")\000"
.str171:
    .ascii "not\000"
.str172:
    .ascii "(!\000"
.str173:
    .ascii ")\000"
.str174:
    .ascii "0\000"
.str175:
    .ascii "(\000"
.str176:
    .ascii " \000"
.str177:
    .ascii " \000"
.str178:
    .ascii ")\000"
.str179:
    .ascii "(0 \000"
.str180:
    .ascii " \000"
.str181:
    .ascii ")\000"
.str182:
    .ascii "(\000"
.str183:
    .ascii " \000"
.str184:
    .ascii " \000"
.str185:
    .ascii ")\000"
.str186:
    .ascii "(\000"
.str187:
    .ascii ", \000"
.str188:
    .ascii ")\000"
.str189:
    .ascii "/* unknown */0\000"
.str190:
    .ascii "0\000"
.str191:
    .ascii "if (\000"
.str192:
    .ascii ") {\012\000"
.str193:
    .ascii "    return \000"
.str194:
    .ascii ";\012\000"
.str195:
    .ascii "}\012\000"
.str196:
    .ascii "else \000"
.str197:
    .ascii "\000"
.str198:
    .ascii "return \000"
.str199:
    .ascii ";\012\000"
.str200:
    .ascii "add(3, 4) = \000"
.str201:
    .ascii "\000"
.str202:
    .ascii "square(5) = \000"
.str203:
    .ascii "\000"
.str204:
    .ascii "abs(10) = \000"
.str205:
    .ascii ", abs(-10) = \000"
.str206:
    .ascii "\000"
.str207:
    .ascii "max(3,7) = \000"
.str208:
    .ascii ", max(7,3) = \000"
.str209:
    .ascii "\000"
.str210:
    .ascii "factorial(5) = \000"
.str211:
    .ascii "\000"
.str212:
    .ascii "(add (square 3) (square 4)) = \000"
.str213:
    .ascii "\000"
.str214:
    .ascii "All tests passed!\000"
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
    mov %rdi, -8(%rbp)
    mov $24, %rax
    push %rax
    pop %rdi
    call malloc
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L16
    mov $4, %rax
    mov %rax, -8(%rbp)
.L16:
    mov -16(%rbp), %rax
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -32(%rbp)
    mov $0, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $8, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    push %rax
    pop %rdi
    call malloc
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -16(%rbp), %rax
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
    jz .L18
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
.L19:
    mov -88(%rbp), %rax
    push %rax
    mov -56(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L20
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
    jmp .L19
.L20:
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
.L18:
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
    jz .L22
    mov $0, %rax
    leave
    ret
.L22:
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
.L23:
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
    jz .L24
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
    jmp .L23
.L24:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L26
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -16(%rbp)
.L26:
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
.L27:
    mov -48(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L28
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
    jmp .L27
.L28:
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
.L29:
    mov -64(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L30
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
    jz .L32
    mov -72(%rbp), %rax
    leave
    ret
.L32:
    mov -16(%rbp), %rax
    push %rax
    mov -88(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L34
    mov -72(%rbp), %rax
    leave
    ret
.L34:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -64(%rbp)
    jmp .L29
.L30:
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
.L35:
    mov -96(%rbp), %rax
    push %rax
    mov -72(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L36
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
    jmp .L35
.L36:
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
.L37:
    mov -96(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L38
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
    jz .L40
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
.L40:
    mov -96(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -96(%rbp)
    jmp .L37
.L38:
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
    jz .L42
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call map_grow
.L42:
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
    jz .L44
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
.L44:
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
    jz .L46
    mov $0, %rax
    leave
    ret
.L46:
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
    jz .L48
    mov $0, %rax
    leave
    ret
.L48:
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
.L49:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L50
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
    jmp .L49
.L50:
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
.L51:
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
    jz .L52
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L51
.L52:
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
.L53:
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
    jz .L55
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
.L55:
    test %rax, %rax
    jz .L54
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
    jz .L57
    mov $0, %rax
    leave
    ret
.L57:
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
    jmp .L53
.L54:
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
    jz .L59
    mov $1, %rax
    leave
    ret
.L59:
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
    jz .L61
    xor %rax, %rax
    leave
    ret
.L61:
    mov $0, %rax
    mov %rax, -40(%rbp)
.L62:
    mov -40(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L63
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
    jz .L65
    xor %rax, %rax
    leave
    ret
.L65:
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -40(%rbp)
    jmp .L62
.L63:
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
.L66:
    mov -48(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L67
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
    jmp .L66
.L67:
    mov $0, %rax
    mov %rax, -56(%rbp)
.L68:
    mov -56(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L69
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
    jmp .L68
.L69:
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
.L70:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
    test %rax, %rax
    jz .L71
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
    jmp .L70
.L71:
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
    jz .L73
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
.L73:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L75
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
.L75:
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
.L76:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L77
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
    jmp .L76
.L77:
.L78:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L79
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
    jmp .L78
.L79:
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
    jz .L81
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
.L81:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L83
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
.L83:
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
.L84:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L85
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
    jmp .L84
.L85:
.L86:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L87
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
    jmp .L86
.L87:
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
    jz .L89
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -24(%rbp)
.L90:
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
    jz .L91
    mov -24(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -24(%rbp)
    jmp .L90
.L91:
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
.L92:
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
    jz .L93
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
    jmp .L92
.L93:
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
.L89:
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
.L94:
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
    jz .L95
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
    jmp .L94
.L95:
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
    jz .L97
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
.L97:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L99
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
.L99:
    mov -16(%rbp), %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L100:
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L101
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
    jmp .L100
.L101:
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -40(%rbp)
.L102:
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L103
    mov $1, %rax
    mov %rax, -48(%rbp)
    mov $0, %rax
    mov %rax, -56(%rbp)
.L104:
    mov -56(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L105
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
    jmp .L104
.L105:
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
    jmp .L102
.L103:
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
.L106:
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L107
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L109
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
.L109:
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
    jmp .L106
.L107:
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
.L110:
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
    jz .L111
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
    jz .L112
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
    jmp .L113
.L112:
    mov -24(%rbp), %rax
    push %rax
    mov $92, %rax
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
    mov $92, %rax
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
    mov $10, %rax
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
    mov $110, %rax
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
    mov $13, %rax
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
    mov $114, %rax
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
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L120
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
    jmp .L121
.L120:
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
.L121:
.L119:
.L117:
.L115:
.L113:
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -8(%rbp)
    jmp .L110
.L111:
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
    jz .L122
    mov -8(%rbp), %rax
    push %rax
    mov $57, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L122:
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
    jz .L125
    mov -8(%rbp), %rax
    push %rax
    mov $90, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L125:
    test %rax, %rax
    jnz .L124
    mov -8(%rbp), %rax
    push %rax
    mov $97, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L126
    mov -8(%rbp), %rax
    push %rax
    mov $122, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L126:
.L124:
    test %rax, %rax
    jnz .L123
    mov -8(%rbp), %rax
    push %rax
    mov $95, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L123:
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
    jnz .L127
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
.L127:
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
    jnz .L130
    mov -8(%rbp), %rax
    push %rax
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L130:
    test %rax, %rax
    jnz .L129
    mov -8(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L129:
    test %rax, %rax
    jnz .L128
    mov -8(%rbp), %rax
    push %rax
    mov $13, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L128:
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
    jz .L132
    mov $0, %rax
    leave
    ret
.L132:
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
    jz .L134
    mov $0, %rax
    leave
    ret
.L134:
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
    jz .L136
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
.L136:
    xor %rax, %rax
    leave
    ret

.globl tok_skip_whitespace
tok_skip_whitespace:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
.L137:
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
    jz .L139
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_space
.L139:
    test %rax, %rax
    jz .L138
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L137
.L138:
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
    jz .L141
    mov TOK_EOF(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L141:
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
    jz .L143
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
.L143:
    mov -16(%rbp), %rax
    push %rax
    mov $41, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L145
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
.L145:
    mov -16(%rbp), %rax
    push %rax
    mov $91, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L147
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
.L147:
    mov -16(%rbp), %rax
    push %rax
    mov $93, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L149
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
.L149:
    mov -16(%rbp), %rax
    push %rax
    mov $123, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L151
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
.L151:
    mov -16(%rbp), %rax
    push %rax
    mov $125, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L153
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
.L153:
    mov -16(%rbp), %rax
    push %rax
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L155
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
.L155:
    mov -16(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L157
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
.L157:
    mov -16(%rbp), %rax
    push %rax
    mov $47, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L159
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
.L159:
    mov -16(%rbp), %rax
    push %rax
    mov $37, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L161
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
.L161:
    mov -16(%rbp), %rax
    push %rax
    mov $44, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L163
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
.L163:
    mov -16(%rbp), %rax
    push %rax
    mov $58, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L165
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
.L165:
    mov -16(%rbp), %rax
    push %rax
    mov $59, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L167
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
.L167:
    mov -16(%rbp), %rax
    push %rax
    mov $46, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L169
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
.L169:
    mov -16(%rbp), %rax
    push %rax
    mov $61, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L171
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
.L171:
    mov -16(%rbp), %rax
    push %rax
    mov $60, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L173
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
.L173:
    mov -16(%rbp), %rax
    push %rax
    mov $62, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L175
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
.L175:
    mov -16(%rbp), %rax
    push %rax
    mov $33, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L177
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
.L177:
    mov -16(%rbp), %rax
    push %rax
    mov $38, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L179
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
.L179:
    mov -16(%rbp), %rax
    push %rax
    mov $124, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L181
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
.L181:
    mov -16(%rbp), %rax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L183
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
    jz .L185
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L186:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L187
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L186
.L187:
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
.L185:
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
.L183:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L189
.L190:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L191
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L190
.L191:
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
.L189:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
    test %rax, %rax
    jz .L193
.L194:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_alnum
    test %rax, %rax
    jz .L195
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L194
.L195:
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
.L193:
    mov -16(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L197
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L198:
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
    jz .L200
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
.L200:
    test %rax, %rax
    jz .L199
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
    jz .L202
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L202:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L198
.L199:
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
    jz .L204
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L204:
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
.L197:
    mov -16(%rbp), %rax
    push %rax
    mov $39, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L206
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L207:
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
    jz .L209
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
.L209:
    test %rax, %rax
    jz .L208
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
    jz .L211
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L211:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L207
.L208:
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
    jz .L213
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L213:
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
.L206:
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
.L214:
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
    jz .L215
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
    jmp .L214
.L215:
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
    jz .L218
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L218:
    test %rax, %rax
    jz .L217
    mov $1, %rax
    mov %rax, -32(%rbp)
    mov $1, %rax
    mov %rax, -40(%rbp)
.L217:
    mov $0, %rax
    mov %rax, -48(%rbp)
.L219:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L220
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
    jmp .L219
.L220:
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L222
    mov $0, %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    leave
    ret
.L222:
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
.L223:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L224
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
    jz .L227
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
.L227:
    test %rax, %rax
    jz .L226
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
    jz .L228
    mov $10, %rax
    mov %rax, -56(%rbp)
    jmp .L229
.L228:
    mov -64(%rbp), %rax
    push %rax
    mov $114, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L230
    mov $13, %rax
    mov %rax, -56(%rbp)
    jmp .L231
.L230:
    mov -64(%rbp), %rax
    push %rax
    mov $116, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L232
    mov $9, %rax
    mov %rax, -56(%rbp)
    jmp .L233
.L232:
    mov -64(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L234
    mov $34, %rax
    mov %rax, -56(%rbp)
    jmp .L235
.L234:
    mov -64(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L236
    mov $92, %rax
    mov %rax, -56(%rbp)
    jmp .L237
.L236:
    mov -64(%rbp), %rax
    mov %rax, -56(%rbp)
.L237:
.L235:
.L233:
.L231:
.L229:
.L226:
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
    jmp .L223
.L224:
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
    jz .L239
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
    leave
    ret
.L239:
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
    jz .L241
    xor %rax, %rax
    leave
    ret
.L241:
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
    jz .L243
    xor %rax, %rax
    leave
    ret
.L243:
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
    jz .L244
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
    jmp .L245
.L244:
    lea .str6(%rip), %rax
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
    jmp .L247
.L246:
    lea .str8(%rip), %rax
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
    jmp .L249
.L248:
    lea .str10(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L250
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
    jmp .L251
.L250:
    lea .str12(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L252
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
    jmp .L253
.L252:
    lea .str14(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call gp_is_keyword
    test %rax, %rax
    jz .L254
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
    jmp .L255
.L254:
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
    jz .L256
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
    jz .L259
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
.L259:
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
    jmp .L257
.L256:
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
    jz .L260
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
    jz .L263
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_next
.L263:
    jmp .L261
.L260:
    xor %rax, %rax
    leave
    ret
.L261:
.L257:
.L255:
.L253:
.L251:
.L249:
.L247:
.L245:
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
    jz .L264
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
    jmp .L265
.L264:
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
    jz .L266
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
    jmp .L267
.L266:
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
    jz .L269
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
    jz .L271
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
.L271:
.L269:
.L267:
.L265:
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
.L272:
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L273
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
    jz .L274
    mov $1, %rax
    mov %rax, -24(%rbp)
    jmp .L275
.L274:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L275:
    jmp .L272
.L273:
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
    jz .L277
    xor %rax, %rax
    leave
    ret
.L277:
    mov -40(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L279
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    leave
    ret
.L279:
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
    jz .L281
    xor %rax, %rax
    leave
    ret
.L281:
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L282:
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
    jz .L283
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
    jz .L285
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L285:
    jmp .L282
.L283:
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
    jz .L287
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    leave
    ret
.L287:
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
    jz .L289
    xor %rax, %rax
    leave
    ret
.L289:
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
    jz .L291
    xor %rax, %rax
    leave
    ret
.L291:
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
    jz .L293
    xor %rax, %rax
    leave
    ret
.L293:
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
.L294:
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call tok_eof
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L296
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L296:
    test %rax, %rax
    jz .L295
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
    jz .L297
    mov $1, %rax
    mov %rax, -32(%rbp)
    jmp .L298
.L297:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call grammar_add_rule
.L298:
    jmp .L294
.L295:
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
.L299:
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
    jz .L300
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
    jmp .L299
.L300:
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
.L301:
    mov -32(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L302
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
    jmp .L301
.L302:
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
    jz .L304
    xor %rax, %rax
    leave
    ret
.L304:
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
.L305:
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
    jz .L306
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
    jz .L307
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
    jz .L310
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
    jz .L311
    lea .str40(%rip), %rax
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
    mov $41, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L313
    lea .str41(%rip), %rax
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
    mov $91, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L315
    lea .str42(%rip), %rax
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
    mov $93, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L317
    lea .str43(%rip), %rax
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
    mov $123, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L319
    lea .str44(%rip), %rax
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
    mov $125, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L321
    lea .str45(%rip), %rax
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
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L323
    lea .str46(%rip), %rax
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
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L325
    lea .str47(%rip), %rax
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
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L327
    lea .str48(%rip), %rax
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
    mov $47, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L329
    lea .str49(%rip), %rax
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
    mov $44, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L331
    lea .str50(%rip), %rax
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
    mov $46, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L333
    lea .str51(%rip), %rax
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
    mov $61, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L335
    lea .str52(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L336
.L335:
    mov -96(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_int
.L336:
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
.L310:
    jmp .L308
.L307:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_TOKTYPE(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L337
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
    jz .L339
    lea .str57(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L340
.L339:
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
    jz .L341
    lea .str59(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L342
.L341:
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
    jz .L343
    lea .str61(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L344
.L343:
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
    jz .L345
    lea .str63(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L346
.L345:
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
    jz .L348
    lea .str65(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L348:
.L346:
.L344:
.L342:
.L340:
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
    jz .L349
    lea .str69(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L350
.L349:
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
    jz .L351
    lea .str71(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L352
.L351:
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
    jz .L353
    lea .str73(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L354
.L353:
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
    jz .L355
    lea .str75(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    jmp .L356
.L355:
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
    jz .L358
    lea .str77(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L358:
.L356:
.L354:
.L352:
.L350:
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
    jmp .L338
.L337:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_REF(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L359
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
    jmp .L360
.L359:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_SEQ(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L361
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
    jz .L363
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
    jz .L366
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
.L366:
    jmp .L364
.L363:
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
    jz .L368
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
.L368:
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
    jz .L369
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
    jmp .L370
.L369:
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
.L370:
.L364:
    jmp .L362
.L361:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_CHOICE(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L371
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
    jz .L373
    mov -64(%rbp), %rax
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
.L376:
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
    jmp .L374
.L373:
    mov -176(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -192(%rbp)
.L377:
    mov -192(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L378
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
    jmp .L377
.L378:
.L374:
    jmp .L372
.L371:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_STAR(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L379
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
    jz .L381
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
    jmp .L382
.L381:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L384
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
.L384:
.L382:
    jmp .L380
.L379:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_PLUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L385
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
    jz .L387
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
    jmp .L388
.L387:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L389
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
    jmp .L390
.L389:
    mov -64(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L392
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
.L392:
.L390:
.L388:
    jmp .L386
.L385:
    mov -72(%rbp), %rax
    push %rax
    mov GNODE_OPT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L394
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
.L394:
.L386:
.L380:
.L372:
.L362:
.L360:
.L338:
.L308:
    jmp .L305
.L306:
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
.L395:
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L396
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
    jmp .L395
.L396:
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
    jz .L398
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
.L398:
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
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
    call tok_kind
    push %rax
    mov TOK_IDENT(%rip), %rax
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
.L402:
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L404
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
    jnz .L412
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
.L412:
    test %rax, %rax
    jnz .L411
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
.L411:
    test %rax, %rax
    jnz .L410
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
.L410:
    test %rax, %rax
    jnz .L409
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_PERCENT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L409:
    test %rax, %rax
    jnz .L408
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_LT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L408:
    test %rax, %rax
    jnz .L407
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    mov TOK_GT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L407:
    test %rax, %rax
    jz .L406
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
.L406:
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L414
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call parse_list
    mov %rax, -16(%rbp)
.L414:
.L404:
.L400:
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
    jz .L416
    mov $0, %rax
    push %rax
    pop %rdi
    call pnode_new
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L416:
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L418
    xor %rax, %rax
    leave
    ret
.L418:
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L420
    mov -32(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L420:
    xor %rax, %rax
    mov %rax, -40(%rbp)
    mov $8, %rax
    push %rax
    pop %rdi
    call vec_new
    mov %rax, -48(%rbp)
    mov $0, %rax
    mov %rax, -56(%rbp)
.L421:
    mov -56(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L422
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
    jz .L424
    mov $1, %rax
    mov %rax, -56(%rbp)
.L424:
    mov -64(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L426
    mov -64(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L426:
    jmp .L421
.L422:
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
    jz .L428
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L428:
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
    jz .L430
    mov $0, %rax
    push %rax
    pop %rdi
    call pnode_new
    mov %rax, -72(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L430:
    mov -72(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L432
    mov -72(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L432:
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call pnode_list
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    leave
    ret

.globl lisp_to_lang
lisp_to_lang:
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
    jz .L434
    lea .str125(%rip), %rax
    leave
    ret
.L434:
    call sb_new
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call sb_finish
    leave
    ret

.globl list_inner
list_inner:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $1, %rax
    push %rax
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    leave
    ret

.globl list_get
list_get:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call list_inner
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_get
    leave
    ret

.globl list_len
list_len:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call list_inner
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    call vec_len
    leave
    ret

.globl is_symbol
is_symbol:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L436
    xor %rax, %rax
    leave
    ret
.L436:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L438
    xor %rax, %rax
    leave
    ret
.L438:
    mov -16(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    leave
    ret

.globl is_comparison
is_comparison:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    lea .str126(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L440
    mov $1, %rax
    leave
    ret
.L440:
    lea .str127(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L442
    mov $1, %rax
    leave
    ret
.L442:
    lea .str128(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L444
    mov $1, %rax
    leave
    ret
.L444:
    lea .str129(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L446
    mov $1, %rax
    leave
    ret
.L446:
    lea .str130(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L448
    mov $1, %rax
    leave
    ret
.L448:
    lea .str131(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L450
    mov $1, %rax
    leave
    ret
.L450:
    xor %rax, %rax
    leave
    ret

.globl comparison_op
comparison_op:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    lea .str132(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L452
    lea .str133(%rip), %rax
    leave
    ret
.L452:
    lea .str134(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L454
    lea .str135(%rip), %rax
    leave
    ret
.L454:
    mov -8(%rbp), %rax
    leave
    ret

.globl is_arith
is_arith:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    lea .str136(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L456
    mov $1, %rax
    leave
    ret
.L456:
    lea .str137(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L458
    mov $1, %rax
    leave
    ret
.L458:
    lea .str138(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L460
    mov $1, %rax
    leave
    ret
.L460:
    lea .str139(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L462
    mov $1, %rax
    leave
    ret
.L462:
    lea .str140(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L464
    mov $1, %rax
    leave
    ret
.L464:
    xor %rax, %rax
    leave
    ret

.globl is_if_expr
is_if_expr:
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
    jz .L466
    xor %rax, %rax
    leave
    ret
.L466:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L468
    xor %rax, %rax
    leave
    ret
.L468:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call list_len
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L470
    xor %rax, %rax
    leave
    ret
.L470:
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -16(%rbp)
    lea .str141(%rip), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call is_symbol
    leave
    ret

.globl lisp_emit
lisp_emit:
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
    jz .L472
    lea .str142(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L472:
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
    jz .L474
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
.L474:
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
    jz .L476
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
.L476:
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
    jz .L478
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
.L478:
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
    jz .L480
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call list_len
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L482
    lea .str143(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L482:
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
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
    jz .L484
    lea .str144(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L484:
    lea .str145(%rip), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call is_symbol
    test %rax, %rax
    jz .L486
    mov -24(%rbp), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L488
    lea .str146(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L488:
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -40(%rbp)
    mov $2, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -48(%rbp)
    mov $3, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -56(%rbp)
    lea .str147(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -40(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str148(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    call list_len
    mov %rax, -64(%rbp)
    mov $0, %rax
    mov %rax, -72(%rbp)
.L489:
    mov -72(%rbp), %rax
    push %rax
    mov -64(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L490
    mov -72(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L492
    lea .str149(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L492:
    mov -72(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -80(%rbp)
    mov -80(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str150(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -72(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -72(%rbp)
    jmp .L489
.L490:
    lea .str151(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -56(%rbp), %rax
    push %rax
    pop %rdi
    call is_if_expr
    test %rax, %rax
    jz .L493
    lea .str152(%rip), %rax
    push %rax
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call lisp_emit_if_body
    jmp .L494
.L493:
    lea .str153(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -56(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str154(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L494:
    lea .str155(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L486:
    lea .str156(%rip), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call is_symbol
    test %rax, %rax
    jz .L496
    mov -24(%rbp), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L498
    lea .str157(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L498:
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -88(%rbp)
    mov $2, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -96(%rbp)
    mov $3, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -104(%rbp)
    lea .str158(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -88(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str159(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -96(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str160(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -88(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str161(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -104(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str162(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L496:
    lea .str163(%rip), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call is_symbol
    test %rax, %rax
    jz .L500
    lea .str164(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    mov %rax, -112(%rbp)
.L501:
    mov -112(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L502
    mov -112(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L504
    lea .str165(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L504:
    mov -112(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    mov -112(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -112(%rbp)
    jmp .L501
.L502:
    lea .str166(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L500:
    lea .str167(%rip), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call is_symbol
    test %rax, %rax
    jz .L506
    lea .str168(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    mov %rax, -120(%rbp)
.L507:
    mov -120(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L508
    mov -120(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L510
    lea .str169(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L510:
    mov -120(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    mov -120(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -120(%rbp)
    jmp .L507
.L508:
    lea .str170(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L506:
    lea .str171(%rip), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call is_symbol
    test %rax, %rax
    jz .L512
    lea .str172(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str173(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L512:
    mov -32(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L515
    mov -32(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    pop %rdi
    call is_comparison
.L515:
    test %rax, %rax
    jz .L514
    mov -24(%rbp), %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L517
    lea .str174(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L517:
    lea .str175(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str176(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -32(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    pop %rdi
    call comparison_op
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str177(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $2, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str178(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L514:
    xor %rax, %rax
    mov %rax, -128(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L518
    mov -32(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -128(%rbp)
    jmp .L519
.L518:
    mov -32(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L522
    mov -32(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    pop %rdi
    call is_arith
.L522:
    test %rax, %rax
    jz .L521
    mov -32(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, -128(%rbp)
.L521:
.L519:
    mov -128(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L524
    mov -24(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L526
    mov -32(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    xor %rax, %rax
    leave
    ret
.L526:
    mov -24(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L528
    lea .str179(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
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
    call sb_str
    lea .str180(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str181(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L528:
    lea .str182(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    mov $2, %rax
    mov %rax, -136(%rbp)
.L529:
    mov -136(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L530
    lea .str183(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
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
    call sb_str
    lea .str184(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -136(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    mov -136(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -136(%rbp)
    jmp .L529
.L530:
    lea .str185(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L524:
    mov -32(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L532
    mov -32(%rbp), %rax
    mov 8(%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str186(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov $1, %rax
    mov %rax, -144(%rbp)
.L533:
    mov -144(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L534
    mov -144(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L536
    lea .str187(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L536:
    mov -144(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    mov -144(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -144(%rbp)
    jmp .L533
.L534:
    lea .str188(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L532:
    lea .str189(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret
.L480:
    lea .str190(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    xor %rax, %rax
    leave
    ret

.globl lisp_emit_if_body
lisp_emit_if_body:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov $1, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -32(%rbp)
    mov $2, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -40(%rbp)
    mov $3, %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call list_get
    mov %rax, -48(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str191(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -32(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str192(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str193(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -40(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call lisp_emit
    lea .str194(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str195(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    call is_if_expr
    test %rax, %rax
    jz .L537
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str196(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str197(%rip), %rax
    push %rax
    mov -48(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call lisp_emit_if_body
    jmp .L538
.L537:
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
    lea .str198(%rip), %rax
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
    call lisp_emit
    lea .str199(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_str
.L538:
    xor %rax, %rax
    leave
    ret

.globl add
add:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

.globl square
square:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    leave
    ret

.globl abs
abs:
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
    jz .L540
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    leave
    ret
.L540:
    mov -8(%rbp), %rax
    leave
    ret

.globl max
max:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L542
    mov -8(%rbp), %rax
    leave
    ret
.L542:
    mov -16(%rbp), %rax
    leave
    ret

.globl factorial
factorial:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L544
    mov $1, %rax
    leave
    ret
.L544:
    mov -8(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    pop %rdi
    call factorial
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $4, %rax
    push %rax
    mov $3, %rax
    push %rax
    pop %rdi
    pop %rsi
    call add
    mov %rax, -8(%rbp)
    lea .str200(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str201(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov -8(%rbp), %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L546
    mov $1, %rax
    leave
    ret
.L546:
    mov $5, %rax
    push %rax
    pop %rdi
    call square
    mov %rax, -16(%rbp)
    lea .str202(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str203(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov -16(%rbp), %rax
    push %rax
    mov $25, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L548
    mov $2, %rax
    leave
    ret
.L548:
    mov $10, %rax
    push %rax
    pop %rdi
    call abs
    mov %rax, -24(%rbp)
    mov $10, %rax
    neg %rax
    push %rax
    pop %rdi
    call abs
    mov %rax, -32(%rbp)
    lea .str204(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str205(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str206(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L550
    mov $3, %rax
    leave
    ret
.L550:
    mov -32(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L552
    mov $4, %rax
    leave
    ret
.L552:
    mov $7, %rax
    push %rax
    mov $3, %rax
    push %rax
    pop %rdi
    pop %rsi
    call max
    mov %rax, -40(%rbp)
    mov $3, %rax
    push %rax
    mov $7, %rax
    push %rax
    pop %rdi
    pop %rsi
    call max
    mov %rax, -48(%rbp)
    lea .str207(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -40(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str208(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -48(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str209(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov -40(%rbp), %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L554
    mov $5, %rax
    leave
    ret
.L554:
    mov -48(%rbp), %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L556
    mov $6, %rax
    leave
    ret
.L556:
    mov $5, %rax
    push %rax
    pop %rdi
    call factorial
    mov %rax, -56(%rbp)
    lea .str210(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -56(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str211(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov -56(%rbp), %rax
    push %rax
    mov $120, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L558
    mov $7, %rax
    leave
    ret
.L558:
    mov $4, %rax
    push %rax
    pop %rdi
    call square
    push %rax
    mov $3, %rax
    push %rax
    pop %rdi
    call square
    push %rax
    pop %rdi
    pop %rsi
    call add
    mov %rax, -64(%rbp)
    lea .str212(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -64(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str213(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov -64(%rbp), %rax
    push %rax
    mov $25, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L560
    mov $8, %rax
    leave
    ret
.L560:
    lea .str214(%rip), %rax
    push %rax
    pop %rdi
    call println
    mov $0, %rax
    leave
    ret

