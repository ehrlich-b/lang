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
    .ascii "  tok_next: c = \000"
.str7:
    .ascii "\012\000"
.str8:
    .ascii "  matched 40!\012\000"
.str9:
    .ascii "  matched 43!\012\000"
.str10:
    .ascii "  fallthrough to unknown\012\000"
.str11:
    .ascii "(+\000"
.str12:
    .ascii "Before tok_next:\012\000"
.str13:
    .ascii "  input[0] = \000"
.str14:
    .ascii "\012\000"
.str15:
    .ascii "After tok_next:\012\000"
.str16:
    .ascii "  tok_kind = \000"
.str17:
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
    jz .L77
    mov $0, %rax
    leave
    ret
.L77:
    mov -8(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov 8(%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov (%rax), %rax
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
    jz .L79
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
.L79:
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
    jz .L81
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    xor %rax, %rax
    leave
    ret
.L81:
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_peek_char
    mov %rax, -16(%rbp)
    lea .str6(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -16(%rbp), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str7(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -16(%rbp), %rax
    push %rax
    mov $40, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L83
    mov $4, %rax
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
    lea .str8(%rip), %rax
    push %rax
    pop %rdi
    call print
    xor %rax, %rax
    leave
    ret
.L83:
    mov -16(%rbp), %rax
    push %rax
    mov $43, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L85
    mov $10, %rax
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
    lea .str9(%rip), %rax
    push %rax
    pop %rdi
    call print
    xor %rax, %rax
    leave
    ret
.L85:
    lea .str10(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $99, %rax
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

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $48, %rax
    push %rax
    pop %rdi
    call alloc
    mov %rax, -8(%rbp)
    lea .str11(%rip), %rax
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
    mov $2, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 16(%rcx)
    mov $0, %rax
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
    mov $0, %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, 40(%rcx)
    lea .str12(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str13(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov (%rax), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str14(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    call tok_next
    lea .str15(%rip), %rax
    push %rax
    pop %rdi
    call print
    lea .str16(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov -8(%rbp), %rax
    mov 40(%rax), %rax
    push %rax
    pop %rdi
    call print_int
    lea .str17(%rip), %rax
    push %rax
    pop %rdi
    call print
    mov $0, %rax
    leave
    ret

