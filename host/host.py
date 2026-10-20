import sys
import os
import tempfile
import shutil
import gc
from wasmtime import Config, Store, Module, Instance, WasiConfig, Engine, Linker

# ANSI Color Codes for Terminal Output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# FINE-GRAINED ACCESS CONTROL POLICY
# Defines per-file and per-operation capabilities for specific guest modules.
# Operations: "r" (read-only), "w" (write), "rw" (read/write).
SECURITY_POLICY = {
    "tests/03_cap_file_access/file_test.wasm": {
        "public.txt": "r"
    },
    "tests/07_fine_grained/prog1.wasm": {
        "x.txt": "r"       # Prog1 gets Read-Only access to x.txt
    },
    "tests/07_fine_grained/prog2.wasm": {
        "y.txt": "rw"      # Prog2 gets Read/Write access to y.txt
    }
}

def main():
    if len(sys.argv) < 2:
        print(f"{Colors.FAIL}{Colors.BOLD}[ERROR]{Colors.ENDC} TCB requires a path to a .wasm module.")
        sys.exit(1)
        
    target_wasm_file = sys.argv[1]

    # 1. THE EXECUTION LAYER (SFI & Liveness)
    config = Config()
    config.consume_fuel = True
    engine = Engine(config)
    store = Store(engine)
    store.set_fuel(50000)

    # 2. CAPABILITY RESOLUTION
    # Default to an empty capability set (Zero Ambient Authority)
    allowed_files = SECURITY_POLICY.get(target_wasm_file, {})

    # 3. EPHEMERAL SANDBOX CONSTRUCTION
    # We create a temporary directory that acts as the strict capability boundary
    with tempfile.TemporaryDirectory() as ephemeral_sandbox:
        
        # Populate the ephemeral sandbox based on the security policy
        for filename, mode in allowed_files.items():
            src_path = os.path.join("./sandbox_data", filename)
            dst_path = os.path.join(ephemeral_sandbox, filename)
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                
                # Enforce per-operation capabilities using OS-level permissions
                if mode == "r":
                    os.chmod(dst_path, 0o444) # Read-only
                elif "w" in mode or "rw" in mode:
                    os.chmod(dst_path, 0o644) # Read/Write
            else:
                print(f"{Colors.WARNING}[TCB WARNING] Policy grants access to missing file: {filename}{Colors.ENDC}")

        # 4. SYSTEM LAYER (Object Capabilities & WASI)
        wasi = WasiConfig()
        wasi.inherit_stdout()
        
        # Delegate ONLY the ephemeral sandbox 
        # The guest now believes this strict view is its entire /data directory.
        wasi.preopen_dir(ephemeral_sandbox, "/data")
        store.set_wasi(wasi)

        # 5. LINKING AND INSTANTIATION
        linker = Linker(engine)
        linker.define_wasi()
        
        try:
            module = Module.from_file(engine, target_wasm_file)
        except Exception as e:
            print(f"{Colors.FAIL}{Colors.BOLD}[ERROR]{Colors.ENDC} Host failed to load '{target_wasm_file}': {e}")
            sys.exit(1)

        instance = linker.instantiate(store, module)
        start_func = instance.exports(store)["_start"]
        print(f"{Colors.HEADER}{Colors.BOLD}--- Sandbox Initialized. Executing Guest Code ---{Colors.ENDC}")
        
        try:
            start_func(store)
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCESS]{Colors.ENDC} Guest code executed and terminated normally.")
        except Exception as e:
            print(f"\n{Colors.WARNING}{Colors.BOLD}[HOST SAVED]{Colors.ENDC} Execution forcefully terminated by VM: \n{Colors.FAIL}{e}{Colors.ENDC}")

        # Optional: If your policy allows "w" (write), you would sync modifications 
        # from `ephemeral_sandbox` back to `./sandbox_data` here.
        del start_func
        del instance
        del linker
        del store
        del engine
        gc.collect()

if __name__ == "__main__":
    main()