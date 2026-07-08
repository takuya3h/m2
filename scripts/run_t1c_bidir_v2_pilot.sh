#!/usr/bin/env bash
# ============================================================================
# ③ 双方向 §4.6 パイロット v2（非対称・高品質S4事後 / 1-seed=42）
#   A' = v2 bidir      : phase→det=収束済S4事後注入 + det→phase=online phase head（可塑）  GPU0
#   C  = plastic-phase : det→phase(可塑検出器+phase head) のみ, phase→det off（可塑性単独の寄与） GPU1
# 判定: phase→det Δ = det_mAP(A') − ① camt-all inj 0.7181（S4注入・det→phase off）
#       det→phase Δ = phase_acc(A') − B frozen baseline 0.3690（v1 pilot）; C で可塑性 vs 注入の寄与分離
# 恒等ガード: A' は init det mAP=0.7303 assert（camt zero-init 恒等・S4注入でも warm-start は寄与0）。
# ============================================================================
set -euo pipefail
SEED="${SEED:-42}"; EPOCHS="${EPOCHS:-6}"; INIT_MAP=0.7302938995; TOL=0.02
GPU_A="${GPU_A:-0}"; GPU_C="${GPU_C:-1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"; mkdir -p logs
VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV 無い"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い"; exit 1; }
[ -f "$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${SEED}/best_ap.pth" ] || { echo "[ERR] ckpt 無し"; exit 1; }
[ -f "$ROOT/data/processed/phase_context/relation_detr_seed42/train_phasectx.npz" ] || { echo "[ERR] S4 事後 npz 無し"; exit 1; }

echo "============ T1c 双方向 pilot v2 (seed$SEED, epochs=$EPOCHS) ============"
echo " A'=v2-bidir(S4注入)→GPU$GPU_A  C=plastic-phase(phase→det off)→GPU$GPU_C"
echo "======================================================================"

# A': v2 非対称双方向（phase→det=S4事後注入 + det→phase online）
CUDA_VISIBLE_DEVICES="$GPU_A" T1C_WORK_DIR="/tmp/t1c_v2_A_seed${SEED}" \
  "$VENV" scripts/train_t1c_bidir.py --seed "$SEED" --epochs "$EPOCHS" --bidir --phase2det-source s4 --trainable all \
    --assert-init-map "$INIT_MAP" --assert-init-tol "$TOL" \
    > "logs/t1c_v2_A_seed${SEED}.log" 2>&1 &
pid_a=$!

# C: 可塑検出器 + phase head（phase→det off・det→phase の可塑性単独寄与）
CUDA_VISIBLE_DEVICES="$GPU_C" T1C_WORK_DIR="/tmp/t1c_v2_C_seed${SEED}" \
  "$VENV" scripts/train_t1c_bidir.py --seed "$SEED" --epochs "$EPOCHS" --lambda-phase 1.0 --trainable all \
    > "logs/t1c_v2_C_seed${SEED}.log" 2>&1 &
pid_c=$!

wait "$pid_a"; wait "$pid_c"
echo "[本走] A'/C 完了"
dst="transfer/t1c_bidir_v2_pilot_seed${SEED}"; mkdir -p "$dst"
cp -f "/tmp/t1c_v2_A_seed${SEED}/t1c_result.json" "$dst/bidir_s4_result.json"     2>/dev/null || echo "[WARN] A' result 欠損"
cp -f "/tmp/t1c_v2_C_seed${SEED}/t1c_result.json" "$dst/plasticphase_result.json" 2>/dev/null || echo "[WARN] C result 欠損"
cp -f "logs/t1c_v2_A_seed${SEED}.log" "$dst/" 2>/dev/null || true
cp -f "logs/t1c_v2_C_seed${SEED}.log" "$dst/" 2>/dev/null || true

echo "================ 完了・回収サマリ ================"
for tag in bidir_s4 plasticphase; do
  f="$dst/${tag}_result.json"
  [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  $tag: init det={r['init_det_mAP']:.4f} -> final det={r['final_det_mAP']:.4f} phase={r['final_phase_acc']:.4f}\")"
done
echo "判定: phase→det Δ=det_mAP(bidir_s4)−0.7181 / det→phase Δ=phase_acc(bidir_s4)−0.3690。C は可塑性単独の phase 寄与。"
echo "[ALLDONE] T1c 双方向 pilot v2 (seed$SEED) 完了"
