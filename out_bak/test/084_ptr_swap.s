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

.globl swap
swap:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    mov (%rax), %rax
    mov %rax, -24(%rbp)
    mov -16(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    mov -24(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    mov %rax, (%rcx)
    xor %rax, %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $10, %rax
    mov %rax, -8(%rbp)
    mov $20, %rax
    mov %rax, -16(%rbp)
    lea -16(%rbp), %rax
    push %rax
    lea -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call swap
    mov -8(%rbp), %rax
    push %rax
    mov $20, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov -16(%rbp), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L4
    mov $0, %rax
    leave
    ret
.L4:
.L2:
    mov $1, %rax
    leave
    ret

