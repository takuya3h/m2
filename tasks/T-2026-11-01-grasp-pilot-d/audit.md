# audit — T-2026-11-01-grasp-pilot-d（非公式の測定）

時刻は JST（ログの時刻は UTC のまま引く）。ホストは bengio（`hostname` = Bengio）。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d`。重ねの BODY は `OV=/home/ubuntu/slocal2/s2fix-bengio-body`。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/egtp-original-form`。`feat/grasp-pilot-d` は手元にも遠隔にも無く、契約の履歴も `tasks/T-2026-11-01-grasp-pilot-d` も `.sync-pause` も無かった
- 開始前の未追跡 5 件（`experiments/analysis/gaze_data_survey/survey.py`、`experiments/phase1/grasppilot_pd_B_{empty,gt}_ep4_seed42/logs/{eval_meta_val,val_metrics_by_epoch}.json`）
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 ebc35d7b）→ 追跡下の変更 0、未追跡・起点に在り中身が同じ 5（通す）、ほか 0、`分類: 通す`
- `make task-start` → `分岐を作成: feat/grasp-pilot-d（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、`完了。`。中身は `task_id=` と `branch=` の 2 行。`grep -c sync-pause ~/bin/m2-sync.sh` → 2（対応済み）
- `make task-validate` → `OK`、exit 0（WARN なし）
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、P4・P5・P13・P14（kind=analysis で対象外）、P12（解決前提の参照なし）。P9 spec_lint は該当なし

## Task A — 開始状態（G1）

### A-1 分岐と起点

    $ git branch --show-current; git rev-parse origin/phase0; git merge-base HEAD origin/phase0
    feat/grasp-pilot-d
    ebc35d7b67d85983d31af087a08a4c2968950fad
    ebc35d7b67d85983d31af087a08a4c2968950fad
    $ git ls-tree --name-only ebc35d7b scripts/grasppilot/ | wc -l     → 17（PR 272 c942fd13 の内容が起点に在る）

### A-2 開始前から在る未追跡

- 上の 5 件は起点（phase0）に同じ中身で追跡されており、分岐を作った後は追跡下で差分なし。消していない
- 開始の後（16:15 UTC）に同期で `experiments/analysis/grasp_pilot_g/c3/c3_controls.py` が届いた（二本目の andrew の出力。本契約は作っていない）。
  消さず、commit にも含めない。`make forbidden-check` はこれを `experiments/` の内側として拾う（Task E 参照）

### A-3 compute プロセス（`$S/start/a3_procs.json`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 53, gpu_pids [], n_compute 0（python3.11 1 は道具自身で除外）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh          → count 8（自分のシェル PID 3241355 を含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9   → count 0
    $ ps -eo pid,user,comm,args | awk '$3 ~ /^(python|torchrun|accelerate)/' | wc -l  → 0（他の利用者の PID の補完）
    $ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv     → 0 件

**本契約以外の compute プロセスは 0 件。**

### A-4 記憶領域・GPU（`$S/start/a4_df.txt`、`a4_gpu.txt`）

    $ df -B1 /home/ubuntu/slocal2
    /dev/sdb1  7937302376448  6091524706304  1445682802688  81%
    $ free -b → Mem total 134,986,752,000、available 112,051,191,808。Swap 2,147,479,552 のうち 2,146,791,424 使用
    $ nvidia-smi --query-gpu=index,name,uuid,power.limit,power.default_limit,power.max_limit,memory.total,driver_version
    0, NVIDIA RTX A6000, GPU-1b153400-…, 220.00 W, 300.00 W, 300.00 W, 49140 MiB, 595.84
    1, NVIDIA RTX A6000, GPU-525aae08-…, 220.00 W, 300.00 W, 300.00 W, 49140 MiB, 595.84

空き 1,445,682,802,688 B。見積もり（上限側）: 腕 1 本の checkpoint（main.py の total_limit 5 × 約 0.6 GB）3 GB × 3 腕と試走、最後の重みと予測 ≤ 2 GB、標的 ≤ 0.1 GB。合計 ≤ 15 GB。足りる。
**電力の上限は 220 W（既定 300 W）**。記録の検出塔（ホスト不明）や andrew と速さが違いうる。

### A-5 試験（開始時、`$S/start/a5_pytest_start.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 961 passed, 5 skipped, 26 warnings, 1 error in 49.45s

失敗の名前（bengio の開始時の集合。一本目の andrew の 6 件とは別のホストの集合）:

    ERROR  tests/test_stage1_dtower_convergence.py - FileNotFoundError
    FAILED tests/test_check_spec.py::test_teacher_detection_rate
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    FAILED tests/test_stage1_ptower_heads.py::test_existing_candidates_match_baseline[A]
    FAILED tests/test_stage1_ptower_heads.py::test_existing_candidates_match_baseline[B]
    FAILED tests/test_stage1_ptower_heads.py::test_existing_candidates_match_baseline[C]
    FAILED tests/test_stage1_ptower_heads.py::test_existing_candidates_match_baseline[linear]

### A-5（契約の 5）Relation-DETR と検出器の仮想環境（`$S/start/a5_reldetr_*.json`、道具 `scripts/grasppilot/reldetr_digest.py`。andrew では標準出力に出すだけ）

`source_tree_sha256` は `scripts/stage2pilot/input_digest.py` と同じ規則（.py .cu .cuh .cpp .h）、`all_tree_sha256` は拡張子を問わない全ファイル。

| 場所 | source_files | source_tree_sha256 | all_files | all_tree_sha256 | python | 3.11 | パッケージ（importlib） |
|---|---:|---|---:|---|---|---|---|
| andrew `m2/third_party/Relation-DETR` | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… | uv cpython-3.11.16 | 3.11.16 | 72、8f08a2457e681d6d… |
| bengio main `m2/third_party/Relation-DETR` | 127 | 3ade18f0709362fa… | 140 | 89dc93b4a82f1e06… | 同 | 3.11.16 | 72、8f08a2457e681d6d… |
| bengio 重ねの BODY `$OV/third_party/Relation-DETR` | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… | 同（`$OV/.venv-relation-detr` は main の venv へのリンク） | 3.11.16 | 72、8f08a2457e681d6d… |

- andrew の Relation-DETR は commit b485955c、未 commit の変更 42 件（前回の記録と同じ件数）。`source_tree_sha256` は前回の記録 2f08e521…f1e393 と一致
- **bengio main は andrew と違う（127 vs 142 ファイル）。前例（handoff_bengio §6 の (b)）どおり重ねの BODY を使い、bengio main の `third_party` は変えない。** 重ねの BODY は andrew と全 155 ファイルで一致したので、写し直さずそのまま使う（読むだけ）
- 陽性対照: 重ねの BODY を scratch に写し `main.py` に 1 行足した写しは `source_tree_sha256`・`all_tree_sha256` とも不一致（`a5_reldetr_tampered_copy.json`）。写しは消した
- 拡張: `[env] torch 2.1.2+cu118 cuda True ms_deform_attn_ext True`（`experiments/analysis/grasp_pilot_d/repro/env_check_det.txt`。既存のビルド `~/.cache/torch_extensions/py311_cu118` を読んだ）

### A-6 COCO の重み（`$S/start/a6_weights_sha256.txt`）

    $ sha256sum data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
    2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff   （andrew の同じ経路も同じ値。重ねの BODY の data は main の data へのリンク）
    196,140,106 B

### A-7 既存の仮想環境のパッケージの一覧（`$S/start/a7_pkgs_*.txt`）

    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv                 108 行  9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0
    .venv-relation-detr    72 行  a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090

（一本目の andrew の値と同じ。）

### A-8 起票時の値

    $ git log -1 --format=%H -- context/conventions.md   → 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（conventions_rev と一致）
    $ git log -1 --format=%H -- runindex/                → 68befc3b62ffc071077cca446df5d3c83b8c38b9（created_from.runindex_commit と一致）
    行数（見出しを除く）: index 2363、experiments 1130、verdicts 1736（created_from.counts と一致）

差し替えは無い。`meta.amendments` は空のまま。

### G1 の判定

分岐 `feat/grasp-pilot-d`、起点 origin/phase0 ebc35d7b（PR 272 の内容が在る）、本契約以外の compute プロセス 0 件、
Relation-DETR と仮想環境は重ねの BODY で andrew と一致、COCO の重みが在る、空き・失敗の名前・電力の上限を記録した。**通過。**

## Task B — 再現と処方（G2）

### B-1 塔単独の val（`experiments/analysis/grasp_pilot_d/repro/run_repro.sh`、01:20〜01:23 JST）

`scripts/eval_relation_detr_map.py` は台本の位置から `third_party` を引く（bengio main の違う中身を使う）ため使わず、
一本目の B-4 と handoff_bengio R5 の前例どおり `scripts/stage2pilot/pd_eval.py --cfg plain` を `EGO_BODY=$OV` で回した。

| checkpoint | sha256 | overall mAP | 標的群 AP | 陰性対照群 AP |
|---|---|---:|---:|---:|
| seed 42（`.../dcoco_foldA_seed42/work/best_ap.pth`） | 30d199b1…682c4（`DET_SHA256` と一致） | 0.7273450248 | 0.7950748009 | 0.6726631818 |
| 記録（一本目の RESULT §3） | — | 0.7273450 | 0.7950748 | 0.6726632 |
| 差 | — | 0.0 | < 1e-7 | < 1e-7 |
| 対照: seed 123 | — | 0.7288631 | 0.8234321 | 0.6701777 |

- 対照の差は overall +0.0015（許容差の中）、**標的群 +0.0284（許容差 0.005 を超える）**。判定は別の塔を見分ける
- 予測を `$S/b/plain_val_preds_seed42.json.gz` に保存した

### B-2 記録から読んだ処方（`experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/`）

    command.sh: accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36
    training.log 36 行: Namespace(..., accumulate_steps=1, seed=42, convergence_schedule=True, plateau_patience=4, plateau_factor=0.1, max_epochs=36)
    training.log 152 行: load pretrained from /home/ubuntu/slocal2/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
    training.log 2516 行: [convergence] epoch 9: … 学習率を 0.1 倍にした (lr=[1e-05, 1e-06, 1e-06, 1e-06, 1e-06, 1e-05])
    training.log 3649 行: [convergence] epoch 14: … 打ち切る / Training time: 9:58:04
    各 epoch の歩 0 の lr（群 0）: epoch 0 は 0（warmup 1000 歩）→ 2400 歩で 1e-4、epoch 1〜9 は 1e-4、epoch 10〜14 は 1e-5
    歩数: [0/2405]（1 過程あたり。2 GPU × batch 2）
    convergence.json: best_epoch 10、decayed_epoch 9、stopped_epoch 14、observed_epochs 15

§2 の値（上限 36、停滞 4、epoch 9 で低下、epoch 14 で打ち切り、15 epoch、最良 10、2 GPU × batch 2）と一致する。

**本契約の長さ**: 収束規則を使わず、設定の `MultiStepLR(milestones=[10])` と `--max-epochs 15` にする。main.py は収束規則が無いとき
epoch の終わりに `lr_scheduler.step()` を呼ぶので、epoch 0〜9 が 1e-4、epoch 10〜14 が 1e-5（記録と同じ並び）になる。試走で確かめた（Task C）。

### G2 の判定

overall mAP と標的群 AP の差がともに 0.005 以内（0.0 と 1e-7 未満）。**通過。**

## Task C — 補助の頭と、補助損失なしの腕（G3）

### C-1 実装（third_party と既存スクリプトは変えない。新しいファイルだけ）

| ファイル | 役割 |
|---|---|
| `scripts/grasppilot/grasp_aux_d.py` | 派生。元の模型設定が作った `RelationDETR` の実体の型を差し替え、補助の頭（256→4 線形）を足す。頭の初期値は専用の `torch.Generator`（seed 20261101）から作り、大域の乱数を動かさない。学習時だけ、`class_head[-1]` の前向きの事前フックの最初の発火（主経路。hybrid は 2 回目）の末尾 `num_queries`（900）個と、criterion の最初の呼び出しの最初の B 回の matcher の出力（最終層の主経路の照合）を取り、対応づいた枠で 4 値 CE を平均。`loss_grasp = weight × CE` だけを損失の dict に入れ、CE（重みの前）・当たり・枠の数・反転の数を歩ごとに `grasp_steplog.jsonl` へ書く。読み込みの前後の要約値を `load_record.jsonl` へ書く。データセットの派生 `GraspTargetCoco` は注釈の並びの番号を `category_id` に埋めて変換を通し（変換は値を見ない）、残った枠の q を表から引く。最上段の反転を `_get_params` の呼び出しで反転を記録する派生に替え、反転した画像では q の左手と右手を入れ替える |
| `scripts/grasppilot/d_model_config.py` | 模型設定。元の `configs/relation_detr/relation_detr_resnet50_egosurgery.py` をそのまま実行し、`attach_grasp_head` を当てる |
| `scripts/grasppilot/d_train_config.py` | 学習設定。記録の `train_config_egosurgery_seed42.py` と同じ値。違うのは train_dataset（派生）、model_path（派生）、num_epochs 15、COCO の重みがファイルでなければ止めること |
| `scripts/grasppilot/run_d_arm.sh` | 起動。GPU 1 枚、`accelerate launch --num_processes 1 main.py --config-file <写し>/d_train_config.py --seed 42 --mixed-precision fp16 --accumulate-steps 2 --max-epochs 15`。コードは中身の要約値ごとの置き場 `$S/code/<16 桁>/` に写して読み取り専用にし、全腕をその写しから回す |
| `scripts/grasppilot/d_check.py`、`d_targets.py`、`d_finalize.py` | 確かめ、標的の表、後処理 |

**反転と左右の扱い（利用者の決定、2026-11-01 01:3x JST）**: presets.detr は確率 0.5 で左右反転する。SPEC に記載が無いため諮り、
「反転時に左右を入れ替える（両手・なしはそのまま）」に決まった。

### C-2 確かめ（`experiments/analysis/grasp_pilot_d/taskC/c2_check.json`。腕に数えない）

試走の標的: 一本目の正解の枠ごとの r（andrew の `…/T-2026-10-31-grasp-pilot-probe/signals/boxstate_train.npz`、sha256 fb7af1a3…709 を両端で照合して
`$S/targets/probe_copy/` へ写した）から `d_targets.py from-boxstate` で q を作った（`$S/targets/trial_q_probe_gt_train.npz`、6d2375f4…bbb1、32,272 枠）。
照合（`$S/targets/trial_q_check.json`）: train の注釈の全 32,272 枠に対応し欠け 0・余り 0。和の検査は Σr > 1 の 3 枠で外れを出す（一本目の式の性質。試走だけに使う）。

    $ CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/d_check.py --q $S/targets/trial_q_probe_gt_train.npz --out <絶対経路>/c2_check.json
    data_identical True（64 項目で元の CocoDetection と画像・枠・ラベルが一致）、q_matches_table True（64/64、反転は左右を入れ替えた値）、
    flip_probe_controls True（p=1 で 20/20、p=0 で 0/20）、反転 33/64
    init_equal True（同じ種で作った元の模型と、頭を除いたパラメータが一致）、coco_changed_params True
    w0_max_abs_diff 0.0、w0_total_equal_base True（重み 0 の全損失・全項が頭の無い元の模型と一致。4 batch）
    w0_max_abs_diff_plain_same_instance 0.0、w0_total_equal_plain_same_instance True（同じ実体で元の forward を呼んだ経路とも一致）
    base_repeat_max_abs_diff 0.0（同じ模型を二度回したときの差。素の非決定性は 0）
    w0_head_grad_zero True、w03_aux_enters True（全損失 − 検出の損失 = 0.388、0.380、0.374、0.351 ≈ 0.3 × CE）、w03_head_grad_positive True（2.50、2.12、2.49、2.70）
    matched_eq_n_gt True（対応づいた枠 = 正解の枠: 7、4、9、10）、indices_eq_recomputed True（取った indices = 照合を外から計算し直したもの）

確かめの経緯（確かめ側の不備を 3 回直した。実装は変えていない）:
1. 一回目は `RandomSizeCrop` が python の `random` を使うのに torch の種しか揃えておらず、データが 34/64 しか一致しなかった → python・numpy の種も揃えて 64/64
2. 頭の無い経路を `no_grad` で計算していたため最大 0.0049 ずれた → 勾配を有効にした同じ条件で比べて差 0.0
3. 合計を python の倍精度で足していたため合計だけ見かけ上ずれた → main.py と同じく fp32 のテンソルで足して一致

**COCO の重みを読んだことの記録**: 読み込みの記録（`taskC/load_record.jsonl`）は要約値 d2586acb… → 6a26aac9…（changed true、
missing は `grasp_head.weight`・`grasp_head.bias` だけ）。

### C-2 main.py を通した試走（`experiments/phase1/grasppilot3_d_smoke*`。腕に数えない。train 8 枚・val 4 枚の注釈 `$S/smoke_ann/`）

| 試走 | 内容 | 結果 |
|---|---|---|
| `grasppilot3_d_smoke`（16:41 UTC、GPU 0） | 重み 0.3、12 epoch | rc 0。`load pretrained from …coco_1x.pth` 1 行。歩 0 の lr: epoch 0 は 3.3e-05（warmup）、1〜9 は 1e-4、**10・11 は 1e-5**。optimizer の歩数 checkpoint_7 → 11 で 11 → 19（16 マイクロ歩で 8 更新 = ため込み 2 が効いている。初期の不足は fp16 のスケーラーが溢れで飛ばした歩）。**歩ごとの記録が書かれていなかった**（50 件ためてから書く作りで 48 歩では一度も書かれない）→ 1 行ずつ書く形に直した |
| `grasppilot3_d_smoke_nococo`（GPU 1） | 陽性対照。COCO の経路を `/nonexistent/...` にし、`GRASP_ALLOW_MISSING_COCO=1` で設定の停止を外す | rc 0。`load pretrained` の行 0、`load_record.jsonl` が無い（読み込みの記録が無くなる） |
| `grasppilot3_d_smoke2`（GPU 1、直した後のコード） | 重み 0.3、12 epoch | rc 0。歩ごとの記録 48 行、各歩の特徴のフックは 2 回（主経路と hybrid）、特徴の長さ 1098〜1100（denoising + 900）、対応づいた枠 = 正解の枠。後処理 `d_finalize.py` も通った |

直した後のコードで `d_check.py` を回し直し、上の C-2 の判定はすべて同じ値で真。コードの要約値（`code_sha256.txt`）:
`grasp_aux_d.py` 653faeb5…f416、`d_model_config.py` aa019384…56b4、`d_train_config.py` 2edc8879…8400（置き場 `$S/code/<16 桁>/`）。

### C-3 補助損失なしの腕

    $ CUDA_VISIBLE_DEVICES=0 setsid nohup bash scripts/grasppilot/run_d_arm.sh none 29821 > $S/logs/none.out 2>&1 &
    start.txt 2026-10-31 16:44:5x UTC（01:45 JST）、commit 23c34e5a
    training.log 142 行: load pretrained from /home/ubuntu/slocal2/s2fix-bengio-body/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
    Epoch: [0] [100/4809] eta 0:34:43、GPU 0 は 207 W・12.9 GB
