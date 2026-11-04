#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
    int64_t n = 5000000;
    if (argc > 1) { n = atol(argv[1]); }
    int64_t * keys = malloc(65536 * 8);
    int64_t * values = malloc(65536 * 8);
    int64_t i = 0;
    while (i < 65536) { keys[i] = -1; values[i] = 0; i = i + 1; }
    i = 0;
    while (i < n) {
        int64_t key = ((i * 48271) % 1000003) % 32768;
        int64_t slot = (key * 4051) % 65536;
        while (keys[slot] != -1 && keys[slot] != key) { slot = (slot + 1) % 65536; }
        keys[slot] = key;
        values[slot] = values[slot] + i % 97;
        i = i + 1;
    }
    int64_t result = 0;
    i = 0;
    while (i < 65536) { result = result + values[i]; i = i + 1; }
    free(keys);
    free(values);
    printf("%lld\n", (long long)result);
    return 0;
}
