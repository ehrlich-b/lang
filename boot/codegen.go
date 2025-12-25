package main

import (
	"fmt"
	"strconv"
	"strings"
)

// System V AMD64 ABI
var argRegs = []string{"rdi", "rsi", "rdx", "rcx", "r8", "r9"}
var syscallArgRegs = []string{"rdi", "rsi", "rdx", "r10", "r8", "r9"}

type LocalVar struct {
	Offset int
	Type   Type
}

type Codegen struct {
	out      strings.Builder
	labelNum int

	// Current function context
	locals    map[string]LocalVar
	stackSize int

	// Global variables
	globals      map[string]bool
	globalTypes  map[string]Type
	globalInits  map[string]Expr // initializer expressions

	// String literals
	strings   []string
	stringNum int
}

func NewCodegen() *Codegen {
	return &Codegen{
		locals:      make(map[string]LocalVar),
		globals:     make(map[string]bool),
		globalTypes: make(map[string]Type),
		globalInits: make(map[string]Expr),
	}
}

func (c *Codegen) Generate(prog *Program) string {
	// First pass: collect global variables
	for _, decl := range prog.Decls {
		if v, ok := decl.(*VarDecl); ok {
			c.globals[v.Name] = true
			c.globalTypes[v.Name] = v.Type
			c.globalInits[v.Name] = v.Init
		}
	}

	// Data section for string literals and global variables
	c.emit(".section .data")

	// Generate code, collecting strings
	var codeBuf strings.Builder
	origOut := c.out
	c.out = codeBuf

	for _, decl := range prog.Decls {
		c.genDecl(decl)
	}

	code := c.out.String()
	c.out = origOut

	// Emit collected string literals
	for i, s := range c.strings {
		c.emit(".str%d:", i)
		c.emit("    .ascii %s", formatAscii(s))
	}

	// Emit global variables (8 bytes each)
	for name := range c.globals {
		c.emit("%s:", name)
		initVal := int64(0)
		if init, ok := c.globalInits[name]; ok && init != nil {
			initVal = c.evalConstant(init)
		}
		c.emit("    .quad %d", initVal)
	}

	// Text section
	c.emit("")
	c.emit(".section .text")
	c.emit(".globl _start")
	c.emit("_start:")
	c.emit("    call main")
	c.emit("    mov %%rax, %%rdi")
	c.emit("    mov $60, %%rax")
	c.emit("    syscall")
	c.emit("")

	c.out.WriteString(code)

	return c.out.String()
}

func (c *Codegen) genDecl(decl Decl) {
	switch d := decl.(type) {
	case *FuncDecl:
		c.genFunc(d)
	case *VarDecl:
		c.genGlobalVar(d)
	case *StructDecl:
		// Struct layout (not implemented for Phase 0)
	}
}

func (c *Codegen) genGlobalVar(v *VarDecl) {
	c.globals[v.Name] = true
	// Global variables are emitted in the data section by Generate()
}

func (c *Codegen) genFunc(f *FuncDecl) {
	c.emit(".globl %s", f.Name)
	c.emit("%s:", f.Name)

	// Reset locals
	c.locals = make(map[string]LocalVar)
	c.stackSize = 0

	// Prologue
	c.emit("    push %%rbp")
	c.emit("    mov %%rsp, %%rbp")

	// Reserve space for locals (placeholder, patched after body generation)
	c.emit("    sub $STACKSIZE, %%rsp")

	// Store parameters in locals
	for i, param := range f.Params {
		c.stackSize += 8
		c.locals[param.Name] = LocalVar{Offset: -c.stackSize, Type: param.Type}
		if i < len(argRegs) {
			c.emit("    mov %%%s, %d(%%rbp)", argRegs[i], -c.stackSize)
		}
	}

	// Generate body
	c.genBlock(f.Body)

	// If function doesn't end with return, add default
	if f.RetType == nil || isVoidType(f.RetType) {
		c.emit("    xor %%rax, %%rax")
		c.emit("    leave")
		c.emit("    ret")
	}

	// Patch stack size (align to 16)
	alignedStack := (c.stackSize + 15) & ^15
	if alignedStack == 0 {
		alignedStack = 16
	}

	// Rebuild output with correct stack size
	output := c.out.String()
	patched := strings.Replace(output, "    sub $STACKSIZE, %rsp",
		fmt.Sprintf("    sub $%d, %%rsp", alignedStack), 1)
	c.out.Reset()
	c.out.WriteString(patched)

	c.emit("")
}

func (c *Codegen) genBlock(b *BlockStmt) {
	for _, stmt := range b.Stmts {
		c.genStmt(stmt)
	}
}

func (c *Codegen) genStmt(stmt Stmt) {
	switch s := stmt.(type) {
	case *VarDecl:
		c.stackSize += 8
		c.locals[s.Name] = LocalVar{Offset: -c.stackSize, Type: s.Type}
		if s.Init != nil {
			c.genExpr(s.Init)
			c.emit("    mov %%rax, %d(%%rbp)", c.locals[s.Name].Offset)
		}

	case *ExprStmt:
		c.genExpr(s.Expr)

	case *ReturnStmt:
		if s.Value != nil {
			c.genExpr(s.Value)
		} else {
			c.emit("    xor %%rax, %%rax")
		}
		c.emit("    leave")
		c.emit("    ret")

	case *IfStmt:
		elseLabel := c.newLabel()
		endLabel := c.newLabel()

		c.genExpr(s.Cond)
		c.emit("    test %%rax, %%rax")
		if s.Else != nil {
			c.emit("    jz %s", elseLabel)
		} else {
			c.emit("    jz %s", endLabel)
		}

		c.genBlock(s.Then)

		if s.Else != nil {
			c.emit("    jmp %s", endLabel)
			c.emit("%s:", elseLabel)
			switch e := s.Else.(type) {
			case *BlockStmt:
				c.genBlock(e)
			case *IfStmt:
				c.genStmt(e)
			}
		}
		c.emit("%s:", endLabel)

	case *WhileStmt:
		startLabel := c.newLabel()
		endLabel := c.newLabel()

		c.emit("%s:", startLabel)
		c.genExpr(s.Cond)
		c.emit("    test %%rax, %%rax")
		c.emit("    jz %s", endLabel)
		c.genBlock(s.Body)
		c.emit("    jmp %s", startLabel)
		c.emit("%s:", endLabel)

	case *BlockStmt:
		c.genBlock(s)
	}
}

func (c *Codegen) genExpr(expr Expr) {
	switch e := expr.(type) {
	case *NumberExpr:
		c.emit("    mov $%s, %%rax", e.Value)

	case *StringExpr:
		idx := c.stringNum
		c.strings = append(c.strings, e.Value)
		c.stringNum++
		c.emit("    lea .str%d(%%rip), %%rax", idx)

	case *BoolExpr:
		if e.Value {
			c.emit("    mov $1, %%rax")
		} else {
			c.emit("    xor %%rax, %%rax")
		}

	case *NilExpr:
		c.emit("    xor %%rax, %%rax")

	case *IdentExpr:
		if local, ok := c.locals[e.Name]; ok {
			c.emit("    mov %d(%%rbp), %%rax", local.Offset)
		} else if c.globals[e.Name] {
			c.emit("    mov %s(%%rip), %%rax", e.Name)
		} else {
			// Function - get address
			c.emit("    lea %s(%%rip), %%rax", e.Name)
		}

	case *GroupExpr:
		c.genExpr(e.Expr)

	case *UnaryExpr:
		c.genExpr(e.Expr)
		switch e.Op {
		case TOKEN_MINUS:
			c.emit("    neg %%rax")
		case TOKEN_BANG:
			c.emit("    test %%rax, %%rax")
			c.emit("    setz %%al")
			c.emit("    movzx %%al, %%rax")
		case TOKEN_STAR: // dereference
			// Determine the element type to use correct load size
			ptrType := c.getExprType(e.Expr)
			elemType := getPointedType(ptrType)
			size := 8
			if elemType != nil {
				size = getTypeSize(elemType)
			}
			switch size {
			case 1:
				c.emit("    movzbl (%%rax), %%eax")
			case 2:
				c.emit("    movzwl (%%rax), %%eax")
			case 4:
				c.emit("    mov (%%rax), %%eax")
			default:
				c.emit("    mov (%%rax), %%rax")
			}
		case TOKEN_AMP: // address-of
			// The inner expr should be an lvalue - handle specially
			if ident, ok := e.Expr.(*IdentExpr); ok {
				if local, ok := c.locals[ident.Name]; ok {
					c.emit("    lea %d(%%rbp), %%rax", local.Offset)
				} else if c.globals[ident.Name] {
					c.emit("    lea %s(%%rip), %%rax", ident.Name)
				}
			}
		}

	case *BinaryExpr:
		if e.Op == TOKEN_EQ {
			// Assignment
			c.genExpr(e.Right)
			c.genLValueStore(e.Left)
			return
		}

		// Short-circuit for && and ||
		if e.Op == TOKEN_AMPAMP {
			endLabel := c.newLabel()
			c.genExpr(e.Left)
			c.emit("    test %%rax, %%rax")
			c.emit("    jz %s", endLabel)
			c.genExpr(e.Right)
			c.emit("%s:", endLabel)
			return
		}
		if e.Op == TOKEN_PIPEPIPE {
			endLabel := c.newLabel()
			c.genExpr(e.Left)
			c.emit("    test %%rax, %%rax")
			c.emit("    jnz %s", endLabel)
			c.genExpr(e.Right)
			c.emit("%s:", endLabel)
			return
		}

		// Evaluate left, push, evaluate right, pop left into rcx
		c.genExpr(e.Left)
		c.emit("    push %%rax")
		c.genExpr(e.Right)
		c.emit("    mov %%rax, %%rcx")
		c.emit("    pop %%rax")

		switch e.Op {
		case TOKEN_PLUS:
			c.emit("    add %%rcx, %%rax")
		case TOKEN_MINUS:
			c.emit("    sub %%rcx, %%rax")
		case TOKEN_STAR:
			c.emit("    imul %%rcx, %%rax")
		case TOKEN_SLASH:
			c.emit("    cqo")
			c.emit("    idiv %%rcx")
		case TOKEN_PERCENT:
			c.emit("    cqo")
			c.emit("    idiv %%rcx")
			c.emit("    mov %%rdx, %%rax")
		case TOKEN_EQEQ:
			c.emit("    cmp %%rcx, %%rax")
			c.emit("    sete %%al")
			c.emit("    movzx %%al, %%rax")
		case TOKEN_BANGEQ:
			c.emit("    cmp %%rcx, %%rax")
			c.emit("    setne %%al")
			c.emit("    movzx %%al, %%rax")
		case TOKEN_LT:
			c.emit("    cmp %%rcx, %%rax")
			c.emit("    setl %%al")
			c.emit("    movzx %%al, %%rax")
		case TOKEN_GT:
			c.emit("    cmp %%rcx, %%rax")
			c.emit("    setg %%al")
			c.emit("    movzx %%al, %%rax")
		case TOKEN_LTEQ:
			c.emit("    cmp %%rcx, %%rax")
			c.emit("    setle %%al")
			c.emit("    movzx %%al, %%rax")
		case TOKEN_GTEQ:
			c.emit("    cmp %%rcx, %%rax")
			c.emit("    setge %%al")
			c.emit("    movzx %%al, %%rax")
		}

	case *CallExpr:
		// Check for syscall builtin
		if ident, ok := e.Func.(*IdentExpr); ok && ident.Name == "syscall" {
			c.genSyscall(e.Args)
			return
		}

		// Regular function call
		// Push args in reverse, then pop into registers
		for i := len(e.Args) - 1; i >= 0; i-- {
			c.genExpr(e.Args[i])
			c.emit("    push %%rax")
		}
		for i := 0; i < len(e.Args) && i < len(argRegs); i++ {
			c.emit("    pop %%%s", argRegs[i])
		}

		// Get function address
		if ident, ok := e.Func.(*IdentExpr); ok {
			c.emit("    call %s", ident.Name)
		} else {
			c.genExpr(e.Func)
			c.emit("    call *%%rax")
		}

	case *FieldExpr:
		// Not implemented for Phase 0
		c.genExpr(e.Expr)

	case *IndexExpr:
		// array[index] = base + index * 8
		c.genExpr(e.Index)
		c.emit("    push %%rax")
		c.genExpr(e.Expr)
		c.emit("    pop %%rcx")
		c.emit("    lea (%%rax,%%rcx,8), %%rax")
		c.emit("    mov (%%rax), %%rax")
	}
}

func (c *Codegen) genLValueStore(expr Expr) {
	switch e := expr.(type) {
	case *IdentExpr:
		if local, ok := c.locals[e.Name]; ok {
			c.emit("    mov %%rax, %d(%%rbp)", local.Offset)
		} else if c.globals[e.Name] {
			c.emit("    mov %%rax, %s(%%rip)", e.Name)
		}
	case *UnaryExpr:
		if e.Op == TOKEN_STAR {
			// *ptr = value
			c.emit("    push %%rax") // save value
			c.genExpr(e.Expr)        // get address
			c.emit("    mov %%rax, %%rcx")
			c.emit("    pop %%rax")
			c.emit("    mov %%rax, (%%rcx)")
		}
	case *IndexExpr:
		// array[index] = value
		c.emit("    push %%rax")     // save value
		c.genExpr(e.Index)
		c.emit("    push %%rax")     // save index
		c.genExpr(e.Expr)            // get base
		c.emit("    pop %%rcx")      // index
		c.emit("    lea (%%rax,%%rcx,8), %%rcx") // address
		c.emit("    pop %%rax")      // value
		c.emit("    mov %%rax, (%%rcx)")
	}
}

func (c *Codegen) genSyscall(args []Expr) {
	if len(args) == 0 {
		return
	}

	// First arg is syscall number -> rax
	// Rest go to rdi, rsi, rdx, r10, r8, r9
	for i := len(args) - 1; i >= 0; i-- {
		c.genExpr(args[i])
		c.emit("    push %%rax")
	}

	c.emit("    pop %%rax") // syscall number
	for i := 1; i < len(args) && i-1 < len(syscallArgRegs); i++ {
		c.emit("    pop %%%s", syscallArgRegs[i-1])
	}

	c.emit("    syscall")
}

func (c *Codegen) newLabel() string {
	c.labelNum++
	return fmt.Sprintf(".L%d", c.labelNum)
}

func (c *Codegen) emit(format string, args ...interface{}) {
	fmt.Fprintf(&c.out, format+"\n", args...)
}

// Parse escape sequences in string literals
func parseString(s string) string {
	// Remove quotes
	s = s[1 : len(s)-1]

	var result strings.Builder
	for i := 0; i < len(s); i++ {
		if s[i] == '\\' && i+1 < len(s) {
			i++
			switch s[i] {
			case 'n':
				result.WriteByte('\n')
			case 't':
				result.WriteByte('\t')
			case 'r':
				result.WriteByte('\r')
			case '\\':
				result.WriteByte('\\')
			case '"':
				result.WriteByte('"')
			case '0':
				result.WriteByte(0)
			default:
				result.WriteByte(s[i])
			}
		} else {
			result.WriteByte(s[i])
		}
	}
	return result.String()
}

// Format string for .ascii directive (includes null terminator)
func formatAscii(s string) string {
	s = parseString(s)
	var result strings.Builder
	result.WriteByte('"')
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c >= 32 && c < 127 && c != '"' && c != '\\' {
			result.WriteByte(c)
		} else {
			result.WriteString(fmt.Sprintf("\\%03o", c))
		}
	}
	result.WriteString("\\000") // null terminator
	result.WriteByte('"')
	return result.String()
}

func parseInt(s string) int {
	n, _ := strconv.Atoi(s)
	return n
}

func isVoidType(t Type) bool {
	if bt, ok := t.(*BaseType); ok {
		return bt.Name == "void"
	}
	return false
}

// getTypeSize returns the size in bytes for a type
func getTypeSize(t Type) int {
	switch t := t.(type) {
	case *BaseType:
		switch t.Name {
		case "u8", "i8", "bool":
			return 1
		case "u16", "i16":
			return 2
		case "u32", "i32":
			return 4
		case "u64", "i64":
			return 8
		default:
			return 8 // pointers, unknown
		}
	case *PtrType:
		return 8
	default:
		return 8
	}
}

// getPointedType returns the element type of a pointer type
func getPointedType(t Type) Type {
	if pt, ok := t.(*PtrType); ok {
		return pt.Elem
	}
	return nil
}

// getExprType tries to infer the type of an expression
func (c *Codegen) getExprType(expr Expr) Type {
	switch e := expr.(type) {
	case *IdentExpr:
		if local, ok := c.locals[e.Name]; ok {
			return local.Type
		}
		if t, ok := c.globalTypes[e.Name]; ok {
			return t
		}
	case *UnaryExpr:
		if e.Op == TOKEN_STAR { // dereference
			innerType := c.getExprType(e.Expr)
			return getPointedType(innerType)
		}
		if e.Op == TOKEN_AMP { // address-of
			innerType := c.getExprType(e.Expr)
			return &PtrType{Elem: innerType}
		}
		return c.getExprType(e.Expr)
	case *BinaryExpr:
		// For arithmetic, return left operand type
		// For pointer + int, return pointer type
		return c.getExprType(e.Left)
	case *GroupExpr:
		return c.getExprType(e.Expr)
	case *NumberExpr:
		return &BaseType{Name: "i64"}
	case *StringExpr:
		return &PtrType{Elem: &BaseType{Name: "u8"}}
	case *BoolExpr:
		return &BaseType{Name: "bool"}
	}
	return &BaseType{Name: "i64"} // default
}

// evalConstant evaluates a constant expression at compile time
// Used for global variable initializers
func (c *Codegen) evalConstant(expr Expr) int64 {
	switch e := expr.(type) {
	case *NumberExpr:
		val, _ := strconv.ParseInt(e.Value, 10, 64)
		return val
	case *BoolExpr:
		if e.Value {
			return 1
		}
		return 0
	case *NilExpr:
		return 0
	case *IdentExpr:
		// Handle nil and other special identifiers
		if e.Name == "nil" {
			return 0
		}
		// Try to look up global constant
		if init, ok := c.globalInits[e.Name]; ok && init != nil {
			return c.evalConstant(init)
		}
		return 0
	case *UnaryExpr:
		val := c.evalConstant(e.Expr)
		switch e.Op {
		case TOKEN_MINUS:
			return -val
		case TOKEN_BANG:
			if val == 0 {
				return 1
			}
			return 0
		}
		return val
	case *BinaryExpr:
		left := c.evalConstant(e.Left)
		right := c.evalConstant(e.Right)
		switch e.Op {
		case TOKEN_PLUS:
			return left + right
		case TOKEN_MINUS:
			return left - right
		case TOKEN_STAR:
			return left * right
		case TOKEN_SLASH:
			if right != 0 {
				return left / right
			}
			return 0
		case TOKEN_PERCENT:
			if right != 0 {
				return left % right
			}
			return 0
		case TOKEN_EQEQ:
			if left == right {
				return 1
			}
			return 0
		case TOKEN_BANGEQ:
			if left != right {
				return 1
			}
			return 0
		case TOKEN_LT:
			if left < right {
				return 1
			}
			return 0
		case TOKEN_GT:
			if left > right {
				return 1
			}
			return 0
		case TOKEN_LTEQ:
			if left <= right {
				return 1
			}
			return 0
		case TOKEN_GTEQ:
			if left >= right {
				return 1
			}
			return 0
		}
		return 0
	case *GroupExpr:
		return c.evalConstant(e.Expr)
	}
	return 0
}
