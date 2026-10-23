#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "dispatch.h"
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    int64_t a = (int64_t)strtoull(argv[2], 0, 0);
    int64_t b = (int64_t)strtoull(argv[3], 0, 0);
    printf("%lld\n", (long long)numeric_probes[atoi(argv[1])](a, b, strtod(argv[2], 0), strtod(argv[3], 0)));
    return 0;
}
