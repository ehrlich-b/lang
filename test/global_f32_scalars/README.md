Frozen words are independent of the compiler and runtime oracle. Integer values
retain 24 significant binary digits, rounding discarded bits to nearest, ties
to even (16777217 -> 0x4b800000; 16777219 -> 0x4b800002;
33554435 -> 0x4c000001). The two integer readers are handwritten separately.

Decimal cases use exact decimal spellings of powers of two: 2^-149, 2^-150,
the largest subnormal, the smallest normal and (2 - 2^-23) * 2^127. The value
1 + 2^-24 + 10^-36 must round upward; converting through binary64 first loses
the final term and would produce 0x3f800000 instead of 0x3f800001. At the
finite overflow threshold 2^128 - 2^103, ties-to-even overflows and is refused.
Decimal signs survive exact zero and underflow. Decimal inputs remain Lang-only
because the core reader does not support decimal tokens.

Mutation checks initial reads, integer/decimal literal assignment, copying a
global, an explicit numeric f32 result and a local f32 load. The C oracle calls
the compiled accessor in order and compares words. Its Wasm entry wrapper
returns the oracle status through the existing i64 host main convention.
