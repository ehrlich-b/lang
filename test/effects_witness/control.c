#include "machine.h"

/* Hand-lowered lexical exits/captures. Source and independent direct-style
 * oracles are in control-sources.lang, flow-exits.lang and run.py. */
static const Descriptor REGION, EXIT_BODY, EXIT_CLAUSE, COUNT, YIELD_CLAUSE,
    HOST_BODY, HOST_CLAUSE, HOSTED, HOSTED_BODY, HOSTED_CLAUSE;

static Action handle(const Descriptor *body, I x, unsigned effect,
                     const Descriptor *clause, Frame *environment) {
    Action a = enter(body, x, effect, 0, 10, 7);
    a.clause = clause; a.environment = environment; return a;
}
static Action leave(Frame *f) {
    Frame *owner = f->lexical;
    I mode = owner->v[0];
    if (mode == 18 || mode == 19)
        return source_exit(SOURCE_RETURN, owner, 0, 40 + ++owner->v[3]);
    owner->v[1] += owner->v[2];
    return source_exit(mode == 20 || mode == 22 ? SOURCE_BREAK : SOURCE_CONTINUE,
                       owner, mode == 20 || mode == 22 ? 20 : 10, 0);
}
static Action exit_body(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) {
        I mode = f->lexical->v[0];
        if (mode == 19 || mode == 22 || mode == 23) return leave(f);
        return perform(1, 10); /* Skip the inner Effect 2 prompt. */
    }
    return action(RETURN, 9000); /* Must never run. */
}
static Action region(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return handle(&EXIT_BODY, 0, 2, &EXIT_CLAUSE, f->lexical);
    return action(RETURN, 9000); /* Must never run or apply return clauses. */
}
static Action exit_clause(Context *c, Frame *f) {
    ++c->effects;
    return leave(f);
}
static Action count(Context *c, Frame *f) {
    if (f->pc == 1) { ++f->v[1]; f->pc = 0; }
    if (f->v[1] == f->v[0]) return action(RETURN, 0);
    /* The resumed body sees the same owner cell the clause mutated. */
    if (f->lexical->v[0] == 25 &&
        f->lexical->v[1] != f->v[1] * (f->v[1] - 1) / 2) {
        c->error = "E_CAPTURE"; return action(BAD_PC, 0);
    }
    f->pc = 1;
    return perform(1, f->v[1]);
}
static Action yield_clause(Context *c, Frame *f) {
    ++c->effects;
    if (f->lexical->v[0] == 24 && f->v[0] == 3)
        return source_exit(SOURCE_RETURN, f->lexical, 0, f->v[0]);
    I *total = &f->lexical->v[1]; /* By reference to the owner, never a copy. */
    *total += f->v[0];
    return resume(f->token, 0);
}
static Action hosted_body(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) return perform(1, 10);
    return action(RETURN, f->input + 1);
}
static Action hosted_clause(Context *c, Frame *f) {
    ++c->effects;
    return resume(f->token, f->v[0] + 20);
}
static Action hosted(Context *c, Frame *f) {
    (void)c;
    if (f->pc++ == 0) {
        Action a = handle(&HOSTED_BODY, 0, 1, &HOSTED_CLAUSE, f);
        a.scale = 2; a.return_bias = 3;
        return a;
    }
    return action(RETURN, f->input);
}
/* Ordinary native ABI, effect-closed to its caller. Dispatchers nest on the
 * native stack; task identity, registry and foreign_depth are shared. */
static I native_host(Context *c, I mode) {
    ++c->native_calls;
    return run(c, mode == 27 ? &HOSTED_BODY : &HOSTED, 0);
}
static Action host_body(Context *c, Frame *f) {
    if (f->pc++ == 0) {
        I mode = f->lexical->v[0];
        if (mode == 28) ++c->foreign_depth;
        I value = native_host(c, mode);
        if (mode == 28) --c->foreign_depth;
        if (c->error) return action(RETURN, 0);
        return perform(1, value);
    }
    return action(RETURN, f->input);
}
static Action host_clause(Context *c, Frame *f) {
    ++c->effects;
    return resume(f->token, f->v[0] + 100);
}
static Action control(Context *c, Frame *f) {
    (void)c;
    I mode = f->v[0];
    switch (f->pc) {
    case 0:
        f->pc = 11;
        if (mode == 24 || mode == 25) {
            Action a = handle(&COUNT, mode == 24 ? 6 : 5, 1, &YIELD_CLAUSE, f);
            a.scale = 0; a.return_bias = 0; /* flow's discarded return clause. */
            return a;
        }
        if (mode >= 26) {
            Action a = handle(&HOST_BODY, 0, 1, &HOST_CLAUSE, f);
            a.scale = 1; a.return_bias = 0;
            return a;
        }
        f->pc = 10;
        /* fall through */
    case 10:
        if (f->v[2] == 4) return action(RETURN, f->v[2] * 100 + f->v[1]);
        ++f->v[2]; f->pc = 11;
        return handle(&REGION, 0, 1, &EXIT_CLAUSE, f);
    case 11:
        if (mode == 25) return action(RETURN, f->v[1]);
        if (mode >= 26) return action(RETURN, f->input);
        return action(RETURN, 9000 + f->input); /* Wrong fallthrough sentinel. */
    case 20: return action(RETURN, f->v[2] * 100 + f->v[1]);
    default: return action(BAD_PC, 0);
    }
}
#define DESC(name, fn) const Descriptor name = {1, 1, fn}
DESC(CONTROL, control);
#define LOCAL(name, fn) static const Descriptor name = {1, 1, fn}
LOCAL(REGION, region); LOCAL(EXIT_BODY, exit_body); LOCAL(EXIT_CLAUSE, exit_clause);
LOCAL(COUNT, count); LOCAL(YIELD_CLAUSE, yield_clause); LOCAL(HOST_BODY, host_body);
LOCAL(HOST_CLAUSE, host_clause); LOCAL(HOSTED, hosted);
LOCAL(HOSTED_BODY, hosted_body); LOCAL(HOSTED_CLAUSE, hosted_clause);

int verify_control(Context *c, I mode) {
    if (mode < 18) return 1;
    if (c->foreign_depth) return 0;
    for (unsigned i = 0; i < c->nh; ++i) if (c->handlers[i].live) return 0;
    for (unsigned i = 0; i < c->nt; ++i) {
        if (c->tokens[i].state == FRESH) return 0;
        if (mode <= 23 && c->tokens[i].state != ABANDONED) return 0;
        if (mode == 24 && c->tokens[i].state != (i == 3 ? ABANDONED : USED)) return 0;
    }
    if (mode <= 23) {
        unsigned at = 0, next = 3;
        unsigned iterations = mode == 21 || mode == 23 ? 4 : 1;
        unsigned width = mode == 19 || mode >= 22 ? 2 : 3;
        for (unsigned i = 0; i < iterations; ++i) {
            for (unsigned j = width; j; --j)
                if (c->cleanup[at++] != next + j - 1) return 0;
            next += width;
        }
        if (c->cleanup[at++] != 2 || c->cleanup[at++] != 1 || at != c->nc) return 0;
    }
    return 1;
}
