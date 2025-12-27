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
    .ascii "emit_number(42) = \000"
.str7:
    .ascii "\012\000"
.str8:
    .ascii "emit_number(-17) = \000"
.str9:
    .ascii "\012\000"
.str10:
    .ascii "2\000"
.str11:
    .ascii "+\000"
.str12:
    .ascii "1\000"
.str13:
    .ascii "emit_binop(1, +, 2) = \000"
.str14:
    .ascii "\012\000"
.str15:
    .ascii "*\000"
.str16:
    .ascii "+\000"
.str17:
    .ascii "(1 + (2 * 3)) = \000"
.str18:
    .ascii "\012\000"
.str19:
    .ascii "hello\000"
.str20:
    .ascii "emit_string(hello) = \000"
.str21:
    .ascii "\012\000"
.str22:
    .ascii "5\000"
.str23:
    .ascii "-\000"
.str24:
    .ascii "emit_unary(-, 5) = \000"
.str25:
    .ascii "\012\000"
.str26:
    .ascii "1\000"
.str27:
    .ascii "2\000"
.str28:
    .ascii "3\000"
.str29:
    .ascii "foo\000"
.str30:
    .ascii "emit_call(foo, [1,2,3]) = \000"
.str31:
    .ascii "\012\000"
heap_pos:
    .quad 0
heap_end:
    .quad 0
free_list:
    .quad 0

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
    jz .L77
    mov -8(%rbp), %rax
    mov 16(%rax), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -24(%rbp)
.L78:
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
    jz .L79
    mov -24(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -24(%rbp)
    jmp .L78
.L79:
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -32(%rbp)
    mov $0, %rax
    mov %rax, -40(%rbp)
.L80:
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
    jz .L81
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
    jmp .L80
.L81:
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
.L77:
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
.L82:
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
    jz .L83
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
    jmp .L82
.L83:
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
    jz .L85
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
.L85:
    mov -16(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L87
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
.L87:
    mov -16(%rbp), %rax
    mov %rax, -24(%rbp)
    mov $0, %rax
    mov %rax, -32(%rbp)
.L88:
    mov -24(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L89
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
    jmp .L88
.L89:
    mov -32(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -40(%rbp)
.L90:
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
    test %rax, %rax
    jz .L91
    mov $1, %rax
    mov %rax, -48(%rbp)
    mov $0, %rax
    mov %rax, -56(%rbp)
.L92:
    mov -56(%rbp), %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L93
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
    jmp .L92
.L93:
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
    jmp .L90
.L91:
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
.L94:
    mov -40(%rbp), %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
    test %rax, %rax
    jz .L95
    mov -40(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L97
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
.L97:
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
    jmp .L94
.L95:
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
.L98:
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
    jz .L99
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
    jz .L100
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
    jmp .L101
.L100:
    mov -24(%rbp), %rax
    push %rax
    mov $92, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L102
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
    jmp .L103
.L102:
    mov -24(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L104
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
    jmp .L105
.L104:
    mov -24(%rbp), %rax
    push %rax
    mov $13, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L106
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
    jmp .L107
.L106:
    mov -24(%rbp), %rax
    push %rax
    mov $9, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L108
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
    jmp .L109
.L108:
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call sb_char
.L109:
.L107:
.L105:
.L103:
.L101:
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -8(%rbp)
    jmp .L98
.L99:
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

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $42, %rax
    push %rax
    pop %rdi
    call emit_number
    mov %rax, -8(%rbp)
    lea .str6(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call print
    lea .str7(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $17, %rax
    neg %rax
    push %rax
    pop %rdi
    call emit_number
    mov %rax, -16(%rbp)
    lea .str8(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call print
    lea .str9(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str10(%rip), %rax
    push %rax
    lea .str11(%rip), %rax
    push %rax
    lea .str12(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call emit_binop
    mov %rax, -24(%rbp)
    lea .str13(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -24(%rbp), %rax
    push %rax
    pop %rdi
    call print
    lea .str14(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $1, %rax
    push %rax
    pop %rdi
    call emit_number
    mov %rax, -32(%rbp)
    mov $3, %rax
    push %rax
    pop %rdi
    call emit_number
    push %rax
    lea .str15(%rip), %rax
    push %rax
    mov $2, %rax
    push %rax
    pop %rdi
    call emit_number
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call emit_binop
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    lea .str16(%rip), %rax
    push %rax
    mov -32(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    call emit_binop
    mov %rax, -48(%rbp)
    lea .str17(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -48(%rbp), %rax
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
    call emit_string
    mov %rax, -56(%rbp)
    lea .str20(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -56(%rbp), %rax
    push %rax
    pop %rdi
    call print
    lea .str21(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str22(%rip), %rax
    push %rax
    lea .str23(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    call emit_unary
    mov %rax, -64(%rbp)
    lea .str24(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -64(%rbp), %rax
    push %rax
    pop %rdi
    call print
    lea .str25(%rip), %rax
    push %rax
    pop %rdi
    call print
    call vec_new
    mov %rax, -72(%rbp)
    lea .str26(%rip), %rax
    push %rax
    mov -72(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    lea .str27(%rip), %rax
    push %rax
    mov -72(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    lea .str28(%rip), %rax
    push %rax
    mov -72(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call vec_push
    mov -72(%rbp), %rax
    push %rax
    lea .str29(%rip), %rax
    push %rax
    pop %rdi
    pop %rsi
    call emit_call
    mov %rax, -80(%rbp)
    lea .str30(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -80(%rbp), %rax
    push %rax
    pop %rdi
    call print
    lea .str31(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $0, %rax
    leave
    ret

