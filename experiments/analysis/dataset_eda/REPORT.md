# EgoSurgery データセット EDA レポート

対象: `data/annotations`（生成: `experiments/analysis/dataset_eda/analyze.py`）

## 0. 規模サマリ

| データ | train | val | test | 合計 |
|---|--:|--:|--:|--:|
| 術具 画像 | 9657 | 1515 | 4265 | 15437 |
| 術具 instance | 32272 | 4707 | 12673 | 49652 |
| 手 instance | 27726 | 4918 | 13676 | 46320 |
| 工程ラベル付き frame | — | — | — | 17233 |

- 術具クラス（15）: Bipolar Forceps, Electric Cautery, Forceps, Gauze, Hook, Mouth Gag, Needle Holders, Raspatory, Retractor, Scalpel, Scissors, Skewer, Suction Cannula, Syringe, Tweezers
- 手クラス（4）: Own hands left, Own hands right, Other hands left, Other hands right
- 工程クラス（9）: anesthesia, closure, design, disinfection, dissection, dressing, hemostasis, incision, irrigation

## 1. 術具クラス分布（長尾性）

| 術具 | instance数 | 全体比 | 出現frame数 | 平均面積(px²) |
|---|--:|--:|--:|--:|
| Tweezers | 10012 | 20.2% | 9086 | 91738 |
| Gauze | 6695 | 13.5% | 5858 | 107238 |
| Forceps | 6063 | 12.2% | 3219 | 46314 |
| Mouth Gag | 5985 | 12.1% | 5982 | 270144 |
| Needle Holders | 4829 | 9.7% | 4754 | 153564 |
| Suction Cannula | 4411 | 8.9% | 4399 | 101361 |
| Scissors | 2736 | 5.5% | 2733 | 101573 |
| Retractor | 2404 | 4.8% | 1420 | 42900 |
| Electric Cautery | 1667 | 3.4% | 1659 | 181536 |
| Hook | 1349 | 2.7% | 1037 | 44361 |
| Scalpel | 1066 | 2.1% | 1065 | 117210 |
| Raspatory | 814 | 1.6% | 809 | 147578 |
| Bipolar Forceps | 696 | 1.4% | 694 | 176236 |
| Syringe | 581 | 1.2% | 564 | 62805 |
| Skewer | 344 | 0.7% | 343 | 160267 |

- **クラス不均衡比（最多/最少）= 29×**。

## 2. 工程（phase）分布

| 工程 | frame数 | 全体比 |
|---|--:|--:|
| closure | 7231 | 42.0% |
| dissection | 5799 | 33.7% |
| incision | 1170 | 6.8% |
| hemostasis | 1169 | 6.8% |
| design | 646 | 3.7% |
| anesthesia | 555 | 3.2% |
| dressing | 321 | 1.9% |
| irrigation | 217 | 1.3% |
| disinfection | 125 | 0.7% |

## 3. 術具 × 工程 共起（中核分析）

術具検出と工程ラベルが両方ある **15314 frame** で集計。

### 3a. P(術具が出現 | 工程) — 各工程で各術具が映るフレーム割合 [%]

| 術具＼工程 | anesth | closur | design | disinf | dissec | dressi | hemost | incisi | irriga |
|---|---|---|---|---|---|---|---|---|---|
| Tweezers | 3 | 71 | 10 | · | 56 | 63 | 69 | 43 | · |
| Gauze | 45 | 23 | 11 | · | 50 | 8 | 70 | 44 | 64 |
| Forceps | · | 15 | 4 | · | 33 | · | 33 | 5 | 3 |
| Mouth Gag | 28 | 49 | 32 | · | 32 | 88 | 25 | 30 | 8 |
| Needle Holders | · | 72 | · | · | · | · | · | · | · |
| Suction Cannula | 2 | 11 | · | · | 49 | 6 | 51 | 39 | 32 |
| Scissors | · | 6 | · | · | 42 | 5 | 3 | · | · |
| Retractor | · | 1 | · | · | 21 | · | 12 | 8 | 25 |
| Electric Cautery | · | · | · | · | 27 | · | 16 | · | 1 |
| Hook | · | · | · | · | 17 | · | 7 | 2 | 13 |
| Scalpel | · | · | · | · | · | · | · | 95 | · |
| Raspatory | · | 2 | · | · | 12 | · | · | · | · |
| Bipolar Forceps | · | · | · | · | · | · | 61 | · | · |
| Syringe | 95 | · | · | · | · | · | · | · | 56 |
| Skewer | · | · | 92 | · | · | · | · | · | · |

### 3b. 術具の工程特異性（エントロピー: 低いほど特定工程に集中）

| 術具 | 主要工程(P(phase\|tool)上位) | 正規化エントロピー |
|---|---|--:|
| Needle Holders | closure 100% | 0.00 |
| Skewer | design 100% | 0.01 |
| Bipolar Forceps | hemostasis 98% | 0.05 |
| Scalpel | incision 97% | 0.07 |
| Electric Cautery | dissection 89%, hemostasis 11% | 0.16 |
| Syringe | anesthesia 84%, irrigation 16% | 0.20 |
| Raspatory | dissection 81%, closure 19% | 0.22 |
| Scissors | dissection 84%, closure 15% | 0.23 |
| Hook | dissection 87%, hemostasis 8%, incision 3% | 0.24 |
| Retractor | dissection 79%, hemostasis 9%, incision 6% | 0.35 |
| Forceps | dissection 55%, closure 31%, hemostasis 11% | 0.47 |
| Tweezers | closure 52%, dissection 33%, hemostasis 8% | 0.52 |
| Suction Cannula | dissection 60%, closure 16%, hemostasis 13% | 0.53 |
| Mouth Gag | closure 54%, dissection 29%, incision 5% | 0.57 |
| Gauze | dissection 46%, closure 26%, hemostasis 13% | 0.65 |

※ エントロピー小 = その術具は特定工程に強く紐づく（= phase→detection の手掛かりが強い）。

## 4. フレーム構成

| 1frame あたり術具 instance 数 | frame数 |
|---|--:|
| 1 | 1284 |
| 2 | 4076 |
| 3 | 4318 |
| 4 | 2754 |
| 5 | 1761 |
| 6 | 637 |
| 7 | 321 |
| 8 | 119 |
| 9 | 25 |
| 10 | 15 |
| 11 | 3 |
| 12 | 1 |

- 術具が1つ以上写る frame: 15314
- 工程ラベルはあるが術具 instance が0の frame: 1919（11.1%。準備/移行など術具非依存の工程の可能性）

### 4b. 術具ペア共起（同一frame, 上位10）

| 術具ペア | 共起frame数 |
|---|--:|
| Needle Holders + Tweezers | 3719 |
| Gauze + Tweezers | 3585 |
| Mouth Gag + Tweezers | 3094 |
| Suction Cannula + Tweezers | 2292 |
| Mouth Gag + Suction Cannula | 2080 |
| Scissors + Tweezers | 2045 |
| Mouth Gag + Needle Holders | 2042 |
| Gauze + Suction Cannula | 1941 |
| Forceps + Gauze | 1900 |
| Forceps + Tweezers | 1704 |

## 5. 工程の時系列構造（動画 = clip 単位）

- clip 数: 23 / 1 clip に出現する工程数: 平均 4.8（1〜8）

### 5a. 工程の平均継続長（連続frame）

| 工程 | 平均継続frame | 出現セグメント数 |
|---|--:|--:|
| closure | 172 | 42 |
| dressing | 80 | 4 |
| dissection | 53 | 110 |
| anesthesia | 35 | 16 |
| design | 32 | 20 |
| irrigation | 27 | 8 |
| disinfection | 21 | 6 |
| incision | 20 | 59 |
| hemostasis | 19 | 62 |

### 5b. 主要な工程遷移（上位12）

| 遷移 | 回数 |
|---|--:|
| dissection → hemostasis | 57 |
| incision → dissection | 50 |
| hemostasis → dissection | 45 |
| dissection → incision | 25 |
| dissection → closure | 17 |
| anesthesia → incision | 15 |
| design → anesthesia | 12 |
| closure → dissection | 12 |
| hemostasis → closure | 8 |
| closure → incision | 8 |
| dissection → design | 6 |
| disinfection → design | 5 |

## 6. 手（hand）× 工程（補助）

- 手クラス: Own hands left, Own hands right, Other hands left, Other hands right
| 手クラス | instance数 |
|---|--:|
| Own hands left | 14043 |
| Own hands right | 13584 |
| Other hands left | 11033 |
| Other hands right | 7660 |

## 7. カバレッジ / split 整合

| split | 術具frame | 工程frame(該当split) | 両方ある |
|---|--:|--:|--:|
| train | 9657 | 9657 | 9657 |
| val | 1515 | 1515 | 1515 |
| test | 4265 | 4265 | 4265 |

### 7b. 各 split で instance 0 の術具クラス（学習/評価の偏り注意）

- train: なし
- val: Retractor
- test: なし

## 8. multitask 結合（STEP B）への含意

**(1) 術具↔工程の結合信号は強い（一部ペアはほぼ決定的）。**
  - 工程特異な術具（正規化エントロピー<0.25）: Needle Holders→closure 100%, Skewer→design 100%, Bipolar Forceps→hemostasis 98%, Scalpel→incision 97%, Electric Cautery→dissection 89%, Syringe→anesthesia 84%, Raspatory→dissection 81%, Scissors→dissection 84%, Hook→dissection 87%

**(2) 各工程の signature tool（P(tool|phase)≥50% かつ術具側も特異）:**
  - anesthesia: **Syringe**（95%）
  - closure: **Needle Holders**（72%）
  - design: **Skewer**（92%）
  - incision: **Scalpel**（95%）

**(3) 希少 ∧ 工程特異な術具（検出が難しく、かつ工程文脈が効きうる最有力ペア）:**
  - Skewer（0.7%, design 100%）, Bipolar Forceps（1.4%, hemostasis 98%）, Scalpel（2.1%, incision 97%）, Syringe（1.2%, anesthesia 84%）, Raspatory（1.6%, dissection 81%）
  - → **phase→detection 結合の最有力仮説**: 工程文脈で希少術具の検出を補助できる可能性。STEP 0-1 で Bipolar Forceps 等の希少術具が検出困難だった事実と符合。

**(4) 偏在術具（エントロピー>0.5, 工程手掛かりに乏しい）:** Gauze, Mouth Gag, Suction Cannula, Tweezers → これらは結合の恩恵が小さい想定（対照群）。

**(5) 工程は強い時系列構造を持つ（§5）:** 平均4.8工程/動画・closure が長い・dissection↔hemostasis↔incision が循環 → 時系列ヘッド（TeCNO）と工程文脈の併用が有効。

**(6) 注意点:** 工程ラベルが closure42%/dissection34% に偏在（§2）／val に Retractor 0件（§7b）／11% の frame は術具0（術具非依存の工程）。Δ 評価時の per-class・per-phase 分解が必要。
