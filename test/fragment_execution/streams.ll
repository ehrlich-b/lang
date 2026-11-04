@msg = private constant [4 x i8] c"ok\0A\00"
declare i64 @write(i32, ptr, i64)
define i32 @main() {
  %a = call i64 @write(i32 1, ptr @msg, i64 3)
  %b = call i64 @write(i32 2, ptr @msg, i64 3)
  ret i32 7
}
