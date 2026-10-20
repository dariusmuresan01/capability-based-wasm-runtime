#include <stdio.h>
#include <string.h>

// The attacker's goal is to redirect execution here.
void secret_function() {
    printf("CRITICAL SFI FAILURE: Control flow hijacked!\n");
}

void vulnerable_function(char *input) {
    int safe_var = 0x11223344;
    char buffer[16];

    // VULNERABILITY: strcpy does no bounds checking
    strcpy(buffer, input);

    printf("Buffer contains: %s\n", buffer);
    printf("safe_var is: 0x%x\n", safe_var);
}

int main() {
    printf("--- Normal Execution ---\n");
    vulnerable_function("Hello World");

    printf("\n--- Exploitation Attempt ---\n");
    // We send 16 bytes of junk to fill the buffer, 
    // plus extra bytes to overflow into adjacent memory
    vulnerable_function("AAAAAAAAAAAAAAAA_BBBBBBBBBBBBBBBB");

    return 0;
}