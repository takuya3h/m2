#!/bin/bash
# keeper.sh: cron/systemd の無いコンテナ環境用の常駐スーパーバイザ。
# 配置:   git -C <m2> show origin/phase0:scripts/sync/keeper.sh > ~/bin/keeper.sh
#         （作業ツリーのブランチに依存しないよう、git オブジェクトから直接展開する）
# 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
# 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
resolve_tunnel() {
  TUNNEL_MARKER=
  for candidate in "$HOME"/.tunnel_to_*; do
    if [ -f "$candidate" ]; then
      TUNNEL_MARKER=$candidate
      break
    fi
  done
  [ -n "$TUNNEL_MARKER" ] || return 1

  HUB_NAME=${TUNNEL_MARKER##*/}
  HUB_NAME=${HUB_NAME#.tunnel_to_}
  TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
  HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
  [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
  [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
}

exec 9>~/.keeper.lock
flock -n 9 || exit 0

M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

while true; do
  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
  # 1行目は秘密鍵パス、任意の2行目は中心の住所。2行目が無い旧形式では中心名をSSH別名に使う。
  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
      -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
      ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
  fi
  # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
  # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
  fi
  # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
  git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
    && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
  # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
  git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
    && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
  ~/bin/m2-sync.sh 9>&-
  sleep 1800 9>&-
done
