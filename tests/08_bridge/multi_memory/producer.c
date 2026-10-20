#include <stdio.h>

extern void channel_write(int offset, int value);
extern int  channel_read(int offset);

int main() {
    printf("[Producer] Working in private memory...\n");
    const char *secret_work = "Processed_Data_Result";

    printf("[Producer] Copying result to the channel...\n");
    int i = 0;
    while (secret_work[i] != '\0') {
        channel_write(i + 1, (unsigned char)secret_work[i]);
        i++;
    }
    channel_write(i + 1, 0);  
    channel_write(0, 1);      

    printf("[Producer] Result exported. Private memory is still isolated.\n");
    return 0;
}