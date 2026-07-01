#!/usr/bin/env bash
# ============================================================================
# §18.4 L1-2 oracle-phase（★最重要・negative result 防御）
# 3-seed × inj/ctrl を lecun 2GPU wave-by-wave で実行。T1b-CA と完全同条件、
# 唯一の差は **phase-source=oracle**（S4 TeCNO 予測 → phase_manifest GT one-hot）。
#
# 仮説:
#   - oracle-phase でも overall mAP が改善しない → phase→det 機構非依存性が**最終確定**
#     （phase 推定誤差ではなく phase 情報そのものが det に貢献しないことを実証）
#   - oracle-phase で改善する → phase 推定誤差が真因（推定改善方向の研究余地）
#
# 設定:
#   inject=ca, trainable=film, epochs=6, lr=1e-4, film_lr=5e-4, tol=0.02
#   phase-source=oracle（GT one-hot）
#   warm-start: 各 seed 専用 ckpt（既存と同じ）
#
# 6 run × 約 4h、2 GPU 並列で約 12h 完走。
# ============================================================================
set -euo pipefail

INJECT=ca
TRAINABLE=film
EPOCHS=6
ASSERT_INIT_TOL=0.02
INIT_LO=0.65
INIT_HI=0.78
PHASE_SRC=oracle

SEEDS=(42 123 456)
GPU_A="${GPU_A:-0}"
GPU_B="${GPU_B:-1}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

for S in "${SEEDS[@]}"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done

echo "================ §18.4 L1-2 oracle-phase 3-seed × inj/ctrl ================"
echo " inject=$INJECT trainable=$TRAINABLE epochs=$EPOCHS phase_source=$PHASE_SRC"
echo " 比較: T1b-CA (real phase) の純効果 +0.00178 と paired-σ で比較"
echo " 期待: oracle で改善しなければ → §7.5 撤退ライン最終確定（査読防御完成）"
echo "==========================================================================="

run_one() {
  local seed="$1" gpu="$2" work="$3" log="$4"; shift 4
  CUDA_VISIBLE_DEVICES="$gpu" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$seed" --inject "$INJECT" --trainable "$TRAINABLE" \
      --phase-source "$PHASE_SRC" \
      "$@" \
      > "$log" 2>&1
}

extract_init_map() {
  "$VENV" - "$1" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
v = r.get("init_mAP"); assert isinstance(v, (int, float))
print(f"{v:.10f}")
PY
}

# Step 0: MSDeformAttn CUDA 拡張を warmup
echo "[warmup] MSDeformAttn ext build ..."
CUDA_VISIBLE_DEVICES="$GPU_A" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] OK')" \
  || { echo '[ERR] warmup 失敗'; exit 1; }

# Step 1: measure-only で per-seed init mAP（assert 値固定）
declare -A MEAS_DIR INIT_MAP
for S in "${SEEDS[@]}"; do MEAS_DIR[$S]="/tmp/oracle_phase_measure_seed${S}"; done

echo "[measure wave1] seed42(GPU$GPU_A) + seed123(GPU$GPU_B) 並列 ..."
run_one 42  "$GPU_A" "${MEAS_DIR[42]}"  "logs/oracle_phase_measure_seed42.log"  --epochs 0 &
pa=$!
run_one 123 "$GPU_B" "${MEAS_DIR[123]}" "logs/oracle_phase_measure_seed123.log" --epochs 0 &
pb=$!
wait "$pa"; wait "$pb"
echo "[measure wave2] seed456(GPU$GPU_A) 単独 ..."
run_one 456 "$GPU_A" "${MEAS_DIR[456]}" "logs/oracle_phase_measure_seed456.log" --epochs 0

for S in "${SEEDS[@]}"; do
  INIT_MAP[$S]="$(extract_init_map "${MEAS_DIR[$S]}/t1b_result.json")"
  echo "[measure] seed$S init mAP=${INIT_MAP[$S]}"
done

# 健全帯
"$VENV" - "${INIT_MAP[42]}" "${INIT_MAP[123]}" "${INIT_MAP[456]}" "$INIT_LO" "$INIT_HI" <<'PY'
import sys
a, b, c, lo, hi = map(float, sys.argv[1:6])
bad = [(s, v) for s, v in ((42,a),(123,b),(456,c)) if not (lo <= v <= hi)]
if bad:
    for s, v in bad: print(f"[PREFLIGHT-FAIL] seed{s} init mAP={v:.4f} 健全帯外 → 中断")
    sys.exit(3)
print("[measure] 全 seed 健全帯 OK")
PY

# Step 2: wave A = inj (real ctx = oracle GT)
INJ_DIR_42=/tmp/oracle_phase_inj_seed42
INJ_DIR_123=/tmp/oracle_phase_inj_seed123
INJ_DIR_456=/tmp/oracle_phase_inj_seed456

echo "[wave A:inj wave1] seed42(GPU$GPU_A) + seed123(GPU$GPU_B) 並列 ..."
run_one 42  "$GPU_A" "$INJ_DIR_42"  "logs/oracle_phase_inj_seed42.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[42]}" --assert-init-tol "$ASSERT_INIT_TOL" &
pa=$!
run_one 123 "$GPU_B" "$INJ_DIR_123" "logs/oracle_phase_inj_seed123.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[123]}" --assert-init-tol "$ASSERT_INIT_TOL" &
pb=$!
wait "$pa"; wait "$pb"
echo "[wave A:inj wave2] seed456(GPU$GPU_A) ..."
run_one 456 "$GPU_A" "$INJ_DIR_456" "logs/oracle_phase_inj_seed456.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[456]}" --assert-init-tol "$ASSERT_INIT_TOL"
echo "[wave A:inj] 完了"

# Step 3: wave B = ctrl (zero ctx, oracle/real 無関係に ctx=0)
CTRL_DIR_42=/tmp/oracle_phase_ctrl_seed42
CTRL_DIR_123=/tmp/oracle_phase_ctrl_seed123
CTRL_DIR_456=/tmp/oracle_phase_ctrl_seed456

echo "[wave B:ctrl wave1] seed42(GPU$GPU_A) + seed123(GPU$GPU_B) 並列 ..."
run_one 42  "$GPU_A" "$CTRL_DIR_42"  "logs/oracle_phase_ctrl_seed42.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[42]}" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
pa=$!
run_one 123 "$GPU_B" "$CTRL_DIR_123" "logs/oracle_phase_ctrl_seed123.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[123]}" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
pb=$!
wait "$pa"; wait "$pb"
echo "[wave B:ctrl wave2] seed456(GPU$GPU_A) ..."
run_one 456 "$GPU_A" "$CTRL_DIR_456" "logs/oracle_phase_ctrl_seed456.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[456]}" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx
echo "[wave B:ctrl] 完了"

# Step 4: 回収
echo "================ 完了・回収サマリ ================"
for S in "${SEEDS[@]}"; do
  dst="transfer/oracle_phase_seed${S}"
  mkdir -p "$dst"
  cp -f "/tmp/oracle_phase_inj_seed${S}/t1b_result.json"  "$dst/injected_result.json" 2>/dev/null || echo "[WARN] inj 欠損 seed$S"
  cp -f "/tmp/oracle_phase_ctrl_seed${S}/t1b_result.json" "$dst/control_result.json"  2>/dev/null || echo "[WARN] ctrl 欠損 seed$S"
  cp -f "logs/oracle_phase_inj_seed${S}.log"   "$dst/" 2>/dev/null || true
  cp -f "logs/oracle_phase_ctrl_seed${S}.log"  "$dst/" 2>/dev/null || true
  echo "-- seed$S --"
  for f in "$dst/injected_result.json" "$dst/control_result.json"; do
    [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  {('inj' if not r['zero_ctx'] else 'ctrl')}: init={r['init_mAP']:.4f} best@ep{r['best_epoch']} mAP={r['mAP']:.4f}\")"
  done
done
echo "次: T1b-CA real (+0.00178) と paired-σ で oracle 効果差を確定。"
