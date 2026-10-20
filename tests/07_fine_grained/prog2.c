#include <stdio.h>
#include <errno.h>
#include <string.h>

int main() {
    printf("--- Prog2 (Policy: y.txt 'rw') ---\n\n");

    // 1. Attempt authorized write to y.txt
    FILE *f_y_write = fopen("/data/y.txt", "a");
    if (f_y_write) {
        fprintf(f_y_write, " (Modified by Prog2)\n");
        printf("[\033[32mGRANTED\033[0m] Successfully wrote to y.txt\n");
        fclose(f_y_write);
    } else {
        printf("[\033[31mFAIL\033[0m] Could not write to y.txt: %s\n", strerror(errno));
    }

    // 2. Attempt authorized read on y.txt
    FILE *f_y = fopen("/data/y.txt", "r");
    if (f_y) {
        char buf[64];
        fgets(buf, sizeof(buf), f_y);
        printf("[\033[32mGRANTED\033[0m] Read y.txt: %s\n", buf);
        fclose(f_y);
    } else {
        printf("[\033[31mFAIL\033[0m] Could not read y.txt: %s\n", strerror(errno));
    }

    // 3. Attempt unauthorized read on x.txt
    FILE *f_x = fopen("/data/x.txt", "r");
    if (f_x) {
        printf("[\033[31mFAIL\033[0m] Opened x.txt! Per-file policy failed.\n");
        fclose(f_x);
    } else {
        printf("[\033[32mBLOCKED\033[0m] Read x.txt denied: %s\n", strerror(errno));
    }

    return 0;
}