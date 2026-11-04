\ UTF-8 byte offsets survive skipped comments: λ
: debug_forth ( n -- r ) 2 + ;
: main ( -- r )
    40 debug_forth
    42 -
;
