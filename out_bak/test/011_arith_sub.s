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
    push %rax
    mov $3, %rax
    mov %rax, %rcx
    pop %rax
    sub %rcx, %rax
    push %rax
    mov $7, %rax
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

