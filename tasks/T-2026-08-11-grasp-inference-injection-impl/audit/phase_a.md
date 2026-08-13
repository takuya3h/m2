# Phase A audit

## 環境と現在値

- branch: `feat/grasp-inference-injection-impl`
- venv python: `/home/ubuntu/slocal2/m2/.venv/bin/python`
- `.sync-pause`: 存在
- `context/conventions.md` の最新 commit: `d422b08`（契約値と一致）
- `runindex/` の最新 commit: `44697d9`（2026-08-11T08:41:54+00:00）

## 既存の注入と対照

- `runindex/experiments.csv` には `control_of` を持つ experiment が 136 件あった。
- `runindex/index.csv` には `control_of` を持つ run が 439 件あり、全件 `arm=injection`、`pairing_provenance=from_config_yaml` だった。
- signal-level の工程注入 `b2a_det2phase` は、凍結 Relation-DETR の tool-presence 15 次元を GAP 2048 次元へ連結し、2063 次元として causal TeCNO に渡す。
- legacy T1b の同一 seed 対は同じモデル構成を二 run で用い、`ctx_for_targets(..., zero_ctx=False)` では実 phase context 9 次元、`zero_ctx=True` では同形の零 9 次元を同じ `set_phase_context` 注入点へ渡す。
- T1b の ctrl/inj はモデル構成、学習対象、optimizer、学習量を共有し、入力信号だけを実値と零で切り替える。対照は「同じ run 内」ではなく、同一 seed の二 run として保存されていた。
- 工程側への入口は TeCNO の第1段入力である。新経路は既存 `b2a_det2phase` を変更せず、同じ「信号を入力へ連結する」原理の独立経路として追加できる。
- S4 の eval recipe は `task=phase`、`online_causal`、`jaccard_mode=strict`、凍結源・TeCNO 構成をキーにする。推論・注入設定は recipe の外側へ置く。

## 推論器の配置

- 採用: 凍結済み Relation-DETR GAP 2048 次元を入力とする独立枝。
- 理由: 推論器と工程 TeCNO の間に学習可能な共有表現を作らず、`inj - ctrl` を渡す信号の差として解釈しやすくするため。
- ctrl と inj は同じ推論器を同じ補助損失で学習し、ctrl だけ工程入力を同形・同サイズの零 5 次元へ置換する。
- `ctrl - A` は推論器の容量と補助学習を追加した構成との差。ただし独立枝なので、工程出力へ直接効く経路は ctrl の零信号だけである。

## 教師と損失旗

- `data/annotations/egosurgery_hts/hand_tool_seg/{train,val,test}.json` は COCO 形式で、category_id 1〜5 は左手、右手、左手の器具、右手の器具、両手の器具。
- 直接確認例: train の image id 0 は `01_1_0124.jpg`、同 image の annotation id 0 は category_id 1。
- 注釈画像数 / 注釈数: train 9356 / 32408、val 1514 / 5653、test 4107 / 14081。
- `load_loss_mask` の返却数: train 301、val 1、test 158、合計 460。
- 注釈画像数と mask 数の和は train 9657、val 1515、test 4265 で工程母集団と一致する。目録は落とさず、mask frame だけ補助損失を遮断できる。

## G1

PASS。既存の signal-level 注入と同じ原理で新しい独立経路を追加でき、既存注入の実装を変更する必要はない。

## CodeGraph

`codegraph init` は既に初期化済みだった。導入版に `codegraph watch` はなく `unknown command` となったため、変更後に `codegraph sync` と `codegraph impact` を実行する。
