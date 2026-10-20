# Capability-Based WebAssembly Runtime

> Built by **Rui Xavier**, **Jendrik Engels** and **Darius Mureșan**.

A secure, capability-based runtime for executing **untrusted C code** inside WebAssembly sandboxes, written in Python on top of [Wasmtime](https://wasmtime.dev/). The project demonstrates how the foundational Language-Based Security properties (**Software-Based Fault Isolation (SFI)**, **Object Capabilities**, and **Execution Monitoring**) can be composed into a working hypervisor that defeats classic memory-corruption, confused-deputy, and denial-of-service attacks.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Environment Setup](#environment-setup)
- [Building & Running](#building--running)
- [Security Test Suite](#security-test-suite)
- [Documentation](#documentation)

---

## Overview

Rather than relying on native OS process isolation or ambient authority, this project uses **WebAssembly (Wasm)** and Python via **Wasmtime** to enforce three core Language-Based Security properties:

| # | Property | What it gives us |
|---|----------|------------------|
| 1 | **SFI** | Wasm's split-memory architecture contains memory corruption, so stack buffer overflows and indirect call hijacking that succeed on native x86 are structurally defeated. Grounded in *Wahbe et al. (1993)*. |
| 2 | **Object Capabilities** | A strict, zero-ambient-authority capability model over WASI. Directly addresses the **Confused Deputy** problem (*Hardy, 1988*), and extends WASI's coarse directory delegation into fine-grained, per-file, per-operation control via ephemeral sandboxing. |
| 3 | **Execution Monitoring** | Liveness and termination enforced via Wasmtime's **fuel-based instruction counter**. |

---

## Repository Structure

We maintain a strict physical boundary between the trusted host runtime and the untrusted guest code. The `host/` directory is our **Trusted Computing Base (TCB)**, which is the only code we trust unconditionally. Everything under `tests/` is treated as adversarial input.

```text
capability-based-wasm-runtime/
├── docs/
│   └── report.pdf                     # Full project report
├── host/
│   ├── host.py                        # TCB: single-guest runtime
│   ├── host_bridge.py                 # TCB variant: filesystem-bridged Producer/Consumer
│   └── host_multimem.py               # TCB variant: host-mediated channel for parallel sandboxes
├── sandbox_data/
│   ├── public.txt                     # File the guest is explicitly granted access to
│   ├── secret.txt                     # File the guest is denied access to (sits outside the sandbox)
│   ├── x.txt                          # Target file for fine-grained capability test (Prog1)
│   └── y.txt                          # Target file for fine-grained capability test (Prog2)
└── tests/                             # Untrusted guest code (malicious C programs)
    ├── 01_hello_world/                # Baseline WASI execution test
    ├── 02_sfi_buffer_overflow/        # Tests linear memory isolation (SFI)
    ├── 03_cap_file_access/            # Tests capability bounding and path traversal
    ├── 04_sfi_indirect/               # Tests coarse-grained CFI via type signatures
    ├── 05_execution_monitoring/       # Tests execution monitoring / DoS mitigation
    ├── 06_cap_network_access/         # Tests network access restriction
    ├── 07_fine_grained/               # Tests ephemeral per-file and per-operation capabilities
    └── 08_bridge/
        ├── transfer_file/             # Test 09: filesystem-bridged two-sandbox communication
        └── multi_memory/              # Test 10: parallel sandboxes with host-mediated channel
```

> **Note:** The `secret.txt` was on purpose placed at the repository root and not in in `sandbox_data/`. It serves as a target for path traversal attacks in Test 03, and its inaccessibility from within the sandbox demonstrates that the capability boundary is enforced correctly.

---

## Environment Setup

### 1. Python Host (All Platforms)

Requires **Python 3.10+**. From the repository root:

```bash
python -m venv wasi-host-env
```

Activate the environment:

```bash
# macOS / Linux
source wasi-host-env/bin/activate

# Windows
wasi-host-env\Scripts\activate
```

Install the Wasmtime VM:

```bash
pip install wasmtime
```

### 2. C-to-Wasm Compiler

Standard `gcc` or `clang` target native x86/ARM and **cannot** be used here. We require a toolchain configured for the `wasm32-wasip1` target, which produces WebAssembly binaries conforming to the WASI p1 system interface rather than making direct OS syscalls.

#### Arch Linux

```bash
sudo pacman -S clang lld wasi-libc
```

#### macOS, Windows, and Ubuntu/Debian

- Download the official WASI SDK from the [WASI SDK Releases page](https://github.com/WebAssembly/wasi-sdk/releases).
- It bundles Clang, LLD, and the `wasi-libc` sysroot (with the required `libclang_rt.builtins-wasm32.a`) into a single folder.
- Extract it to a known location (e.g., `~/wasi-sdk` or `C:\wasi-sdk`).

> **Ubuntu/Debian:** The distro `wasi-libc` package installs headers to a non-standard path and does not ship the compiler-rt builtins. Use the official WASI SDK release instead.

> **Windows (WSL2):** Run `sudo apt install clang lld` and use the Linux WASI SDK release.

---

## Building & Running

### Compiling all tests

We use a `Makefile` with a wildcard rule that automatically discovers and compiles every `.c` file found anywhere under the `tests/` directory. Adding a new test requires only creating a new subfolder with a `.c` file.

```bash
make
```

For macOS and Windows users whose WASI SDK is not at the default path (`/usr/share/wasi-sysroot`), override the compiler and sysroot on the command line:

```bash
make CC=/path/to/wasi-sdk/bin/clang SYSROOT=/path/to/wasi-sdk/share/wasi-sysroot
```

> **macOS users:** The system `clang` (Apple's toolchain) does not support the `wasm32-wasip1` target. The `CC` override is therefore required even if `clang` is already on your PATH.

### Running tests

We provide an interactive CLI that presents a numbered menu of all available tests and invokes the appropriate host hypervisor against the selected binary:

```bash
python run_tests.py
```

Select a test number, `a` to run the full suite sequentially, or `q` to quit.

---

## Security Test Suite

Each test demonstrates one of the core Language-Based Security properties in isolation. Click the test names to jump to the relevant directory.

### Test 02: Memory Isolation via SFI
[`tests/02_sfi_buffer_overflow/`](./tests/02_sfi_buffer_overflow/)

**Attack.** A `strcpy` stack buffer overflow attempts to overwrite a saved return address and hijack control flow, redirecting execution to an attacker-controlled address.

**Result.** The overflow occurs and successfully corrupts adjacent local variables within Wasm linear memory, which confirms the memory is contiguous and the write goes out of bounds, but execution is never redirected. The program terminates normally without the attacker gaining control.

**Why it works.** This distinction between *"the overflow happens"* and *"the exploit succeeds"* is the key demonstration. On native x86, the saved return address lives on the same stack as local variables, so overflowing a buffer can overwrite it directly. Wasm uses a split-stack architecture. Linear memory (where heap and stack-allocated buffers live) is entirely decoupled from the VM's internal execution stack, where return addresses reside. C code compiled to Wasm has no means to address the execution stack at all and it is managed exclusively by the VM and is not part of the addressable memory space. (CFI) against linear overflows is therefore guaranteed structurally and not by any runtime check.

---

### Test 03: Object Capabilities
[`tests/03_cap_file_access/`](./tests/03_cap_file_access/)

**Attack.** The guest acts as a Confused Deputy, attempting to read `/etc/passwd` and to escape the sandbox via a path traversal (`../secret.txt`), exploiting what it assumes to be the host's ambient authority over the filesystem.

**Result.** All unauthorised access attempts are blocked. The guest can read only `/data/public.txt`.

**Why it works.** The Python host initialises the Wasmtime instance with **zero ambient authority**, so no filesystem access is granted by default. It then explicitly pre-opens `./sandbox_data` and maps it to `/data` inside the guest's namespace. This pre-opened directory handle is the only file descriptor the guest ever receives. Because the guest has no capability token for any other path, it cannot name files outside this boundary regardless of what path strings it constructs. Path traversal strings like `../secret.txt` are meaningless without a corresponding capability, because there is no authority to traverse from.

---

### Test 04: Coarse-Grained Control Flow Integrity
[`tests/04_sfi_indirect/`](./tests/04_sfi_indirect/)

**Attack.** The guest overflows a struct to overwrite a function pointer, redirecting it to an `admin_shell()` function that was never intended to be called via that pointer.

**Result.** The Wasmtime VM intercepts the indirect call and ends with `RuntimeError: call indirect type mismatch`.

**Why it works.** Wasm does not store function pointers as raw memory addresses, which is what makes this attack category dangerous on native x86. Instead, all callable functions are registered in a VM-managed structure called Table, which is a hidden array of function references that is separate from linear memory and cannot be read or written by guest code. A "function pointer" in compiled Wasm is simply an integer index into this table. When an indirect call is made, the VM performs a **type-signature check**. So it compares the signature of the function at that index against the signature expected at the call site. Because `admin_shell(int)` has a different signature from the expected `void()`, the check fails and the VM aborts execution before the jump ever occurs. Even if an attacker can overwrite the index value, they cannot call a function with a mismatched signature.

---

### Test 05: Execution Monitoring
[`tests/05_execution_monitoring/`](./tests/05_execution_monitoring/)

**Attack.** A Denial-of-Service attempt in which the guest triggers an infinite loop to monopolise host CPU resources indefinitely, preventing the hypervisor from serving any further requests.

**Result.** The host terminates the guest and catches the resulting trap, keeping the hypervisor responsive.

**Why it works.** We configure Wasmtime with `consume_fuel = True` and provision each guest instance with exactly 50,000 fuel units before execution begins, where one unit corresponds to approximately one Wasm instruction. This value is deliberately small to make the demonstration immediate. In production it would be calibrated to a sensible computational budget. Once the loop exhausts this budget, the VM raises an out-of-fuel trap that our host catches in a `try/except` block, printing a denial message and returning control cleanly. The guest is terminated without any impact on the host process.

---

### Test 06: Network Access Restriction
[`tests/06_cap_network_access/`](./tests/06_cap_network_access/)

**Attack.** The guest attempts to access network-related system resources like `/dev/tcp`, `/proc/net/tcp`, and `/etc/hosts` to simulate an attempt to exfiltrate data or establish a connection to an external server.

**Result.** All three attempts fail with `No such file or directory`. No network resource is reachable from within the sandbox, and the guest terminates normally after reporting each failure.

**Why it works.** The restriction operates at two levels.
1. **Structural impossibility.** WASI p1 exposes no socket primitives whatsoever. `socket()` and `connect()` do not exist in the WASI sysroot and cannot even be compiled against it. Network access is structurally impossible at the language level, not merely blocked at runtime.
2. **Capability bounding.** Our host delegates only the `./sandbox_data` directory as `/data`. Paths such as `/dev`, `/proc`, and `/etc` are not part of the guest's capability set and are entirely invisible to it, so from the guest's perspective, they simply do not exist.

---

### Tests 07 & 08: Fine-Grained Object Capabilities
[`tests/07_fine_grained/`](./tests/07_fine_grained/)

**Attack.** `prog1.c` attempts to write to its allowed file (`x.txt`) and read a forbidden file (`y.txt`). `prog2.c` attempts to read and write to its allowed file (`y.txt`) while attempting to read a forbidden file (`x.txt`).

**Result.** `prog1.c` successfully reads `x.txt`, but traps on write, and is blocked from seeing `y.txt`. `prog2.c` seamlessly reads and writes `y.txt`, but cannot see `x.txt`.

**Why it works.** By default, WASI P1 implements coarse-grained directory delegation. To enforce the Principle of Least Privilege and mitigate the Confused Deputy problem at a per-file/per-operation level, the Python TCB builds an ephemeral sandbox (via Python's `tempfile`) per execution. The TCB dynamically copies only the explicitly allowed files into this ephemeral directory and enforces per-operation access (`r`, `w`, `rw`) by applying native OS-level permissions (`os.chmod`) to the copied descriptors before passing the capability token to the Wasm guest.

---

### Test 09: Compositional Security via Filesystem Bridge
[`tests/08_bridge/transfer_file/`](./tests/08_bridge/transfer_file/)

**Attack.** Two mutually untrusted sandboxes (Producer and Consumer) must exchange data without either being able to compromise the other or escalate its own capabilities. The Producer writes a result to a shared filesystem location; the Consumer reads it back.

**Result.** Data is successfully transferred end-to-end. Neither sandbox holds a capability outside the narrow access granted for its phase of the workflow, and neither can write into the other's private state.

**Why it works.** The host creates a shared directory but tightly controls the information flow by dynamically rotating permissions (`os.chmod`) between executions. The Producer is granted write access during its phase and the Consumer is granted read access during its phase. Because capability tokens cannot be forged or escalated within the guest, the Consumer can never write back into the bridge after the Producer is finished, and the Producer cannot read what the Consumer subsequently produces.

---

### Test 10: Parallel Sandboxes with Host-Mediated Channel
[`tests/08_bridge/multi_memory/`](./tests/08_bridge/multi_memory/)

**Attack.** Two sandboxes run concurrently in parallel threads, each with its own private linear memory. They need to exchange data continuously while live, without giving either sandbox a capability that could be abused to read the other's private state.

**Result.** The Producer streams a message into a bounded shared region (the "channel") and the Consumer reads it back, byte by byte, while both are executing in parallel. Neither sandbox ever holds a Wasm-level memory import that aliases the other's private memory. Out-of-bounds accesses are rejected by the host with a logged denial.

**Why it works.** Each guest is instantiated in its own `Store` (Wasmtime's per-instance state container), running on its own OS thread, with its own private linear memory. The "channel" is a fixed-size `bytearray` owned by the Python host and exposed to each guest only through two imported functions: `channel_write(offset, value)` and `channel_read(offset)`. Every cross-sandbox byte transfer therefore traps out of the guest, into host code, which performs a bounds check against the channel size and a lock acquisition for atomicity before touching the buffer. **The host stands in the middle of every byte.** Wasmtime's `Engine` is shared across threads (effectively immutable once configured), while the mutable per-guest state lives in its `Store`, so the two sandboxes run truly concurrently without sharing any mutable Wasm state.

#### Why we did not let one sandbox point directly into the other's memory

Another approach to the design design would have given the Consumer a Wasm-level pointer or memory import that referenced the Producer's linear memory directly. We rejected this approach because it violates SFI between the two sandboxes*:

- **The premise of SFI is that each module has a disjoint, contained address space.** Wahbe et al.'s isolation guarantee depends on the inability of a module to name any address outside its own region. A pointer into another sandbox's memory destroys exactly that property and the Consumer would have a legitimate, addressable handle into Producer-owned memory, and any C-level pointer arithmetic would let it roam freely across the Producer's heap, stack, and global state. Isolation degrades from "absolute" to "depends on the Consumer not computing bad offsets."
- **Direct pointers are unbounded by construction.** Even with a small initial window, a pointer is just an integer in linear memory and the guest can add to it, subtract from it, or overwrite it via any of the memory-corruption attacks. There would be no place for the host to interpose a bounds check, because the dereference happens inside the Wasm VM without any host trap.
- **It collapses the two-sandbox security model into one.** If Consumer can read arbitrary Producer memory, then Producer's "private memory" is no longer private but it is effectively shared.

The Producer's secret state lives in Producer's linear memory and is invisible to the Consumer and the only data the Consumer ever sees is what the Producer chose to push to the channel. Even if the Consumer attempts wild pointer dereferences inside its own linear memory, those reads can never reach the Producer, so the two address spaces are never connected at the Wasm level.

---

## Documentation

The full write-up (background, threat model, design and evaluation) is in [`docs/report.pdf`](./docs/report.pdf).

### References

- Wahbe, R., Lucco, S., Anderson, T. E., and Graham, S. L. (1993). *Efficient software-based fault isolation.* SOSP '93.
- Hardy, N. (1988). *The confused deputy: (or why capabilities might have been invented).* ACM SIGOPS Operating Systems Review, 22(4).
- Saltzer, J. H. and Schroeder, M. D. (1975). *The protection of information in computer systems.* Proceedings of the IEEE, 63(9).
- Moore, S., Dimoulas, C., King, D., and Chong, S. (2014). *SHILL: A secure shell scripting language.* OSDI '14.
- Fitzgibbons, M., Paraskevopoulou, Z., Mushtak, N., Thalakottur, M., Manzur, J. S., and Ahmed, A. (2024). *RichWasm: Bringing safe, fine-grained, shared-memory interoperability down to WebAssembly.* PLDI '24.
- Ferreira, G., Jia, L., Sunshine, J., and Kästner, C. (2021). *Containing malicious package updates in npm with a lightweight permission system.* ICSE '21.
- Cornelissen, E. and Balliu, M. (2025). *NodeShield: Runtime enforcement of security-enhanced SBOMs for Node.js.* CCS '25.