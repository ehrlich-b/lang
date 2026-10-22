/* Cross-target constants, not an execution receipt. */
#include <stdint.h>
#include <stddef.h>
#define ROW(n,T) const uint64_t storage_##n[5] = {sizeof(T),_Alignof(T),sizeof(T),sizeof(T[7]),sizeof(T[3][7])}
ROW(i8,int8_t); ROW(u8,uint8_t); ROW(i16,int16_t); ROW(u16,uint16_t);
ROW(i32,int32_t); ROW(u32,uint32_t); ROW(i64,int64_t); ROW(u64,uint64_t);
ROW(f32,float); ROW(f64,double); ROW(bool,_Bool);
