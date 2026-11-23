/* SysV AMD64: integer and pointer arguments already occupy the libc ABI
 * registers and stack slots. AL is the count of vector arguments. The reader
 * assigns each call arity a distinct fixed-signature core symbol. */
.text
.macro variadic name, arity
.globl __c_\name\()\arity
.type __c_\name\()\arity, @function
__c_\name\()\arity:
    xor %eax, %eax
    jmp \name@PLT
.size __c_\name\()\arity, .-__c_\name\()\arity
.endm

.irp arity,1,2,3,4,5,6,7,8,9,10,11,12
    variadic printf, \arity
    variadic sprintf, \arity
.endr

.section .note.GNU-stack,"",@progbits
