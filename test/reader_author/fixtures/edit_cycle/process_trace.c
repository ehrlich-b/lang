// Test-only process counts for the complete native build tree.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
pid_t fork(void) {
    static pid_t (*real_fork)(void);
    if (!real_fork) real_fork = dlsym(RTLD_NEXT, "fork");
    pid_t child = real_fork();
    const char *path = getenv("EDIT_PROCESS_TRACE");
    if (child > 0 && path) {
        int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
        if (fd >= 0) {
            char row[100];
            int n = snprintf(row, sizeof row, "%ld %ld\n", (long)getpid(), (long)child);
            if (write(fd, row, n) != n) _exit(125);
            close(fd);
        }
    }
    return child;
}
