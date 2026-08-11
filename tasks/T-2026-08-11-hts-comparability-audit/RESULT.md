# RESULT — 補助信号を足す実験が既存の基準点と比較できるかを測る

**task_id:** `T-2026-08-11-hts-comparability-audit`  **kind:** `analysis`
**実行ホスト:** `lecun`（`resolve_server_name()` の実測値）  **分岐:** `feat/hts-comparability-audit`
**status:** pass（10 問すべてに出典・実測値・UNKNOWN のいずれかが対応した）

---

## 0. 冒頭に置く事項（`escalate_if` 該当）

契約の `escalate_if` に「注釈の欠落が特定のクラスや工程に偏っており、補助信号の効果と
交絡すると判明した場合」がある。**該当する。ただし起票者が恐れた向きとは違う。**

補助注釈が無い 460 枚（全体の 2.980% = 460/15,437）の偏りを実測した結果:

| 偏りの対象 | 実測 | 全体基準 2.98% との比 |
|---|---:|---:|
| **希少工程 irrigation** | 15/177 = **8.47%** | 2.8 倍 |
| **希少工程 anesthesia** | 34/499 = **6.81%** | 2.3 倍 |
| 希少工程 dressing | 6/119 = 5.04% | 1.7 倍 |
| 希少工程 disinfection | 1/11 = 9.09%（n=11 と小さい） | 3.1 倍 |
| **Skewer（起票者が恐れたクラス）** | **0/343 = 0.00%** | **0 倍** |
| Mouth Gag（同上） | 164/5,982 = 2.74% | 0.9 倍 |
| design 工程（Skewer が 99.7% 集中する工程） | **0/378 = 0.00%** | 0 倍 |

**補助教師が最も欠けているのは、工程認識が最も弱い希少工程である。**
補助信号は「効いてほしい場所で最も薄い」構造になっている。効果が出なかった場合に
「補助信号が無効」なのか「その工程に補助教師が無かった」なのかを分離できない。

一方、**起票者が交絡源として名指しした Skewer は 1 枚も除外されていない。**
Skewer は design 工程に 99.7% 集中する稀少クラスであり、design 工程の除外率も 0.00% で整合する。

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]` の原文

`context/conventions.md`（現在値 `d422b08`、`spec.yaml` の `conventions_rev` と一致・置換不要）
の `<a id="prohibitions"></a>` 節の原文をそのまま引く。

> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### `inputs.sigma_policy`（省略）→ `context/conventions.md#sigma` の既定を継承

原文をそのまま引く。

> ### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）
>
>     series: pstd
>     sigma_source: paired_delta
>     delta_sigma_source: paired
>
> この既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、
> 決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、
> `RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。

判定規約も同節の原文どおり `abs(delta) / sigma >= 1 かつ 全 seed 同符号` を用いた。

### その他の参照

| 参照 | 解決先 | 実測値 |
|---|---|---|
| `runindex` の版 | `git log -1 -- runindex/` | `44697d9` 2026-08-11T08:41:54+00:00。**起票時の記載 `44697d9` と一致** |
| `created_from.counts` | 実ファイルの行数 | index 751 / experiments 207 / verdicts 1038。**起票時の記載と 3 つとも一致** |
| `inputs.denominator.ref` | — | spec に記載なし（Phase C で `control_of` 集計から分母一覧を実測した） |
| `inputs.frozen_source.ref` | — | spec に記載なし（索引の `frozen_source_tag` を実測した） |

---

## 2. 10 問への回答

| # | 問い | 回答 | 出典 / 実測 |
|---|---|---|---|
| Q1 | 領域注釈の分割は術具の 10 対 2 対 3 と一致するか | **一致する。** 現行 canonical の 3 種すべてで train 13 セグメント（動画 01,02,03,06,08,11,12,13,14,15）/ val 3（09,10）/ test 6（04,05,07）。工程 manifest の clip 数 13/3/6 とも一致 | **実測**（`AUD/hts_entity.txt` §3）。既存監査 `hts_coverage_2026-07-30` 結論 5 が指摘した壊れた `04_handtool/coco_splits_5cls`（val/test 入替・動画 03,14 脱落）は、07-31 の再構築で**使われていない** |
| Q2 | 領域注釈のフレーム集合は術具・工程とどう重なるか | 対 術具 15,437: hand_seg **99.74%** / tool_seg **96.96%** / hand_tool_seg **97.02%**。逆方向は術具 split 外に hand 4,035 / tool 3,532 / hand-tool 3,420 枚（`extra.json`、術具集合との交差 0）。工程 17,233 に対しては HTS 母集団外が 1,796 枚 | **実測**（`AUD/hts_entity.txt` §2）。工程側の 1,796 は `hts_coverage_2026-07-30` 結論 3 |
| Q3 | 分割を跨ぐフレームの重複は無いか | **無い。** 3 種すべてで train∩val = train∩test = val∩test = **0**。セグメント単位でも 0 | **実測**（`AUD/hts_entity.txt` §3）。**陽性対照つき**（val の識別子 `10_1_1434` を train へ 1 件注入 → ちょうど 1 件検出） |
| Q4 | 領域注釈のクラス定義は術具 15 と手 4 にどう対応するか | **直交する。** hand_tool_seg の 5 クラスは `First Person's Left Hand` / `First Person's Right Hand` / `Left Hand Tool` / `Right Hand Tool` / `Two Hands Tool` で、**術具の同定ではなく手役割**。hand_seg 4 クラスは `First/Other Person's Left/Right Hand` で既存の手 bbox 4 クラスと対応。tool_seg は 31 クラスで、術具 15 の上位集合だが `Mouth Gag` と `Suture, Suture Needle` の annotation が 0 件 | **実測**（`AUD/hts_entity.txt` §1）+ 既存監査 `hts_next6` §4（VBS(15)→V14(14) は一意写像、Mouth Gag 5,985 ann は写像先なし、V14 採用は box 差し替えで I4 に抵触） |
| Q5 | 注釈が無い 460 フレームはどこに偏るか | **§0 のとおり。** クラス偏りは弱い（最大 Syringe 5.67%、Skewer は 0.00%）。**工程偏りが本体**で、希少工程に 2〜3 倍。除外 460 の工程ラベル欠落は 0 件。術具の箱が 1 つも無いフレームは 460 中 **6 枚**のみ | **実測**（`AUD/hts_entity.txt` §4）。工程集中度は既存 `annotations_eda` §5.2（Skewer→design 99.7%） |
| Q6 | 把持関係のラベルは実在するか | **実在する。** hand_tool_seg そのものが把持関係の GT（どの手が持つ器具か）。train 32,408 / val 5,653 / test 14,081 annotation。疑似ラベル `data/annotations/pseudo_labels/` は**ディレクトリごと存在しない**（07-29 監査時は空の .gitkeep があった＝以後削除された） | **実測**。導出規則の発明は不要（GT が実在するため） |
| Q7 | 既存の 4 つの基準点のうちどれと比較できるか | 工程側 2 つは**可**（条件 3 つつき）。検出側 2 つは**条件付き可**（paired 分母の前例が索引に無い） | **実測**（`AUD/comparability.md` §1・§6） |
| Q8 | 補助課題を足すと学習の母集団はどう変わるか | **設計次第で変わる/変わらない。** 工程学習の母集団は `phase_manifest` の実測で 9,657/1,515/4,265 = **15,437**（検出と完全同一）。補助損失をフレーム単位フラグで無効化すれば母集団は 15,437 のまま。manifest から落とすと 14,977 に縮み全基準点と揃わなくなる。**現時点で `load_loss_mask` に呼び出し元は無く、主課題への波及はゼロ** | **実測**（`AUD/comparability.md` §4）。実装追跡: `src/` と `configs/` で HTS を参照するのは `loss_mask.py` のみ |
| Q9 | 補助課題の容量増を基準点に織り込む必要があるか | **工程側は要る。検出側は必須でない。** neck 追加の前例を seed 対応で実測: 工程 paired Δ = **+0.017432 / 4.850σ / 全 seed 同符号 True**（規約を満たす）、検出 paired Δ = **+0.004404 / 1.221σ / 同符号 False**（規約を満たさない） | **実測**（`AUD/comparability.md` §2） |
| Q10 | 把持関係の推論は工程側の推論手順の制約に反しないか | **反しない設計が可能で、検証手段も既存にある。** 工程側は `online_causal` + Jaccard `strict` で固定（`s4_phase*` 64 run すべて `e98ffddee042`）。`tests/test_tecno.py::test_tecno_is_causal` が「未来入力を差し替えて過去出力が不変」を検証する構造テストで、`(B, C, T)` の時系列ヘッドなら**中身に依らず流用できる** | **実測**（`AUD/comparability.md` §5） |

---

## 3. 「補助信号を足す以外は同一」が成立する条件と、成立しない条件

### 成立する（工程側・主課題）

`phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`
（accuracy 0.8973015、pstd 0.0059171、seeds 42/123/456、17 run、**119 回の分母実績**）
および `_neck` 版（accuracy 0.9141914、pstd 0.0014259）との比較は、次の 3 条件で成立する。

1. **凍結源を `relation_detr_seed42` に固定する。** 索引の `frozen_source_tag` が
   基準点と一致する必要がある（実測: 両基準点とも `relation_detr_seed42`）。
2. **工程側 `test_cfg` の時系列ヘッド構成キーを変えない。**
   `temporal_head` / `num_stages` / `num_layers` / `num_f_maps` / `backbone` /
   `inference_protocol` / `jaccard_mode` / `task` の 8 キーが実効比較の対象である。
3. **補助損失をフレーム単位フラグで無効化し、manifest を縮めない。**

### 成立しない（そのままでは）

| 揃わないもの | 何が起きるか | 解き方 |
|---|---|---|
| **共有部分の容量** | 補助ヘッドの追加は neck 追加と同型の容量増。工程側の前例は容量増だけで **4.850σ** 動いた。Δ が補助信号の効果か容量増かを分離できない | **基準点の取り直しではなく、容量一致対照で解ける。** 「補助ヘッドはあるが補助教師を与えない」腕を 1 本足す |
| **評価レシピ（条件 2 を崩した場合）** | `recipes_match` が False → `DeltaCalculator` が `InconsistentRecipeError` を送出。**統計以前に計算が拒否される** | **設計側で回避する。** 補助ヘッドを時系列ヘッド構成の外側に置く |
| **学習の母集団（設計 (b) を採った場合）** | 母集団が 14,977 に縮み、既存の全基準点（15,437）と揃わなくなる | **設計側で回避する。** フレーム単位フラグ方式（設計 (a)）を採る |
| **補助教師の工程分布** | §0 の偏り。希少工程で補助教師が 2〜3 倍薄い | **どちらでも解けない。** 効果を工程別に分解して報告し、希少工程の結論は保留するしかない |

### 検出側（従）は条件付き

凍結源・評価条件・母集団は揃えられるが、**S0-frozen は `control_of` の分母として
索引に 0 回しか現れない。** 既存の検出 Δ は同一 run 内の inj − ctrl（paired）で
測られており、S0-frozen との比較は **unpaired の絶対値比較**という前例の無い使い方になる。

---

## 4. 工程側と検出側それぞれ、比較できる基準点

| 主/従 | 基準点 | 主指標 | 値 ± pstd | 比較可否 |
|---|---|---|---|---|
| **主（工程）** | `frozen_tecno_phase_baseline@val~relation_detr_seed42` | accuracy | **0.8973015 ± 0.0059171** | **可**。neck 無しの補助信号モデルの分母 |
| **主（工程）** | `frozen_tecno_phase_baseline_neck@val~relation_detr_seed42` | accuracy | **0.9141914 ± 0.0014259** | **可**。neck 有りの補助信号モデルの分母 |
| **従（検出）** | `baselines/s0_frozen/relationdetr_s0frozen_cocohead@val` | mAP | **0.7051403 ± 0.0042154** | **条件付き可**。NMS-free 系統で評価すること。paired 分母の前例なし |
| **従（検出）** | `baselines/s0_frozen/relationdetr_s0frozen_neck_cocohead@val` | mAP | **0.7095447 ± 0.0073983** | **条件付き可**。neck 追加自体が有意でない（1.221σ・符号不一致）ため、neck 有無の選択は検出側では Δ に影響しにくい |

検出側は `NMS_FREE_TEST_CFG`（`score_thr=0.0` / `nms_pre=null` / `nms_iou=null` /
`max_per_img=300`）で記録されている。実装のコメントに、比較の三角形の検出ヘッドへ
locked-down の NMS@0.6 を適用すると **−4.5pt mAP** になる実測が残っている。

---

## 5. 起票者の推測のうち、実測で裏づけられたもの・否定されたもの

### 裏づけられたもの

| 推測 | 実測 |
|---|---|
| 想定した 5 経路に既存監査がある | **5 経路すべて実在**（想定 → 実体の差 0 件） |
| 術具側の分割の 460 フレームに注釈が無い | **合計 460 と完全一致**（train 301 / val 1 / test 158）。しかも「術具 split にあり hand_tool_seg 注釈が無い」集合と**差 0 で一致** |
| 術具の分割は 9,657 / 1,515 / 4,265 | **一致**。工程 manifest も同じ 15,437 |
| 工程側は `online_causal` / `strict` でロック | **一致**。`s4_phase*` 64 run すべて `e98ffddee042` |
| 検出側の評価条件が 2 系統に分かれる | **一致**。`LOCKED_DOWN_TEST_CFG` と `NMS_FREE_TEST_CFG` が定義され、S0-frozen は後者 |
| neck の前例は工程側で 1σ を超えた | **一致し、さらに強い**。4.850σ・全 seed 同符号 |

### 否定されたもの

| 推測 | 実測 | 影響 |
|---|---|---|
| **「`hand_tool_seg` の生成経路は Mouth Gag と Skewer と器具なしフレームを構造的に除外する」** | **Skewer の除外率 0.00%（0/343）**、Mouth Gag 2.74%（全体 2.98% より低い）、器具なしは 460 中 6 枚。この記述は `src/egosurgery/datasets/loss_mask.py` の docstring（3-6 行目）にもそのまま書かれており、**実装の説明文がデータと食い違っている** | 交絡の向きの読み違い。実際の偏りは**希少工程**にある |
| 「領域を入力チャネルに使う実験（G-2）で領域 > 矩形は 0/6」（再検証しない前提として提示） | 本 task では再検証していないが、`experiments/g2_main_2026-07-29_lecun/RESULTS.md` が実在し前提は保持される。**ただし起票者の想定経路一覧にこのファイルは無かった** | 想定の網羅漏れ |
| `data/annotations/pseudo_labels/{hand_tool_relation,bbox_near_contact}` は「空の .gitkeep のみ」（既存監査の記述） | **ディレクトリごと存在しない**（`data/annotations/pseudo_labels` 自体が無い） | Q6 の前提が変わる。ただし GT が実在するため結論は変わらない |

### 既存の監査どうしの食い違いを決着させた

同じ問い（術具 15,437 枚のうち hand_tool_seg 注釈を持つ枚数）に 2 つの値があった。

| 出典 | 値 | 読んだ対象 |
|---|---|---|
| `hts_next6_2026-07-29` §2 T1 | 9,106 / 15,437 = 59.0%（判定 **FAIL**） | `04_handtool` の `by_split` / `merged_annotations.json` |
| `hts_coverage_2026-07-30` 結論 2 | 14,977 / 15,437 = 97.02% | `json_per_video` を basename で dedupe |

**本 task の実測は 14,977 / 15,437 = 97.02% で、後者と一致する。**
2026-07-31 に `data/annotations/egosurgery_hts/` が `json_per_video` から
tool_split 整合で再構築されており（`README.md` §5 に生成コマンドが記録されている）、
`hts_next6` が FAIL 判定の根拠にした壊れた `coco_splits_5cls` は使われていない。

→ **`hts_next6` の「分母を 9,106 に変更し、既存 Δ を全て再計算しなければ比較できない」
という設計変更の要求は、07-31 の再構築によって不要になっている。**
補助課題は 15,437 の母集団の上で 97.02% の被覆で成立する。

---

## 6. 交絡の恐れ

1. **§0 の希少工程偏り。** 補助教師が最も薄いのが希少工程。効果を工程別に分解して
   報告しない限り、平均値は「補助教師が濃い工程の効果」に引きずられる。
2. **容量増（4.850σ の前例）。** 容量一致対照を置かなければ分離できない。
3. **同一 seed でも結果が再現しない既知の現象**（`experiments/g2_followup_2026-07-29/REPORT.md`
   の「重大な発見」）。本 task では再測していないが、Δ の σ をどう取るかに直結する。
   **本 task で実測した paired Δ の pstd（工程 0.003594 / 検出 0.003607）は
   この再現ばらつきを含んだ値である。**
4. **`tool_seg` の test 被覆が 92.08%** と train（98.66%）より 6.6pt 低い。
   hand_tool_seg では test 96.30% / train 96.88% で差は小さい。
   3 種を同時に使う設計では test 側の欠落が効く。

---

## 7. 判断が要る事項

`spec.yaml` の `decisions_required` は空であり、実行者が決めた事項は無い。
以下は**材料であって決定ではない**。決めるのは起票者と利用者である。

1. **容量一致対照を置くか。** 工程側の前例が 4.850σ である以上、置かなければ
   補助信号の効果を主張できない。置く場合は腕が 1 本増える。
2. **補助損失の無効化方式。** フレーム単位フラグ（母集団を保つ）か、
   manifest から落とす（母集団が縮む）か。前者を推すが決定ではない。
3. **希少工程の結論をどう扱うか。** 補助教師が 2〜3 倍薄い工程について、
   効果の主張を保留するか、工程別に分解して報告するか。
4. **検出側 S0-frozen との比較を行うか。** paired 分母の前例が無く、
   unpaired の絶対値比較になる。`§13 の 4 分母運用`（0.7271 と 0.7051 は別 checkpoint）
   に照らして、どの分母を使うかの判断が要る。

---

## 8. 測れなかったこと（UNKNOWN）

| 項目 | 理由 |
|---|---|
| 補助課題を足したモデルの実測値 | **本 task は読み取りのみで学習・評価を行わない契約**。比較の土台が成立するかだけを測った |
| 補助ヘッドが実際にどれだけ容量を増やすか | 補助ヘッドが未設計・未実装のため測れない。neck の前例（4.850σ）を代理指標として提示した |
| `s0_frozen` の `frozen_source_tag` が空である理由 | 索引上は空。S0-frozen 自身が凍結源の生成側であるためと解釈できるが、**実装で確かめていないため断定しない** |
| 同一 seed の再現ばらつきの現在値 | 既存レポートに記述があるが本 task では再測していない |

---

## 9. 逸脱

| # | 種別 | 内容 |
|---|---|---|
| 1 | judgement | SPEC Phase B Step 3 は「Q1 から Q3 が Phase A で埋まっていない場合のみ実施」とするが、**Q1・Q2 は既存監査が古い（07-29/07-30）のに対し実体が 07-31 に再構築されていた**ため、SPEC の「既存の監査が古く注釈が更新されている → 測り直す」に従って全問を実測した。測り直した結果、Q2 について既存監査 2 本の食い違いが決着した |
| 2 | judgement | `tests` の件数を**開始前に測っていない**。`src/` `tests/` を一切変更していないため before = after として 5 failed / 359 passed を記録した。作業ツリーの確認（§10）で変更が無いことを裏づけている |
| 3 | environment | 常駐同期処理 `m2-sync.sh` が本 task の直前（16:03）に別分岐 `feat/s0-reevaluation-feasibility` へ `origin/phase0` を自動統合・自動 push した記録がある（`~/claude-sync/sync-alerts.log`）。**実行者の逸脱ではない。**本 task の分岐では作業開始時に `.sync-pause` を置いており、稼働中の版が対応済み（`grep -c sync-pause ~/bin/m2-sync.sh` = 2）であることを確認した |
| 4 | environment | SPEC 記載の `grep -rln ... --include=*.md ...` は**実行シェル（zsh）がグロブを展開して失敗**し `no matches found` で 0 件になった。引用して再実行し 25 件を得た。SPEC の注意 8 が想定した事象そのもの |

---

## 10. 作業ツリーの確認

    git status --porcelain | cut -c1-120

変更は `tasks/` 配下のみ。`src/` `configs/` `scripts/` `experiments/` `data/` `runindex/` に
変更が無いことを確認した（詳細は §11 のコマンド出力）。

## 11. 生成物

| パス | 内容 |
|---|---|
| `audit/q_coverage.md` | Phase A の 10 問仕分け表・監査物の両方向集合差・既存監査どうしの食い違い |
| `audit/measure_hts_entity.py` | Phase B の測定スクリプト（読み取りのみ） |
| `audit/hts_entity.txt` | 同出力（規模・集合差・重複・陽性対照・460 の内訳） |
| `audit/measure_baselines.py` | Phase C の測定スクリプト（読み取りのみ） |
| `audit/baselines.txt` | 同出力（基準点 4 つ・paired Δ・レシピ分布・凍結源分布） |
| `audit/comparability.md` | Phase C の比較可否分類 |
| `RESULT.md` | 本ファイル |
| `result.yaml` | 機械可読の対 |
