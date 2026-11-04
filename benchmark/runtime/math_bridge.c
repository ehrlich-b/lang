/* Identical libm entry point for both programs, including the preserved seed's
 * integer-carried FFI. memcpy preserves the bits without aliasing violations. */
#include <math.h>
#include <stdint.h>
#include <string.h>
int64_t bench_sqrt_bits(int64_t bits) {
    double value;
    memcpy(&value, &bits, sizeof value);
    value = sqrt(value);
    memcpy(&bits, &value, sizeof bits);
    return bits;
}
