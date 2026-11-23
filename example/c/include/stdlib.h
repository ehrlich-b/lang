#ifndef CX_STDLIB_H
#define CX_STDLIB_H
#include <stddef.h>
void *malloc(size_t);
void *calloc(size_t, size_t);
void *realloc(void *, size_t);
void free(void *);
void exit(int);
int atoi(const char *);
int abs(int);
#endif
