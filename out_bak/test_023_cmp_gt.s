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
    mov $7, %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov $5, %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L4
    mov $1, %rax
    leave
    ret
.L4:
    mov $3, %rax
    push %rax
    mov $5, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setg %al
    movzx %al, %rax
    test %rax, %rax
    jz .L6
    mov $2, %rax
    leave
    ret
.L6:
    mov $0, %rax
    leave
    ret
.L2:
    mov $3, %rax
    leave
    ret

