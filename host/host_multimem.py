
import os
import threading
import time

import wasmtime
from wasmtime import (
    Config, Engine, Store, Module, Linker, WasiConfig,
    FuncType, ValType, Func,
)

# The channel: a fixed-size byte buffer owned by the host.
# Both guests see it only through channel_read / channel_write.

CHANNEL_SIZE = 4096
channel = bytearray(CHANNEL_SIZE)
channel_lock = threading.Lock() 


def make_channel_imports(store, name):
    """Build the read & write host functions for one guest instance."""

    def channel_write(offset, value):
        # value comes in as an i32; we only store the low byte.
        if offset < 0 or offset >= CHANNEL_SIZE:
            print(f"\033[91m[TCB] {name} blocked: write @ {offset} out of bounds\033[0m")
            return
        with channel_lock:
            channel[offset] = value & 0xFF

    def channel_read(offset):
        if offset < 0 or offset >= CHANNEL_SIZE:
            print(f"\033[91m[TCB] {name} blocked: read @ {offset} out of bounds\033[0m")
            return 0
        with channel_lock:
            return channel[offset]

    write_ty = FuncType([ValType.i32(), ValType.i32()], [])
    read_ty = FuncType([ValType.i32()], [ValType.i32()])

    return (
        Func(store, write_ty, channel_write),
        Func(store, read_ty, channel_read),
    )


def run_instance(name, wasm_path, engine):
    """Run one guest in its own Store/thread with private linear memory."""
    store = Store(engine)

    wasi = WasiConfig()
    wasi.inherit_stdout()
    store.set_wasi(wasi)

    linker = Linker(engine)
    linker.define_wasi()

    write_fn, read_fn = make_channel_imports(store, name)
    linker.define(store, "env", "channel_write", write_fn)
    linker.define(store, "env", "channel_read", read_fn)

    print(f"\033[94m[TCB] Loading {name}...\033[0m")
    try:
        module = Module.from_file(engine, wasm_path)
        instance = linker.instantiate(store, module)
        start = instance.exports(store)["_start"]
        start(store)
        print(f"\033[92m[TCB] {name} finished cleanly.\033[0m")
    except Exception as e:
        print(f"\033[91m[TCB Error] {name} failed: {e}\033[0m")


def main():
    config = Config()
    engine = Engine(config)

    prod_wasm = "tests/08_bridge/multi_memory/producer.wasm"
    cons_wasm = "tests/08_bridge/multi_memory/consumer.wasm"

    if not os.path.exists(prod_wasm) or not os.path.exists(cons_wasm):
        print("\033[91m[Error] Wasm files not found. Did you compile them?\033[0m")
        return

    print("\033[95m\033[1m[TCB] Launching Parallel Sandboxes with bounded channel...\033[0m")
    print(f"[TCB] Channel size: {CHANNEL_SIZE} bytes, mediated by host functions.")

    t1 = threading.Thread(target=run_instance, args=("Producer", prod_wasm, engine))
    t2 = threading.Thread(target=run_instance, args=("Consumer", cons_wasm, engine))

    t1.start()
    time.sleep(0.05)
    t2.start()

    t1.join()
    t2.join()

    print("\033[92m\033[1m[TCB] Parallel Workflow Successfully Terminated.\033[0m")


if __name__ == "__main__":
    main()