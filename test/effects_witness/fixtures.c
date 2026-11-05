#include "machine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The same arithmetic as the inherited two-perform IR, with all live values
 * stored in frame fields. No register, stack-pointer, or label address escapes. */
static Action work(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: f->v[1] = f->v[0]*3; f->v[2] = f->v[0]+7;
            return perform(1, f->v[1]);
    case 1: f->v[3] = f->input; f->v[4] = f->v[1]*f->v[2]+f->v[3];
            return perform(1, f->v[4]);
    case 2: f->v[5] = f->input; f->v[6] = f->v[5]-f->v[1]+f->v[2];
            f->v[7] = f->v[6]*2+100;
            return action(RETURN, f->v[1]+f->v[2]*10+f->v[3]*100+f->v[4]*1000+
                          f->v[5]*3+f->v[6]*7+f->v[7]*11);
    default: return action(BAD_PC, 0);
    }
}
static Action step(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: f->v[1] = f->v[0]*11; return perform(1, f->v[1]);
    case 1: f->v[2] = f->input; f->v[3] = f->v[1]+2*f->v[2]; return perform(1, f->v[3]);
    case 2: return action(RETURN, f->v[1]+3*f->v[2]+5*f->v[3]+7*f->input);
    default: return action(BAD_PC, 0);
    }
}
static Action sum_work(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: return call(&WORK, f->v[0]);
    case 1: f->v[1] = f->input; return call(&WORK, f->v[0] == 5 ? 2 : 3);
    case 2: return action(RETURN, f->v[1]+f->input);
    default: return action(BAD_PC, 0);
    }
}
static Action sum_step(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: return call(&STEP, 1);
    case 1: f->v[1] = f->input; return call(&STEP, 4);
    case 2: return action(RETURN, f->v[1]+f->input);
    default: return action(BAD_PC, 0);
    }
}
static Action leaf(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return perform((unsigned)f->v[0], 10);
    return action(RETURN, f->input+1);
}
static Action nested(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: return enter(&LEAF, 1, 2, 200, 2, 1); /* Effect 1 skips this inner prompt. */
    case 1: f->v[1] = f->input; return enter(&LEAF, 2, 2, 20, 1, 0);
    case 2: return action(RETURN, f->v[1]+f->input);
    default: return action(BAD_PC, 0);
    }
}
static Action deep(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: return call(&LEAF, 1);
    case 1: return action(RETURN, f->input+1000);
    default: return action(BAD_PC, 0);
    }
}
static Action mixed(Context *c, Frame *f) {
    (void)c;
    switch (f->pc++) {
    case 0: return perform(1, 10);
    case 1: f->v[1] = f->input; return perform(2, 20);
    case 2: return action(RETURN, f->v[1]+f->input);
    default: return action(BAD_PC, 0);
    }
}
static Action mixed_region(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return enter(&MIXED, 0, 2, 200, 1, 0);
    return action(RETURN, f->input);
}
static const Descriptor MIX_REGION = {1, 1, mixed_region};
static const Descriptor BAD_DESCRIPTOR = {0, 0, NULL};
static void callback(Context *c) { (void)may_suspend(c); }
/* Scenario numbers are harness inputs. The clauses are ordinary resumable
 * frames themselves, including reentrant handles and side effects. */
static Action clause(Context *c, Frame *f) {
    I mode = c->frames[0].v[0];
    ++c->effects;
    if (mode == 8) return action(RETURN, 77); /* Abandon. */
    if (mode == 9) { c->saved = f->token; return action(RETURN, 77); }
    if (mode == 10) {
        if (!c->saved.slot) c->saved = f->token;
        else return resume(c->saved, 0); /* Old token consumed by first perform. */
    }
    if (mode == 6 && f->clause_of->bias == 100 && f->pc++ == 0) {
        return enter(&LEAF, 2, 2, 7, 1, 0);
    }
    I answer = f->v[0]+f->clause_of->bias;
    if (mode == 6 && f->clause_of->bias == 100) answer += f->input;
    return resume(f->token, answer);
}
static Action root(Context *c, Frame *f) {
    I mode = f->v[0];
    switch (f->pc++) {
    case 0:
        switch (mode) {
        case 1: return enter(&SUM_WORK, 5, 1, 100, 1, 0);
        case 2: return enter(&SUM_WORK, 9, 1, 17, 1, 0);
        case 3: return enter(&SUM_STEP, 0, 1, 1, 1, 0);
        case 4: return enter(&NESTED, 0, 1, 100, 1, 0);
        case 5: return enter(&DEEP, 0, 1, 5, 1, 0);
        case 6: return enter(&LEAF, 1, 1, 100, 1, 0);
        case 7: return enter(choose_worker(5), 5, 1, 100, 1, 0);
        case 8: case 9: return enter(&DEEP, 0, 1, 5, 2, 1);
        case 10: return enter(&WORK, 5, 1, 100, 1, 0);
        case 11: return call(&WORK, 1); /* Prior review's unhandled worker call. */
        case 12: return enter(&LEAF, 1, 1, 5, 2, 1);
        case 13:
            ++c->foreign_depth; ++c->native_calls;
            f->v[1] = foreign_leaf(4); --c->foreign_depth;
            return enter(&LEAF, 1, 1, f->v[1], 1, 0);
        case 14:
            ++c->foreign_depth; foreign_callback(c, callback); --c->foreign_depth;
            return action(RETURN, 0);
        case 15: return call(&BAD_DESCRIPTOR, 0);
        case 16: return enter(&MIX_REGION, 0, 1, 100, 1, 0);
        case 17: return enter(choose_worker(c->seed), c->seed, 1, 100, 1, 0);
        case 18: case 19: case 20: case 21: case 22: case 23:
        case 24: case 25: case 26: case 27: case 28:
            return call(&CONTROL, mode);
        default: return action(BAD_PC, 0);
        }
    case 1:
        if (mode == 3) { f->v[1] = f->input; return enter(&SUM_STEP, 0, 1, 7, 1, 0); }
        return action(RETURN, f->input);
    case 2: return action(RETURN, f->v[1]*10000+f->input);
    default: return action(BAD_PC, 0);
    }
}
#define DESC(name, fn) const Descriptor name = {1, 1, fn}
DESC(WORK, work); DESC(STEP, step); DESC(SUM_WORK, sum_work); DESC(SUM_STEP, sum_step);
DESC(LEAF, leaf); DESC(NESTED, nested); DESC(DEEP, deep); DESC(CLAUSE, clause);
DESC(ROOT, root); DESC(MIXED, mixed);

int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) return 2;
    I mode = strtoll(argv[1], NULL, 10);
    Context *c = calloc(1, sizeof(*c));
    if (!c) return 3;
    c->task = 1;
    c->seed = argc == 3 ? strtoll(argv[2], NULL, 10) : 0;
    I value = run(c, &ROOT, mode);
    if (mode == 9) (void)validate_token(c, c->saved, NULL);
    /* Check cleanup uniqueness independently of the live-frame count. */
    unsigned seen[513] = {0};
    for (unsigned i = 0; i < c->nc; ++i)
        if (!c->cleanup[i] || c->cleanup[i] > c->nf || seen[c->cleanup[i]]++) return 4;
    if (c->live || c->drops != c->nf || c->nc != c->nf) return 5;
    if (!verify_control(c, mode)) return 7;
    if (mode == 8 || mode == 9) {
        const unsigned expected[] = {4, 3, 2, 1};
        if (c->nc != 4 || memcmp(c->cleanup, expected, sizeof(expected))) return 6;
    }
    if (c->error) printf("%s cleanup=%u/%u", c->error, c->drops, c->nf);
    else printf("%lld effects=%lld cleanup=%u/%u native=%lld",
                (long long)value, (long long)c->effects, c->drops, c->nf, (long long)c->native_calls);
    if (mode >= 18) {
        printf(" trace=");
        for (unsigned i = 0; i < c->nc; ++i) printf("%s%u", i ? "," : "", c->cleanup[i]);
    }
    printf("\n");
    int status = c->error ? 64 : 0;
    free(c);
    return status;
}
