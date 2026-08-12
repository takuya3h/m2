# Audit — T-2026-08-12-hub-from-marker

## Phase A: 変更前

### 前提

```text
$ touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
2
$ git branch --show-current
feat/hub-from-marker
$ git --no-pager status --porcelain
 M tasks/todo.md
?? tasks/T-2026-08-12-hub-from-marker/
```

`tasks/todo.md` は上位指示で要求された計画記録である。契約ディレクトリ以外の未追跡物は無い。

### 正本と稼働中の実体

```text
$ wc -l scripts/sync/keeper.sh; wc -c scripts/sync/keeper.sh
34 scripts/sync/keeper.sh
2250 scripts/sync/keeper.sh
$ wc -l ~/bin/keeper.sh 2>/dev/null; wc -c ~/bin/keeper.sh 2>/dev/null
34 /home/ubuntu/bin/keeper.sh
2250 /home/ubuntu/bin/keeper.sh
$ git --no-pager diff --no-index -- scripts/sync/keeper.sh ~/bin/keeper.sh > /tmp/kd.txt 2>&1
$ wc -l /tmp/kd.txt; cat /tmp/kd.txt
0 /tmp/kd.txt
```

差分出力は 0 行であり、正本と稼働中の実体は一致している。

### 中心に関わる箇所

```text
$ grep -n -i -E "philip|150|tunnel|22001|22000|50072|hub" scripts/sync/keeper.sh
13:  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
14:  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
15:  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
16:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
19:      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &
$ grep -c -i -E "philip|150|tunnel|22001|22000|50072|hub" scripts/sync/keeper.sh
5
```

判定に使われる固定値は、目印名 `.tunnel_to_philip` と SSH 宛先 `192.168.196.150` である。

### 変更前の挙動（実装読解）

| 状況 | 変更前の挙動 |
|---|---|
| `~/.tunnel_to_philip` がある | 固定条件が真になり、philip の固定住所へ張る |
| `~/.tunnel_to_lecun` だけがある | 固定条件が偽になるため張らない |
| 目印が無い | 固定条件が偽になるため張らない |

実際の SSH 命令は起動していない。

### 自ホストの目印（変更していない）

```text
$ ls -a ~/ | grep -i tunnel; echo "count=$(ls -a ~/ | grep -c -i tunnel)"
.tunnel.log
.tunnel_to_philip
count=2
$ stat -c 'keeper path=%n size=%s mtime=%y' ~/bin/keeper.sh
keeper path=/home/ubuntu/bin/keeper.sh size=2250 mtime=2026-07-04 07:17:08.974760455 +0000
$ stat -c 'marker path=%n size=%s mtime=%y' ~/.tunnel_to_* 2>/dev/null
marker path=/home/ubuntu/.tunnel_to_philip size=43 mtime=2026-07-03 23:36:05.625355038 +0000
```

`tunnel` を含む項目はログを含め 2 件、`.tunnel_to_*` 形式の目印は 1 件である。

### 変更前のプロセス数

検索命令自身とその祖先を除外し、`/proc/*/cmdline` を走査した。

```text
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
```

陰性対照が 0 であるため、計数器は存在しない語を誤検出していない。

### G1

PASS。正本と稼働版の一致、中心関連 5 行、変更前の三通りの挙動、自ホストの目印と変更前プロセス数を記録した。

## Phase B: 変更後

### 実装上の決定

- 目印は `"$HOME"/.tunnel_to_*` のうち辞書順で最初の通常ファイルを一つ選ぶ。
- 中心名は目印のファイル名から `.tunnel_to_` を除いて導出する。
- 1 行目は秘密鍵パス、任意の 2 行目は中心の住所とする。
- 2 行目が無い旧形式では、中心名を SSH 別名として使う。既存の SSH 設定が `Host philip` を住所へ解決する。
- 目印が無い場合、または中心名・鍵パスが空の場合は中継を張らない。

### 固定値の除去と構文

```text
$ grep -n -i -E "philip|192\.168\.196\.150" scripts/sync/keeper.sh; echo "grep_exit=$?"
grep_exit=1
$ sh -n scripts/sync/keeper.sh; echo "syntax_exit=$?"
syntax_exit=0
$ command -v shellcheck && shellcheck scripts/sync/keeper.sh || echo "shellcheck 不在"
shellcheck 不在
```

固定中心名・旧住所は 0 件である。`grep_exit=1` は一致なしを表す。構文検査は通過した。

### 四通りの対照

`sed -n '/^resolve_tunnel() {/,/^}/p'` で変更後スクリプトから解決関数だけを `/tmp/resolve_tunnel.sh` へ抽出し、`/tmp/hub-marker-test.7di2Uz` を偽の HOME として Bash で評価した。keeper のループと SSH 命令は実行していない。

最初に対話シェルの zsh で評価したところ、目印なしの未一致 glob を zsh がエラーにした。

```text
resolve_tunnel:2: no matches found: /tmp/hub-marker-test.7di2Uz/none/.tunnel_to_*
```

対象スクリプトの shebang と同じ Bash で全件を再測定した生出力は次のとおり。

```text
case=legacy marker=.tunnel_to_philip hub=philip key=/tmp/legacy_key address=philip
case=new marker=.tunnel_to_lecun hub=lecun key=/tmp/new_key address=192.0.2.20
case=none no_tunnel
case=multiple marker=.tunnel_to_lecun hub=lecun key=/tmp/first_key address=192.0.2.20
```

| # | 偽の家の目印 | 実測 |
|---|---|---|
| 1 | 旧形式 `.tunnel_to_philip` | `hub=philip address=philip`。旧目印名と SSH 別名を維持 |
| 2 | 新形式 `.tunnel_to_lecun` | `hub=lecun address=192.0.2.20`。名前と住所を目印から導出 |
| 3 | 目印なし | `no_tunnel` |
| 4 | lecun と philip の二つ | 辞書順で lecun の一件を選択 |

偽の HOME は正確なパスを指定して削除し、次を確認した。

```text
removed
```

### 変更後のプロセス数

変更前と同じ自己一致除外付き `/proc/*/cmdline` 走査の生出力。

```text
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
```

変更前から増減は無く、試験中に中継を張っていない。

### 稼働中の実体と本物の目印

```text
keeper path=/home/ubuntu/bin/keeper.sh size=2250 mtime=2026-07-04 07:17:08.974760455 +0000
marker path=/home/ubuntu/.tunnel_to_philip size=43 mtime=2026-07-03 23:36:05.625355038 +0000
2250 /home/ubuntu/bin/keeper.sh
-rwxrwxr-x 1 ubuntu ubuntu 2250 Jul  4 07:17 /home/ubuntu/bin/keeper.sh
-rw-rw-r-- 1 ubuntu ubuntu 43 Jul  3 23:36 /home/ubuntu/.tunnel_to_philip
```

サイズと更新時刻は Phase A と一致する。稼働版と本物の目印は変更していない。

### 変更後の中心関連箇所

```text
7:resolve_tunnel() {
8:  TUNNEL_MARKER=
9:  for candidate in "$HOME"/.tunnel_to_*; do
11:      TUNNEL_MARKER=$candidate
15:  [ -n "$TUNNEL_MARKER" ] || return 1
17:  HUB_NAME=${TUNNEL_MARKER##*/}
18:  HUB_NAME=${HUB_NAME#.tunnel_to_}
19:  TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
20:  HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
21:  [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
22:  [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
31:  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
33:  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
34:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
37:      ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
count=15
```

変更前より該当行数が増えたのは、中心を導出する汎用変数と解決関数を追加したためである。固定中心名と旧住所の一致は 0 件である。

### G2

PASS。四対照はすべて期待どおりで、構文検査に合格し、中継数・稼働版・本物の目印は変更前と一致した。
