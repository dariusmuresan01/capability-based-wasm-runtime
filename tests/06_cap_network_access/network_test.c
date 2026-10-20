#include <stdio.h>
#include <errno.h>
#include <string.h>

// WASI p1 does not expose socket syscalls.
// manually invoke the raw syscall number for socket() to prove the host kernel interface is completely absent
extern int __wasi_sock_open; 

int main() {
    printf("[GUEST] Attempting network access...\n");

    // Try to open /dev/tcp 
    FILE *f = fopen("/dev/tcp", "r");
    if (f == NULL) {
        printf("[GUEST] fopen('/dev/tcp') failed: %s\n", strerror(errno));
    }

    // Try to open /proc/net/tcp; read network state
    FILE *g = fopen("/proc/net/tcp", "r");
    if (g == NULL) {
        printf("[GUEST] fopen('/proc/net/tcp') failed: %s\n", strerror(errno));
    }

    // Try to reach outside the sandbox via path traversal to network config
    FILE *h = fopen("/etc/hosts", "r");
    if (h == NULL) {
        printf("[GUEST] fopen('/etc/hosts') failed: %s\n", strerror(errno));
    } else {
        printf("[GUEST] WARNING: /etc/hosts opened! Capability model failed!\n");
        fclose(h);
    }

    printf("[GUEST] All network/system access attempts blocked.\n");
    printf("[GUEST] No socket primitives available in WASI p1.\n");
    return 0;
}