#include <stdio.h>

struct Sample {
    char tag;
    int amount;
    short marks[3];
};

struct Sample sample = { .amount = 9, .marks = { 2, 4, 6 } };

int main(void) {
    struct Sample *p = &sample;
    int n = 0;
    int i;
    for (i = 0; i < 3; ++i) {
        if (i == 1) continue;
        n += p->marks[i];
    }
    switch (p->amount) {
    case 9:
        n += 3;
    case 3:
        n += 1;
        break;
    default:
        return 7;
    }
    printf("%d %lu\n", n, sizeof(*p));
    return 0;
}
