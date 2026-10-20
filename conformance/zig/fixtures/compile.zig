test "harness must observe required type rejection" {
    const value: u8 = "invalid integer";
    _ = value;
}
