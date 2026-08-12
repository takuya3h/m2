# RESULT — T-2026-08-12-ilya-hub-feasibility

**ilyaを中心に据えられるかの実測**  
ホスト `aolab`（契約上 ilya）/ 分岐 `feat/ilya-hub-feasibility` / 実行日 2026-08-12

生出力は `audit.md` に記録した。本契約では鍵・設定・常駐処理・中心を変更していない。

## 結果

ilyaの受け入れ一覧は2件で、目標4台を直接示す注釈は0件だった。契約の判定規則では
efros・lecun・bengio・andrewの4台すべてに登録が要る。

入られる側の局所機能は動いている。SSHはコンテナ内22番、Syncthingは22000番でLISTENし、
Syncthingは2プロセス、keeperは1プロセスだった。外から見えるilyaの住所とSSH番号は
自ホストから測れないためUNKNOWN。

過去2回の「ilyaは構内へ出られない」は今日の値と食い違った。他ノード10台のうち、philipを
除く9台の50072番はOPENで、目標4台もすべて含む。philipだけは22000番が
`No route to host`、50072番がTIMEOUTだった。外向きGit経路もexit 0。

## 完了判定21項目

| # | 完了判定 | 実測値 |
|---:|---|---|
| 1 | 受け入れ一覧の場所と行数 | 既定2候補を確認。実在は `~/.ssh/authorized_keys`、空でない行2件 |
| 2 | 指紋と注釈 | 2件。`dakyo-mba@dmba.local` / `ubuntu@aolab`。鍵本文なし |
| 3 | 目標4台の受け入れ | efros・lecun・bengio・andrewはいずれも直接の注釈なし。各台「登録が要る」 |
| 4 | 手元の鍵と中継目印 | `.tunnel.log` / `.tunnel_to_philip` の2件。SSHディレクトリは名前・属性だけを記録 |
| 5 | 記録に秘匿値なし | 説明語のみ検出。囮の秘密鍵ヘッダーは1件検出 |
| 6 | 待ち受け復号 | ポート集合7件。22・22000・8384はLISTEN。陽性対照 `True→False` |
| 7 | SSHの口 | コンテナ内22番LISTEN。外から見える番号はUNKNOWN |
| 8 | 同期処理 | Syncthing=2、keeper=1、不存在対照=0、22000番LISTEN |
| 9 | 自ホスト住所 | コンテナ内 `172.17.0.14`、hostname `aolab`。外から見える住所はUNKNOWN |
| 10 | 対象一覧 | SSH設定・hosts・Syncthing設定から収集。直接deviceは11台、目標4台を含む |
| 11 | 到達性の分類合計 | 10台×2ポート=20。OPEN 9 + REFUSED 9 + 経路なし2 = 20 |
| 12 | 今日の構内到達性 | 9台の50072番へ到達。過去2回の「出られない」と食い違う。philipのみ経路なし |
| 13 | 外向き経路 | `refs/heads/phase0` が返りexit 0 |
| 14 | known_hosts前後比較 | サイズ1956・mtime `2026-08-03 22:14:59.236043451 +0000`で同一。隔離先9行 |
| 15 | 判定1–14の空欄 | 0。測れない外部番号・住所はUNKNOWN |
| 16 | 中心要件表 | 下表に記載。中心にすべきかの判断は記載しない |
| 17 | 変更範囲 | 契約ディレクトリ、判断受け皿、上位指示の `tasks/todo.md`、抑止目印だけ |
| 18 | 分岐送出 | UNKNOWN（後続Stepで更新） |
| 19 | PR | UNKNOWN（後続Stepで更新） |
| 20 | 同期抑止解除 | UNKNOWN（報告直前の後続Stepで更新） |
| 21 | 台帳報告 | UNKNOWN（後続Stepで更新） |

## 中心の要件

| 要件 | 実測 |
|---|---|
| efrosがilyaへ入れるか | 受け入れ注釈に直接該当なし。登録が要る |
| lecunがilyaへ入れるか | 受け入れ注釈に直接該当なし。登録が要る |
| bengioがilyaへ入れるか | 受け入れ注釈に直接該当なし。登録が要る |
| andrewがilyaへ入れるか | 受け入れ注釈に直接該当なし。登録が要る |
| SSHの口 | コンテナ内22番LISTEN。外から見える番号はUNKNOWN |
| 同期処理の局所待ち受け | Syncthing=2、22000番LISTEN |
| 追加登録が要る台数 | 4 |

## 陽性対照

| 判定 | 壊す入力 | 実測 |
|---|---|---|
| LISTEN復号 | 一時ソケットを開閉する | 開いている間`True`、閉じた後`False` |
| 到達性三分類 | OPEN先・閉じた先・経路のない先を与える | `OPEN` / `REFUSED` / `OSERROR:Network_is_unreachable`。amendment後の三分類と一致 |
| プロセス計数 | 存在しない語を数える | `zzz_no_such_process=0`。自分と祖先は除外 |
| 秘匿検査 | 秘密鍵ヘッダー型の囮を与える | 囮1件を検出。本文の一致は説明語だけ |
| known_hosts無変更 | 未知ホストへaccept-newで接続する | ホスト鍵9件は `/tmp/kh_audit.txt` のみ。禁止領域はサイズ・mtime同一 |
| 外向き経路 | originが不通なら参照が返らない | phase0の参照が返りexit 0 |

## 逸脱と契約修正

- 当初の陽性対照は経路なしを`TIMEOUT`だけに限定していたが、ilyaではカーネルが
  `Network_is_unreachable`を即時に返した。一度停止し、ユーザー承認後に両者を同値な
  経路なし分類とするamendmentを追加して再開した。
- 三出所の一覧を使い、既存監査と同じく他ノード10台の22000番と50072番の計20組を測った。
- 上位指示に従って`tasks/todo.md`へ計画を追記し、Codegraphを初期化した。
  `.codegraph`は自身のgitignoreにより差分へ入らない。このCLI版には`watch`がないため、
  編集後に`codegraph sync`を実行した。

## 起票者の誤り

当初契約は、経路のない`192.0.2.1`への接続が必ず`TIMEOUT`になると実測前に固定し、
それ以外なら停止するよう指示していた。実際のilyaでは`OSERROR:Network_is_unreachable`が
返り、指示どおり停止すると、測定器が経路なしを正しく即時判定しているにもかかわらず
本対象を測れない。ユーザー承認のamendmentで修正した。

## UNKNOWN

- 外部から見えるilyaの住所とSSHポート。
- `ubuntu@aolab`注釈がilyaとphilipのどちらに由来するか。
- 受け入れ鍵の注釈が実際の所有ホストと一致するか。相手側指紋との照合はしていない。
- philipが到達不能な理由。実測は`No route to host` / `TIMEOUT`まで。

`contract.conventions_rev`の実測は `d422b08` で、契約記載と一致した。

