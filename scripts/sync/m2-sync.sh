#!/bin/bash
# m2-sync.sh: keeper.sh から30分毎に実行される。統合ブランチの参照を安全に最新化する。
# - 統合ブランチ上に居る場合: ff-only で更新（衝突時はアラートのみ、作業は壊さない）
# - 作業ブランチ上に居る場合: 統合ブランチの参照だけ進める（ワークツリー不干渉）
MAIN=phase0   # 幹ブランチが移ったらここだけ変更
M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)
LOG=~/claude-sync/sync-alerts.log
mkdir -p "$(dirname "$LOG")"
cd "$M2DIR" || exit 1

git fetch -q origin || {
  echo "$(date '+%F %T') [$(hostname)] fetch失敗(PAT期限切れ?)" >> "$LOG"
  exit 1
}

BR=$(git symbolic-ref --short HEAD 2>/dev/null)
if [ "$BR" = "$MAIN" ]; then
  # 幹ブランチ上に居るのは統合担当(philip)のみの想定
  git merge --ff-only "origin/$MAIN" -q ||
    echo "$(date '+%F %T') [$(hostname)] ${MAIN}更新失敗(未コミット変更と衝突)" >> "$LOG"
else
  git fetch -q origin "$MAIN:$MAIN" ||
    echo "$(date '+%F %T') [$(hostname)] ローカル${MAIN}が分岐(${MAIN}に直接コミットした?)" >> "$LOG"
fi
