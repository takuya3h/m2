# egosurgery_multitask

EgoSurgery データセット上で、手術器具検出・セグメンテーション・フェーズ認識・関係推論を
**Ego/Exo マルチタスク**で統合的に学習・評価する CV 研究プロジェクト。

---

## 設計原則

本プロジェクトは以下の 7 つの原則の上に構築されている。

1. **`src/` と `configs/` と `experiments/` を絶対に分ける** — コード・設定・実験結果の混在は再現性を壊す。
2. **すべての実験に「証拠」を残す** — 各実験フォルダには最低限 `config.yaml` / `command.sh` / `git_commit.txt` / `metrics.json` / `notes.md` を自動保存する。
3. **`data/` は Git 管理しない** — ただし `data/splits/` と `data/README.md` は Git 管理する。
4. **Phase-0 / Phase-1 の 2 フェーズ構成を構造に反映** — mask アノテーション依存のモジュールを条件付きとして分離する。
5. **S0〜S9 のステップと実験を対応づける** — 連番付き命名規則で Δ 基準点の追跡性を担保する。
6. **Ego / Exo のデータパイプラインを明示的に分離** — 推論時 Ego 単独の制約を構造で保証する。
7. **論文は最初から作る** — `paper/` は Day 1 から存在する。

---

## セットアップ

```bash
# 依存関係のインストール（開発用ツールを含む）
pip install -e ".[dev]"

# 環境変数の設定（W&B / データルート / 事前学習重み）
cp .env.example .env
# .env を編集して WANDB_API_KEY などを設定する
```

`uv` を用いる場合:

```bash
uv venv
uv pip install -e ".[dev]"
```

---

## ディレクトリ構造の概要

```
egosurgery_multitask/
├── configs/        # 設定（コードと完全分離）
├── data/           # データ（Git 管理外。splits/ と README.md のみ管理）
├── src/egosurgery/ # 実装コード
├── scripts/        # 実験起動・前処理・集計スクリプト
├── experiments/    # 実験結果（ExperimentManager が自動生成）
├── notebooks/      # 探索用ノートブック（本番実験はやらない）
├── outputs/        # 図表・レポート
├── docs/           # アイデアログ・実験ログ・読書ノート
├── paper/          # 論文（Day 1 から存在）
├── tests/          # テスト
└── tools/          # 補助ツール
```

### `configs/` の 4 軸

設定は Hydra の config group として **4 つの軸**に分解される。コマンドラインで部品を差し替えられる。

| 軸 | 内容 | 例 |
|----|------|----|
| `model/` | モデル部品（backbone / detection_head / temporal / phase_injection / relation / exo / object_token） | `backbone=dinov2_vitl14_reg` |
| `data/` | データセット定義 | `data=egosurgery_tool` |
| `train/` | 学習ステージ設定（stage_a0 〜 stage_d） | `train=stage_a1` |
| `stage/` | S0〜S9 のステップ定義 | `stage=s4_temporal` |

加えて `configs/experiment/`（アブレーション・ベンチマーク一式）と `configs/sweep/`（ハイパラ探索）を持つ。

### `src/egosurgery/` の構造

- `datasets/` — Ego / Exo / ペア / 時系列データセットと変換・サンプラ
- `models/` — `backbones/` `heads/` `temporal/` `object_token/` `feedback/` `relation/` `exo/` `losses/`
  - `feedback/` `relation/` `exo/` `object_token/` `temporal/` は仮説 H1〜H4 に対応するモジュール群
- `engines/` — ステージ別トレーナ（stage_a 〜 stage_d）・バリデータ・フック
- `metrics/` — 検出 / セグメンテーション / フェーズ / 関係 / Δ 評価
- `utils/` — seed 固定・チェックポイント・**実験管理（ExperimentManager）**
- `analysis/` — 埋め込み・失敗事例・注意マップ・ロングテール解析

### `experiments/` の 6 カテゴリ

`baselines/` `phase0/` `phase1/` `ablations/` `transfer/` `final/` の 6 つ。
個別の実験フォルダは手作業で作らず、`ExperimentManager` が実行時に自動生成する。
詳細は [`experiments/README.md`](experiments/README.md) を参照。

---

## 実験の実行方法

`Makefile` 経由でステップ単位の実験を起動する。

```bash
make s0      # S0: tool 検出ベースライン
make s2      # S2: hand
make s4      # S4: temporal
make s5      # S5: object token
make s6      # S6: bidirectional
make eval    # 評価
make delta   # Δ（基準点比較）の算出
make tables  # 論文用テーブルの書き出し
```

`make s0` は内部で `bash scripts/run_s0.sh` を呼び、`ExperimentManager` が
`experiments/baselines/s0_001_..._seed42/` を採番・生成して証拠ファイルを残す。

---

## 命名規則

実験フォルダは以下の規則で **自動採番**される（手作業で命名しない）。

```
{step}_{seq:03d}_{description}_seed{seed}
```

- `step` — S0〜S9 のステップ（`s0` 〜 `s9`）、またはアブレーション（`a1` 〜 `a7`）
- `seq` — 同一 `category` + `step` 内での 3 桁ゼロ埋め連番（`001`, `002`, ...）
- `description` — 実験内容の短い説明（例: `maskdino_bbox`）
- `seed` — 乱数シード（既定 42）

例: `s0_001_maskdino_bbox_seed42` / `s4_003_srmamba_seed42` / `a5_001_relation_seed42`

連番は `ExperimentManager` が `experiments/{category}/` 配下の既存フォルダを走査して
自動決定するため、命名のゆれや重複が構造的に発生しない。

---

## 主要ドキュメント

- [`docs/experiment_log.md`](docs/experiment_log.md) — 全実験の「仮説→実験→結果→解釈→次」記録
- [`docs/idea_log.md`](docs/idea_log.md) — アイデアログ
- [`docs/decision_log.md`](docs/decision_log.md) — 設計判断の記録
- [`docs/TODO.md`](docs/TODO.md) — TODO
