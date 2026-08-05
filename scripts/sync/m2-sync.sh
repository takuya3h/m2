#!/bin/bash
# m2-sync.sh: keeper.sh から30分毎に実行される。統合ブランチの参照を安全に最新化する。
# - 統合ブランチ上に居る場合: ff-only で更新（衝突時はアラートのみ、作業は壊さない）
# - 作業ブランチ上に居る場合: 統合ブランチの参照だけ進める（ワークツリー不干渉）
#   加えて、コミット済みで未 push のものを自分の作業ブランチへ送る（auto-push）
#
# 本スクリプトは keeper.sh が毎ループ origin/phase0 から自己更新する。
# そのため phase0 にマージすれば全台へ自動で配られる（最短 2 ループ / 最大 60 分）。
MAIN=phase0   # 幹ブランチが移ったらここだけ変更
M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)
LOG=~/claude-sync/sync-alerts.log

# サーバー名は 3 段で解決する。
# 稼働中の keeper は SERVERNAME を設定する前に起動していることがあり
# （例: ilya の PID 73082 は 2026-07-04 起動 / SERVERNAME 設定は 2026-08-02）、
# その場合 hostname へ落ちる。philip と ilya はどちらも aolab を返すため
# 自動操作の出所が判別できなくなる。keeper を触らずに直すため .servername を挟む。
SRV="${SERVERNAME:-}"
[ -z "$SRV" ] && [ -f "$M2DIR/.servername" ] && SRV=$(head -1 "$M2DIR/.servername" | tr -d ' \n')
[ -z "$SRV" ] && SRV=$(hostname)

mkdir -p "$(dirname "$LOG")"
alert() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$SRV" "$1" >> "$LOG"; }

cd "$M2DIR" || exit 1

git fetch -q origin || {
  alert "fetch失敗(PAT期限切れ?)"
  exit 1
}

BR=$(git symbolic-ref --short HEAD 2>/dev/null)
if [ "$BR" = "$MAIN" ]; then
  # 幹ブランチ上に居るのは統合担当(philip)のみの想定
  git merge --ff-only "origin/$MAIN" -q ||
    alert "${MAIN}更新失敗(未コミット変更と衝突)"
else
  git fetch -q origin "$MAIN:$MAIN" ||
    alert "ローカル${MAIN}が分岐(${MAIN}に直接コミットした?)"
fi

# --- auto-push: コミット済みで未 push のものを自分の作業ブランチへ送る ---
# 2026-08-02 に lecun で 72 run（selection_noise）が 1 か月未 push だった。
# commit は自動化しない。push だけを自動化する。
#
# 基準は @{u} ではなく push 先の origin/$BR を使う。
# `git switch -c <new> origin/phase0` で作ったブランチは上流が origin/phase0 の
# ままになり、@{u} 基準だと push しても ahead が減らず、30 分ごとに無意味な
# auto-push とアラートを繰り返す（2026-08-05 に ilya で再現・実測）。
#
# 対象外: 幹ブランチ（保護ブランチで push できない）
#         origin に未登録のブランチ（人間が作りかけのものを勝手に公開しない）
if [ "$BR" != "$MAIN" ] && git rev-parse --verify -q "origin/$BR" >/dev/null; then
  AHEAD=$(git rev-list --count "origin/$BR..HEAD" 2>/dev/null || echo 0)
  if [ "$AHEAD" != "0" ]; then
    if git push -q origin "$BR" 2>/dev/null; then
      alert "auto-push: $BR ($AHEAD commits)"
    else
      alert "auto-push失敗: $BR ($AHEAD commits) 手動確認が必要"
    fi
  fi
fi
