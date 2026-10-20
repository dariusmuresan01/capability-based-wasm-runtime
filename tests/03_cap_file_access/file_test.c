#include <stdio.h>
#include <stdlib.h>

void try_read_file(const char* filename) {
    printf("Attempting to open: %s\n", filename);
    FILE *file = fopen(filename, "r");

    if (file == NULL) {
        printf("[\033[31mDENIED\033[0m] Could not open %s. Capability missing!\n\n", filename);
        return;
    }

    printf("[\033[32mGRANTED\033[0m] Successfully opened %s. Contents:\n", filename);
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), file) != NULL) {
        printf(" -> %s", buffer);
    }
    printf("\n\n");
    fclose(file);
}

int main() {
    printf("--- WASI Object Capability Test ---\n\n");

    // 1. Legal access (inside the explicitly granted capability directory)
    try_read_file("/data/public.txt");

    // 2. Illegal access (attempting to read absolute host paths)
    try_read_file("/etc/passwd");

    // 3. Illegal access (attempting directory traversal to escape the sandbox)
    try_read_file("/data/../secret.txt");

    return 0;
}