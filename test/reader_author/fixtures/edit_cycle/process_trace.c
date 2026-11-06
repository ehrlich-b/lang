// Test-only process counts through libc fork and POSIX spawn, including Clang's linker.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static void record(const char *kind, pid_t child) {
    const char *path = getenv("EDIT_PROCESS_TRACE");
    if (path) {
        int fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0600);
        if (fd >= 0) {
            char row[100];
            int n = snprintf(row, sizeof row, "%s %ld %ld\n", kind, (long)getpid(), (long)child);
            if (write(fd, row, n) != n) _exit(125);
            close(fd);
        }
    }
}
pid_t fork(void) {
    static pid_t (*real_fork)(void);
    if (!real_fork) real_fork = dlsym(RTLD_NEXT, "fork");
    pid_t child = real_fork();
    if (child > 0) record("fork", child);
    return child;
}
int posix_spawn(pid_t *pid, const char *path, const posix_spawn_file_actions_t *actions,
                const posix_spawnattr_t *attrs, char *const argv[], char *const envp[]) {
    static int (*real_spawn)(pid_t *, const char *, const posix_spawn_file_actions_t *,
                            const posix_spawnattr_t *, char *const [], char *const []);
    if (!real_spawn) real_spawn = dlsym(RTLD_NEXT, "posix_spawn");
    int result = real_spawn(pid, path, actions, attrs, argv, envp);
    if (!result) record("spawn", *pid);
    return result;
}
int posix_spawnp(pid_t *pid, const char *path, const posix_spawn_file_actions_t *actions,
                 const posix_spawnattr_t *attrs, char *const argv[], char *const envp[]) {
    static int (*real_spawnp)(pid_t *, const char *, const posix_spawn_file_actions_t *,
                             const posix_spawnattr_t *, char *const [], char *const []);
    if (!real_spawnp) real_spawnp = dlsym(RTLD_NEXT, "posix_spawnp");
    int result = real_spawnp(pid, path, actions, attrs, argv, envp);
    if (!result) record("spawnp", *pid);
    return result;
}
