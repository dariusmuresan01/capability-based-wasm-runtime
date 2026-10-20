#include <stdio.h>
#include <errno.h>
#include <string.h>

int main() {
    printf("--- Prog1 (Policy: x.txt 'r') ---\n\n");

    // 1. Attempt authorized read on x.txt
    FILE *f_x = fopen("/data/x.txt", "r");
    if (f_x) {
        char buf[64];
        fgets(buf, sizeof(buf), f_x);
        printf("[\033[32mGRANTED\033[0m] Read x.txt: %s\n", buf);
        fclose(f_x);
    } else {
        printf("[\033[31mFAIL\033[0m] Could not read x.txt: %s\n", strerror(errno));
    }

    // 2. Attempt unauthorized write to x.txt
    FILE *f_x_write = fopen("/data/x.txt", "a");
    if (f_x_write) {
        printf("[\033[31mFAIL\033[0m] Wrote to x.txt! Per-operation policy failed.\n");
        fclose(f_x_write);
    } else {
        printf("[\033[32mBLOCKED\033[0m] Write to x.txt denied: %s\n", strerror(errno));
    }

    // 3. Attempt unauthorized read on y.txt
    FILE *f_y = fopen("/data/y.txt", "r");
    if (f_y) {
        printf("[\033[31mFAIL\033[0m] Opened y.txt! Per-file policy failed.\n");
        fclose(f_y);
    } else {
        printf("[\033[32mBLOCKED\033[0m] Read y.txt denied: %s\n", strerror(errno));
    }

    return 0;
}