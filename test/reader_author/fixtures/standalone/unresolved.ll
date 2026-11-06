declare i64 @standalone_missing_link_symbol()
define i64 @main() {
  %value = call i64 @standalone_missing_link_symbol()
  ret i64 %value
}
