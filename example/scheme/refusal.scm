; Continuations need an explicit lifetime and re-entry policy.
(define answer
(call/cc (lambda (k) (k 42))))
