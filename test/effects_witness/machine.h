#ifndef EFFECT_MACHINE_H
#define EFFECT_MACHINE_H
#include <stdint.h>
#include <stddef.h>

/* Hand-lowered witness, not a lang compiler or a public runtime ABI. */
typedef int64_t I;
typedef struct Context Context;
typedef struct Frame Frame;
typedef struct Handler Handler;
typedef struct Descriptor Descriptor;
typedef struct { unsigned slot, task; } Token;
/* RETURN completes a generated frame; SOURCE_* retain lexical source targets. */
typedef enum { RETURN, CALL, ENTER, PERFORM, RESUME,
               SOURCE_RETURN, SOURCE_BREAK, SOURCE_CONTINUE, BAD_PC } Tag;
typedef struct {
    Tag tag;
    I value, scale, bias, return_bias;
    unsigned effect;
    const Descriptor *target, *clause;
    Frame *owner, *environment;
    unsigned next_pc;
    Token token;
} Action;
struct Descriptor { unsigned abi, signature; Action (*step)(Context *, Frame *); };
struct Frame {
    const Descriptor *code;
    Frame *caller;
    Frame *lexical;
    Handler *scope, *lifetime, *completion, *clause_of;
    I v[8], input;
    Token token;
    unsigned pc, live, id;
};
struct Handler {
    Handler *parent, *lifetime_parent;
    Frame *owner, *root;
    Frame *environment;
    const Descriptor *clause;
    unsigned effect, live;
    I bias, scale, return_bias;
};
typedef enum { FRESH, USED, ABANDONED } TokenState;
typedef struct { Frame *top, *clause; Handler *handler; TokenState state; } Entry;
struct Context {
    Frame frames[512]; Handler handlers[128]; Entry tokens[256];
    unsigned nf, nh, nt, task, foreign_depth, live, drops, dispatches;
    unsigned cleanup[512], nc;
    I effects, native_calls, seed;
    Token saved;
    const char *error;
};
extern const Descriptor WORK, STEP, CLAUSE, ROOT, SUM_WORK, SUM_STEP, LEAF,
    NESTED, DEEP, MIXED, CONTROL;
int verify_control(Context *ctx, I mode);
Action action(Tag tag, I value);
Action call(const Descriptor *target, I argument);
Action enter(const Descriptor *body, I argument, unsigned effect, I bias, I scale, I return_bias);
Action perform(unsigned effect, I value);
Action resume(Token token, I value);
Action source_exit(Tag tag, Frame *owner, unsigned next_pc, I value);
I run(Context *ctx, const Descriptor *root, I argument);
int validate_token(Context *ctx, Token token, Frame *clause);
int may_suspend(Context *ctx);
I foreign_leaf(I value);
void foreign_callback(Context *ctx, void (*callback)(Context *));
const Descriptor *choose_worker(I selector);
#endif
