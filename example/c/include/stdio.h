#ifndef CX_STDIO_H
#define CX_STDIO_H
#include <stddef.h>
typedef struct CFile FILE;
int printf(const char *, ...);
int sprintf(char *, const char *, ...);
int puts(const char *);
int putchar(int);
FILE *fopen(const char *, const char *);
int fclose(FILE *);
#define EOF (-1)
int fgetc(FILE *);
int getc(FILE *);
char *fgets(char *, int, FILE *);
int fputc(int, FILE *);
size_t fread(void *, size_t, size_t, FILE *);
size_t fwrite(const void *, size_t, size_t, FILE *);
#endif
