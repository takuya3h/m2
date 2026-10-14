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
# で使う。MS-Deform-Attn は JIT ビルド（ninja 同梱）で、本スクリプトの末尾で
# ビルドとロードまで検証する。
#
# 前提（docs/environment.md / reproduce_on_new_machine.md 参照）:
#   - CUDA Toolkit（nvcc）導入済み。**12.x（現行サーバーの 12.9）でも 11.8 でもよい。**
#     torch は cu118 のままだが、nvcc 12.9 + gcc 13 でビルドした拡張が凍結源の出力を
#     bit 一致で再現する（2026-08-29 lecun / 2026-10-13 andrew 実測）。
#     既定は /usr/local/cuda。別の場所なら CUDA_HOME で指す。
#   - 拡張は実行時に $CUDA_HOME/lib64 の libcudart を要る（LD_LIBRARY_PATH に載っていること）。
#   - uv 導入済み。third_party/Relation-DETR のソースが展開済み
#     （無ければ: bash scripts/restore_relation_detr_source.sh）。
#
# 使い方:
#   bash scripts/setup_env_relation_detr.sh
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
case "${NVCC_VER}" in
  11.8|12.*) ;;
  *)
    if [ "${SKIP_CUDA_CHECK:-0}" != "1" ]; then
      echo "[ERROR] nvcc が 11.8 でも 12.x でもありません（検出: ${NVCC_VER}）。" >&2
      echo "        MS-Deform-Attn の JIT ビルドを実測で確かめたのは 11.8 と 12.9 だけです。" >&2
      echo "        CUDA_HOME で nvcc の場所を指すか、SKIP_CUDA_CHECK=1 で続行（自己責任）。" >&2
      exit 1
    fi ;;
esac
if [ ! -f "$LOCK" ]; then
  echo "[ERROR] $LOCK が見つかりません（正本 lock 欠落）。" >&2; exit 1
fi
# checkpoints だけが置かれたホストがあるため、ディレクトリではなくソースの実在で見る。
if [ ! -f "third_party/Relation-DETR/main.py" ]; then
  echo "[ERROR] third_party/Relation-DETR にソースがありません（main.py が無い）。" >&2
  echo "        復元: bash scripts/restore_relation_detr_source.sh" >&2
  exit 1
fi

# --- 1. 仮想環境 ------------------------------------------------------------ #
echo "[setup-reldetr] === 1. uv 仮想環境（${VENV}, Python ${PY_VERSION}）==="
"$UV" venv "$VENV" --python "$PY_VERSION"

# --- 2. torch / torchvision（cu118 専用 index を先行）----------------------- #
echo "[setup-reldetr] === 2. torch 2.1.2 + torchvision 0.16.2 (cu118) ==="
"$UV" pip install --python "$VENV/bin/python" \
  torch==2.1.2 torchvision==0.16.2 --index-url "$CU118_INDEX"

# --- 3. lock の厳密版を適用（torch は導入済 → +cu118 解決に extra index を併用）- #
# index-strategy unsafe-best-match: +cu118 パッケージは PyTorch index、その他（iopath 等）は
# PyPI と、全 index を横断して最適版を解決する（uv 既定は first-index-only で iopath==0.1.10 を
# cu118 index に見つけられず失敗するため）。--no-deps ゆえ版は lock で厳密固定され confusion リスク無し。
echo "[setup-reldetr] === 3. ${LOCK} で全 72 パッケージを厳密固定 ==="
"$UV" pip install --python "$VENV/bin/python" --no-deps \
  --extra-index-url "$CU118_INDEX" --index-strategy unsafe-best-match -r "$LOCK"

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
print("  import OK・CUDA 動作 OK")
PY

# --- 5. MS-Deform-Attn の JIT ビルドとロード -------------------------------- #
# 上流は失敗を warning に落として _C=None で先へ進むため、ここで止めないと
# 初回の detector forward まで気づけない。ninja は venv の bin から取る。
echo "[setup-reldetr] === 5. MS-Deform-Attn の JIT ビルド（nvcc ${NVCC_VER}）==="
JIT_LOG="$(mktemp)"   # コンパイラの警告が数百行出るため、失敗時だけ末尾を見せる
if (
  cd third_party/Relation-DETR
  PATH="$PROJECT_DIR/$VENV/bin:$PATH" CUDA_HOME="$CUDA_HOME" \
    "$PROJECT_DIR/$VENV/bin/python" - <<'PY'
import warnings
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    from models.bricks import ms_deform_attn
reasons = [str(w.message) for w in caught if "MultiScaleDeformableAttention" in str(w.message)]
assert ms_deform_attn._C is not None, "MS-Deform-Attn のビルド/ロードに失敗: " + " / ".join(reasons)
print("  MS-Deform-Attn ビルド OK・ロード OK")
PY
) >"$JIT_LOG" 2>&1; then
  tail -n 1 "$JIT_LOG"
else
  tail -n 20 "$JIT_LOG" >&2
  echo "[ERROR] MS-Deform-Attn を用意できませんでした（全文: $JIT_LOG）。" >&2
  echo "        LD_LIBRARY_PATH に ${CUDA_HOME}/lib64 が載っているかを確認してください。" >&2
  exit 1
fi

echo ""
echo "[setup-reldetr] 完了。検出器側スクリプトは次のように使う:"
echo "  source ${VENV}/bin/activate    # ninja を PATH に載せる（拡張の再ビルド判定に要る）"
echo "  export CUDA_HOME=${CUDA_HOME}   # 構築時と同じ場所を指す（変えると再ビルドになる）"
echo "  CUDA_VISIBLE_DEVICES=0 python scripts/extract_t1a_regiontoken.py --subset val --limit 8  # 疎通"
