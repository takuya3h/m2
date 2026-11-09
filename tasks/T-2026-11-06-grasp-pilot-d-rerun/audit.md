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

## 外部の使用の終了と Task C の開始（2026-11-07 03:55 JST）

- 待機の見張り（`$S/logs/gpu_wait.csv`）は、外部の学習（02:28 JST ごろから両 GPU が約 25 GiB・利用率 100 %）が終わった後、**03:51:57 JST が最後の外部の観測**で、
  03:55 JST に「両 GPU が 100 MiB 以下（39・37 MiB）を 3 分間維持」の基準を満たした（`$S/logs/external_gpu_clear.txt`）。compute 一覧は 0 件、利用率 0 %
- 学習中の見張り `experiments/analysis/grasp_pilot_d_rerun/taskD/gpu_watch.sh` を 03:55 JST に起動した（60 秒ごと、`$S/logs/gpu_watch.csv`）

## Task C — 確かめ（G3）

台本は `experiments/analysis/grasp_pilot_d_rerun/taskC/`。GPU 0・1 を並行（03:55〜04:25 JST）。記録 `$S/logs/c_gpu{0,1}.log`

### C-1 案 D の確かめ（`taskC/c1_check.json`、`run_caseD_check.sh`。道具 `d_check.py` を変えずに使った。標的は目録の q、sha256 ab5dc79e…）

    $ CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/d_check.py --q $RB/q_CF_train.npz --out taskC/c1_check.json   （重ねの BODY、rc 0、ms_deform_attn_ext True）
    data_identical True（64 項目で元の CocoDetection と画像・枠・ラベルが一致）、q_matches_table True（64/64、反転 33 件は左右を入れ替えた値）、
    flip_probe_controls True（p=1 で 20/20、p=0 で 0/20）
    init_equal True、coco_changed_params True
    w0_total_equal_base True（重み 0 の全損失・全項が頭の無い元の模型と一致。4 batch）、w0_max_abs_diff 0.0、w0_max_abs_diff_plain_same_instance 0.0、base_repeat_max_abs_diff 0.0
    w0_head_grad_zero True、w03_aux_enters True（全損失 − 検出の損失 = 0.3972、0.3811、0.3611、0.3507）、w03_head_grad_positive True（2.293、2.084、2.734、2.590）
    matched_eq_n_gt True（対応づいた枠 = 正解の枠: 7、4、9、10）、indices_eq_recomputed True

- **COCO の重みを読んだ記録**: `load_record`（`c1_check.json`）で要約値 d2586acb… → 6a26aac9…（changed true、missing は `grasp_head.weight`・`grasp_head.bias` だけ、unexpected なし）。三本目と同じ値
- 空振りでないことの確認: 0.3 で 全損失 − 検出の損失 が 0 でない（上の 4 値）。重み 0 の一致は「頭の勾配 0」と「元の模型の二度の実行の差 0.0」とあわせて見ている

### C-1 main.py を通した試走（`experiments/phase1/graspd2_smoke*`。腕に数えない。train 8 枚・val 4 枚の注釈 `$S/smoke_ann/`）

| 試走 | 内容 | 結果 |
|---|---|---|
| `graspd2_smoke`（GPU 0） | 重み 0.3、12 epoch、目録の q | rc 0。`load pretrained from …/s2fix-bengio-body/…coco_1x.pth` 1 行。lr（歩 0）: epoch 0 は 3.3e-05（warmup）、1〜9 は 1e-4、10・11 は 1e-5。歩ごとの記録 48 行、各歩の特徴のフックは 2 回、対応づいた枠 = 正解の枠（全歩）、重み 0.3、補助損失（重みの前）1.318 → 0.926。`d_finalize_rerun.py` も rc 0 |
| `graspd2_smoke_nococo`（GPU 1） | 陽性対照。COCO の経路を `/nonexistent/…` にし、`GRASP_ALLOW_MISSING_COCO=1` で設定の停止を外す。1 epoch | rc 0。`load pretrained` の行 0、`load_record.jsonl` が無い（**読み込みの記録が消える**） |

- コードの写し `$S/code/9b1ecd5fa432ea69/`（`code_sha256.txt` は 653faeb5…・aa019384…・2edc8879…。三本目と同じ中身の要約値）

### C-2 案 B の恒等性（`taskC/caseB/identity_*.json`、`run_caseB_identity.sh`、道具 `pd_grasp_eval.py`。基準は B-2 の塔単独の予測 seed 42）

| 腕 | 学習前の mAP | score の差の最大・枠の差の最大・ラベルの食い違い | 学ぶ集合 |
|---|---|---|---|
| 空（`--mode zero`） | 0.7273450248 | 0.0・0.0 px・0 | `phase_iface.weight` 10,240。外のパラメータを一つ混ぜると不一致 |
| 正解（`--mode gt`） | 0.7273450248 | 0.0・0.0 px・0 | 同 |

| 陽性対照（界面の重み N(0, 0.05²)） | 界面の重みの絶対値の最大 | mAP | score の差の最大 | ラベルの食い違い |
|---|---|---|---|---|
| 正解（判定に使う） | 0.2034 | 0.7278873 | **0.3827** | **329,465** |
| 空（記録だけ。判定に使わない） | 0.2034 | 0.7273450 | 0.0 | 0 |

- 空の腕は入力が零のため、重みを変えても出力が変わらない（SPEC のとおり。記録のみ）。正解の腕では出力が変わる
- 凍結部の要約値 `non_interface_digest` は 4 件とも 4fed8516…（四本目の値と同じ）

### C-3 案 B の台本の試走（`$S/smoke/grasparms_B_{gt,empty}_ep4_seed42_smoke`。腕に数えない）

- `gt`（GPU 0）: rc 0、`ms_deform_attn_ext True`、`code_sha256.txt` が B-4 の 7 件と一致、`phase_grad=True init_mAP=0.8917 => PASS`。台本に足した `gt` の腕が通る
- `empty`（GPU 1）: **rc 2。`phase_grad=False … => FAIL`**。試走の判定（界面の重みに勾配が届くか）は、入力が全零の空の腕では勾配が 0 で原理的に満たされない
  （四本目の起票者の誤り 3 と同じ性質）。台本の欠陥ではなく、`--smoke` を付けない本番の学習には使われない判定。`code_sha256.txt` は一致
- 記憶の山（5 秒ごとの観測 `$S/logs/c_mem.csv`、384 点）: GPU0 最大 15,448 MiB（案 D の試走・確かめ）、GPU1 最大 14,356 MiB（案 B の評価の恒等性）。
  案 D 本番の実測は三本目で 12.9 GiB、案 B 本番は四本目で 1 本 7.4〜8.3 GiB。**1 枚に案 D 1 本 + 案 B 1 本で 約 24 GiB（48 GiB の半分）と見込む**

**G3: pass**（案 D: 重み 0 で一致・0.3 で入る・対応づいた枠 = 正解の枠・COCO を読んだ記録と消える対照。案 B: 空と正解で学習前の出力が塔単独と一致、正解で重みを変えると出力が変わる）

### 載せ方の決定（SPEC §3.3「記憶の実測で決め、記録する」）

- 案 D の 2 本は 1 枚ずつ。案 B の 2 本は、**案 D と同じ枚に 1 本ずつ載せる**（GPU 0: 案 D G を教師 + 案 B 空、GPU 1: 案 D 入れ替えた教師 + 案 B 正解）。
  山の見込みは 1 枚 約 24 GiB で 48 GiB に収まる。案 D の後に回すと全体が 約 4〜5 時間延びる。2 枚で対称にして腕の間の載せ方の差を小さくする
- ただし 1 枚に 2 本載せると、案 D の 1 本の所要が三本目（単独 10 時間 05 分〜10 時間 26 分）より延びうる。値は seed と設定で決まり、載せ方では変わらない設計だが、
  GPU の共有による数値の揺れの有無は UNKNOWN（四本目は 1 枚 3 本並行だった）

## Task D — 学習（起動 2026-11-07 17:02 JST）

台本は `experiments/analysis/grasp_pilot_d_rerun/taskD/run_all.sh`。記録 `$S/logs/{run_all.out,d_*.out,b_*.out,gpu_watch.csv,d_launch_time.txt}`

### D-0 起動の経緯

- 04:58 JST に、外部の使用が繰り返し現れ 12 時間続く空きは来ない可能性が高いと報告して利用者に諮り、**「長い空き（例: 両 GPU が 6 時間空く）を待つ」**の決定を得た
  （回答は 08:3x JST より後。待機の見張り `launch_clear_seconds.txt` は 21,600 秒）。前のセッションが終わり、待機の見張りは止まった
- 2026-11-07 17:02 JST に利用者から「あいた」と連絡があった。**この連絡を起動の合図として扱い**、6 時間の連続の空きの基準（21,600 秒）は満たさないまま起動した（逸脱）。
  確認した状態（17:02 JST）: GPU 0・1 が 39・37 MiB・利用率 0 %・compute 一覧 0 件、`gpu_watch.csv` で連続の空き 466 秒（16:54 JST から）
- 載せ方は Task C の決定どおり: GPU 0 = 案 D G を教師 + 案 B 空、GPU 1 = 案 D 入れ替えた教師 + 案 B 正解。起動は 30 秒ずつずらし、
  開始（UTC）は 案 B 空 08:03:43、案 B 正解 08:04:13、案 D の 2 本 08:04:24（JST は +9 時間）

### D-1 起動直後の観測

- 案 D（重ねの BODY 経由）と案 B（m2 本体経由）が同じ名前の拡張 `MultiScaleDeformableAttention` を別のソース経路から同時に読み込み、共有のビルド先
  `~/.cache/torch_extensions/py311_cu118/` で再ビルドが入った（ソースの中身は両経路で同一。`nvcc`・`cicc` が起動後 数分動き、`ninja` が `build.ninja` を書き直した）。
  4 本とも `ms_deform_attn_ext True` で学習ステップに入った（17:09 JST ごろ）。ビルドの競合による失敗は無かった
- 学習ステップに入った時点の GPU の使用量は 1 枚 約 19.8 GiB（見込み 約 24 GiB の範囲）。案 D の epoch 0 の見込み時間は 1 時間 09 分〜1 時間 12 分（250 歩目の eta）

### D-2 学習中の観測（17:10〜21:30 JST）

- **GPU の記憶（17:20〜17:29 JST の山。訂正あり）**: 学習ステップに入った時点は 1 枚 約 19.8 GiB。17:20 JST に GPU0 が 36.5 GiB、17:26 JST に GPU1 が 37.0 GiB、
  17:28〜17:29 JST に両 GPU が 37 GiB になり、17:30 JST に両 GPU とも 21 GiB へ戻った（`$S/logs/gpu_watch.csv`、1 秒間隔の確認 `spike_probe.csv`）。
  **当初は「自分の run の確保量の増加で定着した」と書いたが誤りだった。** 片方ずつ現れて数分で消えたので、**外部の短い使用**とみる（自分の run は 17:30 以降 約 21〜22 GiB で一定）。
  OOM は起きていない。プロセスごとの使用量はコンテナの中から見えないため、出所は UNKNOWN（外部とみる根拠は、現れ方と、その前後で自分の run の使用量が一定だったこと）
- **見張りの不具合（自分側の欠陥）**: 学習の終了を見張る Monitor の台本が zsh で実行され、`RUNS="a b c d"` が単語分割されず 1 要素になって、終了・異常の検出が効かなかった。
  案 B の 2 本の完了（20:xx・21:xx JST）を通知できず、進行の確認で気づいた。bash の台本 `$S/logs/watch_runs.sh` に直し、終わった 2 本で `RUN終了` が出ることを確かめた（陽性対照）。
  学習そのものへの影響は無い（見張りは読むだけ）。メモリ警告の閾値は最初 36 GiB だったため上の増加で誤警報が出て、46 GiB に直した
- **案 B の 2 本の完走**（`experiments/phase1/grasparms_B_{empty,gt}_ep4_seed42`）: 開始 UTC 08:03:43・08:04:13、終了 UTC 12:20:18（空）・12:03:30（正解）、rc 0、結果の epoch 3（4 epoch 目）、
  凍結部の前後一致 True、`ms_deform_attn_ext True`、host Bengio。所要は 空 4 時間 16 分・正解 3 時間 59 分（四本目の 5 時間 15 分〜5 時間 33 分は 1 枚 3 本並行。本契約は 1 枚に案 D との 2 本）
  - 空: overall 0.7273450 / 標的群 0.7950748 / 陰性対照群 0.6726632。全 epoch で 0.7273、界面の重みは 0.0 のまま（入力が零のため。塔単独と同値）
  - 正解: overall 0.7367827 / 標的群 0.8115416 / 陰性対照群 0.6770576。epoch ごと 0.7345・0.7353・0.7352・0.7368、界面の重みの絶対値の最大 0.4020

### D-3 学習中に現れた外部の GPU 使用（2026-11-07 23:18 JST〜11-08 09:12 JST。**記録して諮る条件（SPEC §9）に当たるが、その場で諮れなかった**）

案 B の 2 本が終わった後、案 D の 2 本だけの GPU の使用は 約 14.25 GiB（両 GPU）だった。`gpu_watch.csv` の時系列:

| 時刻（JST） | GPU0 | GPU1 | 出来事 |
|---|---|---|---|
| 11-07 23:06 | 14,251 MiB | 14,249 MiB | 案 D の 2 本だけ |
| 11-07 23:18 | 26,976 MiB | 26,874 MiB | 両 GPU が同時に増え始める |
| 11-07 23:19〜23:23 | 40,046 MiB | 39,950 MiB | 両 GPU で +25.8 GiB ずつ（外部の学習で見た 約 25〜26 GiB と同じ大きさ）。利用率 85〜100 % |
| 11-08 08:38 | 40,048 MiB | 14,518 MiB | **GPU1 だけ 14.5 GiB へ戻る**（案 D の shuf はまだ走っていて 09:24 JST に終了） |
| 11-08 09:12 | 14,520 MiB | 14,251 MiB | **GPU0 も 14.5 GiB へ戻る**（案 D の gteach はまだ走っていて 09:56 JST に終了） |

- **外部の使用とみる根拠**: 増加が両 GPU で同時で同じ大きさ、減少が案 D の run の終了より前（自分の run の確保量が走行中に 約 26 GiB 急に縮むとは考えにくい）、増加の前後の案 D の使用は 14.25 GiB で一定。
  プロセスごとの使用量は見えないため、断定は UNKNOWN。他のプロセスは止めていない（SPEC §7-7）。OOM は起きず、2 本とも rc 0 で完走した
- **見逃し（自分側の欠陥）**: 04:02・06:02・08:03 JST に 40 GiB を見たが、「案 D の確保量の増加」と誤読した（21:30 JST に 14 GiB だった事実と突き合わせなかった）。
  警告の閾値を 46 GiB にしていたため 40 GiB では警告が鳴らなかった。気づいたのは 11-08 10:0x JST に時系列を出したとき（学習の完了後）。**学習の途中で利用者に諮る機会を逃した**
- **影響**: 案 D の所要が三本目（単独 10 時間 05〜26 分）より長い（gteach 16 時間 51 分、shuf 16 時間 20 分）。案 B と同居した最初の約 4 時間と、外部と同居した約 9〜10 時間が含まれる。
  損失・乱数の経路は GPU の共有で変わらない設計だが、共有による数値の揺れの有無は UNKNOWN。三本目の補助損失なしの値との差は、この違いを含む

## Task E — 集計・検証（2026-11-08 10:00 JST〜）

### E-1 集計と検算（`scripts/grasppilot/rerun_aggregate.py`、`experiments/analysis/grasp_pilot_d_rerun/{summary.json,tables.md,verify.json,testcheck.json,REPORT.md}`）

    $ rerun_aggregate.py aggregate --out summary.json --tables tables.md
    {"missing_D": [], "missing_B": [], "predictions": {"1": true, "2": true, "3": true, "4": true}}
    $ rerun_aggregate.py verify --summary summary.json --out verify.json
    n_runs_in_summary 11、n_runs_present 11、n_fake_runs_present 0（存在しない run の名前 2 つで 0 件）
    recompute_equal true（差を各 run の記録のファイルから別の経路で計算し直して一致）
    preds_recompute_equal_D: none・gteach・shuf とも true（保存した予測から det_metrics.summary で計算し直して一致）
    対照: 案 B の差を 1e-6 ずらした写し・案 D の差を 1e-6 ずらした写しの両方で不一致を検出（control_detects true）
    $ rerun_aggregate.py testcheck --out testcheck.json
    union 01・02・03・06・08・09・10・11・12・13・14・15、test との共通 []、04 を混ぜた対照で ["04"]
    $ rerun_make_report.py   → REPORT.md（数値は summary.json のみから作る）

- 案 D の学習の動画: 案 D の注釈は train 10 本 + val {09, 10}（`metrics.json` の `videos_passed`、`test_overlap` は []）。案 B の train は注釈 `instances_train.json`、val は `logs/eval_meta_val.json` の画像 id から
- 試走の dry-run（三本目の run で道具を試した）は scratchpad だけに書いた。本番の集計の前に案 D の値が三本目の記録（0.7227621 / 0.7265707 / 0.7263878）と一致することを確かめた

### E-2 禁止の場所と試験・仮想環境（`$S/end/`）

- **終了時の要約値**（`end/digest_end/`、取得は 10:02 JST に開始、`rerun_digest.py snapshot`。開始時と同じ 13 根・同じ除外）と `compare`（`end/digest_compare.json`）。
  許可する追加は本契約の `allow_write` の経路（`experiments/analysis/grasp_pilot_d_rerun`・`experiments/phase1/graspd2_*`・`grasparms_B_{empty,gt}_*`）と本契約の新しいスクリプト 7 件だけ:

| 根 | 開始 | 終了 | 変更 | 消失 | 追加（許可 / 想定外） |
|---|---:|---:|---:|---:|---|
| data / third_party / .venv / .venv-relation-detr / stage2pilot_store / runindex / tasks / context / src / configs | 同じ | 同じ | 0 | 0 | 0 / 0 |
| scripts | 370 | 376 | 0 | 0 | 6 / 0（`rerun_make_report.py` は取得の後に追加したので終了の表には無い） |
| experiments | 28,870 | 29,015 | 1 | 0 | 133 / 12 |
| **重ねの BODY（$OV）** | 174 | 174 | **15** | 0 | 0 / 0 |

- **重ねの BODY の変更 15 件は本契約の過失**: すべて `third_party/Relation-DETR/per_class_coco_map/epoch_000〜014.json`。学習エンジン（`util/engine.py` 203〜204 行）が `RELDETR_EVIDENCE_DIR`（未設定なら実行時の作業ディレクトリ `.`）の下へ
  epoch ごとのクラス別 mAP を書く。三本目の台本の写し `run_d_arm_rerun.sh` はこの環境変数を設定せず、作業ディレクトリが重ねの BODY（`cd $OV/third_party/Relation-DETR`）なので、**案 D の 2 本が同じ 15 件を上書きした**
  （最終書き込み 2026-11-08 00:56:15 UTC。2 本が同じパスに書くので epoch ごとに後から終わった方の値）。開始時にあった 15 件は三本目の出力で、**中身は戻せない**（開始時の要約値は sha256 だけ）。
  - 影響: **ソースの木は不変**（`reldetr_digest.py`: source 142 件 `2f08e521…`、all 155 件 `20f15c06…` が三本目の記録と開始時の値と同じ。この道具は `per_class_coco_map` を除く）。この 15 件は本契約の測定の入力ではない（報告の数値は `d_finalize_rerun.py` の `pd_eval.py` と各 run の `metrics.json` から取っている）
  - 防げた誤り: エンジンの出力先を台本の写しを作る前に読んでいれば、`RELDETR_EVIDENCE_DIR` を run の置き場へ向けられた（経路だけの変更で、三本目の規律「違うのは重みと標的の経路と置き場だけ」の範囲）。読まなかった
  - 契約の側の欠陥: SPEC §7-5・§8-i は「重ねの BODY を変えない・要約値が一致」を求めるが、指定した台本の元（三本目）は必ずここへ書く。三本目の A-5 の要約値は `per_class_coco_map` を除く道具だったので気づけなかった
- **他の契約のファイル（本契約が書いたものではない）**: `experiments/analysis/dtower_rerun/tools/*.py` の 12 件（想定外の追加）と `dtower_batch_search/tools/summarize.py` の 1 件の更新（11-07 05:52 UTC）は、学習中に同期で届いた。SPEC §7 の冒頭「同期処理による配布を含まない」のとおり。
  mtime は 11-07 10:15 UTC など、本契約のプロセスが触らない経路。`.sync-pause` は `m2-sync.sh`（git の統合）を止めるもので、ファイルの同期（syncthing）は止めない
- 対照（要約値の道具が空振りでないこと）: 小さな木で 1 バイト追記・削除・想定外の追加を検出（Task A-7）。本番でも上の 15 件と 13 件を実際に検出した
- **BODY の照合の対照**: `$OV/third_party/Relation-DETR` のソース 142 件を写し（`end/tamper/copy`）、変更なしで `source_tree_sha256` が原本 `2f08e5213cb5c377…` と一致、`main.py` に 1 行足すと `bc5d786042ab1a6b…` で不一致
- `make forbidden-check TASK=T-2026-11-06-grasp-pilot-d-rerun` → status fail、changed 154・checked 154、permitted 130、violations 12。**12 件すべて `experiments/analysis/dtower_rerun/tools/*.py`（他の契約の同期で届いた未追跡）。本契約の経路の違反は 0 件**（`end/e_forbidden_full.txt`）。
  forbidden-check は git の作業ツリーだけを見るので、版管理の外の重ねの BODY の変更は拾えない（要約値の比べで拾った）
- 試験: `11 failed, 980 passed, 5 skipped`（307.98 s。要約値の取得とディスクを取り合って遅かった）。失敗の名前の集合は開始時と同じ 11 件（`end/e_fail_names.txt`）
- 仮想環境の一覧の要約値: `.venv` 9c7be5c9…、`.venv-relation-detr` a74c9c78…（開始時と一致、`end/e_pkgs_*.txt`）

### E-3 完了判定（SPEC §8）の実測

| # | 判定 | 実測 |
|---|---|---|
| a | 開始状態 | Task A のとおり。存在しない GPU 7 で `No devices were found`（rc 6）、`proc_enum` は zsh 9 件・存在しない exe 0 件、BODY の照合は 1 行足した写しで不一致 → 満たした |
| b | 材料と再現 | 26/26 一致（破損の写しで 25/26）、D_q の sha256・枠 32,272・行の和・値の範囲が一致、塔単独の差 +2.5e-8 / +8.6e-10、別 seed 123 で標的群 +0.0284 → 満たした |
| c | 経路の一致 | 案 D 3 件・案 B 8 run が一致、1 文字変えた写しで不一致 → 満たした |
| d | 案 D の確かめ | 重み 0 で一致（差 0.0）、0.3 で 全損失 − 検出の損失 0.35〜0.40、対応づいた枠 = 正解の枠、COCO の読み込みの記録（d2586acb… → 6a26aac9…）、経路を無くすと記録が消える → 満たした |
| e | 案 B の恒等性 | 空・正解とも学習前の出力が塔単独と一致（score 差 0.0・枠 0.0 px・ラベル 0）、正解で重みを変えると score 差 0.383・ラベル 329,465 件変わる、空は変わらない（記録のみ）→ 満たした |
| f | 学習 | 4 本とも rc 0 で固定の長さ（案 D 15 epoch、案 B 4 epoch）、epoch ごとの val と案 D の補助損失を記録（`tables.md`）、存在しない run の名前で 0 件 → 満たした |
| g | 記述 | `REPORT.md`・`tables.md`。差を別の経路で計算し直して一致、1e-6 ずらした写しで不一致 → 満たした |
| h | test 不使用 | 通した動画 01・02・03・06・08・09・10・11・12・13・14・15、{04, 05, 07} との共通 0 件、04 を混ぜると 1 件 → 満たした |
| i | 書き込みと試験 | **満たさなかった部分あり**: 重ねの BODY の `per_class_coco_map/` 15 件が変わった（上記）。仮想環境の要約値は一致、失敗の名前は増えず、forbidden-check の本契約の経路の違反は 0 件 |
| j | PR | 下の送出の節 |
