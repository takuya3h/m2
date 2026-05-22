# egosurgery_multitask — プロジェクト指示

EgoSurgery 上の術具検出・工程認識・関係推論を Ego/Exo マルチタスクで統合する
CV 研究プロジェクト。S0〜S9 の段階的実験と Δ（相互改善幅）基準点追跡が中核。

## 環境（検証済み構成・再構築しないこと）

- 仮想環境: `.venv`（uv, Python 3.11）。**コードを動かす前に必ず有効化**
  （`source .venv/bin/activate`、または `.venv/bin/python` を明示）。無ければ作成。
- torch 2.1.2+cu118（システム nvcc 11.8 と一致 → CUDA 拡張がビルド可能）。
  CUDA 利用可（RTX A6000、driver 535）。
- 導入済み: mmcv 2.1.0 / mmdet 3.3.0 / mmengine 0.10.7 /
  mamba-ssm 2.2.2 / causal-conv1d 1.4.0。
- `transformers` は **4.44.2 固定**（mamba-ssm 2.2.2 が旧 generation API を参照するため）。
- `numpy<2` 固定（torch 2.1 系の要件）。
- セットアップ手順の詳細は `README.md` の「推奨セットアップ」を参照。

## 実行規約

- import パスは `src/` 配下。`PYTHONPATH` は `.claude/settings.local.json` で
  通してあるが、明示する場合は `PYTHONPATH=src`。
- 学習エントリーポイント: `python -m egosurgery.train stage=<stage> ...`（Hydra）。
  `cfg.experiment.step` が s0/s1/s2 なら `StageATrainer`、それ以外は dummy `Trainer`。
- ステージ実験は `scripts/run_sX.sh`。スモークは環境変数 `S0_EXTRA_ARGS` で
  小構成（vit-S・少データ・少 epoch）を渡す。
- 長時間 GPU 学習は **background 実行 + Monitor 監視**で運用する。
- 実験は `experiments/baselines/` 等が空の scaffold 状態から、`ExperimentManager`
  が実行時に `{step}_{seq:03d}_{desc}_seed{seed}/` を自動生成する。

## 研究インテグリティ（厳守）

- **metrics / mAP 等の数値を絶対に捏造しない**。環境制約等で未達なら、
  「未達」「環境制約により不可」と正直に報告する。ダミー値で取り繕わない。
- Δ 基準点の汚染防止: optimizer / seed / scheduler / augmentation / batch size を
  S0〜S9 で揃える。改善主張は §10.1 に従い `|Δ| > 1σ` のときのみ行う。
- 各実験には証拠（config.yaml / command.sh / git_commit.txt / metrics.json /
  per_class_ap.json / notes.md）を必ず残す（`ExperimentManager` が自動化）。

## ドキュメント更新（必須）

- コード変更後は `README.md` に変更内容と現状を記録する。
- 実験を行ったら `docs/experiment_log.md` に「仮説→実験→結果→解釈→次」を追記する。

## ハマりどころ

- semgrep フックの誤検知: pycocotools の評価器クラス名が組み込み eval 関数と
  誤判定される → `import ... as` エイリアスで回避。`DataLoader` への pin_memory
  指摘は `# nosemgrep` で抑制済み。
- 検出の座標系: モデルは `img_size` 正方空間で予測。評価器の COCO GT は元解像度。
  予測は元座標へ逆スケールしてから評価する（`StageATrainer._rescale_to_original`）。

## .claude/ ツール（このプロジェクト用）

- スラッシュコマンド: `/run-stage` `/verify-phase` `/delta` `/exp-report`
  `/new-hypothesis` `/env-check`
- サブエージェント: `experiment-runner` `delta-analyst` `trace-debugger` `paper-writer`
- スキル: `run-experiment` `add-model-component`
- フック: `src/`・`tests/` の Python 編集時に ruff で軽量チェック

## ツール方針

- `uv` でパッケージ・仮想環境管理、`Hydra` で設定管理、`W&B` で実験追跡。
- 構造的な調査（呼び出し関係・定義位置・影響範囲）は CodeGraph MCP を優先。
