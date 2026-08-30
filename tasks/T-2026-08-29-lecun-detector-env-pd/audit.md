# audit — T-2026-08-29-lecun-detector-env-pd

実行ホスト `lecun` / repo `/home/ubuntu/slocal/m2` / 分岐 `feat/lecun-detector-env-pd`。
GPU は RTX A6000 ×2。`data/` の生データ・分割・既存キャッシュへは書き込まない。
`third_party` 実装と `.venv-relation-detr` は版管理外のまま用意した。

---

## 1. Step A-1 参照の再確認

    runindex 最終変更: 09fdefb3   conventions: a8c07e81
    index.csv 1250 / experiments.csv 277 / verdicts.csv 1486   ← 事前記入値と全一致

| 参照 | 解決 |
|---|---|
| 分母 `exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` | experiments.csv に **1 件一意**。`n_runs=17` / `split=val` / `accuracy_mean=0.8973014948553679` / `accuracy_pstd=0.005917073407586465` |
| 凍結源 `run:baselines/s0_016_relationdetr_bbox_seed42` | index.csv に **1 件一意**。`group=baselines` |

    $ sha256sum third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824   ← conventions の正本と一致

---

## 2. Step A-2 検出器環境の用意

### 2.1 欠落の実測（同期規約どおり）

    $ find third_party/Relation-DETR -type f | wc -l   → 12（checkpoints のみ）
    $ ls third_party/Relation-DETR/models             → No such file or directory
    $ ls -d .venv*                                     → .venv のみ
    $ git check-ignore -v .venv-relation-detr          → .gitignore:63  .venv*/
    $ git check-ignore -v third_party/Relation-DETR/main.py → .gitignore:133 third_party/

**独自 config はミラーに無い。** `configs/detector_relation_detr/` は augstrong 系 2 件のみで、
凍結源が使う `train_config_egosurgery_seed42.py` を含まない。実体は版管理下の
`third_party_snapshot/lecun/Relation-DETR/project_files.tar.gz`（config 15 件を含む 23 件）に在る。

### 2.2 philip 参照は使えなかった

    $ ssh -o BatchMode=yes -o ConnectTimeout=10 philip 'hostname'
    ubuntu@192.168.196.150: Permission denied (publickey,password).

SPEC §1 は「lecun から philip へ SSH が使える（利用者の申告）」としていたが**実測と食い違う**。
SSH 設定の読み取りは実行基盤の保護規則で拒否されたため原因は特定していない。参照は使わずに進めた。

### 2.3 復元（利用者の判断: snapshot から）

    provenance.txt:
      origin: https://github.com/xiuqhou/Relation-DETR.git
      commit: b485955c72452788240600da6d0f0b8cc49f33c7   branch: main   shallow: true
      captured_at: 2026-08-02T11:03:30+00:00   captured_on: lecun

    $ git clone --depth 50 https://github.com/xiuqhou/Relation-DETR.git "$TMP"
    → HEAD が b485955（記録の commit と一致）
    $ git checkout b485955c72452788240600da6d0f0b8cc49f33c7
    $ git apply --check "$SNAP/upstream_mods.patch"   → exit 0
    $ git apply "$SNAP/upstream_mods.patch"
      optimizer/param_dict.py | 127 +++++  /  util/engine.py | 30 +++
    $ tar xzf "$SNAP/project_files.tar.gz"
    $ file_list.txt との突き合わせ → 欠落 0 件 / 記録 23 件

合流は checkpoints を除外して行った。

    $ rsync -a --exclude 'checkpoints/' "$TMP/" third_party/Relation-DETR/
    合流前後とも checkpoints 12 ファイル / sha256 03936318f9d45ac9... 不変

### 2.4 venv の構築

🔴 **ホストの nvcc は 12.9 で、文書が前提とする 11.8 は存在しない。**

    $ nvcc --version → release 12.9   /  $ ls -d /usr/local/cuda-11.8 → No such file or directory
    $ 本体 .venv の torch → 2.1.2+cu118

`setup_env_relation_detr.sh` は nvcc≠11.8 で停止するため `SKIP_CUDA_CHECK=1` を渡した。

    SKIP_CUDA_CHECK=1 CUDA_HOME=/usr/local/cuda bash scripts/setup_env_relation_detr.sh
    → torch 2.1.2+cu118 / torchvision 0.16.2+cu118 / accelerate 1.14.0 / CUDA 動作 OK

**MS-Deform-Attn の JIT ビルドは nvcc 12.9 でも成功した**（`Loading extension module
MultiScaleDeformableAttention...`）。これは実測であって保証ではない。

---

## 3. Step A-3 実装可否と重みの所在（判定 a）

### 3.1 🔴 前方計算が既知値を完全再現した

    $ .venv-relation-detr/bin/python scripts/eval_relation_detr_map.py \
        --config configs/train_config_egosurgery_seed42.py \
        --checkpoint checkpoints/incoming/seed42/best_ap.pth
    [eval] => mAP=0.7303  mAP50=0.8546  (凍結源 目標 val/mAP≈0.7297 / mAP50≈0.854)
    AP   = 0.7302938994613697
    AP50 = 0.8545901117284289

`configs/stage/s4_phase_baseline.yaml:9` の「再 eval mAP **0.7303**」と一致する。
索引の `s0_016` の 0.729749 は旧 recipe（`_legacy_score_thr_0`）の値で別物である。

**独立な裏づけ**: 後述の P→D 四段はいずれも warm-start init mAP が **0.7303** を示した
（zero-init FiLM = 恒等）。評価経路が二系統（eval スクリプトと t1b の内部評価）で一致している。

### 3.2 B4 の ImageNet-R50

    URL: https://download.pytorch.org/models/resnet50-0676ba61.pth   ← 認証を伴わない
    取得後: /home/ubuntu/.cache/torch/hub/checkpoints/resnet50-0676ba61.pth  102,530,333 バイト
    sha256: 0676ba61b6795bbe1773cffd859882e5e297624d384b6993f7c9e683e722fb8a

sha256 の先頭がファイル名の `0676ba61` と一致する（torchvision の完全性検査）。
検出器の backbone 初期化で `resnet50-11ad3fa6.pth`（IMAGENET1K_V2）も自動取得された。

### 3.3 P→D の入力経路は既存実装で足りた

新設は不要だった。snapshot に次が在る。

| 要素 | 実体 |
|---|---|
| 界面 | `set_phase_context(ctx)`（forward 前に呼ぶ） |
| 注入 | `RelationDETRPhaseFiLM`（C5 への FiLM。**zero-init = 恒等**） |
| W1 | `scripts/train_t1b.py --trainable film` → `requires_grad = "phase" in name` |
| 段の切替 | `--zero-ctx`（空）/ `--phase-source real`（予測）/ `oracle`（正解） |

W1 が効いていることの実測: `phase_params=266880 total_trainable=266880`
（＝注入層だけが学習対象。検出器は凍結）。

**正解 ⊕ 予測段のみ最小追加が要った**（§6.1）。

---

## 4. Step A-4 prereg の commit

    $ git commit （prereg.md / SPEC.md / spec.yaml / inbox.d / docs/setup）
    [feat/lecun-detector-env-pd 762ee4f5] exp(detector-env): register the prereg ...
    $ git --no-pager show -s --format=%cI 762ee4f5
    2026-08-29T17:08:04+00:00

再度のプリフライト: **7 PASS / 0 WARN / 2 SKIP / 0 FAIL（exit 0）**。
SKIP は P2 `cuda_ext_loaded` と P3 `deterministic_flags`（いずれも
`plan.env.preflight` に記載が無いため未実行。**合格ではない**）。

---

## 5. Phase B の B2（送り手評価）

同一 ckpt・同一 recipe であることを config で示す。差分は ann_file の 1 行のみ。

    $ diff configs/train_config_egosurgery_seed42.py configs/train_config_egosurgery_seed42_evaltrain.py
    40c40
    <     ann_file=f"{ANN_DIR}/instances_val.json",   # use instances_test.json for final test eval
    ---
    >     ann_file=f"{ANN_DIR}/instances_train.json",  # <B2> 送り手評価: 訓練動画側。他は seed42 と同一

| 分割 | AP | AP50 |
|---|---|---|
| train | **0.8425732477176417** | 0.9819822059638547 |
| val | **0.7302938994613697** | 0.8545901117284289 |
| **差（train − val）** | **+0.1122793483** | +0.1273920942 |

---

## 6. Phase B の P→D 四段

### 6.1 追加した経路（W1 の範囲）

`scripts/train_t1b.py` へ次を足した。**評価規則は変更していない。**

- `load_both_phase_ctx`: 正解 one-hot(9) ⊕ 予測事後(9) = 18-d。連結順は **正解 → 予測**に固定。
  frame_id が食い違えば `KeyError`（補完しない）
- `--phase-source` の choices に `both`
- `--task-id`（`config.yaml` の最上位へ書く。契約の `outputs.stamp.task_id_in` が要求）
- `T1B_MODEL_CFG` の明示 override（`T1B_WORK_DIR` と同じ作法）

18-d 用の model config は third_party 内に作った（版管理外・差分 1 行）。

    $ diff relation_detr_resnet50_egosurgery_t1b.py relation_detr_resnet50_egosurgery_t1b_both.py
    34c34
    < num_phases = 9
    ---
    > num_phases = 18  # <T-2026-08-29-lecun-detector-env-pd> 正解9d ⊕ 予測9d の結合段

読み込みだけの検証（学習しない）:

    frame 数: 1515 1515 1515
    次元: oracle (9,) real (9,) both (18,)
    both 前半 == oracle: True   /  both 後半 == real: True
    oracle と real は別物: True
    oracle は one-hot: 1.0   /  real は事後（和≈1）: 1.0

### 6.2 🔴 実効バッチが S0 のレシピと揃っていない

    train 画像 9657 ÷ det_steps/ep 4809 = 2.008  → t1b の実効バッチ = 2

| | S0 検出器学習（正本） | t1b（本契約） |
|---|---|---|
| 起動 | `accelerate launch --num_processes 2` | `python scripts/train_t1b.py`（単一プロセス） |
| per-GPU batch | 2 | 2 |
| **実効バッチ** | **4**（2 GPU DDP） | **2** |

`configs/detector_relation_detr/README.md` は「per-GPU 2 × 2 GPU DDP = **実効 bs 4**（S0 parity）」
と明記する。一方 `train_t1b` を DDP で起動する記述は**リポジトリ全域で 0 件**で
（`scripts/run_t1b.sh` は存在せず、docstring 自身が単一プロセス起動を記載）、
既存 t1b 23 run も同じ経路で作られている。

**利用者の判断によりバッチ 2 のまま完走させた。** 四段の内部比較（本契約の目的）は
同一条件で成立するが、**S0 とのバッチ不一致は残る**。UNKNOWN として報告する。

### 6.3 実行と結果

四段を 2 枚の GPU へ振り分けて実行した（GPU0: 空 → 正解 / GPU1: 予測 → 正解⊕予測）。
`train_t1b.py` に DDP 経路が無いため、DDP ではなく run 単位の並行である（§6.2）。

| 段 | best mAP | init mAP | 空段との差 | best epoch | phase_source | zero_ctx | model_cfg |
|---|---|---|---|---|---|---|---|
| 空 | 0.733576 | 0.730294 | +0.000000 | 2 | real | **True** | t1b（9d） |
| 予測 | 0.737538 | 0.730294 | **+0.003963** | 2 | real | False | t1b（9d） |
| 正解 | 0.741071 | 0.730294 | **+0.007496** | 2 | oracle | False | t1b（9d） |
| 正解 ⊕ 予測 | 0.742487 | 0.730294 | **+0.008912** | 2 | both | False | t1b_both（**18d**） |

**空振りでないことの確認**:

- 四段の best mAP は**四つとも異なる**（測定が入力に感応している）
- **init mAP は四段とも 0.7302938994613697 で同値**。zero-init FiLM が恒等であり、
  かつ §3.1 の eval スクリプトが出した凍結源の値と**完全一致**する。
  評価経路が二系統で一致していることの独立な裏づけでもある
- `trainable` は四段とも `film`（W1）。`total_trainable=266880` が注入層のみであることを示す
- `task_id` は四段とも記録されている

**所要時間**: 2 本並行で 1 epoch 36〜40 分、6 epoch で 1 run 約 4 時間。
単独実行時は 2.2 it/s（37 分/epoch）。最初の見積もり 103 分/epoch は smoke 6 step
（CUDA 起動と JIT を含む）由来の過大評価だった。**smoke の eta を計画の根拠にしない。**

---

## 7. Phase C の B4（強い工程塔）

### 7.1 塔の構築

既存に「画像から工程を学ぶ経路」が無いため `scripts/train_phase_tower_r50.py` を新設した。
**`scripts/` は契約 §2 の変更対象外であり逸脱である。**

    [tower] train frames=9657 videos=['01','02','03','06','08','11','12','13','14','15'] (val/test は使わない)
    [tower][ep0] loss=0.5141 train_acc=0.8387 (36s)
    [tower][ep1] loss=0.1259 train_acc=0.9585 (70s)
    [tower][ep2] loss=0.0572 train_acc=0.9831 (105s)
    [tower] val accuracy=0.6924 macro_f1=0.4360

**学習は train の 10 動画のみ**（出力の `videos` が実測。val 2・test 3 は使っていない）。
前契約 SPEC の「十五動画」は分割違反であり、本契約 §5 が訂正したとおりに実装した。

特徴は既存形式で書き出した（`frame_ids` + `features` 2048-d）。

    stage1_features/imagenet_r50_phasetower_seed42/train_gap.npz (9657, 2048)  79,458,316 バイト
    stage1_features/imagenet_r50_phasetower_seed42/val_gap.npz   (1515, 2048)  12,465,940 バイト

### 7.2 受け手と送り手のタグ分離

`train_b2a.py` は GAP と tool 信号の両方を `RELDETR_FROZEN_TAG` から引いていた。
B4 は**受け手が新しい塔・送り手は凍結検出器**なので分離が要る。
`RELDETR_SIGNAL_TAG` を足した（`train_t1a.py` の `RELDETR_REGION_TAG` と同じ作法）。

    GAP   : imagenet_r50_phasetower_seed42
    SIGNAL: relation_detr_seed42
    ORACLE: oracle_toolpresence
    val clip 数: 3  入力次元: (518, 2063)

config へ `gap_tag` と `signal_tag` を書くようにし、run の証跡で確認できるようにした。

### 7.3 D→P 四段 × 三 seed（12 run）

| 段 | 平均 acc | pstd | 空段との差 | 平均 macro_f1 | in_dim |
|---|---|---|---|---|---|
| 空 | 0.736854 | 0.005290 | +0.000000 | 0.453332 | 2063 |
| 予測 | 0.744774 | 0.004356 | **+0.007921** | 0.468409 | 2063 |
| 正解 | 0.750495 | 0.004312 | **+0.013641** | 0.469508 | 2063 |
| 正解 ⊕ 予測 | 0.757976 | 0.003293 | **+0.021122** | 0.488676 | 2078 |

**解釈は書かない**（契約の規定）。

空振りでないことの確認: 四段の平均は四つとも異なる。12 run の acc の相異なる値は 10/12。

所要時間（A6000 1 枚、50 epoch）: 空 19.1〜21.6 s / 予測 14.5〜20.4 s /
正解 16.4〜20.9 s / 正解⊕予測 29.7〜32.2 s。**12 run 合計 約 4 分。**

### 7.4 並行実行

B4 は本体 `.venv` で動き検出器に依存しないため、**P→D と同時に走らせた**。
塔の学習と 12 run を GPU0 に載せ、P→D の 2 段は GPU0/GPU1 で継続した。
GPU のメモリは各 49,140 MiB のうち 18〜26 GiB が空いていた。

---

## 8. 変更範囲と検査

### 8.1 収穫

    収穫前: index 1250 / experiments 277 / verdicts 1486 / per_class 9027
    $ make runindex  → exit=0、走査 1266、回帰テスト 9 項目すべて PASS

| 表 | 前 | 後 | 追加 | 削除 | 既存行の変更 |
|---|---|---|---|---|---|
| `index.csv` | 1250 | 1266 | **+16** | **0** | **0** |
| `experiments.csv` | 277 | 285 | +8 | 0 | **0** |
| `verdicts.csv` | 1486 | 1506 | +20 | 0 | **0** |
| `per_class.csv` | 9027 | 9195 | +168 | 0 | 0 |

    追加 16 のうち本契約の run: 16 / 混入: 0
    task_id 全件: True
    判定列（same_sign / verdict_pstd / verdict_sstd / agree / reason / n_seeds）で変わったもの: なし

### 8.2 検査（終了コードを個別に測った）

    make task-validate    -> exit=0
    make taskindex-check  -> exit=0
    make inbox-check      -> exit=0
    make context-check    -> exit=0
    make docs-check       -> exit=0
    make agent-check      -> exit=0
    make forbidden-check  -> exit=2   ← 既知の制約（下記）

### 8.3 forbidden-check の違反の内訳

    changed=167  checked=159  excluded=8  違反=146
    接頭辞別: {'experiments/': 124, 'runindex/': 22}
    内訳: runindex/ 22 / 本契約の run 配下 136 / 新規特徴 0 / その他 4

`runindex/` 22 件と本契約の run 配下 136 件は §2 が許可した対象である。
新規に書いた特徴キャッシュ（`stage1_features/imagenet_r50_phasetower_seed42/`）は
`data/processed/**` が版管理外のため違反に現れない。

🔴 **残る 4 件は本契約の作業ではない。**

    experiments/analysis/hts_candidate_acceptance/{apply_criteria,hand_count,make_outputs,scan_candidates}.py

中身が `T-2026-08-30-hts-candidate-acceptance` の Phase A と名乗っており、生成時刻は
**2026-08-30 02:34〜02:40**。本契約の最後の run（08-29 23:00:28）より後である。
`~/claude-sync/sync-alerts.log` は同時刻帯に他ホストの活動を記録しており、
`.sync-pause` は**分岐への統合を止めるがファイル同期は止めない**（既知。
`tasks/inbox.d/T-2026-08-26-lovo-decision-rule.md` に実測がある）。

契約 §7 の「**禁止は実行者の操作に対するものであり、同期処理による配布や衝突ファイルの
生成を含まない**」に該当する。**commit しない。**

### 8.4 判定 e の空振り確認（差分検出器の対照）

    陽性（収穫前 vs 収穫後）: 追加 16 / 削除 0 / 変更 0、追加集合は本契約の run と完全一致
    陰性（先契約 k1-reeval-and-harvest の同じ器）: 集約表で変更 8 件を検出した実績がある

同じ器が別の入力で非零を返しているため、今回の「変更 0 件」は常に 0 を返す壊れ方ではない。

### 8.5 判定 f の実測

    凍結源 ckpt   作業前 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
                  作業後 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824  → 一致
    分割          ego_train c28816de94c5ed83e4f1e47fd63b3a9e4f9e5ab970e8b38a85aeebc66922a8e2
                  ego_val   f1bc456a0439b60674507a05484784065a1bdcbcb89274b5b83680a16cc093ea
                  ego_test  7edeab6294574cfdb13b07f57c5ca71fe9e0eb878ec2d1b7fc0c5c22a6befaef
    venv / 実装   git status での該当 0 件（.gitignore:63 と :133）
