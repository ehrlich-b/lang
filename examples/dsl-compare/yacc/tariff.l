%option noyywrap yylineno nodefault noinput nounput
%{
#include "tariff.tab.h"
%}
%%
[ \t\r\n]+       ;
"//"[^\n]*       ;
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
[0-9]+           { yylval.text=c(yytext); return INT; }
[(){};,=+*/%<>-] return yytext[0];
.                return INVALID;
%%
