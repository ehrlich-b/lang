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
    mov $1, %rax
    test %rax, %rax
    jnz .L3
    mov $1, %rax
    mov %rax, -8(%rbp)
.L3:
    test %rax, %rax
    jz .L2
    mov -8(%rbp), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L5
    mov $0, %rax
    leave
    ret
.L5:
    mov $1, %rax
    leave
    ret
.L2:
    mov $2, %rax
    leave
    ret

