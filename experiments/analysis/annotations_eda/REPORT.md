# EgoSurgery アノテーション EDA — ドメイン特性レポート

- 対象: `data/annotations/`（術具検出 COCO ＋ 手 COCO ＋ 工程 CSV）
- 生成: `scripts/analyze_annotations_eda.py`（実データ集計のみ。数値は捏造せず、未結合フレームはカバレッジとして明示）
- 機械可読版: `experiments/analysis/annotations_eda/stats.json`
- 行列CSV: `tool_by_phase_appearance.csv` / `phase_by_tool_distribution.csv`
- 図: `fig_tool_distribution.png` / `fig_phase_distribution.png` / `fig_tool_by_phase_heatmap.png`
- 結合キー: **COCO 画像 `file_name` の basename（拡張子無）== 工程 CSV の `Frame` 列**

---

## 0. 要約（このデータセットの性格）

1. **エゴセントリック（頭部装着）手術映像**。1920×1080、術野の接写であり、**bbox の約96%が COCO "large"**（小物体検出問題ではなく、大物体・遮蔽・モーションブラーが主課題）。
2. **強い長尾**。術具15クラスの出現は最大/最小で **29.1倍**、工程9クラスのフレーム数は **57.8倍**（closure 7,231 vs disinfection 125）。
3. **術具と工程がほぼ決定的に結合**。多くの術具が単一工程に集中（例: Skewer→design 99.7%、Syringe→anesthesia 84.2%、Scalpel→incision 97.4%、Needle Holders→closure 99.9%、Bipolar Forceps→hemostasis 98.0%）。これは本プロジェクトの中核仮説（術具⇄工程の相互改善 Δ）の**データ的根拠**。
4. **検出と工程のフレーム整合が完全**（検出フレーム 15,437 件すべてに工程ラベルが付与、未結合 0）。マルチタスク学習の前提が成立。
5. **分割は動画単位（patient-level hold-out）**。フレームリークなし。ただし split 間でクラス・工程分布が偏る（ドメインシフト）。

---

## 1. データセット全体像

### 1.1 ファイル構成
| 種別 | パス | 内容 |
|---|---|---|
| 術具検出 | `egosurgery_tool/instances_{train,val,test}.json` | COCO・**15 術具クラス** |
| 術具+手 検出 | `egosurgery_tool_hand/instances_{train,val,test}.json` | COCO・**19 クラス**（術具15＋手4） |
| 手のみ（マージ元） | `egosurgery_tool_hand/{train,val,test}.json` | 手4クラスのみ（file_name に split/video 接頭辞なし） |
| 工程 | `egosurgery_phase/<vid>_<sess>.csv` | `Frame,Phase`・**9 工程クラス**・23 セッション（動画01–15） |
| 空 scaffold | `egosurgery_hts/`, `pseudo_labels/{bbox_near_contact,exo_phase_transfer,hand_tool_relation}/` | 将来用（現状 `.gitkeep` のみ） |

### 1.2 split と規模（術具COCO）
| split | 画像数 | アノテ数 | アノ/画像 | 物理動画 | 術具なし画像 |
|---|---:|---:|---:|---|---:|
| train | 9,657 | 32,272 | 3.34 | 01,02,03,06,08,11,12,13,14,15（10本） | 39 |
| val | 1,515 | 4,707 | 3.11 | 09,10（2本） | 0 |
| test | 4,265 | 12,673 | 2.97 | 04,05,07（3本） | 84 |
| **計** | **15,437** | **49,652** | — | 15本 | 123（0.8%） |

> `video_id` フィールドは split 内連番のため、物理動画IDはファイル名から復元（上表）。
> **分割は動画（患者）単位**で、同一動画のフレームが train/val/test にまたがらない＝厳密な hold-out。

### 1.3 フレーム共起
- 1フレームあたり術具インスタンス数 平均 **約3.0**、異なる術具クラス数 平均 **約2.5–3.0**、最大 **6 クラス同時**。
- ほぼ全フレームに術具が存在（術具なしは 0.8%。主に disinfection 等の手指のみ工程）。
- → **常に複数術具が共在**する密なシーン。単一物体前提のモデルでは不利。

---

## 2. 術具 15 クラス分布（全split合算）

| 術具 | インスタンス数 | 含む画像数 | 構成比 |
|---|---:|---:|---:|
| Tweezers | 10,012 | 9,086 | 20.2% |
| Gauze | 6,695 | 5,858 | 13.5% |
| Forceps | 6,063 | 3,219 | 12.2% |
| Mouth Gag | 5,985 | 5,982 | 12.1% |
| Needle Holders | 4,829 | 4,754 | 9.7% |
| Suction Cannula | 4,411 | 4,399 | 8.9% |
| Scissors | 2,736 | 2,733 | 5.5% |
| Retractor | 2,404 | 1,420 | 4.8% |
| Electric Cautery | 1,667 | 1,659 | 3.4% |
| Hook | 1,349 | 1,037 | 2.7% |
| Scalpel | 1,066 | 1,065 | 2.1% |
| Raspatory | 814 | 809 | 1.6% |
| Bipolar Forceps | 696 | 694 | 1.4% |
| Syringe | 581 | 564 | 1.2% |
| **Skewer** | **344** | 343 | 0.7% |

- **不均衡比 = 29.1倍**（Tweezers 10,012 / Skewer 344）。希少クラス: Skewer / Syringe / Bipolar Forceps / Raspatory。
- `Forceps`・`Retractor`・`Hook` は「インスタンス数 ≫ 含む画像数」＝**1フレームに複数本**写る傾向（例: Forceps 6,063 inst / 3,219 img）。
- 図: `fig_tool_distribution.png`（対数軸の棒グラフ）。

### 2.1 bbox サイズ（COCO scale, train基準）
| size | 定義 | 件数 | 割合 |
|---|---|---:|---:|
| large | area ≥ 96² | 30,957 | 95.9% |
| medium | 32² ≤ area < 96² | 1,257 | 3.9% |
| small | area < 32² | 58 | 0.18% |

- **接写エゴ視点ゆえ術具は大きく写る**。一般物体検出の「小物体問題」ではなく、**遮蔽・truncation・手との重なり・モーションブラー**が主な難所。

---

## 3. 手 4 クラス（egosurgery_tool_hand, train）

| 手クラス | インスタンス数 |
|---|---:|
| Own hands left | 8,704 |
| Own hands right | 8,447 |
| Other hands left | 6,542 |
| Other hands right | 4,033 |

- **自分の手 / 他者（助手）の手 × 左右** を区別 — エゴセントリック手術映像に固有の構造。術者–助手の協調や **hand–tool 関係**（pseudo_labels の将来軸）に直結。

---

## 4. 工程 9 クラス

### 4.1 フレーム分布（全 CSV, 17,233 フレーム）
| 工程 | フレーム数 | 構成比 |
|---|---:|---:|
| closure | 7,231 | 42.0% |
| dissection | 5,799 | 33.7% |
| incision | 1,170 | 6.8% |
| hemostasis | 1,169 | 6.8% |
| design | 646 | 3.7% |
| anesthesia | 555 | 3.2% |
| dressing | 321 | 1.9% |
| irrigation | 217 | 1.3% |
| disinfection | 125 | 0.7% |

- **closure + dissection で約76%** を占める強い偏り（最大/最小 57.8倍）。工程認識の macro-F1 は希少工程に強く律速される。
- 図: `fig_phase_distribution.png`。

### 4.2 時間構造（アノテ済みフレーム列上のセグメント・※実時間ではない）
| 工程 | セグメント数 | 平均長 | 中央長 | 最大長 |
|---|---:|---:|---:|---:|
| closure | 42 | 172.2 | 133 | 619 |
| dressing | 4 | 80.2 | 84 | 116 |
| dissection | 110 | 52.7 | 26 | 493 |
| anesthesia | 16 | 34.7 | 35 | 79 |
| design | 20 | 32.3 | 20 | 170 |
| irrigation | 8 | 27.1 | 21 | 61 |
| disinfection | 6 | 20.8 | 17 | 44 |
| incision | 59 | 19.8 | 14 | 176 |
| hemostasis | 62 | 18.9 | 12 | 102 |

- **closure は長い連続区間**、**dissection / hemostasis / incision は細切れに反復**（dissection↔hemostasis を往復）。TCN/因果モデルの受容野設計に関わる。

### 4.3 主な工程遷移（隣接フレームの変化, 上位）
`dissection→hemostasis (57)`, `incision→dissection (50)`, `hemostasis→dissection (45)`, `dissection→incision (25)`, `dissection→closure (17)`, `anesthesia→incision (15)`, `design→anesthesia (12)` …

- 概ね手術の標準フロー（disinfection→design→anesthesia→incision→dissection⇄hemostasis→(irrigation)→closure→dressing）に沿うが、**dissection と hemostasis の往復が支配的**。

---

## 5. 術具 × 工程 結合（コア結果）

検出フレーム（15,437・工程ラベル100%付与）で集計。`C(P,T)` = 工程 P のフレームで術具 T を1つ以上含むフレーム数、`N(P)` = 工程 P の検出フレーム数、`M(T)` = 術具 T を含むフレーム数。

### 5.1 工程ごとの術具登場割合 `A = C(P,T)/N(P)`（%）
各行＝その工程フレームで各術具が写る確率。完全版は `tool_by_phase_appearance.csv`。

| 工程 (N) | Tweez | Gauze | Forcep | MouthGag | Needle | Suction | Sciss | Retr | Cautery | Hook | Scalpel | Rasp | Bipolar | Syringe | Skewer | any |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| disinfection (11) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| design (378) | 10 | 10 | 3 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **90** | 98 |
| anesthesia (499) | 3 | 46 | 0 | 29 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **95** | 0 | 100 |
| incision (1096) | 43 | 44 | 5 | 30 | 0 | 39 | 0 | 8 | 0 | 3 | **95** | 0 | 0 | 0 | 0 | 100 |
| dissection (5440) | 56 | 50 | 33 | 32 | 0 | 49 | 42 | 21 | 27 | 17 | 0 | 12 | 0 | 0 | 0 | 99 |
| hemostasis (1121) | 69 | 70 | 33 | 25 | 0 | 51 | 3 | 12 | 16 | 7 | 0 | 0 | **61** | 0 | 0 | 100 |
| irrigation (177) | 0 | 57 | 3 | 7 | 0 | 28 | 0 | 22 | 1 | 11 | 0 | 0 | 0 | 50 | 0 | 89 |
| closure (6596) | 71 | 23 | 15 | 49 | **72** | 11 | 6 | 1 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 100 |
| dressing (119) | 61 | 8 | 0 | **85** | 0 | 6 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 97 |

### 5.2 術具ごとの工程登場割合 `B = C(P,T)/M(T)`（%・各行合計≈100）
各行＝その術具が写るフレームの工程内訳。完全版は `phase_by_tool_distribution.csv`。

| 術具 (M) | disinf | design | anesth | incis | dissec | hemo | irrig | closure | dress |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Skewer** (343) | 0 | **99.7** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Syringe** (564) | 0 | 0 | **84.2** | 0 | 0 | 0 | 16 | 0 | 0 |
| **Scalpel** (1065) | 0 | 0 | 0 | **97.4** | 2 | 0 | 0 | 1 | 0 |
| **Needle Holders** (4754) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **99.9** | 0 |
| **Bipolar Forceps** (694) | 0 | 0 | 0 | 0 | 1 | **98.0** | 0 | 1 | 0 |
| **Electric Cautery** (1659) | 0 | 0 | 0 | 0 | **88.8** | 11 | 0 | 0 | 0 |
| **Hook** (1037) | 0 | 0 | 0 | 3 | **87.0** | 8 | 2 | 1 | 0 |
| **Scissors** (2733) | 0 | 0 | 0 | 0 | **83.6** | 1 | 0 | 15 | 0 |
| **Raspatory** (809) | 0 | 0 | 0 | 0 | **81.2** | 0 | 0 | 19 | 0 |
| **Retractor** (1420) | 0 | 0 | 0 | 6 | **79.4** | 9 | 3 | 2 | 0 |
| Suction Cannula (4399) | 0 | 0 | 0 | 10 | **60.0** | 13 | 1 | 16 | 0 |
| Forceps (3219) | 0 | 0 | 0 | 2 | **55.2** | 11 | 0 | 31 | 0 |
| Mouth Gag (5982) | 0 | 2 | 2 | 6 | 29 | 5 | 0 | **54.2** | 2 |
| Gauze (5858) | 0 | 1 | 4 | 8 | **46.2** | 13 | 2 | 26 | 0 |
| Tweezers (9086) | 0 | 0 | 0 | 5 | 33 | 9 | 0 | **51.6** | 1 |

### 5.3 解釈
- **準・決定的な術具→工程シグナル**（単一工程に ≥80% 集中）: Skewer→design, Syringe→anesthesia, Scalpel→incision, Needle Holders→closure, Bipolar Forceps→hemostasis, Electric Cautery/Hook/Scissors/Raspatory/Retractor→dissection。
  → 「この術具が見えれば工程がほぼ確定」。**検出→工程**転移（B2a）の上限が高いことを示唆。
- **工程シグネチャ**（工程を特徴づける術具）: design=Skewer, anesthesia=Syringe, incision=Scalpel, closure=Needle Holders（縫合）, hemostasis=Bipolar Forceps, dissection=Cautery/Hook。
- **曖昧な術具**: Tweezers / Gauze / Mouth Gag / Suction は複数工程に広く分布（汎用器具・開創保持）。工程弁別には弱い。
- **disinfection は術具0**（手指のみ）。検出特徴だけでは判別不能＝**時間文脈や手情報が必須**な工程が存在する。
- 図: `fig_tool_by_phase_heatmap.png`（登場割合ヒートマップ）。

---

## 6. ドメイン特性まとめ（網羅）

1. **モダリティ**: エゴセントリック（頭部装着カメラ）顔面手術。視点動揺・自己手遮蔽・術野接写が前提。
2. **空間**: bbox は約96%が large。**小物体問題ではなく**、遮蔽・truncation・ブラー・複数器具の重畳（最大6クラス同時）が課題。
3. **クラス長尾**: 術具29.1倍、工程57.8倍。希少術具（Skewer/Syringe/Bipolar）と希少工程（disinfection/irrigation/dressing）が評価を律速。長尾対策（RFS/copy-paste 等）の対象が明確。
4. **強い術具⇄工程結合**: 5章のとおり多くが準決定的。マルチタスク（検出×工程）で相互に効く**信号が実在**。本プロジェクトの Δ 仮説の前提が成立。
5. **完全なフレーム整合**: 検出フレーム＝工程ラベル付き（join 100%, 未結合0）。フレーム単位の結合学習・解析が無損失で可能。
6. **手構造**: 自手/他手×左右の4クラス。hand–tool 関係・術者助手協調という固有軸（pseudo_labels で将来拡張）。
7. **時間構造**: closure が長区間、dissection⇄hemostasis が反復。標準ワークフロー順だが往復遷移が支配的＝時系列モデルの受容野が重要。
8. **分割設計**: 動画（患者）単位 hold-out（train10/val2/test3本）。フレームリークなし。一方 split 間で分布が偏り**ドメインシフト**を内包（汎化評価としては妥当だが分散大）。
9. **未整備領域**: `egosurgery_hts/`・`pseudo_labels/*` は空 scaffold。HTS（hand-tool 接触）・exo→ego 工程転移・hand-tool relation は今後のデータ生成対象。

---

## 7. 研究上の含意・注意点

- **B2a（検出→工程, 信号レベル）**: 5.2 の準決定的シグナル（Scalpel/Syringe/Skewer/Needle Holders 等）から、tool-presence 15次元は工程の強い予測子。Δ_phase 改善余地は、これらが**弱い工程**（disinfection: 術具0、汎用器具中心の closure 内訳など）に限られる可能性。
- **工程の難所**: disinfection（術具0・サンプル極少 N=11）、irrigation/dressing（希少）。これらは検出特徴のみでは弁別困難＝**時間・手情報の寄与**を測る好材料。
- **評価指標**: 強い長尾のため accuracy より **macro-F1 / 希少クラス AP** を主指標にすべき（既存方針と整合）。
- **交絡注意**: split 間のクラス・工程分布差（例: val=動画09/10, test=04/05/07）が seed 横断分散に効く。Δ は paired-σ（対 seed 差）で判定する既存規約が妥当。
- **再現性**: 本レポートは `scripts/analyze_annotations_eda.py` で完全再生成可能。数値は `stats.json` が単一情報源。

---

## 8. 成果物一覧
| ファイル | 内容 |
|---|---|
| `scripts/analyze_annotations_eda.py` | 再現用解析スクリプト |
| `experiments/analysis/annotations_eda/stats.json` | 全集計値（機械可読） |
| `experiments/analysis/annotations_eda/tool_by_phase_appearance.csv` | 工程ごとの術具登場割合 [phase×tool] |
| `experiments/analysis/annotations_eda/phase_by_tool_distribution.csv` | 術具ごとの工程登場割合 [tool×phase] |
| `experiments/analysis/annotations_eda/fig_tool_distribution.png` | 術具分布（対数） |
| `experiments/analysis/annotations_eda/fig_phase_distribution.png` | 工程分布 |
| `experiments/analysis/annotations_eda/fig_tool_by_phase_heatmap.png` | 術具×工程 登場割合ヒートマップ |

---

# 追加分析（実験設計向け, 2026-06-20）

生成: `scripts/analyze_annotations_advanced.py` / 値: `stats_advanced.json` / 図: `fig_adv_*.png`。
各節末に **「どの実験判断に効くか」** を付す。

## 9. split 間の分布シフト（一般化の難しさ）

JS divergence（bits, 小さいほど類似）:
| 比較 | 術具クラス分布 | 工程分布 |
|---|---:|---:|
| train↔val | 0.063 | 0.034 |
| train↔test | 0.064 | 0.046 |
| **val↔test** | **0.133** | **0.071** |

工程フレーム数（split別・検出フレーム）:
| phase | train | val | test |
|---|---:|---:|---:|
| disinfection | **11** | **0** | **0** |
| design | 245 | 103 | 30 |
| anesthesia | 281 | 98 | 120 |
| incision | 763 | 170 | 163 |
| dissection | 3832 | 506 | 1102 |
| hemostasis | 825 | 57 | 239 |
| irrigation | 93 | **0** | 84 |
| closure | 3595 | 557 | 2444 |
| dressing | 12 | 24 | 83 |

- **致命的な評価ギャップ（Fail Loud）**: **disinfection は train のみ**（val/test に0）、**irrigation は val に0**、dressing は train で極少(12)。
  → これらの工程は val/test で **per-class 指標が定義不能 or 極端に不安定**。macro-F1 は欠損工程を 0 とみなすか除外するかで値が大きく動く。
- **val↔test の乖離(0.133)が train との乖離(0.064)より大きい** = val は test の良い代理になりにくい。
- **実験判断**: ①工程の主指標は macro-F1 だが、**欠損工程の扱いを固定**して報告する（例: 「val/test に存在する工程のみで macro-F1」を明記）。②**val でのモデル選択は test を保証しない**（val 過楽観）。③Δ_phase の seed 分散が大きいのは、希少工程の split 偏在が一因。paired-σ 判定（対 seed 差）の妥当性を裏付ける。

## 10. クラス↔動画の集中度と split カバレッジ（per-class AP の評価可能性）

| 術具 | 含む動画数 | 単一動画集中率 | train | val | test |
|---|---:|---:|---:|---:|---:|
| Electric Cautery | 8 | **0.77** | 1404 | 101 | 162 |
| Forceps | 13 | 0.49 | 2534 | 154 | 3375 |
| **Retractor** | 7 | 0.43 | 2079 | **0** | 325 |
| Hook | 6 | 0.40 | 1045 | 147 | 157 |
| Raspatory | 8 | 0.37 | 654 | 76 | 84 |
| Skewer | 9 | 0.25 | 212 | 103 | 29 |
| Mouth Gag | 5 | 0.23 | 3807 | 990 | 1188 |
| Gauze | 15 | 0.23 | 4596 | 455 | 1644 |
| （以下 max1vid<0.22, 省略。全クラス train・test には在） | | | | | |

- **全15術具は train と test に存在**（検出評価ギャップ無し＝良好）。ただし **Retractor は val に0件**（val AP 不能）。
- **Electric Cautery は77%が単一動画**・Hook/Retractor は6–7動画のみ＝**動画特異**。動画単位 hold-out では「学習で見た動画の癖」を test 動画へ一般化できるかが問われ、**これら希少・偏在クラスの test AP は分散が大きい/低くなりやすい**。
- **実験判断**: ①長尾対策（RFS・copy-paste, §既存方針）の主対象は Electric Cautery / Hook / Retractor / Raspatory / Skewer / Bipolar。②per-class AP を主張する際は「動画集中率」を併記し、単一動画依存の数値を過大評価しない。③val 依存の早期停止は Retractor 等で機能しない。

## 11. tool-presence → 工程 の予測上限（B2a の信号天井）

GT 術具プレゼンス(15次元二値)からフレーム単位で工程を経験ベイズ予測（**時間情報なし**）:
| 集合 | accuracy | macro-F1 |
|---|---:|---:|
| train（当て嵌め上限） | 0.933 | 0.675 |
| val | 0.952 | 0.646 |
| **test（汎化）** | **0.752** | **0.529** |
| test 多数決ベースライン | 0.573 | — |

相互情報量 MI(presence; phase)（bits, 上位）: Needle Holders **0.52** ≫ Scalpel 0.32 > Syringe 0.20 > Bipolar 0.18 > Scissors 0.17 > Electric Cautery 0.15。最小: Mouth Gag 0.036 / Forceps 0.061（汎用器具＝工程弁別に無力）。

- **解釈**: 「どの術具が見えるか」だけで test 75.2% / mF1 0.53 まで届く（多数決+18pt）。しかし **実測の時系列 S4 base は acc 0.899**＝**時間モデリングが瞬間プレゼンスを大きく上回る**。
- train(0.93)→test(0.75) の急落 = **同じ術具集合でも動画により工程が異なる**（プレゼンス写像は動画間で非一定）。
- **実験判断**: ①**B2a（tool-presence→工程）の純粋な追加効果は上限が限定的**で、実測 Δ_phase(B2a)=+0.038 は妥当。**T1a の region 埋め込み(+0.050)が presence(+0.038) を上回る**のは、presence の天井(75%)を超える object 特徴が効くため、と本分析が裏付ける。②工程改善の主役は**時系列**であり、検出→工程の貢献は「補完」と位置づけるのが正しい。③MI 上位術具（Needle Holders, Scalpel, Syringe, Bipolar）に絞った軽量シグナルでも大半の効果が得られる可能性（ablation 候補）。

## 12. 工程の混同度（tool 空間での区別しにくさ）

術具登場ベクトル間 cosine 類似（高いほど tool だけでは区別困難）:
| 工程ペア | cosine |
|---|---:|
| anesthesia ↔ irrigation | 0.82 |
| **dissection ↔ hemostasis** | **0.81** |
| closure ↔ dressing | 0.72 |
| dissection ↔ closure | 0.59 |
| hemostasis ↔ closure | 0.56 |

- dissection↔hemostasis（往復遷移も最多, §4.3）と anesthesia↔irrigation は **tool シグネチャが重複**＝検出特徴では分離困難。
- **実験判断**: これらのペアは**時間文脈・手情報（§14）でしか割れない**。検出→工程（B2a/T1a）の誤りはこの混同ペアに集中するはず → **混同行列をこの軸で検証**すれば、マルチタスクが「どこを」改善したかを説明できる（論文の主張強化）。

## 13. 術具共起（関係推論・多ラベル検出の素地）

frame-level 共起。**強い特異的共起（PMI 上位）**:
| ペア | PMI(bits) | 共起frame | p(B\|A) |
|---|---:|---:|---:|
| Electric Cautery + Retractor | 1.94 | 584 | 0.35 |
| Raspatory + Retractor | 1.71 | 243 | 0.30 |
| Electric Cautery + Forceps | 1.58 | 1037 | 0.63 |
| Electric Cautery + Hook | 1.48 | 311 | 0.19 |
| Hook + Scissors | 1.32 | 457 | 0.44 |

**高頻度共起（普遍的ペア）**: Needle Holders+Tweezers（3719f, p=0.78＝縫合）、Gauze+Tweezers（3585f）、Mouth Gag+Tweezers、Scissors+Tweezers（p=0.75）。

- 特異的 PMI ペアは**機能的チーム**（cautery+retractor＝展開しつつ焼灼、raspatory+retractor＝骨膜剥離＋展開）。普遍ペアは Tweezers がハブ。
- **実験判断**: ①`pseudo_labels/hand_tool_relation`・関係推論（Relation-DETR）の**正例設計**に直結（PMI 上位＝意味のある関係）。②**多ラベル検出/クエリ設計**で強相関を活用可。③Tweezers は共起ハブゆえ、その検出品質が他クラスの文脈特徴に波及（誤検出の影響大）。

## 14. 手の解析（相互作用チャネル）

工程別の手の在・hand-tool 共起:
| phase | 手あり率 | 手&術具 同時 | 平均手数 |
|---|---:|---:|---:|
| disinfection | 1.00 | 0.00 | 2.0 |
| incision | 0.70 | 0.70 | 2.0 |
| dissection | 0.70 | 0.70 | 2.1 |
| **hemostasis** | 0.74 | 0.73 | **2.4** |
| design | 0.65 | 0.63 | 1.5 |
| anesthesia | 0.56 | 0.56 | 1.6 |
| closure | 0.55 | 0.55 | 1.3 |
| irrigation | 0.53 | 0.45 | 1.5 |
| **dressing** | **0.10** | 0.08 | 0.2 |

- **disinfection は手のみ・術具0**（純手技）、**dressing は手も術具もほぼ無い**（手を引く工程）。能動工程（incision/dissection/hemostasis）は**手と術具がほぼ常時共在**（≈0.70）で hemostasis は手数最多。
- **実験判断**: ①§11 で tool だけでは天井 75% だった分の一部は **手情報で補える**（特に disinfection＝tool 0 は手でしか判別不能、dressing＝両方ほぼ無し）。**手枝を足す多タスク**の価値が定量化された。②`hand_tool_relation` 疑似ラベルは能動工程（共起0.70）に密に作れる。

## 15. bbox 幾何・データ品質（検出設計・健全性）

- **中心バイアス弱い**: bbox 中心 中央値 (0.54, 0.52)＝ほぼ中央だが、中央 1/3×1/3 領域に入るのは **28%** のみ＝術具は**画面全体に分布**（エゴ視点で手・術具が周縁から入る）。→ 中心前提の anchor/query 設計は不利。中心バイアス前提を置かない。
- **truncation が多い**: **34.3%(17,010/49,652) の bbox が画像端に接触**＝部分可視。→ 切れた術具のロバスト検出が要。NMS/AP 評価でも truncated box の扱いに注意。
- **品質は良好**: 退化 bbox(w/h≤0) 0件、枠外 0件、iscrowd 0件。
- **時間解像度が高い**: 工程アノテの連続フレーム間隔は **stride=1（中央値・最頻・p90 すべて1）**＝ほぼ全フレーム連続ラベル。→ **TCN/因果モデルの時間文脈は密に供給可能**（時系列が効くという §11 の結論と整合）。

## 16. 実験への示唆（要点）

1. **工程評価の規約固定**: disinfection(=train専用)・irrigation(=val欠)・dressing(=train極少) のため、macro-F1 は「対象 split に存在する工程のみ」で算出し**欠損工程の扱いを明記**。val でのモデル選択は test を保証しない。
2. **検出→工程の位置づけ**: tool-presence の天井は test 75%（時系列 S4 base 90% 未満）。B2a の +0.038 は妥当で、**主役は時系列・検出は補完**。T1a(region) が presence を超えるのは天井超えの object 特徴ゆえ（本分析が説明）。
3. **長尾の主対象**: Electric Cautery/Hook/Retractor/Raspatory/Skewer/Bipolar（希少 or 動画特異）。per-class AP は動画集中率併記で過大評価を回避。Retractor は val 評価不能。
4. **混同の所在**: dissection↔hemostasis, anesthesia↔irrigation が tool では割れない → マルチタスク/時系列/手の効果はここで検証。
5. **関係・手チャネル**: PMI 上位（cautery+retractor 等）と能動工程の手-術具共起(≈0.70)は、関係推論・hand_tool_relation 疑似ラベル・手枝多タスクの具体的素地。

## 17. 追加成果物
| ファイル | 内容 |
|---|---|
| `scripts/analyze_annotations_advanced.py` | 追加分析の再現スクリプト |
| `experiments/analysis/annotations_eda/stats_advanced.json` | 追加分析の全集計値 |
| `experiments/analysis/annotations_eda/class_video_coverage.csv` | クラス↔動画 集中度・split カバレッジ |
| `experiments/analysis/annotations_eda/fig_adv_center_bias.png` | bbox 中心分布 |
| `experiments/analysis/annotations_eda/fig_adv_cooccurrence_pmi.png` | 術具共起 PMI ヒートマップ |
| `experiments/analysis/annotations_eda/fig_adv_phase_split.png` | split 別 工程分布 |

---

# 追加分析 第2弾（疑似ラベル前段・時間構造・実務パラメタ, 2026-06-20）

生成: `scripts/analyze_annotations_extra.py` / 値: `stats_extra.json` / 図: `fig_ext_*.png`。

## 18. 手–術具の空間接触（bbox_near_contact / hand_tool_relation の前段）

19クラス COCO（手+術具の box が同一フレームに併存）で、各術具 box と手 box の IoU・中心距離を集計。
- **術具 box の 56.1% が手と重なる**（IoU>0.1）、**59.6% が近接**（中心距離 < 0.15×対角）。平均 max-IoU=0.16、中心距離中央値=0.13×対角。
- 工程別の「手-術具接触フレーム率」:

| phase | 接触率 |
|---|---:|
| hemostasis | 0.96 |
| dissection | 0.94 |
| incision | 0.94 |
| design | 0.85 |
| anesthesia | 0.84 |
| irrigation | 0.83 |
| closure | 0.83 |
| dressing | 0.80 |

- **実験判断**: 空 scaffold の **`pseudo_labels/bbox_near_contact`・`hand_tool_relation` は生成可能性が高い**（過半の術具が手と接触/近接）。能動工程（hemostasis/dissection/incision ≈0.95）で特に密に正例が作れる。接触しきい値は IoU>0.1 or 中心距離<0.15対角が妥当な初期値。図 `fig_ext_hand_tool_iou.png` / `fig_ext_contact_by_phase.png`。

## 19. 工程の時間予測性（時系列が主役であることの裏付け）

工程系列（全17,233フレーム, 連続）上で:
- **自己遷移率 = 0.982**（隣接フレームは98.2%が同一工程）、**境界フレーム率 = 3.5%**。
- **1次マルコフ「次フレーム」予測精度 = 0.982**（＝最尤遷移は常に「現状維持」）。

- **解釈**: フレーム単位の工程は**極めて粘性**。直前工程を据え置くだけで98%（GT前提・上限）。§11 で tool-presence のみの予測上限が test 75% だったのに対し、**時系列の連続性こそが工程認識の支配的シグナル**であり、実測 S4 base 0.899 はこの時間的滑らかさを利用している。
- **実験判断**: ①工程の誤りは**境界(3.5%)に集中**するはず → マルチタスク(検出→工程)の改善余地も境界・曖昧工程に限定的。混同行列を「境界 vs 内部」で分けて評価すると効果が見える。②TCN の役割は平滑化が大きく、検出シグナルは「いつ切り替わるか」の補助。

## 20. シーンテンプレート（検出クエリ設計・解釈性）

フレームの術具集合（363通り）。**ラベル濃度分布**（1フレームの異種術具数）:
| #class | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|---:|
| frames | 123 | 1490 | 4539 | 5310 | 2825 | 1076 | 74 |

**頻出術具セット（上位）**:
| frames | 主工程(占有) | 術具セット |
|---:|---|---|
| 1257 | closure(1.00) | Needle Holders + Tweezers（縫合） |
| 800 | closure(1.00) | Mouth Gag + Needle Holders + Tweezers |
| 552 | closure(0.80) | Mouth Gag + Tweezers |
| 535 | closure(1.00) | Mouth Gag + Needle Holders |
| 428 | closure(1.00) | Gauze + Needle Holders + Tweezers |
| 301 | dissection(0.99) | Mouth Gag + Scissors + Suction Cannula + Tweezers |

- **実験判断**: ①1フレーム最大6クラス・中央値3 → 検出ヘッドの **query/slot は十分(例 100 query)で過不足なし**、多ラベル前提が必須。②頻出セットは**工程をほぼ一意に決める**（closure 系セットは占有1.0）→ セット単位の弱教師・解釈に使える。図 `fig_ext_cardinality.png`。

## 21. 工程順序の動画間一貫性（全域工程事前分布の妥当性）

canonical 順 `disinfection→design→anesthesia→incision→dissection→hemostasis→irrigation→closure→dressing` に対する**遵守率（中央フレーム位置で判定）= 0.943**。
- 最も崩れるペア: **irrigation の位置**（design<irrigation 0.80, anesthesia<irrigation 0.83, hemostasis<irrigation 0.83）＝irrigation は工程途中に複数回挿入され順序が可変。design<anesthesia 0.85 等は軽微。
- **実験判断**: 手術ワークフロー順は **94% 一貫**＝**単調順序事前/因果マスクは概ね妥当**。ただし irrigation は例外（割り込み）として扱う。順序事前を使うモデル（例 SKiT/順序制約）は irrigation に注意。

## 22. 手の左右/自他 × 工程（エゴ相互作用構造）

各工程フレームでの手クラス在率:
| phase | Own L | Own R | Other L | Other R | any_own | **any_other(助手)** |
|---|---:|---:|---:|---:|---:|---:|
| disinfection | 1.00 | 1.00 | 0.00 | 0.00 | 1.00 | **0.00** |
| design | 0.91 | 0.97 | 0.27 | 0.17 | 0.99 | 0.38 |
| anesthesia | 0.94 | 0.86 | 0.52 | 0.38 | 0.97 | 0.53 |
| incision | 0.89 | 0.90 | 0.66 | 0.46 | 0.96 | 0.72 |
| dissection | 0.94 | 0.91 | 0.69 | 0.56 | 0.98 | **0.83** |
| hemostasis | 0.96 | 0.91 | 0.76 | 0.54 | 0.99 | **0.84** |
| irrigation | 0.76 | 0.89 | 0.73 | 0.73 | 0.94 | **0.89** |
| closure | 0.87 | 0.84 | 0.63 | 0.35 | 0.96 | 0.67 |
| dressing | 0.70 | 0.78 | 0.25 | 0.13 | 0.90 | 0.30 |

- 術者の手（own）はほぼ常時(0.9–1.0)。**助手の手（other）は能動工程で急増**（dissection 0.83 / hemostasis 0.84 / irrigation 0.89）、design/dressing/disinfection で低い（0–0.38）。
- **実験判断**: **助手手の在/不在は工程の補助シグナル**（能動 vs 準備/撤収を弁別）。§19 の境界曖昧性の一部を手情報が補える可能性。two-operator の hand_tool_relation 設計に直結。

## 23. 推奨クラス重み（損失重み・RFS 閾値の出発点）

effective-number (β=0.999, 平均1に正規化):
- **術具**: Skewer 2.36 / Syringe 1.56 / Bipolar 1.37 / Raspatory 1.24 / Scalpel 1.05 / Hook 0.93 / … / Tweezers 0.69。
- **工程**: disinfection 2.88 / irrigation 1.73 / dressing 1.23 / anesthesia 0.79 / design 0.71 / incision 0.49 / hemostasis 0.49 / dissection 0.34 / closure 0.34。

- **実験判断**: そのまま CE/focal の class weight や RFS の希少判定に投入できる初期値。**ただし §9–§10 の評価ギャップ（disinfection=train専用, Retractor=val欠）と併せて使う**こと（重み付けと評価可能性は別問題）。

## 24. 工程別の術具スケール ＋ 検出難易度プロキシ

工程別 平均術具相対面積(%): dressing **13.2** > design 9.6 > closure 8.4 > incision 7.3 ≈ irrigation 7.2 > hemostasis 6.5 ≈ dissection 6.5 > anesthesia 5.4。
検出難易度プロキシ（rel-area IQR / aspect IQR / 画像あたり平均本数）抜粋:
| 術具 | rel-area IQR(%) | aspect IQR | inst/img |
|---|---|---|---:|
| Electric Cautery | 4.9–13.9 | 1.39–5.16 | 1.0 |
| Skewer | 3.4–14.2 | 0.86–2.32 | 1.1 |
| Scalpel | 3.1–8.8 | 0.71–2.55 | 1.0 |
| Hook | 0.9–4.2 | 0.30–1.48 | 1.3 |
| Gauze | 2.7–8.7 | 0.79–1.46 | 1.4 |
| Tweezers | 2.1–8.1 | 0.81–2.97 | 1.5 |

- **実験判断**: **Electric Cautery / Skewer / Scalpel は縦横比の振れが大きく（細長く回転）スケール幅も広い → 局在化が難しい**。anesthesia は術具が小さく写り、dressing/design は大きい（接写）。アンカー/クエリのスケール多様性、回転にロバストな特徴が要。Hook/Gauze/Tweezers は複数本共起しやすい（NMS 設計）。

## 25. 検出アノテ無しの工程フレーム（合同学習で使えるフレーム量）

- 工程ラベル付き **17,233** に対し検出アノテは **15,437** → **1,796 フレームは工程のみ**（検出 box 無し）。
- 内訳: closure 635 / dissection 359 / design 268 / dressing 202 / **disinfection 114** / incision 74 / anesthesia 56 / hemostasis 48 / irrigation 40。
- 特に **disinfection は検出側11に対し工程側125**（114が検出無し）＝**術具不在ゆえ検出アノテが構造的に希薄**。
- **実験判断**: ①工程枝は検出より多いフレームを使える → **検出特徴を入力にする結合（B2a/T1a）は1,796枚で特徴が欠ける**点に注意（GAP/region 抽出時に空フレーム処理を明示）。②これらは**半教師（工程のみ）**の候補。③disinfection は検出からはほぼ学べない＝**時間・手情報で拾う工程**。

## 26. 第2弾の実験示唆（要点）

1. **疑似ラベル**: 手-術具接触は過半（56%重なり/60%近接, 能動工程≈0.95）→ `bbox_near_contact`・`hand_tool_relation` は生成可。閾値 IoU>0.1 / 中心距離<0.15対角。
2. **時系列が主役**: 自己遷移98.2%・境界3.5%。検出→工程の効きは境界・曖昧工程に局在。評価は「境界 vs 内部」で分解推奨。
3. **順序事前は妥当（94%）**だが **irrigation は割り込み**で例外扱い。
4. **助手手は能動工程の補助シグナル**（other 在率 0.83–0.89）。
5. **実務パラメタ**: §23 の effective-number 重みを loss/RFS 初期値に。§24 で Cautery/Skewer/Scalpel が局在困難と判明。
6. **合同学習のフレーム差**: 工程のみ1,796枚（disinfectionは検出ほぼ無）→ 結合入力の空フレーム処理と半教師の余地。

## 27. 第2弾 成果物
| ファイル | 内容 |
|---|---|
| `scripts/analyze_annotations_extra.py` | 第2弾 再現スクリプト |
| `experiments/analysis/annotations_eda/stats_extra.json` | 第2弾 全集計値 |
| `experiments/analysis/annotations_eda/fig_ext_hand_tool_iou.png` | 手-術具 IoU 分布 |
| `experiments/analysis/annotations_eda/fig_ext_contact_by_phase.png` | 工程別 接触率 |
| `experiments/analysis/annotations_eda/fig_ext_cardinality.png` | ラベル濃度分布 |
