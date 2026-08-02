#!/usr/bin/env bash
# N2: TF32 仮説の検証 — 数値精度設定を変えて region-token を再抽出する。
#
# scripts/extract_t1a_regiontoken.py は **改変しない**。
# TF32 フラグはラッパー (runpy) 経由で注入し、出力先は RELDETR_FROZEN_TAG で切り替える。
# 既存キャッシュは上書きしない（一時タグに出力してから $OUT/reextract へ移動）。
#
# ★ MSDeformAttn 拡張について (2026-07-29 に判明した最重要の注意点):
#   models/bricks/ms_deform_attn.py は import 時に torch.utils.cpp_extension.load() で
#   CUDA 拡張を JIT ロードする。これには **ninja が PATH 上にある**ことが必要で、
#   ninja は .venv-relation-detr/bin にのみ存在する。
#   したがって venv を activate せず `.venv-relation-detr/bin/python` を直接呼ぶと
#   ninja が見つからず拡張のロードに失敗し、**PyTorch フォールバック実装**に落ちる。
#   フォールバックは CUDA カーネルと数値が異なり、region-token が bit-exact に再現しない。
#
#   EXT_MODE=cuda     (既定) venv/bin を PATH に載せて CUDA 拡張を使う  ← 正しい手順
#   EXT_MODE=fallback PATH に載せず、意図的にフォールバックで走らせる（対照実験用）
#
# Usage:
#   bash scripts/analysis/reextract_precision_sweep.sh <OUT_DIR> [subset]
#     OUT_DIR : 出力先 (例 experiments/analysis/repro_variance_2026-07-29)
#     subset  : 既定 val
#   EXT_MODE=fallback bash scripts/analysis/reextract_precision_sweep.sh ...
set -euo pipefail

OUT="${1:?OUT_DIR を指定してください}"
SUBSET="${2:-val}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

VENV="$REPO/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い (誤生成された .venv は使わない)"; exit 1; }

EXT_MODE="${EXT_MODE:-cuda}"
if [ "$EXT_MODE" = "cuda" ]; then
  # runsheet と同じ状態にする (activate 相当)。ninja が PATH に載り CUDA 拡張がロードされる。
  export PATH="$REPO/.venv-relation-detr/bin:$PATH"
fi
command -v ninja >/dev/null 2>&1 && NINJA_ON_PATH=1 || NINJA_ON_PATH=0
echo "[env] EXT_MODE=$EXT_MODE ninja_on_PATH=$NINJA_ON_PATH"

mkdir -p "$OUT/reextract" "$OUT/json"
WRAP="$OUT/reextract/_tf32_wrap.py"

# ラッパー: env で TF32 を設定してから元スクリプトを __main__ として実行する。
# sys.argv を明示的に組み立てて元スクリプトの argparse に渡す。
cat > "$WRAP" <<'EOF'
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
EOF

run_one () {  # $1=id $2=mm $3=cudnn $4=benchmark(optional)
  local id="$1" mm="$2" cud="$3" bench="${4:-}"
  local tag="__prec_${id}"
  echo "=== [$id] matmul_tf32=$mm cudnn_tf32=$cud benchmark=${bench:-default} ==="
  rm -rf "data/processed/t1a_regiontoken/${tag}"
  mkdir -p "data/processed/t1a_regiontoken/${tag}"
  local envs=(MM_TF32="$mm" CUDNN_TF32="$cud"
              TARGET_SCRIPT="scripts/extract_t1a_regiontoken.py"
              TARGET_ARGS="--subset ${SUBSET}"
              RELDETR_FROZEN_TAG="${tag}" CUDA_VISIBLE_DEVICES=0)
  [ -n "$bench" ] && envs+=(CUDNN_BENCHMARK="$bench")
  env "${envs[@]}" "$VENV" "$WRAP" 2>&1 | grep -Ev "UserWarning|torch\.has_|^\s*$" | tail -4
  mv "data/processed/t1a_regiontoken/${tag}/${SUBSET}_regiontoken.npz" \
     "$OUT/reextract/${SUBSET}_${id}.npz"
  rmdir "data/processed/t1a_regiontoken/${tag}"
  echo "  -> $OUT/reextract/${SUBSET}_${id}.npz"
}

# --- N2-2: 2x2 スイープ ------------------------------------------------------
run_one P00 0 0
run_one P01 0 1
run_one P10 1 0
run_one P11 1 1

# --- N2-5: cudnn.benchmark の追加 2 本 (既定 TF32 のまま) ---------------------
if [ "${WITH_BENCHMARK:-0}" = "1" ]; then
  run_one B0 0 1 0
  run_one B1 0 1 1
fi

echo "sweep done -> $OUT/reextract/"
