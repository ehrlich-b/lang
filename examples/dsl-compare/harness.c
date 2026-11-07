#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern int64_t compute(int64_t n);
int main(int argc, char **argv) {
    int64_t n = argc > 1 ? strtoll(argv[1], NULL, 10) : 2000000;
    printf("%" PRId64 "\n", compute(n));
    return 0;
}
