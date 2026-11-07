%option noyywrap yylineno nodefault noinput nounput
%{
#include "tariff.tab.h"
%}
%%
[ \t\r\n]+       ;
"//"[^\r\n]*       ;
"fn"             return FN;
"let"            return LET;
"if"             return IF;
"else"           return ELSE;
"while"          return WHILE;
"return"         return RETURN;
"=="             return EQ;
"!="             return NE;
"<="             return LE;
">="             return GE;
[a-zA-Z_][a-zA-Z_0-9]* { yylval.text=c(yytext); return ID; }
[0-9]+           {
    /* Tariff integers are decimal even when their spelling starts with zero. */
    const char *decimal=yytext;
    while (decimal[0]=='0' && decimal[1]) ++decimal;
    yylval.text=c(decimal); return INT;
}
[(){};,=+*/<>-] return yytext[0];
.                return INVALID;
%%
