#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
int main(int argc, char **argv) {
    if (argc < 3) return 2;
    int ok = 0, fd;
    if (!strcmp(argv[1], "read")) { fd=open(argv[2],O_RDONLY); ok=fd>=0; }
    if (!strcmp(argv[1], "write")) { fd=open(argv[2],O_WRONLY); ok=fd>=0; }
    if (!strcmp(argv[1], "socket")) {
        fd=socket(AF_INET,SOCK_STREAM,0);
        printf("socket-created=%s\n",fd>=0?"yes":"no");
        if (fd>=0) {
            struct timeval timeout={2,0};
            struct sockaddr_in address={0};
            setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
            address.sin_family=AF_INET;
            address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
            address.sin_port=htons(atoi(argv[2]));
            ok=connect(fd,(struct sockaddr *)&address,sizeof(address))==0;
            close(fd);
        }
    }
    if (!strcmp(argv[1], "descriptor")) { char c; ok=read(atoi(argv[2]),&c,1)==1; }
    if (!strcmp(argv[1], "child")) {
        pid_t p=fork(); if (p==0) _exit(0);
        if (p>0) { int s; waitpid(p,&s,0); ok=WIFEXITED(s)&&WEXITSTATUS(s)==0; }
    }
    printf("%s=%s\n",argv[1],ok?"ESCAPE":"DENIED");
    return ok ? 1 : 0;
}
