#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "text.h"
Text *result;
Text *c(const char *value) {
    Text *t=calloc(1,sizeof(*t));
    if (!t || !(t->value=strdup(value))) exit(2);
    return t;
}
Text *cat(Text *left, Text *right) {
    Text *t=calloc(1,sizeof(*t));
    if (!t) exit(2);
    t->left=left; t->right=right;
    return t;
}
Text *binary(Text *left, const char *op, Text *right) {
    return cat(c("("),cat(left,cat(c(op),cat(right,c(")")))));
}
void emit(Text *text) {
    size_t count=0, capacity=128;
    Text **stack=malloc(capacity*sizeof(*stack));
    if (!stack) exit(2);
    stack[count++]=text;
    while (count) {
        Text *t=stack[--count];
        if (!t) continue;
        if (t->value) { fputs(t->value,stdout); continue; }
        if (count+2>capacity) {
            capacity*=2; stack=realloc(stack,capacity*sizeof(*stack));
            if (!stack) exit(2);
        }
        stack[count++]=t->right; stack[count++]=t->left;
    }
    free(stack);
}
