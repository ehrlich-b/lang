#include <stdint.h>
extern int64_t external_export(void), second_export(void), guest_entry(void);
extern intptr_t initialized_callback;
int main(void) {
    int64_t (*callback)(int64_t) = (int64_t (*)(int64_t))initialized_callback;
    return external_export() != 42 || second_export() != 43 ||
           guest_entry() != 35 || callback(35) != 42;
}
