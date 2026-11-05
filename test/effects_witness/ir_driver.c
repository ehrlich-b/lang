#include <stdint.h>
#include <stdio.h>
struct Frame { int32_t pc; int64_t saved, result; };
extern int32_t two_ticks(struct Frame *, int64_t, int64_t *);
int main(void) {
    struct Frame f = {0}; int64_t payload = 0;
    if (two_ticks(&f, 0, &payload) != 1 || payload != 10) return 1;
    if (two_ticks(&f, payload+100, &payload) != 1 || payload != 130) return 2;
    if (two_ticks(&f, payload+100, &payload) != 0 || f.result != 340) return 3;
    f.pc = 99;
    if (two_ticks(&f, 0, &payload) != 2) return 4;
    puts("340 checked-invalid-pc");
    return 0;
}
