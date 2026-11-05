; Mutual, indirect calls; apply and begin remain in tail position.
(define (left n acc next)
  (if (= n 0) acc
      (begin (+ 1 2) (next (- n 1) (+ acc 1) left))))
(define (right n acc next)
  (if (= n 0) acc
      (apply next (list (- n 1) (+ acc 1) right))))
(assert (= (left 10000000 0 right) 10000000))
(display "tail 10000000 ok") (newline)
