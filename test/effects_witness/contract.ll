; Minimal selected contract: PERFORM returns an event; a later ordinary call
; reaches a local switch case. There is no edge into another activation.
; Target selected by native clang; no architecture-specific instructions.
%Frame = type { i32, i64, i64 }

define i32 @two_ticks(ptr %frame, i64 %reply, ptr %payload) {
entry:
  %pcptr = getelementptr %Frame, ptr %frame, i32 0, i32 0
  %savedptr = getelementptr %Frame, ptr %frame, i32 0, i32 1
  %resultptr = getelementptr %Frame, ptr %frame, i32 0, i32 2
  %pc = load i32, ptr %pcptr
  switch i32 %pc, label %bad [i32 0, label %first
                             i32 1, label %second
                             i32 2, label %done]
first:
  store i32 1, ptr %pcptr
  store i64 10, ptr %payload
  ret i32 1 ; PERFORM(10), no fallthrough to second
second:
  store i64 %reply, ptr %savedptr
  %next = add i64 %reply, 20
  store i32 2, ptr %pcptr
  store i64 %next, ptr %payload
  ret i32 1 ; PERFORM(reply + 20)
done:
  %saved = load i64, ptr %savedptr
  %value = add i64 %saved, %reply
  store i64 %value, ptr %resultptr
  ret i32 0 ; DONE(value)
bad:
  ret i32 2 ; checked E_PC, never undefined/unreachable
}
