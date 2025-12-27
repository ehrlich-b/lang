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
    mov $25, %rax
    push %rax
    mov $25, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov $25, %rax
    push %rax
    mov $25, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

