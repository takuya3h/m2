# conventions — 逐語で渡す規約

このファイルの各節は `spec.yaml` の `contract.inject_verbatim` から
`conventions#<anchor>` の形で参照される。**要約して渡してはならない。**
CLI は実行直前にこのファイルから原文を読み、指示に差し込む。

改訂したら末尾の変更履歴に追記すること。参照側は `contract.conventions_rev` で
起票時点の commit を記録しており、差があれば検証時に差分が提示される。

---

<a id="split"></a>
## split

論文準拠 split の動画 ID は次のとおり。

- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
- val: `09`, `10`
- test: `04`, `05`, `07`

転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。

<a id="eval_recipe"></a>
## eval_recipe

転記元: `src/egosurgery/utils/eval_recipe.py`。

- `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`
- `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`
- `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`

比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため `UNKNOWN（転記元未特定）`。

<a id="frozen_source"></a>
## frozen_source

比較の三角形で認める凍結源は Relation-DETR seed42 完走 checkpoint。
同定パスは `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。
転記元: `docs/experiment_log.md` の STEP 0-2、および `configs/stage/s4_phase_baseline.yaml`。

凍結源を変更してはならない。変更が必要な場合は別 task で判断を記録し、同じ凍結源を使う比較群と分母を再構成する。checkpoint の正本 SHA-256 は `UNKNOWN（転記元未特定）`。実行時に対象ファイルから計算し、契約の解決結果へ記録する。

<a id="sigma"></a>
## sigma

sigma に関する列は 4 系統ある（backlog B-18）。

1. `{metric}_pstd` / `{metric}_sstd` — seed 間の sigma（母集団 / 標本）
2. `delta_pstd_{metric}` / `delta_sstd_{metric}` — 実験間 paired Delta の sigma
3. `sigma_source` — sigma の系統。値は paired_delta または within_run_seed_spread
4. `delta_sigma_source` — paired sigma の計算方法。値は paired または unpaired_pooled

3 と 4 は直交する（どの sigma を使ったか vs paired sigma をどう計算したか）。

### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

この既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、
決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、
`RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。

<a id="naming"></a>
## naming

実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

    {step}_{seq:03d}_{description}_seed{seed}

- `step`: `s0`〜`s9`、または `a1`〜`a7`
- `seq`: 同一 category と step 内の3桁ゼロ埋め連番
- `description`: 実験内容の短い説明
- `seed`: 乱数シード。既定42

転記元: `README.md` の「命名規則」。

---

## 変更履歴

| 日付 | commit | 変更 |
|---|---|---|
| 2026-08-03 | （このコミット） | 新規作成。アンカー 7 節を定義 |
