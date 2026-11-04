#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
int64_t fib(int64_t n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}
int main(int argc, char **argv) {
    int64_t n = 38;
    if (argc > 1) { n = atol(argv[1]); }
    int64_t result = fib(n);
    printf("%lld\n", (long long)result);
    return 0;
}
