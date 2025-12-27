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

.globl multiply
multiply:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    leave
    ret

.globl square
square:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    push %rax
    pop %rdi
    pop %rsi
    call multiply
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $7, %rax
    push %rax
    pop %rdi
    call square
    leave
    ret

