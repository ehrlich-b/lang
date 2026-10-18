#include <stdint.h>
#include <stddef.h>

/* Lang pointer parameters are i64 addresses; pointer returns use the C ABI. */
extern int64_t lang_index_byte(uint64_t p, int64_t i);
extern void lang_store_byte(uint64_t p, int64_t i, int64_t value);
extern uint8_t *lang_index_arg(uint64_t argv, int64_t i);
extern void lang_store_arg(uint64_t argv, int64_t i, uint64_t value);
extern int64_t lang_index_pair(uint64_t p, int64_t i);
extern void lang_copy_pair(uint64_t p);

struct IndexPair { int64_t first, second; };

int64_t pointer_index_check(void) {
    uint8_t bytes[] = {17, 128, 255, 23};
    uint64_t address = (uint64_t)(uintptr_t)bytes;
    if (lang_index_byte(address, 1) != 128) return 1;
    if (lang_index_byte(address, 2) != 255) return 2;
    lang_store_byte(address, 1, 298);
    if (bytes[0] != 17 || bytes[1] != 42 || bytes[2] != 255 || bytes[3] != 23) return 3;

    uint8_t other[] = {7, 9};
    uint8_t *argv[] = {bytes, other, NULL};
    uint64_t slots = (uint64_t)(uintptr_t)argv;
    if (lang_index_arg(slots, 1) != other) return 4;
    if (lang_index_arg(slots, 2) != NULL) return 5;
    lang_store_arg(slots, 1, address);
    if (argv[0] != bytes || argv[1] != bytes || argv[2] != NULL) return 6;

    struct IndexPair pairs[] = {{10, 32}, {99, 88}, {7, 8}};
    uint64_t pair_address = (uint64_t)(uintptr_t)pairs;
    if (lang_index_pair(pair_address, 1) != 88) return 7;
    lang_copy_pair(pair_address);
    if (pairs[1].first != 10 || pairs[1].second != 32) return 8;
    if (pairs[2].first != 7 || pairs[2].second != 8) return 9;
    return 42;
}
