.section .data

.section .text
.globl _start
_start:
    mov (%rsp), %rdi
    lea 8(%rsp), %rsi
    call main
    mov %rax, %rdi
    mov $60, %rax
    syscall

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $5, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    and %rcx, %rax
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov $1, %rax
    leave
    ret
.L2:
    mov $5, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    or %rcx, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L4
    mov $2, %rax
    leave
    ret
.L4:
    mov $5, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    xor %rcx, %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $6, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L6
    mov $3, %rax
    leave
    ret
.L6:
    mov $1, %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    shl %cl, %rax
    mov %rax, -32(%rbp)
    mov -32(%rbp), %rax
    push %rax
    mov $16, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L8
    mov $4, %rax
    leave
    ret
.L8:
    mov $16, %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    sar %cl, %rax
    mov %rax, -40(%rbp)
    mov -40(%rbp), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L10
    mov $5, %rax
    leave
    ret
.L10:
    mov $1, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    shl %cl, %rax
    push %rax
    mov $1, %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    shl %cl, %rax
    mov %rax, %rcx
    pop %rax
    or %rcx, %rax
    mov %rax, -48(%rbp)
    mov -48(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L12
    mov $6, %rax
    leave
    ret
.L12:
    mov $3, %rax
    push %rax
    mov $4, %rax
    push %rax
    mov $6, %rax
    mov %rax, %rcx
    pop %rax
    and %rcx, %rax
    mov %rax, %rcx
    pop %rax
    or %rcx, %rax
    mov %rax, -56(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov $7, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L14
    mov $7, %rax
    leave
    ret
.L14:
    mov $0, %rax
    leave
    ret

