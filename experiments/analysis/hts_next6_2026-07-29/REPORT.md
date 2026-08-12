# EgoSurgery-HTS ─ 分母確定・リーク検査・クラス対応 実測レポート

- 実施日: 2026-07-29
- ホスト: efros / 出力: `experiments/analysis/hts_next6_2026-07-29/`
- 実行範囲: **Phase A（T1–T3）+ Phase B（T4–T5）まで。Phase C（G-1 学習）は未実行**（理由は §6）
- 本レポート中の数値は**すべて実測値**。推測値・概算は 0 件。測れなかったものは `UNKNOWN` / `SKIP` と明記。

---

## 0. 想定外の発見（最優先）

### 0.1 【重大】`merged_annotations.json` の「被覆率向上」は存在しない

指示書 §3 T1 の導出「完全版を使えば被覆率が **87% 以上に上がる**」は**実測で否定された**。

`merged` が by_split 版より多く持つ 4,521 フレームは、**全て annotation 0 件の空エントリ**である。

| 検証項目 | 実測結果 |
|---|---|
| `A∩C(ann≥1)` と `A∩B` の集合一致 | **完全一致**（train/val/test すべて、差分 0 件） |
| フレーム毎の annotation 数の一致 | **9,106 フレーム全てで一致**（不一致 0 件） |
| 「復活」した 4,521 フレームのうち ann≥1 のもの | **0 件** |
| 動画 03（§1.4-b で欠落とされた動画） | 画像エントリ 1,472 枚、うち ann≥1 は **0 件** |
| 動画 14（同上） | 画像エントリ **0 枚**（そもそも存在しない） |

→ **merged は動画 03・14 の Hand-Tool を復活させていない。** §1.4-c の「完全版」という位置づけは
annotation 水準では成立しない。**実被覆率は従来どおり 59.0%。**

### 0.2 【重大】`merged_annotations.json` のファイル整合性の欠陥

| 項目 | 実測値 |
|---|---:|
| 画像エントリ | 17,603 |
| annotations 配列長（論文値 41,605 に対応） | 41,605 |
| うち **有効**（image_id が images に存在） | **40,201** |
| うち **dangling**（image_id が images に存在しない） | **1,404** |
| dangling が指す image_id の範囲 | 17,604–18,019（画像 id 最大値 17,603 を超える） |
| **annotation 0 件の画像エントリ** | **6,618**（37.6%） |

論文の「Hand-Tool 41,605」は annotations 配列の生の長さであり、うち 1,404 件は参照先画像を持たない。
このファイルを素直に読むと、被覆率を **88.3% と誤認**する（本タスクで実際に誤認が起きかけた）。

### 0.3 §1.1「除外 4 セグメント = 4,123 枚」は 2 点で事実と異なる

| 指示書 §1.1 | 実測 |
|---|---|
| 除外セグメントは `03_1, 03_3, 12_2, 15_2` の 4 つ | 母集団に存在するのは **3 つ**（`03_1, 12_2, 15_2`、計 **463 枚**）。<br>`03_3` は画像・アノテーションがどの JSON にも存在しない（生フレームは `01_frames` に 261 枚存在） |
| 除外分は計 4,123 枚 | 4,123 は **P(19,560) − A(15,437)** の差。内訳は<br>除外セグメント **463 枚** + **canonical セグメント内の未採用 3,660 枚** |

→ canonical split は「特定セグメントを丸ごと除外した」のではなく、**セグメント内でもフレームを間引いている**。

### 0.4 §1.4-a「`tool_seg_noskewer` は Skewer を含む」の訂正

| 版 | Skewer の宣言 | Skewer の annotation |
|---|---|---:|
| `tool_seg_noskewer` | categories に宣言あり（31 個） | **0 件** |

→ **annotation 水準では名称は正しい**（Skewer は 1 件も無い）。`Mouth Gag` も 0 件で、
実データを持つクラスは **29**。「31 クラス」は宣言上の数。
（本セッション前半に作成した `SCALE_VERIFICATION.md` の同旨の記述も本レポートに合わせて訂正済み。）

### 0.5 命名と中身の不一致がもう 1 件

`fusion/03_3.json` は名前が `03_3` だが、中身は **セグメント 03_1 / 03_2 の 1,472 枚**で
**annotation は 0 件**。§1.4-a と同種の命名トラップ。

---

## 1. タスク別ステータス

| Task | 内容 | ステータス | 判定 |
|---|---|---|---|
| T1 | 分母確定（merged vs by_split） | 完了 | **FAIL** |
| T2 | SAM 指紋検査（G-2/G-3 ゲート） | 完了 | **WARN**（総合） |
| T3 | クラス体系 4 版の対応表 | 完了 | **PASS** |
| T4 | D1 決定文書 | 完了（決定は未実施） | — |
| T5 | D2 決定文書 + phase 被覆実測 | 完了（決定は未実施） | — |
| T6 | G-1 実験 | **未実行** | ゲート未通過（§6） |

合成データによる検出能力の確認（Step 1-5）は T1・T2・T3・T5 の**全スクリプトで実施し、全て PASS**。

---

## 2. T1: 分母の確定 — 判定 FAIL

### 被覆率（2 定義で実測）

判定には **annotated 基準**（有効な Hand-Tool annotation を 1 件以上持つ）を使用。
annotation 0 件のフレームは relation 特徴を持たないため分母に数えられない。

| split | canonical | by_split | merged(entry) | **merged(annotated)** | recovered |
|---|---:|---:|---:|---:|---:|
| train | 9,657 | 5,668 (0.587) | 7,847 (0.813) | **5,668 (0.587)** | **+0** |
| val | 1,515 | 1,344 (0.887) | 1,515 (1.000) | **1,344 (0.887)** | **+0** |
| test | 4,265 | 2,094 (0.491) | 4,265 (1.000) | **2,094 (0.491)** | **+0** |
| **計** | **15,437** | **9,106 (0.5899)** | 13,627 (0.8827) | **9,106 (0.5899)** | **+0** |

有効 annotation 数: by_split 34,175 / merged 34,175（**完全一致**）。

### 判定

| 実測 `coverage_merged`（annotated） | 判定 | アクション |
|---|---|---|
| **0.5899**（< 0.70） | **FAIL** | 従来の 59% と大差なし。**G-1 の設計を「縮約 split 上での比較」に変更する必要がある** |

### 母集団はみ出し確認（Step 1-3）

- `C − P` = **0 件** → merged は 19,560 枚の母集団の外の画像を含まない（導出の前提は崩れていない）
- `C − (A ∪ 除外セグメント)` = 3,513 件。ただしこれは §0.3 のとおり
  「canonical セグメント内の未採用フレーム」であり、母集団外ではない
- basename パース失敗 0 件 / 未知 video 0 件

### 動画 ID 抽出規則（レポート明記事項）

`os.path.basename` 適用後、正規表現 `^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)\.(jpg|png)$` を適用し、
video = 第 1 トークン、segment = `video_segidx` とする。
**集合 A の `file_name` は `train/01/01_1_0124.jpg` のようにパス接頭辞を持つため basename 化が必須**
（素朴に `file_name` で join すると交差が 0 件になる）。

### 出力

`$OUT/subsets/subset_ht_{train,val,test}.txt` = **5,668 / 1,344 / 2,094（計 9,106）**。これが Phase C の分母。

---

## 3. T2: SAM 指紋検査 — 判定 WARN（総合）

### 前提の確認

マスク JSON の `ann['bbox']` は **mask の外接矩形から導出**されており（実測: 差が常に 1px = w/h 規約差）、
独立な検出 box ではない。したがって照合相手には外部の **canonical bbox（既存実験の凍結源）** を使用した。

### 3 トラックの実測

| トラック | pairs | IoU median | IoU IQR | 内包率 mean | 内包率 q1 | 充填率 median | 判定 |
|---|---:|---:|---:|---:|---:|---:|---|
| tool_seg31 vs canonical tool bbox | 45,583 | 0.8771 | 0.1515 | 0.9418 | 0.9368 | 0.2044 | **PASS** |
| HT tool mask vs canonical tool bbox | 15,019 | 0.8994 | 0.1376 | 0.9554 | 0.9690 | 0.1645 | **WARN** |
| HT hand mask vs hand bbox | 19,329 | 0.8855 | 0.3698 | 0.8430 | 0.7911 | 0.5783 | **PASS** |

### 参照指紋との比較（§1.5）

| 指標 | 前バンドル（偽物） | 今回の実測 |
|---|---:|---|
| 内包率 mean | 0.879 | 0.9418 / 0.9554 / 0.8430 |
| IoU median | 0.927 | 0.8771 / 0.8994 / 0.8855 |
| 集中度（IoU IQR < 0.10 が SAM 条件） | 該当 | 0.1515 / 0.1376 / 0.3698（**全て 0.10 超**） |

**前バンドルの SAM 指紋は 3 トラックとも再現しなかった。**

### 分布の形状（ビン幅 0.02 のヒストグラムより）

| トラック | 内包率 ≥0.98 | 内包率 ≤0.95 | IoU ≥0.98 |
|---|---:|---:|---:|
| tool_seg31 | 52.0% | **26.1%** | 2.4% |
| HT tool | 69.3% | **15.7%** | 6.4% |
| HT hand | 51.5% | **40.8%** | 6.0% |

bbox 条件付き生成なら mask はほぼ全て bbox に内包されるはずだが、
実測では **15.7〜40.8% のマスクが bbox からはみ出している**。これは bbox 条件付き生成では説明しにくい。

### WARN の意味（誤読防止）

HT tool トラックが WARN なのは、**SAM 条件に該当したからではない**。
SAM 条件（内包率 mean 0.86–0.90 かつ IoU median 0.91–0.94 かつ IQR < 0.10）に対し
実測 内包率 mean = 0.9554 は範囲外で、**SAM 由来ではないと判断できる**。
一方で PASS 条件（IoU IQR ≥ 0.15 かつ 内包率 q1 < 0.95）にも僅かに届かない
（IQR 0.1376、q1 0.9690）ため、境界値として WARN とした。
§7 の「境界値は通したことにせず WARN として報告」に従う。

### Step 2-4: 充填率と G-2 の期待効果量

充填率 = `area(mask) / area(bbox)`。低いほど bbox 内の背景が多く、mask pooling の効果が大きい。

| signature 術具 | n | 充填率 median | q1 | q3 |
|---|---:|---:|---:|---:|
| **Bipolar Forceps** | 696 | **0.203** | 0.145 | 0.312 |
| **Scalpel** | 1,066 | **0.199** | 0.139 | 0.308 |
| **Needle Holders** | 4,829 | **0.120** | 0.090 | 0.187 |

- 術具全体の充填率 median は **0.204**（bbox の約 80% が背景）→ 背景除去の効果は**原理的に大きい**
- signature 3 術具はいずれも 0.12–0.20 と低く、**G-2 の期待効果量が大きい**側に属する
- 対照的に手は充填率 median 0.578 と高く、手に対する mask pooling の効果は相対的に小さい

---

## 4. T3: クラス体系の対応表 — 判定 PASS

### 4 版の実測

| 版 | 実体 | 宣言カテゴリ | 実データを持つクラス | ann |
|---|---|---:|---:|---:|
| V31 | `by_video/tool` | 31 | 31 | 67,687 |
| V14 | `03_tool/coco_splits_14cls_cleaned` | 14 | 14 | 51,329 |
| V15k | `03_tool/coco_splits_15cls_withkidney` | 15 | **14**（Skewer 0 件） | 51,052 |
| VBS | `data/annotations/egosurgery_tool`（凍結源） | 15 | 15 | 49,652 |

**「15 クラス」を名乗る版が 2 つあるが中身が違う**: VBS = 14cls + **Mouth Gag** / V15k = 14cls + **Kidney Dish** − Skewer。

### Q1: signature 3 術具は V14 で生存しているか → **生存（吸収 0 件）**

| 術具 | VBS ann | V14 ann | 他クラスへの吸収 |
|---|---:|---:|---|
| Bipolar Forceps | 696 | 713 | なし |
| Scalpel | 1,066 | 1,125 | なし |
| Needle Holders | 4,829 | 5,307 | なし |

### Q2: Skewer の扱い（4 版 + noskewer）

| 版 | 宣言 | annotation |
|---|---|---:|
| V31 | あり | 344 |
| V14 | あり | 344 |
| V15k | あり | **0** |
| VBS | あり | 344 |
| `tool_seg_noskewer` | あり | **0**（§0.4 のとおり名称は annotation 水準で正しい） |

### Q3: VBS(15) → V14(14) は一意写像か → **一意写像である**

閾値感度（V14 の box は VBS と別導出のため単一閾値では決められない）:

| IoU 閾値 | マッチ率（対 VBS） | 実質的な 1 対多（支配率 ≥5%） |
|---|---:|---|
| 0.95（指示書の literal 基準） | 0.145 | **なし** |
| 0.90 | 0.372 | **なし** |
| 0.70 | 0.782 | **なし** |
| 0.50 | 0.861 | **なし** |

literal 基準では `Scissors → {Scissors 421, Gauze 1}` が検出されるが、
Gauze は **1 件（0.24%）**で閾値を変えると消えるマッチングノイズ。実質的な 1 対多は全閾値で 0。

- **VBS にあり V14 に写像先が無いクラス: `Mouth Gag`（5,985 ann）** → V14 採用時に脱落
- **V14 の box は VBS と座標が一致しない**（best-IoU 中央値 **0.871**、IoU≥0.95 は 15.6% のみ）
  → V14 採用は「クラス数の変更」ではなく **box の差し替え**であり、I4 に抵触するリスク（D1 §決定 2 参照）

### assert ヘルパ

`scripts/analysis/assert_class_system.py` を追加。実測済みの正解クラス名を `KNOWN_SYSTEMS` に保持し、
Phase C で読む全 annotation ファイルを読み込み時に検証する。

---

## 5. 不変量 I1–I5 の再評価

| 不変量 | 内容 | 再評価 | 根拠 |
|---|---|---|---|
| **I1** | 評価フレーム集合が既存実験と一致 | **不成立（要設計変更）** | HT が使えるのは 9,106 / 15,437（59.0%）。merged でも回復しない（§0.1）。<br>G-1 は縮約 split 上での比較になる |
| **I2** | split 定義が canonical と一致 | **成立** | `data/splits/ego_*.txt` を正本として使用。動画割当の組み替えなし。<br>HT subset は canonical の**部分集合**であり再分割ではない |
| **I3** | クラス体系が既存と対応づけ可能 | **成立** | VBS→V14 は一意写像、signature 3 術具は生存（§4）。<br>ただし Mouth Gag 5,985 ann は V14 に写像先なし |
| **I4** | 凍結源・特徴抽出パイプラインが不変 | **成立（ただし条件付き）** | 本タスクでは凍結源を一切変更していない。<br>**V14 を正本に採用すると box 座標が変わり I4 を破る**（§4 Q3） |
| **I5** | 統計手続き（3-seed, paired-σ）が不変 | **未評価（SKIP）** | Phase C 未実行のため。<br>rare 工程は枚数が小さく効果量 CI が広くなる点を D2 に記載済み |

---

## 6. Phase C を実行しなかった理由

実行ゲート（§5）の判定:

| ゲート条件 | 実測 | 通過 |
|---|---|---|
| T1 が PASS または WARN | **FAIL**（0.5899 < 0.70） | **不通過** |
| T3 が PASS または WARN | PASS | 通過 |
| D1 / D2 についてユーザの決定を受領済み | 未受領 | **不通過** |

**T1 が FAIL のため、§5 の規定「FAIL なら設計変更が必要なので停止」に従い Phase C を 1 本も実行していない。**
加えて Phase B（Step 5-5）の規定により、D1 / D2 をユーザに提示して決定を待つ段階で停止している。

> T2 の WARN は G-1 のゲートではない（T2 は G-2 / G-3 をゲートする）。念のため明記する。

### G-1 に必要な設計変更（T1 FAIL の帰結・提案であり決定ではない）

- 分母を canonical 15,437 ではなく **HT subset 9,106** に変更する
- §1.2 の既存 Δ（B2a +0.0383 / T1a +0.0497 / H-6 +0.0004）は 15,437 枚上の値であり、
  **9,106 枚上で C-a / C-b / C-d / G-1 を全て再計算しなければ比較できない**（指示書 Step 6-3 と同旨）
- 被覆率 59.0% と、非被覆フレームの工程分布（§3 の表）を論文に明記する必要がある

---

## 7. 成果物一覧

| パス | 内容 |
|---|---|
| `json/t1_denominator.json` | T1 実測値・判定・母集団検査 |
| `csv/t1_coverage_by_split.csv` / `t1_coverage_by_video.csv` | 被覆率（split 別 / 動画別） |
| `subsets/subset_ht_{train,val,test}.txt` | **Phase C の分母（9,106 枚）** |
| `json/t2_fingerprint.json` | T2 3 トラックの分布統計と判定 |
| `csv/t2_iou_incl_by_class.csv` | クラス別 IoU / 内包率 / 充填率 |
| `csv/t2_fill_ratio_by_class.csv` | ヒストグラム（ビン幅 0.02） |
| `json/t3_class_mapping.json` | 4 版の対応表・閾値感度・Q1–Q3 |
| `csv/t3_class_crosstab.csv` / `t3_categories.csv` | 版 × 版 混同行列 / categories 実測ダンプ |
| `json/t5_phase_coverage.json` / `csv/t5_phase_coverage.csv` | 9 工程 × split の被覆 |
| `decisions/D1_canonical_source.md` | HT 正本・術具クラス正本の選択肢と推奨 |
| `decisions/D2_eval_protocol.md` | 評価プロトコル 3 案の比較と推奨 |

### 使用スクリプト（すべて `--self-test` 付き）

```bash
python3 scripts/analysis/hts_denominator.py    --self-test && python3 scripts/analysis/hts_denominator.py    --out $OUT
uv run --with 'numpy<2' --with pycocotools \
  python3 scripts/analysis/hts_sam_fingerprint.py --self-test && \
uv run --with 'numpy<2' --with pycocotools \
  python3 scripts/analysis/hts_sam_fingerprint.py --out $OUT
python3 scripts/analysis/hts_class_mapping.py   --self-test && python3 scripts/analysis/hts_class_mapping.py   --out $OUT
python3 scripts/analysis/hts_phase_coverage.py  --self-test && python3 scripts/analysis/hts_phase_coverage.py  --out $OUT
```

環境注記: efros には `.venv` が存在しないため、pycocotools を要する T2 のみ `uv` の一時オーバーレイ
（`numpy<2` 固定）で実行した。T1・T3・T5 は標準ライブラリのみで動作する。

### 元データへの変更

**なし。** `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/` は読み取りのみ（§0 の禁止事項を遵守）。
split の再定義も行っていない。
