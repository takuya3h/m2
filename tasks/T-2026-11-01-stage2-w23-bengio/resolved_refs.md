# 解決された参照 — T-2026-11-01-stage2-w23-bengio

`contract.inject_verbatim` の 7 アンカーの**原文**（`context/conventions.md`、版 2d946b07a57abebc4a8f66150d6dbaf2ccd22186、契約の `conventions_rev` 2d946b07 と一致）。
機械で切り出した（各アンカーの `<a id>` から次の `<a id>` の直前まで）。**要約していない。**

<!-- 原文 conventions#prohibitions: sha256 96500b3286e7eb30b2dddb27f0e09a3337629ed741631e87e9e6c471092c3443 -->

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |


<!-- 原文 conventions#issuer_cautions: sha256 359c36a37e1dc1f0cae406cbcd010006b735425b229354fdbd73d1ec709663f9 -->

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
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。


<!-- 原文 conventions#env_p0: sha256 eb196f6425f7c39af5c15369c06a1b75227fb9e9356c98b2921ccaaea1096281 -->

<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。


<!-- 原文 conventions#folds: sha256 d2892601d90f4f8728f366f17ed3ebc4818e3b9b6e2f12d8ea3b323ea0b42f05 -->

<a id="folds"></a>
## folds

動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。

| 折り | test（3） | val（2） |
|---|---|---|
| A | 04, 05, 07 | 09, 10 |
| B | 01, 03, 14 | 02, 08 |
| C | 02, 08, 11 | 06, 12 |
| D | 06, 13, 15 | 04, 05 |
| E | 09, 10, 12 | 07, 15 |

train はその折りの test と val を除いた 10 本である。
**折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。

### 追加 6 動画

工程の注釈がある追加動画は次の 6 本である。

    17, 18, 19, 20, 21, 22

**22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
`tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。

**用途は訓練のみである。どの折りの test にも val にも現れない。**
15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。

### 規律

**選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。

出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。

### val と test の重なり

各折りの val 2 本（計 10 本）は、どれもほかの折りの test に現れる。上の表から読める対応は次のとおり。

| val の動画 | val に使う折り | test に持つ折り |
|---|---|---|
| 09, 10 | A | E |
| 02, 08 | B | C |
| 06 | C | D |
| 12 | C | E |
| 04, 05 | D | A |
| 07 | E | A |
| 15 | E | D |

**val に一度も入らないのは 01・03・11・13・14 の 5 本**である。test としては折り B に 3 本（01・03・14）、
C に 1 本（11）、D に 1 本（13）、A と E には 0 本。

val で設定・処方・構造・型・止め方を選ぶ段（両塔の学び直しと Stage 2 以降）では、次の三つを守る。

1. この重なりを prereg と報告に明記する
2. test の値を報告するときは、val に一度も入らない 5 動画だけで集計した値を副次として添える。
   各動画の値は、その動画を test に持つ折りのモデルが出す。集計の仕方は prereg に書く
3. 副次の値は、判定・関門・選定のどれにも使わない

選ぶ規則（規律の小節。その折りの val で選ぶ）は変えない。

出所: 利用者の決定 2026-10-19（契約 `T-2026-10-21-ops-taskstart-resume-folds-val` SPEC §2）、上の折りの表、
`docs/stage1/design_val_subsets.md` 223 行。

---


<!-- 原文 conventions#split: sha256 e4cb5c8fa440c7f9174dfd25c4ffb26f98f5160c92655491ded9fd6708e27b1c -->

<a id="split"></a>
## split

論文準拠 split の動画 ID は次のとおり。

- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
- val: `09`, `10`
- test: `04`, `05`, `07`

転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。


<!-- 原文 conventions#eval_recipe: sha256 222c25f38b90d5ace430c3133f14ec57b2923fc2d3c475d7b10bb85e413616bd -->

<a id="eval_recipe"></a>
## eval_recipe

転記元: `src/egosurgery/utils/eval_recipe.py`。

- `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`
- `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`
- `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`

比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため `UNKNOWN（転記元未特定）`。


<!-- 原文 conventions#det_groups: sha256 dc7200adee3b83a11999ea0a35c29e34664d5b446fa0872616258f3910df9953 -->

<a id="det_groups"></a>
## det_groups

検出の co-primary と陰性対照の集合。研究方針 v2 §7.3（2026-06-19 に EDA から事前登録。結果を見て選んだ群ではない）。

| 群 | クラス | 用途 |
|---|---|---|
| 標的群 | Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory | 検出の co-primary（標的群 AP = 5 クラスの AP の平均） |
| 陰性対照群 | Gauze、Mouth Gag、Suction Cannula、Tweezers | Δ ≈ 0 であるべき群。動いたら交絡を疑う |

- クラス名は検出塔の注釈と完全一致で照合する
- ある折りの評価集合に出現しないクラスは、その折りの群 AP から除き、除いたことを明記する。0 で埋めない
- AP rare（Skewer、Syringe）は副次指標として別に報告する

