#include <stdio.h>

typedef unsigned short Counter;

int main(void) {
    int values[4] = { [2] = 17, 23 };
    int *p = values + 2;
    Counter c = 65535;
    c++;
    ++*p;
    int first = *p++;
    printf("%d %d %d %d\n", values[0], first, *p, c);
    return 0;
}
