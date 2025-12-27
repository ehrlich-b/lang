.section .data
.str0:
    .ascii "ok\012\000"
.str1:
    .ascii "fail\012\000"

.section .text
.globl _start
_start:
    mov (%rsp), %rdi
    lea 8(%rsp), %rsi
    call main
    mov %rax, %rdi
    mov $60, %rax
    syscall

.globl factorial
factorial:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov $1, %rax
    mov %rax, -16(%rbp)
    mov $1, %rax
    mov %rax, -24(%rbp)
.L1:
    mov -24(%rbp), %rax
    push %rax
    mov -8(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    setle %al
    movzx %al, %rax
    test %rax, %rax
    jz .L2
    mov -16(%rbp), %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    imul %rcx, %rax
    mov %rax, -16(%rbp)
    mov -24(%rbp), %rax
    push %rax
    mov $1, %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    mov %rax, -24(%rbp)
    jmp .L1
.L2:
    mov -16(%rbp), %rax
    leave
    ret

.globl main
main:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov $5, %rax
    push %rax
    pop %rdi
    call factorial
    mov %rax, -8(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov $120, %rax
    mov %rax, %rcx
    pop %rax
    cmp %rcx, %rax
    sete %al
    movzx %al, %rax
    test %rax, %rax
    jz .L3
    mov $3, %rax
    push %rax
    lea .str0(%rip), %rax
    push %rax
    mov $1, %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    syscall
    jmp .L4
.L3:
    mov $5, %rax
    push %rax
    lea .str1(%rip), %rax
    push %rax
    mov $1, %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rax
    pop %rdi
    pop %rsi
    pop %rdx
    syscall
.L4:
    mov $0, %rax
    leave
    ret

