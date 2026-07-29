#!/usr/bin/env bash
# ============================================================================
# P4 T1b Phase→Det 最小版（classification-only phase bias / inject=clsbias）
# 3seed × inj/ctrl を efros 2GPU で実行する。科学的設定は T1b-CA
# (run_t1b_ca_seeds_lecun.sh) と**完全一致**: trainable=film / epochs=6 / lr=1e-4 /
# film_lr=5e-4 / tol=0.02。唯一の差は inject=clsbias。
#   clsbias = box 枝を一切触らず、class logit にのみ phase 事後(9-d)→MLP(zero-init)→
#   per-tool 15次元 residual を加え、rare∧工程特異術具のみ通す
#   (Bipolar=0 / Scalpel=9 / Skewer=11 / Syringe=13)。zero-init ゆえ warm-start 直後は
#   S0-frozen と厳密一致（恒等）→ Δ_detection が「注入効果」を測る。
#
# 【assert 値の決め方（捏造防止・誠実）／T1b-CA と同一手順】
#   各 seed 独立の init mAP を --epochs 0 で実測 → 健全帯確認 → --assert-init-map に固定して
#   本走。inj と ctrl は同一 warm-start・zero-init ゆえ init mAP は一致するはず（再現性ガード）。
#
# 進行（2GPU: inj→GPU_INJ / ctrl→GPU_CTRL。seed 毎に measure→inj∥ctrl→回収）:
#   warmup(MSDeformAttn) → [seed 42→123→456] measure → 本走 inj∥ctrl → transfer/ 回収。
#
# 使い方（親が nohup/background で起動想定。SSH 切断耐性は tmux/nohup 側で担保）:
#   bash scripts/run_t1b_clsbias_3seed_efros.sh
#   # GPU 割当変更: GPU_INJ=0 GPU_CTRL=1 bash scripts/run_t1b_clsbias_3seed_efros.sh
# ============================================================================
set -euo pipefail

# --- 固定設定（T1b-CA と一致・変更不可） ---
INJECT=clsbias
TRAINABLE=film
EPOCHS=6
ASSERT_INIT_TOL=0.02
INIT_LO=0.65
INIT_HI=0.78                       # base 検出器 mAP ≒ 0.70–0.73（seed42=0.7303）帯
SEEDS=(42 123 456)
GPU_INJ="${GPU_INJ:-0}"
GPU_CTRL="${GPU_CTRL:-1}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い。scripts/setup_env.sh で .venv-relation-detr を構築せよ"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
# ninja を PATH に通す（無いと MS-Deform-Attn C++ ext がロードできず純 PyTorch フォールバック=低速。
# コンパイル済み .so が cache にあれば ninja は再ビルドせず「no work」で高速ロードのみ）。
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い（$ROOT/.venv-relation-detr/bin/ninja を確認）"; exit 1; }

for S in "${SEEDS[@]}"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done

echo "================ P4 T1b-clsbias 3seed（efros・固定設定）================"
echo " inject=$INJECT trainable=$TRAINABLE epochs=$EPOCHS tol=$ASSERT_INIT_TOL"
echo " seeds=${SEEDS[*]}  割当: inj→GPU$GPU_INJ  ctrl→GPU$GPU_CTRL"
echo " 健全帯: init mAP ∈ [$INIT_LO, $INIT_HI]（外れたら中断）"
echo "======================================================================="

# train_t1b.py を 1 本起動する薄いラッパ。$1=seed $2=gpu $3=workdir $4=logfile $5..=extra
run_one() {
  local seed="$1" gpu="$2" work="$3" log="$4"; shift 4
  CUDA_VISIBLE_DEVICES="$gpu" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$seed" --inject "$INJECT" --trainable "$TRAINABLE" \
      "$@" \
      > "$log" 2>&1
}

# result.json から init_mAP を厳密抽出（範囲外/欠損は Fail Loud）
extract_init_map() {
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
CUDA_VISIBLE_DEVICES="$GPU_INJ" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] MSDeformAttn ext ready')" \
  || { echo '[ERR] MSDeformAttn 拡張の事前ビルドに失敗'; exit 1; }

# ---------------------------------------------------------------------------
# seed ごと: measure → 帯チェック → 本走 inj∥ctrl → 回収
# ---------------------------------------------------------------------------
for S in "${SEEDS[@]}"; do
  echo ""
  echo "############### seed$S ###############"
  MEAS=${ROOT}/experiments/transfer/t1b_clsbias_measure_seed${S}
  echo "[measure seed$S] init mAP を実測（--epochs 0, GPU$GPU_INJ）..."
  run_one "$S" "$GPU_INJ" "$MEAS" "logs/t1b_clsbias_measure_seed${S}.log" --epochs 0 --no-save-predictions
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

  INJ=${ROOT}/experiments/transfer/t1b_clsbias_seed${S}
  CTRL=${ROOT}/experiments/transfer/t1b_clsbias_zeroctx_seed${S}
  echo "[seed$S 本走] inj(GPU$GPU_INJ) ∥ ctrl(GPU$GPU_CTRL) 並列起動（epochs=$EPOCHS）..."
  run_one "$S" "$GPU_INJ" "$INJ" "logs/t1b_clsbias_seed${S}.log" \
    --epochs "$EPOCHS" --assert-init-map "$INIT" --assert-init-tol "$ASSERT_INIT_TOL" &
  pid_inj=$!
  run_one "$S" "$GPU_CTRL" "$CTRL" "logs/t1b_clsbias_zeroctx_seed${S}.log" \
    --epochs "$EPOCHS" --assert-init-map "$INIT" --assert-init-tol "$ASSERT_INIT_TOL" --zero-ctx &
  pid_ctrl=$!
  wait "$pid_inj"; wait "$pid_ctrl"
  echo "[seed$S 本走] 完了"

  # §4.6 の比較前提（注入層 zero-init=恒等 → inj/ctrl の init 予測は完全一致）を実測で記録する。
  # 一致しなければ warm-start か恒等性が壊れており、Δ を注入効果と解釈できない。
  "$VENV" scripts/run_artifacts.py --verify-init-identity "$INJ" "$CTRL" \
    > "logs/t1b_${TAG}_init_identity_seed${S}.json" \
    || echo "[WARN] seed$S: inj/ctrl の init 予測が不一致（恒等性の破れを疑え）"

  dst="transfer/t1b_clsbias_seed${S}_efros"
  mkdir -p "$dst"
  cp -f "$INJ/t1b_result.json"  "$dst/injected_result.json" 2>/dev/null || echo "[WARN] inj result 欠損 seed$S"
  cp -f "$CTRL/t1b_result.json" "$dst/control_result.json"  2>/dev/null || echo "[WARN] ctrl result 欠損 seed$S"
  cp -f "logs/t1b_clsbias_seed${S}.log"         "$dst/" 2>/dev/null || true
  cp -f "logs/t1b_clsbias_zeroctx_seed${S}.log" "$dst/" 2>/dev/null || true
done

# ---------------------------------------------------------------------------
# 最終サマリ
# ---------------------------------------------------------------------------
echo ""
echo "================ 完了・回収サマリ ================"
for S in "${SEEDS[@]}"; do
  dst="transfer/t1b_clsbias_seed${S}_efros"
  echo "-- seed$S --"
  for f in "$dst/injected_result.json" "$dst/control_result.json"; do
    [ -f "$f" ] && "$VENV" -c "import json;r=json.load(open('$f'));print(f\"  {('inj' if not r['zero_ctx'] else 'ctrl')}: init={r['init_mAP']:.4f} best@ep{r['best_epoch']} mAP={r['mAP']:.4f}\")"
  done
done
echo "次: scripts/analyze_t1b_clsbias.py で rare-tool per-class AP を 3-seed paired-σ 判定（inj−ctrl）。"
echo "[ALLDONE] P4 T1b-clsbias 3seed 完了"
