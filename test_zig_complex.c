#define ZIG_TARGET_MAX_INT_ALIGNMENT 16
#include "zig.h"
struct anon__lazy_39 {
 uint8_t const *ptr;
 uintptr_t len;
};
#define test_zig_complex_factorial__227 factorial
zig_extern int64_t factorial(int64_t);
#define test_zig_complex_main__228 main
zig_extern int64_t main(void);
static uint64_t const builtin_zig_backend__232;
static bool const start_simplified_logic__108;
static uint8_t const builtin_output_mode__233;
static struct anon__lazy_39 const zig_errorName[1] = {};

(func factorial ((param arg0 (type_base i64))) (type_base i64)
  (block
    (var t0 (type_base i64) (number 0))
    (assign (ident t0) (number 1))
    (var t1 (type_base i64) (number 0))
    (assign (ident t1) (number 1))
    (block
      (while (number 1)
        (block
          (block
            (var t2 (type_base bool) (binop <= (ident t1) (ident arg0)))
            (if (ident t2)
              (block
                (var t3 (type_base i64) (binop * (ident t0) (ident t1)))
                (assign (ident t0) (ident t3))
                (var t4 (type_base i64) (binop + (ident t1) (number 1)))
                (assign (ident t1) (ident t4))
                (break (number 0)))
              (block
                (break (number 0))))))))
    (return (ident t0))))

(func main () (type_base i64)
  (block
    (var t0 (type_base i64) (call (ident factorial) (number 5)))
    (return (ident t0))))

static uint64_t const builtin_zig_backend__232 = UINT64_C(3);

static bool const start_simplified_logic__108 = false;

static uint8_t const builtin_output_mode__233 = UINT8_C(2);
