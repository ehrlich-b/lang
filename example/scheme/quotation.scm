; Long and abbreviated quotation must preserve continuation names as data.
(assert (eq? (quote call/cc) 'call/cc))
(assert (eq? (quote call-with-current-continuation) 'call-with-current-continuation))
(assert (equal? (quote (call/cc (call-with-current-continuation)))
                '(call/cc (call-with-current-continuation))))
(assert (eq? ( ; a comment before the long-form head
               quote ; and before the datum
               call/cc) 'call/cc))
(assert (equal? (quote ((test 0 call/cc) . call/cc)) '((test 0 call/cc) . call/cc)))
(write (quote call/cc)) (newline)
(display "quotation ok") (newline)
