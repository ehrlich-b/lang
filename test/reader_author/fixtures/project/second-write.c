// Deterministic storage failure on the generated project's second file.
// No production fault-injection hooks and no modification of existing files.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

ssize_t write(int fd, const void *data, size_t size) {
    char proc[64], path[4096];
    snprintf(proc, sizeof proc, "/proc/self/fd/%d", fd);
    ssize_t n = readlink(proc, path, sizeof path - 1);
    if (n >= 0) {
        path[n] = 0;
        const char *suffix = "/failed/runtime.lang";
        size_t length = strlen(suffix);
        if ((size_t)n >= length && !strcmp(path + n - length, suffix)) {
            errno = ENOSPC;
            return -1;
        }
    }
    ssize_t (*real_write)(int, const void *, size_t) = dlsym(RTLD_NEXT, "write");
    return real_write(fd, data, size);
}
