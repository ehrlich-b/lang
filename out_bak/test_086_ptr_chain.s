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
    mov %rax, -8(%rbp)
    mov $2, %rax
    mov %rax, -16(%rbp)
    mov $3, %rax
    mov %rax, -24(%rbp)
    lea -8(%rbp), %rax
    mov %rax, -32(%rbp)
    lea -16(%rbp), %rax
    mov %rax, -40(%rbp)
    lea -24(%rbp), %rax
    mov %rax, -48(%rbp)
    mov -32(%rbp), %rax
    mov (%rax), %rax
    push %rax
    mov -40(%rbp), %rax
    mov (%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -48(%rbp), %rax
    mov (%rax), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -56(%rbp)
    mov -56(%rbp), %rax
    push %rax
    mov $6, %rax
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

