test "harness must observe checked narrowing trap" {
    var value: u16 = 256;
    const runtime_value: *volatile u16 = &value;
    const narrowed: u8 = @intCast(runtime_value.*);
    try @import("std").testing.expect(narrowed == 0);
}
