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
    mov $1, %rax
    test %rax, %rax
    jz .L4
    mov $1, %rax
.L4:
    test %rax, %rax
    jz .L3
    mov $1, %rax
.L3:
    test %rax, %rax
    jz .L2
    mov $0, %rax
    test %rax, %rax
    jnz .L8
    mov $0, %rax
.L8:
    test %rax, %rax
    jnz .L7
    mov $1, %rax
.L7:
    test %rax, %rax
    jz .L6
    mov $1, %rax
    test %rax, %rax
    jz .L12
    mov $0, %rax
.L12:
    test %rax, %rax
    jnz .L11
    mov $1, %rax
.L11:
    test %rax, %rax
    jz .L10
    mov $0, %rax
    leave
    ret
.L10:
.L6:
.L2:
    mov $1, %rax
    leave
    ret

