#include <dlfcn.h>
#include <ffi.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

double putchard(double x) {
    if (x > -2147483649.0 && x < 2147483648.0) fputc((unsigned char)(int)x, stderr);
    return 0;
}

double printd(double x) { fprintf(stderr, "%f\n", x); return 0; }

void kal_result(const double *result) { fprintf(stderr, "Evaluated to %f\n", *result); }

double kal_apply(const char *name, uint64_t n, void **args) {
    void *symbol = dlsym(RTLD_DEFAULT, name);
    ffi_type *types[n + 1];
    for (uint64_t i = 0; i < n; ++i) types[i] = &ffi_type_double;
    ffi_cif call;
    if (!symbol || ffi_prep_cif(&call, FFI_DEFAULT_ABI, n, &ffi_type_double, types) != FFI_OK) {
        fprintf(stderr, "unavailable double ABI symbol: %s\n", name);
        exit(1);
    }
    double result;
    ffi_call(&call, FFI_FN(symbol), &result, args);
    return result;
}
