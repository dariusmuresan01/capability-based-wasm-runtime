#include <stdio.h>

int main() {
    FILE *f = fopen("/bridge/message.txt", "w");
    if (f == NULL) return 1;
    fprintf(f, "LBS_SECRET_TOKEN_2026");
    fclose(f);
    printf("Guest A: Successfully sent message to bridge.\n");
    return 0;
}