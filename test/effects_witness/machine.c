#include "machine.h"
#include <string.h>

Action action(Tag tag, I value) { Action a = {0}; a.tag = tag; a.value = value; return a; }
Action call(const Descriptor *d, I x) { Action a = action(CALL, x); a.target = d; return a; }
Action enter(const Descriptor *d, I x, unsigned e, I b, I s, I rb) {
    Action a = action(ENTER, x); a.target = d; a.clause = &CLAUSE;
    a.effect = e; a.bias = b; a.scale = s; a.value = x;
    /* Return-clause offset is separate from handler reply bias. */
    a.return_bias = rb;
    return a;
}
Action perform(unsigned e, I x) { Action a = action(PERFORM, x); a.effect = e; return a; }
Action resume(Token k, I x) { Action a = action(RESUME, x); a.token = k; return a; }
Action source_exit(Tag tag, Frame *owner, unsigned pc, I value) {
    Action a = action(tag, value); a.owner = owner; a.next_pc = pc; return a;
}

static int within(Handler *scope, Handler *boundary) {
    for (; scope; scope = scope->lifetime_parent) if (scope == boundary) return 1;
    return 0;
}
static void drop(Context *c, Frame *f) {
    if (f && f->live) {
        f->live = 0; --c->live; ++c->drops;
        c->cleanup[c->nc++] = f->id;
    }
}
static void retire(Context *c, Handler *h) {
    /* Invalidate before any cleanup can observe the abandoned continuation. */
    for (unsigned i = 0; i < c->nt; ++i)
        if (within(c->tokens[i].handler, h) && c->tokens[i].state == FRESH)
            c->tokens[i].state = ABANDONED;
    for (unsigned i = c->nf; i; --i)
        if (within(c->frames[i-1].lifetime, h)) drop(c, &c->frames[i-1]);
    for (unsigned i = 0; i < c->nh; ++i)
        if (within(&c->handlers[i], h)) c->handlers[i].live = 0;
}
static Frame *frame(Context *c, const Descriptor *d, I x, Frame *parent,
                    Handler *scope, Handler *lifetime) {
    if (!d || d->abi != 1 || d->signature != 1 || !d->step) {
        c->error = "E_INDIRECT_ABI"; return NULL;
    }
    if (c->nf == 512) { c->error = "E_LIMIT"; return NULL; }
    Frame *f = &c->frames[c->nf++];
    memset(f, 0, sizeof(*f));
    f->id = c->nf; f->live = 1; ++c->live;
    f->code = d; f->v[0] = x; f->caller = parent;
    f->lexical = f;
    f->scope = scope; f->lifetime = lifetime;
    return f;
}
int may_suspend(Context *c) {
    if (c->foreign_depth) { c->error = "E_FOREIGN_SUSPEND"; return 0; }
    return 1;
}
int validate_token(Context *c, Token k, Frame *clause) {
    if (k.task != c->task || !k.slot || k.slot > c->nt) {
        c->error = "E_TOKEN"; return 0;
    }
    Entry *t = &c->tokens[k.slot-1];
    if (!t->handler->live) { c->error = "E_ESCAPE"; return 0; }
    if (t->state != FRESH) { c->error = "E_USED"; return 0; }
    if (clause != t->clause || !clause || !clause->live) {
        c->error = "E_TOKEN_SCOPE"; return 0;
    }
    return 1;
}
I run(Context *c, const Descriptor *root, I argument) {
    /* A native, effect-closed host starts a nested dispatcher on the same task.
     * Its root has no outward scope; cleanup must preserve the outer host. */
    unsigned first_frame = c->nf, first_handler = c->nh, first_token = c->nt;
    Frame *f = frame(c, root, argument, NULL, NULL, NULL);
    I result = 0;
    while (f && !c->error) {
        ++c->dispatches;
        Action a = f->code->step(c, f);
        if (c->error) break;
        if (a.tag == SOURCE_RETURN || a.tag == SOURCE_BREAK || a.tag == SOURCE_CONTINUE) {
            /* Targets are compiler-resolved lexical owners, never token data.
             * Check ancestry before touching the target; native hosts are roots. */
            Frame *p = f;
            while (p && p != a.owner) p = p->caller;
            if (!p || !p->live) { c->error = "E_EXIT_TARGET"; break; }
            Handler *boundary = f->lifetime;
            while (boundary && boundary->lifetime_parent != p->lifetime)
                boundary = boundary->lifetime_parent;
            if (!boundary || boundary == p->lifetime) {
                c->error = "E_EXIT_TARGET"; break;
            }
            retire(c, boundary); /* Active clause, captured body, inner prompts. */
            f = p;
            if (a.tag != SOURCE_RETURN) { f->pc = a.next_pc; continue; }
            a.tag = RETURN; /* Owner's own return, after child prompts close. */
        }
        switch (a.tag) {
        case CALL:
            f = frame(c, a.target, a.value, f, f->scope, f->lifetime);
            break;
        case ENTER: {
            if (c->nh == 128) { c->error = "E_LIMIT"; break; }
            Handler *h = &c->handlers[c->nh++];
            memset(h, 0, sizeof(*h)); h->live = 1;
            h->parent = f->scope; h->lifetime_parent = f->lifetime;
            h->owner = f; h->clause = a.clause;
            h->environment = a.environment ? a.environment : f;
            h->effect = a.effect; h->bias = a.bias; h->scale = a.scale;
            h->return_bias = a.return_bias;
            h->root = frame(c, a.target, a.value, f, h, h);
            if (h->root) {
                h->root->completion = h;
                h->root->lexical = h->environment;
            }
            f = h->root;
            break;
        }
        case PERFORM: {
            if (!may_suspend(c)) break;
            Handler *h = f->scope;
            while (h && h->effect != a.effect) h = h->parent;
            if (!h || !h->live) { c->error = "E_UNHANDLED"; break; }
            if (c->nt == 256) { c->error = "E_LIMIT"; break; }
            Entry *t = &c->tokens[c->nt++];
            t->top = f; t->handler = h; t->state = FRESH;
            Frame *cl = frame(c, h->clause, a.value, h->owner, h->parent, h);
            if (!cl) break;
            cl->clause_of = h; cl->token = (Token){c->nt, c->task}; t->clause = cl;
            cl->lexical = h->environment;
            f = cl;
            break;
        }
        case RESUME: {
            if (!may_suspend(c) || !validate_token(c, a.token, f)) break;
            Entry *t = &c->tokens[a.token.slot-1];
            t->state = USED; /* Consume before transfer, never on return. */
            drop(c, f); f = t->top; f->input = a.value;
            break;
        }
        case RETURN: {
            Frame *parent = f->caller;
            I value = a.value;
            if (f->clause_of) retire(c, f->clause_of); /* Abandon, bypass return clause. */
            else if (f->completion) {
                Handler *h = f->completion;
                value = value * h->scale + h->return_bias;
                retire(c, h);
            } else drop(c, f);
            if (parent) parent->input = value; else result = value;
            f = parent;
            break;
        }
        default: c->error = "E_PC"; break;
        }
    }
    /* Error path and normal root return dispose every retained activation once. */
    for (unsigned i = first_token; i < c->nt; ++i)
        if (c->tokens[i].state == FRESH) c->tokens[i].state = ABANDONED;
    for (unsigned i = c->nf; i > first_frame; --i) drop(c, &c->frames[i-1]);
    for (unsigned i = first_handler; i < c->nh; ++i) c->handlers[i].live = 0;
    return result;
}
