#include "machine.h"
/* Separate translation unit: native ABI calls and dynamic descriptor selection. */
I foreign_leaf(I x) { return x * 3 + 1; }
void foreign_callback(Context *c, void (*callback)(Context *)) { callback(c); }
const Descriptor *choose_worker(I selector) { return selector & 1 ? &WORK : &STEP; }
