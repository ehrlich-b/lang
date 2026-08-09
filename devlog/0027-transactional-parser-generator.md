# The parser generator learns to say no

`#parser{}` used to work only when every choice announced itself with a distinct
first token. Worse, a sequence checked only its first element: after that, a
missing token could be accepted as if it had never been required. The shipped C
reader knowingly shaped its grammar around both bugs.

Generated parsers now checkpoint the tokenizer around choices, sequences,
optionals, and repetitions. A failed alternative rewinds before the next one;
a required sequence element fails the whole sequence; and a repetition stops
instead of spinning when its child succeeds without consuming input. Generated
locals also have unique names, removing the old one-digit temporary-name limit.

The tokenizer keeps the furthest failed byte, the found token, and the expected
forms accumulated there. Readers can query the offset or one-based line/column,
or call `tok_print_error(tokens, "mylang")` for a useful default diagnostic.

The stricter sequence semantics exposed one honest dependency in the C reader:
its postfix `++`/`--` operand had only been optional by accident. The grammar now
says so with `c_unary?`. It also exposed an older tokenizer/parser mismatch where
`?` had gained a token kind but the grammar parser still looked only for an
unknown character.

`test/suite/277_parser_transaction.lang` guards shared-prefix alternatives,
whole-sequence rewind, exact multi-character literals, furthest expectations,
EOF reporting, and line/column calculation. The full reader matrix—including C,
Forth, Lisp, flow, minipy, and the polyglot build—runs through the new generator.
