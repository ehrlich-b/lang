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
    .ascii "EOF\000"
.str7:
    .ascii "NUMBER\000"
.str8:
    .ascii "IDENT\000"
.str9:
    .ascii "STRING\000"
.str10:
    .ascii "LPAREN\000"
.str11:
    .ascii "RPAREN\000"
.str12:
    .ascii "PLUS\000"
.str13:
    .ascii "MINUS\000"
.str14:
    .ascii "STAR\000"
.str15:
    .ascii "SLASH\000"
.str16:
    .ascii "?\000"
.str17:
    .ascii "=== Tokenizer Test ===\012\012\000"
.str18:
    .ascii "Input: (+ 1 2)\012\000"
.str19:
    .ascii "(+ 1 2)\000"
.str20:
    .ascii "  \000"
.str21:
    .ascii ": \000"
.str22:
    .ascii "\012\000"
.str23:
    .ascii "\012\000"
.str24:
    .ascii "Input: (* (+ 1 2) 3)\012\000"
.str25:
    .ascii "(* (+ 1 2) 3)\000"
.str26:
    .ascii "  \000"
.str27:
    .ascii ": \000"
.str28:
    .ascii "\012\000"
.str29:
    .ascii "\012\000"
.str30:
    .ascii "Input: (- -5 3)\012\000"
.str31:
    .ascii "(- -5 3)\000"
.str32:
    .ascii "  \000"
.str33:
    .ascii ": \000"
.str34:
    .ascii " = \000"
.str35:
    .ascii "\012\000"
.str36:
    .ascii "\012\000"
.str37:
    .ascii "Input: (define x 42)\012\000"
.str38:
    .ascii "(define x 42)\000"
.str39:
    .ascii "  \000"
.str40:
    .ascii ": \000"
.str41:
    .ascii "\012\000"
.str42:
    .ascii "\012All tokenizer tests passed!\012\000"
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

.globl hash_str
hash_str:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $5381, %rax
    mov %rax, -16(%rbp)
.L19:
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
    jz .L20
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
    jmp .L19
.L20:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L22
    mov $0, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -16(%rbp)
.L22:
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
.L23:
    mov -48(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L24
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
    jmp .L23
.L24:
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
.L25:
    mov -64(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L26
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
    jz .L28
    mov -72(%rbp), %rax
    leave
    ret
.L28:
    mov -16(%rbp), %rax
    push %rax
    mov -88(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call streq
    test %rax, %rax
    jz .L30
    mov -72(%rbp), %rax
    leave
    ret
.L30:
    mov -64(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -64(%rbp)
    jmp .L25
.L26:
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
.L31:
    mov -96(%rbp), %rax
    push %rax
    mov -72(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L32
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
    jmp .L31
.L32:
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
.L33:
    mov -96(%rbp), %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L34
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
    jz .L36
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
.L36:
    mov -96(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -96(%rbp)
    jmp .L33
.L34:
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
    jz .L38
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call map_grow
.L38:
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
    jz .L40
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
.L40:
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
    jz .L42
    mov $0, %rax
    leave
    ret
.L42:
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
    jz .L44
    mov $0, %rax
    leave
    ret
.L44:
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
.L45:
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
    jz .L46
    mov -16(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    jmp .L45
.L46:
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
.L47:
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
    jz .L49
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
.L49:
    test %rax, %rax
    jz .L48
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
    jz .L51
    mov $0, %rax
    leave
    ret
.L51:
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
    jmp .L47
.L48:
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
    jz .L53
    mov $1, %rax
    leave
    ret
.L53:
    mov $0, %rax
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
.L54:
    mov -48(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L55
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
    jmp .L54
.L55:
    mov $0, %rax
    mov %rax, -56(%rbp)
.L56:
    mov -56(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L57
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
    jmp .L56
.L57:
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
.L58:
    mov -32(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
    test %rax, %rax
    jz .L59
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
    jmp .L58
.L59:
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
    jz .L61
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
.L61:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L63
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
.L63:
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
.L64:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L65
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
    jmp .L64
.L65:
.L66:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L67
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
    jmp .L66
.L67:
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
    jz .L69
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
.L69:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L71
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
.L71:
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    mov %rax, -24(%rbp)
.L72:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L73
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
    jmp .L72
.L73:
.L74:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L75
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
    jmp .L74
.L75:
    xor %rax, %rax
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
    jz .L76
    mov -8(%rbp), %rax
    push %rax
    mov $57, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L76:
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
    jz .L79
    mov -8(%rbp), %rax
    push %rax
    mov $90, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L79:
    test %rax, %rax
    jnz .L78
    mov -8(%rbp), %rax
    push %rax
    mov $97, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L80
    mov -8(%rbp), %rax
    push %rax
    mov $122, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L80:
.L78:
    test %rax, %rax
    jnz .L77
    mov -8(%rbp), %rax
    push %rax
    mov $95, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L77:
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
    jnz .L81
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
.L81:
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
    jnz .L84
    mov -8(%rbp), %rax
    push %rax
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L84:
    test %rax, %rax
    jnz .L83
    mov -8(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L83:
    test %rax, %rax
    jnz .L82
    mov -8(%rbp), %rax
    push %rax
    mov $13, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L82:
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
    jz .L86
    mov $0, %rax
    leave
    ret
.L86:
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
    jz .L88
    mov $0, %rax
    leave
    ret
.L88:
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
    jz .L90
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
.L90:
    xor %rax, %rax
    leave
    ret

.globl tok_skip_whitespace
tok_skip_whitespace:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
.L91:
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
    jz .L93
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_space
.L93:
    test %rax, %rax
    jz .L92
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L91
.L92:
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
    jz .L95
    mov TOK_EOF(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L95:
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
    jz .L97
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
.L97:
    mov -16(%rbp), %rax
    push %rax
    mov $41, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L99
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
.L99:
    mov -16(%rbp), %rax
    push %rax
    mov $91, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L101
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
.L101:
    mov -16(%rbp), %rax
    push %rax
    mov $93, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L103
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
.L103:
    mov -16(%rbp), %rax
    push %rax
    mov $123, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L105
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
.L105:
    mov -16(%rbp), %rax
    push %rax
    mov $125, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L107
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
.L107:
    mov -16(%rbp), %rax
    push %rax
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L109
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
.L109:
    mov -16(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L111
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
.L111:
    mov -16(%rbp), %rax
    push %rax
    mov $47, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L113
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
.L113:
    mov -16(%rbp), %rax
    push %rax
    mov $37, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L115
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
.L115:
    mov -16(%rbp), %rax
    push %rax
    mov $44, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L117
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
.L117:
    mov -16(%rbp), %rax
    push %rax
    mov $58, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L119
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
.L119:
    mov -16(%rbp), %rax
    push %rax
    mov $59, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L121
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
.L121:
    mov -16(%rbp), %rax
    push %rax
    mov $46, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L123
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
.L123:
    mov -16(%rbp), %rax
    push %rax
    mov $61, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L125
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
.L125:
    mov -16(%rbp), %rax
    push %rax
    mov $60, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L127
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
.L127:
    mov -16(%rbp), %rax
    push %rax
    mov $62, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L129
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
.L129:
    mov -16(%rbp), %rax
    push %rax
    mov $33, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L131
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
.L131:
    mov -16(%rbp), %rax
    push %rax
    mov $38, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L133
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
.L133:
    mov -16(%rbp), %rax
    push %rax
    mov $124, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L135
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
.L135:
    mov -16(%rbp), %rax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L137
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
    jz .L139
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L140:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L141
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L140
.L141:
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
.L139:
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
.L137:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L143
.L144:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L145
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L144
.L145:
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
.L143:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
    test %rax, %rax
    jz .L147
.L148:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_alnum
    test %rax, %rax
    jz .L149
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L148
.L149:
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
.L147:
    mov -16(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L151
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L152:
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
    jz .L154
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
.L154:
    test %rax, %rax
    jz .L153
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
    jz .L156
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L156:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L152
.L153:
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
    jz .L158
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L158:
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
.L151:
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
.L159:
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
    jz .L160
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
    jmp .L159
.L160:
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
    jz .L163
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L163:
    test %rax, %rax
    jz .L162
    mov $1, %rax
    mov %rax, -32(%rbp)
    mov $1, %rax
    mov %rax, -40(%rbp)
.L162:
    mov $0, %rax
    mov %rax, -48(%rbp)
.L164:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L165
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
    jmp .L164
.L165:
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L167
    mov $0, %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    leave
    ret
.L167:
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
.L168:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L169
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
    jz .L172
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
.L172:
    test %rax, %rax
    jz .L171
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
    jz .L173
    mov $10, %rax
    mov %rax, -56(%rbp)
    jmp .L174
.L173:
    mov -64(%rbp), %rax
    push %rax
    mov $114, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L175
    mov $13, %rax
    mov %rax, -56(%rbp)
    jmp .L176
.L175:
    mov -64(%rbp), %rax
    push %rax
    mov $116, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L177
    mov $9, %rax
    mov %rax, -56(%rbp)
    jmp .L178
.L177:
    mov -64(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L179
    mov $34, %rax
    mov %rax, -56(%rbp)
    jmp .L180
.L179:
    mov -64(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L181
    mov $92, %rax
    mov %rax, -56(%rbp)
    jmp .L182
.L181:
    mov -64(%rbp), %rax
    mov %rax, -56(%rbp)
.L182:
.L180:
.L178:
.L176:
.L174:
.L171:
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
    jmp .L168
.L169:
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
    jz .L184
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
    leave
    ret
.L184:
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
    jz .L186
    xor %rax, %rax
    leave
    ret
.L186:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
    leave
    ret

.globl kind_name
kind_name:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov TOK_EOF(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L188
    lea .str6(%rip), %rax
    leave
    ret
.L188:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_NUMBER(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L190
    lea .str7(%rip), %rax
    leave
    ret
.L190:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_IDENT(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L192
    lea .str8(%rip), %rax
    leave
    ret
.L192:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_STRING(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L194
    lea .str9(%rip), %rax
    leave
    ret
.L194:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_LPAREN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L196
    lea .str10(%rip), %rax
    leave
    ret
.L196:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_RPAREN(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L198
    lea .str11(%rip), %rax
    leave
    ret
.L198:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_PLUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L200
    lea .str12(%rip), %rax
    leave
    ret
.L200:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_MINUS(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L202
    lea .str13(%rip), %rax
    leave
    ret
.L202:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_STAR(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L204
    lea .str14(%rip), %rax
    leave
    ret
.L204:
    mov -8(%rbp), %rax
    push %rax
    mov TOK_SLASH(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L206
    lea .str15(%rip), %rax
    leave
    ret
.L206:
    lea .str16(%rip), %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    lea .str17(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str18(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str19(%rip), %rax
    push %rax
    pop %rdi
    call tok_new
    mov %rax, -8(%rbp)
.L207:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_eof
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L208
    lea .str20(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    pop %rdi
    call kind_name
    push %rax
    pop %rdi
    call print
    lea .str21(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    pop %rdi
    call print
    lea .str22(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L207
.L208:
    lea .str23(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str24(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str25(%rip), %rax
    push %rax
    pop %rdi
    call tok_new
    mov %rax, -8(%rbp)
.L209:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_eof
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L210
    lea .str26(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    pop %rdi
    call kind_name
    push %rax
    pop %rdi
    call print
    lea .str27(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    pop %rdi
    call print
    lea .str28(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L209
.L210:
    lea .str29(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str30(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str31(%rip), %rax
    push %rax
    pop %rdi
    call tok_new
    mov %rax, -8(%rbp)
.L211:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_eof
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L212
    lea .str32(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    pop %rdi
    call kind_name
    push %rax
    pop %rdi
    call print
    lea .str33(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    pop %rdi
    call print
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
    jz .L214
    lea .str34(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_number
    push %rax
    pop %rdi
    call print_int
.L214:
    lea .str35(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L211
.L212:
    lea .str36(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str37(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str38(%rip), %rax
    push %rax
    pop %rdi
    call tok_new
    mov %rax, -8(%rbp)
.L215:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_eof
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L216
    lea .str39(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_kind
    push %rax
    pop %rdi
    call kind_name
    push %rax
    pop %rdi
    call print
    lea .str40(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_text
    push %rax
    pop %rdi
    call print
    lea .str41(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    jmp .L215
.L216:
    lea .str42(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $0, %rax
    leave
    ret

