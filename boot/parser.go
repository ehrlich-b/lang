package main

import "fmt"

type Parser struct {
	tokens  []Token
	current int
	errors  []string
}

func NewParser(tokens []Token) *Parser {
	return &Parser{tokens: tokens}
}

func (p *Parser) Parse() (*Program, []string) {
	prog := &Program{}
	for !p.isAtEnd() {
		decl := p.declaration()
		if decl != nil {
			prog.Decls = append(prog.Decls, decl)
		}
	}
	return prog, p.errors
}

// --- Declarations ---

func (p *Parser) declaration() Decl {
	switch {
	case p.match(TOKEN_FUNC):
		return p.funcDecl()
	case p.match(TOKEN_STRUCT):
		return p.structDecl()
	case p.match(TOKEN_VAR):
		return p.varDecl()
	default:
		p.error("expected declaration")
		p.advance()
		return nil
	}
}

func (p *Parser) funcDecl() *FuncDecl {
	name := p.expect(TOKEN_IDENT, "expected function name")
	p.expect(TOKEN_LPAREN, "expected '(' after function name")

	var params []Param
	if !p.check(TOKEN_RPAREN) {
		for {
			pname := p.expect(TOKEN_IDENT, "expected parameter name")
			ptype := p.parseType()
			params = append(params, Param{Name: pname.Lexeme, Type: ptype})
			if !p.match(TOKEN_COMMA) {
				break
			}
		}
	}
	p.expect(TOKEN_RPAREN, "expected ')' after parameters")

	var retType Type
	if !p.check(TOKEN_LBRACE) {
		retType = p.parseType()
	}

	body := p.block()
	return &FuncDecl{
		Name:    name.Lexeme,
		Params:  params,
		RetType: retType,
		Body:    body,
	}
}

func (p *Parser) structDecl() *StructDecl {
	name := p.expect(TOKEN_IDENT, "expected struct name")
	p.expect(TOKEN_LBRACE, "expected '{' after struct name")

	var fields []Field
	for !p.check(TOKEN_RBRACE) && !p.isAtEnd() {
		fname := p.expect(TOKEN_IDENT, "expected field name")
		ftype := p.parseType()
		p.expect(TOKEN_SEMICOLON, "expected ';' after field")
		fields = append(fields, Field{Name: fname.Lexeme, Type: ftype})
	}
	p.expect(TOKEN_RBRACE, "expected '}' after struct fields")

	return &StructDecl{Name: name.Lexeme, Fields: fields}
}

func (p *Parser) varDecl() *VarDecl {
	name := p.expect(TOKEN_IDENT, "expected variable name")
	typ := p.parseType()

	var init Expr
	if p.match(TOKEN_EQ) {
		init = p.expression()
	}
	p.expect(TOKEN_SEMICOLON, "expected ';' after variable declaration")

	return &VarDecl{Name: name.Lexeme, Type: typ, Init: init}
}

// --- Types ---

func (p *Parser) parseType() Type {
	if p.match(TOKEN_STAR) {
		elem := p.parseType()
		return &PtrType{Elem: elem}
	}
	if p.match(TOKEN_LBRACKET) {
		size := p.expect(TOKEN_NUMBER, "expected array size")
		p.expect(TOKEN_RBRACKET, "expected ']' after array size")
		elem := p.parseType()
		// Parse size (simplified, assumes decimal)
		sizeVal := 0
		for _, c := range size.Lexeme {
			sizeVal = sizeVal*10 + int(c-'0')
		}
		return &ArrayType{Size: sizeVal, Elem: elem}
	}

	// Base type
	tok := p.advance()
	switch tok.Type {
	case TOKEN_I8, TOKEN_I16, TOKEN_I32, TOKEN_I64,
		TOKEN_U8, TOKEN_U16, TOKEN_U32, TOKEN_U64,
		TOKEN_BOOL, TOKEN_VOID, TOKEN_IDENT:
		return &BaseType{Name: tok.Lexeme}
	default:
		p.errorAt(tok, "expected type")
		return &BaseType{Name: "error"}
	}
}

// --- Statements ---

func (p *Parser) block() *BlockStmt {
	p.expect(TOKEN_LBRACE, "expected '{'")
	var stmts []Stmt
	for !p.check(TOKEN_RBRACE) && !p.isAtEnd() {
		stmts = append(stmts, p.statement())
	}
	p.expect(TOKEN_RBRACE, "expected '}'")
	return &BlockStmt{Stmts: stmts}
}

func (p *Parser) statement() Stmt {
	switch {
	case p.match(TOKEN_VAR):
		return p.varDecl()
	case p.match(TOKEN_IF):
		return p.ifStmt()
	case p.match(TOKEN_WHILE):
		return p.whileStmt()
	case p.match(TOKEN_RETURN):
		return p.returnStmt()
	case p.check(TOKEN_LBRACE):
		return p.block()
	default:
		return p.exprStmt()
	}
}

func (p *Parser) ifStmt() *IfStmt {
	cond := p.expression()
	then := p.block()

	var els Stmt
	if p.match(TOKEN_ELSE) {
		if p.check(TOKEN_IF) {
			p.advance()
			els = p.ifStmt()
		} else {
			els = p.block()
		}
	}
	return &IfStmt{Cond: cond, Then: then, Else: els}
}

func (p *Parser) whileStmt() *WhileStmt {
	cond := p.expression()
	body := p.block()
	return &WhileStmt{Cond: cond, Body: body}
}

func (p *Parser) returnStmt() *ReturnStmt {
	var value Expr
	if !p.check(TOKEN_SEMICOLON) {
		value = p.expression()
	}
	p.expect(TOKEN_SEMICOLON, "expected ';' after return")
	return &ReturnStmt{Value: value}
}

func (p *Parser) exprStmt() *ExprStmt {
	expr := p.expression()
	p.expect(TOKEN_SEMICOLON, "expected ';' after expression")
	return &ExprStmt{Expr: expr}
}

// --- Expressions (precedence climbing) ---

func (p *Parser) expression() Expr {
	return p.assignment()
}

func (p *Parser) assignment() Expr {
	expr := p.orExpr()
	if p.match(TOKEN_EQ) {
		value := p.assignment()
		return &BinaryExpr{Op: TOKEN_EQ, Left: expr, Right: value}
	}
	return expr
}

func (p *Parser) orExpr() Expr {
	expr := p.andExpr()
	for p.match(TOKEN_PIPEPIPE) {
		right := p.andExpr()
		expr = &BinaryExpr{Op: TOKEN_PIPEPIPE, Left: expr, Right: right}
	}
	return expr
}

func (p *Parser) andExpr() Expr {
	expr := p.equality()
	for p.match(TOKEN_AMPAMP) {
		right := p.equality()
		expr = &BinaryExpr{Op: TOKEN_AMPAMP, Left: expr, Right: right}
	}
	return expr
}

func (p *Parser) equality() Expr {
	expr := p.comparison()
	for p.match(TOKEN_EQEQ, TOKEN_BANGEQ) {
		op := p.previous().Type
		right := p.comparison()
		expr = &BinaryExpr{Op: op, Left: expr, Right: right}
	}
	return expr
}

func (p *Parser) comparison() Expr {
	expr := p.additive()
	for p.match(TOKEN_LT, TOKEN_GT, TOKEN_LTEQ, TOKEN_GTEQ) {
		op := p.previous().Type
		right := p.additive()
		expr = &BinaryExpr{Op: op, Left: expr, Right: right}
	}
	return expr
}

func (p *Parser) additive() Expr {
	expr := p.mult()
	for p.match(TOKEN_PLUS, TOKEN_MINUS) {
		op := p.previous().Type
		right := p.mult()
		expr = &BinaryExpr{Op: op, Left: expr, Right: right}
	}
	return expr
}

func (p *Parser) mult() Expr {
	expr := p.unary()
	for p.match(TOKEN_STAR, TOKEN_SLASH, TOKEN_PERCENT) {
		op := p.previous().Type
		right := p.unary()
		expr = &BinaryExpr{Op: op, Left: expr, Right: right}
	}
	return expr
}

func (p *Parser) unary() Expr {
	if p.match(TOKEN_MINUS, TOKEN_BANG, TOKEN_STAR, TOKEN_AMP) {
		op := p.previous().Type
		expr := p.unary()
		return &UnaryExpr{Op: op, Expr: expr}
	}
	return p.postfix()
}

func (p *Parser) postfix() Expr {
	expr := p.primary()
	for {
		if p.match(TOKEN_LPAREN) {
			expr = p.finishCall(expr)
		} else if p.match(TOKEN_LBRACKET) {
			index := p.expression()
			p.expect(TOKEN_RBRACKET, "expected ']' after index")
			expr = &IndexExpr{Expr: expr, Index: index}
		} else if p.match(TOKEN_DOT) {
			name := p.expect(TOKEN_IDENT, "expected field name")
			expr = &FieldExpr{Expr: expr, Field: name.Lexeme}
		} else {
			break
		}
	}
	return expr
}

func (p *Parser) finishCall(callee Expr) Expr {
	var args []Expr
	if !p.check(TOKEN_RPAREN) {
		for {
			args = append(args, p.expression())
			if !p.match(TOKEN_COMMA) {
				break
			}
		}
	}
	p.expect(TOKEN_RPAREN, "expected ')' after arguments")
	return &CallExpr{Func: callee, Args: args}
}

func (p *Parser) primary() Expr {
	switch {
	case p.match(TOKEN_NUMBER):
		return &NumberExpr{Value: p.previous().Lexeme}
	case p.match(TOKEN_STRING):
		return &StringExpr{Value: p.previous().Lexeme}
	case p.match(TOKEN_TRUE):
		return &BoolExpr{Value: true}
	case p.match(TOKEN_FALSE):
		return &BoolExpr{Value: false}
	case p.match(TOKEN_NIL):
		return &NilExpr{}
	case p.match(TOKEN_IDENT):
		return &IdentExpr{Name: p.previous().Lexeme}
	case p.match(TOKEN_LPAREN):
		expr := p.expression()
		p.expect(TOKEN_RPAREN, "expected ')' after expression")
		return &GroupExpr{Expr: expr}
	default:
		p.error("expected expression")
		return &NumberExpr{Value: "0"}
	}
}

// --- Helpers ---

func (p *Parser) match(types ...TokenType) bool {
	for _, t := range types {
		if p.check(t) {
			p.advance()
			return true
		}
	}
	return false
}

func (p *Parser) check(t TokenType) bool {
	if p.isAtEnd() {
		return false
	}
	return p.peek().Type == t
}

func (p *Parser) advance() Token {
	if !p.isAtEnd() {
		p.current++
	}
	return p.previous()
}

func (p *Parser) previous() Token {
	return p.tokens[p.current-1]
}

func (p *Parser) peek() Token {
	return p.tokens[p.current]
}

func (p *Parser) isAtEnd() bool {
	return p.peek().Type == TOKEN_EOF
}

func (p *Parser) expect(t TokenType, msg string) Token {
	if p.check(t) {
		return p.advance()
	}
	p.error(msg)
	return Token{Type: TOKEN_ERROR}
}

func (p *Parser) error(msg string) {
	tok := p.peek()
	p.errorAt(tok, msg)
}

func (p *Parser) errorAt(tok Token, msg string) {
	errMsg := fmt.Sprintf("%d:%d: %s (got %s)", tok.Line, tok.Col, msg, tok.Type)
	p.errors = append(p.errors, errMsg)
}
