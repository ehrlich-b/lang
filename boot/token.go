package main

type TokenType int

const (
	// Special
	TOKEN_EOF TokenType = iota
	TOKEN_ERROR

	// Literals
	TOKEN_IDENT
	TOKEN_NUMBER
	TOKEN_STRING

	// Keywords
	TOKEN_FUNC
	TOKEN_VAR
	TOKEN_STRUCT
	TOKEN_IF
	TOKEN_ELSE
	TOKEN_WHILE
	TOKEN_RETURN
	TOKEN_TRUE
	TOKEN_FALSE
	TOKEN_NIL

	// Types (also keywords)
	TOKEN_I8
	TOKEN_I16
	TOKEN_I32
	TOKEN_I64
	TOKEN_U8
	TOKEN_U16
	TOKEN_U32
	TOKEN_U64
	TOKEN_BOOL
	TOKEN_VOID

	// Operators
	TOKEN_PLUS     // +
	TOKEN_MINUS    // -
	TOKEN_STAR     // *
	TOKEN_SLASH    // /
	TOKEN_PERCENT  // %
	TOKEN_AMP      // &
	TOKEN_BANG     // !
	TOKEN_EQ       // =
	TOKEN_EQEQ     // ==
	TOKEN_BANGEQ   // !=
	TOKEN_LT       // <
	TOKEN_GT       // >
	TOKEN_LTEQ     // <=
	TOKEN_GTEQ     // >=
	TOKEN_AMPAMP   // &&
	TOKEN_PIPEPIPE // ||

	// Punctuation
	TOKEN_LPAREN    // (
	TOKEN_RPAREN    // )
	TOKEN_LBRACE    // {
	TOKEN_RBRACE    // }
	TOKEN_LBRACKET  // [
	TOKEN_RBRACKET  // ]
	TOKEN_COMMA     // ,
	TOKEN_SEMICOLON // ;
	TOKEN_DOT       // .
	TOKEN_COLON     // :
	TOKEN_COLONEQ   // := (Phase 1, but tokenize it)
)

type Token struct {
	Type   TokenType
	Lexeme string
	Line   int
	Col    int
}

var keywords = map[string]TokenType{
	"func":   TOKEN_FUNC,
	"var":    TOKEN_VAR,
	"struct": TOKEN_STRUCT,
	"if":     TOKEN_IF,
	"else":   TOKEN_ELSE,
	"while":  TOKEN_WHILE,
	"return": TOKEN_RETURN,
	"true":   TOKEN_TRUE,
	"false":  TOKEN_FALSE,
	"nil":    TOKEN_NIL,
	"i8":     TOKEN_I8,
	"i16":    TOKEN_I16,
	"i32":    TOKEN_I32,
	"i64":    TOKEN_I64,
	"u8":     TOKEN_U8,
	"u16":    TOKEN_U16,
	"u32":    TOKEN_U32,
	"u64":    TOKEN_U64,
	"bool":   TOKEN_BOOL,
	"void":   TOKEN_VOID,
}

func (t TokenType) String() string {
	names := []string{
		"EOF", "ERROR",
		"IDENT", "NUMBER", "STRING",
		"func", "var", "struct", "if", "else", "while", "return", "true", "false", "nil",
		"i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "bool", "void",
		"+", "-", "*", "/", "%", "&", "!", "=", "==", "!=", "<", ">", "<=", ">=", "&&", "||",
		"(", ")", "{", "}", "[", "]", ",", ";", ".", ":", ":=",
	}
	if int(t) < len(names) {
		return names[t]
	}
	return "UNKNOWN"
}
