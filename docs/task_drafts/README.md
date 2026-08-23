# docs/task_drafts — 起票前の TASK 契約ドラフト（2026-08-22）

`docs/research_review_and_next_plan_2026-08-22.md` §6 の実験を、
`tasks/_templates/exp/spec.yaml` の様式でそのまま起票できる形に落としたもの。

**これは起票済みの task ではない。** `tasks/` 配下には置いていないので
`make taskindex` / `make spec-check` の対象にならない。
起票するときは次の手順を踏むこと。

1. `task_id` の日付を起票日に直し、`tasks/<task_id>/spec.yaml` へ置く。
2. `meta.created_from.runindex_commit` と `counts` を起票時点の実測値に更新する
   （本ドラフト作成時点: runindex commit `7918b5dd` /
   index 1,177 行 / experiments 213 行 / verdicts 1,038 行。ヘッダ行を除く実数）。
3. `contract.conventions_rev` を起票時点の `context/conventions.md` の commit に更新する
   （本ドラフト作成時点: `d422b087`）。
4. `prereg.commit` は **走らせる前に** 事前登録を commit した hash で埋める。
5. `make spec-check` → `make task-verify` を通す。

## 検証状況（本セッションで実測）

3 本とも **プロジェクトの検証器 `tools/validate_task.py` の L1 / L2 を findings 0 で通る**
ことを確認済み（`meta.task_id` を仮のディレクトリ名に差し替えて実行）。

```
Em1_oracle_upper_bound_test.spec.yaml         L1=0 L2=0
E9_prune_high_entropy_tools.spec.yaml         L1=0 L2=0
E1_causal_denoise.spec.yaml                   L1=0 L2=0
```

検証で直した点（起票時に同じ轍を踏まないための記録）:

- `inputs.denominator.ref` は **`experiments.csv` の `experiment_id` 列の完全形**が要る
  （`exp:transfer/b2a_regiononly_pred/b2a_regiononly_pred@val~relation_detr_seed42`）。
- `inputs.frozen_source.ref` は **`run:<group>/<run_name>` の 2 段**でなければならない。
- `intent` / `prereg` の本文に **縦棒（表の区切り文字）と数値リテラルを書いてはいけない**。
  数値は参照で書く（`§3.2` のような節番号も小数と解釈されるので、節の名前で書く）。
- `inputs.caches` は **波括弧展開が効かない**。1 行 1 パスで書く。
- `meta.created_from.counts` は **ヘッダ行を除いた実数**（`wc -l` の値から 1 を引く）。

## ドラフト一覧

| ファイル | 対応する実験 | 何を決めるか |
|---|---|---|
| `Em1_oracle_upper_bound_test.spec.yaml` | **E−1** | val で見えた「オラクル上限」が本番 TeCNO の test でも成立するか（再学習なし・約 30 分） |
| `E9_prune_high_entropy_tools.spec.yaml` | **E9（主路）** | 工程を弁別しない術具を落とすと分類（macro-F1）が改善するか |
| `E1_causal_denoise.spec.yaml` | **E1（反証テスト）** | 検出信号の因果デノイズが分節指標を改善するか。**プロキシは「改善しない」と予測している** |

## 実行順

**E−1 → E9 → E1 → E8（LOVO）**。

**E9 が主路である**理由:
- プロキシで最も頑健な介入（6 凍結源で 6/6 正・効果量 +1.13〜+2.13pt）。
- **時間方向の受容野を TeCNO 相当（K=128）まで与えても利得が残る**（macro-F1 +3.08pt・2.24σ）。
- **既存 CLI（`--drop-gap --mask-tool-dims`）だけで動く**のでコード変更が要らない。

**E1 は反証テストである**理由:
- per-frame 分類器に **8 フレームの文脈を与えるだけで edit 利得が +9.11 → +0.008 に落ちる**。
  TeCNO 相当の K=128 でも +2.83（1.09σ）で有意でない。
- **時系列モデルが自力でちらつきを吸収する**ため、入力側デノイズは冗長になる公算が大きい。
- **「効かないことを確かめて経路を閉じる」ために回す。** 予測が外れて効いた場合は、
  工程モデルの実効受容野が想定より狭いことを意味する。

## 共通の注意（報告書の実測から）

- **主終点を目的で分ける**: 術具除去 → `macro-F1`（accuracy は非劣化条件）、
  デノイズ → `edit` / `seg-F1@50`。
- **`--drop-gap` を使う**。GAP は動画 ID を 99.8% 識別する「動画指紋」で、
  15 次元 presence に足すと有意に害になる。
- **val 単独の結果を成果として報告しない**。test を必ず含める。
  報告書自身が 7 回、単一 split・選択の仕方・凍結源 1 本・プロキシの構造で見た所見に覆されている。
- **効果量の期待値を事前登録に書く**（除去: macro-F1 が主・LOVO では acc +1.1〜+2.1pt、
  標準 split では macro-F1 val +6.4pt / test +1.8pt で accuracy は横ばい）。
  デノイズは **「+9.11 を再現する」と書いてはいけない**（凍結源 seed42 固有の上振れであり、
  かつ受容野を与えると有意に検出できなくなる）。
- **しきい値・k・腕を結果を見てから選ばない**。事前に固定し、掃引は感度分析として別に報告する。
