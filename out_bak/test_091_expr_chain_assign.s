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
    mov $0, %rax
    mov %rax, -8(%rbp)
    mov $0, %rax
    mov %rax, -16(%rbp)
    mov $0, %rax
    mov %rax, -24(%rbp)
    mov $100, %rax
    mov %rax, -24(%rbp)
    mov %rax, -16(%rbp)
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $100, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov -16(%rbp), %rax
    push %rax
    mov $100, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L4
    mov -24(%rbp), %rax
    push %rax
    mov $100, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L6
    mov $0, %rax
    leave
    ret
.L6:
.L4:
.L2:
    mov $1, %rax
    leave
    ret

