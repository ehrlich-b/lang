"""ANTLR's generated parser and visitor lower Tariff to C, never interpret it."""
import sys
from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener
from TariffLexer import TariffLexer
from TariffParser import TariffParser
from TariffVisitor import TariffVisitor


class Errors(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"tariff:{line}:{column + 1}: {msg}", file=sys.stderr)
        raise SystemExit(1)


class Emit(TariffVisitor):
    def signature(self, ctx):
        names = ctx.parameters().ID() if ctx.parameters() else []
        params = ', '.join('int64_t ' + n.getText() for n in names) or 'void'
        return f'int64_t {ctx.ID().getText()}({params})'

    def visitProgram(self, ctx):
        functions = ctx.function()
        return ('#include <stdint.h>\n' +
                '\n'.join(self.signature(f) + ';' for f in functions) + '\n' +
                '\n'.join(self.visit(f) for f in functions))

    def visitFunction(self, ctx):
        return self.signature(ctx) + self.visit(ctx.block())

    def visitBlock(self, ctx):
        return '{\n' + ''.join(self.visit(s) for s in ctx.statement()) + '}\n'

    def visitStatement(self, ctx):
        return self.visit(ctx.getChild(0))

    def visitBinding(self, ctx):
        return 'int64_t ' + ctx.ID().getText() + '=' + self.visit(ctx.expression()) + ';\n'

    def visitAssignment(self, ctx):
        return ctx.ID().getText() + '=' + self.visit(ctx.expression()) + ';\n'

    def visitConditional(self, ctx):
        other = self.visit(ctx.otherwise()) if ctx.otherwise() else ''
        return 'if(' + self.visit(ctx.expression()) + ')' + self.visit(ctx.block()) + other

    def visitOtherwise(self, ctx):
        return 'else ' + self.visit(ctx.block())

    def visitLoop(self, ctx):
        return 'while(' + self.visit(ctx.expression()) + ')' + self.visit(ctx.block())

    def visitReturning(self, ctx):
        return 'return ' + self.visit(ctx.expression()) + ';\n'

    def visitExpression(self, ctx):
        return self.visit(ctx.equality())

    def fold(self, ctx):
        value = self.visit(ctx.getChild(0))
        for i in range(1, ctx.getChildCount(), 2):
            value = '(' + value + ctx.getChild(i).getText() + self.visit(ctx.getChild(i + 1)) + ')'
        return value

    visitEquality = fold
    visitComparison = fold
    visitAddition = fold
    visitProduct = fold

    def visitUnary(self, ctx):
        return '(-' + self.visit(ctx.unary()) + ')' if ctx.unary() else self.visit(ctx.primary())

    def visitPrimary(self, ctx):
        if ctx.call():
            return self.visit(ctx.call())
        if ctx.expression():
            return '(' + self.visit(ctx.expression()) + ')'
        if ctx.INT():
            return ctx.getText().lstrip('0') or '0'
        return ctx.getText()

    def visitCall(self, ctx):
        args = ctx.arguments().expression() if ctx.arguments() else []
        return ctx.ID().getText() + '(' + ','.join(self.visit(a) for a in args) + ')'


def main():
    lexer = TariffLexer(FileStream(sys.argv[1], encoding='utf-8'))
    lexer.removeErrorListeners()
    lexer.addErrorListener(Errors())
    parser = TariffParser(CommonTokenStream(lexer))
    parser.removeErrorListeners()
    parser.addErrorListener(Errors())
    tree = parser.program()
    print(Emit().visit(tree))


if __name__ == '__main__':
    main()
