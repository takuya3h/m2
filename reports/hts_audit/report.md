# EgoSurgery-HTS 受入監査レポート (C01–C11)

- HTS_ROOT: `data/raw/OpenSurgery_Dataset/05_egosurgery_hts`
- PROJECT_ROOT: `.`
- 出力: `reports/hts_audit` / seed=42 / max_json_mb=90.0 / rle_sample=4000
- すべての数値は実測値. 測定不能は SKIP/UNKNOWN と明記.

## ⚠ 想定外の発見 (事前情報 §2.6 との差異)

- §2.6-b の『孤児annotation 濃厚』仮説は反証: 実測 orphan=0. train_toolhand(7847img)→withmask(5668img) で削られた 2179枚は『空アノテ画像』であり, アノテ付き画像ではない (孤児は発生せず). 事実を採用.
- §2.6-h 確認: HTS tools と project instances は basename 正規化後に内容一致 (生 file_name はパス接頭辞が違うため naive ハッシュ照合では DIFFERENT に誤判定する点に注意).

## 1. 判定サマリ

| Check | 内容 | ステータス | 主要実測値 |
|---|---|---|---|
| C01 | インベントリとクラス体系 | **OK** | n_json=156; n_taxonomies=5; signature_present={'Scalpel': True, 'Needle Holders': True, 'Bipolar Forceps': True} |
| C02 | 参照整合性と COCO 妥当性 | **OK** | max_orphan=0; max_dup=0 |
| C03 | 動画×split×タスク フレーム行列 | **WARN** | leaks=0; missing=3; base_total=15437 |
| C04 | phase CSV の分布 (17-22含む) | **OK** | gap={'disinfection': {'01-15': 125, '17-22': 115}, 'dressing': {'01-15': 321, '17-22': 196}, 'irrigation': {'01-15': 217 |
| C05 | 重複検出 (HTS vs project) | **OK** | verdicts=['IDENTICAL_CONTENT', 'IDENTICAL_CONTENT', 'IDENTICAL_CONTENT'] |
| C06 | mask外接矩形 vs bbox IoU/充填率 | **WARN** | iou_median=0.8595196302944491; fill_median=0.19223231765645518; matched=51318 |
| C07 | which_tool 復元と手クラス対応 | **OK** | n_sampled=9680; containment_p50=0.9982602531413233; frac_ge05=0.9366735537190083 |
| C08 | PNG split別枚数 (リーク検査) | **FAIL** | per_split={'train': 11308, 'test': 4637, 'val': 1703}; leak_png=6340 |
| C09 | (hand,tool) 共起頻度と疎性 | **OK** | nonzero_cells=41; train_sparse_lt10=13; train_effective=24 |
| C10 | relation の時間安定性 | **OK** | mean_run_length=7.040849206439562; mean_switch_rate=0.2013467469412597 |
| C11 | 被覆率と再計算分母リスト出力 | **OK** | n_rows=15 |

## 2. 不変量 I1–I5 の合否

| 不変量 | 内容 | 判定 | 根拠 |
|---|---|---|---|
| I1 | 評価フレーム集合15,437 | 保持(基底)/サブセット限定 | tool_bbox 総フレーム=15437 で 15,437 に完全一致 (C05: project instances と 同一内容). phase被覆=1.0. mask/relation は C11 のサブセットのみ→新実験のΔは要再計算 |
| I2 | split定義(動画hold-out) | 定義は保持/PNG層は要再フィルタ | canonical定義(data/splits)は不変・C03 split-json は LEAK=0. ただし handtool_masks_5cls/train が val/test を 6340枚混在→naiveローダはリーク |
| I3 | クラス体系 tool15/hand4/phase9 | 参照 | C01/C04 (実測クラス数を参照) |
| I4 | 凍結源・特徴抽出 | 維持可 | C05 重複判定=['IDENTICAL_CONTENT', 'IDENTICAL_CONTENT', 'IDENTICAL_CONTENT'] |
| I5 | 統計手続き(paired-σ, macro-F1) | 本監査対象外(データ非依存) | — |

## 3. ゲート G-1〜G-4 判定

| ゲート | 内容 | 判定 | 理由 |
|---|---|---|---|
| G-1 | GT hand-tool relation を工程認識へ | 実行可 | C07 復元率(内包率>=0.5)=0.9366735537190083 / C09/C10 参照 |
| G-2 | region-token を bbox→mask pooling | 実行可 | C01 signature生存={'Scalpel': True, 'Needle Holders': True, 'Bipolar Forceps': True} / C06 IoU中央値=0.8595196302944491 |
| G-3 | mask局在改善が phase→det の壁を動かすか | 要再定義 | C06: mask は box 由来(SAM) -> oracle は GT box と近い. 『前景/背景分離の効果』へ再定義推奨 |
| G-4 | 評価プロトコル(ギャップ工程) | 拡張test split案を推奨 | C04: 17-22の評価ギャップ工程={'disinfection': {'01-15': 125, '17-22': 115}, 'dressing': {'01-15': 321, '17-22': 196}, 'irrigation': {'01-15': 217, '17-22': 321}} |

## 4. 各検査の詳細

### C01 インベントリとクラス体系 — **OK**

- HTS配下 JSON 総数 = 156
- tool_seg_noskewer categories = 31
- signature 3術具 in 31cls = {'Scalpel': True, 'Needle Holders': True, 'Bipolar Forceps': True}
- 出力: csv/c01_inventory.csv, csv/c01_taxonomy.csv, csv/c01_map_31_to_15.csv

### C02 参照整合性と COCO 妥当性 — **OK**

- 出力: csv/c02_integrity.csv

### C03 動画×split×タスク フレーム行列 — **WARN**

- LEAK=0 MISSING=3 未parse file_name=0
- tool_bbox 総フレーム=15437 (内訳 {'test': 4265, 'train': 9657, 'val': 1515}) ← I1 の基底
- MISSING 内訳: toolhand/train:動画14, toolhand_withmask/train:動画03, toolhand_withmask/train:動画14
- MISSING は WARN. C11 の分母設計に反映せよ (tool_bbox基底は保持, 欠落は toolhand_withmask の派生タスクのみ)
- 出力: csv/c03_frame_matrix.csv, csv/c03_split_conformance.csv

### C04 phase CSV の分布 (17-22含む) — **OK**

- phase CSV ヘッダ種別 = [(['Frame', 'Phase'], 46)]
- 評価ギャップ3工程 (train01-15 / 17-22): {'disinfection': {'01-15': 125, '17-22': 115}, 'dressing': {'01-15': 321, '17-22': 196}, 'irrigation': {'01-15': 217, '17-22': 321}}
- 動画17-22 に評価ギャップ工程あり -> G-4 は『拡張 test split』案を強く推奨 (ただし17-22 は bbox/mask 無し -> S4/B2a のみ拡張可)
- 出力: csv/c04_phase_per_file.csv, csv/c04_phase_distribution.csv

### C05 重複検出 (HTS vs project) — **OK**

- [train] basename正規化後は内容一致 (差はfile_name形式のみ: HTS_fn=01_1_0124.jpg / PROJ_fn=train/01/01_1_0124.jpg / img数一致=True / ann数一致=True)
- [val] basename正規化後は内容一致 (差はfile_name形式のみ: HTS_fn=09_1_0213.jpg / PROJ_fn=val/09/09_1_0213.jpg / img数一致=True / ann数一致=True)
- [test] basename正規化後は内容一致 (差はfile_name形式のみ: HTS_fn=04_1_0511.jpg / PROJ_fn=test/04/04_1_0511.jpg / img数一致=True / ann数一致=True)
- 全 split basename正規化後は同一内容 -> I4 は無改修維持可 (HTS tool bbox は project instances と同一フレーム/同一bbox, file_name のパス接頭辞のみ相違). 片方削除で容量節約可
- 出力: csv/c05_duplicate_check.csv

### C06 mask外接矩形 vs bbox IoU/充填率 — **WARN**

- matched=51318 unmatched=8896 n_masks=60214
- IoU中央値=0.8595196302944491
- 充填率中央値=0.19223231765645518
- noskewer mask 実体を持つ15クラス=13/15, 実体0件の15クラス=['Mouth Gag', 'Skewer']
- IoU中央値<0.90 -> G-2のΔが『mask効果』か『box定義変更』か交絡. 対照実験『mask由来boxで作ったbbox版T1a』が必須
- 実体0件の術具 ['Mouth Gag', 'Skewer'] は G-2 の per-phase 分析から脱落 (Skewer=design工程signature0.997, Mouth Gag). §2.6-f 確認
- 充填率が1に近い術具=背景除去効果小/低い術具(細長)=G-2期待効果大 (分布はG-2効果量の事前予測子)
- 出力: csv/c06_mask_bbox_geometry.csv, csv/c06_fill_ratio_by_class.csv

### C07 which_tool 復元と手クラス対応 — **OK**

- 実サンプル tool mask 数 = 9680 (上限 rle_sample=4000/split)
- 内包率分位 = {5: 0.23655772104718567, 25: 0.985230013408771, 50: 0.9982602531413233, 75: 1.0, 95: 1.0}
- 内包率>=0.5 割合 = 0.9366735537190083
- margin<0.2 (曖昧) 割合 = 0.08016528925619834
- 手対応 Own=10238 Other=23 (Other比率=0.0022414969301237696, 内包率>=0.5 のみ集計)
- Other対応ほぼ0 (Other比率0.22%) -> 助手手のrelationは事実上取得不可. 論文の限界として明記が必要
- 出力: csv/c07_which_tool_recovery.csv, csv/c07_hand_class_correspondence.csv

### C08 PNG split別枚数 (リーク検査) — **FAIL**

- PNG枚数 canonical別 = {'train': 11308, 'test': 4637, 'val': 1703}
- val/test 混在 6340枚 -> ディレクトリ名を信用したローダは即リーク. canonical split による再フィルタを必須要件に
- 出力: csv/c08_png_split.csv

### C09 (hand,tool) 共起頻度と疎性 — **OK**

- 非ゼロセル数(全split, 内包率>=0.5) = 41
- train で 10例未満のセル数 = 13
- train 非ゼロセル数 = 37
- B2aでは15次元中12次元がノイズ・利得129%を上位3次元が支配. relationでも同型を想定し実用セル数を明示
- 出力: csv/c09_cooccurrence.csv

### C10 relation の時間安定性 — **OK**

- 平均継続長(全系列平均)=7.040849206439562 フレーム, 平均切替率=0.2013467469412597
- 比較: 既存工程の自己遷移率0.982 (粘性大), サンプリング0.5fps
- 継続長が短ければT1aのflicker由来過分節(edit 41.08->37.07)が再発 -> 因果 min-segment debounce(k=2) の relation版を事前用意すべき
- 出力: csv/c10_temporal_stability.csv

### C11 被覆率と再計算分母リスト出力 — **OK**

- ★ このフレームリストを分母に S4/B2a/T1a/H-6 を同一集合で再計算しない限り, 新Δは既存 +0.0383/+0.0497/+0.0004 と比較不能 (I1 の破れ). 再計算は G-4 に含める
- 出力: csv/c11_coverage.csv, subsets/subset_{task}_{split}.txt

## 5. 次に取るべきアクション (優先度順)

- [P0] C08 PNGリーク: handtool_masks_5cls/train のローダに canonical split 再フィルタを必須化 (val/test 混在)
- [P1] C11 のフレームリスト(subsets/)を分母に mask/relation 実験の Δ を測る際は S4/B2a/T1a/H-6 を同一サブセットで再計算 (基底15,437は保持だが派生タスクはサブセット). G-4 の作業に含める
- [P3] C05: HTS tools と project instances は内容一致 -> 正本決定は不要. 片方を削除して容量節約可 (任意)
- [P2] G-4 の方針: C04 に基づき 拡張test split案を推奨
