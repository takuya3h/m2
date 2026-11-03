"""Task A-5: その仮想環境の Python で、§6.1 の env の静的な欄を取る（読むだけ。標準出力の JSON）。

GPU は初期化しない限り触れない。CUDA の実行時の版と cuDNN・NCCL の版は torch が持つ値を読む。
学習のプロセスが実際に読んだ値（TF32・決定性・autocast）は各 run の記録から別に取る。

    <venv>/bin/python tasks/T-2026-11-02-hostdiff-andrew/tools/env_capture.py
"""
from __future__ import annotations

import importlib.metadata as md
import json
import os
import subprocess
import sys


def version(name):
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def main():
    import torch
    import torchvision
    from PIL import Image, features

    smi = subprocess.run(["nvidia-smi", "--query-gpu=index,name,driver_version,power.limit,"
                          "power.default_limit,clocks.max.sm,clocks.max.mem,pcie.link.gen.max,"
                          "pcie.link.width.max", "--format=csv,noheader"],
                         capture_output=True, text=True, check=True).stdout.strip().splitlines()
    out = {
        "python": sys.executable, "python_version": sys.version.split()[0],
        "torch": torch.__version__, "torch_cuda_runtime": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "nccl": ".".join(map(str, torch.cuda.nccl.version())),
        "torchvision": torchvision.__version__,
        "accelerate": version("accelerate"),
        "pillow": version("pillow"), "pillow_simd": version("pillow-simd"),
        "image_decoder": {"pil_jpeg": features.check("jpg"),
                          "libjpeg_turbo": features.check_feature("libjpeg_turbo"),
                          "libjpeg_version": features.version("jpg"),
                          "torchvision_image_backend": torchvision.get_image_backend(),
                          "decode_path": "PIL.Image.open(...).convert('RGB')"},
        "tf32_default_in_fresh_process": {"matmul": torch.backends.cuda.matmul.allow_tf32,
                                          "cudnn": torch.backends.cudnn.allow_tf32},
        "nvidia_smi": smi,
        "env": {k: os.environ.get(k) for k in ("NCCL_P2P_DISABLE", "CUDA_HOME", "CUBLAS_WORKSPACE_CONFIG")},
        "pil_open": Image.__name__,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
