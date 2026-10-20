"""
Interactive Test Selector
This script provides an interactive CLI to choose which security test to run,
and then spawns the host hypervisor as a subprocess.
"""

import os
import subprocess
import sys

# ANSI Color Codes for Terminal Output
class Colors:
    HEADER = '\033[95m'      # Magenta/Purple
    OKBLUE = '\033[94m'      # Blue
    OKCYAN = '\033[96m'      # Cyan
    OKGREEN = '\033[92m'     # Green
    WARNING = '\033[93m'     # Yellow
    FAIL = '\033[91m'        # Red
    ENDC = '\033[0m'         # Reset to default
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Sentinel paths for tests that use a dedicated host rather than the standard host.py
BRIDGE_FILE_TRANSFER = "BRIDGE_FILE_TRANSFER"
MULTI_MEMORY_CHANNEL = "MULTI_MEMORY_CHANNEL"

# Map menu choices to their descriptions and target Wasm binaries
TESTS = {
    "1":  ("Baseline Test (Hello World)", "tests/01_hello_world/test.wasm"),
    "2":  ("Proving Memory Isolation (SFI)", "tests/02_sfi_buffer_overflow/vuln.wasm"),
    "3":  ("Proving Object Capabilities", "tests/03_cap_file_access/file_test.wasm"),
    "4":  ("Proving Coarse-Grained CFI", "tests/04_sfi_indirect/indirect.wasm"),
    "5":  ("Proving Execution Monitoring (Liveness)", "tests/05_execution_monitoring/infinite_loop.wasm"),
    "6":  ("Proving Network Access Restriction", "tests/06_cap_network_access/network_test.wasm"),
    "7":  ("Proving Fine-Grained Cap (Prog1 - Read Only x.txt)", "tests/07_fine_grained/prog1.wasm"),
    "8":  ("Proving Fine-Grained Cap (Prog2 - Read/Write y.txt)", "tests/07_fine_grained/prog2.wasm"),
    "9":  ("Two-Box: Secure File Transfer (Producer -> Consumer)", BRIDGE_FILE_TRANSFER),
    "10": ("Two-Box: Multi-Memory Channel (Producer || Consumer)", MULTI_MEMORY_CHANNEL),
}


def build_command(path):
    """Pick the right host script and command for a given test path"""
    if path == BRIDGE_FILE_TRANSFER:
        return ["python", "host/host_bridge.py"]
    if path == MULTI_MEMORY_CHANNEL:
        return ["python", "host/host_multimem.py"]
    # Standard test: run via the main host with the wasm binary as an argument
    return ["python", "host/host.py", path]


def check_binaries_exist(path):
    """Verify the wasm artifact(s) for this test are present on disk"""
    if path == BRIDGE_FILE_TRANSFER:
        required = [
            "tests/08_bridge/transfer_file/producer.wasm",
            "tests/08_bridge/transfer_file/consumer.wasm",
        ]
    elif path == MULTI_MEMORY_CHANNEL:
        required = [
            "tests/08_bridge/multi_memory/producer.wasm",
            "tests/08_bridge/multi_memory/consumer.wasm",
        ]
    else:
        required = [path]

    missing = [p for p in required if not os.path.exists(p)]
    return missing


def run_test(desc, path):
    """Validate and run a single test. Returns True on success, False if binaries are missing"""
    missing = check_binaries_exist(path)
    if missing:
        print(f"\n{Colors.FAIL}{Colors.BOLD}[ERROR]{Colors.ENDC} Required wasm binary not found:")
        for p in missing:
            print(f"        {p}")
        print(f"{Colors.WARNING}Did you forget to run 'make' to compile the C code first?{Colors.ENDC}")
        return False

    cmd = build_command(path)
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}>>> Running:{Colors.ENDC} {desc}")
    print(f"{Colors.OKBLUE}>>> Command:{Colors.ENDC} {' '.join(cmd)}\n")
    subprocess.run(cmd)
    return True


def run_all():
    """Run every test in TESTS sequentially, continuing past failures"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}==================================================={Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}      RUNNING ALL SECURITY TESTS SEQUENTIALLY      {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}==================================================={Colors.ENDC}")

    results = []
    for key, (desc, path) in TESTS.items():
        ok = run_test(desc, path)
        results.append((key, desc, ok))
        print(f"{Colors.WARNING}" + "-" * 51 + f"{Colors.ENDC}")

    # Summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}=================== SUMMARY ==================={Colors.ENDC}")
    for key, desc, ok in results:
        status = (f"{Colors.OKGREEN}[OK]{Colors.ENDC}" if ok
                  else f"{Colors.FAIL}[SKIPPED]{Colors.ENDC}")
        print(f"  {status} [{key}] {desc}")

    skipped = sum(1 for _, _, ok in results if not ok)
    if skipped:
        print(f"\n{Colors.WARNING}{skipped} test(s) skipped due to missing binaries.{Colors.ENDC}")
    else:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUITE COMPLETE]{Colors.ENDC} All tests finished executing.")


def main():
    print(f"{Colors.HEADER}{Colors.BOLD}==================================================={Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  Language-Based Security: Wasm Sandbox Test Menu  {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}==================================================={Colors.ENDC}\n")

    for key, (desc, _path) in TESTS.items():
        print(f"  {Colors.OKGREEN}[{key:>2}]{Colors.ENDC} {desc}")

    print(f"\n  {Colors.WARNING}[ a]{Colors.ENDC} Run All Tests")
    print(f"  {Colors.FAIL}[ q]{Colors.ENDC} Quit")

    max_key = max(int(k) for k in TESTS.keys())
    choice = input(
        f"\n{Colors.BOLD}Select an option (1-{max_key}, a, q): {Colors.ENDC}"
    ).strip().lower()

    if choice == 'q':
        print(f"{Colors.OKCYAN}Exiting...{Colors.ENDC}")
        sys.exit(0)

    if choice == 'a':
        run_all()
        return

    if choice in TESTS:
        desc, path = TESTS[choice]
        run_test(desc, path)
        return

    print(f"\n{Colors.FAIL}[ERROR] Invalid choice. Please select a valid option.{Colors.ENDC}")


if __name__ == "__main__":
    main()