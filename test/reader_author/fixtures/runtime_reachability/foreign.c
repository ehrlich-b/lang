#include <stdint.h>
extern int64_t dead_helper(void), guest_entry(void);
int64_t foreign_dependency(void) { return dead_helper(); }
int main(void) { return guest_entry() != 901; }
