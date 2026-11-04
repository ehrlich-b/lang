define i32 @main() {
  call void asm sideeffect "", ""()
  ret i32 0
}
