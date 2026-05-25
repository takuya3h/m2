# フェーズ I 追加修正プロンプト：eval_recipe 整合性検証 & server_name 記録

> **改訂理由（2026/05/24 研究計画 §15 反映）**
> S0 完走後に発覚した split 取り違え（§15.1）と test_cfg 不一致（§15.2）を受け、Δ 基準点の信頼性を担保するための eval_recipe 整合性検証と server_name 記録をフェーズ I パイプラインに追加する。
> 本プロンプトは Phase II Part 1 の**前提条件**であり、Part 1 着手前に必ず適用すること。
>
> **改訂 v2（2026/05/25 §8.0 DDP 運用条件・§13.2 DDP 実装要件 反映）**
> S0 を bengio（RTX A6000 ×2）の DDP 2 GPU で再実行する方針変更（§14）に伴い、eval_recipe に `gpu_count` と `effective_batch_size` を追加する（§8.0 条件 (5)）。これにより `DeltaCalculator` は「同一 GPU 構成での測定同士」を照合できる。単一 GPU と DDP 2 GPU の混在は §8.0 条件 (4) で禁止されているため、recipe 照合の対象に GPU 構成を含める。

---

## 0. 前提

- フェーズ I（ディレクトリ構造 + 実験パイプライン）は完了済み
- `ExperimentManager` / `DeltaCalculator` / `train.py` / Hydra config / W&B 連携が動作する状態
- 本修正は既存ファイルへの**追加・拡張のみ**であり、models / datasets / engines は触らない

> **監査で判明した現状（2026/05/25 ddp_migration_audit）**
> `src/egosurgery/utils/eval_recipe.py` は**既に存在する**が、`build_eval_recipe` に
> `gpu_count` 引数が**ない旧版**である。したがって本プロンプトの作業は、
> `eval_recipe.py` を新規作成するのではなく、**既存の `eval_recipe.py` を
> v2 仕様（DDP フィールド追加）に書き換える差分修正**である。
> `server_name.py`・`delta.py` も既存の可能性が高いため、まず `view` で
> 現状を確認し、不足分のみ追加すること。`create_file` がファイル既存で
> 失敗する場合は `str_replace` または既存ファイルへの追記で対応する。

---

## 1. 新規ファイル：eval_recipe モジュール

### `src/egosurgery/utils/eval_recipe.py`

以下の定数・関数を実装する。

```python
"""
Evaluation recipe: Δ 基準点の正当性を保証するための評価条件記録モジュール。
§15.3 G3・§15.4 A・§8.-1 に準拠。
"""

# === Locked-down test_cfg（§15.3 G1） ===
LOCKED_DOWN_TEST_CFG = {
    "score_thr": 1e-8,
    "max_per_img": 300,
    "nms_pre": 3000,
    "nms_iou": 0.6,
}

# === 論文公式 split サイズ（§15.1・Table 3a） ===
PAPER_SPLIT_SIZES = {
    "train": {"images": 9657, "annotations": 32272},
    "val":   {"images": 1515, "annotations": 4707},
    "test":  {"images": 4265, "annotations": 12673},
}

# === 論文公式 split の動画割り当て ===
PAPER_SPLIT_VIDEOS = {
    "train": ["01", "02", "03", "06", "08", "11", "12", "13", "14", "15"],  # 10 videos
    "val":   ["09", "10"],                                                    # 2 videos
    "test":  ["04", "05", "07"],                                              # 3 videos
}


def build_eval_recipe(test_cfg: dict, split_sizes: dict, server_name: str,
                      gpu_count: int = 1, effective_batch_size: int = None,
                      lr_scaling: str = "none") -> dict:
    """
    評価条件を構造化した dict を返す。metrics.json に併記する。

    Args:
        test_cfg: 検出後処理の設定（score_thr, max_per_img, nms_pre, nms_iou）
        split_sizes: {"train": {"images": N, "annotations": M}, "val": ..., "test": ...}
        server_name: 実行サーバー名（例: "bengio"）
        gpu_count: 学習に使った GPU 枚数（§8.0 条件 (5)。単一 GPU=1, DDP 2 GPU=2）
        effective_batch_size: gpu_count × per-GPU batch size（§8.0 条件 (5)）
        lr_scaling: lr 線形スケーリングの適用状況（§8.0 条件 (6)）。
                    "none"（単一 GPU）/ "linear_x2"（DDP 2 GPU で lr×2）/
                    "per_gpu_bs_adjusted"（per-GPU bs を下げて effective bs を維持）

    Returns:
        eval_recipe dict
    """
    return {
        "test_cfg": test_cfg,
        "split_train_images": split_sizes["train"]["images"],
        "split_train_annotations": split_sizes["train"]["annotations"],
        "split_val_images": split_sizes["val"]["images"],
        "split_val_annotations": split_sizes["val"]["annotations"],
        "split_test_images": split_sizes["test"]["images"],
        "split_test_annotations": split_sizes["test"]["annotations"],
        "server_name": server_name,
        # === DDP / GPU 構成（§8.0 条件 (4)(5)(6)） ===
        "gpu_count": gpu_count,
        "effective_batch_size": effective_batch_size,
        "lr_scaling": lr_scaling,
    }


def recipes_match(recipe_a: dict, recipe_b: dict) -> bool:
    """
    2 つの eval_recipe が Δ 計算に互換かを判定する。
    test_cfg・split サイズ・GPU 構成（gpu_count）が一致していれば True。
    server_name の不一致は警告のみ（例外にしない）。

    【§8.0 条件 (4)】gpu_count が異なる（単一 GPU vs DDP 2 GPU）測定同士は
    effective batch size・NCCL allreduce 非決定性・BN/LN 挙動差により
    Δ の意味が崩壊するため、recipe 不一致とみなす（False を返す）。
    """
    # test_cfg の全項目を比較
    for key in LOCKED_DOWN_TEST_CFG:
        if recipe_a.get("test_cfg", {}).get(key) != recipe_b.get("test_cfg", {}).get(key):
            return False
    # split サイズを比較
    for key in ["split_train_images", "split_val_images", "split_test_images"]:
        if recipe_a.get(key) != recipe_b.get(key):
            return False
    # GPU 構成を比較（§8.0 条件 (4)：単一 GPU と DDP の混在禁止）
    if recipe_a.get("gpu_count") != recipe_b.get("gpu_count"):
        return False
    if recipe_a.get("effective_batch_size") != recipe_b.get("effective_batch_size"):
        return False
    return True
```

### `src/egosurgery/utils/server_name.py`

```python
"""
実行サーバー名の解決（§14・§8.0）。
優先順: EGOSURGERY_SERVER_NAME 環境変数 → Hydra logging.server_name → socket.gethostname()
"""
import os
import socket
from omegaconf import DictConfig, OmegaConf


def resolve_server_name(cfg: DictConfig) -> str:
    """実行サーバー名を解決する。"""
    # 1. 環境変数
    env_name = os.environ.get("EGOSURGERY_SERVER_NAME")
    if env_name:
        return env_name
    # 2. Hydra config
    try:
        cfg_name = OmegaConf.select(cfg, "logging.server_name", default=None)
        if cfg_name:
            return str(cfg_name)
    except Exception:
        pass
    # 3. hostname
    return socket.gethostname()
```

---

## 2. 既存ファイルの修正

### `src/egosurgery/utils/experiment_manager.py` への追加

`ExperimentManager` クラスに以下を追加する。

1. **`setup()` に server_name 記録を追加**：
   - `resolve_server_name(cfg)` を呼び、実験フォルダに `server.txt` を書き出す
   - `self.server_name` として保持

2. **`log_eval_recipe(eval_recipe: dict)` メソッドを新設**：
   - `metrics.json` に `eval_recipe` キーを追加して書き出す
   - 既存の metrics がある場合はマージする

3. **`setup()` 後のフォルダに `server.txt` が生成される**こと

### `src/egosurgery/metrics/delta.py` への追加

`DeltaCalculator` クラスに以下を追加する。

1. **`InconsistentRecipeError` 例外クラスを新設**

2. **`compute_delta()` を拡張**：
   - 2 つの metrics.json から `eval_recipe` を読み込む
   - 両方に `eval_recipe` がある場合 → `recipes_match()` で照合、不一致なら `InconsistentRecipeError` を送出
   - 片方にのみ `eval_recipe` がある場合 → 警告を出して計算続行
   - server_name の不一致 → 警告のみ（例外にしない）
   - **gpu_count / effective_batch_size の不一致 → `InconsistentRecipeError` を送出**（§8.0 条件 (4)：単一 GPU と DDP 2 GPU の混在は Δ の意味を崩壊させるため、test_cfg・split 不一致と同格の致命的不整合として扱う）

### `configs/default.yaml` への追加

```yaml
logging:
  server_name: bengio  # §8.0・§14 と整合
```

### `.env.example` への追加

```bash
EGOSURGERY_SERVER_NAME=bengio
```

---

## 3. テスト

`tests/test_delta.py` に以下を追加する:

1. `test_eval_recipe_match_same`: 同一 recipe 同士で `recipes_match` が True を返す
2. `test_eval_recipe_mismatch_score_thr`: `score_thr` が異なる recipe で `recipes_match` が False
3. `test_eval_recipe_mismatch_split`: `split_train_images` が異なる recipe で False
4. `test_compute_delta_raises_on_inconsistent_recipe`: 不一致 recipe で `compute_delta` が `InconsistentRecipeError` を送出する【§15.6 の最重要テスト】
5. `test_compute_delta_warns_on_missing_recipe`: 一方に recipe が無い場合、例外ではなく警告で計算続行する
6. `test_server_name_mismatch_warns_not_raises`: server_name 違いは警告のみで例外にしない
7. `test_eval_recipe_mismatch_gpu_count`: `gpu_count` が異なる（単一 GPU vs DDP 2 GPU）recipe で `recipes_match` が False（§8.0 条件 (4)）
8. `test_eval_recipe_mismatch_effective_batch_size`: `effective_batch_size` が異なる recipe で False
9. `test_compute_delta_raises_on_gpu_count_mismatch`: gpu_count 不一致の metrics 同士で `compute_delta` が `InconsistentRecipeError` を送出する（単一 GPU と DDP 混在の検知）
10. `test_build_eval_recipe_ddp_fields`: `build_eval_recipe` が `gpu_count`・`effective_batch_size`・`lr_scaling` を含む dict を返す

`tests/test_pipeline.py` に以下を追加する:

11. `test_experiment_manager_writes_server_txt`: `setup()` 後に `server.txt` が存在し中身が空でないこと
12. `test_log_eval_recipe`: `log_eval_recipe()` 後に metrics.json に `eval_recipe` キーがあること
13. `test_log_eval_recipe_includes_gpu_count`: `log_eval_recipe()` 後の metrics.json の eval_recipe に `gpu_count` と `effective_batch_size` が含まれる

---

## 4. 完了判定

1. `from egosurgery.utils.eval_recipe import LOCKED_DOWN_TEST_CFG, PAPER_SPLIT_SIZES, build_eval_recipe` がエラーなく通る
2. `from egosurgery.utils.server_name import resolve_server_name` がエラーなく通る
3. `from egosurgery.metrics.delta import DeltaCalculator, InconsistentRecipeError` がエラーなく通る
4. `ExperimentManager.setup()` 後に実験フォルダに `server.txt` が生成される
5. `ExperimentManager.log_eval_recipe()` で metrics.json に `eval_recipe` が併記される
6. `DeltaCalculator.compute_delta()` が、異なる test_cfg や split サイズの実験間で `InconsistentRecipeError` を送出する
7. **`build_eval_recipe()` が `gpu_count`・`effective_batch_size`・`lr_scaling` を含む eval_recipe を返す**（§8.0 条件 (5)(6)）
8. **`recipes_match()` が gpu_count 不一致（単一 GPU vs DDP 2 GPU）を recipe 不一致と判定する**（§8.0 条件 (4)）
9. **`DeltaCalculator.compute_delta()` が gpu_count の異なる実験間で `InconsistentRecipeError` を送出する**
10. `pytest tests/test_delta.py tests/test_pipeline.py -v` が全テストパスする

---

## 5. この改修で触らないファイル

- `src/egosurgery/models/` 配下
- `src/egosurgery/datasets/` 配下（Part 1 で扱う）
- `src/egosurgery/engines/` 配下（Part 3 で eval_recipe を実際に書き込む処理を追加する）
