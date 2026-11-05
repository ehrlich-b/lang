; Literal values, lexical scope, closures and conditional calls.
(define (add x) (lambda (y) (+ x y)))
(assert (= ((add 20) 22) 42))
(assert (equal? '(a 2 . c) (cons 'a (cons 2 'c))))
(assert (= ((if #f + *) 6 7) 42))
(display "basic ok") (newline)
