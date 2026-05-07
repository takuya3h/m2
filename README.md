# Research Template

深層学習・コンピュータビジョン研究用プロジェクトテンプレート。

## 目的

このテンプレートは、以下を実現するために設計されています。

- **実験の再現性**：設定ファイルと Git commit を紐付けて再現可能な実験管理
- **実験条件と実験結果の分離**：`configs/` と `experiments/` を明確に分ける
- **論文執筆へのスムーズな接続**：`outputs/` に論文用図表を集約
- **失敗分析の蓄積**：`experiments/*/notes.md` に仮説・結果・解釈を記録
- **共同研究における可読性**：統一された命名規則とディレクトリ構造
- **3か月後の自分が実験を追跡できる状態の維持**：メタ情報（config, command, commit）を実験フォルダに保存

## 設計思想

- コード、設定、データ、実験結果、論文成果物を混ぜない
- 実験は必ず設定ファイル（`configs/`）から起動する
- 実験結果には、設定・実行コマンド・Git commit・メトリクス・メモを残す
- データ本体や巨大なチェックポイントは Git 管理しない
- データ分割ファイル（`data/splits/`）は再現性に関わるため Git 管理対象にする
- ノートブックは探索・分析用であり、本番実験の実行場所にしない
- 論文用の図表は `outputs/` に集約する
- 各実験は「仮説 → 実験 → 結果 → 解釈 → 次の行動」で管理する

## ディレクトリ構成

| ディレクトリ | 役割 |
|---|---|
| `configs/` | 実験設定ファイル。`data/`, `model/`, `experiment/`, `sweep/` に分類 |
| `data/` | データ本体および分割情報。本体は Git 管理しない。`splits/` のみ管理 |
| `src/` | 再利用可能な研究コード。パッケージとして `pip install -e .` で使う |
| `scripts/` | 実験作成・学習・評価など実行用シェル/Pythonスクリプト |
| `notebooks/` | 探索・可視化・失敗分析用ノートブック |
| `experiments/` | 各実験の設定・ログ・チェックポイント・メモの保存先 |
| `outputs/` | 論文・発表に使う最終的な図・表・レポート |
| `docs/` | アイデアログ・実験ログ・TODO・読書メモ・会議メモ |
| `paper/` | 論文執筆用 LaTeX ファイル |
| `tests/` | ユニットテスト |
| `tools/` | モデル変換・プロファイリングなどユーティリティツール |

## 実験ディレクトリの命名規則

```
YYYY-MM-DD_NNN_short-description
```

| 要素 | 説明 |
|---|---|
| `YYYY-MM-DD` | 実験作成日 |
| `NNN` | その日の実験連番（3桁ゼロ埋め） |
| `short-description` | 英小文字・数字・ハイフン・アンダースコアのみ |

例：

```
experiments/2026-05-07_001_baseline_resnet50
experiments/2026-05-07_002_resnet50_randaugment
experiments/2026-05-08_001_vit_b16_aug_ablation
```

## 実験フォルダの構成

各実験フォルダには以下が保存されます。

```
experiments/YYYY-MM-DD_NNN_short-description/
├── config.yaml          # 実験設定（configのコピー）
├── command.sh           # 実行コマンド
├── git_commit.txt       # 実験時点の Git commit hash
├── metrics.json         # 評価メトリクス
├── logs/                # 学習・評価ログ（Git管理外）
├── checkpoints/         # モデルチェックポイント（Git管理外）
├── predictions/         # 推論結果（Git管理外）
├── visualizations/      # 可視化結果（Git管理外）
└── notes.md             # 仮説・結果・解釈・次の行動
```

## 実験の開始方法

### 1. 環境構築

```bash
pip install -e .
```

### 2. 実験フォルダの作成

```bash
python scripts/create_experiment.py --name baseline_resnet50 --config configs/experiment/baseline.yaml
```

出力例：

```
Created experiment directory: experiments/2026-05-07_001_baseline_resnet50
```

### 3. 学習の実行

```bash
bash scripts/train.sh experiments/2026-05-07_001_baseline_resnet50
```

### 4. 評価の実行

```bash
bash scripts/eval.sh experiments/2026-05-07_001_baseline_resnet50
```
