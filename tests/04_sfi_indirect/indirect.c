#include <stdio.h>
#include <string.h>
#include <stdint.h>

// 1. The target function we want to illegally execute
// Notice it has a different signature (takes an int) than the safe function
void admin_shell(int privilege_level) {
    printf("CRITICAL SFI FAILURE: Control flow hijacked! Admin shell spawned with privilege %d.\n", privilege_level);
}

// 2. The expected, safe function
void print_user() {
    printf("Executing safe user function.\n");
}

// Define a function pointer type that takes no arguments
typedef void (*func_t)();

struct UserAction {
    char buffer[16];
    func_t action_ptr;
};

void process_action(char *payload) {
    struct UserAction action;
    action.action_ptr = print_user;

    // VULNERABILITY: strcpy overruns the 16-byte buffer and overwrites action_ptr
    strcpy(action.buffer, payload);

    printf("Dispatching function pointer...\n");
    // The Indirect Call
    action.action_ptr();
}

int main() {
    printf("--- Normal Execution ---\n");
    process_action("hello");

    printf("\n--- Exploit Attempt ---\n");
    
    // Construct a payload to overflow the buffer and overwrite the function pointer
    char payload[24];
    memset(payload, 'A', 16); 
    
    // In x86, we would put the raw memory address of admin_shell here
    // In Wasm, function pointers are actually just integer indices into a hidden table
    // We will blindly guess that admin_shell is at index 1 or 2 in that table
    uint32_t guessed_index = 2; 
    memcpy(payload + 16, &guessed_index, sizeof(guessed_index));
    payload[20] = '\0'; 

    process_action(payload);

    return 0;
}