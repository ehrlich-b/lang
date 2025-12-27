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
    .ascii "1 2 3 4 5\000"
.str7:
    .ascii "FAIL: result is nil\012\000"
.str8:
    .ascii "FAIL: expected 5 numbers, got \000"
.str9:
    .ascii "\012\000"
.str10:
    .ascii "PASS: parser_precompiled_test - \000"
.str11:
    .ascii " numbers parsed\012\000"
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
    jz .L86
    mov -8(%rbp), %rax
    push %rax
    mov $57, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L86:
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
    jz .L89
    mov -8(%rbp), %rax
    push %rax
    mov $90, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L89:
    test %rax, %rax
    jnz .L88
    mov -8(%rbp), %rax
    push %rax
    mov $97, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L90
    mov -8(%rbp), %rax
    push %rax
    mov $122, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
.L90:
.L88:
    test %rax, %rax
    jnz .L87
    mov -8(%rbp), %rax
    push %rax
    mov $95, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L87:
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
    jnz .L91
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
.L91:
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
    jnz .L94
    mov -8(%rbp), %rax
    push %rax
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L94:
    test %rax, %rax
    jnz .L93
    mov -8(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L93:
    test %rax, %rax
    jnz .L92
    mov -8(%rbp), %rax
    push %rax
    mov $13, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L92:
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
    jz .L96
    mov $0, %rax
    leave
    ret
.L96:
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
    jz .L98
    mov $0, %rax
    leave
    ret
.L98:
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
    jz .L100
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
.L100:
    xor %rax, %rax
    leave
    ret

.globl tok_skip_whitespace
tok_skip_whitespace:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
.L101:
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
    jz .L103
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_space
.L103:
    test %rax, %rax
    jz .L102
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L101
.L102:
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
    jz .L105
    mov TOK_EOF(%rip), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L105:
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
    jz .L107
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
.L107:
    mov -16(%rbp), %rax
    push %rax
    mov $41, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L109
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
.L109:
    mov -16(%rbp), %rax
    push %rax
    mov $91, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L111
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
.L111:
    mov -16(%rbp), %rax
    push %rax
    mov $93, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L113
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
.L113:
    mov -16(%rbp), %rax
    push %rax
    mov $123, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L115
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
.L115:
    mov -16(%rbp), %rax
    push %rax
    mov $125, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L117
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
.L117:
    mov -16(%rbp), %rax
    push %rax
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L119
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
.L119:
    mov -16(%rbp), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L121
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
.L121:
    mov -16(%rbp), %rax
    push %rax
    mov $47, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L123
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
.L123:
    mov -16(%rbp), %rax
    push %rax
    mov $37, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L125
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
.L125:
    mov -16(%rbp), %rax
    push %rax
    mov $44, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L127
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
.L127:
    mov -16(%rbp), %rax
    push %rax
    mov $58, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L129
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
.L129:
    mov -16(%rbp), %rax
    push %rax
    mov $59, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L131
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
.L131:
    mov -16(%rbp), %rax
    push %rax
    mov $46, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L133
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
.L133:
    mov -16(%rbp), %rax
    push %rax
    mov $61, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L135
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
.L135:
    mov -16(%rbp), %rax
    push %rax
    mov $60, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L137
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
.L137:
    mov -16(%rbp), %rax
    push %rax
    mov $62, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L139
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
.L139:
    mov -16(%rbp), %rax
    push %rax
    mov $33, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L141
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
.L141:
    mov -16(%rbp), %rax
    push %rax
    mov $38, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L143
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
.L143:
    mov -16(%rbp), %rax
    push %rax
    mov $124, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L145
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
.L145:
    mov -16(%rbp), %rax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L147
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
    jz .L149
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L150:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L151
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L150
.L151:
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
.L149:
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
.L147:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L153
.L154:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_digit
    test %rax, %rax
    jz .L155
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L154
.L155:
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
.L153:
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call tok_is_alpha
    test %rax, %rax
    jz .L157
.L158:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    push %rax
    pop %rdi
    call tok_is_alnum
    test %rax, %rax
    jz .L159
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L158
.L159:
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
.L157:
    mov -16(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L161
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L162:
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
    jz .L164
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
.L164:
    test %rax, %rax
    jz .L163
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
    jz .L166
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L166:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L162
.L163:
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
    jz .L168
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L168:
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
.L161:
    mov -16(%rbp), %rax
    push %rax
    mov $39, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L170
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L171:
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
    jz .L173
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
.L173:
    test %rax, %rax
    jz .L172
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
    jz .L175
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L175:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
    jmp .L171
.L172:
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
    jz .L177
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_advance_char
.L177:
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
.L170:
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
.L178:
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
    jz .L179
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
    jmp .L178
.L179:
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
    jz .L182
    mov -16(%rbp), %rax
    movzbl (%rax), %eax
    push %rax
    mov $45, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
.L182:
    test %rax, %rax
    jz .L181
    mov $1, %rax
    mov %rax, -32(%rbp)
    mov $1, %rax
    mov %rax, -40(%rbp)
.L181:
    mov $0, %rax
    mov %rax, -48(%rbp)
.L183:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L184
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
    jmp .L183
.L184:
    mov -32(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L186
    mov $0, %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    leave
    ret
.L186:
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
.L187:
    mov -40(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L188
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
    jz .L191
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
.L191:
    test %rax, %rax
    jz .L190
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
    jz .L192
    mov $10, %rax
    mov %rax, -56(%rbp)
    jmp .L193
.L192:
    mov -64(%rbp), %rax
    push %rax
    mov $114, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L194
    mov $13, %rax
    mov %rax, -56(%rbp)
    jmp .L195
.L194:
    mov -64(%rbp), %rax
    push %rax
    mov $116, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L196
    mov $9, %rax
    mov %rax, -56(%rbp)
    jmp .L197
.L196:
    mov -64(%rbp), %rax
    push %rax
    mov $34, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L198
    mov $34, %rax
    mov %rax, -56(%rbp)
    jmp .L199
.L198:
    mov -64(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L200
    mov $92, %rax
    mov %rax, -56(%rbp)
    jmp .L201
.L200:
    mov -64(%rbp), %rax
    mov %rax, -56(%rbp)
.L201:
.L199:
.L197:
.L195:
.L193:
.L190:
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
    jmp .L187
.L188:
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
    jz .L203
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
    leave
    ret
.L203:
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
    jz .L205
    xor %rax, %rax
    leave
    ret
.L205:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    mov $1, %rax
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

.globl parse_nums
parse_nums:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    xor %rax, %rax
    mov %rax, -16(%rbp)
    mov $8, %rax
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
    mov TOK_NUMBER(%rip), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L207
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
    mov %rax, -32(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L207:
    mov -32(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L209
    xor %rax, %rax
    leave
    ret
.L209:
    mov -32(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    mov $0, %rax
    mov %rax, -40(%rbp)
.L210:
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L211
    xor %rax, %rax
    mov %rax, -48(%rbp)
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
    jz .L213
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
    mov %rax, -48(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
.L213:
    mov -48(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L215
    mov $1, %rax
    mov %rax, -40(%rbp)
.L215:
    mov -48(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L217
    mov -48(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
.L217:
    jmp .L210
.L211:
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call pnode_list
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    lea .str6(%rip), %rax
    push %rax
    pop %rdi
    call tok_new
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call parse_nums
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    xor %rax, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L219
    lea .str7(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $1, %rax
    leave
    ret
.L219:
    mov -16(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    pop %rdi
    call vec_len
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L221
    lea .str8(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str9(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $2, %rax
    leave
    ret
.L221:
    lea .str10(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str11(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $0, %rax
    leave
    ret

