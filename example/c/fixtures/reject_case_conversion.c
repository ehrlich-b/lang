int main(void) {
    unsigned int selector = 0;
    switch (selector) {
    case -1:
        return 1;
    case 4294967295U:
        return 2;
    }
    return 0;
}
