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

凍結源を変更してはならない。変更が必要な場合は別 task で判断を記録し、同じ凍結源を使う比較群と分母を再構成する。

checkpoint の正本 SHA-256 は次のとおり。

    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824

サイズは 195421066 bytes。転記元は 2026-08-06 に実施した11ホストの ssh 一括監査であり、
11 ホスト全てで SHA-256 が一致し、mtime もナノ秒まで同一であった。
`third_party/` は git の追跡対象外だが、実体はホスト間で同期されている。

`verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は
`no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。
skip する経路は設けない。

### 検査の適用範囲

凍結源の照合は、凍結源を使う契約に対して適用される。実行直前の検査では
`meta.kind` が `exp` の契約に対して実施し、それ以外は適用対象外として
未実施と記録する。

**適用対象となった場合に、照合を省略する経路は存在しない。**
照合に失敗した場合は実行を中止し、人へ差し戻す。

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

### 判定規約の表記

判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。
縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない
（backlog B-33 と同型の事故）。

    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号
    誤: 縦線で delta を囲む記法

同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。

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
| 2026-08-03 | 8b17c4d | 新規作成。アンカー 7 節を定義 |
| 2026-08-06 | cac8147 | frozen_source の SHA-256 正本値を確定。sigma 節に判定規約の abs() 表記ルールを追加 |
| 2026-08-07 | 290da51 | frozen_source に「検査の適用範囲」を追記。実行直前検査での適用条件と、適用時に省略経路が無いことを明文化 |
<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。
