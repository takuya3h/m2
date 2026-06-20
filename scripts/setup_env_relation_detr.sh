#!/usr/bin/env bash
# ============================================================================
# setup_env_relation_detr.sh — 検出器(Relation-DETR)側 venv を別マシンで再現する
#
# 本体 .venv（setup_env.sh）とは別に、Relation-DETR の推論・抽出に使う
# `.venv-relation-detr` を構築する。これは ①系統の検出器 forward が必要な工程:
#   - S0-frozen 検出推論 / Stage1 GAP 抽出（extract_stage1_features.py）
#   - B2a tool-presence 抽出（extract_b2a_detsignal.py）
#   - T1a region-token 抽出（extract_t1a_regiontoken.py）
#   - B1 統合トレーナー（train_b1_mtl.py, egosurgery 非 import）
# で使う。MS-Deform-Attn は実行時 JIT ビルド（ninja 同梱・CUDA_HOME=11.8 が必要）。
#
# 前提（docs/environment.md / reproduce_on_new_machine.md 参照）:
#   - CUDA Toolkit 11.8（nvcc 11.8）導入済み。MS-Deform-Attn の JIT ビルドが
#     torch cu118 と整合するため必須。CUDA_HOME でそれを指す。
#   - uv 導入済み。third_party/Relation-DETR がチェックアウト済み。
#
# 使い方:
#   bash scripts/setup_env_relation_detr.sh
#   （CUDA_HOME を明示する場合: CUDA_HOME=/usr/local/cuda-11.8 bash scripts/setup_env_relation_detr.sh）
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
echo "[setup-reldetr] プロジェクト: $PROJECT_DIR"

UV="${UV:-$(command -v uv || echo "$HOME/.local/bin/uv")}"
CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
PY_VERSION="3.11"
VENV=".venv-relation-detr"
CU118_INDEX="https://download.pytorch.org/whl/cu118"
LOCK="requirements.relation_detr.lock.txt"

# --- 0. 前提チェック -------------------------------------------------------- #
echo "[setup-reldetr] === 前提チェック ==="
if [ ! -x "$UV" ] && ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv が見つかりません。導入: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[ERROR] nvidia-smi が見つかりません。NVIDIA driver を導入してください。" >&2
  exit 1
fi
NVCC_VER="$("${CUDA_HOME}/bin/nvcc" --version 2>/dev/null | sed -n 's/.*release \([0-9.]*\).*/\1/p' || echo "none")"
echo "[setup-reldetr] nvcc(${CUDA_HOME}): ${NVCC_VER} / driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
if [ "${NVCC_VER}" != "11.8" ] && [ "${SKIP_CUDA_CHECK:-0}" != "1" ]; then
  echo "[ERROR] nvcc が 11.8 ではありません（検出: ${NVCC_VER}）。" >&2
  echo "        MS-Deform-Attn の JIT ビルドは torch cu118 と一致する CUDA 11.8 が必要です。" >&2
  echo "        CUDA 11.8 を導入し CUDA_HOME で指すか、SKIP_CUDA_CHECK=1 で続行（自己責任）。" >&2
  exit 1
fi
if [ ! -f "$LOCK" ]; then
  echo "[ERROR] $LOCK が見つかりません（正本 lock 欠落）。" >&2; exit 1
fi
if [ ! -d "third_party/Relation-DETR" ]; then
  echo "[ERROR] third_party/Relation-DETR が見当たりません（submodule/checkout を確認）。" >&2; exit 1
fi

# --- 1. 仮想環境 ------------------------------------------------------------ #
echo "[setup-reldetr] === 1. uv 仮想環境（${VENV}, Python ${PY_VERSION}）==="
"$UV" venv "$VENV" --python "$PY_VERSION"

# --- 2. torch / torchvision（cu118 専用 index を先行）----------------------- #
echo "[setup-reldetr] === 2. torch 2.1.2 + torchvision 0.16.2 (cu118) ==="
"$UV" pip install --python "$VENV/bin/python" \
  torch==2.1.2 torchvision==0.16.2 --index-url "$CU118_INDEX"

# --- 3. lock の厳密版を適用（torch は導入済 → +cu118 解決に extra index を併用）- #
echo "[setup-reldetr] === 3. ${LOCK} で全 72 パッケージを厳密固定 ==="
"$UV" pip install --python "$VENV/bin/python" --no-deps \
  --extra-index-url "$CU118_INDEX" -r "$LOCK"

# --- 4. 検証 ---------------------------------------------------------------- #
echo "[setup-reldetr] === 4. 検証 ==="
"$VENV/bin/python" - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA が利用不可"
x = torch.randn(256, 256, device="cuda")
_ = (x @ x).sum().item()
import torchvision, accelerate, omegaconf, albumentations, pycocotools, ninja  # noqa: F401
print(f"  torch {torch.__version__} / CUDA {torch.version.cuda} / GPU {torch.cuda.get_device_name(0)}")
print(f"  torchvision {torchvision.__version__} / accelerate {accelerate.__version__}")
print("  import OK・CUDA 動作 OK（MS-Deform-Attn は初回 detector forward で JIT ビルドされる）")
PY

echo ""
echo "[setup-reldetr] 完了。検出器側スクリプトは次のように使う:"
echo "  source ${VENV}/bin/activate    # ninja を PATH に載せ MS-Deform-Attn を JIT ビルド可能に"
echo "  export CUDA_HOME=${CUDA_HOME}"
echo "  CUDA_VISIBLE_DEVICES=0 python scripts/extract_t1a_regiontoken.py --subset val --limit 8  # 疎通"
