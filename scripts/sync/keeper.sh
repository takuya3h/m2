#!/bin/bash
# keeper.sh: cron/systemd の無いコンテナ環境用の常駐スーパーバイザ。
# 配置:   git -C <m2> show origin/phase0:scripts/sync/keeper.sh > ~/bin/keeper.sh
#         （作業ツリーのブランチに依存しないよう、git オブジェクトから直接展開する）
# 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
# 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
exec 9>~/.keeper.lock
flock -n 9 || exit 0

M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

while true; do
  # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 &
  fi
  # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
  git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
    && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
  # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
  git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
    && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
  ~/bin/m2-sync.sh
  sleep 1800
done
