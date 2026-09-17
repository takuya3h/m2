# RESULT — T-2026-09-17-efros-syncthing-join

**実行ホスト** `efros` / **分岐** `feat/efros-syncthing-join` / **開始** 2026-09-17T15:57:31+09:00
手続きの証跡は `audit.md`（408 行）。以下は行番号で指す。

## 判定

**verdict: pass。efros は群れへ入った。六台目である。**

| Gate | 結果 | 実測の要点 | audit.md |
|---|---|---|---|
| G1 | **pass** | 実行権 600、目印 0 件、同期処理と中継 0 件。中心へ `ssh -N` で入れた | 12–107 |
| G2 | **pass** | 自動更新 12→0、告知と外部中継を無効、最上位フォルダ 2 件 | 115–166 |
| G3 | **pass** | 正本と配置物の sha256 が一致、`bash -n` が両方 0、抑止対応 2 件 | 170–218 |
| G4 | **pass** | 中継 `22001` 待ち受け、版が中心と同じ `v2.1.3`、自動更新 0 のまま | 224–337 |

## 完了判定

| # | 項目 | 実測値 |
|---|---|---|
| A | 開始状態 | 実行権 `600`、目印 **0 件**、syncthing **0**、中継 **0**（対照: 正 `zsh`=5 / 負 `zzz`=0） |
| B | 共有領域 | **0 bytes / 0 件**（`~/claude-sync/` が存在しなかった）。repo **68314468570 bytes / 234767 件** |
| C | `~/bin/` | **`syncthing` 1 件のみ**。keeper も m2-sync も無い |
| D | 控え | `~/.syncthing-config-backup-20260917-155900/`（repo 外、`stat -c %d` が双方 **233**） |
| E | 戻し方 | audit.md 69–86 に記録。**実行していない** |
| F | 中心へ入れた | `Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey"`。負の対照（口 50073）は `Connection refused` |
| G | 自動更新 | `options/autoUpgradeIntervalH` `12` → **`0`** |
| H | 告知と中継 | `globalAnnounceEnabled` `true`→`false`、`relaysEnabled` `true`→`false`、`localAnnounceEnabled` `true` のまま |
| I | 自分の登録名 | **初期値が既に `efros`。置換 0 件**（五台の `Bengio`/`Andrew`/`aolab` と違った） |
| J | 中心の登録 | 識別子は `scripts/sync/device_ids/philip.txt`、名前 `philip`、住所 `tcp://127.0.0.1:22001` |
| K | 共有フォルダ | `count(/configuration/folder)` = **2**（`claude-sync`, `m2`）。ひな型は 1、全階層は 3 |
| L | 書式 | `xmllint --noout` exit 0、最上位 device **2**、権限 `600` のまま |
| M | 要約値の一致 | keeper `9fe9c423…dd90`、m2-sync `bcf46ba9…e25f`。**正本と配置物が一致** |
| N | 構文検査 | `bash -n` = **0 / 0**。負の対照は **2** |
| O | 起動行 | **追記していない。`~/.zshrc` に既に在った**（`grep -c 'keeper.sh'` = 1、135–138 行） |
| P | 抑止 | `.sync-pause` を置いた。`grep -c sync-pause ~/bin/m2-sync.sh` = **2**（対応版） |
| Q | 目印 | `~/.tunnel_to_philip` 59 bytes、権限 `600`、2 行。`~/.tunnel_to_*` は **1 件** |
| R | 常駐処理 | **1 件**（PID 53967、PPID=1）。錠 `~/.keeper.lock` が作られた |
| S | 中継 | `22001` 待ち受け **2**（負の対照 `65533` は 0）。PID 53974 は keeper の子で引数に `ubuntu@192.168.196.150` |
| T | 実行権 | `600`→`700`。sha256 `e8a08fdd…96c4` は**前後で同一** |
| U | 同期処理 | **2 件**。PID **73191**（PPID=53967）→ PID **73210**（PPID=73191）。版 `v2.1.3` |
| V | 定義 | 最上位フォルダ **2 のまま**、`autoUpgradeIntervalH` **0 のまま**（`grep -ci upgrade` = 0） |
| W | 接続の記録 | `Established secure connection (device=3J4TRX4 connection.remote=127.0.0.1:22001 …)` 3 件 |
| X | 試験ファイル | `probe-efros.txt` sha256 `0055a45f…8900`、**77 bytes** |
| Y | 中心が持っている | `db/file` の `availability` に **`3J4TRX4-7ZOHQAY-…-DZOCQQE`**（版管理の `philip.txt` と一致）。`db/completion` = **100 / needItems 0**。負の対照は HTTP **404**、陽性は **200** |
| Z | 共有領域の増分 | **0 bytes / 0 件 → 2859815 bytes / 17 件**。五台の `probe-*.txt` **4 件**が届いた |
| AA | repo の進み方 | 16:43:34 `scanning` local 17654225337 → 16:45:41 `sync-preparing` local 44514451803 → **17:10:06 `idle` local 49228326381 / `needBytes` 0**。`du -sb` は **68314468570 → 73028668690**（**+4714200120 bytes が実際に届いた**）。**受け取りは完了した。中心への送り出しは 75.66% で進行中**（`needBytes=11983979383`） |
| AD | 禁止語 | SPEC・audit・RESULT に **0 件**。陽性対照（囮）は **2 件検出 / exit 1** |
| AE | 秘匿検査 | 後述 |
| AF | 送出 | 後述 |
| AG | 退避 | **退避していない**（分岐が既に在り、切る必要が無かった）。開始前からの未追跡 **2 件**は触れていない。**入れ子は作っていない** |

## 常駐処理を入れた手順（五台には無かった工程）

**次に同じことをするときはこの順で足りる。**

1. `git show origin/phase0:scripts/sync/keeper.sh > ~/bin/keeper.sh`（m2-sync.sh も同様）、`chmod 755`
2. `bash -n` で両方を検査する（誤りのまま起動すると即座に落ちる）
3. `~/.zshrc` の起動行を **`grep -c 'keeper.sh'` で数えてから**判断する。**本ホストは既に在った**
4. `touch .sync-pause`。`grep -c sync-pause ~/bin/m2-sync.sh` が 0 でないことを確かめる
5. 目印 `~/.tunnel_to_<中心>`（1 行目に鍵、2 行目に住所）、権限 `600`
6. `( nohup ~/bin/keeper.sh >/dev/null 2>&1 & )` で一度だけ起こす
7. **中継が立ってから** `chmod 700 ~/bin/syncthing`

**注意すべき点が 3 つあった。**

- **起動行だけが先に配られていて、指す先の脚本が無い状態であった。** 追記すると二重になる
- **`~/claude-sync/` が存在しない。** `m2-sync.sh` の `mkdir -p` が作る
- **`~/claude-sync/.stfolder` も無い。先回りして作る必要は無い。** syncthing が起動時に自分で作った（audit.md 326–337）

## 実測（待ち時間と進み方）

| 事象 | 実測 |
|---|---|
| keeper 起動 → 中継が立つ | **約 4 秒**（16:10:38 → 16:10:42）。SPEC の 413〜1569 秒は既に回っている keeper を待つ場合の値 |
| 実行権を戻す → 同期処理が起きる | **1695 秒**（周回 1800 秒を一度越えただけ。二度は越えていない） |
| 試験ファイルを置く → 中心が持つ | **121 秒**（一度目の問いは `needItems=1` で「無い」と返った） |
| repo の同期（受け取り） | 起動から **約 29 分**で完了（16:40:41 → 17:10:06 に `idle` / `needBytes` 0）。**実際に届いた量は 4714200120 bytes** |
| repo の同期（送り出し） | **完了していない。** 17:10 時点で中心から見た完了率 **75.66%**、`needBytes=11983979383` |

## 起票者の誤り

1. **`asserted_without_measuring`** — SPEC は「起動時に設定は書き戻される。**要約値は変わる**」と断定するが、
   本ホストでは sha256 も大きさも変わらなかった（`c4e6c320…d63b5` / 11179 bytes のまま）。
   指示どおり定義で確かめたため判定には影響しない。
2. **`asserted_without_measuring`** — SPEC の「中継は周期千八百秒。実測は四百十三〜千五百六十九秒」を
   そのまま当てると待ち方を誤る。**自分で起こした最初の周回では約 4 秒**であった。

**`check_does_not_check` と `self_contradiction` と `shell_assumption` は無かった。**

## 規約の適用判定

- **`proposal_gate`**: 適用される。`tools/check_proposal.py --only forbidden` を SPEC・audit・RESULT に当てて **0 件**。
  陽性対照（禁止語 2 語を含む囮）で **2 件検出 / exit 1** を確かめた。**囮は版管理の外に置き commit していない**
- **`folds`**: **適用されない。** 本契約は学習も評価も行わない。
  検査器側でも確かめた: `grep -c folds tools/validate_task.py tools/preflight.py` = **0**
  （`folds` に触れる道具は `tools/estimate_tier_cost.py` だけで、本契約は呼ばない）
- **`conventions_rev`**: 実測は `e7a51005`。契約の記載 `e7a5100` は同じコミットの短縮形であり、
  `validate_task.py` の照合（`git diff <rev>..HEAD -- context/conventions.md`）は差分なし。**置換していない**
- **`inputs.data`**: 雛形の必須項目であり、**本契約は参照しなかった**（`ego_val.txt` も dataset も読んでいない）

## 逸脱・想定外・UNKNOWN

**逸脱**

1. `judgement` — `~/.zshrc` へ起動行を**追記しなかった**。既存が 1 件在ったため（SPEC Task 3 Step 3 の指示どおり）
2. `judgement` — `conventions_rev` を**置換しなかった**。実測値と同じコミットを指しており、置換は無意味であるため
3. `judgement` — 退避を**行わなかった**。分岐が既に在り、`git checkout -b` が不要であったため
4. `environment` — `ss` `netstat` `lsof` `ip` が本ホストに無く、待ち受けは `/proc/net/tcp{,6}` の `st=0A` を数えた
5. `judgement` — `~/claude-sync/.stfolder` を先回りして作らず、実挙動を測った（結果、人の操作は不要であった）

**想定外**

- **測定器の最初の実装が壊れていた。** 正の対照が 0 を返し、負の対照 `zzz_no_such_token` が 1 を返した。
  実体は**自分の命令文を命令行に持つ自分の子シェル**であった。`shell-snapshots` を除外して直した（audit.md 12–27）
- **記録の衝突が起きた**（`sync-alerts.sync-conflict-20260917-074045-LW4CO4U.log` 他）。正常であり両方残っている
- **中心から見た `m2` の完了率が 67.39% → 28.83% へ下がった。** 本ホストが持つものを申告して分母が増えたためで、退行ではない

**UNKNOWN**

- **中心が本ホストの分を取り込み終える時刻。** 完了を待たない指示のため測っていない。
  17:10 時点で中心から見た `m2` の完了率 **75.66%**、`needBytes=11983979383`。
  **本ホストの受け取り側は完了している**（起動から約 29 分、`needBytes` 0）。
  報告を書いた 16:45 時点では `needBytes=5915279436` で未完了であり、**その後に完了した**。

## 送出

| 項目 | 結果 |
|---|---|
| commit | `7ae0a73d`（契約 5 ファイル + 受け皿 1 + 投影 4 の変更のみ。開始前からの未追跡 2 件は含めていない） |
| push | 終了コード **0**（`feat/efros-syncthing-join` を新規に送った） |
| PR | **#180**（`feat/efros-syncthing-join` → `phase0`） |
| `make task-validate` | 終了コード **0** |
| `make task-preflight` | **6 PASS / 0 WARN / 6 SKIP / 0 FAIL**。SKIP は P2 `cuda_ext_loaded`・P3 `deterministic_flags`・P4 `prereg_committed`・P5 `frozen_source_hash`・P11 `gpu_free`・P12 `refs_resolved` |
| `make forbidden-check` | 終了コード **0**（`status: pass`、`violations: []`、生成物 4 件を除外） |
| `make taskindex-check` | 終了コード **0**。`tasks_summary.csv` と `results_recent.md` に本契約が現れる |
| `make inbox-check` | 終了コード **0** |
| 秘匿検査（自前） | 送出物 6 件に対し **合計一致 0 件 / exit 0**。**検査は値を出力せず長さと件数だけを出した** |
| `make task-report` | 終了コード **0**。`verdict=pass` / `n_issuer_defects=2` / `report_bytes=10732` / `report_sha256=b0492499…11fc` / `replaced_blocks=0` |
| 抑止の解除 | **解除した**。`.sync-pause` を別名へ移して解除を確かめたのち削除した（`.sync-pause.released` は `.gitignore` に載らず未追跡として残るため）。抑止が効いていた記録は `sync-alerts.log` に 3 件 |
| 作業ツリー | 開始時と同じ未追跡 **2 件**のみ（`docs/sessions/digest/`）。**入れ子は作っていない** |
