#!/usr/bin/env bash
# ============================================================================
# ③ 双方向 §4.6 パイロット（1-seed=42・frame 粒度・2-pass teacher-forced）
#   A = bidir       : 両方向 on（det→phase + phase→det online 注入, trainable=all 可塑）  GPU0
#   B = phase-frozen : det→phase off baseline（phase head を凍結検出器上で学習, inject off） GPU1
# 判定: det→phase Δ = phase_acc(A) − phase_acc(B) ; phase→det Δ = det_mAP(A) − ① camt-all ctrl(0.7110)
# 恒等ガード: A は warm-start init det mAP を S0-frozen 0.7303 に assert（camt zero-init 恒等）。
# ============================================================================
set -euo pipefail
SEED="${SEED:-42}"
EPOCHS="${EPOCHS:-6}"
INIT_MAP=0.7302938995
TOL=0.02
GPU_A="${GPU_A:-0}"
GPU_B="${GPU_B:-1}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"; mkdir -p logs
VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い"; exit 1; }
CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${SEED}/best_ap.pth"
[ -f "$CK" ] || { echo "[ERR] warm-start ckpt 無し: $CK"; exit 1; }

echo "================ T1c 双方向 pilot (seed$SEED, epochs=$EPOCHS) ================"
echo " A=bidir→GPU$GPU_A  B=phase-frozen→GPU$GPU_B"
echo "==============================================================="

# A: bidir（両方向 on・可塑）— 恒等ガード付き
CUDA_VISIBLE_DEVICES="$GPU_A" T1C_WORK_DIR="$ROOT/experiments/transfer/t1c_bidir_A_seed${SEED}" \
  "$VENV" scripts/train_t1c_bidir.py --seed "$SEED" --epochs "$EPOCHS" --bidir --trainable all \
    --assert-init-map "$INIT_MAP" --assert-init-tol "$TOL" \
    > "logs/t1c_bidir_A_seed${SEED}.log" 2>&1 &
pid_a=$!

# B: phase-frozen baseline（det→phase off: 凍結検出器 + phase head のみ学習・inject off）
CUDA_VISIBLE_DEVICES="$GPU_B" T1C_WORK_DIR="$ROOT/experiments/transfer/t1c_bidir_B_seed${SEED}" \
  "$VENV" scripts/train_t1c_bidir.py --seed "$SEED" --epochs "$EPOCHS" --lambda-phase 1.0 --trainable film \
    > "logs/t1c_bidir_B_seed${SEED}.log" 2>&1 &
pid_b=$!

wait "$pid_a"; wait "$pid_b"
echo "[本走] A/B 完了"

dst="transfer/t1c_bidir_pilot_seed${SEED}"
mkdir -p "$dst"
cp -f "$ROOT/experiments/transfer/t1c_bidir_A_seed${SEED}/t1c_result.json" "$dst/bidir_result.json"       2>/dev/null || echo "[WARN] A result 欠損"
cp -f "$ROOT/experiments/transfer/t1c_bidir_B_seed${SEED}/t1c_result.json" "$dst/phasefrozen_result.json" 2>/dev/null || echo "[WARN] B result 欠損"
cp -f "logs/t1c_bidir_A_seed${SEED}.log" "$dst/" 2>/dev/null || true
cp -f "logs/t1c_bidir_B_seed${SEED}.log" "$dst/" 2>/dev/null || true

echo "================ 完了・回収サマリ ================"
for tag in bidir phasefrozen; do
  f="$dst/${tag}_result.json"
  [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  $tag: init det={r['init_det_mAP']:.4f} phase={r['init_phase_acc']:.4f} -> final det={r['final_det_mAP']:.4f} phase={r['final_phase_acc']:.4f}\")"
done
echo "次: scripts/analyze で det→phase Δ=acc(bidir)−acc(phasefrozen) / phase→det Δ=det_mAP(bidir)−① camt-all ctrl 0.7110 を判定。"
echo "[ALLDONE] T1c 双方向 pilot (seed$SEED) 完了"
