#!/usr/bin/env bash
# ============================================================================
# H-C-v1（T1b-CA + per-frame entropy gate / §7.2 H-C コアの最小実装）
# seed42/123/456 を lecun 2GPU で **wave-by-wave 並列実行**する。T1b-CA と
# **科学的設定を完全一致**させ、唯一の差は inject=hc（gate 追加）のみ。
#
# 【H-C-v1 vs T1b-CA の比較プロトコル】
#   - 同 warm-start ckpt (per-seed best_ap.pth)
#   - 同 epochs=6 / lr=1e-4 / film_lr=5e-4 / trainable=film / tol=0.02
#   - 同 phase context 入力 / 同 eval_recipe / 同 locked-down test_cfg
#   - 唯一の差 = forward 前の entropy gate（gate_tau=0.5, gate_scale=10 を model cfg で固定）
#   よって inj-mAP の差は **gate 単体の寄与**として解釈できる。
#
# 【3-seed × inj/ctrl = 6 run の 2GPU 割当】
#   wave 1: measure(seed42 GPU0 / seed123 GPU1)         # init mAP 実測
#   wave 2: measure(seed456 GPU0)                        # 残り 1 seed
#   wave 3: inj(seed42 GPU0 / seed123 GPU1)              # 本走 wave A
#   wave 4: inj(seed456 GPU0)                            # 残り 1 seed
#   wave 5: ctrl(seed42 GPU0 / seed123 GPU1)             # 本走 wave B
#   wave 6: ctrl(seed456 GPU0)                           # 残り 1 seed
#   時間概算: measure ~30min + 本走 6h×3 wave = ~18h（lecun A6000×2 想定）。
#
# 使い方（lecun・tmux/screen 推奨。SSH 切断で死なないよう。本スクリプトは
#   親が nohup/background で起動する想定）:
#   nohup bash scripts/run_hc_seeds_lecun.sh > logs/run_hc_seeds_lecun.parent.log 2>&1 &
# ============================================================================
set -euo pipefail

# --- 固定設定（T1b-CA と一致・変更不可。差分は inject=hc のみ） ---
INJECT=hc
TRAINABLE=film
EPOCHS=6
ASSERT_INIT_TOL=0.02
INIT_LO=0.65
INIT_HI=0.78

SEEDS=(42 123 456)
GPU_A="${GPU_A:-0}"
GPU_B="${GPU_B:-1}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い。先に .venv-relation-detr を構築せよ"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"

for S in "${SEEDS[@]}"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done

echo "================ H-C-v1 seed{42,123,456}（lecun・固定設定）================"
echo " inject=$INJECT (= T1b-CA + entropy gate) trainable=$TRAINABLE epochs=$EPOCHS"
echo " 健全帯: init mAP ∈ [$INIT_LO, $INIT_HI]"
echo " 割当: 2GPU wave-by-wave（GPU$GPU_A / GPU$GPU_B、残り1seedはGPU$GPU_A単独）"
echo "==============================================================================="

# 1 run 起動ラッパ
run_one() {
  local seed="$1" gpu="$2" work="$3" log="$4"; shift 4
  CUDA_VISIBLE_DEVICES="$gpu" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$seed" --inject "$INJECT" --trainable "$TRAINABLE" \
      "$@" \
      > "$log" 2>&1
}

extract_init_map() {  # $1=result.json
  "$VENV" - "$1" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
v = r.get("init_mAP")
assert isinstance(v, (int, float)), f"init_mAP 不正: {v!r}"
print(f"{v:.10f}")
PY
}

# ---------------------------------------------------------------------------
# Step 0: MSDeformAttn CUDA 拡張を単一プロセスで事前 JIT ビルド
# ---------------------------------------------------------------------------
echo "[warmup] MultiScaleDeformableAttention CUDA 拡張を事前ビルド中 ..."
CUDA_VISIBLE_DEVICES="$GPU_A" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] MSDeformAttn ext ready')" \
  || { echo '[ERR] MSDeformAttn 拡張の事前ビルドに失敗'; exit 1; }

# ---------------------------------------------------------------------------
# Step 1: measure-only（--epochs 0）で 3 seed の init mAP を実測
# ---------------------------------------------------------------------------
declare -A MEAS_DIR INIT_MAP
for S in "${SEEDS[@]}"; do
  MEAS_DIR[$S]="/tmp/hc_measure_seed${S}"
done

echo "[measure wave1] seed42(GPU$GPU_A) / seed123(GPU$GPU_B) 並列 measure ..."
run_one 42  "$GPU_A" "${MEAS_DIR[42]}"  "logs/hc_measure_seed42.log"  --epochs 0 &
pa=$!
run_one 123 "$GPU_B" "${MEAS_DIR[123]}" "logs/hc_measure_seed123.log" --epochs 0 &
pb=$!
wait "$pa"; wait "$pb"

echo "[measure wave2] seed456(GPU$GPU_A) 単独 measure ..."
run_one 456 "$GPU_A" "${MEAS_DIR[456]}" "logs/hc_measure_seed456.log" --epochs 0
wait

for S in "${SEEDS[@]}"; do
  INIT_MAP[$S]="$(extract_init_map "${MEAS_DIR[$S]}/t1b_result.json")"
  echo "[measure] seed$S init mAP=${INIT_MAP[$S]}"
done

# 健全帯チェック
"$VENV" - "${INIT_MAP[42]}" "${INIT_MAP[123]}" "${INIT_MAP[456]}" "$INIT_LO" "$INIT_HI" <<'PY'
import sys
a, b, c, lo, hi = map(float, sys.argv[1:6])
seeds = [(42, a), (123, b), (456, c)]
bad = [(s, v) for s, v in seeds if not (lo <= v <= hi)]
if bad:
    for s, v in bad:
        print(f"[PREFLIGHT-FAIL] seed{s} init mAP={v:.4f} が健全帯[{lo},{hi}]外 → 中断")
    sys.exit(3)
print("[measure] 全 seed 健全帯チェック OK")
PY

# ---------------------------------------------------------------------------
# Step 2: 本走 wave A = inj（real ctx）
# ---------------------------------------------------------------------------
INJ_DIR_42=/tmp/hc_inj_seed42
INJ_DIR_123=/tmp/hc_inj_seed123
INJ_DIR_456=/tmp/hc_inj_seed456

echo "[wave A:inj wave1] seed42(GPU$GPU_A) + seed123(GPU$GPU_B) 並列起動 ..."
run_one 42  "$GPU_A" "$INJ_DIR_42"  "logs/hc_inj_seed42.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[42]}" --assert-init-tol "$ASSERT_INIT_TOL" &
pa=$!
run_one 123 "$GPU_B" "$INJ_DIR_123" "logs/hc_inj_seed123.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[123]}" --assert-init-tol "$ASSERT_INIT_TOL" &
pb=$!
wait "$pa"; wait "$pb"

echo "[wave A:inj wave2] seed456(GPU$GPU_A) 単独 ..."
run_one 456 "$GPU_A" "$INJ_DIR_456" "logs/hc_inj_seed456.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[456]}" --assert-init-tol "$ASSERT_INIT_TOL"
echo "[wave A:inj] 完了"

# ---------------------------------------------------------------------------
# Step 3: 本走 wave B = ctrl（zero ctx）
# ---------------------------------------------------------------------------
CTRL_DIR_42=/tmp/hc_ctrl_seed42
CTRL_DIR_123=/tmp/hc_ctrl_seed123
CTRL_DIR_456=/tmp/hc_ctrl_seed456

echo "[wave B:ctrl wave1] seed42(GPU$GPU_A) + seed123(GPU$GPU_B) 並列起動 ..."
run_one 42  "$GPU_A" "$CTRL_DIR_42"  "logs/hc_ctrl_seed42.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[42]}" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
pa=$!
run_one 123 "$GPU_B" "$CTRL_DIR_123" "logs/hc_ctrl_seed123.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[123]}" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
pb=$!
wait "$pa"; wait "$pb"

echo "[wave B:ctrl wave2] seed456(GPU$GPU_A) 単独 ..."
run_one 456 "$GPU_A" "$CTRL_DIR_456" "logs/hc_ctrl_seed456.log" \
  --epochs "$EPOCHS" --assert-init-map "${INIT_MAP[456]}" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx
echo "[wave B:ctrl] 完了"

# ---------------------------------------------------------------------------
# Step 4: 結果回収（transfer/hc_seed{S}/ へ inj+ctrl result を保全）
# ---------------------------------------------------------------------------
echo "================ 完了・回収サマリ ================"
for S in "${SEEDS[@]}"; do
  dst="transfer/hc_seed${S}"
  mkdir -p "$dst"
  cp -f "/tmp/hc_inj_seed${S}/t1b_result.json"  "$dst/injected_result.json" 2>/dev/null || echo "[WARN] inj result 欠損 seed$S"
  cp -f "/tmp/hc_ctrl_seed${S}/t1b_result.json" "$dst/control_result.json"  2>/dev/null || echo "[WARN] ctrl result 欠損 seed$S"
  cp -f "logs/hc_inj_seed${S}.log"   "$dst/" 2>/dev/null || true
  cp -f "logs/hc_ctrl_seed${S}.log"  "$dst/" 2>/dev/null || true
  echo "-- seed$S --"
  for f in "$dst/injected_result.json" "$dst/control_result.json"; do
    [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  {('inj' if not r['zero_ctx'] else 'ctrl')}: init={r['init_mAP']:.4f} best@ep{r['best_epoch']} mAP={r['mAP']:.4f}\")"
  done
done
echo "次: T1b-CA inj/ctrl と 3-seed paired-σ で純効果差を比較（gate 単体寄与）。"
