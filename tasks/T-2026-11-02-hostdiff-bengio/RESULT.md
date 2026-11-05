# RESULT — T-2026-11-02-hostdiff-bengio

時刻は JST。経過の全文と命令の出力は `audit.md`（以下「audit」）。値は `experiments/analysis/hostdiff_andrew_bengio/bengio/values.json` と `REPORT.md`。

## 1. 判定

- **verdict: pass**。5 本とも収束規則で終わり、§6.1 の全キーに値がある（UNKNOWN 0）
- **G1 通過**: 分岐 `feat/hostdiff-bengio`、起点 origin/phase0 8aefdce3。Relation-DETR の要約値が andrew main と同じ、入力の要約値が記録と同じ、
  起動の設定 27/27 が手本と許した違いの他で同じ、GPU 2 枚が空き（audit「Task A」）
- **G2 通過**: 工程塔の backbone の短い学習二回の損失の列が両 rank とも bit 単位で一致（audit「Task B」）

## 2. 解決された参照

- 注入の 8 アンカー（prohibitions・issuer_cautions・env_p0・folds・frame_sets・det_groups・symmetry・precision）の原文は `resolved_refs.md`（機械で切り出し、要約なし）
- `contract.conventions_rev`: 起票時 d145854e と `context/conventions.md` の中身は同じ（最後の変更の commit は 2d946b07）。runindex 68befc3b・2363/1130/1736 は起票時と同じ
- 参照しなかった項目: `inputs.denominator`（本契約は処置と分母を持たない。SPEC §11）

## 3. 完了判定（SPEC §8）

| # | 実測 | 空振りでないことの確認 |
|---|---|---|
| a | 照合の結果 `a_reldetr.json`・`a_inputs.json`（不一致 0）・`a_launch_compare.json`（27/27）、`env` は `values.json` | 記録の要約値を一文字変えると不一致。手本の `workers=4` を `workers=2` に変えた写しは不一致 |
| b | rank0・rank1 とも micro-step 200・optimizer step 50 の損失の列が一致（`b_determinism.json`） | 二回目の列の一値の最下位の bit を変えると不一致 |
| c | 5 本とも収束規則で終了（上限に届かず）。COCO の読み込み: 工程塔は両 rank の `load pretrained COCO backbone … sha256=a755b3eb…`、検出塔は `matched true` | 経路を存在しない経路にした設定は回していない（UNKNOWN。§6 参照） |
| d | `values.json` の欠け 0・UNKNOWN 0（`build_values.py`） | 写しから `detector.seed42b.AP50` を消すと欠けとして出る |
| e | 5 本とも `foreign_gpu_use: []`（標本 956〜2,892 件） | 列挙の道具 `proc_enum.py` が陽性（zsh）8・陰性 0（audit A-1） |
| f | test 04・05・07 との共通 0（`f_test_videos.json`）。同期の型 0 / 317 経路（`f_sync_types.json`） | 04 を混ぜると共通 1。`experiments/x/foo.npy` は `!experiments/**/*.npy` に当たる |
| g | 道具の試験 4 passed（22ce24b2 の版） | 既定の契約名を一つ変えた写しで 2 failed |
| h | PR #288、base phase0、分岐 feat/hostdiff-bengio、Draft でない | — |

## 4. 実測

| run | 主の値（val） | 一歩の秒（中央値） | wall_s | epoch（checkpoint / 停止 / 観測） | 本契約以外の GPU の使用 |
|---|---|---|---|---|---|
| 工程塔 seed42 | J_mean 0.5903（J_max 0.6589、backbone frame acc 0.8125） | micro 0.6929・optimizer 2.7846 | 10,013 | 11 / 19 / 19 | 無し |
| 工程塔 seed123 | J_mean 0.6189（J_max 0.6373、backbone frame acc 0.7957） | micro 0.6960・optimizer 2.7979 | 12,095 | 19 / 23 / 23 | 無し |
| 検出塔 seed42a | mAP 0.7264（標的群 0.8133、陰性対照群 0.6616） | 0.5103 | 29,799 | 17 / 21 / 22 | 無し |
| 検出塔 seed42b | mAP 0.7318（標的群 0.8118、陰性対照群 0.6777） | 0.5107 | 23,185 | 12 / 16 / 17 | 無し |
| 検出塔 seed123 | mAP 0.7296（標的群 0.8230、陰性対照群 0.6708） | 0.5078 | 24,409 | 13 / 17 / 18 | 無し |

工程塔の epoch は 1 起点、検出塔は 0 起点。期間は 2026-11-02 23:00 〜 11-04 02:38。発散・非数は無し。相手のホストとの比べは書かない（§6.2）。

## 5. 起票者の誤り

- **check_does_not_check**: プリフライト P2 `cuda_ext_loaded` は `sys.executable`（契約の `env.venv: .venv`）で検出器を import するが、検出器は `.venv-relation-detr` で動く。
  指示どおり回すと `.venv` に `fvcore` が無いため FAIL になり、検出の拡張の読み込みを確かめていない（`.venv-relation-detr` では読み込める）。利用者の判断で記録して続けた
- **asserted_without_measuring**: SPEC §1 は「#284 が phase0 に統合済み」を前提に置いたが、起票の時点で #284 は OPEN だった。指示どおり始めると起点が #284 を含まない。
  利用者が統合し、分岐を早送りで 8aefdce3 へ合わせた
- **self_contradiction**: 契約は「一度に走らせる学習は一本」とし、同時に手本（backbone の後の記録の評価と取り出しを 2 枚で並行、ヘッドを 2 本ずつ）と同じ手順を求めた。
  字面どおりでは両方を満たせない。利用者の判断で手本どおり並行にした（塔の run を同時に 2 本走らせない意味に読んだ）

## 6. 逸脱

- **spec_defect**: 利用者の指示で、5 本の後に origin/phase0（#286 hostdiff-andrew の統合後、89fe4a41）を取り込んだ（merge c518bf6d）。scripts/ の 3 ファイル
  （`run_ptower_search.py`・`tower_search_common.py`・`train_relation_detr_search.py`）は phase0 の版を採った。**bengio の 5 本の run が使った版は commit 22ce24b2 である。**
  分岐の先頭の scripts/ は run が使った版ではない。`values.json` の `code_commit` に同じことを書いた。両方の契約が同じ scripts/ を別々に変えてよい形だったため衝突した（audit「phase0 の取り込み」）
- **judgement**: 取り込みは、検出塔 123 の評価と記録（学習の後に起動し、その時点の scripts/ を読む）が終わってから行った
- **judgement**: 道具の試験 `test_defaults.py` は取り込みの後、22ce24b2 を repo の外へ展開して回した（4 passed）。分岐の先頭の scripts/ に向けると 3 failed（bengio の仕掛けが無い。想定どおり）
- **judgement**: 工程塔 seed42 の backbone の `git_commit.txt` は 8aefdce3。起動（11-02 23:00:17）の 69 秒後に道具の変更を 22ce24b2 として commit したため。
  変更の最後は起動の前（22:59:16）で、動いた内容は 22ce24b2 と同じ
- **judgement**: 時間ヘッドの公開名は 10 本とも `001_P15_…`（手本は 003〜012）。1 本ずつ別の作業場で回すため連番が振り直された。起動の引数は照合済みで、差は名前だけ
- **judgement**: 一歩ごとの時刻を取るため、`scripts/` の道具に環境変数 `TOWER_SEARCH_STEP_LOG` があるときだけ働く記録を足し、起動の照合では許した違いに数えた
- **environment**: 本測定の前の検出塔の 12 ステップの確かめで、`optimizer.step` の差し替えが `LinearLR` を壊した。記録の位置を勾配のクリップへ移して直した（学習の挙動は変えていない）
- **judgement**: プリフライト P2 FAIL（§5）は利用者の判断で記録して続けた。拡張と COCO の重みの読み込みは各 run の記録で確かめた

## 7. 想定外・UNKNOWN

- 完了判定 c の対照（COCO の重みの経路を存在しない経路にした設定）は回していない。observed は UNKNOWN
- pytest（`tests/`）: 分岐の先頭 11 failed / 985 passed、phase0（一時の worktree）12 failed / 968 passed / 16 skipped。先頭の 11 件は phase0 の 12 件に含まれ、本契約の変更と関係しない。
  うち `test_stage1_ptower_heads::test_existing_candidates_match_baseline` 4 件は CPU の float 出力のバイトの要約値を比べる試験で、22ce24b2 の版でも落ちる（ホストで要約値が違う）
- 同じ seed の検出塔 42a と 42b は値も停止の epoch も違う（決定性を有効にしない設定）。差の解釈は §6.2 の比べで行う

## 8. 送出

- PR: #288（base phase0、分岐 feat/hostdiff-bengio、Draft でない）
- `make task-report`: 終了コード 0（verdict pass、report_sha256 55a7b1ad…、8,171 B）
