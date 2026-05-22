#!/usr/bin/env bash
# ============================================================================
# setup_env.sh — egosurgery_multitask の実行環境を別マシンで再現するスクリプト
#
# 前提（docs/environment.md 参照）:
#   - Linux x86_64 / NVIDIA GPU（driver は CUDA 12.x 対応 = 535 系以降を推奨）
#   - CUDA Toolkit 11.8（nvcc 11.8）がシステムに導入済み
#     → mamba-ssm / causal-conv1d のソースビルドが torch cu118 と整合するため必須
#   - uv が導入済み（無ければ: curl -LsSf https://astral.sh/uv/install.sh | sh）
#
# 使い方:
#   bash scripts/setup_env.sh
#
# 設計:
#   1) 特殊 tier（torch cu118 / mmcv prebuilt / mamba ソースビルド）を正しい
#      方法で先に導入する
#   2) 最後に requirements.lock.txt を --no-deps で適用し、全 100 パッケージを
#      検証済みの厳密バージョンへスナップ（途中の近似解決を矯正）する
# ============================================================================
set -euo pipefail

# --- プロジェクトルートへ移動 ------------------------------------------------ #
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
echo "[setup] プロジェクト: $PROJECT_DIR"

UV="${UV:-$(command -v uv || echo "$HOME/.local/bin/uv")}"
CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
PY_VERSION="3.11"

# --- 0. 前提チェック -------------------------------------------------------- #
echo "[setup] === 前提チェック ==="
if [ ! -x "$UV" ] && ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv が見つかりません。導入: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[ERROR] nvidia-smi が見つかりません。NVIDIA driver を導入してください。" >&2
  exit 1
fi
NVCC_VER="$("${CUDA_HOME}/bin/nvcc" --version 2>/dev/null | sed -n 's/.*release \([0-9.]*\).*/\1/p' || echo "none")"
echo "[setup] nvcc: ${NVCC_VER} / driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
if [ "${NVCC_VER}" != "11.8" ] && [ "${SKIP_CUDA_CHECK:-0}" != "1" ]; then
  echo "[ERROR] nvcc が 11.8 ではありません（検出: ${NVCC_VER}）。" >&2
  echo "        mamba-ssm / causal-conv1d のソースビルドは torch cu118 と" >&2
  echo "        一致する CUDA 11.8 Toolkit が必要です。CUDA 11.8 を導入するか、" >&2
  echo "        mamba 系を諦める場合は SKIP_CUDA_CHECK=1 で続行できます。" >&2
  exit 1
fi

# --- 1. 仮想環境 ------------------------------------------------------------ #
echo "[setup] === 1. uv 仮想環境（.venv, Python ${PY_VERSION}）==="
"$UV" venv .venv --python "$PY_VERSION"

# --- 2. torch / torchvision（cu118 専用 index）------------------------------ #
echo "[setup] === 2. torch 2.1.2 + torchvision 0.16.2 (cu118) ==="
"$UV" pip install --python .venv/bin/python \
  torch==2.1.2 torchvision==0.16.2 \
  --index-url https://download.pytorch.org/whl/cu118

# --- 3. mmcv / mmdet（cu118/torch2.1 prebuilt wheel）----------------------- #
echo "[setup] === 3. mmcv 2.1.0 + mmdet 3.3.0 ==="
"$UV" pip install --python .venv/bin/python mmcv==2.1.0 \
  --find-links https://download.openmmlab.com/mmcv/dist/cu118/torch2.1/index.html
"$UV" pip install --python .venv/bin/python mmdet==3.3.0

# --- 4. ビルドツール（setuptools<80 は pkg_resources のため必須）------------ #
echo "[setup] === 4. ビルドツール ==="
"$UV" pip install --python .venv/bin/python "setuptools<80" ninja packaging wheel

# --- 5. mamba-ssm / causal-conv1d（CUDA 拡張をソースビルド）----------------- #
echo "[setup] === 5. causal-conv1d 1.4.0 + mamba-ssm 2.2.2（ソースビルド）==="
CUDA_HOME="$CUDA_HOME" MAX_JOBS="${MAX_JOBS:-8}" \
  "$UV" pip install --python .venv/bin/python --no-build-isolation \
  causal-conv1d==1.4.0 mamba-ssm==2.2.2

# --- 6. 全依存をロックファイルの厳密版へスナップ ---------------------------- #
echo "[setup] === 6. requirements.lock.txt で全 100 パッケージを厳密固定 ==="
"$UV" pip install --python .venv/bin/python --no-deps -r requirements.lock.txt

# --- 7. プロジェクト本体を editable install -------------------------------- #
echo "[setup] === 7. egosurgery を editable install ==="
"$UV" pip install --python .venv/bin/python --no-deps -e .

# --- 8. 検証 ---------------------------------------------------------------- #
echo "[setup] === 8. 検証 ==="
.venv/bin/python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA が利用不可"
x = torch.randn(256, 256, device="cuda")
_ = (x @ x).sum().item()
import torchvision, mmcv, mmdet, mmengine, mamba_ssm, causal_conv1d  # noqa: F401
import hydra, omegaconf, wandb, timm, peft, albumentations, pycocotools  # noqa: F401
import egosurgery  # noqa: F401
print(f"  torch {torch.__version__} / CUDA {torch.version.cuda} / GPU {torch.cuda.get_device_name(0)}")
print(f"  mmcv {mmcv.__version__} / mmdet {mmdet.__version__} / mamba-ssm {mamba_ssm.__version__}")
print("  全 import OK・CUDA 動作 OK・egosurgery 解決 OK")
PY

echo ""
echo "[setup] 完了。'source .venv/bin/activate' で有効化できます。"
echo "[setup] テスト: .venv/bin/python -m pytest tests/ -q"
