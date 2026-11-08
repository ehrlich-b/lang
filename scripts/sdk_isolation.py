"""Unprivileged Linux filesystem isolation for archive consumer checks.

The child can see SDK resources, its fresh work directory and system tools, but
cannot open the source checkout, bootstrap seed or any other directory in /work.
Landlock is inherited by every compiler/linker child; no namespace root is used.
"""
import ctypes
import os
from pathlib import Path


def isolate(writable, readonly):
    libc = ctypes.CDLL(None, use_errno=True)
    # Linux x86-64 syscall numbers. Packaging already checks this platform.
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 1:
        raise OSError('SDK isolation requires Linux Landlock ABI 1 or newer')
    rights = (1 << 13) - 1  # ABI 1 filesystem rights, through MAKE_SYM
    handled = ctypes.c_uint64(rights)
    ruleset = libc.syscall(444, ctypes.byref(handled), 8, 0)
    if ruleset < 0:
        raise OSError(ctypes.get_errno(), 'landlock_create_ruleset')

    class Rule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed', ctypes.c_uint64), ('parent', ctypes.c_int)]

    try:
        for paths, access in ((writable, rights), (readonly, 1 | 4 | 8)):
            for path in paths:
                if not Path(path).exists():
                    continue
                fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
                try:
                    rule = Rule(access, fd)
                    if libc.syscall(445, ruleset, 1, ctypes.byref(rule), 0):
                        raise OSError(ctypes.get_errno(), 'landlock_add_rule')
                finally:
                    os.close(fd)
        if libc.prctl(38, 1, 0, 0, 0) or libc.syscall(446, ruleset, 0):
            raise OSError(ctypes.get_errno(), 'landlock_restrict_self')
    finally:
        os.close(ruleset)
