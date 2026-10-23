#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
extern int64_t witness_wrap(int64_t,int64_t);
extern int64_t witness_signed(int64_t,int64_t);
extern int64_t witness_unsigned(int64_t,int64_t);
extern int64_t witness_storage(void);
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    uint64_t a = strtoull(argv[2], 0, 10), b = strtoull(argv[3], 0, 10);
    int64_t result;
    switch(atoi(argv[1])) {
        case 0: result = witness_wrap(a,b); break;
        case 1: result = witness_signed(a,b); break;
        case 2: result = witness_unsigned(a,b); break;
        case 3: result = witness_storage(); break;
        default: return 3;
    }
    printf("%lld\n", (long long)result);
}
