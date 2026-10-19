#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 3) return 2;
    int ok = 0, fd;
    if (!strcmp(argv[1], "read")) { fd=open(argv[2],O_RDONLY); ok=fd>=0; }
    if (!strcmp(argv[1], "write")) { fd=open(argv[2],O_WRONLY); ok=fd>=0; }
    if (!strcmp(argv[1], "socket")) { fd=socket(AF_INET,SOCK_STREAM,0); ok=fd>=0; }
    if (!strcmp(argv[1], "descriptor")) { char c; ok=read(atoi(argv[2]),&c,1)==1; }
    if (!strcmp(argv[1], "child")) {
        pid_t p=fork(); if (p==0) _exit(0);
        if (p>0) { int s; waitpid(p,&s,0); ok=WIFEXITED(s)&&WEXITSTATUS(s)==0; }
    }
    printf("%s=%s\n",argv[1],ok?"ESCAPE":"DENIED");
    return ok ? 1 : 0;
}
