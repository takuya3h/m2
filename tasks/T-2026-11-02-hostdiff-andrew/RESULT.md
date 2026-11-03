# RESULT — T-2026-11-02-hostdiff-andrew（andrew）

詳細は `audit.md`（行番号で指す）。値の全件は `experiments/analysis/hostdiff_andrew_bengio/andrew/{values.json,REPORT.md}`。時刻は JST。

## 1. 解決された参照

- `contract.inject_verbatim` の 8 アンカー（prohibitions・issuer_cautions・env_p0・folds・frame_sets・det_groups・symmetry・precision）の原文は `resolved_refs.md`（機械で切り出した。要約していない）
- 規約の版 `conventions_rev` d145854e と `runindex_commit` 68befc3b は、実行時の HEAD でも同じ本文・同じ索引（`git diff` 空。audit 225〜228 行）
- 参照しなかった項目: `inputs.denominator`（本契約は処置と分母を持たない）、`inputs.frozen_source`（凍結源を使わない）

## 2. 判定

- **verdict: pass**。5 本の測定がすべて終わり、§6.1 の値が欠けなく揃った
- G1 通過（audit 133 行）: Relation-DETR の source 142・2f08e521… と all 155・20f15c06… が記録と一致、入力の 32,670 画像と注釈・manifest・split・COCO の重みが一致、command.sh 13 本 × 2 seed と config の許していない差 0、GPU 2 枚が空き
- G2 通過（audit 137〜150 行）: 縮めた fine-tune 二回で、両 rank の 200 micro-step・50 optimizer step の損失の列が bit 単位で一致

## 3. 完了判定（SPEC §8）

| # | 判定 | 実測 | 空振りでないことの確認（実測） |
|---|---|---|---|
| a | 開始状態と照合 | Relation-DETR・入力・起動の設定が一致。`env` は values.json にある（audit 45〜135） | 記録の要約値の先頭一文字を変えた値 → 不一致。手本の `workers=4` を 8 にした写し → その行が差に出た。`ft_patience` を 5 にした写し → 差に出た |
| b | 決定性 | 両 rank で一致（sha256 3cd3c19c…・4a89babb…） | 二回目の 100 番目の値の最下位 bit を反転 → 不一致、最初の差は 100 番目 |
| c | 5 本の学習 | 5 本とも収束規則で停止（上限 36 に未到達）。値・時間・収束の記録あり。COCO の重みを読んだ行が 5 本ともある（audit 172〜186） | 実行しなかった。既知の挙動を引く: env-facts 53 行（`main.py` はファイルでなければ読み込みを飛ばし、行が出ない）。本契約の検出塔の設定 `train_search.py` は経路がファイルでなければ `FileNotFoundError` で止まる |
| d | values.json | 欠けたキー 0、UNKNOWN 0（`check_values.py` exit 0） | `detector.seed123.AP_signature` を消した写し → 欠けとして出た |
| e | 他の使用 | 5 本とも `foreign_gpu_use` は空の列。全区間 8,275 標本で本契約以外の標本 0 | `proc_enum.py`: 実在の `/usr/bin/zsh` → 5、存在しない経路 → 0 |
| f | test と置き場 | test 動画 04・05・07 との共通 0（検出塔 3 本・工程塔 24 run）。同期の型 0 件（313 ファイル） | 04 を足した集合 → 共通 1。`experiments/x/foo.npy` → `*.npy` に当たる |
| g | 道具 | 既定の挙動の試験 17 passed（`test_tower_search_overrides.py` 8 件 ＋ `test_tower_search.py` 9 件） | 既定の識別子を変えた写しで試験が落ちる（`test_breaking_control_changed_default_fails`） |
| h | PR | #286、base phase0、分岐 `feat/hostdiff-andrew`、Draft でない | — |

## 4. 実測（主の値。全件は REPORT.md）

| run | 主の値 | 一歩の秒数の中央値 | wall_s | lr 低下 / 停止の epoch | 本契約以外の GPU の使用 |
|---|---|---|---:|---|---|
| 工程塔 seed 42 | J_mean 0.5903（J_max 0.6589） | micro 0.5962 s・optimizer 2.4086 s | 8,950.4 | 15 / 19 | なし |
| 工程塔 seed 123 | J_mean 0.6189（J_max 0.6373） | micro 0.5964 s・optimizer 2.4094 s | 10,695.3 | 12 / 23 | なし |
| 検出塔 seed 42a | mAP 0.7157（標的群 0.7931） | optimizer 0.4189 s | 24,770.5 | 13 / 21 | なし |
| 検出塔 seed 42b | mAP 0.7286（標的群 0.8084） | optimizer 0.4182 s | 19,325.4 | 11 / 16 | なし |
| 検出塔 seed 123 | mAP 0.7242（標的群 0.8032） | optimizer 0.4179 s | 19,320.4 | 10 / 16 | なし |

## 5. 起票者の誤り

- **check_does_not_check**: P2 `cuda_ext_loaded` は本体 `.venv` の Python で `models.bricks.relation_transformer` を import するが、`fvcore` は `.venv-relation-detr` にだけある。指示どおりに回すと、検出塔の環境が正しくても必ず FAIL になる（audit 17〜21）
- **asserted_without_measuring**: SPEC §3 は andrew の MS-Deform-Attn の `.so` を 79b55a8a… としたが、P2 の import が共有の torch_extensions の置き場で拡張を作り直す。プリフライトを回すだけで値が d1d9d1ac… に変わり、記録の値の写しは残らない（audit 30〜43）
- **asymmetric_comparison**: 手本の run は二枚へ配る変更 3c562015 より前の `run_tower_search.py` の版で回った。今の版の並べ方（後段を二枚に配る）で回すと起動の設定が手本と違う。SPEC はこの版の違いに触れていない（audit 101〜104）

## 6. 逸脱

1. P2 の FAIL を、利用者の承認（「2」）で構造的な FAIL として通した（audit 17〜21）
2. task-start の起点 d145854e が PR #284 を含まなかったため、commit の無い分岐を `--ff-only` で 7f9e31f6 へ早送りした（audit 23〜28）
3. MS-Deform-Attn の `.so` がプリフライトと確認の import で作り直された。本測定は d1d9d1ac… で回った（audit 30〜43）
4. 工程塔の `source_sha256` が手本と違う。手本の commit の後に `scripts/stage1_ptower.py` へ新しいヘッドの候補が足された。SPEC §3 のコードの行に従い、起点のコードのまま回した。既存の候補の出力が同じことは試験が固定の要約値で確かめる（audit 152〜157、217）
5. 管理台本を手本の版の順（後段は一枚目の GPU で順に）に合わせた（audit 101〜104）
6. 環境変数 `TOWER_SEARCH_TASK`・`TOWER_SEARCH_OBSERVER`・`TOWER_SEARCH_PHASE_PUBLISH`・`TOWER_SEARCH_SEED` を足した（識別子・記録・置き場・W&B の seed）（audit 120〜131）
7. 検出塔の経路を 60 歩の対照で一度確かめた（本測定に数えない）（audit 159〜164）
8. 利用者の指示で、測定の途中（11-03 13:51）に記録を commit・push した（audit 190）
9. `aggregate.py` の `code_commit` を、run の commit の集合と集計の時の HEAD に分けて書く形に直した。`aggregated_at` は values.json を含む commit の一つ前を指す（audit 194）
10. config の実物の比べで、seed 123 の `best_epoch`・`checkpoint_sha256`・`cache_sha256` は学習の結果に由来する値と判断し、起動の設定の差に数えなかった（audit 217）

## 7. 想定外・UNKNOWN

- UNKNOWN の欄は無い
- 全試験は 7 failed・989 passed。7 件は起点 7f9e31f6 でも通っていない（2 枚の試験は NCCL_P2P_DISABLE=1 で通る）（audit F-6）
- 段ごとの壁時計（学習後の評価・特徴・ヘッド）は 5 秒の刻みで丸まる（audit 168）。一歩と epoch の秒数はこの刻みを受けない
- 検出塔 seed 42 の一回目と二回目は、値と停止の epoch（21 と 16）が違った。理由は確かめていない
- 工程塔 seed 42 の fine-tune だけ、記録の commit が fdbb6ff6 である（起動が次の commit より前）。学習のコードは同じ（audit 189）

## 8. 送出

- PR #286
- `make task-report`: 終了コード 0（audit F-7）
