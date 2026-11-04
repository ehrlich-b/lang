#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
    int64_t n = 100;
    if (argc > 1) { n = atol(argv[1]); }
    uint8_t * text = malloc(1048576);
    int64_t i = 0;
    while (i < 1048576) { text[i] = (uint8_t)(32 + (i * 17) % 95); i = i + 1; }
    int64_t result = 0;
    int64_t round = 0;
    while (round < n) {
        uint8_t * cursor = text;
        uint8_t * end = text + 1048576;
        while (cursor < end) {
            if (*cursor == 97 || *cursor == 101) { result = result + 1; }
            cursor = cursor + 1;
        }
        round = round + 1;
    }
    free(text);
    printf("%lld\n", (long long)result);
    return 0;
}
