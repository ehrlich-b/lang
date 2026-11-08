#!/bin/sh
# Keep dependency failures ahead of reader expansion and generated code.
case "${1-}" in
    new|help|version|--version|--help|-h|doctor|'') ;;
    *)
        if ! command -v "${LANG_CLANG:-clang}" >/dev/null 2>&1; then
            echo 'Error: clang is required; install Clang and the system C development toolchain (Debian/Ubuntu: apt install clang build-essential), then add clang to PATH or set LANG_CLANG.' >&2
            exit 127
        fi
        ;;
esac
sdk_bin=$(CDPATH= cd -- "${0%/*}" && pwd) || exit 1
exec "$sdk_bin/../libexec/lang" "$@"
