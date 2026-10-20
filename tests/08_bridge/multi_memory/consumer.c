#include <stdio.h>
#include <unistd.h>

extern void channel_write(int offset, int value);
extern int  channel_read(int offset);

int main() {
    printf("[Consumer] Monitoring the channel for updates...\n");

    while (channel_read(0) != 1) {
        usleep(1000);
    }

    // Read the message byte by byte into a local buffer
    char buf[256];
    int i = 0;
    while (i < (int)sizeof(buf) - 1) {
        int b = channel_read(i + 1);
        buf[i] = (char)b;
        if (b == 0) break;
        i++;
    }
    buf[sizeof(buf) - 1] = 0;

    printf("[Consumer] Flag detected! Reading from shared space: %s\n", buf);
    return 0;
}