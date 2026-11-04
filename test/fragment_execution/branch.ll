define i32 @main() {
entry:
  %wrapped = add i8 127, 1
  %negative = icmp slt i8 %wrapped, 0
  br i1 %negative, label %yes, label %no
yes:
  br label %done
no:
  br label %done
done:
  %result = phi i32 [ 0, %yes ], [ 1, %no ]
  ret i32 %result
}
