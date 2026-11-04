#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {
    int64_t n = 2000;
    if (argc > 1) { n = atol(argv[1]); }
    double pos[192];
    double vel[192];
    int64_t i = 0;
    while (i < 192) {
        pos[i] = (double)(i % 17) * 0.125;
        vel[i] = 0.0;
        i = i + 1;
    }
    int64_t step = 0;
    while (step < n) {
        i = 0;
        while (i < 64) {
            int64_t j = 0;
            double ax = 0.0;
            double ay = 0.0;
            double az = 0.0;
            while (j < 64) {
                double dx = pos[j * 3] - pos[i * 3];
                double dy = pos[j * 3 + 1] - pos[i * 3 + 1];
                double dz = pos[j * 3 + 2] - pos[i * 3 + 2];
                double inv = 0.0001 / (1.0 + dx * dx + dy * dy + dz * dz);
                ax = ax + dx * inv;
                ay = ay + dy * inv;
                az = az + dz * inv;
                j = j + 1;
            }
            vel[i * 3] = vel[i * 3] + ax;
            vel[i * 3 + 1] = vel[i * 3 + 1] + ay;
            vel[i * 3 + 2] = vel[i * 3 + 2] + az;
            i = i + 1;
        }
        i = 0;
        while (i < 192) { pos[i] = pos[i] + vel[i]; i = i + 1; }
        step = step + 1;
    }
    double total = 0.0;
    i = 0;
    while (i < 192) { total = total + pos[i] * pos[i]; i = i + 1; }
    int64_t result = (int64_t)(total * 1000.0);
    printf("%lld\n", (long long)result);
    return 0;
}
