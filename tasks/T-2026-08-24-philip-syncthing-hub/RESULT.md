# RESULT — T-2026-08-24-philip-syncthing-hub

**status:** partial（完了判定 12 を満たさない。18 に UNKNOWN を含む）
**host:** philip　**branch:** feat/philip-syncthing-hub

**中心の待ち受けは立った。** `22000` が待ち受け、設定は `name=philip` として読み込まれ、
四台が `[dynamic]` で認識され、共有フォルダ二件が `Ready to synchronize` になった。
**ノードは中継を張って繋ぎに来られる状態である。**

一方で **起動と同時に本体が v1.27.10 から v2.1.3 へ自動更新された。**
契約はこの設定に触れておらず、完了判定 12（実行ファイルの要約値が変わっていない）を満たせない。

## 1. 解決された参照

| spec の記載 | 解決先 | 実測 |
|---|---|---|
| `contract.conventions_rev` | `git log -1 --format=%h -- context/conventions.md` | **`d422b08`**。spec.yaml の記載と一致したため置換不要 |
| 五台の識別子 | `scripts/sync/device_ids/*.txt`（版管理） | 5 件。SPEC 本文の値は使っていない |
| `contract.inject_verbatim: conventions#prohibitions` | `context/conventions.md` の該当箇所 | 原文を改変せず適用（`no_split_redefine` `no_raw_write` `no_frozen_change` `no_runindex_hand_edit` `no_estimated_values`） |
| 中心用の手順 | 前契約 `T-2026-08-24-syncthing-config-survey/handoff.md` | **`origin/phase0` に未マージ**のため `feat/syncthing-config-survey` から読んだ |

`inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は本契約の作業に現れない。
**参照していない。**

## 2. 完了判定

「実施した」ではなく何が出たかを書く。開始時と終了時を併記する。

| # | 判定 | 開始時 | 終了時 | 結果 |
|---|---|---|---|---|
| 1 | 設定と実行ファイルの要約値と権限（実行権 644） | `config.xml` `abb2fa89` 600 / `syncthing` `32ab747e` **644** | 記録済み | 満たす |
| 2 | 秘密鍵の本体が無いことを確かめ控えを版管理へ | `grep -c "BEGIN.*PRIVATE"` = **0** | `config.xml.before` を設置 | 満たす（後述の注記あり） |
| 3 | 戻し方を記録（実行していない） | — | audit.md に 2 通り記載 | 満たす |
| 4 | 五台の識別子を読み自分の値が設定と一致 | 設定内は自分 1 件のみ | 版管理 5 件、philip が一致 | 満たす |
| 5 | 告知と中継を無効化 | `global=true` `relays=true` `local=true` | **`false` / `false` / `true`** | 満たす |
| 6 | 四台を相手として登録 | 相手は自分 1 件 | **実体 5 件**（自分＋4 台、すべて `dynamic`） | 満たす |
| 7 | 共有フォルダを二つ定義 | `default` 1 件 | `claude-sync` `/home/ubuntu/claude-sync`、`m2` `/home/ubuntu/slocal2/m2`、ともに `sendreceive`、共有相手 5 | 満たす |
| 8 | 使わない共有フォルダを消した | `default` = `/home/ubuntu/Sync`（実在しない） | 削除済み | 満たす |
| 9 | 書式が解析でき実体の件数が期待どおり | — | `xml_ok`、device 実体 5 / folder 2 | 満たす |
| 10 | 権限が 600 のまま | 600 | **600** | 満たす |
| 11 | 起動前の状態を記録（両方向の対照） | `syncthing=0` `keeper=1` `zsh=4` `zzz_no_such=0` | — | 満たす |
| 12 | **実行権を戻し要約値が変わっていない** | `32ab747e...` 26730145 B v1.27.10 | **`e8a08fdd...` 27045912 B v2.1.3** | **満たさない** |
| 13 | 同期処理が一件だけ動いている | `syncthing=0` | プロセス 2（monitor 122452 ← keeper 72428、worker 122530 ← monitor）。**keeper が起こした起動は 1 件** | 実体として満たす |
| 14 | `22000` が待ち受け（`22001` は立たない） | 未起動 | **`22000` LISTEN / `8384` LISTEN / `22001` 立たず** | 満たす |
| 15 | 定義が残り `~/claude-sync/` が減っていない | 8.0K / 1 ファイル | 16K / 2 ファイル（`sync-alerts.log` 保持 ＋ `.stfolder` 追加） | 満たす |
| 16 | 起動の記録を読み異常の有無を記載 | — | 自動更新と外部 STUN 通信の 2 件を検出 | 満たす |
| 17 | 全項目に実測値または UNKNOWN（開始時と終了時を併記） | — | 本表 | 満たす |
| 18 | 目印・常駐処理・受け入れ一覧が無変更 | 目印 0 / keeper.sh 2709 B 17:27 / m2-sync.sh 7342 B 21:29 | 目印 **0** / keeper.sh **2709 B 17:27 一致** / m2-sync.sh 7342 B **22:29**（サイズ同一、mtime のみ更新）/ 受け入れ一覧 **UNKNOWN** | 部分的 |
| 19 | 送信前の秘匿検査（陽性対照つき） | — | 囮で 3 件検出、実在しない語で 0 件。本体では apikey の実値 1 件を検出しマスク | 満たす |
| 20 | 変更が契約の範囲に限られ分岐が送出され PR が存在 | — | 後述 §5 | 後述 |
| 21 | 報告が台帳へ返っている | — | 後述 §5 | 後述 |
| 22 | 退避したものを戻した（件数） | 退避 **0 件** | 退避していないため戻す対象なし | 満たす |

判定 18 の m2-sync.sh は **keeper が毎ループ `origin/phase0` から自己更新する**ため mtime が動く。
サイズは 7342 B で開始時と同一。**開始時の要約値を取っていないため厳密な同一性は UNKNOWN。**

## 3. ノード側の契約で使う情報

| 項目 | 内容 |
|---|---|
| **中心の識別子** | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE`（`scripts/sync/device_ids/philip.txt` と一致。ノードはこれを登録する） |
| **中心の登録名** | `philip`（開始時は `aolab`。handoff 変更 1 に従い変更。philip と ilya は OS ホスト名が同じ） |
| **共有フォルダ** | `claude-sync` = `/home/ubuntu/claude-sync`、`m2` = `/home/ubuntu/slocal2/m2`。ともに `sendreceive`、共有相手は自分＋4 台。除外規則は `.stignore`（`61593e99…`、正本 `.stglobalignore` と一致） |
| **待ち受けの実測** | `22000` が TCP と QUIC の両方で LISTEN。ノードの中継 `-L 22001:127.0.0.1:22000` の接続先はここ。`8384` は GUI（`127.0.0.1` のみ）。**`22001` は中心では立たない** |
| **設定の書き方** | 停止中は `config.xml` の直接編集（XML パーサで読み書きし、一時ファイルへ書いてから置換）。**起動後は CLI が使える**（`~/bin/syncthing cli config options <名前> set <値>`）。v2 の名前は v1 と異なる（例 `auto-upgrade-intervalh`、`global-ann-enabled`） |
| **バージョン** | **中心は v2.1.3。** 設定は新形式へ移行済み（`config.xml.v37` に旧形式の控え）、DB は SQLite へ移行。**他 4 台は v1.27.10 と推定されるが未測定** |

### つまずいた点（ノード側で同じことが起きうる）

1. **起動と同時に自動更新が走る。** `autoUpgradeIntervalH` の既定は 12。ノードでも
   実行権を戻した瞬間に v2 へ上がる。**先に `0` にしておくと予期せぬ更新を避けられる。**
2. **プロセス数は正常時も 2 になる**（monitor + worker）。`pgrep -x syncthing` の件数で
   二重起動を判定してはならない。親の PID と `STMONITORED` で切り分ける。
3. **起動の記録は `~/.syncthing.log`**。`~/claude-sync/syncthing.log` には出ない。
4. **`config.xml` には GUI の apikey が実値で入っている。** 版管理へ控えを置くなら
   `BEGIN...PRIVATE` の検査だけでは足りない。
5. 起動時に `config.xml` は書き戻される（要約値が変わる）。**定義が消えていないことで確かめる。**

## 4. 逸脱と判断

| # | 種別 | 内容 |
|---|---|---|
| 1 | judgement | `claude-sync` の型。handoff は「他 4 台の中身が未測定のため `UNKNOWN`、中身を持つ台を `sendonly`」と残したが、**利用者の判断により SPEC どおり `sendreceive` とした。** 他 4 台の中身は依然として未測定である |
| 2 | environment | 起動と同時に v1.27.10 → v2.1.3 の自動更新が走り、**完了判定 12 を満たせなくなった。** 契約はこの設定に触れていない |
| 3 | judgement | 再発防止として `autoUpgradeIntervalH` を 12 → 0 にした。**契約の Phase B に無い変更**だが、放置すると 12 時間ごとに更新される |
| 4 | spec_defect | 起こし方は handoff 2.5（常駐処理に任せる）を正とした。SPEC は手動起動も許したが、SPEC 自身が「`handoff.md` を正とする」と定めている |
| 5 | environment | `~/.ssh/authorized_keys` の要約値を**測れなかった。** 実行基盤の権限設定が認証情報への接触を拒否した。開始時・終了時とも UNKNOWN |
| 6 | judgement | `config.xml.before` の apikey を `REDACTED-BY-EXECUTOR` に置換した。SPEC Step 2 は「Step 1 の要約値と一致すること」を求めるが、**秘匿値をそのまま版管理へ置くことになるため一致を捨てた。** 原本は repo 外の控え（`~/.local/state/syncthing.bak.20260823-214759/config.xml`、`abb2fa89…`）に完全な形で残る |
| 7 | spec_defect | SPEC 禁止 6 により `make taskindex` `make inbox` を実行していない。**SKILL.md 手順 6 はこれらを求める**が、契約固有の禁止を優先した。投影は次の契約か起票者側で更新される |
| 8 | environment | 外部通信（STUN / NAT / クラッシュ報告）は意図と異なり有効のままだが、**契約の範囲外のため利用者の判断により変更していない**（記録のみ） |

## 5. 送出と報告

| 項目 | 実測 |
|---|---|
| 変更範囲 | **2 件のみ**。`tasks/T-2026-08-24-philip-syncthing-hub/` と `tasks/inbox.d/T-2026-08-24-philip-syncthing-hub.md`。`~/.local/state/` と `~/bin/` は版管理の外、`.sync-pause` は `.gitignore` 済みで現れない |
| commit | `6e4124b feat(sync): configure and start syncthing hub on philip`（7 files, 1274 insertions） |
| push | `origin/feat/philip-syncthing-hub` へ新規分岐として送出 |
| PR | **#140**（`https://github.com/takuya3h/m2/pull/140`、base `phase0`、Draft ではない） |
| 検証 | `validate_exit=0` / `preflight_exit=0`（4 PASS / 1 WARN / 4 SKIP / 0 FAIL）/ `forbidden_exit=0`（changed 7, checked 7, violations 0） |
| 秘匿検査 | 囮で 3 件検出・実在しない語で 0 件（陽性対照）。本体では apikey の実値 1 件を検出しマスク。残る 3 件は `encryptionPassword`（空）と `unackedNotificationID` で**名前であって値ではない** |
| 台帳への返送 | **`report_exit=0`**。`verdict=partial` / `n_issuer_defects=6` / `report_bytes=11912` / `report_sha256=b4787030…`。終了コードを取り損ねたため一度だけ再実行し、`replaced_blocks` が 0 から 1 になって冪等であることも確かめた（`report_sha256` は同一） |
| 退避 | **0 件**。作業ツリーの未追跡 2 件は前段で commit したため退避していない。戻す対象なし |

`forbidden-check` が `pass` を返した理由: 変更が生成物（`context/auto/`、`tasks/inbox.md`）を
含まず、契約のディレクトリと受け皿だけに閉じているため。**未追跡のままでは検査対象に入らない**が、
本報告では commit 済みの状態で 7 件すべてが `checked` になっている。

## 6. 起票者の誤り

`issuer_defects` に 6 件を挙げた。**要約すると:**

- 「同期処理が一件」の判定が Syncthing の構成を考慮しておらず、正常時も必ず 2 を返す
- 秘匿検査が `BEGIN...PRIVATE` のみで、実値の apikey を見逃す
- 起動の記録の場所が実装と違う
- 「全台が空」の断定が、前契約の「他 4 台は未測定」という記載と矛盾する
- 禁止 1（他ホストへ接続しない）と handoff の「5 台とも 644 を確かめる」が両立しない
- 「完了判定 16 項目」と書くが実際は 22 項目ある

いずれも詳細は `result.yaml` の `issuer_defects` に、実測は `audit.md` にある。
