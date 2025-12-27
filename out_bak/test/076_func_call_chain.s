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

.globl a
a:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $1, %rax
    leave
    ret

.globl b
b:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    call a
    push %rax
    mov $2, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

.globl c
c:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    call b
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

.globl d
d:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    call c
    push %rax
    mov $4, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    call d
    push %rax
    mov $10, %rax
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

