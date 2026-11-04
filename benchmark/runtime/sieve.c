#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
    int64_t n = 20000000;
    if (argc > 1) { n = atol(argv[1]); }
    uint8_t * flags = malloc(n + 1);
    int64_t i = 0;
    while (i <= n) { flags[i] = 1; i = i + 1; }
    i = 2;
    while (i * i <= n) {
        if (flags[i] != 0) {
            int64_t j = i * i;
            while (j <= n) { flags[j] = 0; j = j + i; }
        }
        i = i + 1;
    }
    int64_t result = 0;
    i = 2;
    while (i <= n) { result = result + flags[i]; i = i + 1; }
    free(flags);
    printf("%lld\n", (long long)result);
    return 0;
}
