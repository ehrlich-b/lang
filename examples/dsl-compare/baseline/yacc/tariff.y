%{
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "text.h"
int yylex(void);
void yyerror(const char *message);
extern FILE *yyin;
extern int yylineno;
Text *prototypes;
%}
%code requires { #include "text.h" }
%define parse.error detailed
%expect 0
%union { Text *text; }
%token FN LET IF ELSE WHILE RETURN EQ NE LE GE INVALID
%token <text> ID INT
%type <text> program function parameters parameter_list block statements statement
%type <text> binding assignment conditional otherwise loop returning expression
%type <text> equality comparison addition product unary primary call arguments argument_list
%%
program: function { $$=$1; } | program function { $$=cat($1,$2); };
function: FN ID '(' parameters ')' block {
    Text *signature=cat(c("int64_t "),cat($2,cat(c("("),cat($4,c(")")))));
    prototypes=cat(prototypes,cat(signature,c(";\n")));
    $$=cat(signature,$6);
    /* Emit only after the complete parse has succeeded. */
    result=cat(result,$$);
};
parameters: %empty { $$=c("void"); } | parameter_list { $$=$1; };
parameter_list: ID { $$=cat(c("int64_t "),$1); }
    | parameter_list ',' ID { $$=cat($1,cat(c(", int64_t "),$3)); };
block: '{' statements '}' { $$=cat(c("{\n"),cat($2,c("}\n"))); };
statements: %empty { $$=c(""); } | statements statement { $$=cat($1,$2); };
statement: binding | assignment | conditional | loop | returning;
binding: LET ID '=' expression ';' { $$=cat(c("int64_t "),cat($2,cat(c("="),cat($4,c(";\n"))))); };
assignment: ID '=' expression ';' { $$=cat($1,cat(c("="),cat($3,c(";\n")))); };
conditional: IF '(' expression ')' block otherwise { $$=cat(c("if("),cat($3,cat(c(")"),cat($5,$6)))); };
otherwise: %empty { $$=c(""); } | ELSE block { $$=cat(c("else "),$2); };
loop: WHILE '(' expression ')' block { $$=cat(c("while("),cat($3,cat(c(")"),$5))); };
returning: RETURN expression ';' { $$=cat(c("return "),cat($2,c(";\n"))); };
expression: equality;
equality: comparison | equality EQ comparison { $$=binary($1,"==",$3); }
    | equality NE comparison { $$=binary($1,"!=",$3); };
comparison: addition | comparison '<' addition { $$=binary($1,"<",$3); }
    | comparison '>' addition { $$=binary($1,">",$3); }
    | comparison LE addition { $$=binary($1,"<=",$3); }
    | comparison GE addition { $$=binary($1,">=",$3); };
addition: product | addition '+' product { $$=binary($1,"+",$3); }
    | addition '-' product { $$=binary($1,"-",$3); };
product: unary | product '*' unary { $$=binary($1,"*",$3); }
    | product '/' unary { $$=binary($1,"/",$3); };
unary: primary | '-' unary { $$=cat(c("(-"),cat($2,c(")"))); };
primary: INT | call | ID | '(' expression ')' { $$=cat(c("("),cat($2,c(")"))); };
call: ID '(' arguments ')' { $$=cat($1,cat(c("("),cat($3,c(")")))); };
arguments: %empty { $$=c(""); } | argument_list;
argument_list: expression | argument_list ',' expression { $$=cat($1,cat(c(","),$3)); };
%%
void yyerror(const char *message) { fprintf(stderr,"tariff:%d: %s\n",yylineno,message); }
int main(int argc, char **argv) {
    if (argc!=2 || !(yyin=fopen(argv[1],"r"))) return 2;
    int failed=yyparse();
    fclose(yyin);
    if (failed) return 1;
    puts("#include <stdint.h>");
    emit(prototypes); emit(result);
    return 0;
}
