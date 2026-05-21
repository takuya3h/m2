# experiments/

全実験の結果を格納するディレクトリ。**個別の実験フォルダは手作業で作らない。**
`ExperimentManager`（`src/egosurgery/utils/experiment_manager.py`）が実験実行時に
連番採番・証拠ファイル生成を自動で行う。

---

## 6 つのカテゴリ

| カテゴリ | 用途 |
|----------|------|
| `baselines/` | 各タスクの単体ベースライン（S0 など）。Δ 計測の基準点。 |
| `phase0/`    | Phase-0 実験。mask アノテーションに依存しないモジュールのみで構成。 |
| `phase1/`    | Phase-1 実験。mask アノテーション依存モジュールを追加した構成。 |
| `ablations/` | アブレーション実験（A1〜A7）。各設計要素の寄与を切り分ける。 |
| `transfer/`  | 転移・外部データセット（PHAKIR / CholecT45 / EgoExoR）での検証。 |
| `final/`     | 論文掲載用の最終実験。 |

---

## 命名規則

```
{step}_{seq:03d}_{description}_seed{seed}
```

- `step` — ステップ識別子。S0〜S9（`s0`..`s9`）またはアブレーション（`a1`..`a7`）。
- `seq` — 同一 `category` + `step` 内での 3 桁ゼロ埋め連番。`ExperimentManager` が
  既存フォルダを走査して自動決定する。
- `description` — 実験内容の短い説明（例: `maskdino_bbox`）。
- `seed` — 乱数シード（既定 42）。

### 例

```
experiments/baselines/s0_001_maskdino_bbox_seed42/
experiments/baselines/s0_002_maskdino_bbox_seed42/   # 同じ step の 2 回目
experiments/phase1/s4_001_srmamba_seed42/
experiments/ablations/a5_001_relation_seed42/
```

---

## 各実験フォルダに自動生成されるファイル

`ExperimentManager.setup()` を呼ぶと、以下の構造が自動生成される。

```
{exp_dir}/
├── config.yaml          # Hydra の resolved config のコピー
├── command.sh           # 実行コマンドの記録（sys.argv から再構成）
├── git_commit.txt       # git rev-parse HEAD の結果
├── metrics.json         # {} で初期化、学習中に log_metrics() で更新
├── per_class_ap.json    # {} で初期化、評価時に log_per_class_ap() で更新
├── notes.md             # テンプレート付き（仮説/結果/解釈/次の行動）
├── logs/                # 学習ログ（Git 管理外）
├── checkpoints/         # モデル重み（Git 管理外）
├── predictions/         # 推論結果（Git 管理外）
└── visualizations/      # 可視化（Git 管理外）
```

| ファイル | 説明 |
|----------|------|
| `config.yaml` | その実験で実際に使われた設定。`${...}` 補間を展開済み（resolve=True）。 |
| `command.sh` | 実験を起動したコマンド。コピペで再実行できる形で保存。 |
| `git_commit.txt` | どのコード状態で出た結果かを特定する commit hash。 |
| `metrics.json` | エポック/タスクごとの主要メトリクス。論文テーブルに直結する形式。 |
| `per_class_ap.json` | クラス別 AP。ロングテール解析・付録テーブル用。 |
| `notes.md` | 「仮説→結果→解釈→次の行動」を人手で記入する実験ノート。 |

---

## Git 管理方針

| 区分 | 対象 | 理由 |
|------|------|------|
| **管理する** | `config.yaml` / `command.sh` / `git_commit.txt` / `metrics.json` / `per_class_ap.json` / `notes.md` | 軽量で、実験の「証拠」として再現性の根幹をなす。 |
| **管理しない** | `checkpoints/` / `logs/` / `predictions/` / `visualizations/` / `*.pt` / `*.pth` / `*.npy` | 大容量で、`config.yaml` + `git_commit.txt` から再生成可能。 |

ルート `.gitignore` の `experiments/**/...` ルールでこの区別を実現している。

---

## `ExperimentManager` の使い方

```python
from egosurgery.utils.experiment_manager import ExperimentManager

manager = ExperimentManager(
    base_dir="experiments",
    category="baselines",      # baselines / phase0 / phase1 / ablations / transfer / final
    step="s0",                 # s0..s9 / a1..a7
    description="maskdino_bbox",
    seed=42,
)

# フォルダを採番・生成し、証拠ファイルを初期化する。
exp_dir = manager.setup()
# -> experiments/baselines/s0_001_maskdino_bbox_seed42/

# Hydra の resolved config を保存する。
manager.save_config(cfg)

# 学習中・評価時にメトリクスを記録する（それぞれ上書き保存）。
manager.log_metrics({"epoch": 10, "tool_mAP": 0.42})
manager.log_per_class_ap({"forceps": 0.55, "scissors": 0.31})
```

`setup(cfg)` のように config を渡せば、フォルダ生成と同時に `config.yaml` も保存される。
