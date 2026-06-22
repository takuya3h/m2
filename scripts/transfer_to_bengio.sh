#!/usr/bin/env bash
# ============================================================================
# lecun → bengio : T1b 実行に必要な資産を転送する（rsync・1回の実行で完結）。
#
# 前提: bengio 側で先に clone 済みであること:
#   ssh ubuntu@bengio 'git clone https://github.com/takuya3h/m2.git ~/m2 \
#                       && cd ~/m2 && git checkout docs/plan-rewrite-2026-06'
#
# 使い方（lecun で）:  bash scripts/transfer_to_bengio.sh
#   - user=ubuntu 前提。host "bengio" が解決しない場合のみ下の BENGIO を IP/別名に変更。
#   - BPATH（bengio の clone 先）は run_t1b.sh を探して自動検出するので編集不要。
# ============================================================================
set -euo pipefail

BENGIO="ubuntu@bengio"          # user=ubuntu。host が違う場合のみここを変更（例 ubuntu@10.0.0.x）

SRC=/home/ubuntu/slocal2/m2
cd "$SRC"

# 1) SSH 接続確認
ssh -o ConnectTimeout=10 "$BENGIO" 'echo ok' >/dev/null \
  || { echo "[ERR] $BENGIO に SSH 接続できません（host 名/鍵を確認。host が 'bengio' で解決するか？）"; exit 1; }

# 2) bengio の clone 先を自動検出（run_t1b.sh を探し、その scripts/ の親＝リポルート）
BPATH="$(ssh "$BENGIO" 'd=$(find ~ -maxdepth 6 -name run_t1b.sh 2>/dev/null | head -1); [ -n "$d" ] && cd "$(dirname "$d")/.." && pwd')"
[ -n "$BPATH" ] || {
  echo "[ERR] bengio に clone が見つかりません。先に bengio で実行:"
  echo "      git clone https://github.com/takuya3h/m2.git ~/m2 && cd ~/m2 && git checkout docs/plan-rewrite-2026-06"
  exit 1
}
echo "[xfer] BENGIO=$BENGIO  BPATH(auto-detected)=$BPATH"

# 3) 転送（--mkpath で足りない親 dir を自動作成）
echo "[xfer] (B) Relation-DETR コード一式 ..."
rsync -a --mkpath --exclude=.git --exclude=checkpoints --exclude=__pycache__ \
  --exclude='*.pth' --exclude=train --exclude=outputs --exclude=per_class_coco_map \
  third_party/Relation-DETR/ "$BENGIO:$BPATH/third_party/Relation-DETR/"

echo "[xfer] (C1) 凍結検出器 ×3 (585MB) ..."
rsync -a --mkpath third_party/Relation-DETR/checkpoints/incoming/ \
  "$BENGIO:$BPATH/third_party/Relation-DETR/checkpoints/incoming/"

echo "[xfer] (C2) phase context cache ..."
rsync -a --mkpath data/processed/phase_context/ "$BENGIO:$BPATH/data/processed/phase_context/"

echo "[xfer] (C3) 検出アノテ (59MB) ..."
rsync -a --mkpath data/annotations/egosurgery_tool/ "$BENGIO:$BPATH/data/annotations/egosurgery_tool/"

echo "[xfer] (C4) 画像 (1.2GB・symlink 実体化) ..."
rsync -aL --mkpath data/raw/ego/ "$BENGIO:$BPATH/data/raw/ego/"

# 4) 検証
echo "[xfer] === 検証 ==="
ssh "$BENGIO" "ls -la '$BPATH/third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth'; \
  echo images_val_09=\$(ls '$BPATH/data/raw/ego/val/09/' 2>/dev/null | wc -l); \
  ls '$BPATH/data/processed/phase_context/relation_detr_seed42/'"
echo "[xfer] DONE — 次は bengio で: cd $BPATH && bash scripts/setup_env.sh"
