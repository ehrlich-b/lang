int main(void) {
    union Number { int x; char b[4]; } n;
    return n.x;
}
