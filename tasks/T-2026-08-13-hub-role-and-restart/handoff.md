# Handoff — hub配置・再起動・復旧手順

この文書は次の実行契約用である。本契約では以下を一つも実行していない。

## 1. 結論と順序

1. **lecunを最初に更新する。** 新keeper、目印なし、Syncthing 22000待受、keeper 1件、
   flock保持を確認する。
2. efrosまたはbengioのうち、現地preflightで鍵指紋・旧中継・ローカル操作経路が揃う一台を
   canaryにする。両者の優先順位は実装からは決まらないため `UNKNOWN`。
3. canaryで新keeper、新目印、新中継、Syncthing接続、双方向ファイル到達を確認する。
4. 残りの一般ノードを一台ずつ更新する。**一台の全確認が終わるまで次を触らない。**
5. 各ホストの `.sync-pause` は、そのホストの報告・pushが終わった後にだけ解除する。

根拠は正本 `scripts/sync/keeper.sh` の31–38行（目印と中継だけの分岐）、39–50行
（目印と独立したSyncthing監視・同期設定反映・m2-sync実行）、および
`m2-sync.sh` の中継参照0件である。

## 2. 全ホスト共通の停止条件

- keeper、m2-sync、marker、authorized_keysの開始時SHA-256を採れない。
- keeper PIDを `/proc` から一意に同定できない、または2件以上ある。
- 一般ノードで使用予定の秘密鍵から導出した公開鍵指紋が、lecun登録済み指紋と一致しない。
- markerが2件以上ある、または対象外markerの意味を説明できない。
- 中心の22000 LISTENが無い。
- 控えのSHA-256が原本と一致しない。
- local consoleまたは独立した復旧経路が無い。

上記はいずれも**変更前に停止**する。

## 3. lecun（中心）の手順

### 3.1 事前の記録

- `~/bin/keeper.sh`、`~/bin/m2-sync.sh`、全 `.tunnel_to_*`、`~/.ssh/authorized_keys`、
  `.stignore` の行数・mode・SHA-256。
- keeper、m2-sync、syncthing、`ssh -N -L` のPID・PPID・cmdline・起動tick・件数。
- keeperのFD9 lock、FD255のinode/SHA-256。
- `/proc/net/tcp*` の22000、22001、50072、8384 LISTEN。
- `git status --porcelain` と現在分岐。同期作業用 `.sync-pause` の存在。

現タスクの基準はkeeper `603a6c...e503`、m2-sync `bcf46b...25f`、
旧marker `e179ab...1f46`、authorized_keys `4e861b...d9db`、keeper 1、
syncthing 2、中継0である。次契約では必ず再測定し、この値を固定前提にしない。

### 3.2 控え

- `~/bin/keeper.sh` をmode込みで `~/bin/keeper.sh.before.T-2026-08-13-hub-migration` へ複製する。
- 全 `.tunnel_to_*` を、globに一致しない
  `~/.hub-migration-backup.T-2026-08-13/` へmode込みで複製する。
- 控えと原本のSHA-256一致、控え件数、modeを確認する。
- 削除ではなく移動で切り替え、復旧可能性を保つ。

### 3.3 配置と目印

1. `origin/phase0:scripts/sync/keeper.sh` を契約専用の一時パスへ展開する。
2. Git objectのblob、展開物、期待正本のSHA-256を三者照合する。
3. 展開物をmode `755` にし、`~/bin/keeper.sh` へatomic renameする。
4. lecunでは全 `.tunnel_to_*` をバックアップディレクトリへ移す。新markerは作らない。
5. この時点で `~/bin/keeper.sh` は新版だが、旧PIDは旧FD255で走り続ける。

### 3.4 再起動

1. `/proc` から旧keeperを一意に再同定し、開始時PIDとcmdlineが一致することを確認する。
2. 広域 `pkill` は使わず、その数値PIDだけへTERMを送る。
3. `/proc/PID` 消滅と `.keeper.lock` の非待機取得成功を待つ。期限内に消えなければ停止し、
   KILLを使うかは別の明示判断にする。
4. `nohup ~/bin/keeper.sh >/dev/null 2>&1 &` で一度だけ明示起動する。
5. `.zshrc:56` との競合があってもflockで片方がexitする。最終的にkeeper 1件でなければ失敗。

### 3.5 成功確認

- keeper 1件、PPID 1、FD9にWRITE flock、FD255のSHA-256が配置版と一致。
- `.tunnel_to_*` 0件、`ssh -N -L 22001:127.0.0.1:22000` 0件。
- syncthing件数が開始時と一致し、22000がLISTEN。
- m2-syncの一周目が実行される。`.sync-pause` 中なら「一時停止中」記録でよく、
  Git書き込みがないことを確認する。
- keeper、marker、processの結果をcommit前のauditへ保存する。

### 3.6 戻し方

1. 新keeperの数値PIDだけへTERMし、PID消滅とlock解放を確認する。
2. 新 `~/bin/keeper.sh` を失敗版として別名へ移す。
3. 控えをmode込みで `~/bin/keeper.sh` へ戻し、開始時SHA-256と一致させる。
4. 控えた `.tunnel_to_philip` を元の場所へ戻す。
5. 旧keeperを明示起動し、keeper・syncthing・中継の件数と全SHA-256が開始時へ戻ったことを確認する。

## 4. 一般ノードの手順

各ノードのlocal consoleで、一台ずつ実行する。lecunから一括投入しない。

### 4.1 事前の記録と鍵の照合

- 3.1と同じSHA-256、mode、PID、lock、LISTENを記録する。
- marker一覧を先頭ドットを含めて列挙し、件数を出す。
- 旧markerの1行目から鍵パス、任意2行目から住所を読む。秘密鍵本文は出力しない。
- 使用予定鍵から公開鍵を標準出力へ導出し、そのまま`ssh-keygen -lf -`へ渡す。
- 導出指紋がlecunの `authorized_keys` に登録された当該ノードの指紋と1件一致することを確認する。
- 既存指紋を陽性対照、存在しない指紋を陰性対照にして照合器を検証する。

一致しない場合はmarkerを作らず停止する。

### 4.2 控えとstaging

- 現行keeperと全markerを、ホスト名・task ID付きのglob非一致バックアップへmode込みで保存する。
- `origin/phase0` のkeeperを一時パスへ展開し、Git blobとのSHA-256一致後にmode `755` とする。
- 新markerの一時ファイルは1行目に照合済み鍵の絶対パス、2行目に
  `192.168.196.176` を書き、mode `600` とする。
- 一時markerは `.tunnel_to_*` に一致しない名前にする。

### 4.3 切り替えと再起動

1. 新keeperを `~/bin/keeper.sh` へatomic renameする。
2. 旧keeperの数値PIDだけへTERMし、PID消滅とlock解放を待つ。
3. 旧SSH中継の数値PIDとcmdlineを再確認し、そのPIDだけへTERMする。
4. local 22001のLISTENが消えたことを確認する。
5. 旧 `.tunnel_to_philip` をバックアップディレクトリへ移す。
6. 一時markerを `~/.tunnel_to_lecun` へatomic renameする。
7. `nohup ~/bin/keeper.sh >/dev/null 2>&1 &` で新版を一度だけ明示起動する。

**旧中継の終了は必須。** 正本33行の`pgrep`は接続先を区別しないため、旧中継が残ると
新keeperはlecun向け中継を起動しない。

### 4.4 成功確認

- keeper 1件、FD9 lock、FD255 SHA-256が正本一致。
- markerは `.tunnel_to_lecun` 1件だけで、2行、mode 600。鍵指紋を再照合。
- SSH cmdlineは `-L 22001:127.0.0.1:22000`、port 50072、接続先lecunだけを含む。
- local 22001がLISTENし、旧philip接続先を含むSSH processは0件。
- Syncthing接続情報で対象deviceがconnectedとなり、接続先アドレスを記録する。
- 下記の双方向プローブを通す。

### 4.5 戻し方

1. 新keeperの数値PIDだけへTERMし、lock解放を確認する。
2. lecun向けSSH中継の数値PIDだけへTERMし、22001解放を確認する。
3. 新markerを失敗版としてglob非一致名へ移し、旧markerを控えから元の名前・modeで戻す。
4. 新keeperを失敗版として別名へ移し、旧keeperを控えから元のSHA-256・modeで戻す。
5. 旧keeperを明示起動し、旧中継、keeper、syncthing、全SHA-256が開始時へ戻ったことを確認する。

## 5. 疎通確認の強さ

| 確認 | 示すこと | 示さないこと |
|---|---|---|
| keeper 1件・FD255正本hash・flock | 新keeperが一意に常駐 | 中継・Syncthingの通信成功 |
| SSH中継processとlocal 22001 LISTEN | SSHが起動しlocal forwardをbind | 中心22000到達、Syncthing認識、ファイル到達 |
| center SSH 50072への鍵認証 | 公開鍵登録とSSH入口が有効 | port forward先22000、Syncthing、ファイル到達 |
| lecunの22000 LISTEN | 中心Syncthingが入口を開いている | 一般ノードからの経路・認証 |
| Syncthingでdevice connected | Syncthing sessionが成立 | 対象ファイルがignore外で最新まで複製済み |
| m2-syncログ更新 | Git同期ループが動いた | SSH中継・Syncthingデータ同期 |
| 一方向ファイルの同一SHA-256 | その向きのwatch・ignore・転送・書込みが通った | 逆方向、必ず新中継を通ったこと |
| 双方向ファイルの同一SHA-256＋接続先記録 | 双方向データ面と観測した接続が同時に成立 | 将来の継続稼働 |

## 6. 最も強いファイル到達試験

1. ノード名とtask IDとランダムnonceを含むroot直下の小さな `.pt` を一般ノードで作る。
2. 作成前に `git check-ignore -v` が `.gitignore:46:*.pt` を返すことを確認する。
3. `.stignore:57` の `!*.pt` と末尾68行の `**` を記録する。
4. sourceでバイト数とSHA-256を固定し、lecunの同じ相対パスに到着するまで期限付きで待つ。
5. lecunでバイト数とSHA-256一致を確認する。
6. 別名・別内容の `.pt` をlecunから一般ノードへ送り、逆方向も同様に確認する。
7. 同時刻のSyncthing接続情報で対象deviceと接続先を記録する。
8. プローブの保持・削除は次契約で明示する。無断削除しない。

現タスクで予定名 `hrr-probe.pt` は `git check-ignore -v` が
`.gitignore:46:*.pt`、exit 0を返した。プローブ自体は作成していない。

## 7. 失敗様式と復旧

| 失敗 | 症状 | 検出方法 | 戻し方 |
|---|---|---|---|
| 配置物破損・mode不正 | keeperが起動しない | FD255不在、SHA不一致、process 0 | keeper控えをrestoreし再起動 |
| 旧keeperが残る | 新keeperがflockで即終了 | 旧PID継続、FD255 hashが旧版 | 旧PIDだけTERM、lock解放後に新版起動 |
| 旧中継が残る | 新中継が起動しないか旧hubへ流れる | SSH cmdlineに旧接続先、正本33行のpgrep成立 | keeper停止後、旧SSH PIDだけTERMして再起動 |
| marker名・行・鍵が誤り | SSHが即終了、22001不在 | marker三検査、指紋、`.tunnel.log` | 新markerを退避し旧markerをrestore |
| lecun SSH認証失敗 | tunnel processが残らない | 50072認証exitとログ | 一般ノードをrollback。authorized_keysは別契約で修正 |
| lecun 22000停止 | SSHは生きてもSyncthing接続なし | lecun `/proc/net/tcp*`、device state | 先にlecunをrollbackまたはSyncthingを復旧 |
| `.sync-pause` 解除忘れ | m2-syncが毎周回「一時停止中」 | sync-alerts.log | 報告後にmarkerを契約専用名へ退避 |
| 双方向probe不一致 | processは正常でも実データが届かない | path・size・SHA-256 | 次のノードへ進まず、その一台だけrollback |
| 全台同時停止 | 遠隔復旧不能 | 複数台でkeeper/中継0 | lecunをlocal consoleで先に確立し、一台ずつgateする |

## 8. 全台断を避ける運用gate

- lecunのlocal consoleを保持したまま中心を最初に完了させる。
- 一般ノードは一台だけ変更し、他の三台は開始時状態のまま残す。
- keeper一意性、中継接続先、Syncthing device、双方向probeが全てpassするまで次へ進まない。
- rollback手順と控えのhashを、変更前にそのホストで検証する。
- remote sessionだけを復旧経路にしない。session断時に使えるlocal/out-of-band経路を先に確認する。
