"""仮想環境の中から torch の版と CUDA・cuDNN・NCCL の版を読み、MS-Deform-Attn のビルド物を読み込めるかを試す
（T-2026-11-02-bengio-andrew-env-survey、Task C-5・C-6）。

読むだけ。CUDA の装置を見せない形（呼び出し側が CUDA_VISIBLE_DEVICES="" を置く）で、``python -B -I -`` に標準入力で渡す。
ビルド物は ``torch.utils.cpp_extension.load`` を呼ばず（呼ぶとビルドし直しうる）、拡張の .so を直接読み込む。
"""
import glob
import hashlib
import json
import os
import sys

res = {"executable": sys.executable, "version": sys.version.split()[0],
       "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES")}
try:
    import torch
    res["torch"] = torch.__version__
    res["torch_cuda"] = torch.version.cuda
    res["cudnn"] = torch.backends.cudnn.version()
    try:
        res["nccl"] = ".".join(map(str, torch.cuda.nccl.version())) if isinstance(torch.cuda.nccl.version(), tuple) else torch.cuda.nccl.version()
    except Exception as e:  # noqa: BLE001
        res["nccl"] = f"UNKNOWN ({type(e).__name__}: {e})"
    res["cuda_is_available"] = torch.cuda.is_available()
    res["device_count"] = torch.cuda.device_count()
    res["cuda_initialized"] = torch.cuda.is_initialized()
except Exception as e:  # noqa: BLE001
    res["torch"] = f"UNKNOWN ({type(e).__name__}: {e})"
try:
    import torchvision
    res["torchvision"] = torchvision.__version__
except Exception as e:  # noqa: BLE001
    res["torchvision"] = f"UNKNOWN ({type(e).__name__}: {e})"

ext = {}
for so in sorted(glob.glob(os.path.expanduser("~/.cache/torch_extensions/*/MultiScaleDeformableAttention/*"))):
    if os.path.isfile(so):
        h = hashlib.sha256(open(so, "rb").read()).hexdigest()
        st = os.stat(so)
        ext[so] = {"bytes": st.st_size, "sha256": h, "mtime": int(st.st_mtime)}
res["ext_files"] = ext
sos = [p for p in ext if p.endswith("MultiScaleDeformableAttention.so")]
if "--load" in sys.argv and sos and "torch" in sys.modules:
    import importlib.machinery
    import importlib.util
    try:
        loader = importlib.machinery.ExtensionFileLoader("MultiScaleDeformableAttention", sos[0])
        spec = importlib.util.spec_from_file_location("MultiScaleDeformableAttention", sos[0], loader=loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        res["ext_load"] = {"ok": True, "attrs": sorted(a for a in dir(mod) if not a.startswith("_"))}
    except Exception as e:  # noqa: BLE001
        res["ext_load"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    res["cuda_initialized_after_load"] = torch.cuda.is_initialized()
print(json.dumps(res, ensure_ascii=False, indent=1))
