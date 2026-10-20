#include <stdio.h>

int main() {
    char buf[100];
    FILE *f = fopen("/bridge/message.txt", "r");
    if (f == NULL) {
        printf("Guest B: Access Denied to Bridge!\n");
        return 1;
    }
    fgets(buf, 100, f);
    printf("Guest B received data: %s\n", buf);
    fclose(f);
    return 0;
}