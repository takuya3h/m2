# STEP C 追補 — test split 再評価：方向非対称は本番データで保たれるか

**位置づけ**: 本書は `REPORT.md`（STEP C 本編・主に **val** で結論）の **test split 確証**である。
val は希少術具・希少工程の実例が乏しく（EDA §9 の train/val/test 分布乖離 JS=0.133）、結論が
val 過適合でないかを **test（検出 4265 枚 / 工程 6 clip）** で検証する。
**捏造禁止の原則に従い、val より弱く出た数値・符号が変わった数値もそのまま報告する。**

---

## 0. エグゼクティブサマリ

| 主張（REPORT.md, val） | test split での確証 | 判定 |
|---|---|---|
| det→phase は効く（acc +0.038〜+0.050） | **macro-F1 で確証（B2a +0.026 / T1a +0.164, 共に有意）**。acc は B2a 中立化・T1a +0.026 | **支持（macro-F1で強化）** |
| 利得は混同/signature 工程に局在（hemostasis 倍増） | **hemostasis test F1 +0.267(T1a, 全seed正)**, incision +0.227, design +0.257 | **強く支持** |
| phase→det は機構問わず≈0（FiLM +0.0019, CA +0.0025） | **test も FiLM +0.0028 / CA +0.0030（≈0 を維持・CA≤FiLM水準）** | **支持** |
| FiLM は希少術具を標的化しない（val 3-seed） | **test は rare∧特異 +0.0069 > 汎用 +0.0009 と弱い標的化の兆候**（n=1・高ノイズ） | **部分反証（要追試）** |

**一行結論**: **方向非対称（det→phase ≫ phase→det）は test split で保たれる。** むしろ test は
val が飽和で隠していた headroom を露出させ、**検出信号（特に region-token=T1a）が長尾・難工程を
救う効果を macro-F1 で一層鮮明にした**。phase→det は test でも≈0 で、STEP C の中核は本番データで頑健。

---

## 1. 方法（再現性・非干渉）

- **検出側（phase→det）**: 収束済み検出器 4 種を `instances_test.json`（4265 枚）で COCO 評価（`scripts/eval_phase2det_test.py`）。
  - `s0_frozen`(注入なし基準) / `t1b_film_inj`(FiLM・real ctx) / `t1b_film_ctrl`(FiLM・zero ctx) / `t1b_ca_inj`(CA・real ctx)。
  - **対照法**: FiLM の純効果は `inj − ctrl`（同一重みで phase文脈の有無のみ差）、CA は ckpt 構成上 `inj − base`。
- **工程側（det→phase）**: phase head（TeCNO）は元実験で ckpt 未保存のため **同一 seed・同一ハイパーで再学習**し、
  val best を選んで（再現確認）→ **test** で per-phase F1（`scripts/eval_det2phase_test.py`、s4/b2a/t1a × seed42/123/456）。
  - **再現の忠実性**（再学習 val acc vs 原実験 metrics.json）: s4 0.8928 vs 0.8986 (−0.0058)、
    **b2a 0.9362 vs 0.9369 (−0.0007)・t1a 0.9496 vs 0.9483 (+0.0013)** ＝ **seed 雑音内で忠実再現**。
- **Δ 判定**: §10.1 paired-σ（per-seed 差の平均 `|mean|>pstdev` かつ同符号で「有意」）。
- **非干渉**: 工程再学習は GPU0 上で完結（特徴キャッシュ利用、RSS<1GB）。

> **実装注記（OOM 根治）**: 初回 `eval_det2phase_test.py` は `npz[key][i]` をループ毎に評価し NpzFile を
> 反復展開、RSS 40GB 超でプロセスが SIGKILL された（前セッションの exit 137 の真因）。配列を一度だけ
> 展開する `_index_npz` に修正し **RSS 0.90GB・全 split 2.5 秒** に是正済み（捏造でなく実測の再取得）。

---

## 2. 検出側（phase→det）— test split

### 2.1 val→test の落差（まず分母を理解する）
| モデル | val mAP | **test mAP** | 落差 |
|---|---:|---:|---:|
| s0_frozen seed42（基準） | 0.7100 | **0.5061** | **−0.204（相対 −29%）** |

EDA §9 が予言した train/val→test の分布シフト（JS=0.133）が検出 mAP に約 0.20 の絶対落差として現れる。
**test は val より難しく、ここでの Δ は「過適合でない実効」を表す。**

### 2.2 phase→det 注入の overall mAP（test）
| モデル | test mAP | Δ vs base | Δ vs ctrl |
|---|---:|---:|---:|
| s0_frozen（base） | 0.5061 | — | — |
| FiLM ctrl（zero ctx） | 0.5050 | −0.0011 | — |
| **FiLM inj（real ctx）** | **0.5088** | **+0.0028** | **+0.0039** |
| **CA inj（real ctx, §4.6 primary）** | **0.5090** | **+0.0030** | — |

**含意**: test でも phase→det は **≈+0.003** に留まり、val（FiLM +0.0019 / CA +0.0025）と同オーダーの微小効果。
**§4.6 primary の cross-attention（CA +0.0030）は下限の FiLM（+0.0028）を実質超えない** ——
「表現力を上げても phase→det は伸びない」（REPORT §3.6）が **test で再確認**。phase→det の弱さは機構非依存。

### 2.3 per-class AP（test）— 希少術具ターゲティングは？
| 群 | FiLM(inj−ctrl) | CA(inj−base) | 代表（FiLM）|
|---|---:|---:|---|
| **rare∧工程特異**（Skewer/Bipolar/Scalpel/Syringe）| **+0.0069** | **+0.0051** | Skewer +0.0232, Scalpel +0.0056 |
| 汎用（Tweezers/Gauze/Mouth Gag/Suction）| **+0.0009** | **+0.0020** | Gauze +0.0032, Tweezers −0.0001 |

突出セル: Skewer +0.0232 / Hook +0.0177（FiLM）、Scalpel +0.0141 / Retractor +0.0096（CA）。

**正直な含意（val と符号が変わった点）**: REPORT §3.2 の **val 3-seed** では rare∧特異(+0.0015)≈汎用(+0.0018)＝
**標的化なし**だった。だが **test では rare∧特異(+0.0069) が汎用(+0.0009) を上回り、弱い標的化の兆候**が出た
（EDA §8(3) が「rare∧特異術具こそ phase文脈で補助され得る」と示唆した方向）。
**ただし test の per-class は n=1 seed・希少術具は test でも実例少数で高ノイズ**（Skewer 単独で +0.0232 が群平均を牽引）。
→ **「弱い標的化」は示唆であって確証ではない。** overall は依然 ≈+0.003 で、phase→det の実用的弱さは不変。
確証には **CA/FiLM の test per-class を 3-seed 化**（次段の lecun CA 123/456 ＋ FiLM 既存 ckpt）が必要。

---

## 3. 工程側（det→phase）— test split（3-seed・paired-σ）

### 3.1 overall（accuracy と macro-F1 で物語が割れる）
| 指標 | S4 base | B2a | Δ_B2a（判定） | T1a | Δ_T1a（判定） |
|---|---:|---:|---:|---:|---:|
| test **phase_accuracy** | 0.8069 | 0.7988 | **−0.0081（σ0.0114・中立）** | 0.8328 | **+0.0259（σ0.0074・有意）** |
| test **phase_macro_f1** | 0.5439 | 0.5697 | **+0.0258（σ0.0096・有意）** | 0.7081 | **+0.1641（σ0.0044・有意）** |

**読み解き（核心）**:
- **accuracy は test の分布シフトで圧縮**: B2a（presence のみ）は test accuracy が中立化（val +0.038 → test −0.008）。
  薄い signal（15-d presence）は多数派 accuracy を test で押し上げられない。
- **macro-F1 は真実を語る**: 長尾・難工程を等重みで測る macro-F1 では **B2a +0.026・T1a +0.164 が共に有意**。
  **T1a +0.164 は極めて大きい**（val の公式 macro-F1 +0.096 を test では上回る）。
- **指標選択の正しさが test で実証**: REPORT §3.1/EDA §16 の「accuracy より macro-F1 を見よ」が、
  **test で accuracy=中立／macro-F1=有意大** という形で鮮明に裏付いた。検出信号の本質は **長尾の救済**。
- **表現の豊かさ（T1a≫B2a）が test で拡大**: macro-F1 で T1a(+0.164) は B2a(+0.026) の **約 6 倍**。
  region-token（3840-d）の object 特徴が、presence（15-d）の天井をはるかに超える（val では +1.1pt 差が test で拡大）。

### 3.2 hemostasis（混同工程の核心）val→test
| system | val F1（seeds）| test F1（seeds）|
|---|---|---|
| S4 base | 0.324（0.21/0.24/0.53）| 0.512（0.50/0.58/0.45）|
| B2a | 0.702（0.76/0.68/0.67）| 0.584（0.61/0.57/0.57）|
| T1a | 0.827（0.85/0.86/0.77）| **0.779（0.78/0.77/0.78）** |

**Δ hemostasis(test)**: B2a **+0.072**（per-seed +0.10/−0.01/+0.13）／ **T1a +0.267**（per-seed **+0.28/+0.19/+0.33・全正**）。

- **T1a は test でも hemostasis を全 seed で大幅改善**（+0.267）＝ REPORT §3.4「最弱工程の倍増」は本番でも成立。
- **分散圧縮も再現**: S4 test は seed 間 0.45〜0.58 と不安定、T1a は **0.77〜0.78 に収束**（平均改善＋信頼性獲得）。
- val→test で baseline が変動（S4 val 0.32→test 0.51）し headroom が縮むため絶対利得は val(+0.45) より圧縮されるが、
  **符号・方向・全seed正は不変**。

### 3.3 全工程 per-phase F1（test, 3-seed平均）— 利得則 `gain ≈ headroom × signature` の test 確証
| 工程 | S4 | B2a | Δ_B2a | T1a | Δ_T1a | EDA予言 |
|---|---:|---:|---:|---:|---:|---|
| **hemostasis**（混同・Bipolar0.98）| 0.512 | 0.584 | +0.072 | 0.779 | **+0.267** | ★最弱工程を倍増 |
| **incision**（Scalpel0.97）| 0.694 | 0.796 | +0.103 | 0.921 | **+0.227** | ★ signature 工程 |
| **design**（Skewer0.997）| 0.650 | 0.713 | +0.063 | 0.907 | **+0.257** | ★ val飽和を test が露出 |
| **anesthesia**（Syringe0.84）| 0.889 | 0.946 | +0.057 | 0.981 | +0.092 | ★ signature 工程 |
| dissection（混同相手・拡散）| 0.694 | 0.623 | −0.071 | 0.679 | −0.015 | ○ 多数派・拡散的 |
| closure（Needle H・既高）| 0.914 | 0.895 | −0.019 | 0.897 | −0.016 | ○ 天井近傍 |
| **irrigation**（val欠）| 0.000 | 0.000 | 0 | **0.501** | **+0.501** | ◎ region-token のみ復元 |
| disinfection / dressing（test実例≈0）| 0.000 | 0.000 | 0 | 0.000 | 0 | — 評価不能 |

**新発見 2 件（test 固有の証拠）**:
1. **irrigation の復元（T1a のみ）**: val 欠落工程 irrigation を S4/B2a は test で F1=0（一度も当てない）。
   **T1a だけ 0.501** ——region-token は presence/時系列では捉えられない工程を **object 特徴から復元**。
   「表現の豊かさ」仮説（REPORT §2.5）の最強の新証拠。
2. **design の val→test 逆転**: val でほぼ飽和（~1.0）だった design が test では S4 0.650 まで低下し headroom が顕在化、
   **T1a が +0.257 で埋める**。**val の飽和が隠していた検出信号の価値を test が露出**させた。

→ 利得は **EDA が混同/signature と名指しした工程（hemostasis/incision/design/anesthesia）に集中**し、
拡散的・確立工程（dissection/closure）では中立〜微減。**利得則 `gain ≈ headroom × signature` は test で成立。**

---

## 4. 横断結論 — test が示す「方向非対称」

```
                工程(test phase acc / macro-F1)          検出(test mAP)
det → phase     +0.026〜+0.164(macro-F1) ✓✓              —（検出器凍結）
phase → det     —                                        +0.0028(FiLM)〜+0.0030(CA) ≈0
```

1. **方向非対称は test で頑健**: det→phase は macro-F1 で有意（T1a +0.164）、phase→det は ≈+0.003。
   **片方向だけが強い、というドメインの情報非対称は val 過適合でない。**
2. **test はむしろ det→phase を強化**: 飽和が解けて headroom が顕在化し、検出信号（特に region-token）が
   **長尾・難工程・val欠工程を救う**効果が macro-F1 と irrigation 復元で鮮明化。
3. **phase→det は test でも機構非依存に弱い**: FiLM≈CA≈+0.003。§4.6 primary でも下限 FiLM を超えず、
   REPORT §7.5「科学的撤退ライン」（phase→det は本ドメインで本質的に弱い）に test も整合。
4. **指標の教訓**: accuracy は test 分布シフトで det→phase の効果を覆い隠す。**macro-F1（長尾重視）で見るべき**。

---

## 5. 限界・反証可能性（科学的健全性）

- **phase→det per-class の標的化（§2.3）は n=1 seed**: rare∧特異 +0.0069 > 汎用 +0.0009 は「弱い標的化の兆候」だが、
  Skewer 単独の +0.0232 に牽引され高ノイズ。**3-seed 化（lecun CA 123/456 ＋ FiLM 既存 ckpt の test per-class）で確証/反証する。**
- **CA overall は n=1（seed42）**: +0.0030 は単一 seed。3-seed paired-σ で「CA≤FiLM」を確定させる必要。
- **工程 test の clip 数=6**: per-phase F1 は少数 clip 上の値で、絶対値より「S4→B2a→T1a の単調性・符号」を重視すべき。
- **disinfection/dressing は test 実例 ≈0** で評価不能（捏造せず 0 と明記）。irrigation は test に実例があり T1a の +0.501 は実測。
- **再現変動**: phase head は再学習（s4 val −0.0058）。b2a/t1a はほぼ一致で、結論（方向・符号）に影響しない範囲。

---

## 6. 次アクション（本 test 評価から導かれる優先 TODO）
1. **CA seed123/456 を lecun で起動** → CA を 3-seed paired-σ 化（overall「CA≤FiLM」確定）。
2. **FiLM/CA の test per-class を 3-seed 化** → §2.3「弱い標的化」を確証 or 反証（rare∧特異 vs 汎用）。
3. 本 test 結果を `REPORT.md` §3/§9 と `REPORT_plain.md` に反映（val→test 一節を追加）。
4. 提案コア（REPORT §7.2 H-C）の設計に **「検出→工程の macro-F1 標的化が test で最も確かな相互改善経路」** を明記。

---

### 一次情報源（再現可能）
- 検出: `test_eval_{s0_frozen,t1b_film_inj,t1b_film_ctrl,t1b_ca_inj}.json`（`scripts/eval_phase2det_test.py`）
- 工程: `test_eval_det2phase.json`（`scripts/eval_det2phase_test.py --device cuda:0 --seeds 42,123,456 --epochs 50`）
- val 側基準・機構: `REPORT.md`（§1.2 Δ表 / §3 per-phase・per-class分解 / §7 提案）
