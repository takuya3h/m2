# RESULT — T-2026-08-29-k1-reeval-and-harvest

命令とその出力の全文・再評価の過程・対照の出力は `audit.md` にある。本書からは節番号で指す。

## 判定

**status: pass。** 関門 G1 は pass。

🔴 **K1 の照合は三値のうち「一致（実測復帰）」で確定した。**

**ただし Phase B の収穫で escalate が発動した**（集約表に既存行の変更 8 件）。
利用者の判断を仰ぎ、**続行**の回答を得た（audit §4.5、`tasks/inbox.d/`）。

🔴 **前二契約の結論を訂正する。** 六 run の metrics は失われていなかった。
失われていたのは `metrics.json` という**成果物ファイル**で、数値そのものは
`checkpoints/best_tecno.pth` の `val` キーに残っていた（audit §2.6）。

## 1. 解決された参照

| spec の記載 | 解決先 | 実測 |
|---|---|---|
| `meta.created_from.runindex_commit` | `runindex/` の最終変更 commit | `7918b5dd`（一致。置換不要） |
| `meta.created_from.counts` | `runindex/*.csv` の行数 | 1177 / 213 / 1038（すべて一致） |
| `contract.conventions_rev` | `context/conventions.md` の最終変更 commit | `a8c07e81`（一致） |
| `contract.inject_verbatim` | `conventions#prohibitions` `#issuer_cautions` `#naming` | 原文のまま参照（要約していない） |
| `inputs.sigma_policy`（省略） | `conventions#sigma` の既定を継承 | `series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired` |
| `inputs.data.split_files` | `data/splits/ego_val.txt` | 動画 `09` `10`。実際の評価は `phase_manifest/val.json`（clip `09_1/10_1/10_2`、1515 フレーム）で、両者は整合（audit §2.3） |

**ddof=0（pstd）は実測でも裏付いた。** 再評価値から計算した両側のばらつきが記録と一致する。

## 2. 完了判定（SPEC §6）

| # | 判定 | 実測の結果 | 空振りでないことの確認（実測） |
|---|---|---|---|
| a | 収穫 | `index.csv` は **+61 / 削除 0 / 既存行の変更 0**。追加行の path 集合は棚卸し 61 件と**完全一致**（差 0）。🔴 ただし集約表に変更あり: `experiments.csv` +60/変更 **1**、`verdicts.csv` +420/変更 **7**、`per_class.csv` +549/変更 0 | 陽性: 収穫前後の対に差分検出器を当てると 61 件の追加を検出。陰性: 同一入力（収穫後どうし）の対では 追加 0 / 削除 0 / 変更 0。変更 8 行は全量を audit §4.5 に載せた |
| b | 投影 | `taskindex-check` / `inbox-check` / `context-check` すべて exit 0 | `context/auto/tasks_summary.csv` に 1 バイト足すと **`taskindex-check` だけが exit 2**、他 2 つは exit 0 のまま。`make taskindex` で復元し sha256 が `e422714d...` へ戻ることを確認（audit §7） |
| c | K1 再評価 | **「一致（実測復帰）」で確定。** run ごとの値・3-seed 集計・照合の表は本書 §3 と audit §5 に全量 | 評価器: 陽性 GPU 2 回が完全一致・CPU とも完全一致・**保存値とビット一致 6/6**（差 < 1e-15）。陰性 別 checkpoint で hemostasis F1 が **6/6 すべて異なる**。集計器: 陽性 mean(記録 paired)=−0.069067 が区間内で一致、陰性 1 件除外の 3 通りすべて不一致（audit §5.4・§5.7） |
| d | digest | 版管理へ入れた。内容は一字も変えていない | 退避前後の sha256 が `70d40c63e387b497...` で一致、大きさ 26565 バイトも一致（前セッション開始時の `ls` 実測と同値）。伏せ字の検査は 3 規則とも 0 件で、陽性対照では 3 規則とも検出・陰性対照では 0 件（audit §3.1） |
| e | 変更範囲 | **§2 の対象に限られる。** 差分の全量は本書 §5 | `git status --porcelain` を `experiments/|data/` で絞ると **0 件**。同じ絞り込みを `runindex/` へ当てると **70 件**（未追跡 61 + 変更 9）、`docs/` へ当てると **3 件** 出る（絞り込みは働いている） |
| f | orphan 不変 | `experiments/` `data/` への書き込み **0 件**。六 checkpoint の md5 は作業前後で **6/6 一致** | 一時複製に 1 バイト足すと md5 が `95fc6891...` → `5d7e62b2...` へ変わり照合が不一致になる（大きさ 2599650 → 2599651）。**複製は削除した**（audit §6） |

## 3. K1 の結論 — 一致（実測復帰）

### run ごとの再評価値（val, 1515 フレーム）

| side | seed | best epoch | phase_accuracy | hemostasis F1 |
|---|---|---|---|---|
| relationdetr | 42 | 19 | 0.9478547854785478 | 0.7741935483870968 |
| relationdetr | 123 | 16 | 0.9478547854785478 | 0.8245614035087719 |
| relationdetr | 456 | 39 | 0.9471947194719472 | 0.8041237113402062 |
| aligndetr | 42 | 26 | 0.8917491749174917 | 0.25 |
| aligndetr | 123 | 24 | 0.8752475247524752 | 0.21875 |
| aligndetr | 456 | 28 | 0.8686468646864687 | 0.06779661016949151 |

**再評価値は checkpoint 内の保存値とビット単位で一致した（6/6）。**

### 第一層（seed 対応に依らない量）— 九量すべて一致

| 量 | 再計算 | 記録 | 許容差 | 判定 |
|---|---|---|---|---|
| relationdetr 平均 acc | 0.9476347635 | 0.9476 | ±5e-05 | 一致 |
| relationdetr acc pstd | 0.0003111581 | 0.0003 | ±5e-05 | 一致 |
| relationdetr hemostasis F1 平均 | 0.8009595544 | 0.8010 | ±5e-05 | 一致 |
| relationdetr hemostasis F1 pstd | 0.0206839571 | 0.0207 | ±5e-05 | 一致 |
| aligndetr 平均 acc | 0.8785478548 | 0.8785 | ±5e-05 | 一致 |
| aligndetr acc pstd | 0.0097159085 | 0.0097 | ±5e-05 | 一致 |
| aligndetr hemostasis F1 平均 | 0.1788488701 | 0.1788 | ±5e-05 | 一致 |
| aligndetr hemostasis F1 pstd | 0.0795554060 | 0.0796 | ±5e-05 | 一致 |
| 平均の差 (ali − rel) | −0.0690869087 | −0.06909 | ±5e-06 | 一致 |

### 第二層（seed 対応）— 記録の並びを seed 42/123/456 順と解すると一意

| seed | 再評価の paired 差 | 記録 | 判定 |
|---|---|---|---|
| 42 | −0.05610561056105612 | −0.0561 | 一致 |
| 123 | −0.0726072607260726 | −0.0726 | 一致 |
| 456 | −0.07854785478547854 | −0.0785 | 一致 |

🔴 **順序を無視すると 2 通りが一致する。** relationdetr の seed42 と seed123 の acc が
**完全同値**（0.9478547854785478）で縮退するためで、acc だけでは区別できない。
恒等対応は両方の解に含まれ、どちらでも集計値は変わらない（audit §5.6）。
**「一意」の判定はこの読み方（記録の並び = seed 順）に依存する。**

## 4. 実測（次の契約で使う値）

| 項目 | 実測値 |
|---|---|
| 収穫後の索引件数 | `index.csv` **1238** / `experiments.csv` 273 / `verdicts.csv` 1458 / `per_class.csv` 8919 / `runs/` 1238 |
| 収穫前 | 1177 / 213 / 1038 / 8370 / 1177 |
| `runindex_commit` | 本契約の commit（§6 に記載） |
| 評価の所要時間 | 六 run 合わせて **GPU 3.49 s / CPU 2.28 s**（全体の実時間。学習はしていない） |
| 使用資源 | RTX A6000 1 枚（`cuda`）。CPU でも同値を再現。**GPU は必須ではない** |
| ホスト / repo / 分岐 | `lecun` / `/home/ubuntu/slocal/m2` / `feat/k1-reeval-and-harvest` |
| 六 checkpoint | md5 作業前後で 6/6 不変。索引には**未登録**（`metrics.json` を持たないため走査対象外） |

## 5. 変更範囲（判定 e の全量）

| 対象 | 内容 |
|---|---|
| `runindex/index.csv` `experiments.csv` `verdicts.csv` `per_class.csv` | `make runindex` による収穫（手編集なし） |
| `runindex/anomalies.md` と `runindex/anomalies/*.csv` 4 件 | 収穫器が同時に再生成 |
| `runindex/runs/*.json` **61 件（新規）** | 収穫 |
| `docs/stage0/A7_k1_provenance.md` | 追記 |
| `docs/stage0/stage0_summary.md` | 追記 |
| `docs/sessions/digest/2026-08-25-6ae159a7-*.md`（新規） | 退避 digest の記録 |
| `context/auto/*` / `tasks/inbox.md` | 投影の再生成（`make taskindex` `make inbox` `make context`） |
| `tasks/T-2026-08-29-k1-reeval-and-harvest/` / `tasks/inbox.d/T-...md` | 契約ディレクトリと受け皿 |

`experiments/` `data/` への変更 **0 件**。絞り込みごとの件数: `runindex/` 70（未追跡 61 + 変更 9）/ `docs/` 3 / `context/auto/` 4 / `tasks/` 3。

## 6. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | SPEC §0 が「六 run は metrics を持たず、数値へは遡れない」「当時の metrics は喪失」と断定したが、**checkpoint の `val` キーに当時の値が入っていた**。指示どおり「再評価で回復する」だけを行うと、保存値との照合という最強の裏付けを取り逃す |
| `asserted_without_measuring` | SPEC §1 が「run 名から seed との対応は分からない（config 不在）」としたが、**run ディレクトリ名は `..._seed42` の形で seed を含む**。指示どおり対応不明として扱うと、3×3 の全対応を試す必要のない場面で総当たりを強いる |
| `self_contradiction` | SPEC §4 の「既存行の変更・削除が零件」は**集約表には原理的に満たせない**。新しい run が既存の群へ加入すれば集約行は必ず書き換わる。指示どおり実行すると、正常な収穫で必ず escalate して停止する |
| `check_does_not_check` | `plan.env.preflight` に `gpu_free` を宣言したが、`tools/preflight_task.py` の `CHECK_NAMES` に無く schema も任意文字列を許すため**黙って無視され PASS になる**。指示どおり preflight を信頼すると、GPU が塞がっていても検査を通過する |

## 7. 逸脱・想定外・UNKNOWN・判断待ち

**逸脱**

1. `judgement` — 作業ツリーの未追跡 2 件（前セッションの digest と `.sync-pause.released`）が `task_start.sh` の前提を満たさなかったため、削除せずスクラッチパッドへ退避してから phase0 へ切り替えた。digest は Step A-3 で戻して記録した。
2. `judgement` — Phase B の escalate（集約表の既存行変更 8 件）で停止し、利用者へ提示して「続行」の回答を得た。判断は `tasks/inbox.d/` に記録した。
3. `spec_defect` — 第二層の「一意」判定は、記録の三つ組の並びを seed 42/123/456 順と解する読み方に依存する。順序を無視すると 2 通りになる。SPEC は並びの意味を定めていないため、**読み方を明示した上で一意と判定した**。
4. `judgement` — SPEC が求めた「再評価」に加え、**checkpoint 内の保存値との照合**を行った。指示にない作業だが、再評価が当時の値を再現しているかを直接示せるため実施した。
5. `environment` — 再評価器は `RELDETR_FROZEN_TAG` を設定してから `train_t1a` を読み直す必要があった（経路が import 時に決まるため）。経路が意図どおりかを `assert` で実測している。評価規則そのものは変更していない。

**UNKNOWN**

1. 六 run の**学習時刻と学習ホスト**（checkpoint の mtime は 49 秒に集中しており複製の時刻。前契約 audit §3.5）。
2. 六 run の**当時のハイパーパラメータ**。`config.yaml` が無い。再評価は `train_t1a.py` の既定値（num_stages=2 / num_layers=8 / num_f_maps=64）を使い、`load_state_dict(strict=True)` が通ることが裏付けである。
3. 六 run の `metrics.json` が**いつ・なぜ失われたか**。

**判断待ち**

1. **六 run を索引へ載せるか。** 載せるには `metrics.json` の生成が要るが、当時の生成物ではないため本契約では禁止されている。別途の規約が要る。
2. **集約表に対する収穫の検証規約。** 「既存行の変更・削除が零件」は run 単位の `index.csv` にのみ成立する。集約表には「判定列（`same_sign` / `verdict_pstd` / `verdict_sstd` / `agree`）が不変であること」を条件にする案を提案する。
3. `plan.env.preflight` の未知の名前を FAIL にするか、schema を enum にするか。
4. 追跡済み digest 4 件で本契約の秘匿検出規則が偽陽性を出した（実物の資格情報は含まれない）。規則の `(?!\*)` を伏せ字表記に合わせて直すか。

## 8. 送出

| 検査 | 終了コード |
|---|---|
| `make task-validate` | 0 |
| `make taskindex-check` | 0 |
| `make inbox-check` | 0 |
| `make context-check` | 0 |
| `make docs-check` | 0 |
| `make agent-check` | 0 |
| `make forbidden-check` | 🔴 **2** |

🔴 **`forbidden-check` は exit 2 になる。違反 70 件はすべて `runindex/` で、
本契約 §2 が明示的に許可した収穫の出力そのものである**（自分が測った `runindex/` の
変更 70 件と集合一致）。`experiments/` `data/` `transfer/` の違反は **0 件**。
`tools/check_forbidden.py` は `FORBIDDEN_PREFIXES` を固定で持ち契約ごとの許可を
受け取る引数が無いため、**収穫を行う契約はこの検査を原理的に通せない**（audit §7.3）。

| 項目 | 実測 |
|---|---|
| PR | 未起票（下記） |
| 台帳への報告 | 未送信（下記） |
