; Context and state are required; expected/actual expressions execute once.
(define (add4 x) (+ x 4))
(test 10 (add4 6))
(let ((x 2)) (test 3 (+ x 1)))
(let ((x 0)) (test 1 (begin (set! x (+ x 1)) x)) (test 1 x))
(test #(a b) '#(a b))
