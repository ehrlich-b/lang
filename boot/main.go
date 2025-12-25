package main

import (
	"fmt"
	"os"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: lang0 <file.lang>... [-o output.s] [--tokens] [--ast]")
		os.Exit(1)
	}

	var inputFiles []string
	var outputFile string
	showTokens := false
	showAST := false

	for i := 1; i < len(os.Args); i++ {
		arg := os.Args[i]
		switch {
		case arg == "-o" && i+1 < len(os.Args):
			outputFile = os.Args[i+1]
			i++
		case arg == "--tokens":
			showTokens = true
		case arg == "--ast":
			showAST = true
		case !strings.HasPrefix(arg, "-"):
			inputFiles = append(inputFiles, arg)
		}
	}

	if len(inputFiles) == 0 {
		fmt.Fprintln(os.Stderr, "Error: no input files specified")
		os.Exit(1)
	}

	// Concatenate all source files
	var allSource strings.Builder
	for _, inputFile := range inputFiles {
		source, err := os.ReadFile(inputFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error reading file %s: %v\n", inputFile, err)
			os.Exit(1)
		}
		allSource.Write(source)
		allSource.WriteByte('\n')
	}

	// Lex
	lexer := NewLexer(allSource.String())
	tokens := lexer.ScanTokens()

	// Check for lexer errors
	for _, tok := range tokens {
		if tok.Type == TOKEN_ERROR {
			fmt.Fprintf(os.Stderr, "%d:%d: error: %s\n", tok.Line, tok.Col, tok.Lexeme)
			os.Exit(1)
		}
	}

	if showTokens {
		for _, tok := range tokens {
			fmt.Printf("%3d:%-3d %-12s %q\n", tok.Line, tok.Col, tok.Type, tok.Lexeme)
		}
		return
	}

	// Parse
	parser := NewParser(tokens)
	program, errors := parser.Parse()

	if len(errors) > 0 {
		for _, e := range errors {
			fmt.Fprintf(os.Stderr, "error: %s\n", e)
		}
		os.Exit(1)
	}

	if showAST {
		printAST(program, 0)
		return
	}

	// Code generation
	codegen := NewCodegen()
	asm := codegen.Generate(program)

	if outputFile != "" {
		err := os.WriteFile(outputFile, []byte(asm), 0644)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error writing file: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Wrote %s\n", outputFile)
	} else {
		fmt.Print(asm)
	}
}

func printAST(node interface{}, indent int) {
	prefix := strings.Repeat("  ", indent)

	switch n := node.(type) {
	case *Program:
		fmt.Printf("%sProgram\n", prefix)
		for _, d := range n.Decls {
			printAST(d, indent+1)
		}

	case *FuncDecl:
		fmt.Printf("%sFuncDecl: %s\n", prefix, n.Name)
		fmt.Printf("%s  Params:\n", prefix)
		for _, p := range n.Params {
			fmt.Printf("%s    %s: ", prefix, p.Name)
			printType(p.Type)
			fmt.Println()
		}
		fmt.Printf("%s  Returns: ", prefix)
		if n.RetType != nil {
			printType(n.RetType)
		} else {
			fmt.Print("void")
		}
		fmt.Println()
		fmt.Printf("%s  Body:\n", prefix)
		printAST(n.Body, indent+2)

	case *VarDecl:
		fmt.Printf("%sVarDecl: %s: ", prefix, n.Name)
		printType(n.Type)
		if n.Init != nil {
			fmt.Print(" = ")
			printExpr(n.Init)
		}
		fmt.Println()

	case *StructDecl:
		fmt.Printf("%sStructDecl: %s\n", prefix, n.Name)
		for _, f := range n.Fields {
			fmt.Printf("%s  %s: ", prefix, f.Name)
			printType(f.Type)
			fmt.Println()
		}

	case *BlockStmt:
		fmt.Printf("%sBlock\n", prefix)
		for _, s := range n.Stmts {
			printAST(s, indent+1)
		}

	case *IfStmt:
		fmt.Printf("%sIf: ", prefix)
		printExpr(n.Cond)
		fmt.Println()
		printAST(n.Then, indent+1)
		if n.Else != nil {
			fmt.Printf("%sElse:\n", prefix)
			printAST(n.Else, indent+1)
		}

	case *WhileStmt:
		fmt.Printf("%sWhile: ", prefix)
		printExpr(n.Cond)
		fmt.Println()
		printAST(n.Body, indent+1)

	case *ReturnStmt:
		fmt.Printf("%sReturn: ", prefix)
		if n.Value != nil {
			printExpr(n.Value)
		}
		fmt.Println()

	case *ExprStmt:
		fmt.Printf("%sExprStmt: ", prefix)
		printExpr(n.Expr)
		fmt.Println()
	}
}

func printType(t Type) {
	switch t := t.(type) {
	case *BaseType:
		fmt.Print(t.Name)
	case *PtrType:
		fmt.Print("*")
		printType(t.Elem)
	case *ArrayType:
		fmt.Printf("[%d]", t.Size)
		printType(t.Elem)
	}
}

func printExpr(e Expr) {
	switch e := e.(type) {
	case *BinaryExpr:
		fmt.Print("(")
		printExpr(e.Left)
		fmt.Printf(" %s ", e.Op)
		printExpr(e.Right)
		fmt.Print(")")
	case *UnaryExpr:
		fmt.Printf("(%s", e.Op)
		printExpr(e.Expr)
		fmt.Print(")")
	case *CallExpr:
		printExpr(e.Func)
		fmt.Print("(")
		for i, arg := range e.Args {
			if i > 0 {
				fmt.Print(", ")
			}
			printExpr(arg)
		}
		fmt.Print(")")
	case *IndexExpr:
		printExpr(e.Expr)
		fmt.Print("[")
		printExpr(e.Index)
		fmt.Print("]")
	case *FieldExpr:
		printExpr(e.Expr)
		fmt.Printf(".%s", e.Field)
	case *IdentExpr:
		fmt.Print(e.Name)
	case *NumberExpr:
		fmt.Print(e.Value)
	case *StringExpr:
		fmt.Print(e.Value)
	case *BoolExpr:
		fmt.Print(e.Value)
	case *NilExpr:
		fmt.Print("nil")
	case *GroupExpr:
		printExpr(e.Expr)
	}
}
