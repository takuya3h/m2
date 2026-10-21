"""Run Relation-DETR's main.py unchanged, recording each rank's peak GPU memory in bytes.

T-2026-10-19-dlsta-tower-feasibility, Task D. The training log prints ``max mem`` rounded
to MiB; the contract asks for unrounded values, so a daemon thread writes
``torch.cuda.max_memory_allocated`` / ``max_memory_reserved`` (bytes) every 2 s to
``$MEMPROBE_DIR/torch_mem_rank<R>.json``. Every argument after this script's name is
handed to main.py untouched, and main.py runs as ``__main__`` from the current directory
(third_party/Relation-DETR), exactly as ``accelerate launch ... main.py`` would.
"""
import json
import os
import runpy
import sys
import threading
import time

OUT = os.environ["MEMPROBE_DIR"]
RANK = os.environ.get("RANK", "0")
LOCAL_RANK = int(os.environ.get("LOCAL_RANK", "0"))


def _loop():
    import torch
    path = os.path.join(OUT, f"torch_mem_rank{RANK}.json")
    while True:
        time.sleep(2)
        if not torch.cuda.is_initialized():
            continue
        record = {
            "rank": RANK, "local_rank": LOCAL_RANK,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "max_memory_allocated_bytes": torch.cuda.max_memory_allocated(LOCAL_RANK),
            "max_memory_reserved_bytes": torch.cuda.max_memory_reserved(LOCAL_RANK),
            "memory_allocated_bytes": torch.cuda.memory_allocated(LOCAL_RANK),
            "time": time.time(),
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as handle:
            json.dump(record, handle)
        os.replace(tmp, path)


threading.Thread(target=_loop, daemon=True).start()
sys.path.insert(0, os.getcwd())
sys.argv = ["main.py"] + sys.argv[1:]
runpy.run_path("main.py", run_name="__main__")
