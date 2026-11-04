declare void @exit(i32)
define i32 @main() {
  call void @exit(i32 23)
  unreachable
}
