# STEP C タスク結合の弱点分析と改善手法の提案

## 0. 目的

本書は、以下の成果物と関連実装を再検討し、検出（det）と工程認識（phase）の結合に残る弱点、解釈上の注意点、次に試すべき手法を整理したものである。

- `REPORT.md`
- `TEST_EVAL_REPORT.md`
- det→phase の tool-presence / region-token 実装
- phase→det の FiLM / cross-attention 実装
- 共有 neck による B1 MTL 実装

結論として、次に試すべき主力は以下の2本である。

1. **det→phase**: region-token を時間方向に統合し、境界予測を追加する。
2. **phase→det**: 現行 cross-attention を、複数の tool token を用いる真の query-selective conditioning に変更する。

特に2番目は重要である。現行 T1b-CA の結果だけでは、「選択的な phase→det 注入も無効」とはまだ結論できない。

---

## 1. 現時点で確立している結果

test split の結果まで含めると、以下は強く支持される。

- **det→phase の優位性は頑健**である。
- 特に T1a region-token は test macro-F1 を大きく改善する。
- 利得は hemostasis、incision、design、anesthesia など、signature tool を持つ工程に集中する。
- irrigation は region-token を用いた T1a でのみ復元された。
- phase→det の overall mAP 改善は test でも約 `+0.003` であり、実用上は小さい。
- 単純な共有 neck MTL は検出性能をほぼ維持する一方、工程認識を悪化させる。
- rich な region-token は frame classification を改善する一方、edit score を悪化させる。

最後の点が、現在の det→phase における最大の改善余地である。

---

## 2. 最重要の再解釈：現行 T1b-CA は十分に query-selective ではない

現行実装では、9次元の phase posterior を1個の token に変換している。

- `third_party/Relation-DETR/models/detectors/relation_detr_phasecrossattn.py`
- `third_party/Relation-DETR/models/bricks/relation_decoder_phaseca.py`

処理は概ね以下である。

```text
phase posterior (B, 9)
  ↓ Linear
phase token (B, 1, D)
  ↓
各 object query から cross-attention
```

しかし、attention の key/value が1 tokenだけの場合、softmax の対象は1要素なので attention weight は常に1になる。各 object query が受け取る phase 由来の value は実質的に同一であり、query ごとに異なる phase 情報を選択できない。

したがって、現行CAは次の方式ではない。

> query ごとに異なる phase/tool 情報を選択する注入

実際には次に近い。

> 全 query に同じ phase-conditioned residual を加える注入

FiLMより後段へ注入しているという違いはあるが、選択性の本質はまだ検証されていない。

よって、現行REPORTの解釈は以下のように修正するのが妥当である。

> global phase modulation は FiLM でも single-token CA でも弱かった。真の class/query-selective conditioning は未検証である。

「CAでも伸びなかったため、phase→det は機構非依存で弱い」と断定するのは現時点では早い。ただし、overall mAP が一貫して微小であるため、phase→det に割く実験回数には明確な撤退線を設けるべきである。

---

## 3. 既存手法の弱点

### 3.1 T1a は object 情報を時間的に扱い切れていない

T1a は rich な region-token を工程認識へ渡すことで、signature tool を持つ難工程を大きく改善した。一方で、フレームごとの術具出現変動へ工程予測が過敏に反応する。

考えられる原因は以下である。

- 境界付近で術具が一時的に出入りする。
- confidence や検出数がフレーム間で変動する。
- 一時的な誤検出・未検出がある。
- region-token の rich な変化が、工程変化より短い時間スケールを持つ。

その結果、以下のトレードオフが生じている。

- frame accuracy / macro-F1 は改善する。
- edit score は悪化する。
- 過分節や prediction flicker が発生する。

必要なのは、単なる「region-token と temporal model の連結」ではなく、以下の役割分離である。

- object identity / appearance: **どの工程か**
- boundary evidence: **いつ工程が変わったか**
- temporal persistence: **一時的に術具が消えても状態を保持する**

### 3.2 phase→det は class prior と localization を混同している

phase が主に与える情報は「どの術具が出現しやすいか」という class prior である。通常、phaseだけでは術具のbbox位置を推定できない。

しかし既存方式では、

- FiLM: C5特徴全体を空間一様に変調する。
- CA: decoder query全体へphase residualを加える。

という設計になっている。

これでは、phaseが有効な分類成分と、phaseがほとんど情報を持たないbox localization成分が混ざる。phase情報はまず分類枝だけへ注入し、box枝は固定する方がドメイン仮説に合っている。

### 3.3 B1の失敗には複数の要因が混在している

B1の工程劣化には少なくとも以下が混在する。

- det:phase の更新頻度が約89:1
- 単一neckの容量競合
- gradient normの差
- gradient directionの競合
- spatial detectorとtemporal phase headの表現粒度差

Kendall & Gal型の不確実性重みは主にloss scaleを調整する。更新頻度、共有容量、勾配方向の競合を直接解決しないため、B1 K&Gが失敗したことは自然である。

PCGradやCAGradを評価する前に、同一optimizer step内で両タスクの勾配を比較・統合できる学習スケジュールが必要になる。89回のdet更新と1回のphase更新を維持したままでは、勾配手術が作用する機会自体が少ない。

### 3.4 「術具信号が改善原因」とするには因果介入が不足している

signature toolと改善工程の一致は強い証拠だが、現状は相関的な機構証拠である。次の介入実験で利得源を分解すべきである。

- Bipolar tokenを消したとき、hemostasis改善が消えるか。
- tool class embeddingだけをshuffleする。
- bbox座標だけをshuffleする。
- region appearanceだけをshuffleする。
- region-token系列を時間方向にずらす。
- confidenceを固定または除去する。

これにより、T1aの利得が以下のどこから来るかを特定できる。

- class identity
- appearance
- geometry
- confidence
- temporal alignment

---

## 4. 最優先で試す手法

## 4.1 優先度1：Temporal Object-Set Fusion

T1aのregion-tokenをフレーム単位で直接利用するのではなく、object setとして集約した後に時間モデルへ渡す。

```text
各フレームのregion tokens
  ↓
Set encoder
  ↓
短期object memory / temporal attention
  ↓
TeCNO、MS-TCN++、ASFormer等
  ├─ phase分類ヘッド
  └─ boundary予測ヘッド
```

各region-tokenには、可能なら以下を含める。

- region appearance
- tool class embedding
- detection confidence
- bbox中心座標
- bbox幅・高さ
- 画面端接触・truncationフラグ
- 検出がない場合のno-object token

### 安定経路とrich経路の二経路化

B2aの15次元tool-presenceはtest accuracyでは弱かったが、時間分節ではT1aより安定していた。この性質を捨てず、rich tokenと並列に使う。

```text
安定したtool-presence経路 ─┐
                           ├─ gated residual → temporal model
rich region-token経路 ─────┘
```

presence経路は低周波で頑健な工程証拠、region経路は長尾工程を識別する高情報な証拠として扱う。

### Boundary head

現在の課題はmacro-F1ではなくedit scoreと過分節であるため、分類損失だけでは不十分である。class-agnosticな工程境界を別ヘッドで予測し、境界が低い区間ではphase遷移を抑制する。

候補は以下である。

- ASRF型のboundary regression branch
- MS-TCN++型のmulti-stage refinement
- ASFormer型の長短時間attention
- boundary-aware loss

### 成功基準

- test phase macro-F1がT1aを維持または改善
- edit scoreがS4およびT1aを上回る
- seg-F1@10/25/50がT1aを上回る
- hemostasis / incision / design / irrigationの改善を維持
- seed間分散を悪化させない

---

## 4.2 優先度2：Phase-conditioned Tool Tokens

phase→detでは、1個のglobal phase tokenではなく、tool classごとの複数tokenを生成する。

```text
phase posterior
  ↓
15個のphase-conditioned tool tokens
  ↓
各object queryが15 tokenへattention
  ↓
queryごとに異なるtool priorを選択
```

key/valueが複数になるため、初めてqueryごとに異なるattention distributionを持てる。

### より安全な最小版：classification-only phase bias

decoder全体を変更する前に、box枝を固定し、分類logitだけへzero-init residualを加える。

```text
class_logits' = class_logits + gate × zero_init_MLP(phase posterior)
boxes'        = boxes
```

ただし補正量は全クラス共通ではなく、tool classごとに異なる15次元とする。

この方式の利点は以下である。

- phaseが持つclass priorだけを利用できる。
- box localizationを壊さない。
- zero-initで既存検出器と完全に同じ状態から開始できる。
- phase signalの効果をzero/shuffle context対照で測定しやすい。

最初は以下のrareかつphase-specificな術具だけに適用する。

- Skewer
- Bipolar
- Scalpel
- Syringe

全体mAPよりも、これらのtest per-class APを主要評価項目とする。

### 成功基準

- rare∧phase-specific群のtest AP改善が全seedで同符号
- paired平均差がpaired-σを上回る
- common tool群を悪化させない
- overall mAPを非劣化に保つ
- real contextがzero/shuffled contextを上回る

---

## 4.3 優先度3：Oracle Ladder

大規模な新規実装の前に、phase→detとdet→phaseの情報上限を測定する。

### phase→det

以下を同一評価条件で比較する。

1. zero context
2. predicted phase posterior
3. shuffled phase posterior
4. GT phase one-hot
5. GT phaseと経験的 `P(tool|phase)`
6. GT tool-presence oracle

GT phaseを使ってもrare-class APが改善しなければ、phase→detから撤退できる。GT phaseのみ改善するなら、問題は結合方式ではなくphase予測誤差または較正である。

### det→phase

以下を比較する。

1. GAPのみ
2. predicted tool presence
3. GT tool presence
4. class-only region token
5. class＋bbox
6. appearanceのみ
7. appearance＋class＋bbox

このfactorial ablationによって、T1aの利得源と、必要な入力成分を特定できる。

---

## 4.4 優先度4：Soft-sharing MTL

単一neckを完全共有するのではなく、タスク別neckを保持し、小さな交換モジュールだけを学習する。

```text
frozen backbone
  ├─ detection adapter → detector
  └─ phase adapter     → temporal head
          ↑
     zero-init soft-sharing
```

候補は以下である。

### Cross-stitch

タスク別特徴の混合率を学習する。自己経路を1、他タスク経路を0で初期化すれば、単一タスク基準点を保存できる。

### NDDR

同一解像度のタスク別特徴を結合し、1×1 convolutionで再分離する。完全共有よりタスク別容量を保ちやすい。

### MTAN

共有特徴からタスク固有のattention maskを生成する。検出と工程で必要な特徴領域が異なる場合に適する。

### MTI-Net

複数スケールでtask interactionを行う。phaseへの高レベル意味情報と、detectorへの空間情報を同じ層で無理に共有しない設計が可能になる。

本プロジェクトでは、全層を共有するより、C5近傍またはadapter間だけをzero-initで交換する最小構成が適切である。

---

## 4.5 優先度5：同期MTL＋CAGrad / PCGrad

勾配手術を試す前に、以下を満たす必要がある。

- 同一optimizer stepでdet lossとphase lossを計算する。
- shared parameter上のgradient cosineを記録する。
- タスクごとのgradient normを記録する。
- 更新頻度を1:1または明示的なgradient accumulationで揃える。
- naive weighted sumを同条件の対照にする。

第一候補はCAGrad、簡易比較はPCGradとする。

- **PCGrad**: 負の内積を持つタスク勾配を射影する。
- **CAGrad**: 平均目的を維持しつつ、最も改善しにくいタスクの局所改善を考慮する。
- **FAMO**: 計算効率の高い動的重み付けだが、2タスクでは優先度を下げてよい。
- **Nash-MTL**: 原理的だが、まずCAGradより実装・計算コストが高い。

今回の「検出は維持されるが工程だけ落ちる」という状況には、CAGradの目的が比較的合っている。

---

## 5. 追加で有望な方向

### 5.1 Learned Compatibility Model

固定のphase prior乗算ではなく、phase posteriorとtool logitsの整合性を小さなenergy modelで学習する。

```text
compatibility = f(phase posterior, tool logits)
tool logits'  = tool logits + zero_init_gate × compatibility
```

zero、shuffled、GT contextを対照とし、単なる追加パラメータの効果とphase信号の効果を分離する。

### 5.2 Detector-to-phase Distillation

T1aをteacherとして、軽量なphase modelへ以下を蒸留する。

- tool-presence posterior
- region-token集約表現
- phase logits
- temporal boundary evidence

推論時に検出器を呼ばず、T1aの工程改善を保持できる可能性がある。

### 5.3 Hand / Object Interaction Channel

disinfectionやdressingのようなtool signatureが弱い工程には、術具情報だけでは限界がある。

追加候補は以下である。

- surgeon hand
- assistant hand
- hand-tool relation
- hand-field interaction
- tool motion / hand motion

これは既存det→phaseの単純拡張ではなく、現在欠けている情報軸を追加する手法である。

### 5.4 Phase-conditioned Temporal Tracking

phaseは単発bboxの位置を教えないが、toolの出現・継続・消失priorは提供できる可能性がある。

したがって、phaseをper-frame detectionへ入れるより、以下へ入れる方が理論的に整合する。

- track/query persistence
- temporal query initialization
- track confidence decay
- occlusion時のtool identity保持

phase→detを続ける場合、per-frame bbox改善よりtrackingやtemporal consistencyを評価対象にした方が有望である。

---

## 6. 推奨実験順

### 第1段階：低コストで解釈を確定

1. 現行CAをsingle-token global injectionとして再定義する。
2. phase→detのGT / predicted / shuffled / zero context oracle ladderを行う。
3. T1aのclass / bbox / appearance / confidence / temporal alignment ablationを行う。
4. det→phaseの混同行列とprediction flickerを定量化する。

### 第2段階：最も成功確率が高い改善

5. T1aへboundary headを追加する。
6. B2a presence経路とT1a region経路をgated fusionする。
7. Temporal Object-Set Fusionを実装する。

### 第3段階：phase→detの最終検証

8. classification-only phase biasを実装する。
9. 15 tool-tokenによるmulti-token cross-attentionを実装する。
10. 3-seed test per-classでrare∧phase-specific toolを評価する。

### 第4段階：共有MTLの再検証

11. dual-neck＋zero-init cross-stitchを試す。
12. 同期MTLでgradient cosine/normを測定する。
13. naive sumとCAGradを比較する。

---

## 7. 撤退基準

### phase→det

以下を全て満たさない場合、phase→detを主要改善経路から外す。

- GT phaseではrare∧phase-specific APが改善する。
- predicted phaseがzero/shuffled contextを上回る。
- multi-tokenまたはclassification-only注入が全seed同符号で改善する。
- overall mAPまたは主要common classを悪化させない。

GT phaseでも改善しない場合は、phase情報自体に検出改善能力が不足していると判断できる。

### 共有MTL

同期更新とsoft-sharingを導入しても工程が単一タスク基準を下回る場合、密な共同学習は中止し、疎結合または蒸留へ収束させる。

---

## 8. 最終提案

研究の主軸は、次に置くのが最も堅い。

> **Temporal Object-Set Fusionとboundary modelingにより、region-tokenが持つ長尾工程の分類利得を維持しながら、時間的一貫性とedit scoreを改善する。**

phase→detについては、現行single-token CAを最終結論に使うべきではない。一方でoverall改善が一貫して微小であるため、以下の2実験に限定して撤退判断するのが妥当である。

1. classification-only phase-conditioned class bias
2. multi-tool-tokenによる真のquery-selective cross-attention

この2方式とoracle ladderでも改善しなければ、本研究の結論を以下へ収束できる。

> EgoSurgeryにおけるtask couplingは強く非対称であり、object-level detection evidenceは難工程・長尾工程を改善するが、global phase contextはper-frame object detectionの局在ボトルネックを解消しない。

---

## 9. 参考文献

- Yu et al., [Gradient Surgery for Multi-Task Learning (PCGrad)](https://arxiv.org/abs/2001.06782)
- Liu et al., [Conflict-Averse Gradient Descent for Multi-task Learning](https://arxiv.org/abs/2110.14048)
- Liu et al., [FAMO: Fast Adaptive Multitask Optimization](https://arxiv.org/abs/2306.03792)
- Navon et al., [Multi-Task Learning as a Bargaining Game](https://arxiv.org/abs/2202.01017)
- Misra et al., [Cross-stitch Networks for Multi-task Learning](https://arxiv.org/abs/1604.03539)
- Gao et al., [NDDR-CNN](https://arxiv.org/abs/1801.08297)
- Liu et al., [End-to-End Multi-Task Learning with Attention (MTAN)](https://arxiv.org/abs/1803.10704)
- Vandenhende et al., [MTI-Net](https://arxiv.org/abs/2001.06902)
- Li et al., [MS-TCN++](https://arxiv.org/abs/2006.09220)
- Ishikawa et al., [Alleviating Over-segmentation Errors by Detecting Action Boundaries (ASRF)](https://arxiv.org/abs/2007.06866)
- Yi et al., [ASFormer](https://arxiv.org/abs/2110.08568)
- Ayobi et al., [Pixel-Wise Recognition for Holistic Surgical Scene Understanding / TAPIS / GraSP](https://arxiv.org/html/2401.11174v3)
- Meng et al., [Conditional DETR](https://arxiv.org/abs/2108.06152)
- Cui et al., [Learning Dynamic Query Combinations for Transformer-based Object Detection](https://proceedings.mlr.press/v202/cui23f/cui23f.pdf)

