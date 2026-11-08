#define _GNU_SOURCE
/* Drop host-namespace credentials before ANY setup; mount proc only inside
 * an unprivileged user/PID namespace. No uid 0 mapping or root commands.
 */
#include <fcntl.h>
#include <grp.h>
#include <sched.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/wait.h>

static int mapping(const char *path, const char *text, int length) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) return 1;
    int result = write(fd, text, length) != length;
    close(fd);
    return result;
}

int main(void) {
    if (setgroups(0, 0) || setgid(1000) || setuid(1000)) return 1;
    if (getuid() != 1000 || geteuid() != 1000) return 2;
    /* setuid clears dumpability; restore ownership of our own proc map files. */
    if (prctl(PR_SET_DUMPABLE, 1)) return 3;
    if (unshare(CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID)) {
        perror("unprivileged namespaces"); return 3;
    }
    pid_t child = fork();
    if (child == 0) {
        if (mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, "subset=pid")) {
            perror("unprivileged proc mount"); _exit(4);
        }
        if (mapping("/proc/self/uid_map", "1000 1000 1\n", 12)) {
            perror("uid mapping"); _exit(5);
        }
        if (mapping("/proc/self/setgroups", "deny\n", 5) ||
            mapping("/proc/self/gid_map", "1000 1000 1\n", 12)) {
            perror("gid mapping"); _exit(6);
        }
        char *args[] = {"/usr/bin/python3", "-B", "/journey.py", 0};
        char *env[] = {"PATH=/usr/bin:/bin", "HOME=/consumer", "TMPDIR=/tmp",
                       "LANGBE=llvm", "LANGOS=linux", "PYTHONDONTWRITEBYTECODE=1", 0};
        execve(args[0], args, env);
        _exit(127);
    }
    if (child < 0) return 3;
    int status;
    while (wait(&status) > 0) {
        if (status) {
            fprintf(stderr, "SDK_BOOT_ERROR=guest process exited with status %d\n", status);
        }
    }
    for (;;) pause(); /* The unprivileged host terminates QEMU after the receipt. */
}
