package main

// AST Node types for the language

type Node interface {
	node()
}

type Decl interface {
	Node
	decl()
}

type Stmt interface {
	Node
	stmt()
}

type Expr interface {
	Node
	expr()
}

type Type interface {
	Node
	typ()
}

// --- Declarations ---

type FuncDecl struct {
	Name   string
	Params []Param
	RetType Type // nil for void
	Body   *BlockStmt
}

type Param struct {
	Name string
	Type Type
}

type VarDecl struct {
	Name  string
	Type  Type
	Init  Expr // nil if no initializer
}

type StructDecl struct {
	Name   string
	Fields []Field
}

type Field struct {
	Name string
	Type Type
}

func (*FuncDecl) node()   {}
func (*FuncDecl) decl()   {}
func (*VarDecl) node()    {}
func (*VarDecl) decl()    {}
func (*VarDecl) stmt()    {} // var can also be a statement
func (*StructDecl) node() {}
func (*StructDecl) decl() {}

// --- Types ---

type BaseType struct {
	Name string // i8, i16, i32, i64, u8, u16, u32, u64, bool, void, or struct name
}

type PtrType struct {
	Elem Type
}

type ArrayType struct {
	Size int
	Elem Type
}

func (*BaseType) node()  {}
func (*BaseType) typ()   {}
func (*PtrType) node()   {}
func (*PtrType) typ()    {}
func (*ArrayType) node() {}
func (*ArrayType) typ()  {}

// --- Statements ---

type BlockStmt struct {
	Stmts []Stmt
}

type IfStmt struct {
	Cond Expr
	Then *BlockStmt
	Else Stmt // *BlockStmt or *IfStmt (else if), or nil
}

type WhileStmt struct {
	Cond Expr
	Body *BlockStmt
}

type ReturnStmt struct {
	Value Expr // nil for bare return
}

type ExprStmt struct {
	Expr Expr
}

func (*BlockStmt) node()  {}
func (*BlockStmt) stmt()  {}
func (*IfStmt) node()     {}
func (*IfStmt) stmt()     {}
func (*WhileStmt) node()  {}
func (*WhileStmt) stmt()  {}
func (*ReturnStmt) node() {}
func (*ReturnStmt) stmt() {}
func (*ExprStmt) node()   {}
func (*ExprStmt) stmt()   {}

// --- Expressions ---

type BinaryExpr struct {
	Op    TokenType
	Left  Expr
	Right Expr
}

type UnaryExpr struct {
	Op   TokenType
	Expr Expr
}

type CallExpr struct {
	Func Expr
	Args []Expr
}

type IndexExpr struct {
	Expr  Expr
	Index Expr
}

type FieldExpr struct {
	Expr  Expr
	Field string
}

type IdentExpr struct {
	Name string
}

type NumberExpr struct {
	Value string // keep as string, parse later
}

type StringExpr struct {
	Value string // includes quotes
}

type BoolExpr struct {
	Value bool
}

type NilExpr struct{}

type GroupExpr struct {
	Expr Expr
}

func (*BinaryExpr) node() {}
func (*BinaryExpr) expr() {}
func (*UnaryExpr) node()  {}
func (*UnaryExpr) expr()  {}
func (*CallExpr) node()   {}
func (*CallExpr) expr()   {}
func (*IndexExpr) node()  {}
func (*IndexExpr) expr()  {}
func (*FieldExpr) node()  {}
func (*FieldExpr) expr()  {}
func (*IdentExpr) node()  {}
func (*IdentExpr) expr()  {}
func (*NumberExpr) node() {}
func (*NumberExpr) expr() {}
func (*StringExpr) node() {}
func (*StringExpr) expr() {}
func (*BoolExpr) node()   {}
func (*BoolExpr) expr()   {}
func (*NilExpr) node()    {}
func (*NilExpr) expr()    {}
func (*GroupExpr) node()  {}
func (*GroupExpr) expr()  {}

// Program is the root of the AST
type Program struct {
	Decls []Decl
}
