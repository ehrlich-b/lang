#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
int main(int argc, char **argv) {
    if (argc != 6) return 2;
    const char *op = argv[1], *dst = argv[2], *src = argv[3];
    double a = strtod(argv[4], 0), b = strtod(argv[5], 0), r = 0;
    int bits = atoi(src + 1), db = atoi(dst + 1);
    int sf = *src == 'f', df = *dst == 'f';
    if (sf && bits == 32) { a = (float)a; b = (float)b; }
    if (!strcmp(op, "bitcast")) {
        uint64_t u = strtoull(argv[4], 0, 0);
        if (sf) {
            if (bits == 32) { float f = a; uint32_t v; memcpy(&v, &f, 4); u = v; }
            else memcpy(&u, &a, 8);
        }
        if (db < 64) {
            u &= (UINT64_C(1) << db) - 1;
            if (*dst == 'i' && (u >> (db - 1))) u |= ~((UINT64_C(1) << db) - 1);
        }
        printf("%lld\n", (long long)(int64_t)u); return 0;
    }
    if (!strncmp(op, "convert", 7)) {
        if (sf && !df) {
            long double t = truncl(a), lo = *dst == 'i' ? -ldexpl(1, db - 1) : 0;
            long double hi = ldexpl(1, db - (*dst == 'i'));
            if (!isfinite(a) || t < lo || t >= hi) return 100;
            uint64_t u = *dst == 'i' ? (uint64_t)(int64_t)a : (uint64_t)a;
            printf("%lld\n", (long long)(int64_t)u); return 0;
        }
        if (!sf) {
            uint64_t u = strtoull(argv[4], 0, 0);
            if (bits < 64) u &= (UINT64_C(1) << bits) - 1;
            if (*src == 'i' && bits < 64 && (u >> (bits - 1))) u |= ~((UINT64_C(1) << bits) - 1);
            // Cast directly to the destination precision to avoid double rounding.
            if (db == 32) { float f = *src == 'i' ? (float)(int64_t)u : (float)u; r = f; }
            else r = *src == 'i' ? (double)(int64_t)u : (double)u;
        } else r = a;
    } else if (!strcmp(op, "eq")) r = a == b;
    else if (!strcmp(op, "ne")) r = a != b;
    else if (!strcmp(op, "lt")) r = a < b;
    else if (!strcmp(op, "le")) r = a <= b;
    else if (!strcmp(op, "gt")) r = a > b;
    else if (!strcmp(op, "ge")) r = a >= b;
    else if (bits == 32) {
        float x = a, y = b, z;
        if (!strcmp(op, "add")) z = x + y;
        else if (!strcmp(op, "sub")) z = x - y;
        else if (!strcmp(op, "mul")) z = x * y;
        else if (!strcmp(op, "div")) z = x / y;
        else z = fmodf(x, y);
        r = z;
    } else {
        if (!strcmp(op, "add")) r = a + b;
        else if (!strcmp(op, "sub")) r = a - b;
        else if (!strcmp(op, "mul")) r = a * b;
        else if (!strcmp(op, "div")) r = a / b;
        else r = fmod(a, b);
    }
    uint64_t u;
    if (!df) u = (uint64_t)(int64_t)r;
    else if (db == 32) { float f = r; uint32_t v; memcpy(&v, &f, 4); u = v; }
    else memcpy(&u, &r, 8);
    printf("%lld\n", (long long)(int64_t)u); return 0;
}
