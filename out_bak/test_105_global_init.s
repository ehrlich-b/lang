.section .data
CONST_A:
    .quad 42
CONST_B:
    .quad 10
CONST_C:
    .quad 0

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
    mov CONST_A(%rip), %rax
    push %rax
    mov $42, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov $1, %rax
    leave
    ret
.L2:
    mov CONST_B(%rip), %rax
    push %rax
    mov $10, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L4
    mov $2, %rax
    leave
    ret
.L4:
    mov CONST_C(%rip), %rax
    push %rax
    mov $0, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setne %al
    movzx %al, %rax
    test %rax, %rax
    jz .L6
    mov $3, %rax
    leave
    ret
.L6:
    mov $0, %rax
    leave
    ret

