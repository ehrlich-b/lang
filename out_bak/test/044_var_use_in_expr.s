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
    mov $10, %rax
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $30, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov $0, %rax
    leave
    ret
.L2:
    mov $1, %rax
    leave
    ret

