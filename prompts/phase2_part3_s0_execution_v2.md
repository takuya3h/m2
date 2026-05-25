# フェーズ II — Part 3/5（改訂版 v2.1）: S0 評価指標 + トレーナー + 実行

> **改訂履歴 v2（2026/05/24 研究計画 §14・§15 反映）**
> - 【重大・§15.2】評価時の test_cfg を locked-down 値（score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6）に強制
> - 【重大・§15.3 G3】metrics.json に eval_recipe を併記
> - 【訂正】稀少クラス（AP_rare）を Skewer / Syringe の 2 クラスに修正。Forceps は AP_common に分類
> - トレーナー名を研究計画 §14 と統一: `StageATrainer` → `MMDetTrainer`
> - server_name 記録を学習フローに統合
> - フェーズ I 追加修正プロンプト（eval_recipe）の適用を前提とする
>
> **改訂履歴 v2.1（2026/05/25 §13.2・§9 #6・§8.0 反映）**
> - 【追加】Co-DETR を S0 の追加実験（`s0_007`〜`s0_009`）として `run_s0.sh` に追記（§13.2 S0）
> - 【追加】§9 #6 判断ポイント（Mask DINO vs Co-DETR の APr 比較で切替）の判定手順を明記
> - 【追加】§8.0 暫定運用の 3 条件（Ada 未配備期間の bengio 使用ルール、Ada 配備後の再測定）を明記

前提: Part 1（データパイプライン v2）、Part 2（モデル、Co-DETR 含む v2.1）、および「フェーズ I 追加修正プロンプト（eval_recipe 整合性検証）」が完了済み。

Part 3 では **S0 の評価指標**、**MMDetTrainer**、**実行スクリプト** を実装し、S0 を完走させる。
Part 3 の完了 = S0 の完了 = §2.5(a) 基準点の確立。

> **既存 S0 実験の扱い（重要）**: VFNet / Mask DINO の S0 学習が既に進行中・完了済みの場合、それは破棄しない。S0 完了判定は「VFNet が 45.8 を上回る」ことのみで定義され、進行中の学習はそのまま継続してよい。Co-DETR は §9 #6 の判断ポイント専用の**追加実験**であり、既存実験とは独立に `s0_007`〜`s0_009` として後から差し込む。**手順のやり直しは不要。**

> **監査で判明した現状（2026/05/25 ddp_migration_audit）**
> - `src/egosurgery/engines/mmdet_trainer.py` は**既に存在するが単一 GPU 版**であり、
>   `DistributedDataParallel`・`WORLD_SIZE` への参照が**ない**。本プロンプトの
>   §2 は、この既存の単一 GPU 版 MMDetTrainer を**DDP 対応に書き換える**作業である
>   （ゼロから新規作成するのではない）。`view` で既存実装を確認し、setup・
>   _build_model・_build_dataloader・evaluate・_init_wandb・_resolve_lr 等を
>   DDP 対応に改修する。既存の `_build_mmdet_cfg`（test_cfg 上書き）など
>   正しく動いている部分はロジックを保ったまま DDP 文脈に組み込む。
> - `scripts/run_s0.sh` は**既に存在するが `python -m egosurgery.train` のまま**で
>   `torchrun` を使っていない。本プロンプトの §3 は、この既存 run_s0.sh を
>   `torchrun --nproc_per_node=2` 版に**書き換える**作業である。
> - 停止した単一 GPU の S0 学習成果物が `experiments/baselines/` に残っている
>   場合、DDP 再実行で `s0_001`〜`s0_006` が上書き・混同されないよう、
>   事前に `experiments/baselines/_single_gpu_aborted/` 等へ退避しておくこと
>   （退避はユーザーが実施済みか確認する。§14 と整合）。

---

## 0. 最重要原則（§15）

S0 は研究全体の Δ の分母である。研究計画 §15.4 A は、S0 が正当な Δ 基準点であるための **strict 3 条件** を定める:

1. データ split が EgoSurgery-Tool 公式（train 9657 / val 1515 / test 4265 images）
2. test_cfg が locked-down 値（score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6）
3. metrics.json の `eval_recipe` がこれらと一致

Part 3 はこの 3 条件を**コードで強制**する。

---

## 1. 評価指標

### `src/egosurgery/metrics/detection.py`

```python
class DetectionEvaluator:
    """
    COCO mAP ベースの検出評価（§7.2）。

    出力する指標:
    - mAP（全体）: COCO AP@[.5:.95]
    - mAP@50: COCO AP@.50
    - mAP@75: COCO AP@.75
    - per_class_ap: 全 15 クラスの AP（dict）
    - AP_rare: 稀少クラス（Skewer / Syringe）の平均 AP
    - AP_common: それ以外 13 クラスの平均 AP
    - confusion_matrix: 予測クラス × GT クラスの 15×15 行列
    - shape_similar_confusion: Forceps/Tweezers/Needle Holders/Bipolar Forceps の 4×4 部分行列

    【2026/05/24 訂正】
    - Forceps は 12.21%（トップ3頻出クラス）→ AP_common に分類
    - AP_rare は Skewer / Syringe の 2 クラスのみ
    """

    RARE_CLASSES = ["Skewer", "Syringe"]
    SHAPE_SIMILAR = ["Forceps", "Tweezers", "Needle Holders", "Bipolar Forceps"]

    def evaluate(self, predictions, ground_truth):
        """COCO AP を算出し、上記の全指標を dict で返す。"""
        pass
```

---

## 2. MMDetTrainer（DDP 2 GPU 対応）

### `src/egosurgery/engines/mmdet_trainer.py`

```python
class MMDetTrainer:
    """
    検出モデル（Mask DINO / VarifocalNet / Co-DETR）の学習・評価トレーナー（§14 命名に統一）。

    【§15 反映の最重要ポイント】
    1. _build_mmdet_cfg() で test_cfg を locked-down 値に強制上書き
    2. evaluate() で eval_recipe を metrics.json に併記
    3. setup() で server.txt を記録

    【§13.2 DDP 2 GPU 実装要件（2026/05/25 追加）】
    4. setup() で DistributedDataParallel / DistributedSampler を初期化
    5. _build_eval_recipe() に gpu_count・effective_batch_size を記録
    6. evaluate() の metrics 書き出しは rank=0 のみ（重複書き込み防止）
    7. SyncBatchNorm は BN を使うモデルのみ選択的に適用
    """

    def __init__(self, cfg, experiment_manager):
        self.cfg = cfg
        self.em = experiment_manager
        # === DDP 状態（setup() で確定） ===
        self.is_distributed = False
        self.rank = 0
        self.world_size = 1
        self.local_rank = 0

    def setup(self):
        """
        学習前のセットアップ。
        1. DDP 環境を検出・初期化（torchrun 起動時のみ）
        2. ExperimentManager.setup() で実験フォルダを作成（rank=0 のみ）
        3. server_name を resolve し server.txt に書き出す（rank=0 のみ）
        4. W&B の tags に server:{name} を追加（rank=0 のみ）
        """
        import os
        import torch.distributed as dist
        from egosurgery.utils.server_name import resolve_server_name

        # --- DDP 環境の検出（§13.2 (b)(ii)） ---
        # torchrun は WORLD_SIZE / RANK / LOCAL_RANK 環境変数を設定する
        self.world_size = int(os.environ.get("WORLD_SIZE", "1"))
        self.rank = int(os.environ.get("RANK", "0"))
        self.local_rank = int(os.environ.get("LOCAL_RANK", "0"))
        self.is_distributed = self.world_size > 1

        if self.is_distributed:
            # NCCL backend で process group を初期化
            dist.init_process_group(backend="nccl")
            import torch
            torch.cuda.set_device(self.local_rank)

        self.server_name = resolve_server_name(self.cfg)

        # --- 実験フォルダ作成・server.txt は rank=0 のみ（§13.2 (b)(iii)） ---
        if self.rank == 0:
            self.em.setup()
            server_path = os.path.join(self.em.exp_dir, "server.txt")
            with open(server_path, "w") as f:
                f.write(self.server_name)
        # 全 rank が exp_dir を知る必要がある場合は broadcast する
        if self.is_distributed:
            dist.barrier()

    def _build_model(self):
        """
        モデルを構築し、DDP / SyncBatchNorm を適用する（§13.2 (b)(iv)）。
        """
        import torch
        import torch.nn as nn
        from egosurgery.models.build import build_model

        model = build_model(self.cfg).cuda(self.local_rank)

        if self.is_distributed:
            # SyncBatchNorm は BN を含むモデルのみ変換する。
            # DINOv2 ViT 本体は LayerNorm 主体のため変換不要。
            # ViT-Adapter や一部の detection neck が BatchNorm を含む場合のみ効く。
            # convert_sync_batchnorm は BN が無ければ何も変えないが、
            # 明示的に「BN を持つか」を判定してから適用する方が意図が明確。
            has_bn = any(
                isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d))
                for m in model.modules()
            )
            if has_bn:
                model = nn.SyncBatchNorm.convert_sync_batchnorm(model)
            model = nn.parallel.DistributedDataParallel(
                model, device_ids=[self.local_rank],
                output_device=self.local_rank,
                find_unused_parameters=False,  # 必要なら True に
            )
        return model

    def _build_dataloader(self, dataset, is_train: bool):
        """
        DataLoader を構築する。DDP 時は DistributedSampler を使う（§13.2 (b)(ii)）。
        """
        import torch
        from torch.utils.data import DataLoader

        sampler = None
        if self.is_distributed:
            sampler = torch.utils.data.distributed.DistributedSampler(
                dataset, num_replicas=self.world_size, rank=self.rank,
                shuffle=is_train,
            )
        return DataLoader(
            dataset,
            batch_size=self.cfg.dataloader.batch_size,   # これは per-GPU batch size
            shuffle=(sampler is None and is_train),
            sampler=sampler,
            num_workers=self.cfg.dataloader.num_workers,
            pin_memory=True,
        )

    def _build_mmdet_cfg(self, detector_cfg):
        """
        mmdet の config を構築する。
        【§15.3 G1 最重要】test_cfg を locked-down 値で強制上書きする。
        detector ごとの mmdet default 差を排除する。

        対応 detector: Mask DINO / VarifocalNet / Co-DETR。
        いずれも test_cfg は同一構造で上書きできる（detector 名で分岐しない）。
        """
        from egosurgery.utils.eval_recipe import LOCKED_DOWN_TEST_CFG

        # 全 detector・全 stage で以下を強制
        detector_cfg.model.test_cfg.score_thr = LOCKED_DOWN_TEST_CFG["score_thr"]      # 1e-8
        detector_cfg.model.test_cfg.max_per_img = LOCKED_DOWN_TEST_CFG["max_per_img"]  # 300
        detector_cfg.model.test_cfg.nms_pre = LOCKED_DOWN_TEST_CFG["nms_pre"]          # 3000
        detector_cfg.model.test_cfg.nms.iou_threshold = LOCKED_DOWN_TEST_CFG["nms_iou"]  # 0.6

        return detector_cfg

    def _resolve_lr(self):
        """
        DDP の effective batch size に応じて learning rate を決定する（§13.2 (a)）。

        方針は cfg.train.lr_scaling_mode で選択する:
        - "linear": effective batch size の倍率だけ lr を線形スケーリング
          （単一 GPU lr=1e-4 → DDP 2 GPU で per-GPU bs 同一なら lr=2e-4）
        - "keep_effective_bs": per-GPU batch size を下げて effective bs を
          単一 GPU 時と同じに保ち、lr は据え置く

        選択結果は eval_recipe の lr_scaling フィールドに記録する。
        """
        base_lr = self.cfg.train.lr  # 単一 GPU 基準の lr（1e-4）
        mode = self.cfg.train.get("lr_scaling_mode", "linear")

        if not self.is_distributed:
            self._lr_scaling_label = "none"
            return base_lr

        if mode == "linear":
            self._lr_scaling_label = f"linear_x{self.world_size}"
            return base_lr * self.world_size
        elif mode == "keep_effective_bs":
            self._lr_scaling_label = "per_gpu_bs_adjusted"
            return base_lr
        else:
            raise ValueError(f"unknown lr_scaling_mode: {mode}")

    def _build_eval_recipe(self):
        """
        eval_recipe を構築する（§15.3 G3・§8.0 条件 (5)(6)）。
        metrics.json に併記する評価条件の記録。
        gpu_count・effective_batch_size・lr_scaling を含める。
        """
        from egosurgery.utils.eval_recipe import (
            LOCKED_DOWN_TEST_CFG, PAPER_SPLIT_SIZES, build_eval_recipe
        )
        per_gpu_bs = self.cfg.dataloader.batch_size
        effective_bs = per_gpu_bs * self.world_size
        return build_eval_recipe(
            test_cfg=LOCKED_DOWN_TEST_CFG,
            split_sizes=PAPER_SPLIT_SIZES,
            server_name=self.server_name,
            gpu_count=self.world_size,
            effective_batch_size=effective_bs,
            lr_scaling=getattr(self, "_lr_scaling_label", "none"),
        )

    def train(self):
        """
        学習ループ。
        - AdamW, lr は _resolve_lr() で決定（DDP 時は linear scaling）, weight_decay=0.05
        - cosine scheduler with warmup (5 epochs)
        - AMP bf16
        - gradient checkpointing enabled
        - 全設定は S0〜S9 で完全に同一（GPU 構成も含む）
        - DDP 時は各 epoch 開始時に sampler.set_epoch(epoch) を呼ぶ
        """
        pass

    def evaluate(self):
        """
        評価を実行し、metrics.json に結果 + eval_recipe を書き出す。
        【§13.2 (b)(iii)】metrics の書き出しは rank=0 のみ（重複防止）。
        """
        evaluator = DetectionEvaluator()
        # 推論は全 rank で分担し、rank=0 に集約する（dist.all_gather 等）
        metrics = evaluator.evaluate(self.predictions, self.ground_truth)

        # --- 書き出しは rank=0 のみ ---
        if self.rank != 0:
            return metrics

        # eval_recipe を併記（§15.3 G3・DDP フィールド込み）
        eval_recipe = self._build_eval_recipe()
        metrics["eval_recipe"] = eval_recipe

        # per_class_ap を別ファイルにも保存
        self.em.save_metrics(metrics)
        self.em.save_per_class_ap(metrics["per_class_ap"])

        # confusion matrix を npy で保存
        np.save(
            os.path.join(self.em.exp_dir, "confusion_matrix.npy"),
            metrics["confusion_matrix"]
        )
        return metrics

    def _init_wandb(self):
        """
        W&B の初期化。
        - tags に server:{server_name} と gpu:{world_size} を追加
        - config に server_name・gpu_count・effective_batch_size を含める
        - 【§13.2 (b)(iii)】W&B init は rank=0 のみ
        """
        if self.rank != 0:
            return
        import wandb
        wandb.init(
            project="egosurgery_multitask",
            group=f"s0_{self.cfg.model.name}",
            tags=[f"server:{self.server_name}", f"gpu:{self.world_size}", "s0", "baseline"],
            config=OmegaConf.to_container(self.cfg, resolve=True),
        )
```

---

## 3. 実行スクリプト

### `scripts/run_s0.sh`

```bash
#!/bin/bash
# =============================================================================
# S0: 術具検出ベースライン（§2.5(a) 基準点）— DDP 2 GPU 版
#
# 実行サーバー（§8.0・§14）:
#   本来は RTX 6000 Ada ×1（Δ 基準点専用）。
#   RTX 6000 Ada 未配備期間は bengio（RTX A6000 ×2）の DDP 2 GPU で実行する。
#   §14 の方針変更により、S0 全モデル（VFNet・Mask DINO・Co-DETR）を
#   DDP 2 GPU で統一して学習する。単一 GPU 学習結果は Δ 基準点に使わない。
#
#   §8.0 暫定運用の 6 条件をすべて満たすこと:
#     (1) 同一 Δ 比較群（S0 の VFNet・Mask DINO・Co-DETR）は同一サーバーで測定
#     (2) eval_recipe.server_name と server.txt にサーバー名を記録
#     (3) RTX 6000 Ada 配備後の再測定の必要性を Notion §14 に明記
#     (4) DDP 使用時は S0 内の全モデルを同一 GPU 構成（2 GPU）で揃える
#         ← 本スクリプトは VFNet・Mask DINO・Co-DETR をすべて 2 GPU で統一
#     (5) effective batch size を eval_recipe に記録（_build_eval_recipe が実施）
#     (6) lr 線形スケーリングの適用を config に明記（train.lr_scaling_mode）
#
# 【§15.4 A strict 3 条件】
# - データ split: 論文公式（train 9657 / val 1515 / test 4265）
# - test_cfg: locked-down（score_thr=1e-8, max_per_img=300）
# - eval_recipe: metrics.json に併記（gpu_count=2, effective_batch_size 込み）
#
# 旧 split（_wrong_split_8_2_3）の checkpoint は使用禁止。
# 進行中・完了済みの単一 GPU S0 学習結果も Δ 基準点には使用しない（§14）。
# =============================================================================

set -euo pipefail

EPOCHS=12
SEEDS=(42 123 456)
NPROC=2                       # bengio = RTX A6000 ×2
PER_GPU_BS=2                  # per-GPU batch size。effective bs = 2 GPU × 2 = 4
LR_SCALING_MODE=linear        # §13.2 (a): linear scaling（lr × 2）

# detector ごとのインデックス（MASTER_PORT のユニーク化に使う）
declare -A DET_IDX=( ["mask_dino"]=0 ["vfnet"]=1 ["codetr"]=2 )

# 全 detector 共通の学習関数
run_ddp() {
    local model=$1
    local seed=$2
    local seed_idx=$3
    local det_idx=${DET_IDX[$model]}
    # MASTER_PORT を seed/detector ごとにユニーク化（並列実行時のポート競合回避、§13.2 (c)）
    local port=$((29500 + seed_idx * 3 + det_idx))

    MASTER_PORT=${port} torchrun \
        --nproc_per_node=${NPROC} \
        --master_port=${port} \
        -m egosurgery.train \
        stage=s0_tool_baseline \
        model=${model} \
        seed=${seed} \
        train.epochs=${EPOCHS} \
        dataloader.batch_size=${PER_GPU_BS} \
        train.lr_scaling_mode=${LR_SCALING_MODE} \
        logging.server_name=bengio
}

# === Mask DINO × 3 seeds（s0_001 ~ s0_003）===
seed_idx=0
for seed in "${SEEDS[@]}"; do
    run_ddp mask_dino ${seed} ${seed_idx}
    seed_idx=$((seed_idx + 1))
done

# === VarifocalNet × 3 seeds（s0_004 ~ s0_006）===
seed_idx=0
for seed in "${SEEDS[@]}"; do
    run_ddp vfnet ${seed} ${seed_idx}
    seed_idx=$((seed_idx + 1))
done

# === Co-DETR × 3 seeds（s0_007 ~ s0_009）===
# §13.2 S0「Mask DINO・VarifocalNet・Co-DETR を準備」、§9 #6 判断ポイント用。
seed_idx=0
for seed in "${SEEDS[@]}"; do
    run_ddp codetr ${seed} ${seed_idx}
    seed_idx=$((seed_idx + 1))
done

echo "S0 完了: experiments/baselines/ に s0_001 ~ s0_009 が生成されたことを確認してください"
echo "完了判定: VarifocalNet mAP >= 45.8（公式 split・locked-down test_cfg・DDP 2 GPU 条件下）"
echo "全 metrics.json の eval_recipe.gpu_count == 2 を確認してください（§8.0 条件 (4)(5)）"
echo "判断ポイント #6: 下記コマンドで Mask DINO vs Co-DETR の APr 比較を実行してください"
echo "  python scripts/compare_judge6.py"
```

> **DDP 2 GPU 統一の必須性（§8.0 条件 (4)・§14）**: S0 の VFNet・Mask DINO・Co-DETR は
> Δ 比較群を構成するため、**全モデルを同一 GPU 構成（2 GPU DDP）で揃えなければならない**。
> 特定モデルだけ単一 GPU で学習することは禁止される（effective batch size・NCCL allreduce
> 非決定性・BN/LN 挙動差により Δ の意味が崩壊するため）。進行中・完了済みの単一 GPU
> 学習結果（Mask DINO / VFNet）は §14 の通り Δ 基準点に使わず、本スクリプトで
> `s0_001`〜`s0_009` の 9 実験すべてを DDP 2 GPU で再学習する。
>
> **lr スケーリングの記録（§8.0 条件 (6)）**: 本スクリプトは `train.lr_scaling_mode=linear`
> を指定し、DDP 2 GPU で effective batch size が 2 倍になる分 lr を線形スケーリング（lr×2）
> する。この選択は config に渡され、`MMDetTrainer._resolve_lr()` が適用し、
> `eval_recipe.lr_scaling` に `"linear_x2"` として記録される。per-GPU batch size を
> 下げて effective batch size を単一 GPU 時と同じに保つ運用に切り替える場合は
> `train.lr_scaling_mode=keep_effective_bs` を指定する。

### `scripts/compare_judge6.py`（§9 #6 判断ポイント）

```python
"""
判断ポイント #6（§9 #6・§13.2 S0）:
Mask DINO vs Co-DETR を APr（稀少クラス AP = Skewer / Syringe の平均）で比較し、
3pt 以上の差が出れば S1 以降を Co-DETR ベースに切り替えるべきと判定する。

- Mask DINO の APr: s0_001 ~ s0_003 の 3-seed 平均
- Co-DETR の APr:   s0_007 ~ s0_009 の 3-seed 平均
- DeltaCalculator で eval_recipe 整合性を検証してから比較する
  （同一 split・同一 test_cfg・同一サーバー・同一 GPU 構成であること。
   gpu_count が一致しないと recipes_match が False を返し比較不能）

出力:
- 両モデルの APr 平均±標準偏差
- 差分 ΔAPr = APr(Co-DETR) - APr(Mask DINO)
- 判定: |ΔAPr| >= 3.0 なら「検出ヘッド切替を検討」、未満なら「Mask DINO 継続」

使い方:
    python scripts/compare_judge6.py \
        --maskdino_dir experiments/baselines/ \
        --maskdino_prefix s0_001,s0_002,s0_003 \
        --codetr_prefix s0_007,s0_008,s0_009
"""
```

### `configs/stage/s0_tool_baseline.yaml`

```yaml
stage:
  name: s0_tool_baseline
  category: baselines
  description: "S0: 術具検出ベースライン（§2.5(a) 基準点）"
  tasks: ["tool_detection"]
  direction: "none"  # 単方向（検出のみ）
  phase_head: false
  feedback: false
```

### `configs/default.yaml` への train セクション追記

```yaml
train:
  epochs: 12
  lr: 1.0e-4                  # 単一 GPU 基準の learning rate
  weight_decay: 0.05
  # === DDP lr スケーリング（§8.0 条件 (6)・§13.2 (a)） ===
  lr_scaling_mode: linear     # "linear": effective bs 倍率で lr を線形スケーリング
                              # "keep_effective_bs": per-GPU bs を下げて effective bs 維持
```

---

## 4. テスト

`tests/test_engines.py` に以下を実装:

1. `test_mmdet_trainer_setup`: setup() 後に実験フォルダ・server.txt・config.yaml が存在する
2. `test_mmdet_trainer_locked_test_cfg`: `_build_mmdet_cfg()` が test_cfg を locked-down 値に上書きする
3. `test_mmdet_trainer_eval_recipe`: `_build_eval_recipe()` が正しい構造の dict を返す
4. `test_mmdet_trainer_eval_recipe_in_metrics`: evaluate() 後の metrics.json に `eval_recipe` が含まれる
5. `test_mmdet_trainer_server_txt`: setup() 後に server.txt が存在し中身が空でない
6. `test_mmdet_trainer_wandb_tags`: W&B init の tags に `server:` タグが含まれる
7. `test_mmdet_trainer_codetr_locked_test_cfg`: Co-DETR でも `_build_mmdet_cfg()` が test_cfg を locked-down 値に上書きする
8. `test_compare_judge6_logic`: `compare_judge6.py` の判定ロジックが、|ΔAPr| >= 3.0 で「切替検討」、未満で「継続」を返す
9. `test_mmdet_trainer_eval_recipe_ddp_fields`: `_build_eval_recipe()` の返り値に `gpu_count`・`effective_batch_size`・`lr_scaling` が含まれる
10. `test_mmdet_trainer_single_gpu_fallback`: WORLD_SIZE 未設定（単一 GPU）時に `is_distributed=False`・`gpu_count=1` になる
11. `test_resolve_lr_linear_scaling`: `lr_scaling_mode=linear` かつ world_size=2 で lr が 2 倍になる
12. `test_resolve_lr_keep_effective_bs`: `lr_scaling_mode=keep_effective_bs` で lr が据え置かれる
13. `test_mmdet_trainer_evaluate_rank0_only`: rank≠0 では metrics.json が書き出されない（モック rank で確認）
14. `test_sync_bn_applied_only_with_bn`: BN を含むモデルでのみ SyncBatchNorm 変換が走る（DDP 環境のモックまたは skip 可）

DDP の実挙動テスト（実際に 2 プロセス起動）は CI 環境では難しいため、`is_distributed` の分岐ロジック・`_resolve_lr`・`_build_eval_recipe` の単体テストで代替し、2 プロセス起動の統合テストは `pytest.mark.skipif`（GPU 2 枚未満でスキップ）とする。

---

## 5. 完了判定

1. `pytest tests/test_engines.py -v` が全テストパスする
2. `bash scripts/run_s0.sh` が 9 実験を **DDP 2 GPU で**完走する（VFNet・Mask DINO・Co-DETR 全モデル統一）
3. `experiments/baselines/` に `s0_001_` 〜 `s0_009_` が存在する（Mask DINO ×3 + VFNet ×3 + Co-DETR ×3）
4. 各実験フォルダに config.yaml / metrics.json / per_class_ap.json / notes.md / server.txt / confusion_matrix.npy が存在する
5. **全 metrics.json の `eval_recipe.split_train_images == 9657`** かつ **`eval_recipe.test_cfg.score_thr == 1e-8`**【§15.4 A の strict 3 条件】
6. **全 metrics.json の `eval_recipe.gpu_count == 2`** かつ **`eval_recipe.effective_batch_size` が全 9 実験で同一**【§8.0 条件 (4)(5)】
7. **全 metrics.json の `eval_recipe.lr_scaling` が記録されている**（`linear_x2` 等、§8.0 条件 (6)）
8. VarifocalNet の mAP が公式 split・locked-down test_cfg・DDP 2 GPU の条件下で計測され目標値 45.8 を超える値を出す
9. Mask DINO の mAP が計測されている
10. Co-DETR の mAP が計測されている
11. AP_rare が Skewer / Syringe の 2 クラスで算出されている（Forceps を含まない）
12. 4×4 shape_similar confusion matrix が保存されている
13. `pytest tests/ -v` が全テストパスする
14. W&B の各 run の tags に `server:bengio` と `gpu:2` が付いている
15. `compare_judge6.py` が Mask DINO vs Co-DETR の APr 比較結果（ΔAPr と判定）を出力する（§9 #6）
16. **S0 の 9 実験すべてが同一サーバー・同一 GPU 構成（2 GPU DDP）で測定されている**（§8.0 条件 (1)(4)）
17. **単一 GPU で学習した旧 S0 実験を Δ 基準点として使っていない**（§14：単一 GPU と DDP の混在禁止）

---

## 6. この Part で触らないファイル

- `src/egosurgery/engines/phase_trainer.py` → Part 4
- `src/egosurgery/engines/temporal_trainer.py` → Part 5
- `src/egosurgery/models/heads/phase_head.py` → Part 4
- `src/egosurgery/models/temporal/` 配下 → Part 5
