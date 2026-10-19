test "harness must observe upstream assertion failure" {
    try @import("std").testing.expect(false);
}
