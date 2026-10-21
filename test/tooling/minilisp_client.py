"""Q0 fixture client for the minilisp reader, nested in the Lang reader."""
from wire import envelope


def read(source, syntax):
    # Lisp let lowering uses distinct scopes; the host only receives supplied IDs.
    return envelope(source, syntax, b'#minilisp{', b' (let ((x 10)) (+ (let ((x 32)) x) x)) ')
