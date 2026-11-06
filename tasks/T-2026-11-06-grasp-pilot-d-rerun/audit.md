# audit — T-2026-11-06-grasp-pilot-d-rerun（非公式の測定。関門と設計の判断に使わない）

ホスト bengio。時刻は JST（ホストの時計は UTC なので +9 時間して書く）。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-grasp-pilot-d-rerun`。前契約の置き場
（`T-2026-11-05-grasp-tower-rebuild`・`T-2026-11-01-grasp-pilot-d`・`T-2026-11-06-grasp-pilot-arms`）は読むだけ。
重ねの BODY は `OV=/home/ubuntu/slocal2/s2fix-bengio-body`。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/grasp-pilot-arms`（PR #297 は統合済み）。`feat/grasp-pilot-d-rerun` は手元にも遠隔（`ls-remote`）にも無く、
  契約の履歴も `.sync-pause` も無かった（2026-11-07 00:1x JST）
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 320b4677）→ 全区分 0 件、`分類: 通す`（作業ツリーは清浄）
- `source .venv/bin/activate && source scripts/load_env.sh && make task-start` → `分岐を作成: feat/grasp-pilot-d-rerun（起点 origin/phase0）`、
  **`.sync-pause を作成`**（この契約が置いた目印）、契約を台帳から取り込み、`完了。`
- `make task-validate` → `OK`、`1 task(s), 0 failed`
- 参照の解決: `inject_verbatim` の 8 節（prohibitions・issuer_cautions・env_p0・folds・split・eval_recipe・det_groups・crossfit）は
  `context/conventions.md`（`git log -1` 2d946b07 = 契約の conventions_rev）の原文を読んで適用した。denominator・frozen_source・sigma_policy の参照は無い
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。SKIP: P2・P3（契約に記載なし）、P4・P5・P13・P14（kind=analysis で対象外）、
  P12（解決前提の参照なし）。P9 spec_lint は該当なし。P11 gpu_free は compute 0 件

## Task A — 開始状態（G1）

記録の原本は `$S/start/`。

### A-1 分岐と起点、PR 295・297 の内容（`a1248.txt`）

    $ git branch --show-current; git merge-base HEAD origin/phase0; git rev-parse origin/phase0 HEAD; git log --oneline origin/phase0..HEAD | wc -l
    feat/grasp-pilot-d-rerun / 320b4677…（merge-base・origin/phase0・HEAD が同じ）/ 0 件
    $ git ls-tree --name-only origin/phase0 -- <目録> g5_build.py run_pd_grasparms.sh arms_aggregate.py arms_check_inputs.py <PR295 と PR297 の RESULT.md>
    7 件すべて在る
    $ git log --oneline -1 --grep='#295' origin/phase0 → e389abe5 Merge pull request #295 …
    $ git log --oneline -1 --grep='#297' origin/phase0 → 7828ab88 Merge pull request #297 …
    $ git show origin/phase0:experiments/analysis/grasp_tower_rebuild/signals_manifest.json | sha256sum
    1717ae6963ef692faac5015ad9c14ba91162d7e9ad17db4447c874ecad26f090（四本目 SPEC の 1717ae69… と同じ）

### A-2 開始前から在る未追跡

無視されていない未追跡は `tasks/T-2026-11-06-grasp-pilot-d-rerun/{SPEC.md,spec.yaml}`（task-start が取り込んだ契約そのもの）だけ。
開始前から在る他の未追跡は無く、`.git/info/exclude` への追加も不要だった。

### A-3 GPU の使用（`a3_gpu.txt`・`a3_procs.txt`・`a3_procs.json`）

    2026-11-07 00:19 JST
    0, 39 MiB / 49140 MiB, 0 %, 220 W 上限, NVIDIA RTX A6000
    1, 37 MiB / 49140 MiB, 0 %, 220 W 上限, NVIDIA RTX A6000
    $ nvidia-smi --query-compute-apps=…   → 0 件
    $ nvidia-smi -i 7 …                    → No devices were found（rc 6。存在しない番号で 0 件）
    $ python3 scripts/grasppilot/proc_enum.py  → n_compute 0（単独実行）
    $ proc_enum.py --match-exe /usr/bin/zsh → 9 件、--match-exe /nonexistent/bin/python9 → 0 件

- 最初に `| python3 -c …` のパイプで回したとき `n_compute 1` が出た。中身は自分のパイプ側の `python3` で、単独で回すと 0 件
  （注意 6: 実行基盤の包み込みや自分の命令行を拾う）。本契約以外の compute の使用は無い
- 全体の使用量（39・37 MiB）と一覧の和（0 MiB）の差は駆動の常駐分。利用率 0 %

### A-4 記憶領域（`a1248.txt`）

    $ df -B1 /home/ubuntu/slocal2 → Available 1,291,676,147,712 B（使用 83%）
    $ du -sb 三本目の保存先 四本目の保存先 前契約（tower-rebuild）の保存先 → 18,137,294,352 B・7,295,871,118 B・22,410,806,115 B

- 見積もり: 案 D 2 本（三本目は 3 本で 18.1 GB なので 1 本 約 6 GB）で 約 12 GB、案 B 2 本（四本目は 6 本 + 案 A で 7.3 GB）で 約 2.5 GB、
  塔単独の予測などで 約 1 GB。合計 約 16 GB は空きの 2% 未満。足りる

### A-5 試験と仮想環境（`a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped, 26 warnings in 45.07s
    失敗の名前（11）: test_check_spec::test_teacher_detection_rate、test_engines::test_mmdet_trainer_eval_recipe_in_metrics、
      test_fetch_task::test_rejects_unknown_file_name、test_research_logger の 4 件、test_stage1_ptower_heads::test_existing_candidates_match_baseline[A,B,C,linear]
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0（108 行）
    .venv-relation-detr a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090（72 行）
    （四本目の audit A-5 の値と一致。失敗の名前の集合も四本目と同じ 11 件）

### A-6 重ねの BODY の照合・電力の上限・装置の型（`a6_reldetr_*.json`・`a6_weights_sha256.txt`・`a1248.txt`）

| 場所 | source_files | source_tree_sha256 | all_files | all_tree_sha256 |
|---|---:|---|---:|---|
| 三本目の記録（andrew・重ねの BODY とも、三本目 audit A-5） | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… |
| 本契約: 重ねの BODY `$OV/third_party/Relation-DETR` | 142 | 2f08e5213cb5c377c576172b0d39964f46fb6afb80532ce11f8bad7437f1e393 | 155 | 20f15c061b435ce44d45f3da2e2b225548fffaea0422bbcc2aedfb72775c94f6 |
| 本契約: bengio main `m2/third_party/Relation-DETR` | 142 | 同じ | 155 | 同じ |

- 重ねの BODY は三本目の記録と一致。**bengio main も同じ値になっていた**（三本目の時点では 127 ファイルで違った。T-2026-11-02-bengio-align-andrew で andrew と一致させた後）
- パッケージ（importlib）は両 venv で 72 件・`8f08a2457e681d6d…`（三本目の値）。COCO の重み `2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff`、196,140,106 B（三本目と同じ）
- 電力の上限: GPU 0・1 とも `NVIDIA RTX A6000`、220.00 W（既定・最大 300.00 W）

### A-7 禁止の場所の開始時の要約値（`digest_start/summary.json`、道具 `scripts/grasppilot/rerun_digest.py`）

全ファイルの内容の sha256（シンボリックリンクは辿らず、リンク先の文字列）を取り、根ごとの木の要約値にした。取得は 00:22 JST に開始（`start/digest_start_begin.txt`）、00:3x JST に完了（GPU は使っていない）、読み取りエラー 0。

| 根 | ファイル数 | 木の要約値（先頭 16 桁） |
|---|---:|---|
| data（raw・external・annotations・splits） | 236,176 | 476386f7b0e62919 |
| experiments（baselines・phase1・analysis） | 28,870 | 644996c9e0b84a79 |
| third_party | 196 | 1fa50fecc8e3f011 |
| .venv | 28,349 | 4f0e373707aa9df3 |
| .venv-relation-detr | 18,485 | cbaa8a96d87e245c |
| stage2pilot_store（本契約の保存先を除く 10 契約） | 1,610 | 7538fc3ae6a56dca |
| 重ねの BODY（$OV） | 174 | 5b58a48c16619bd0 |
| runindex | 2,377 | 47bc1c22278812c2 |
| tasks（本契約のフォルダを除く） | 1,859 | d7e9e7dd7202ab38 |
| context | 10 | 555affbe571510e9 |
| src / configs / scripts | 129 / 98 / 370 | 82927259… / a8543a9a… / ed69bccb… |

- `__pycache__` は除いた（実行で書かれうる派生物。入力ではない）。本契約のフォルダ名（`T-2026-11-06-grasp-pilot-d-rerun`）は、保存先と tasks の根では除外した（自分が書く場所）
- 道具の対照（小さな木で。`scratchpad/dg`）: 無変更 0 件／1 バイト追記で `changed` 検出／削除で `removed` 検出／想定外の追加で `added_unexpected` 検出／許可された追加は 0 件。
  終了時に `compare` で比べる（Task E-1）。許可する追加は本契約の `allow_write` の経路と、本契約の新しいスクリプト・文書だけ

### A-8 契約の版

- `contract.conventions_rev` 2d946b07 = `git log -1 -- context/conventions.md`
- `meta.created_from.runindex_commit` 68befc3b = `git log -1 -- runindex/`。件数 index 2,363・experiments 1,130・verdicts 1,736（見出し行を除く）で一致
- 食い違いが無いので `meta.amendments` は空のまま

**G1: pass**（分岐 feat/・起点 origin/phase0・PR 295・297 の内容が起点に在る・本契約以外の compute 0 件・重ねの BODY が三本目の記録と一致・空き・失敗の名前・要約値・電力の上限を記録）

## Task B — 材料（G2）

記録の原本は `$S/b/`。

### B-1 目録の信号と G の重み（`b1_inputs.json`・`b1_inputs.txt`、道具 `scripts/grasppilot/arms_check_inputs.py` を変えずに使った）

    $ .venv/bin/python scripts/grasppilot/arms_check_inputs.py --out $S/b/b1_inputs.json
    一致 26 / 26（G の重み 3、案 A の g 8、案 B の view 8 と地図 3、一本目の正解の g 4）
    $ … --corrupt-copy $S/b/corrupt （対照: pred_noCF_val を写して 100 バイト目を反転）
    一致 25 / 26（NG A_g pred_noCF_val）

### B-1・B-5 目録の D_q（`b5_dq.json`、道具 `scripts/grasppilot/rerun_check_q.py`。本契約で新しく書いた読むだけの道具）

| 項目 | 実測 | 目録 |
|---|---|---|
| q（`q_CF_train.npz`）の sha256 | ab5dc79ec36bef77cb8bc4250649900594fc40f34f93784a6f563fc50d6b4b47 | 一致 |
| 入れ替えの q（`q_shuffle_CF_train.npz`）の sha256 | 722b93711149e0f65e9aa4188b7d4449e0b013dd125a2655f42f057698ccbfc5 | 一致 |
| 枠の数 | 32,272（q・入れ替えとも。ann_ids は昇順で同じ） | 32,272 |
| 行の和の範囲 | [0.99999996, 1.00000004]（float64 で足した値）。目録は [0.9999998807907104, 1.0000001192092896]（float32 の足し算） | 許容差 1e-6 で一致 |
| 値の範囲 | [0.0, 1.0] | [0.0, 1.0] |
| 折り A の train の注釈の枠 | 32,272、**欠け 0・余り 0**。動画は 01・02・03・06・08・11・12・13・14・15（test の 04・05・07 は混じらない） | — |
| 入れ替えの作り直し | 規則（画像 id 昇順、画像ごとに `rng.permutation`、seed 42）で q から作った表と**最大差 0.0**。画像ごとに q の行の多重集合が保たれる | 目録の shuffle_rule |
| 枠が一つの画像 | 575（画像 9,618 のうち） | 三本目の 575 と同じ |
| 元と同じ枠に戻った割合 | 全体 0.2996715、複数枠の画像だけ 0.2869672（枠 31,697） | 三本目の 0.2997 と同じ |

- 対照（`b5_dq_controls.txt`）: q を 1 バイト反転した写し → 読み込み自体が失敗（`load_error`、ok false）／ann_ids を 1 つずらした写し → `missing_in_q 1`・`extra_in_q 1`（ok false）／入れ替えを seed 43 で作った写し →
  sha256 不一致・作り直しと不一致（ok false）。本番は ok true
- 道具の不備を 1 回直した: 最初の版は ann_ids のずれた写しで、欠けを数える前に再構成が KeyError で落ちた。欠け・余りがあれば結果を記録して `ok false` で止める形にし、対照をやり直した

### B-2 塔単独の val の再現（`experiments/analysis/grasp_pilot_d_rerun/repro/run_repro.sh`・`b2_summary.json`。`b2_summary.json` の書き込みは 00:40 JST）

- **基準の BODY は三本目の重ねの BODY（EGO_BODY=$OV）にした。** 四本目は m2 本体を使ったが、A-6 のとおり両者の中身の要約値は同じ
- 台本は四本目の `run_repro.sh` の写し（BODY を `$OV`、置き場を本契約、工程塔の項を除く）。拡張の読み込み: `[env] torch 2.1.2+cu118 cuda True ms_deform_attn_ext True`（`repro/env_check_det.txt`）

| 塔 | overall mAP | 標的群 AP | 陰性対照群 AP | 記録（SPEC §1）との差（overall／標的群） |
|---|---|---|---|---|
| 検出塔 seed 42 | 0.7273450248 | 0.7950748009 | 0.6726631818 | **+2.5e-8／+8.6e-10（許容差 0.005 の中）** |
| 対照: 検出塔 seed 123 | 0.7288631052 | 0.8234320706 | 0.6701777002 | +0.0015／**+0.0284（標的群が許容差 0.005 を超える）** |

- 塔単独の予測は `$S/b/plain_val_preds_seed{42,123}.json.gz`（Task C の案 B の恒等性の基準）

### B-3 案 D の補助損失なしの腕（三本目）の code_sha256（`b3_d_code_now.txt`・`b34_code.txt`）

    $ (cd scripts/grasppilot && sha256sum grasp_aux_d.py d_model_config.py d_train_config.py) と
      experiments/phase1/grasppilot3_d_{none,gteach,shuf}_ep15_seed42/code_sha256.txt を比べた
    3 腕とも一致（653faeb5… / aa019384… / 2edc8879…）

- GPU の使い方も三本目の記録（`config.yaml`）と同じ: 1 枚・batch 2・ため込み 2・fp16・15 epoch・lr 1e-4（epoch 10 から 1e-5）・seed 42・COCO 1x 初期化、ホスト Bengio、RTX A6000 × 2、220 W
- **条件を満たすので補助損失なしは回し直さない（5 本目なし）。** 三本目の値（0.7227621 / 0.8165308 / 0.6728241）を使う

### B-4 案 B の経路の code_sha256（`b4_B_code_now.txt`・`b34_code.txt`）

    $ sha256sum pd_grasp.py pd_grasp_model.py grasp_signals.py train_t1b.py pd_graspmap_{d5,pred5,d10}.py（7 件）と
      experiments/phase1/grasparms_B_*_ep4_seed42/code_sha256.txt（四本目の 6 run）、grasppilot2_B_{empty,gt}_ep4_seed42/code_sha256.txt（二本目、andrew）を比べた
    8 run すべて一致
    対照: 先頭の 1 文字を変えた写しは不一致

- 空と正解の腕を本契約で回しても、四本目の予測の腕と同じ経路になる。止める必要は無い

### 本契約の台本の写し（`b/script_diffs.txt` に原本との差分）

| 新しいファイル | 原本 | 変えた点 |
|---|---|---|
| `scripts/grasppilot/run_d_arm_rerun.sh` | `run_d_arm.sh` | 契約の識別子・保存先・標的の経路（目録の q）・run の名前（`graspd2_*`）・腕の一覧（none を除く）だけ。コード・学習設定・起動の引数は同じ |
| `scripts/grasppilot/d_finalize_rerun.py` | `d_finalize.py` | `TASK` の値と docstring の例だけ（保存先 `S` は `TASK` から決まる） |
| `scripts/grasppilot/run_pd_grasparms_rerun.sh` | `run_pd_grasparms.sh`（四本目） | `TASK` と、腕 `gt`（`GMAP=gt`、設定 `pd_graspmap_d5.py`。二本目の `run_pd_grasp2.sh` と同じ）の追加だけ。code_sha256 の 7 ファイルは変えない |
| `scripts/grasppilot/rerun_check_q.py`・`rerun_digest.py` | （新規） | 本契約の確認用。読むだけ |

既存のスクリプトの既定の挙動は変えていない（原本は一字も変えていない。`scripts/` の終了時の比べで確かめる）。

## 停止して利用者に諮った件（Task B の途中、2026-11-07 00:40 JST に観測）

- B-2 の再現が終わった後、bengio の GPU に**本契約以外の使用**が現れた（`$S/logs/external_gpu_use.txt`）:
  00:40〜00:41 JST の観測は GPU0 が 2.7〜6.8 GiB・利用率 0〜23 %・43〜119 W、GPU1 が 0.5〜1.1 GiB・31〜87 W で断続的。本契約の python は 0 件、`nvidia-smi` の compute 一覧も 0 件
  （コンテナの中で外のプロセスが見えない。SPEC §2 の装置の項のとおり、全体の使用量と一覧の差で見る）。別のセッションか他の利用者の使用とみられる。**止めていない（SPEC §7-7）**
- 契約の停止条件（Task A-3・§9）に当たるため GPU の作業を止めて利用者に諮った。選択肢は「観測しながら続行／終わるまで待つ／中止」。
  **利用者の決定: 外部の使用が終わるまで待つ**（回答は 01:2x JST）。両 GPU が 100 MiB 以下を 3 分間続けて保つのを見張る（`$S/logs/gpu_wait.csv`、01:28 JST から）。
  01:28〜01:30 JST の観測: GPU0 8,247 MiB・利用率 100 %・220 W、GPU1 7,208〜8,004 MiB・100 %・218 W（本格的な学習とみられる。終わる時刻は UNKNOWN）
