#ifndef TARIFF_TEXT_H
#define TARIFF_TEXT_H
typedef struct Text { const char *value; struct Text *left, *right; } Text;
Text *c(const char *value);
Text *cat(Text *left, Text *right);
Text *binary(Text *left, const char *op, Text *right);
void emit(Text *text);
extern Text *result;
#endif
