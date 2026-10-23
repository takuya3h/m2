"""Drive probe.py trials for one phase and append every trial to results.jsonl.

    python run_probe.py calib | vit | moco | vmae | mamba

Batch search: start at the target and halve until a trial fits. Each trial is its own process
with a 30-minute limit; a timeout is recorded as status=timeout (the row becomes UNKNOWN).
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results.jsonl"
LIMIT = 1800
ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "0", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"}
ENV.pop("PYTORCH_CUDA_ALLOC_CONF", None)


def trial(*argv):
    started = time.time()
    try:
        done = subprocess.run([sys.executable, str(HERE / "probe.py"), *argv], env=ENV,
                              capture_output=True, text=True, timeout=LIMIT)
        lines = [ln for ln in done.stdout.splitlines() if ln.startswith("{")]
        rec = json.loads(lines[-1]) if lines else {
            "status": "error", "returncode": done.returncode, "stderr_tail": done.stderr[-1500:]}
    except subprocess.TimeoutExpired:
        rec = {"status": "timeout", "limit_seconds": LIMIT}
    rec.update(argv=list(argv), wall_seconds=time.time() - started,
               finished_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    with OUT.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print(rec.get("status"), argv, f"{rec.get('peak_allocated_gib', float('nan')):.2f}GiB",
          rec.get("step_seconds_mean"), flush=True)
    return rec


def search(target, *argv):
    batch = target
    while batch >= 1:
        rec = trial(*argv, "--batch", str(batch))
        if rec["status"] != "oom":
            return rec
        batch //= 2
    return rec


def main(phase):
    if phase == "calib":
        for b in (1, 2, 16):
            trial("calib", "--batch", str(b))
    elif phase == "vit":
        for size in ("base", "large"):
            for res, target in (("224", 64), ("448", 16), ("800", 4)):
                for scope in ("full", "top4", "linear"):
                    search(target, "vit", "--size", size, "--res", res, "--scope", scope)
    elif phase == "moco":
        search(256, "moco")
    elif phase == "vmae":
        search(256, "vmae")
    elif phase == "mamba":
        trial("mamba")
    elif phase == "control":
        # every target fit, so the search never saw a failure: one batch above the target
        # must fail, or the OOM path of the search is not shown to work
        trial("vit", "--size", "large", "--res", "800", "--scope", "full", "--batch", "8")
        trial("moco", "--batch", "512")
        trial("vmae", "--batch", "512")
        trial("mamba")


if __name__ == "__main__":
    main(sys.argv[1])
