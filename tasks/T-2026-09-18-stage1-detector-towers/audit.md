# audit — T-2026-09-18-stage1-detector-towers

実施ホスト `efros`（RTX A6000 × 2 / driver 595.84 / nvcc 12.9 / torch 2.1.2+cu118）。JST 2026-09-18。
**数値はすべて実測である。未測定は UNKNOWN と書く。**

## Task A — 事前登録の commit と開始状態

### A-1 prereg の commit

| 項目 | 値 |
|---|---|
| commit | `fa9cc5466e0bee7646a0010b06413e6da853e03d` |
| committed_at | `2026-09-17T22:11:38+00:00` |
| 検査 | L3 の P4 が PASS（`prereg_committed`） |

**いかなる学習よりも前に commit した**（Task B の起動は 2026-09-17 22:26:42 UTC で 15 分後）。

### A-2 作業ツリーと装置

| 項目 | 実測 |
|---|---|
| 開始時の HEAD | `be7c771988aace52e2481e693b46b54eef066401`。`origin/phase0` と同一 |
| 分岐 | `feat/stage1-detector-towers`（`make task-start` が `origin/phase0` を起点に作成済み） |
| 開始時の未追跡 | 1 件（`tasks/T-2026-09-18-stage1-detector-towers/`。契約そのもの） |
| 開始前から在った未追跡 | 0 件 |
| 装置（Task B 起動前） | GPU 0: 15 MiB / 0%、GPU 1: 35 MiB / 0%。**compute プロセス 0 件** |

他利用者の処理は 0 件（`nvidia-smi --query-compute-apps=pid --format=csv,noheader` の行数を
`grep -c` で数えた。終了コードを件数として使っていない）。

### A-3 折り表の解決

`conventions#folds`（正本 `docs/stage0/A1_fold_table.md`）と `data/splits/` の実測。

| 折り | test（3） | val（2） | train（10） |
|---|---|---|---|
| A | 04, 05, 07 | 09, 10 | 01, 02, 03, 06, 08, 11, 12, 13, 14, 15 |
| B | 01, 03, 14 | 02, 08 | 04, 05, 06, 07, 09, 10, 11, 12, 13, 15 |
| C | 02, 08, 11 | 06, 12 | 01, 03, 04, 05, 07, 09, 10, 13, 14, 15 |
| D | 06, 13, 15 | 04, 05 | 01, 02, 03, 07, 08, 09, 10, 11, 12, 14 |
| E | 09, 10, 12 | 07, 15 | 01, 02, 03, 04, 05, 06, 08, 11, 13, 14 |

`data/splits/ego_{train,val,test}.txt` の実測は train `01 02 03 06 08 11 12 13 14 15` /
val `09 10` / test `04 05 07` で、**折り A と完全一致**する。

### A-4 凍結源を生んだ処方（出所つき）

出所は `experiments/baselines/_legacy_score_thr_0/s0_016_relationdetr_bbox_seed42/`
（分母参照 `baselines/s0/relationdetr_bbox@val` に属する 3 run のうち seed 42）。

| 項目 | 値 | 出所 |
|---|---|---|
| 起動 | `accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16` | run の `command.sh` |
| **数値精度** | **fp16 の自動混合精度** | 同上 |
| epoch | 12 | config `num_epochs = 12` |
| scheduler | `MultiStepLR(milestones=[10], gamma=0.1)` | config |
| batch | per-GPU 2、2 枚で**実効 4** | config `batch_size = 2` / `metrics.json` の `effective_batch_size: 4`・`gpu_count: 2` |
| lr | 1e-4（`lr_scaling: linear_x2`） | config `learning_rate` / `metrics.json` |
| 最適化器 | `AdamW(lr=1e-4, weight_decay=1e-4, betas=(0.9, 0.999))` | config |
| param_dicts | `param_dict.finetune_backbone_and_linear_projection(lr=1e-4)` | config |
| 勾配の刈り込み | `max_norm = 0.1` | config |
| 増強 | `presets.detr` | config `train_dataset.transforms` |
| 解像度 | `presets.detr` の乱択（短辺 480〜800、長辺 ≤1333） | `transforms/presets.py:60-74` |
| model config | `configs/relation_detr/relation_detr_resnet50_egosurgery.py`（`freeze_indices=(0,)` = stem のみ凍結） | config `model_path` |
| 初期化 | COCO 1x 重み `relation_detr_resnet50_800_1333_coco_1x.pth`（196,140,106 bytes）、class head は 91→15 で再初期化 | config `resume_from_checkpoint` / `notes.md` |
| seed | 42（命令行） | `command.sh` |
| num_workers / pin_memory | 4 / True | config |
| 評価 | NMS-free、`score_thr=0.0`、`max_per_img=300`、`select_box_nums=300` | `metrics.json` の `test_cfg` |
| 実施ホスト / commit | philip / `4327348e444381f1737309252fb86ad9b5034d6a` | run 記録 |
| 結果 | mAP 0.729749 / AP_rare 0.757599 / AP_common 0.725107（best epoch 12） | `metrics.json` |

**UNKNOWN の項目は無い。** 全項目が config・`command.sh`・`metrics.json` のいずれかから引けた。

🔴 **契約の前提と食い違う点がある。** `prereg.md` §2 と SPEC §1 は「凍結源は fp32 で学習されている」
ことを前提に全 run を TF32 とするが、**実測は fp16 の自動混合精度**である。
前契約 `C2` の TF32 の測定は fp32 の界面 run（`train_t1b.py`）を基準にしており、
**検出塔のフル学習には当てはまらない**。利用者の判断（2026-09-18）で全 run を凍結源と同じ fp16 とした
（`meta.amendments`）。これにより処方の差分は真に 0 項目になる。

なお TF32 は `TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=1` で実装改変なしに有効化できることを実測した
（`matmul.allow_tf32` が False → True）。採らなかったのは速さのためではなく**処方を揃えるため**である。

### A-5 折りごとの注釈

`scripts/make_fold_annotations.py` で生成。出力は
`data/annotations/egosurgery_tool_folds/<fold>/instances_{train,val,test}.json`
（`.gitignore:10` により追跡外。公式の `egosurgery_tool/instances_*.json` は 118 行目で
追跡対象のため、**別ディレクトリへ置いて取り違えを防いだ**）。

**公式 3 ファイルの ID は衝突する**（image_id 4,265 件・annotation_id 12,673 件。いずれも 0 始まり）。
折り B〜E は 3 ファイルをプールし、`file_name` の順に決定的に振り直した。
**折り A は公式分割そのものであるため複製して使い、ID を振り直していない**（再現の忠実さのため）。

| 折り | 分割 | 期待動画 | 実測動画 | 集合差 | 画像 | 注釈 |
|---|---|---|---|---:|---:|---:|
| A | train | 01,02,03,06,08,11,12,13,14,15 | 同一 | **0** | 9657 | 32272 |
| A | val | 09,10 | 同一 | **0** | 1515 | 4707 |
| A | test | 04,05,07 | 同一 | **0** | 4265 | 12673 |
| B | train | 04,05,06,07,09,10,11,12,13,15 | 同一 | **0** | 9764 | 31119 |
| B | val | 02,08 | 同一 | **0** | 1861 | 4922 |
| B | test | 01,03,14 | 同一 | **0** | 3812 | 13611 |
| C | train | 01,03,04,05,07,09,10,13,14,15 | 同一 | **0** | 10834 | 34769 |
| C | val | 06,12 | 同一 | **0** | 1988 | 7516 |
| C | test | 02,08,11 | 同一 | **0** | 2615 | 7367 |
| D | train | 01,02,03,07,08,09,10,11,12,14 | 同一 | **0** | 10262 | 35078 |
| D | val | 04,05 | 同一 | **0** | 2554 | 5751 |
| D | test | 06,13,15 | 同一 | **0** | 2621 | 8823 |
| E | train | 01,02,03,04,05,06,08,11,13,14 | 同一 | **0** | 11182 | 33724 |
| E | val | 07,15 | 同一 | **0** | 2131 | 8750 |
| E | test | 09,10,12 | 同一 | **0** | 2124 | 7178 |

- **全折りで分割間の重なり 0**、動画の和は 15 本、画像の合計は 15,437 枚（プール総数と一致＝保存されている）
- **折り A は公式ファイルと sha256 が一致**（train `fc63621ea496ccdc…` / val `db605c06626ff824…` /
  test `f4ce5243fd01fc6e…`。3 分割とも一致）

**陰性対照**: 折り A の test から `04` を抜き `11` を入れた集合と照合すると、集合差は **2** になった
（通常の照合は 0）。🔴 **契約は「差 1 になることを一度示す」と書くが、1 本の入れ替えの対称差は 2 である**
（1 本抜けて 1 本入る）。差が 0 でないことを示すという目的は達している。

### A-6 `--tf32` の所在

PR #182 は **2026-09-17T22:07:33Z に併合済み**（`state: MERGED`）。本分岐は `origin/phase0` と
同一点にあり、`scripts/train_t1b.py` に `--tf32` が 1 件在る。**取り寄せは不要だった。**
ただし A-4 の決定により本契約では TF32 を使わない。

### A-7 占位の差し替え

| 項目 | 実測値 | 出所 |
|---|---|---|
| `contract.conventions_rev` | `e7a5100597a79b3b9c60935bf38d232f8ae96822` | `git log -1 -- context/conventions.md` |
| `meta.created_from.runindex_commit` | `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5` | `git log -1 -- runindex/` |
| `counts` | index 1266 / experiments 285 / verdicts 1506 | 各 CSV の行数からヘッダ 1 行を引いた値 |

差し替え前は L2-8 が「分母が動いています」の WARN を 3 件出していた。**これは占位が 0 のままだった
ことによる見かけの警告**であり、差し替え後は消えた。利用者へ提示して続行の判断を得ている。

## 解決された参照

| 参照 | 解決結果 |
|---|---|
| `inputs.denominator.ref` = `exp:baselines/s0/relationdetr_bbox@val` | n_runs 3 / n_seeds 3 / seeds 42,123,456 / split val / eval_recipe_id `b66459018a92` / host philip。**mAP 平均 0.7267943333・pstd 0.0033960155・sstd 0.0041592526・min 0.722038・max 0.729749**。AP_rare 平均 0.7483483333・pstd 0.0089135919。`require`（n_seeds ≥ 3・sigma present・split val）を**満たす**。分母は動いていない |
| `inputs.sigma_policy`（省略） | `conventions#sigma` の既定を継承（`series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired`） |
| `inputs.frozen_source` | sha256 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` / 195,421,066 bytes。**規約の記載と一致**（L3 の P5 が PASS） |
| `contract.inject_verbatim` 7 件 | `conventions#prohibitions` / `#issuer_cautions` / `#folds` / `#split` / `#eval_recipe` / `#frozen_source` / `#sigma`。原文は `context/conventions.md` rev `e7a5100597a79b3b9c60935bf38d232f8ae96822` の該当アンカー。要約していない |

## L3 プリフライト

    P1 venv_active            PASS
    P2 cuda_ext_loaded        PASS
    P3 deterministic_flags    SKIP UNKNOWN 判定基準が未確定（backlog B-20 が未解決）
    P4 prereg_committed       PASS fa9cc546… committed_at=2026-09-17T22:11:38+00:00
    P5 frozen_source_hash     PASS sha256=03936318…
    P6 decisions_answered     PASS
    P7 destination_writable   PASS
    P8 contract_valid         PASS
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    P10 preflight_names_known PASS 宣言 4 件はすべて実装済み
    P11 gpu_free              PASS GPU を占有する compute プロセスは 0 件
    P12 refs_resolved         SKIP 解決前提の参照は無い

    RESULT: 10 PASS / 0 WARN / 2 SKIP / 0 FAIL

🔴 **P3 は宣言したのに SKIP された。** 契約は `plan.env.preflight` に `deterministic_flags` を
入れているが、検査器は「判定基準が未確定」として SKIP を返す（backlog B-20）。
**宣言しても検査されない項目がある**ことになる。

## Task B — 再現の確認（D\*-COCO 折り A seed 42）

起動 2026-09-17 22:26:42 UTC。命令は
`experiments/baselines/stage1_dtower/dcoco_foldA_seed42/command.sh` に記録した。
凍結源との差は**出力先と注釈ディレクトリの明示だけ**で、処方は同一である。

    2405 step/epoch、iter_time 0.556 s、1 epoch の見込み 22〜24 分

（以降は完走後に記入する）

（Task B の続き）完走した。`Training time: 7:48:59`（`train.log` の末尾）。
**最良 epoch は 12 番目**（0 起点で 11）で、凍結源の記録（best epoch 12）と同じ位置である。

    epoch:  0      1      2      3      4      5      6      7      8      9     10     11
    mAP: 0.5729 0.6674 0.6765 0.6990 0.7044 0.6868 0.7057 0.7110 0.6952 0.7140 0.7240 0.7244
                                                                              ↑lr 1/10   ↑best

（値は TensorBoard の `val/mAP` スカラーの float32 原値。`train.log` の
`Average Precision` 行は 3 桁に丸められており桁が足りない。両者が一致することは確認した。）

### G2 の判定

| 対象 | val mAP | 出所 |
|---|---:|---|
| 凍結源 `s0_016` | 0.729749 | `experiments/baselines/_legacy_score_thr_0/s0_016_relationdetr_bbox_seed42/metrics.json` |
| 本 run | **0.724414** | TensorBoard `val/mAP` step 11 |
| 差 | **−0.005335 = −0.53 mAP** | |

事前登録 §5-2 の規則「1 mAP 以内なら再現」に照らし **再現とみなす。G2 PASS**。
分母参照の 3 seed 平均 0.726794 との差は −0.24 mAP = **0.70σ**（pstd 0.003396）で、
seed 間の散らばりの内側である。

`best_ap.pth` を読み直した eval-only の再評価は **0.7244185525748421** で、
学習時の記録との差は **4.7e-06**。保存された重みと記録が一致する。

## Task C — 残り 13 run

全 14 run が完走した。`Training time` は 7:48:59〜9:13:30。

### 同時実行の方針（実測で決めた）

| 同時本数 | 1 run の 1 step | 総処理量 | GPU 使用率 |
|---:|---:|---:|---|
| 1 | 0.554 s | 1.805 step/s | 平均 5 割（17〜100% に振れる） |
| **2** | 約 0.92 s | **2.17 step/s** | 91.2% / 95.9%（30 秒・1 秒毎の標本） |
| 3 | 約 1.37 s | 2.19 step/s（+1% のみ） | 100% |

**2 本で計算が飽和する。** 3 本目は総処理量を 1% しか増やさず per-run を 1.5 倍遅くするため採らない。
メモリは 2 本時で 28 GB / 49 GB と余るが、**ボトルネックは計算である**。
`scripts/stage1_dtower_queue.sh` が 2 本を切らさず流した。

**処方は 1 本も変えていない。** 全 run が `--num_processes 2`・per-GPU batch 2（実効 4）・fp16 である。

### 折りごとの規模の違い

| 折り | train 枚数 | step/epoch | 1 run の実測（2 本同時） |
|---|---:|---:|---:|
| A | 9,657 | 2,415 | 7.82〜7.93 h |
| B | 9,764 | 2,441 | 8.02〜8.03 h |
| C | 10,834 | 2,709 | 8.89〜8.91 h |
| D | 10,262 | 2,566 | 8.59〜8.70 h |
| E | 11,182 | 2,796 | 9.22〜9.23 h |

14 run の平均 **8.353 h**（中央 8.031）。**14 × 8.353 ÷ 2 枚 = 58.5 h** は実際の経過
58.7 h（9/17 22:26:42 → 9/20 09:09:57 UTC）と一致する。

## Task D — test と散らばり

### D-1 test の評価（折りごとに一度・合計 10 回）

`experiments/baselines/stage1_dtower/test_access_ledger.csv` に 10 行。
各行に checkpoint の sha256・画像数・mAP・理由を持つ。**折り A は seed 42 を確定塔とした**
（凍結源と同じ seed。折り A だけ 3 seed あるため一つ選ぶ必要がある）。

**test を選定に使っていない。** 最良 epoch は折り内 val で既に決まっており、
test は確定した重みを一度評価しただけである。

### D-2 表（2 塔 × 5 折り = 14 行）

| 塔 | 折り | seed | val mAP | val AP_rare | test mAP | test AP_rare | 所要 |
|---|---|--:|--:|--:|--:|--:|--:|
| D*-COCO | A | 42 | 0.7244 | 0.7382 | 0.5117  | 0.6147 | 7:48:59 |
| D*-COCO | A | 123 | 0.7254 | 0.7581 | — | — | 7:55:51 |
| D*-COCO | A | 456 | 0.7208 | 0.7259 | — | — | 7:54:21 |
| D*-COCO | B | 42 | 0.4762 | 0.6049 | 0.4384  | 0.5551 | 8:02:00 |
| D*-COCO | C | 42 | 0.4385 | 0.6004 | 0.5011  | 0.6685 | 8:54:40 |
| D*-COCO | D | 42 | 0.4967 | 0.6665 | 0.5558  | 0.6131 | 8:42:00 |
| D*-COCO | E | 42 | 0.5272 | 0.6611 | 0.5841  | 0.7659 | 9:13:30 |
| D*-ImageNet | A | 42 | 0.6853 | 0.7743 | 0.4724  | 0.6108 | 7:55:30 |
| D*-ImageNet | A | 123 | 0.6774 | 0.7411 | — | — | 7:52:28 |
| D*-ImageNet | A | 456 | 0.6660 | 0.7561 | — | — | 7:53:37 |
| D*-ImageNet | B | 42 | 0.4084 | 0.5130 | 0.4064  | 0.4889 | 8:01:44 |
| D*-ImageNet | C | 42 | 0.4093 | 0.5820 | 0.4802  | 0.5583 | 8:53:38 |
| D*-ImageNet | D | 42 | 0.4801 | 0.6999 | 0.5164  | 0.6229 | 8:35:16 |
| D*-ImageNet | E | 42 | 0.4538 | 0.6381 | 0.5655  | 0.7683 | 9:12:56 |

`AP_rare` は Skewer と Syringe の平均（`src/egosurgery/datasets/constants.py:71` の
`RARE_CLASSES`）。NaN のクラスは平均から除く。評価は NMS-free（`conventions#eval_recipe`）。

### 散らばり

| 塔 | 折り A の seed 間 pstd（3 seed） | 折り間 pstd（B〜E の seed42） | 比 |
|---|---:|---:|---:|
| D\*-COCO | 0.001984 | **0.032249** | **16.3×** |
| D\*-ImageNet | 0.007892 | **0.030500** | **3.9×** |

（参考）A〜E の 5 折りで取ると pstd は COCO 0.100160 / ImageNet 0.102630。
折り A が他より 0.2 以上高いため、A を含めると散らばりがさらに大きくなる。

### D-3 事前登録の予測の当たり外れ

| # | 予測 | 判定 | 実測 |
|---|---|---|---|
| 1 | 折り A seed42 の D\*-COCO は凍結源と 1 mAP 以内 | **当たり** | −0.53 mAP |
| 2 | D\*-ImageNet は全折りで D\*-COCO より低く、差は 5〜15 mAP | **部分的に外れ** | 方向は 5/5 折りで当たり。幅は **1.66〜7.33 mAP** で、5〜15 に入るのは **2/5 折り**のみ。**予測より差が小さい** |
| 3 | 折り間 SD > 折り A の seed 間 SD | **当たり** | 16.3× と 3.9× |
| 4 | D\*-ImageNet は収束が遅く、最良 epoch が後ろに寄る | **外れ** | 最良 epoch は 11〜12 番目で D\*-COCO と同じ位置 |

予測 4 の補足。**「後ろに寄る」という形では外れだが、「収束が遅い」ほうは支持される。**
最後の 1 epoch の伸びは D\*-ImageNet が +0.0067 に対し D\*-COCO 折り A は +0.0004 で **5.2 倍**。
D\*-ImageNet は最終 epoch が最良であり、**12 epoch で打ち切られている可能性が高い**。
🔴 ただし **epoch を増やせば伸びるかは測っていない。UNKNOWN である。**

### D-4 計算器への差し戻し

`det_tower_train` を **8.00 h（代理）→ 8.35 h（実測・`measured: True`）** にした。
`det_tower_w3` は同じ値を代理として引き継ぐ（W3 の run は依然として一件も無い）。
`docs/stage0/B1_tier1_cost_estimate.md` の 8 区画を再生成し `--check-doc` は **差 0 件**。
計算器の UNKNOWN は **10 件 → 9 件**に減った。

| 前提 | 更新前 | 更新後 |
|---|---:|---:|
| 24h/日・Stage 1 + Tier 1〜3・縮退なし | 87.5〜116.6 日 | **87.9〜117.0 日** |
| 12h/日・Stage 1 + Tier 1・縮退なし | 159.9〜218.2 日 | **160.5〜218.8 日** |
| 同・縮退段 3（seed 5→3） | 96.2〜131.2 日 | **96.6〜131.6 日** |

**日数はほぼ動かなかった（+0.4%）。** 代理 8.00 h の置き方が妥当だったことの確認になる。
締切の判定も変わらない。

## Task E — 収穫と検証

`make runindex` の前後。

| 対象 | 収穫前 | 収穫後 | 差 |
|---|---:|---:|---:|
| `index.csv` | 1266 | 1318 | +52 |
| `experiments.csv` | 285 | 303 | +18 |
| `verdicts.csv` | 1506 | 1506 | 0 |

🔴 **行数の差（+52）は新 run の数（14）と一致しない。** 内訳を実測で割った。

| 内訳 | 件数 |
|---|---:|
| 本契約の run（`task_id` で照合） | **14** |
| 前契約 `T-2026-09-17-amp-compile-timing` の tf32 run | 1 |
| 退避フォルダの古い run（`_failed_num_workers_zero` `_smoke_e3` `_pre_redo_s0_smoke` `_prior_no_eval_recipe`） | 12 |
| **新規 run の合計** | **27** |

残る差は**既存行の再生成**による。前回の収穫は 2026-08-30（`96eb3a1c`）で、
それ以降に同期で届いた退避物が混ざった。**本契約が作ったものではない。**

完了判定 g の「収穫前後の行数の差 = 新実験数」という空振り確認は、
**この repo では成り立たない**（収穫器は既存行も更新し、同期で届いた run も拾う）。
`task_id` での照合に替えた。14/14 が `baselines/d{coco,imagenet}_fold{A..E}` として現れている。
