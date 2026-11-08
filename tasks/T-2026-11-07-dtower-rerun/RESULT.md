# RESULT — T-2026-11-07-dtower-rerun

andrew の A6000 × 2 で、探索の 12 番（学習率 3.07e-4、max_norm 0.059、S 4.976e-3）と 0 番（1e-4、0.1、S 4.81e-4）を GPU ごとの batch 6 で 5 折り × seed 42・123（20 本）学ぶ契約。
**利用者の決定で 7 本目（12 番 seed 123 の折り B）の後に学習を止めた。完了は 12 番の 7 本、0 番は 0 本。** 選定は行わない（prereg §3）。凍結する塔（12 番 seed 42 の 5 本）は揃った。
全値は `experiments/analysis/dtower_rerun/REPORT.md`、命令と出力は `audit.md`（以下 `audit:行`）。

## 1. 解決された参照

| 記載 | 解決先 |
|---|---|
| `inputs.denominator.ref` | `exp:baselines/dcoco_foldA/dcoco_foldA@val`: mAP_mean 0.7242876868、**mAP_sstd 0.0037964726778790692**、n_runs 6、n_seeds 3（42・123・456）、split val。require を満たす。起票時の runindex と同じ値（audit:27、33） |
| `inputs.sigma_policy` | 省略 → `conventions#sigma` の既定を継承（audit:34） |
| `contract.inject_verbatim` | `context/conventions.md`（`2d946b07`、`conventions_rev` と一致）の 11 節を原文のまま適用。11 節は実在し、2d946b07 から HEAD まで変更なし（audit:35、315） |
| `meta.created_from` | 起票時 68befc3b・{2363, 1130, 1736} → 実測 **d3e319ac・{2623, 1305, 1947}**。利用者の決定で改訂（amendments、audit:38） |
| 0 番の weight decay | 3.0e-4 → **2.998753e-4**（S 4.81e-4 ÷ (1e-4 × 20 × 802)）。利用者の決定で改訂し、prereg を学習の前に commit（audit:36-37、43） |

## 判定

- status: **partial**（利用者の決定で 7/20 本で停止。run の表が未完）
- G1 pass（audit:130-138）: 分岐と起点 a68672f1、prereg の先行、カード五版、入力 25 件の要約値の一致、compute プロセス 0 件、空き 2 倍以上
- G2 pass（audit:203-209）: 両点の設定が optimizer の群と DataLoader に届く。陽性対照で値が変わり、照合と枚数の検査が外れで止まる。既定の挙動は不変
- G3: **ask**（on_fail ask。利用者の決定で 7 本目の後に停止）。完了した 7 本は条件を満たす（audit:273-280）。7 本とも rc 0・損失の非数 0・溢れ 0・COCO の重みを読んだ行あり。20 本の完了は満たさない（13 本は回していない）

## 完了判定

| # | 判定 | 実測 |
|---|---|---|
| a | prereg の先行 | df18070d（11-07 19:13:18 JST）は最初の学習（20:05:51 JST）の前。P4・P13・P14 PASS（audit:43-50）。UNKNOWN の写しで P13 FAIL、存在しないカードで P14 FAIL（audit:311-314） |
| b | 開始状態と環境 | 分岐・起点・PR 294/299 の内容・未追跡・GPU・試験の前 7 failed / 989 passed・カード五版・環境の表・300 W（audit:53-129）。列挙の対照 1/0/0、四版の写しで rc 1 |
| c | 入力と道具 | 25 件の sha256 一致、5 折りの動画の集合が規約の表と一致。1 バイト変えた写しで不一致 1、test を混ぜた集合で不一致 1。空き 1.62 TB ≥ 見込み 66.5 GB の 2 倍（audit:70-81、105-110） |
| d | 設定の到達 | 7 本の群の値と batch 6 が水準どおり（REPORT §7）。0 番は対照（p0_A）だけで、本番の run は無い。changed・wd_mismatch・batch_mismatch・default の対照（audit:172-187） |
| e | run | **7 本完走、13 本は回していない**（下の一覧）。config.yaml に task_id・点・折り・batch・seed・設定。存在しない名前（点 5・折り F）は 0 件（audit:290-297） |
| f | 記録する量 | prereg §5 の 9 項目を 7 本で記録（REPORT §7）。fp16 の scaler が飛ばした歩 11〜13 |
| g | 表 | 揃った所だけ書き、ほかは UNKNOWN（下の表）。表の 22 マスを metrics.json から計算し直して全桁で一致（audit:290-297）。選定の記述は無い |
| h | test の副次 | 7 本とも一度（`test_access.json`）。5 動画の集計は 12 番 seed 42 だけ（ほかは UNKNOWN）。6 動画の写しで値が変わる（audit:281-297） |
| i | 対称性 | prereg の表 26 行に UNKNOWN 0 件。P13 PASS。壊した写しで FAIL（audit:311-314） |
| j | 凍結する塔 | 5 本の経路・sha256・epoch・val（`frozen_towers.json`）。repo の外に在り、同期の対象の下の `.pth` は 0 件。1 バイト変えた写しで不一致（audit:290-297） |
| k | 収穫と無変更 | runindex に完了した 7 本が task_id つき（20 本ではない）。C5 は別の契約の 3 run で FAIL（audit:305-310）。要約値 21 根・仮想環境・凍結源が一致（audit:298-304）。試験は後も 7 failed / 989 passed で失敗の名前は同じ 7 件（audit:317-320）。forbidden-check の本契約の経路の違反 0 |
| l | PR | #PR_NUMBER、base phase0、Draft でない、head feat/dtower-rerun |

## 実測

| 折り | 12 番 seed 42 | 12 番 seed 123 | 12 番の平均 | 0 番 | 12 − 0 |
|---|---|---|---|---|---|
| A | 0.7196251153 | 0.7366459467 | 0.7281355310 | UNKNOWN | UNKNOWN |
| B | 0.4755093444 | 0.4897202167 | 0.4826147806 | UNKNOWN | UNKNOWN |
| C | 0.4427707417 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| D | 0.5062879070 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| E | 0.5226364946 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

- 10 本の平均: 12 番・0 番とも UNKNOWN。12 番 seed 42 の 5 折りの平均 0.5333659206（記述）
- seed 間の SD（12 番）: 5 折りの合算は UNKNOWN。折り A・B の 2 対だけから 0.0110867（|差| 0.0170・0.0142）
- 折り A と b6（同点幅 0.0076）: seed 42 −0.0188439（外）、seed 123 +0.0038106（内）。同じ設定と seed の繰り返しの差
- 副次の test（12 番 seed 42、5 動画を一つにまとめた評価）0.4354845。動画ごと 01 0.6572・03 0.3471・11 0.5959・13 0.5889・14 0.3142
- 凍結する塔（checkpoint の epoch・val mAP・sha256 の頭）: A 12・0.7196・`4c542a8b`、B 17・0.4755・`3d3035af`、C 11・0.4428・`a13be4d4`、D 12・0.5063・`4e382921`、E 5・0.5226・`2ed21670`
- 所要: 学習の壁時計 3.6〜5.3 h、run あたり評価と写しを含め 4.2〜5.6 h。最大確保 38.0〜38.7 GB（rank ごと）
- 予測（prereg §3.1）: 1 UNKNOWN、2 **外れ**（seed 42）、3 UNKNOWN、4 完了した 7 本で当たり
- 評価の値は、どの注釈ファイルにもある `id: 0` の注釈 1 つ分の pycocotools の影響を含む（全 run・前例に一様。REPORT §8、audit:224-232）

回していない 13 本（続きの契約で回す）:

| 点 | seed | 折り |
|---|---|---|
| 12 | 123 | C・D・E |
| 0 | 42 | A・B・C・D・E |
| 0 | 123 | A・B・C・D・E |

## 起票者の誤り

- asserted_without_measuring: prereg §2.1 の 0 番の weight decay 3.0e-4 は、S を揃える定義から出る 2.998753e-4 を丸めた値で、S が 0.04 % ずれる。利用者の決定で改訂（audit:36）
- asserted_without_measuring: `meta.created_from` は 68befc3b・{2363, 1130, 1736} で、起票時の phase0（d3e319ac・{2623, 1305, 1947}）を測っていない。L2-8 の WARN の原因（audit:38）
- asserted_without_measuring: prereg §2.3 は動画ごとの val mAP を測る量に置くが、`inputs.code` の評価の道具は動画ごとの値を出さない。包み `eval_dump.py` で足した（audit:148）
- asserted_without_measuring: SPEC Task C-2 は checkpoint で test を評価すると書くが、学習の設定は `Search never evaluates test` で test を拒む。評価の道具の `--split test` で評価した（audit:149）

## 逸脱

- **利用者の決定で 7/20 本で停止。残りは続きの契約。** 指示の文面は「14〜15/20 本」と「#7 の後」を含み同時に成り立たないため、止める位置を確かめて #7 の後と決めた（audit:262-270）
- 止め方: 実行器に口が無いため、次の run の作業フォルダを空で先に作り、#8 を起動の前に止めた。空のフォルダは残した（audit:266-269）
- B-5 で、test の口を確かめるために前例の checkpoint（b6 seed 42）で折り A の test を一度評価した（AP 0.5099。腕ではなく、どこにも使わない）（audit:200）
- 集計の道具の恒等性の確かめを、注釈の id を +1 ずらした評価との完全一致に改めた（audit:224-232）。揃わない所を UNKNOWN にするよう直した（audit:281-289）
- environment: 前例の道具 `dtower_batch_search/tools/*.py` 10 件が同期で作業ツリーから消えた（11-08 10:45 JST）。利用者の指示で HEAD の blob から戻し、sha256 が一致。削除も復元も PR の差分に入れていない（audit:247-261）
- environment: 同期で届いた別の契約の未追跡 `experiments/analysis/grasp_cards_survey/tools/*.py` 8 件で forbidden-check が fail。消さず、無視の一覧にも足していない（audit:298-304）
- environment: runindex の作り直しが同期で届いた統合前の別の契約の run（grasparms など 17 件）も拾った。利用者の決定で全体を commit。C5 は別の契約の 3 run で FAIL のまま（audit:305-310）
- `.git/info/exclude` に別の契約の 2 フォルダを書いた（利用者の指示、audit:8-30）。戻すかは利用者に確かめる

## 想定外・UNKNOWN

- 回していない 13 本に関わる値（12 − 0、10 本の平均、5 折りの seed 間の SD、12 番 seed 123 と 0 番の副次の test、予測 1・3）
- 同じ設定・seed の折り A で b6 と 0.0188 違った原因（非決定性の大きさの由来は測っていない）
- 注釈ファイルの `id: 0` は注釈の作り手に由来する。pycocotools の扱いは直していない（評価の経路を変えないため）
- 事後の評価の時間は 30 秒刻みでしか測っていない

## 送出

- PR: #PR_NUMBER（base phase0、isDraft false、head feat/dtower-rerun）
- `make task-report`: TASK_REPORT_RC
