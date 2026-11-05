; Repeated apply dispatch handles primitives, closures and leading arguments.
(assert (= (apply apply (list + '(3 4))) 7))
(assert (= (apply apply (list apply (list + '(3 4)))) 7))
(assert (= (apply apply + '(3 (4))) 7))
(assert (= (apply apply (list (lambda (x y) (+ x y)) '(3 4))) 7))
(display "apply ok") (newline)
