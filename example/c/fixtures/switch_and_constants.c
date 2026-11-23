#include <stdio.h>

enum {
    narrowed = (unsigned char)256,
    signed_narrowed = (signed char)255,
    widened = (unsigned long)(0U - 1U) == 4294967295UL
};

int select_case(unsigned int selector, int *effects) {
    switch (selector) {
    case -1:;
        int local = ++*effects;
        if (local != 1) return 9;
    case 1:
        local = 12;
        return local;
    default:
        break;
    }
    return 3;
}

int main(void) {
    int effects = 0;
    int matched = select_case(4294967295U, &effects);
    int jumped = select_case(1, &effects);
    signed char narrow_selector = -1;
    int promoted = 0;
    switch (narrow_selector) {
    case 255:
        return 4;
    case signed_narrowed:
        promoted = 1;
    }
    printf("%d %d %d %d %d %d %d\n", narrowed, signed_narrowed, widened,
           matched, jumped, effects, promoted);
    return 0;
}
