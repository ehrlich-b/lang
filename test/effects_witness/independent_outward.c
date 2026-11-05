/* Independent ED review probe, originally compiled from stdin on 2026-10-18.
 * This comment was added when preserving the original source; no test was rerun.
 * From the repository root, reproduce with:
 * nice -n 10 clang -std=c11 -Wall -Wextra -Werror -pedantic -O2 \
 *   -fsanitize=address,undefined -fno-sanitize-recover=all \
 *   -I test/effects_witness test/effects_witness/machine.c \
 *   test/effects_witness/independent_outward.c -o ../scratch/outward
 * ../scratch/outward
 */
#include "machine.h"
#include <stdio.h>
#include <stdlib.h>
static const Descriptor BODY, REGION, ROOT_PROBE;
static Action body(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return perform(1, 10);
    return action(RETURN, f->input + 1);
}
static Action region(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return enter(&BODY, 0, 1, 0, 2, 1);
    return action(RETURN, f->input);
}
static Action root_probe(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return enter(&REGION, 0, 2, 0, 3, 1);
    return action(RETURN, f->input);
}
static Action clause_probe(Context *c, Frame *f) {
    if (f->clause_of->effect == 2) {
        if (c->seed) return action(RETURN, 77);
        return resume(f->token, f->v[0] + 20);
    }
    if (f->pc++ == 0) return perform(2, 100);
    return resume(f->token, f->v[0] + f->input);
}
const Descriptor CLAUSE = {1, 1, clause_probe};
static const Descriptor BODY = {1, 1, body};
static const Descriptor REGION = {1, 1, region};
static const Descriptor ROOT_PROBE = {1, 1, root_probe};
int main(void) {
    for (int abort_outer = 0; abort_outer < 2; ++abort_outer) {
        Context *c = calloc(1, sizeof(*c));
        if (!c) return 1;
        c->task = 1; c->seed = abort_outer;
        I result = run(c, &ROOT_PROBE, 0);
        if (c->error || c->live || c->drops != c->nf || result != (abort_outer ? 77 : 790)) return 2;
        unsigned seen[513] = {0};
        for (unsigned i = 0; i < c->nc; ++i)
            if (c->cleanup[i] > c->nf || !c->cleanup[i] || seen[c->cleanup[i]]++) return 3;
        printf("outward_clause_%s=%lld cleanup=%u/%u\n", abort_outer ? "abort" : "resume", (long long)result, c->drops, c->nf);
        free(c);
    }
    return 0;
}
