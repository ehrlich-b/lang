package main

import "fmt"

type Lexer struct {
	source  string
	start   int // start of current token
	current int // current position
	line    int
	col     int
	startCol int
}

func NewLexer(source string) *Lexer {
	return &Lexer{
		source: source,
		line:   1,
		col:    1,
	}
}

func (l *Lexer) ScanTokens() []Token {
	var tokens []Token
	for {
		tok := l.scanToken()
		tokens = append(tokens, tok)
		if tok.Type == TOKEN_EOF || tok.Type == TOKEN_ERROR {
			break
		}
	}
	return tokens
}

func (l *Lexer) scanToken() Token {
	l.skipWhitespace()
	l.start = l.current
	l.startCol = l.col

	if l.isAtEnd() {
		return l.makeToken(TOKEN_EOF)
	}

	c := l.advance()

	if isAlpha(c) {
		return l.identifier()
	}
	if isDigit(c) {
		return l.number()
	}

	switch c {
	case '(':
		return l.makeToken(TOKEN_LPAREN)
	case ')':
		return l.makeToken(TOKEN_RPAREN)
	case '{':
		return l.makeToken(TOKEN_LBRACE)
	case '}':
		return l.makeToken(TOKEN_RBRACE)
	case '[':
		return l.makeToken(TOKEN_LBRACKET)
	case ']':
		return l.makeToken(TOKEN_RBRACKET)
	case ',':
		return l.makeToken(TOKEN_COMMA)
	case ';':
		return l.makeToken(TOKEN_SEMICOLON)
	case '.':
		return l.makeToken(TOKEN_DOT)
	case '+':
		return l.makeToken(TOKEN_PLUS)
	case '-':
		return l.makeToken(TOKEN_MINUS)
	case '*':
		return l.makeToken(TOKEN_STAR)
	case '/':
		return l.makeToken(TOKEN_SLASH)
	case '%':
		return l.makeToken(TOKEN_PERCENT)
	case '&':
		if l.match('&') {
			return l.makeToken(TOKEN_AMPAMP)
		}
		return l.makeToken(TOKEN_AMP)
	case '|':
		if l.match('|') {
			return l.makeToken(TOKEN_PIPEPIPE)
		}
		return l.errorToken("unexpected character '|'")
	case '!':
		if l.match('=') {
			return l.makeToken(TOKEN_BANGEQ)
		}
		return l.makeToken(TOKEN_BANG)
	case '=':
		if l.match('=') {
			return l.makeToken(TOKEN_EQEQ)
		}
		return l.makeToken(TOKEN_EQ)
	case '<':
		if l.match('=') {
			return l.makeToken(TOKEN_LTEQ)
		}
		return l.makeToken(TOKEN_LT)
	case '>':
		if l.match('=') {
			return l.makeToken(TOKEN_GTEQ)
		}
		return l.makeToken(TOKEN_GT)
	case ':':
		if l.match('=') {
			return l.makeToken(TOKEN_COLONEQ)
		}
		return l.makeToken(TOKEN_COLON)
	case '"':
		return l.string()
	}

	return l.errorToken(fmt.Sprintf("unexpected character '%c'", c))
}

func (l *Lexer) skipWhitespace() {
	for {
		if l.isAtEnd() {
			return
		}
		c := l.peek()
		switch c {
		case ' ', '\t', '\r':
			l.advance()
		case '\n':
			l.line++
			l.col = 0
			l.advance()
		case '/':
			if l.peekNext() == '/' {
				// Line comment
				for !l.isAtEnd() && l.peek() != '\n' {
					l.advance()
				}
			} else if l.peekNext() == '*' {
				// Block comment
				l.advance() // consume /
				l.advance() // consume *
				for !l.isAtEnd() {
					if l.peek() == '*' && l.peekNext() == '/' {
						l.advance() // consume *
						l.advance() // consume /
						break
					}
					if l.peek() == '\n' {
						l.line++
						l.col = 0
					}
					l.advance()
				}
			} else {
				return
			}
		default:
			return
		}
	}
}

func (l *Lexer) identifier() Token {
	for isAlphaNumeric(l.peek()) {
		l.advance()
	}
	text := l.source[l.start:l.current]
	if tokType, ok := keywords[text]; ok {
		return l.makeToken(tokType)
	}
	return l.makeToken(TOKEN_IDENT)
}

func (l *Lexer) number() Token {
	for isDigit(l.peek()) {
		l.advance()
	}
	return l.makeToken(TOKEN_NUMBER)
}

func (l *Lexer) string() Token {
	for !l.isAtEnd() && l.peek() != '"' {
		if l.peek() == '\n' {
			l.line++
			l.col = 0
		}
		if l.peek() == '\\' && l.peekNext() != 0 {
			l.advance() // consume backslash
		}
		l.advance()
	}

	if l.isAtEnd() {
		return l.errorToken("unterminated string")
	}

	l.advance() // closing quote
	return l.makeToken(TOKEN_STRING)
}

func (l *Lexer) isAtEnd() bool {
	return l.current >= len(l.source)
}

func (l *Lexer) peek() byte {
	if l.isAtEnd() {
		return 0
	}
	return l.source[l.current]
}

func (l *Lexer) peekNext() byte {
	if l.current+1 >= len(l.source) {
		return 0
	}
	return l.source[l.current+1]
}

func (l *Lexer) advance() byte {
	c := l.source[l.current]
	l.current++
	l.col++
	return c
}

func (l *Lexer) match(expected byte) bool {
	if l.isAtEnd() || l.source[l.current] != expected {
		return false
	}
	l.current++
	l.col++
	return true
}

func (l *Lexer) makeToken(tokType TokenType) Token {
	return Token{
		Type:   tokType,
		Lexeme: l.source[l.start:l.current],
		Line:   l.line,
		Col:    l.startCol,
	}
}

func (l *Lexer) errorToken(msg string) Token {
	return Token{
		Type:   TOKEN_ERROR,
		Lexeme: msg,
		Line:   l.line,
		Col:    l.startCol,
	}
}

func isAlpha(c byte) bool {
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_'
}

func isDigit(c byte) bool {
	return c >= '0' && c <= '9'
}

func isAlphaNumeric(c byte) bool {
	return isAlpha(c) || isDigit(c)
}
