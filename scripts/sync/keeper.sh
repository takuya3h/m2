#!/bin/bash
# keeper.sh: cron/systemd の無いコンテナ環境用の常駐スーパーバイザ。
# 役割: (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行
# 起動:   nohup ~/slocal*/m2/scripts/sync/keeper.sh >/dev/null 2>&1 &
# 多重起動は flock で防止されるため、~/.zshrc 等から毎回呼んでも安全。
exec 9>~/.keeper.lock
flock -n 9 || exit 0

M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

while true; do
  # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 &
  fi
  "$M2DIR/scripts/sync/m2-sync.sh"
  sleep 1800
done
