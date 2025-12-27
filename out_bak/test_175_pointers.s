.section .data
.str0:
    .ascii "logic ok\012\000"

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
    mov $42, %rax
    mov %rax, -8(%rbp)
    lea -8(%rbp), %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L3
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $100, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setl %al
    movzx %al, %rax
.L3:
    test %rax, %rax
    jz .L2
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
.L2:
    mov $1, %rax
    mov %rax, -24(%rbp)
    xor %rax, %rax
    mov %rax, -32(%rbp)
    mov -24(%rbp), %rax
    test %rax, %rax
    jnz .L6
    mov -32(%rbp), %rax
.L6:
    test %rax, %rax
    jz .L5
    mov -32(%rbp), %rax
    test %rax, %rax
    setz %al
    movzx %al, %rax
    test %rax, %rax
    jz .L8
    mov $9, %rax
    push %rax
    lea .str0(%rip), %rax
    push %rax
    mov $1, %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    syscall
.L8:
.L5:
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L11
    mov -8(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setge %al
    movzx %al, %rax
.L11:
    test %rax, %rax
    jz .L10
    mov $0, %rax
    leave
    ret
.L10:
    mov $1, %rax
    leave
    ret

