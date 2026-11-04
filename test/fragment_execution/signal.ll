declare void @llvm.trap()
define i32 @main() {
  call void @llvm.trap()
  unreachable
}
