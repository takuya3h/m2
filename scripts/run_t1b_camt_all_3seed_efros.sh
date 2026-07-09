#!/usr/bin/env bash
# ============================================================================
# T1b-CA-MultiToken（真の query-selective・多トークン Phase→Det CA / §4.6 primary 本命）
# 3seed × inj/ctrl を efros 2GPU で実行する。
#   camt = phase 事後を P 個の phase-prototype token(B,P,embed) に展開し、各 decoder 層の
#   query→phase cross-attention の KV に渡す。各 query が関連 phase token を selective に attend＝
#   真の query-selective（single-token CA の gate 的注意より表現力が高い）。decoder 層は
#   RelationTransformerDecoderLayerPhaseCA を無改造で再利用、phase_attn.out_proj zero-init で
#   warm-start 恒等（S0-frozen）。
#
# 科学的設定は T1b-CA(single-token)・clsbias と完全一致: trainable=film / epochs=6 / lr=1e-4 /
# film_lr=5e-4 / tol=0.02。唯一の差は inject=camt。film ゆえ検出器凍結・注入層(phase_*)のみ学習で
# 「注入の正味効果」を清潔に測る（FiLM 下限・single-token CA との同一プロトコル比較）。
#
# 対照 (ctrl) = --zero-ctx（phase context=0 → token=0 → 注入寄与 0）。
#
# 使い方: bash scripts/run_t1b_camt_3seed_efros.sh
#   GPU 割当変更: GPU_INJ=0 GPU_CTRL=1 bash scripts/run_t1b_camt_3seed_efros.sh
# ============================================================================
set -euo pipefail

INJECT=camt
TRAINABLE=all
EPOCHS=6
ASSERT_INIT_TOL=0.02
INIT_LO=0.65
INIT_HI=0.78
SEEDS=(42 123 456)
GPU_INJ="${GPU_INJ:-0}"
GPU_CTRL="${GPU_CTRL:-1}"
TAG="${TAG:-camt_all}"   # env で上書き可（例: TAG=camt_all_reverify で committed evidence を保護しつつ再走）

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い。scripts/setup_env.sh で .venv-relation-detr を構築せよ"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い（$ROOT/.venv-relation-detr/bin/ninja を確認）"; exit 1; }

for S in "${SEEDS[@]}"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done

echo "================ T1b-CA-MultiToken-ALL($TAG) 3seed（efros）================"
echo " inject=$INJECT trainable=$TRAINABLE epochs=$EPOCHS tol=$ASSERT_INIT_TOL"
echo " seeds=${SEEDS[*]}  割当: inj→GPU$GPU_INJ  ctrl→GPU$GPU_CTRL"
echo " 健全帯: init mAP ∈ [$INIT_LO, $INIT_HI]（外れたら中断）"
echo "====================================================================="

run_one() {
  local seed="$1" gpu="$2" work="$3" log="$4"; shift 4
  CUDA_VISIBLE_DEVICES="$gpu" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$seed" --inject "$INJECT" --trainable "$TRAINABLE" \
      "$@" \
      > "$log" 2>&1
}

extract_init_map() {
  "$VENV" - "$1" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
v = r.get("init_mAP")
assert isinstance(v, (int, float)), f"init_mAP 不正: {v!r}"
print(f"{v:.10f}")
PY
}

echo "[warmup] MultiScaleDeformableAttention CUDA 拡張を事前ビルド中 ..."
CUDA_VISIBLE_DEVICES="$GPU_INJ" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] MSDeformAttn ext ready')" \
  || { echo '[ERR] MSDeformAttn 拡張の事前ビルドに失敗'; exit 1; }

for S in "${SEEDS[@]}"; do
  echo ""
  echo "############### seed$S ###############"
  MEAS=/tmp/t1b_${TAG}_measure_seed${S}
  echo "[measure seed$S] init mAP を実測（--epochs 0, GPU$GPU_INJ）..."
  run_one "$S" "$GPU_INJ" "$MEAS" "logs/t1b_${TAG}_measure_seed${S}.log" --epochs 0
  INIT="$(extract_init_map "$MEAS/t1b_result.json")"
  echo "[measure seed$S] init mAP=$INIT"
  "$VENV" - "$INIT" "$INIT_LO" "$INIT_HI" "$S" <<'PY'
import sys
v, lo, hi = map(float, sys.argv[1:4]); s = sys.argv[4]
if not (lo <= v <= hi):
    print(f"[PREFLIGHT-FAIL] seed{s} init mAP={v:.4f} が健全帯[{lo},{hi}]外 → ckpt 取り違え/恒等破れ。中断。")
    sys.exit(3)
print(f"[measure seed{s}] 健全帯チェック OK")
PY

  INJ=/tmp/t1b_${TAG}_seed${S}
  CTRL=/tmp/t1b_${TAG}_zeroctx_seed${S}
  echo "[seed$S 本走] inj(GPU$GPU_INJ) ∥ ctrl(GPU$GPU_CTRL) 並列起動（epochs=$EPOCHS）..."
  run_one "$S" "$GPU_INJ" "$INJ" "logs/t1b_${TAG}_seed${S}.log" \
    --epochs "$EPOCHS" --assert-init-map "$INIT" --assert-init-tol "$ASSERT_INIT_TOL" &
  pid_inj=$!
  run_one "$S" "$GPU_CTRL" "$CTRL" "logs/t1b_${TAG}_zeroctx_seed${S}.log" \
    --epochs "$EPOCHS" --assert-init-map "$INIT" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
  pid_ctrl=$!
  wait "$pid_inj"; wait "$pid_ctrl"
  echo "[seed$S 本走] 完了"

  dst="transfer/t1b_${TAG}_seed${S}_efros"
  mkdir -p "$dst"
  cp -f "$INJ/t1b_result.json"  "$dst/injected_result.json" 2>/dev/null || echo "[WARN] inj result 欠損 seed$S"
  cp -f "$CTRL/t1b_result.json" "$dst/control_result.json"  2>/dev/null || echo "[WARN] ctrl result 欠損 seed$S"
  cp -f "logs/t1b_${TAG}_seed${S}.log"         "$dst/" 2>/dev/null || true
  cp -f "logs/t1b_${TAG}_zeroctx_seed${S}.log" "$dst/" 2>/dev/null || true
done

echo ""
echo "================ 完了・回収サマリ ================"
for S in "${SEEDS[@]}"; do
  dst="transfer/t1b_${TAG}_seed${S}_efros"
  echo "-- seed$S --"
  for f in "$dst/injected_result.json" "$dst/control_result.json"; do
    [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  {('inj' if not r['zero_ctx'] else 'ctrl')}: init={r['init_mAP']:.4f} best@ep{r['best_epoch']} mAP={r['mAP']:.4f} final@ep{r.get('final_epoch')}={r.get('final_mAP',0):.4f}\")"
  done
done
echo "次: scripts/analyze_t1b_clsbias.py --tag ${TAG} --which final で per-class AP を 3-seed paired-σ 判定。"
echo "[ALLDONE] T1b-CA-MultiToken(${TAG}) 3seed 完了"
