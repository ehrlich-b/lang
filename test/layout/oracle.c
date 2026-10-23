/* Execute only on x86-64. wasm32 rows below are target arithmetic checks,
 * independent of execution or qualification on wasm/arm64. */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>
typedef struct { int64_t size, alignment, stride; } Layout;
extern int64_t layout_probe(const char *,const char *,int64_t,int64_t,int64_t,Layout *);
static unsigned checks;
static void query(const char *name,const char *profile,int64_t count,int64_t outer,
                  int form,int status,int64_t size,int64_t align,int64_t stride) {
    Layout result;
    int64_t got=layout_probe(name,profile,count,outer,form,&result);
    ++checks;
    if(got!=status || result.size!=size || result.alignment!=align || result.stride!=stride) {
        fprintf(stderr,"FAIL %s %s count=%lld outer=%lld form=%d: status=%lld size=%lld align=%lld stride=%lld\n",
                name,profile,(long long)count,(long long)outer,form,(long long)got,
                (long long)result.size,(long long)result.alignment,(long long)result.stride);
        exit(1);
    }
}
#define Q(n,p,c,o,f,s,z,a,r) query(n,p,c,o,f,s,z,a,r)
#define SCALAR(n,T) do { \
    T array[7]; T nested[3][7]; \
    size_t stride=(size_t)((char *)&array[1]-(char *)&array[0]); \
    Q(n,p,0,0,0,0,sizeof(T),_Alignof(T),stride); \
    Q(n,p,7,0,4,0,sizeof(array),_Alignof(T[7]),sizeof(array)); \
    Q(n,p,7,3,5,0,sizeof(nested),_Alignof(T[3][7]),sizeof(nested)); \
    Q(n,p,0,0,4,0,0,_Alignof(T),0); \
    Q(n,p,0,3,5,0,0,_Alignof(T),0); \
    Q(n,p,7,0,5,0,0,_Alignof(T),0); \
    int64_t max=limit/(int64_t)sizeof(T); \
    Q(n,p,max,0,4,0,max*(int64_t)sizeof(T),_Alignof(T),max*(int64_t)sizeof(T)); \
    if(max<INT64_MAX) Q(n,p,max+1,0,4,5,0,0,0); \
    Q(n,p,7,limit/7/(int64_t)sizeof(T)+1,5,5,0,0,0); \
    Q(n,p,-1,0,4,4,0,0,0); \
    printf("%s %s C-size=%zu C-align=%zu C-stride=%zu C-array=%zu C-nested=%zu\n",p,n,sizeof(T),_Alignof(T),stride,sizeof(array),sizeof(nested)); \
} while(0)
int main(void) {
#if !defined(__x86_64__)
#error This execution oracle requires an x86-64 host.
#endif
    for(int target=0;target<2;++target) {
        const char *p=target?"llvm-wasm32":"llvm-linux-x86_64";
        int64_t limit=target?UINT32_MAX:INT64_MAX;
        SCALAR("i8",int8_t); SCALAR("u8",uint8_t);
        SCALAR("i16",int16_t); SCALAR("u16",uint16_t);
        SCALAR("i32",int32_t); SCALAR("u32",uint32_t);
        SCALAR("i64",int64_t); SCALAR("u64",uint64_t);
        SCALAR("f32",float); SCALAR("f64",double); SCALAR("bool",_Bool);
        const char *unsupported[]={"void","i7","u128","Pair","Enum","Mystery"};
        for(unsigned i=0;i<sizeof(unsupported)/sizeof(*unsupported);++i) {
            Q(unsupported[i],p,0,0,0,2,0,0,0);
            Q(unsupported[i],p,0,0,4,2,0,0,0);
        }
        for(int form=1;form<=3;++form) Q("i64",p,0,0,form,3,0,0,0);
        Q("i64",p,0,0,6,2,0,0,0);
        Q("i64",p,0,0,7,3,0,0,0);
        if(target) Q("i64",p,0,limit+1,5,5,0,0,0);
        Q("i64",p,limit,limit,5,5,0,0,0);
    }
    Q("i64","llvm-macos-arm64",0,0,0,1,0,0,0);
    Q("i64","direct-wasm32",0,0,0,1,0,0,0);
    Q("i64","unknown",0,0,0,1,0,0,0);
    Q("i64",NULL,0,0,0,1,0,0,0);
    printf("PASS %u storage checks: x86-64 native C oracle; wasm32 target arithmetic only; no arm64 execution\n",checks);
}
