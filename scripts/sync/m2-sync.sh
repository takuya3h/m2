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

# --- auto-merge: phase0 の更新を作業ブランチへ取り込む ---
# auto-push より前に置く。merge してから push すれば 1 ループで両方片付く。
# 条件: 作業ブランチ上 / 追跡変更 0 件 / behind > 0 / 未追跡が阻害しない
# 安全策: rm は自動化しない（内容同一の判定と退避は人間が行う）。衝突したら即 abort。
if [ "$BR" != "$MAIN" ]; then
  BEHIND=$(git rev-list --count "HEAD..origin/$MAIN" 2>/dev/null || echo 0)
  if [ "$BEHIND" != "0" ]; then
    # grep -c は該当 0 件で exit 1 を返すため || true が要る。
    DIRTY=$(git status --porcelain | grep -vc '^??' || true)
    if [ "${DIRTY:-0}" != "0" ]; then
      alert "auto-merge skip: 追跡変更 ${DIRTY} 件 (behind ${BEHIND})"
    else
      # 未追跡ファイルが取り込み先にも存在すると git は上書きを拒む。
      # 事前に集合の積を取って判定する（rm はしない）。
      BLOCKED=$(comm -12 \
        <(git ls-files --others --exclude-standard | sort) \
        <(git ls-tree -r --name-only "origin/$MAIN" | sort) | wc -l | tr -d ' ')
      if [ "$BLOCKED" != "0" ]; then
        alert "auto-merge skip: 未追跡 ${BLOCKED} 件が阻害 (behind ${BEHIND}) 手動対応が必要"
      elif git merge --no-edit -q "origin/$MAIN" 2>/dev/null; then
        alert "auto-merge: ${BR} <- origin/${MAIN} (${BEHIND} commits)"
      else
        # conflicted state を残すと次ループから毎回失敗し続けるので必ず戻す。
        git merge --abort 2>/dev/null
        alert "auto-merge失敗(abort済): ${BR} <- origin/${MAIN} 手動対応が必要"
      fi
    fi
  fi
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

# --- auto-PR: push した内容を phase0 へ向けた Draft PR にする ---
# Draft なので誤マージされない。人間が Draft を外すとマージ可能になる。
# gh が無い / 認証されていない環境では静かに skip する。
if [ "$BR" != "$MAIN" ] && command -v gh >/dev/null 2>&1; then
  AHEAD_MAIN=$(git rev-list --count "origin/$MAIN..HEAD" 2>/dev/null || echo 0)
  if [ "$AHEAD_MAIN" != "0" ] && git rev-parse --verify -q "origin/$BR" >/dev/null; then
    # gh 呼び出しの失敗（ネットワーク断・認証切れ等）を "0" と誤判定して
    # 重複起票しないよう、初期値を -1 にする。
    EXISTING=$(gh pr list --head "$BR" --state open --json number --jq 'length' 2>/dev/null || echo -1)
    if [ "$EXISTING" = "0" ]; then
      if gh pr create --draft --base "$MAIN" --head "$BR" \
           --title "auto: ${BR} -> ${MAIN}" \
           --body "m2-sync.sh による自動起票（$(date '+%F %T')）。${AHEAD_MAIN} commits。

内容を確認し、問題なければ Draft を外してください。" >/dev/null 2>&1; then
        alert "auto-PR: ${BR} -> ${MAIN} (${AHEAD_MAIN} commits, draft)"
      else
        alert "auto-PR失敗: ${BR} -> ${MAIN} (${AHEAD_MAIN} commits)"
      fi
    fi
  fi
fi
