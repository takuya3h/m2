# 実行ホストに残る退避物の棚卸し（2026-08-09）

## 背景

別ホストとの差ではなく、`origin/phase0` から新規追加された
`runindex/runs/*.json` を機械的に抽出して確認した。新規 record は 35 件であり、
内訳は `excluded=true` の退避物 34 件と、非除外の配線検証 1 件であった。

| 状態 | 件数 |
|---|---:|
| 起票時の `index.csv` | 749 |
| 現在の `index.csv` | 784 |
| 新規 record | 35 |
| うち退避物 | 34 |
| うち非除外の配線検証 | 1 |

退避物 34 件はこのホストのディスク上に実在する。全件が索引では除外済みであり、
解析対象には入っていない。8 親ディレクトリすべてで Git 追跡ファイル数は 0 件、
かつ `.gitignore` の明示規則に一致した。

## 一覧

| 経路 | run 数 | 追跡 | 最終更新 (UTC) | 索引での扱い |
|---|---:|---|---|---|
| `experiments/baselines/_aborted_codetr_no_config` | 3 | 未追跡 | 2026-05-26 04:32:40 | `excluded=true`, `aborted_run` |
| `experiments/baselines/_aborted_s0_cuda_visible_misconfig` | 1 | 未追跡 | 2026-05-25 11:28:59 | `excluded=true`, `aborted_run` |
| `experiments/baselines/_failed_num_workers_zero` | 5 | 未追跡 | 2026-05-25 04:40:43 | `excluded=true`, `failed_run` |
| `experiments/baselines/_smoke_e3` | 1 | 未追跡 | 2026-05-25 15:58:26 | `excluded=true`, `smoke_test` |
| `experiments/baselines/_smoke_prior_simplehead` | 6 | 未追跡 | 2026-05-25 04:34:55 | `excluded=true`, `smoke_test` |
| `experiments/baselines/_smoke_v2_part3` | 6 | 未追跡 | 2026-05-25 08:03:35 | `excluded=true`, `smoke_test` |
| `experiments/phase0/_pre_redo_s0_smoke` | 6 | 未追跡 | 2026-05-25 11:29:35 | `excluded=true`, `smoke_test` |
| `experiments/phase0/_prior_no_eval_recipe` | 6 | 未追跡 | 2026-05-25 07:16:59 | `excluded=true`, `superseded` |
| **合計** | **34** | **全件未追跡** | — | **全件除外済み** |

## 由来

- `.gitignore` はこれらを「S0 やり直しの過程で生まれたローカル証跡」とし、
  容量上の理由から Git 履歴へ載せず、再現性検証・監査用に保持すると記録している。
- `_aborted_codetr_no_config` は Co-DETR config 不在で `setup()` に失敗した旧
  `s0_007`〜`s0_009` であることが `.gitignore` に記録されている。
- `_smoke_e3` は手動 launcher の動作検証用で、検証成功後に本番を起動したことが
  `.gitignore` に記録されている。
- `_aborted_s0_cuda_visible_misconfig`、`_failed_num_workers_zero`、
  `_smoke_prior_simplehead`、`_smoke_v2_part3`、`_pre_redo_s0_smoke`、
  `_prior_no_eval_recipe` の詳細な生成操作は、今回確認した代表 `notes.md` だけでは
  確定できない。由来の詳細は `UNKNOWN` とする。
- 索引上の分類内訳は `smoke_test` 19 件、`superseded` 6 件、
  `failed_run` 5 件、`aborted_run` 4 件で、合計 34 件である。

## 影響

このホストで収穫器を回すたびに、これらの未追跡ディレクトリが走査対象になる。
同じ commit でも退避物の有無によって索引の行数がホスト間で一致せず、生成済み索引を
統合すると、このホスト固有のディスク状態が全ホストへ配布される。

## 処置の案

移動・削除・改名は行っていない。以下は選択肢であり、本 task では選ばない。

| 案 | 内容 | 影響 |
|---|---|---|
| A | 走査対象を Git 追跡下の run に限定する | ホスト間の再現性は高まるが、未追跡の退避証跡が索引から消える |
| B | 退避ディレクトリ一覧を規約化し、全ホストで同一に保持する | 退避証跡を索引へ残せるが、同期・容量・運用負荷が大きい |
| C | 索引をホスト依存の生成物とし、退避物を持たない1ホストを正本に定める | 実装変更は小さいが、正本ホストの決定と再生成手順の厳格な運用が必要 |
| D | 収穫器へ「退避物を索引化するか」の明示オプションを追加する | 目的別に切り替えられるが、モード差による索引の取り違え防止が必要 |

どの案も採用していない。選択は利用者の判断領域であり、退避物は現位置に保持している。
