#!/usr/bin/env bash
# ============================================================================
# STEP D-aux 系統① 手情報→工程 oracle ゲート（§6 実行順）
# 凍結検出器の GAP(2048) に oracle 手特徴を入力連結 → 素 causal TeCNO で Δ_phase を測る。
# 呼ぶのは scripts/train_haux.py（--hand-source oracle）。特徴キャッシュ利用で軽量。
#
#   入力 = concat([ GAP 2048 , hand_feature D ( , tool 15 ) ]) → 素 causal TeCNO
#
# ── ゲート判定（冒頭・最重要）────────────────────────────────────────────────
#   まず H-1(presence oracle) を 3-seed で回し、S4 base 0.8986±0.0028 と paired-σ 判定。
#   H-1 が **no-go**（Δ_phase が σ 内 or 負・全seed同符号でない）なら、
#   oracle という「手情報の上限」ですら工程認識を押し上げないということ。
#   → 系統①の**非-oracle 投資（S2-hand 手検出器の仕上げ = pred 手特徴の生成）は見送る**。
#   H-1 が go（|mean(Δ)|>pstdev(Δ) かつ全seed同符号で ✓）なら、手情報に信号はある。
#   その上で H-2/H-3/H-6 でどの手特徴表現が効くかを切り分け、非-oracle 化に進む。
#   ※ H-2/H-3/H-6 も oracle 上限の probe なので、H-1 と同一 script 内で続けて回す。
# ── §6 実行順: H-1 → H-2 → H-3 → H-6（各 3-seed 42/123/456）─────────────────
#
# 使い方:
#   bash scripts/run_haux_oracle_gate.sh
# ============================================================================
set -euo pipefail

EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }

# .env を source（NOTION_API_KEY/NOTION_DB_ID をロード・自動投稿のため）
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

# ── 入力キャッシュ存在確認（Fail Loud・train_haux.py が読む先と一致）──────────
GAP_DIR="data/processed/stage1_features/relation_detr_seed42"
for split in train val test; do
  [ -f "$GAP_DIR/${split}_gap.npz" ] || \
    { echo "[ERR] GAP キャッシュ不在: $GAP_DIR/${split}_gap.npz（先に stage1 特徴抽出を実行）"; exit 1; }
  for t in presence count geom; do
    f="data/processed/oracle_handfeature/${split}_oraclehand_${t}.npz"
    [ -f "$f" ] || \
      { echo "[ERR] oracle 手特徴 不在: $f（先に scripts/build_oracle_handfeature.py を実行）"; exit 1; }
  done
  f="data/processed/oracle_toolpresence/${split}_oracletool.npz"
  [ -f "$f" ] || \
    { echo "[ERR] oracle tool 不在: $f（H-6 用・先に scripts/build_oracle_toolpresence.py を実行）"; exit 1; }
done

echo "================ STEP D-aux 系統① oracle ゲート（§6）================"
echo " 呼: scripts/train_haux.py --hand-source oracle epochs=$EPOCHS seeds=${SEEDS[*]}"
echo " 分母: S4 base phase acc 0.8986±0.0028 / macro-F1 0.709（全 Δ はこれに対して）"
echo " 順: H-1 presence(GATE) → H-2 count → H-3 geom → H-6 presence+tool"
echo "===================================================================="

# scripts/train_haux.py を 1 run 起動（method 引数は $@ で受け渡し）
run_haux() {
  local seed="$1" gpu="$2" log="$3"; shift 3
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_haux.py \
    --hand-source oracle --seed "$seed" --epochs "$EPOCHS" "$@" > "$log" 2>&1
}

# 1 手法を 3-seed（wave1: 42(GPU0)+123(GPU1) 並列 / wave2: 456(GPU0) 単独）
run_3seed() {
  local tag="$1"; shift
  echo "[$tag] wave 1: seed42(GPU0) + seed123(GPU1) 並列起動 ..."
  run_haux 42  0 "logs/haux_${tag}_seed42.log"  "$@" &
  local pa=$!
  run_haux 123 1 "logs/haux_${tag}_seed123.log" "$@" &
  local pb=$!
  wait "$pa"; wait "$pb"
  echo "[$tag] wave 2: seed456(GPU0) 単独 ..."
  run_haux 456 0 "logs/haux_${tag}_seed456.log" "$@"
  echo "[$tag] 完了"
}

# ── GATE: H-1 presence(D=4) oracle ─────────────────────────────────────────
echo ""
echo "==== H-1 presence oracle（GATE）===="
run_3seed "h1_presence" --hand-feature-type presence
echo "[GATE] H-1 完了。experiments/transfer/haux_hand_presence_oracle_* を集計し、"
echo "       S4 base 0.8986±0.0028 と paired-σ 判定。no-go なら非-oracle 投資は見送り（上記 冒頭 参照）。"

# ── H-2 count(D=4) oracle ──────────────────────────────────────────────────
echo ""
echo "==== H-2 count oracle ===="
run_3seed "h2_count" --hand-feature-type count

# ── H-3 geom(D=16) oracle ──────────────────────────────────────────────────
echo ""
echo "==== H-3 geom oracle ===="
run_3seed "h3_geom" --hand-feature-type geom

# ── H-6 presence + tool-presence(15) 併用 oracle ───────────────────────────
echo ""
echo "==== H-6 presence + with-tool(oracle) ===="
run_3seed "h6_presence_withtool" --hand-feature-type presence --with-tool --tool-source oracle

echo ""
echo "================ 完了・サマリ ================"
for tag in h1_presence h2_count h3_geom h6_presence_withtool; do
  for S in "${SEEDS[@]}"; do
    log="logs/haux_${tag}_seed${S}.log"
    [ -f "$log" ] && echo "-- $tag seed$S --" && tail -3 "$log"
  done
done
echo ""
echo "次: experiments/transfer/haux_hand_*/metrics.json を 3-seed 集計し、S4 base 0.8986±0.0028 と"
echo "    §10.1 paired-σ 判定（per-seed Δ → mean, pstdev, |mean|/pstdev, 全seed同符号 → |mean|>pstdev かつ同符号で ✓）。"

# ── 末尾: 最良手法の shuffle control（§4.3）—— 最良 hand-feature 確定後に手動で有効化 ─────
# 最良手法（例では presence）の frame 対応を破壊し、Δ_phase が S4 base 水準へ消えることを確認
# （容量効果 vs 手-工程の真の相関の切り分け・positive control の反証）。
#   run_3seed "best_shuffle" --hand-feature-type presence --shuffle-hand
