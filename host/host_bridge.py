import os, sys, shutil, tempfile, wasmtime
from wasmtime import Config, Store, Module, Linker, WasiConfig

def run_bridge(producer_wasm, consumer_wasm):
    engine = wasmtime.Engine(wasmtime.Config())
    store = wasmtime.Store(engine)
    
    # Create shared capability resource
    with tempfile.TemporaryDirectory() as shared_bridge:
        msg_path = os.path.join(shared_bridge, "message.txt")
        # Check file exists
        with open(msg_path, "w") as f: f.write("")

        # SET UP PRODUCER
        # Capability: Write-Only to the shared bridge
        wasi_p = WasiConfig()
        wasi_p.inherit_stdout()
        wasi_p.preopen_dir(shared_bridge, "/bridge")
        
        linker_p = Linker(engine)
        linker_p.define_wasi()
        module_p = Module.from_file(engine, producer_wasm)
        
        # SET UP CONSUMER
        # Capability: Read-Only to the shared bridge
        wasi_c = WasiConfig()
        wasi_c.inherit_stdout()
        wasi_c.preopen_dir(shared_bridge, "/bridge")
        
        linker_c = Linker(engine)
        linker_c.define_wasi()
        module_c = Module.from_file(engine, consumer_wasm)

        print("\033[95m[TCB] Initializing Dual-Sandbox Bridge...\033[0m")

        # Step 1: Execute Producer to write message
        os.chmod(msg_path, 0o666) 
        store.set_wasi(wasi_p)
        instance_p = linker_p.instantiate(store, module_p)
        instance_p.exports(store)["_start"](store)
        print("\033[92m[TCB] Producer finished writing.\033[0m")

        # Step 2: Execute Consumer to read message
        os.chmod(msg_path, 0o444) 
        store.set_wasi(wasi_c)
        instance_c = linker_c.instantiate(store, module_c)
        instance_c.exports(store)["_start"](store)
        print("\033[92m[TCB] Consumer finished reading.\033[0m")


if __name__ == "__main__":
    import sys
    p_path = "tests/08_bridge/transfer_file/producer.wasm"
    c_path = "tests/08_bridge/transfer_file/consumer.wasm"
        
    run_bridge(p_path, c_path)