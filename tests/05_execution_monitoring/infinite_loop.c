#include <stdio.h>

int main() {
    printf("Starting infinite loop.\n");
    
    // An infinite loop violates the "Liveness" property (termination)
    while (1) {
        // Do nothing, just spin forever
    }

    return 0;
}