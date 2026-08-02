import os, sys, runpy
import torch

mm = os.environ["MM_TF32"] == "1"
cud = os.environ["CUDNN_TF32"] == "1"
torch.backends.cuda.matmul.allow_tf32 = mm
torch.backends.cudnn.allow_tf32 = cud
if "CUDNN_BENCHMARK" in os.environ:
    torch.backends.cudnn.benchmark = os.environ["CUDNN_BENCHMARK"] == "1"

print(f"[wrap] matmul.allow_tf32={torch.backends.cuda.matmul.allow_tf32} "
      f"cudnn.allow_tf32={torch.backends.cudnn.allow_tf32} "
      f"cudnn.benchmark={torch.backends.cudnn.benchmark}", flush=True)

script = os.environ["TARGET_SCRIPT"]
sys.argv = [script] + os.environ["TARGET_ARGS"].split()
runpy.run_path(script, run_name="__main__")
