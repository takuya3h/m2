# RESULT — T-2026-08-29-stage0-contract-b

命令とその出力の全文・run 一覧・時系列の証跡は `audit.md` にある。本書からは節番号で指す。

## 判定

**status: partial。** 関門 G1 は pass、G2 は pass（実測が見積もりの三倍を大きく下回る）。

**四項目のうち一項目のみ完全に実施できた。** 利用者の判断で縮退して続行した。

| # | 項目 | 状態 |
|---|---|---|
| B1 | run 型ごとの所要時間 | **実施** |
| B2 | 送り手の train/val mAP 差 | 🔴 **不能** — 検出器の実装と `.venv-relation-detr` が無い |
| B3 D→P | 参照入力四段 | **実施**（12 run） |
| B3 P→D | 参照入力四段 | 🔴 **不能** — 同上 |
| B4 | 強い工程塔と D→P 四段 | 🔴 **未実施** — ImageNet-R50 の重みが無い |

🔴 **関門 G0（両方向が測れたか）は片方向のみ成立。** 資産の欠落によるもので、設計の問題ではない。

## 1. 解決された参照

| spec の記載 | 解決先 | 実測 |
|---|---|---|
| `meta.created_from` | `runindex/` の最終変更と行数 | `606d875e` / 1238 / 273 / 1458（すべて一致。置換不要） |
| `contract.conventions_rev` | `context/conventions.md` の最終変更 | `a8c07e81`（一致） |
| `inputs.denominator.ref` | `runindex/experiments.csv` | **1 件一意**。`accuracy_mean=0.8973014948553679` / `accuracy_pstd=0.005917073407586465` / `n_runs=17` / `split=val`。`require` の三条件を満たす |
| `inputs.frozen_source.ref` | **実行者が追加**（SPEC §3 A-1 の指示） | **`run:baselines/s0_016_relationdetr_bbox_seed42`** に一意。ckpt sha256 `03936318f9d45ac9...` が `conventions#frozen_source` の正本と一致 |
| `contract.inject_verbatim` | `conventions` の 7 アンカーの原文 | `#split` `#eval_recipe` `#frozen_source` `#sigma` `#prohibitions` `#issuer_cautions` `#naming` を原文のまま参照（要約していない） |
| `inputs.sigma_policy`（省略） | `conventions#sigma` の既定 | `series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired` |

**凍結源の同定根拠**: `frozen_source_tag == relation_detr_seed42` は 903 件に当たるが mAP を持つ検出 run は **0 件**（すべて凍結源を使う側）。seed42 で mAP を持つ relation 系は 3 件あり、`s0_frozen_001/004` は別ファイル `relation_detr_s0frozen_init_seed42.pth` から学習した**下流**である（notes.md と command.sh で確認）。**「完走 ckpt」に当たるのは `s0_016` のみ**（audit §1.3）。

## 2. 完了判定（SPEC §7）

| # | 判定 | 実測の結果 | 空振りでないことの確認（実測） |
|---|---|---|---|
| a | 四段の成立 | **D→P の四段が揃った**（本書 §3）。P→D は「不能（検出器の実装と venv が無い）」 | 四段の平均 acc は**四つとも異なる**（0.904070 / 0.935974 / 0.958636 / 0.959956）。12 run の acc の相異なる値は **11/12**（`正解 seed42` と `正解⊕予測 seed42` のみ同値）。測定は入力に感応している |
| b | prereg の時系列 | prereg commit `7b1cff8b` が **13:52:50**、最早の run が **13:53:21**。全 12 run が後 | 12 run 分の対照表を audit §6.1 に全量。🔴 ただし §2.4 の**試走は commit 前**（`--no-evidence` で証跡なし。契約が A-2 を A-3 の前に置いているため） |
| c | B1 | run 型ごとの所要時間の表（本書 §4）。n は 2〜3 | 表の各行に対象 run 名が付いている（audit §4.4）。**予測段 seed42 のみ計時していない**ため n=2 |
| d | B2 | 🔴 **不能** | 検出器の実装が無いことを実測で示した（`third_party/Relation-DETR` は checkpoints 12 ファイルのみ、`.venv-relation-detr` 不在、`.gitmodules` なし）。config での同一 recipe 提示は該当なし |
| e | 索引 | `index.csv` **1238 → 1250**（+12）。**削除 0 / 既存行の変更 0**。追加集合は本契約の 12 run と**完全一致**（混入 0）。全件に `task_id` | 集合差の全量は audit §5.3。集約表も **変更 0 件**（四段とも新規群のため）。判定列（`same_sign` / `verdict_pstd` / `verdict_sstd` / `agree` / `reason` / `n_seeds`）で変わったものは**なし** |
| f | 変更範囲と不変 | 変更は §2 の対象に限られる（本書 §5）。`data/` への変更 **0 件**、既存 run への変更 **0 件** | 凍結源 ckpt の sha256 が作業前後で**一致**（`03936318f9d45ac9...`）。分割 3 ファイルの sha256 を記録（audit §6.2）。本契約 run の config に `test` の記載 **0 件** |

## 3. 四段の表（D→P。ばらつきは ddof=0）

| 段 | 平均 acc | pstd | 空段との差 | 平均 macro_f1 | 入力次元 |
|---|---|---|---|---|---|
| 空 | 0.904070 | 0.007337 | +0.000000 | 0.707410 | 2063 |
| 予測 | 0.935974 | 0.001426 | **+0.031903** | 0.787437 | 2063 |
| 正解 | 0.958636 | 0.002244 | **+0.054565** | 0.824222 | 2063 |
| 正解 ⊕ 予測 | 0.959956 | 0.002547 | **+0.055886** | 0.825255 | 2078 |

seed 別の全量は audit §4.1。**解釈は書かない**（SPEC §10）。

**P→D の四段は測れていない。** 値の表は存在しない。

## 4. B1 の表（投稿先判断の材料）

装置は RTX A6000 **1 枚**、`--epochs 50`、キャッシュ特徴上。学習と評価は同一プロセスで分離計測していない。

| run 型 | n | 実時間の範囲 | 対象 run |
|---|---|---|---|
| 空 | 3 | 12.1 〜 13.6 s | `b2a_refin_empty_00{1,2,3}_..._seed{42,123,456}` |
| 予測 | 2 | 16.3 〜 16.7 s | `b2a_refin_pred_00{2,3}_..._seed{123,456}` |
| 正解 | 3 | 11.9 〜 19.1 s | `b2a_refin_oracle_00{1,2,3}_..._seed{42,123,456}` |
| 正解 ⊕ 予測 | 3 | 24.1 〜 30.0 s | `b2a_refin_both_00{1,2,3}_..._seed{42,123,456}` |

起動 約 4.5 s、1 epoch 約 0.4 s。12 run の合計は約 3 分。
**契約の見積もり（24h / 29 run ≒ 50 分/run）を三桁下回る**（検出器の学習を含まない縮退のため）。

**B2 の差**: 測定不能。**B4 の塔単体性能**: 未実施。

## 5. 変更範囲（判定 f の全量）

| 対象 | 内容 |
|---|---|
| `experiments/transfer/b2a_refin_*` **12 run（新規）** | 本契約の出力。命名は `ExperimentManager` の自動採番 |
| `runindex/` | `make runindex` による自 run の収穫（手編集なし） |
| `scripts/train_b2a.py` | **正解 ⊕ 予測段の入力経路の追加**（`--tool-source both`）。W1 の「入力適合層と界面」の範囲。評価規則は変更していない |
| `docs/stage0/B_contract_b_results.md`（新規）／`stage0_summary.md` | 結果表と追記 |
| `context/auto/*` / `tasks/inbox.md` | 投影の再生成 |
| 契約ディレクトリ / `tasks/inbox.d/` | 記録 |

`data/` への変更 **0 件**、既存 run への変更 **0 件**。

## 6. 実測（次の契約で使う値）

| 項目 | 実測値 |
|---|---|
| 収穫後の索引件数 | `index.csv` **1250** / `experiments.csv` 277 / `verdicts.csv` 1486 / `per_class.csv` 9027 / `runs/` 1250 |
| `runindex_commit` | **`09fdefb3`**（収穫を含む commit） |
| prereg commit | `7b1cff8b9e12478bf2638597f385565386d7aed6` / `2026-08-29T13:52:50+00:00` |
| GPU 利用実績 | RTX A6000 **1 枚**、延べ約 3 分。2 枚目は未使用 |
| 欠落資産 | Relation-DETR の実装・`.venv-relation-detr`・ImageNet-R50 の重み |

## 7. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | 初回配布の `inputs.denominator.ref` と `inputs.frozen_source.ref` が `REPLACE-BY-EXECUTOR` のままで、**形式検査のある欄**に置かれていた。参照の解決は取り込み後の手順なのに検証は取り込み前に走るため、指示どおり実行すると契約が設置されず巻き戻る（実際に巻き戻った） |
| `asserted_without_measuring` | SPEC §5・§6 が P→D 四段と B4 を実施可能な前提で書かれているが、lecun には Relation-DETR の実装も `.venv-relation-detr` も ImageNet-R50 の重みも無い。指示どおり進めると Phase C と D の着手時点で止まる |
| `self_contradiction` | SPEC §6 が強い工程塔を「**十五動画**の工程ラベルで微調整」とするが、十五動画は val 2 本と test 3 本を含む。指示どおり実行すると §8 禁止 1（test への接触）に反する |
| `check_does_not_check` | `plan.env.preflight` に `cuda_ext_loaded` を宣言したが、実施した D→P はキャッシュ特徴上で `.venv` だけで動き検出器を import しない。**契約が使う経路と preflight が見る経路がずれており**、指示どおり preflight を通そうとすると使わない資産の欠落で止まる |
| `self_contradiction` | SPEC §3 A-2 が「最小の試走で所要時間を見積もる」を A-3（prereg の commit）の**前**に置く一方、判定 b は「prereg の commit が**全学習 run**の開始より前」を求める。指示どおり実行すると判定 b を厳密には満たせない |

## 8. 逸脱・想定外・UNKNOWN・判断待ち

**逸脱**

1. `judgement` — 未追跡の `.sync-pause.released` が `task_start.sh` の前提を満たさなかったため、削除せずスクラッチパッドへ退避した。
2. `spec_defect` — 初回の取り込みが L1 で落ちて巻き戻ったため実行できず、停止して報告した。利用者が台帳を置き直した後、二度目で取り込めた。再配布版は `denominator` に実値が入り `frozen_source` の欄が外されていた。
3. `judgement` — B2・P→D・B4 が実行不能と判明したため停止して提示し、**縮退して続行**（D→P 四段のみ）の判断を得た。判断は `tasks/inbox.d/` に記録した。
4. `environment` — **P2 `cuda_ext_loaded` が FAIL のまま Phase B を実行した。** 実施した経路が検出器を import しないことを、四段の読み込み検証と 50 epoch の完走で実測した上での判断である（audit §3）。
5. `judgement` — 正解 ⊕ 予測段の入力経路を `train_b2a.py` へ追加した（W1 の範囲。評価規則は不変）。次元決定を `tool_dim` / `in_dim_of` の 2 関数へ集約し、`IN_DIM` の直参照を置換した。
6. `judgement` — `ruff check scripts/train_b2a.py` が I001（import 並び）を 1 件出すが、**HEAD でも同じ 1 件が出る**ため直していない（指摘のみ）。

**UNKNOWN**

1. **予測段 seed42 の所要時間**。命名と証跡の確認のため単独で実行し、計時していない。
2. **学習と評価の内訳時間**。`train_b2a.py` は同一プロセスで両方を行い、分離して計測する経路が無い。
3. **P→D の四段の値**と **B2 の mAP 差**と **B4 の塔単体性能**。いずれも測定していない。
4. 2 枚目の GPU を使った場合の所要時間。1 枚のみで実行した。

**判断待ち**

1. Relation-DETR の実装と `.venv-relation-detr` を lecun へ用意するか（P→D と B2 の前提）。
2. ImageNet-R50 の重みを取得するか（B4 の前提）。いずれも外部通信であり本契約の対象外。
3. SPEC §6 の「十五動画で微調整」の訂正（train 10 動画に限る）。
4. 工程側だけを回す契約で `cuda_ext_loaded` を宣言しない規約。
5. `REPLACE-BY-EXECUTOR` を形式検査のある欄に置けない問題を、道具側（取り込みと検証の順序）で直すか、起票の作法で避けるか。

## 9. 送出

| 検査 | 終了コード |
|---|---|
| `make task-validate` | 0 |
| `make taskindex-check` | 0 |
| `make inbox-check` | 0 |
| `make context-check` | 0 |
| `make docs-check` | 0 |
| `make agent-check` | 0 |
| `make forbidden-check` | 🔴 **2**（既知の制約） |

**`forbidden-check` の違反 104 件はすべて本契約の許可分の内側**（`runindex/` 20 + 本契約の
12 run 配下 84。`data/` 0 件、対象外 0 件）。ファイル単位に揃えた集合で
`違反 ⊆ 許可分 = True`、許可分に無い違反は 0 件（audit §7.2）。

| 項目 | 実測 |
|---|---|
| commit | `09fdefb3`（118 files changed, 3965 insertions, 97 deletions）／prereg `7b1cff8b` |
| push | exit 0（`origin/feat/stage0-contract-b`） |
| PR | **#166**（base `phase0`。起点と同じ分岐） |
| 台帳への報告 | `make task-report` の結果を下に記す |
