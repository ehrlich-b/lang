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

.globl add10
add10:
    push %rbp
    mov %rsp, %rbp
    sub $4096, %rsp
    mov %rdi, -8(%rbp)
    mov %rsi, -16(%rbp)
    mov %rdx, -24(%rbp)
    mov %rcx, -32(%rbp)
    mov %r8, -40(%rbp)
    mov %r9, -48(%rbp)
    mov 16(%rbp), %rax
    mov %rax, -56(%rbp)
    mov 24(%rbp), %rax
    mov %rax, -64(%rbp)
    mov 32(%rbp), %rax
    mov %rax, -72(%rbp)
    mov 40(%rbp), %rax
    mov %rax, -80(%rbp)
    mov -8(%rbp), %rax
    push %rax
    mov -16(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -24(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -32(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -40(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -48(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -56(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -64(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -72(%rbp), %rax
    mov %rax, %rcx
    pop %rax
    add %rcx, %rax
    push %rax
    mov -80(%rbp), %rax
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
    mov $10, %rax
    push %rax
    mov $9, %rax
    push %rax
    mov $8, %rax
    push %rax
    mov $7, %rax
    push %rax
    mov $6, %rax
    push %rax
    mov $5, %rax
    push %rax
    mov $4, %rax
    push %rax
    mov $3, %rax
    push %rax
    mov $2, %rax
    push %rax
    mov $1, %rax
    push %rax
    pop %rdi
    pop %rsi
    pop %rdx
    pop %rcx
    pop %r8
    pop %r9
    call add10
    leave
    ret

