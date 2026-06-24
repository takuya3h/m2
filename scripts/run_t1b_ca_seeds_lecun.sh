#!/usr/bin/env bash
# ============================================================================
# T1b-CA（cross-attention phase→det / §4.6 primary）seed123/456 を lecun で
# 2GPU ロックステップ並行実行する。seed42（run_t1b_ca_seed42_bengio.sh）と
# **科学的設定を完全一致**させ、唯一 seed 固有に変わる warm-start ckpt と
# その init mAP（= assert 値）だけを実測で決める。
#
# 【設定ドリフト根絶】固定: inject=ca / trainable=film / epochs=6 / lr=1e-4 /
#   film_lr=5e-4 / tol=0.02。seed42 と同一。前回 seed42 が --trainable all に
#   化けた事故の再発防止（CLAUDE「実験設定が少しでも異ならないよう徹底」）。
#
# 【assert 値の決め方（捏造防止・誠実）】
#   seed42 の 0.7303 は「その base 検出器の独立既知 mAP」。seed123/456 には
#   独立基準が無いため流用しない。代わりに:
#     (1) --epochs 0 で measure-only 実行 → full-val preflight で init_mAP を実測。
#     (2) 健全帯 [INIT_LO, INIT_HI] 内かを確認（ckpt 取り違え・恒等破れの粗検出）。
#     (3) 実測値を --assert-init-map に固定し本走 → 別プロセスで init mAP が再現
#         されることを検査（プロセス間非決定性・部分ロード等のドリフト検出）。
#   seed42 では inj/ctrl の init_mAP が 15 桁完全一致 → 再現性ガードは健全。
#
# 進行（2GPU を seed123=GPU0 / seed456=GPU1 に割当て、全工程ロックステップ並行）:
#   warmup(MSDeformAttn) → measure(両seed) → 本走wave A(inj 両seed) →
#   本走wave B(ctrl 両seed) → 結果を transfer/ へ回収。
#
# 使い方（lecun・tmux/screen 推奨。SSH 切断で死なないよう。本スクリプトは
#   親が nohup/background で起動する想定）:
#   bash scripts/run_t1b_ca_seeds_lecun.sh
#   # GPU 割当を変える: GPU_A=0 GPU_B=1 bash scripts/run_t1b_ca_seeds_lecun.sh
# ============================================================================
set -euo pipefail

# --- 固定設定（seed42 と一致・変更不可） ---
INJECT=ca
TRAINABLE=film
EPOCHS=6
ASSERT_INIT_TOL=0.02
# 健全帯: warm-start+zero-init 恒等が成立すれば base 検出器 mAP（≒0.70–0.73）に
# 一致するはず。これを大きく外れたら ckpt 取り違え/恒等破れ → 即中断。
INIT_LO=0.65
INIT_HI=0.78

SEED_A=123; GPU_A="${GPU_A:-0}"
SEED_B=456; GPU_B="${GPU_B:-1}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い。先に scripts/setup_env.sh で .venv-relation-detr を構築せよ"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"

for S in "$SEED_A" "$SEED_B"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done

echo "================ T1b-CA seed${SEED_A}/${SEED_B}（lecun・固定設定）================"
echo " inject=$INJECT trainable=$TRAINABLE epochs=$EPOCHS tol=$ASSERT_INIT_TOL"
echo " 割当: seed$SEED_A→GPU$GPU_A  seed$SEED_B→GPU$GPU_B"
echo " 健全帯: init mAP ∈ [$INIT_LO, $INIT_HI]（外れたら中断）"
echo "==============================================================================="

# train_t1b.py を 1 本起動する薄いラッパ。
# 引数: $1=seed $2=gpu $3=workdir $4=logfile $5=extra(空 or "--zero-ctx" or "--epochs 0 override")
#   epochs/assert は呼び出し側が EXTRA で渡す（measure と本走で違うため）。
run_one() {
  local seed="$1" gpu="$2" work="$3" log="$4"; shift 4
  CUDA_VISIBLE_DEVICES="$gpu" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$seed" --inject "$INJECT" --trainable "$TRAINABLE" \
      "$@" \
      > "$log" 2>&1
}

# result.json から init_mAP を厳密抽出（範囲外/欠損は Fail Loud）。
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
# Step 0: MSDeformAttn CUDA 拡張を単一プロセスで事前 JIT ビルド（並列競合回避）
# ---------------------------------------------------------------------------
echo "[warmup] MultiScaleDeformableAttention CUDA 拡張を事前ビルド中 ..."
CUDA_VISIBLE_DEVICES="$GPU_A" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] MSDeformAttn ext ready')" \
  || { echo '[ERR] MSDeformAttn 拡張の事前ビルドに失敗'; exit 1; }

# ---------------------------------------------------------------------------
# Step 1: measure-only（--epochs 0）で各 seed の init mAP を実測（並列）
# ---------------------------------------------------------------------------
echo "[measure] seed$SEED_A(GPU$GPU_A) / seed$SEED_B(GPU$GPU_B) の init mAP を実測 ..."
MEAS_A=/tmp/t1b_ca_measure_seed${SEED_A}
MEAS_B=/tmp/t1b_ca_measure_seed${SEED_B}
run_one "$SEED_A" "$GPU_A" "$MEAS_A" "logs/t1b_ca_measure_seed${SEED_A}.log" --epochs 0 &
pid_a=$!
run_one "$SEED_B" "$GPU_B" "$MEAS_B" "logs/t1b_ca_measure_seed${SEED_B}.log" --epochs 0 &
pid_b=$!
wait "$pid_a"; wait "$pid_b"

INIT_A="$(extract_init_map "$MEAS_A/t1b_result.json")"
INIT_B="$(extract_init_map "$MEAS_B/t1b_result.json")"
echo "[measure] seed$SEED_A init mAP=$INIT_A / seed$SEED_B init mAP=$INIT_B"

# 健全帯チェック（粗誤り検出・Fail Loud）
"$VENV" - "$INIT_A" "$INIT_B" "$INIT_LO" "$INIT_HI" "$SEED_A" "$SEED_B" <<'PY'
import sys
a, b, lo, hi = map(float, sys.argv[1:5])
sa, sb = sys.argv[5], sys.argv[6]
bad = [(s, v) for s, v in ((sa, a), (sb, b)) if not (lo <= v <= hi)]
if bad:
    for s, v in bad:
        print(f"[PREFLIGHT-FAIL] seed{s} init mAP={v:.4f} が健全帯[{lo},{hi}]外 "
              f"→ ckpt 取り違え/恒等破れの疑い。中断。")
    sys.exit(3)
print("[measure] 健全帯チェック OK")
PY

# ---------------------------------------------------------------------------
# Step 2: 本走 wave A = inj（real ctx, 両 seed 並列, 実測 init を assert 固定）
# ---------------------------------------------------------------------------
INJ_A=/tmp/t1b_ca_seed${SEED_A};  INJ_B=/tmp/t1b_ca_seed${SEED_B}
echo "[wave A:inj] seed$SEED_A(GPU$GPU_A) + seed$SEED_B(GPU$GPU_B) 並列起動 ..."
run_one "$SEED_A" "$GPU_A" "$INJ_A" "logs/t1b_ca_seed${SEED_A}.log" \
  --epochs "$EPOCHS" --assert-init-map "$INIT_A" --assert-init-tol "$ASSERT_INIT_TOL" &
pid_a=$!
run_one "$SEED_B" "$GPU_B" "$INJ_B" "logs/t1b_ca_seed${SEED_B}.log" \
  --epochs "$EPOCHS" --assert-init-map "$INIT_B" --assert-init-tol "$ASSERT_INIT_TOL" &
pid_b=$!
wait "$pid_a"; wait "$pid_b"
echo "[wave A:inj] 完了"

# ---------------------------------------------------------------------------
# Step 3: 本走 wave B = ctrl（zero ctx, 両 seed 並列, 同 assert）
# ---------------------------------------------------------------------------
CTRL_A=/tmp/t1b_ca_zeroctx_seed${SEED_A};  CTRL_B=/tmp/t1b_ca_zeroctx_seed${SEED_B}
echo "[wave B:ctrl] seed$SEED_A(GPU$GPU_A) + seed$SEED_B(GPU$GPU_B) 並列起動 ..."
run_one "$SEED_A" "$GPU_A" "$CTRL_A" "logs/t1b_ca_zeroctx_seed${SEED_A}.log" \
  --epochs "$EPOCHS" --assert-init-map "$INIT_A" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
pid_a=$!
run_one "$SEED_B" "$GPU_B" "$CTRL_B" "logs/t1b_ca_zeroctx_seed${SEED_B}.log" \
  --epochs "$EPOCHS" --assert-init-map "$INIT_B" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
pid_b=$!
wait "$pid_a"; wait "$pid_b"
echo "[wave B:ctrl] 完了"

# ---------------------------------------------------------------------------
# Step 4: 結果回収（transfer/t1b_ca_seed{S}_lecun/ へ inj+ctrl result を保全）
# ---------------------------------------------------------------------------
echo "================ 完了・回収用サマリ ================"
for S in "$SEED_A" "$SEED_B"; do
  dst="transfer/t1b_ca_seed${S}_lecun"
  mkdir -p "$dst"
  cp -f "/tmp/t1b_ca_seed${S}/t1b_result.json"        "$dst/injected_result.json" 2>/dev/null || echo "[WARN] inj result 欠損 seed$S"
  cp -f "/tmp/t1b_ca_zeroctx_seed${S}/t1b_result.json" "$dst/control_result.json"  2>/dev/null || echo "[WARN] ctrl result 欠損 seed$S"
  cp -f "logs/t1b_ca_seed${S}.log"          "$dst/" 2>/dev/null || true
  cp -f "logs/t1b_ca_zeroctx_seed${S}.log"  "$dst/" 2>/dev/null || true
  echo "-- seed$S --"
  for f in "$dst/injected_result.json" "$dst/control_result.json"; do
    [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  {('inj' if not r['zero_ctx'] else 'ctrl')}: init={r['init_mAP']:.4f} best@ep{r['best_epoch']} mAP={r['mAP']:.4f}\")"
  done
done
echo "次: 集計（inj−ctrl の Δ_det を seed42 と合わせ 3-seed paired-σ で §10.1 判定）。"
