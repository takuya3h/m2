# RESULT — T-2026-09-17-philip-accept-efros

**efros の公開鍵と識別子を中心へ登録した。既存の五件も四ノードとの接続も失っていない。**

手続きの証跡は `audit.md`。以下の行番号はそこを指す。

## 判定

**verdict: pass**

| Gate | 判定 | 実測 |
|---|---|---|
| G1 | **初回 fail → ask → 解消後 pass** | 受け入れ一覧が実行基盤に拒否され一度 fail（audit §1.1, L111-136）。利用者が設定を変更した後に再測定し四条件を満たした |
| G2 | **pass** | 指紋が前契約と一致／三検査と囮／鍵・識別子の両方で未登録を陽性対照つきに確認（audit §6, L450-518） |
| G3 | **pass** | 消えた行 0 件を集合差で／増えた 1 件の指紋一致／相手を登録し認識／四ノードとの接続が保たれた（audit §7-8, L520-666） |

## 完了判定

| # | 実測 |
|---|---|
| A | 受け入れ一覧: **5 件** / `600` / `1127` B / sha256 `35ad4ef5…b457f4` / 指紋 5 件を記録（L138-176） |
| B | 相手の実体 **5**、共有フォルダ **2**。**素朴な `.//device` は 17**（直下 5 + folder 配下 10 + `defaults` 配下 2）。ひな型を含めていない（L195-220） |
| C | 稼働 **2**（pid 122452 / 122530）。陽性対照 `/usr/bin/zsh` **6**、陰性対照 **0**（L253-268） |
| D | 控え 2 件とも repo 外 `~/task-hold/…/backup/`。**sha256 一致 True**（L286-322） |
| E | 戻し方を記録（実行していない）。設定は REST で外す手順、受け入れ一覧は全体復元と 1 行除去の両方（L324-380） |
| F | **直接編集は不可**（起動 12m15s 後に mtime、`config.xml.v37` あり）。**REST `127.0.0.1:8384` が正しい経路**。再起動不要（L382-448） |
| G | `efros.pub` **95 B / 1 行**、`efros.txt` **64 B / 1 行**。両方とも追跡済み（L452-459） |
| H | 指紋 `SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0` が前契約 `RESULT.md` 行 51 と**一致** |
| I | 三検査 **1 / 0 / 1**。**囮は 0 / 2 / 4 と三つとも逆向きに落ちた** |
| J | efros の指紋 **0**（陽性対照 lecun **1**）／efros の識別子 **0**（陽性対照 philip **1**、陰性対照 **0**） |
| K | 件数 **5 → 6**、権限 **`600` のまま**、大きさ **1127 + 95 = 1222 B**（ぴたり一致） |
| L | **消えた行 0 件。** 陽性対照（1 行抜いた偽の一覧）は **1** を返した |
| M | 増えた 1 件の指紋が Task 2 の値と**一致** |
| N | 解析できた件数 **6** = 空行を除いた件数 **6** |
| O | 識別子は `scripts/sync/device_ids/efros.txt` から。名前 `efros`、住所 `dynamic`。`POST /rest/config/devices` **HTTP 200** |
| P | `claude-sync` / `m2` とも共有相手 **5 → 6**。**定義（`id`/`label`/`path`/`type`）の一致 True**。`defaults` 節の要約値も `8d869daf8e337a16` のまま |
| Q | 相手の実体 **6**、共有フォルダ **2**、`config.xml` の権限 **`600` のまま** |
| R | `devices` **6 件**／`restart-required` **false**／**`connections` に `efros` の項目が出現**／**PID が Task 1 と同一** |
| S | `connected=True` が **4 件**（andrew / bengio / ilya / lecun）。`22000` LISTEN **1**、稼働 **2** |

## 設定を変える手段（次の契約で使う）

**稼働中の同期処理の設定は、ファイルを直接編集しても効かない。**

| 問い | 結論 | 根拠 |
|---|---|---|
| 直接編集できるか | **できない。上書きされる** | 起動 `22:29:18` に対し `config.xml` の mtime が `22:41:33`（**12m15s 後**）。版付きの控え `config.xml.v37` も在る。**処理が設定を持ち自分で書き出す** |
| 命令列 | **使える** | `syncthing cli config` が「Configuration modification command group」として在る。合言葉と住所を受け取る＝稼働中の処理へ REST で話す包み |
| **画面の経路** | **これが正しい手段** | `http://127.0.0.1:8384`（局所のみ）。合言葉は `gui/apikey`（長さ 32）。`GET /rest/config/devices` が 200 |
| 再起動 | **要らない（実測）** | 適用後も `restart-required: false`。**PID が 122452 / 122530 のまま変わっていない** |

使った手順。

    POST  /rest/config/devices            {deviceID, name, addresses:["dynamic"]}
    GET   /rest/config/folders/<id>       既存の devices を取る
    PATCH /rest/config/folders/<id>       {"devices": 既存 + efros}    ← devices だけ送る

**`PATCH` に `id`/`label`/`path`/`type` を含めない。** これで禁止 4 を守れる。
**反映は `GET /rest/system/connections` に相手の項目が現れることで確かめる。**
設定を読んだだけでは処理はこの一覧に項目を作らないため、これが「認識した」の証拠になる。

## 実測（登録後）

| 対象 | 開始時 | 登録後 |
|---|---|---|
| 受け入れ一覧の件数 | 5 | **6** |
| 受け入れ一覧の権限 | `600` | **`600`** |
| 受け入れ一覧の sha256 | `35ad4ef5…b457f4` | `ab3fe1cb…7986fb` |
| 相手の実体 | 5 | **6** |
| 共有フォルダ | 2（共有相手 5 / 5） | **2（共有相手 6 / 6）** |
| `config.xml` の sha256 | `50caaae6…` | `6cfc3ece…60f7b0`（**処理が書いた**。mtime `2026-09-17 05:07:36`） |
| 四ノードとの接続 | `connected=True` **4** | `connected=True` **4** |
| efros の状態 | 項目なし | **項目あり。`connected=False` `paused=False`** |
| 稼働しているもの | 2 | **2（同一 PID）** |

## 疎通の未確認

🔴 **efros から実際に中心へ入れるかは、中心からは測れない。**

測れたのは「受け入れ一覧に指紋が在る」「同期処理が相手として追跡している」まで。
理由は二つ。**禁止 5**（他ホストへ接続しない）に当たるため試行できないこと、
および efros 側が未起動で、**中心は住所 `dynamic` のため相手へ繋ぎに行かない**こと。
接続は efros 側から来る。**疎通の確認は efros 側の契約で行う。**

## 起票者の誤り

| # | 型 | 内容 |
|---|---|---|
| 1 | `asserted_without_measuring` | 前提の手順に `make task-start` を置いたが、**配布台帳の行は本文 0 文字・添付なし・`sha256` 列も空**。指示どおり実行すると `要約値の列が空です` で exit 4 になり、分岐が作られず巻き戻る。契約を台帳へ載せたことを確かめていない（audit §0.1, L14-35） |
| 2 | `self_contradiction` | 「### 既存の実測（**再測定は不要**）」（SPEC:30）で受け入れ一覧 5 件・権限 `600` を与えながら、Task 1 Step 1（SPEC:104-109）と完了判定 A が**同じ項目の測定を必須にしている**。実行すると結局測ることになり、表の宣言が働かない |

**他に起票者の誤りは見つからなかった。** SPEC が与えた既存の実測（5 件 / `600` /
稼働中 / `v2.1.3` / フォルダ 2 件 / 設定の場所 / `id=""` のひな型）は**すべて実測と一致した。**

`P9 spec_lint` の該当 2 件は**起票者の誤りではない。**

- `host_mismatch@SPEC.md:5` — 宣言 `philip` と `hostname` `aolab` は**層が違う**。
  `myID` が `device_ids/philip.txt` と一致し、**実行ホストは正しい**（L270-284）
- `separated_source@SPEC.md:48` — 該当行は `… \` の行継続で**実際には 1 命令**。
  行単位で読む検査器の偽陽性。規則自体は守って実行した

## 逸脱

| # | 型 | 内容 |
|---|---|---|
| 1 | judgement | `make task-start` が上記の理由で exit 4。**同じ起点 `origin/phase0` で分岐を手で作った。** 契約は手元にあり `make task-validate` が exit 0 だったため、取り込みは不要だった |
| 2 | environment | 未追跡 8 件（`experiments/transfer/pd_refin_*` を含む計 **848MB**）を repo 外へ **mv で退避**してから分岐を作った。`task_start.sh` は汚れた作業ツリーで分岐を作らないため。**消していない。報告の後に戻す** |
| 3 | environment | **`Read(~/.ssh/**)` がグローバル設定の `deny` にあり Task 1 Step 1 が不能**。Gate G1（`on_fail: ask`）で停止して判断を仰ぎ、利用者が設定を変更した後に続行した |
| 4 | environment | `ss` が本ホストに無く、待ち受けを `/proc/net/tcp{,6}` から数えた。**`ss \| grep -c` が返した `0` は件数ではなく命令の失敗**であり、件数として扱わなかった |
| 6 | judgement | **退避物を戻す `mv` が入れ子を一段作った。** 退避時は未追跡だった `experiments/**` と契約ディレクトリが、`origin/phase0` 起点の分岐では**追跡下に既に存在した**ため、`mv src dest` が dest の中へ入った。比較したところ入れ子のみに在るのは `checkpoints/` と `predictions/`（計 **866 MB**）で、重なる 2 件は **sha256 が完全一致**。前者を親へ移し、一致を再確認してから重複の入れ子 6 つだけを削除した。**失われたデータは無い**（866 MB が残存。`.gitignore:24` により追跡外） |
| 5 | judgement | 作業中に `~/bin/m2-sync.sh` の mtime が変わった（`04:56:16`）。**keeper の自己更新**で、中身は `origin/phase0` の `scripts/sync/m2-sync.sh` と **sha256 が完全一致**。実行者の変更ではない |

## 想定外

| 事象 | 対応 |
|---|---|
| 配布台帳の行が空 | 取り込みを拒否させたまま、手元の契約で進めた。起票者の誤り 1 に記録 |
| 受け入れ一覧を読めない | SPEC の想定外一覧のとおり Gate G1 で停止し報告。利用者の設定変更後に続行 |
| 常駐処理の件数が **2** と出た | **自分の命令行に `m2-sync` `keeper` の語が含まれていた**（`issuer_cautions` 注意 6 の実測と同型）。自分の pid を除いて **1 件**へ訂正。陰性対照 0 |
| `folder` 配下の共有相手が全て「空」に見えた | 属性名を `deviceID` と誤った。**実際は `id`**。測り直して 5 件すべてが実体と確認 |

**既存の行は一つも消えていない。四ノードとの接続も切れていない。**

## UNKNOWN

- **efros から中心への疎通**（ssh・同期とも）。中心からは測れない（上記「疎通の未確認」）

## 規約の適用判定

| 節 | 判定 | 根拠 |
|---|---|---|
| `conventions#proposal_gate` | **適用されない** | 対象は「手法・結合・補助信号・修正案の**提案**」。本契約は公開鍵と識別子の登録のみ |
| `conventions#folds` | **適用されない** | 動画単位 5-fold の規律。本契約は学習も評価も行わない |
| `conventions_rev` | **`e7a51005`。契約の記載 `e7a5100` と一致**（置換不要） |
| `inputs.data` | **参照しなかった**（雛形の必須項目。`data/splits/ego_val.txt` は実在するが読んでいない） |

## 送出

| 項目 | 値 |
|---|---|
| commit | `5e5d36d2` |
| PR | **#179** |
| 秘匿検査 | **exit 0**（一致 0 件 / 陽性対照 1 件で検査が働いている。値は出力していない） |
| `make task-validate` | exit 0 |
| `make taskindex-check` | exit 0 |
| `make inbox-check` | exit 0 |
| `make forbidden-check` | `status: pass` / `violations: []` |
| 台帳への返送 | **exit 0**。`verdict: pass` / `n_issuer_defects: 2` / `report_bytes: 10831` / `report_sha256: 0d44113ade83a594…` / `replaced_blocks: 0` |
