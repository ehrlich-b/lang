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
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cqo
    idiv %rcx
    mov %rdx, %rax
    mov %rax, -8(%rbp)
    mov $10, %rax
    mov %rax, -16(%rbp)
    mov -16(%rbp), %rax
    push %rax
    mov $2, %rax
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -16(%rbp)
    mov $38, %rax
    mov %rax, -24(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

