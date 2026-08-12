## 16. エポック数・再現性の検証ログ {toggle="true"}
	本節は S0 再実験（§8.0 暫定運用、bengio で DDP 2 GPU 実行）の途中で発見された「エポック数の仮定根拠不足」と「論文 SOTA を大きく上回る数値の妥当性検証」を claude との壁打ちで整理したものである。§15 Lessons Learned の姉妹節として位置づけ、今後同様の「学習設定の仮定根拠不足」「再現性の警鐘」「評価条件の歪み」は本節に蓄積する。
	### 16.1 EgoSurgery-Tool 論文にエポック数の記載がない事実
	- arXiv:2406.03095v4 §3.1 Experimental setups を直接確認した結果、記載は「MMDetection 使用」「MS-COCO 事前学習から fine-tuning」「backbone parameters を寄せる」「confidence 10\^-8 で評価」の 4 点のみ。**エポック数・学習率・batch size・scheduler・augmentation の記述は一切ない**。
	- Fujiry0/EgoSurgery 公式リポジトリは**データセット配布のみで、検出器の学習コード・config が公開されていない**ことを確認。
	- mmdet 公式の 1x スケジュールだけは 12 epochs と定義されているが、これを論文の採用値と認める根拠は論文・公式リポジトリのいずれにもない。
	- **位置づけの修正**：§10.1 S0 手順の「完了判定 = VarifocalNet 公式 SOTA 45.8 を上回る」は、**エポック数を含む学習設定が不明のまま**の状態では有意にならず、eval_recipe だけでは再現性を保証できない。**〔2026-06-19 追記〕** 検出ベースラインはその後 DETR 系 10 モデルで実測完了し、現行の主基準は **Relation-DETR mAP 0.730**（3-seed 平均 0.727・σ0.004・AP_rare 0.758、§12/§13）。本 §16 の VFNet 0.618／論文 45.8 は旧 recipe の途中値・長尾検証の知見として保持する。今後 §10.1 S0 手順の「完了判定」を以下に書き換える（本節を根拠として次ステップで §10.1 を修正）：**(1) §15.4 A の strict 3 条件に加え、(2) 12 / 24 / 36 epochs の各時点で checkpoint を保存し val mAP で early stopping、3-seed std を併記、(3) Δ 比較群（S0 全 detector）で採用エポック数を統一、(4) VarifocalNet 公式 45.8 を上回ることを確認**。エポック数の論文公式値は 2026/05/29 時点で論文・公式リポジトリのいずれにも未公開であり、現状は mmdet 慣行の 1x = 12 epochs を暫定採用する。著者への問い合わせ結果は本節に追記する。
	### 16.2 VFNet 再実験の数値（2026/05/29 実測、bengio DDP 2 GPU）
	<table fit-page-width="true" header-row="true">
<tr>
<td>epoch</td>
<td>iter</td>
<td>mAP</td>
<td>mAP_50</td>
<td>mAP_75</td>
<td>AP_rare</td>
<td>AP_common</td>
</tr>
<tr>
<td>1</td>
<td>2,405</td>
<td>0.361</td>
<td>0.486</td>
<td>0.411</td>
<td>0.237</td>
<td>0.352</td>
</tr>
<tr>
<td>2</td>
<td>4,810</td>
<td>0.460</td>
<td>0.602</td>
<td>0.511</td>
<td>0.537</td>
<td>0.413</td>
</tr>
<tr>
<td>3</td>
<td>7,215</td>
<td>0.432</td>
<td>0.571</td>
<td>0.481</td>
<td>0.428</td>
<td>0.400</td>
</tr>
<tr>
<td>4</td>
<td>9,620</td>
<td>0.495</td>
<td>0.646</td>
<td>0.552</td>
<td>0.436</td>
<td>0.466</td>
</tr>
<tr>
<td>5</td>
<td>12,025</td>
<td>0.512</td>
<td>0.655</td>
<td>0.568</td>
<td>0.560</td>
<td>0.465</td>
</tr>
<tr>
<td>6</td>
<td>14,430</td>
<td>0.513</td>
<td>0.655</td>
<td>0.572</td>
<td>0.502</td>
<td>0.476</td>
</tr>
<tr>
<td>7</td>
<td>16,835</td>
<td>0.522</td>
<td>0.666</td>
<td>0.590</td>
<td>0.546</td>
<td>0.478</td>
</tr>
<tr>
<td>8</td>
<td>19,240</td>
<td>0.532</td>
<td>0.685</td>
<td>0.591</td>
<td>0.558</td>
<td>0.488</td>
</tr>
<tr>
<td>9</td>
<td>21,645</td>
<td>0.610</td>
<td>0.748</td>
<td>0.671</td>
<td>0.698</td>
<td>0.550</td>
</tr>
<tr>
<td>10</td>
<td>24,050</td>
<td>0.614</td>
<td>0.753</td>
<td>0.675</td>
<td>0.697</td>
<td>0.554</td>
</tr>
<tr>
<td>11</td>
<td>26,455</td>
<td>0.616</td>
<td>0.753</td>
<td>0.677</td>
<td>0.710</td>
<td>0.554</td>
</tr>
<tr>
<td>12</td>
<td>28,860</td>
<td>**0.618**</td>
<td>0.757</td>
<td>0.681</td>
<td>**0.706**</td>
<td>**0.557**</td>
</tr>
	</table>
	### 16.3 「乗り越え」の説明候補の網羅的列挙
	12 epoch で mAP 0.618 となり、論文公式 VFNet の 45.8 より 16pt 高い。以下の要因が単独・複合で作用した可能性がある。
	- **A. 評価条件側（最も疑わしい）**：(1) test_cfg.score_thr（論文 10\^-8 vs mmdet default 0.05）、(2) max_per_img（論文側は不明 vs locked-down 300）、(3) nms_pre・nms_iou の default 差、(4) COCO evaluation の IoU 閾値 0.5:0.95 vs 0.5 単独を誤って使うと過大評価、(5) per-class AP の平均方法 macro vs micro の取り違え。
	- **B. 学習設定側**：(1) エポック数 12 vs 24 vs 36、(2) batch size / lr と DDP 2 GPU での effective batch size 倍化 + lr 線形スケーリングの適用有無、(3) augmentation（mstrain / RandomCrop を使うと +2〜3pt）、(4) pretrain 重み torchvision vs open-mmlab、backbone R-50 vs R-50-DCN vs R-101、(5) **長尾対策の有無**：§10.1 S0 手順は Seesaw Loss・RFS・bbox-level Copy-Paste・post-hoc Logit Adjustment を有効化しているため、論文素の VFNet 45.8 を 10〜15pt 上回ること自体は不自然ではない。
	- **C. データ側**：(1) §15.4 の公式 split との一致 / assert_paper_split の pass、(2) 画像解像度設定、(3) annotation バージョン。
	### 16.4 警戒：AP_rare \> AP_common は通常起きない――赤信号
	§16.2 の表で epoch 9 以降 AP_rare が AP_common を常に上回り、最終 AP_rare 0.706 / AP_common 0.557 となった。通常は稀少クラスの AP は頻出クラスより低くなるため、この逆転は重大な警戒信号として記録し、§16.5 優先度 A の検証アクションに位置づける。説明候補は以下の 4 点。
	- (1) **AP_rare / AP_common のクラス分類定義が間違っている**：Forceps は train 2,534 / val 154 / test 3,375 instances と分布を持ち、12.21% の頻出クラスに属するが、test 頻度で rare 判定してしまうと誤って rare に含めてしまうケースがある。
	- (2) **AP_rare の計算対象クラスが極めて少なく分散が大きい**：Skewer test 29 instances / Syringe test 141 instances とサンプル数が小さいため、偶然に高くなりうる。
	- (3) **テストセットの構造的偏り**：稀少クラスが特定 video に集中しており、その video でだけうまく動いた可能性。
	- (4) **データリーク**：稀少クラスが train / val / test の同じ video に出ている可能性。
	### 16.5 検証アクション（優先度順）
	- **優先度 A（即時実行）**：
		1. eval_recipe の完全照合（§15.4 A strict 3 条件、COCO mAP IoU 0.5:0.95 で計算しているかを含む）。
		2. **AP_rare / AP_common の定義をコードで確認**（train 頻度で rare 判定しているか、対象クラスリストは Skewer/Syringe の 2 クラスのみか、計算式は per-class AP の単純平均か instance-weighted か）。
		3. **per-class AP を全 15 クラスで出力**し、全体 0.618 の内訳を確認。
	- **優先度 B（数日以内）**：
		1. **論文素の VFNet vanilla config で再現実験**（長尾対策を全部 OFF にして再学習）し 45.8 付近に着地するかを検証。着地すれば長尾対策で 16pt 上がったと説明でき、ずれるなら環境・データ・eval 側の問題。
		2. **学習曲線の loss 成分を確認**（cls / bbox / iou loss の収束、9 epoch 目の jump が lr decay 起因か）。
		3. **論文著者 Fujii 氏への問い合わせ**：公開 config・学習スクリプト公開予定、エポック数の明記、以上の点を含む厳密仕様の確認。
	- **優先度 C（長期）**：
		1. 複数 seed で再実行、3-seed std を併記し 61.8 が再現するか確認。
		2. Mask DINO / Co-DETR と並走して per-class AP 分布が一貫しているか sanity check。VFNet だけ異常に高い場合は VFNet 特異な実装問題を疑う。
	### 16.6 本節と §10.1 / §15 / §8 との関係
	- **§10.1 S0 手順**：「完了判定」の記述を §16.1 の 4 条件へ書き換える修正を次ステップで適用する。
	- **§15 Lessons Learned**：本節は §15 と並ぶ「評価条件・学習設定の仮定根拠不足・再現性」のランドマークとして位置づける。今後同様の事案は §16 に蓄積する。
	- **§8.-1 eval recipe 整合性の運用規則**：本節は §8.-1 を strict に遵守する趣旨であり、§8.-1 の規則自体は変更しない。
	### 16.7 優先度 A 検証結果（2026/05/29 追加）
	§16.5 優先度 A の (1)〜(3) を実行した結果を記録する。eval_recipe の strict 3 条件はすべて PASS。ただし (i) AP_common の定義上の歪み、(ii) Forceps / Gauze の低 AP という 2 点の重要な発見があった。
	#### 16.7.1 strict 3 条件の照合結果
	- **条件 ① データ split**：train 9,657 / val 1,515 / test 4,265 images、ann 32,272 / 4,707 / 12,673 で論文 Table 3a と完全一致。**PASS**。
	- **条件 ② test_cfg**：score_thr=1e-08、max_per_img=300、nms_pre=3000、nms_iou=0.6 を確認。**PASS**。
	- **条件 ③ 評価指標**：bbox_mAP（mmdet CocoMetric が IoU 0.50:0.95 の 10 点平均で出す標準 COCO AP）を mAP にミラーし、AP_50 は別キーに併記。ヘッドライン 0.618 は AP_50 ではなくフルレンジ COCO mAP。**PASS（フルレンジ）**。
	- **§8 訓練スクリプトに関する補足**：val_evaluator の ann_file は instances_val.json、prefix='val'（mmdet_[config.py:314](http://config.py:314)-320）のため、metrics.json / per_class_ap.json はすべて val split の数値。test split は未評価（最終報告用に温存、Δ 判定は val で行う設計）。
	#### 16.7.2 AP_rare / AP_common の定義検証結果
	- **クラスリスト**：`RARE_CLASSES = ["Skewer", "Syringe"]`（2 クラスのみ、Forceps は含まない）。[constants.py:71](http://constants.py:71) と mmdet_[config.py:321](http://config.py:321)-324 でコード上確認。Forceps は 12.21% でトップ 3 の頻出クラスとして CONFUSABLE_CLASSES（§3.3 と整合）に収められている。
	- **頻度判定基準**：train 頻度（0.7% / 1.17%）。test 頻度で判定している誤りはない。
	- **計算式**：per-class AP の単純平均（macro / 非加重、`np.mean`）。再現計算で AP_rare = mean(Skewer 0.876, Syringe 0.536) = 0.706、AP_common = 残り 13 クラス平均 = 0.5566 と metrics.json 一致。
	#### 16.7.3 見つかり 1：AP_common の定義上の歪み（要修正）
	mmdet_[components.py:87](http://components.py:87) は GT 不在クラスの NaN を 0.0 に倒して AP_common に算入している。そのため Retractor（val GT 0 件）が AP=NaN→0.0 として平均に加わる。COCO 全体 mAP は GT 不在クラスを除外して平均するため、**「全体 mAP は空クラスを除外、AP_common は 0.0 で罰する」という非対称**が生じている。
	- AP_common = 0.557（現状、Retractor 0.0 を含む）、Retractor を除外した nanmean なら 0.603、全体 mAP = 0.6177 ≈ 0.618 で検証済み。
	- **影響**：Δ 判定で AP_common を使う際、Retractor が val に出ない限り全 seed・全モデルで同じ -4.6pt バイアスが乗るため、**相対比較（Δ）は保たれる**。ただし絶対値の解釈（論文記載時に reviewer から「なぜ全体 mAP より AP_common が低いのか？」と問われるリスク）と、Phase-1 で mask 入手後に Retractor が val に現れるバージョンとの比較、の 2 点で問題となる。
	- **修正方針**：
		1. mmdet_[components.py:87](http://components.py:87) を `np.nanmean` に変更して空クラスを除外し、COCO 慣行と整合させる。
		2. eval_recipe に `ap_common_aggregation` フィールドを追加し、`mean_v1`（旧）と `nanmean_v2`（新）の混在を `InconsistentRecipeError` で検出する。
		3. 過去実験（s0_004/005/006 他）は旧定義 `mean_v1` で凍結し、per_class_ap.json から `nanmean_v2` も併記するよう metrics 再計算を走らせる（再学習は不要）。
		4. 論文 Table II 脚注に「AP_common は GT 不在クラスを除外した macro 平均」と明記する。
	#### 16.7.4 見つかり 2：AP_rare \> AP_common の「赤信号」は誤警報、真の異常は Forceps / Gauze
	- **AP_rare 0.706 の中身**：Skewer 0.876 と Syringe 0.536 の平均。以前の「Skewer test 29 instances」の懸念は test split 統計に基づくものだったが、評価が走っているのは val であり、val では Skewer = 103 instances と十分なサンプル数がある。**前回の「Skewer test 29」懸念は val と test を取り違えた誤りであり、ここで訂正する**。ただし少数クラスの AP が高分散になるリスクは val 内で本当に少ない Bipolar Forceps (55) / Raspatory (76) / Syringe (96) に依然として存在し、これらは ±0.05〜0.1 規模で AP が振れうる。
	- **真の異常値**：Forceps AP 0.238（val 154 instances、データ量は十分）と Gauze AP 0.202。Forceps は Tweezers 0.687 / Needle Holders 0.812 という高 AP クラスにとられている構造であり、Gauze は非剛体のため bbox 局在が原理的に困難。**これは §2 結合効果①の根拠「形状類似ペア（Forceps / Tweezers / Needle Holders）の混同は静的視覚特徴のみでは識別困難」を実証しており、タスク結合（工程文脈→検出）で Forceps AP の改善幅に期待をもてるストーリーに整合**する。
	- **高 AP 群**：Electric Cautery 0.911 / Scalpel 0.842 / Mouth Gag 0.757 / Suction Cannula 0.733 は形状が独特で他クラスにとられにくい剛体術具であり、長尾対策と独立に高くなって自然である。
	- **Retractor = NaN**：val に GT が 0 件のため COCO が AP を定義できずに NaN を返すだけで、モデル不具合ではない。
	#### 16.7.5 12 epoch 61.8 mAP の妥当性に関する暫定結論
	- **実装ミス・評価誤りではない**：eval_recipe は strict 3 条件で論文に照合済み、評価指標は COCO mAP IoU 0.50:0.95 で AP_50 単独ではない、高 AP 群は形状が独特な剛体術具で長尾対策と無関係に高くなり自然、低 AP 群 Forceps / Gauze は構造的困難と一致、Phase 文脈の援護なしの S0 段階として妥当に低い。
	- **長尾対策の効果**：Seesaw + RFS + Copy-Paste + Logit Adjustment が Skewer/Syringe を底上げし、論文素の VFNet 45.8 を 10〜15pt 上回ること自体は仮説として受け入れられる。
	- **ただし「実装に問題がない」と確定するには §16.5 優先度 B の検証がなお必要**：
		1. (B-1) vanilla VFNet（長尾対策をすべて OFF）で 45.8 ±2pt に着地するか検証する。着地すれば長尾対策の効果が本物。
		2. (B-2) 3 seeds で std を取り、少数クラス（Bipolar Forceps / Raspatory / Syringe）の std を点検する。
		3. (B-3) 著者 Fujii 氏への問い合わせ。
		4. (C) Mask DINO / Co-DETR と並走で per-class AP 分布が一貫しているか sanity check する。
</content>
</page>
