#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
    int64_t n = 1000;
    if (argc > 1) { n = atol(argv[1]); }
    int64_t result = 0;
    int64_t y = 0;
    while (y < n) {
        int64_t x = 0;
        while (x < n) {
            double cr = (double)(x) * 3.0 / (double)(n) - 2.0;
            double ci = (double)(y) * 2.0 / (double)(n) - 1.0;
            double zr = 0.0;
            double zi = 0.0;
            int64_t k = 0;
            while (k < 200 && zr * zr + zi * zi <= 4.0) {
                double next = zr * zr - zi * zi + cr;
                zi = 2.0 * zr * zi + ci;
                zr = next;
                k = k + 1;
            }
            result = result + k;
            x = x + 1;
        }
        y = y + 1;
    }
    printf("%lld\n", (long long)result);
    return 0;
}
