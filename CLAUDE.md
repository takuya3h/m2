# egosurgery_multitask — プロジェクト指示

EgoSurgery 上の術具検出と工程認識のあいだの**方向性条件付けと相互改善**を測る
CV 研究プロジェクト。設計は**二塔・界面分離型**である。各タスクが自前の最良モデル（**塔**）を
持ち、自分のラベルだけで学習して凍結する。結合は塔と塔のあいだの小さな学習モジュール（**界面**）
だけで行い、**比較で変えるのは界面の入力だけ**にする。
段階は Stage 0（土台整備）から Stage 5（拡張）、関門は G0・G1・G1.5・G2・G3・G4。
**現在地は Stage 0 の起票前である。**

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
- ステージ実験は `scripts/run_sX.sh`。スモークは環境変数 `S0_EXTRA_ARGS` で <!-- docs-check: ignore-line -->
  小構成（vit-S・少データ・少 epoch）を渡す。
- 長時間 GPU 学習は **background 実行 + Monitor 監視**で運用する。
- 実験は `experiments/baselines/` 等が空の scaffold 状態から、`ExperimentManager`
  が実行時に実験フォルダを自動生成する。**腕を区別する軸は、方向（なし / 検出から工程 /
  工程から検出 / 双方向）・参照入力段（空 / 予測 / 正解 / 正解と予測の和）・
  学習範囲（W1 入力適合層のみ / W2 末端ブロックまで / W3 受け取り塔全体）の三つである。**
  **上限として使えるのは参照入力段の最後の段だけ**（旧来の「上限」という語は廃止した）。
  旧規則の `{step}_{seq:03d}_{desc}_seed{seed}` は撤回されたが、
  **既存の実験フォルダ名は当時のまま**である（過去の記録は書き換えない）。

## 研究インテグリティ（厳守）

- **metrics / mAP 等の数値を絶対に捏造しない**。環境制約等で未達なら、
  「未達」「環境制約により不可」と正直に報告する。ダミー値で取り繕わない。
- **受け取り手を全腕で揃える**: 塔と界面の型・容量・水準・スケジュール・種を同一にし、
  **変えるのは界面の入力だけ**にする。比較したい量以外を動かさない。
- **判定の規則**: 評価は動画単位の五分割と五つの種。**判定単位は動画で十五個の対の差**を得る。
  主判定は**折りをクラスタとするブロック・ブートストラップの信頼区間が零を含まないこと**。
  同一折りの三動画は同じモデルで評価されるため独立ではなく、**クラスタは折りに取る**。
- **主判定は一つだけ**置く。確認的な腕は事前に列挙し、族内で **Holm 補正**を当てる。
- **折り単位の全数同符号は主張に使わない**（五分割では符号検定の最小の値が原理的に有意へ届かない）。
  記述統計としてのみ併記する。
- 指標は、工程が **macro Jaccard**（同方向要件として frame accuracy を併記）、
  検出が **overall mAP と標的群 AP の二本立て**（陰性対照群を添える）。
- 効果量は**差そのもの**と、**分母の折り間の散らばりで割った値**の両方を併記する。
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

- スラッシュコマンド（8）: `/run-stage` `/verify-phase` `/delta` `/exp-report`
  `/new-hypothesis` `/env-check` `/log` `/promote-to-master`
- サブエージェント（5）: `experiment-runner` `delta-analyst` `trace-debugger`
  `paper-writer` `notion-archivist`
- スキル（4）: **`task`（TASK 契約の実行。この手順が中心である。Claude Code は
  `/task <task_id>`、Codex は `$task` か `.claude/skills/task/SKILL.md` を読ませる）**
  `run-experiment` `add-model-component` `avoid-past-failures`
- フック: `src/`・`tests/` の Python 編集時に ruff で軽量チェック

## ツール方針

- `uv` でパッケージ・仮想環境管理、`Hydra` で設定管理、`W&B` で**必ず**全ての実験を追跡。
- **認証・追跡の起点**: 実験前に `source scripts/load_env.sh`（暗号化 `.env.gpg` を gpg 復号して env にロード）。
  これで W&B（`egosurgery.utils.tracking` 配線済）と Notion 認証が揃い**自動追跡・自動記録**が有効化。
  平文 `.env` は **絶対に commit しない**（公開リポ）。秘密の運用は `docs/secrets_and_tracking.md`。
  新規 trainer を書くときは `tracking.init/log/finish` を必ず配線する（無認証なら no-op）。
- 構造的な調査（呼び出し関係・定義位置・影響範囲）は CodeGraph MCP を優先。
## Notion 連携（運用ハブ駆動・コンテキスト削減）

研究運用は Notion「**M2研究運用ハブ**」を入口にする。**マスターの「M2研究計画」（長文）は毎回読まない**。
ID レジストリは `configs/notion.yaml`（非秘密）、認証 `NOTION_API_KEY`/`NOTION_DB_ID` は `.env`。詳細は `docs/notion_integration.md`。

**読む（MCP・コンテキスト削減）**: セッションで必要なときだけ、次の順で**スライスのみ**取得する:
1. `pages.current_state`「現在の研究状態」（最優先・小）を MCP fetch。
2. 該当 step の構造化行を `scripts/notion_context_pack.py --step <S0..S9/B>` で抽出
   （意思決定/失敗知見/プロンプト/手順書の関連行のみ）。
3. 「M2研究計画」は**該当 §セクションだけ** MCP fetch（全文を渡さない）。
「研究計画に基づいて答えて」と指示されたら、上記でハブ→該当計画スライスを**必ず**参照して答える。

**書く（自動記録・運用ループ §1-6）**:
- 実験完了 → 実験Run台帳に自動投稿（`notion_logger.log_experiment_to_notion` 配線済 / バックフィルは `scripts/post_experiments_to_notion.py`）。
- 方針変更 → `egosurgery.utils.notion_ops.log_decision(...)`（意思決定ログ）。
- 再発防止の失敗 → `notion_ops.log_lesson(...)`（失敗知見・教訓）。
- 再利用プロンプト → `notion_ops.save_prompt(...)`（プロンプトライブラリ）。
- いずれも `NOTION_API_KEY` 未設定なら no-op（研究フローを止めない）。Name 冪等（同名は update）。
- 高レベル計画本文への反映は週次/マイルストーン単位（毎回はしない）。
- `tasks/lessons.md` に記録した教訓は、再発防止性があれば `notion_ops.log_lesson` でハブにも上げる。
