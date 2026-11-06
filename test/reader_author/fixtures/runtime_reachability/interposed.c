#include <stdint.h>
extern int64_t dead_helper(void), guest_entry(void);
int64_t write(int64_t fd, unsigned char *data, int64_t count) {
    (void)fd; (void)data; (void)count;
#ifdef LEAF_WRITE
    return 901;
#else
    return dead_helper();
#endif
}
int main(void) { return guest_entry() != 901; }
