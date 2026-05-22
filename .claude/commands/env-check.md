---
description: torch/CUDA・mm系・mamba・主要依存の import 健全性を一括確認する
---

`.venv` 環境の健全性を一括チェックします。

手順:

1. `.venv/bin/python` で以下を確認し、表で報告する:
   - `torch` のバージョン・`torch.version.cuda`・`torch.cuda.is_available()`、
     可能なら GPU 上で小さな行列積を実行して実動作を確認
   - `torchvision`
   - `mmcv` / `mmdet` / `mmengine`
   - `mamba_ssm` / `causal_conv1d`（`Mamba` ブロックの GPU forward まで）
   - `hydra` / `omegaconf` / `wandb` / `timm` / `peft` / `transformers`
   - `albumentations` / `cv2` / `pycocotools` / `numpy`
2. import 失敗・CUDA 不可があれば、原因（バージョン不整合・ドライバ等）を切り分けて報告。
3. `nvidia-smi` で GPU の空き状況も確認する。
4. CLAUDE.md の「検証済み構成」と乖離があれば指摘する。問題なければ「環境健全」と報告。
