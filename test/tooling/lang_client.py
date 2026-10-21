"""Q0 fixture client for the Lang reader; no general name analysis is claimed."""
from wire import envelope


def read(source, syntax):
    # Lang lets shadow in expression scopes; seed is captured by the named f closure.
    return envelope(source, syntax, b'#lang{', b' let x = 10 in (let x = 32 in x) + x ')
