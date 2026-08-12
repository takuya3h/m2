## 11. サーベイ結果 {toggle="true"}
	§10 のサーベイロードマップに基づき、2023 年〜2026 年 5 月の最新研究動向を調査した。22 細目のサーベイが完了。各サーベイの詳細は以下の子ページを参照。
	<page url="https://app.notion.com/p/368ee4d47777813e893be630ef77b9a7">§12.1 A1：open surgery 映像解析</page>
	<page url="https://app.notion.com/p/368ee4d4777781639fa9e38099748937">§12.2 A2：手術映像解析（腹腔鏡・内視鏡以外）</page>
	<page url="https://app.notion.com/p/368ee4d47777814db929d669de17fd8c">§12.3 A4：多視点手術映像 / Ego–Exo learning</page>
	<page url="https://app.notion.com/p/368ee4d477778145875bf53ad42a4573">§12.4 B1：物体検出（汎用）</page>
	<page url="https://app.notion.com/p/368ee4d4777781758912e5e2aa0c1f7e">§12.5 B5：工程認識（Phase Recognition）</page>
	<page url="https://app.notion.com/p/368ee4d477778106ac9efb750b05566d">§12.6 B8：手-術具関係認識（Hand-Tool Relation）</page>
	<page url="https://app.notion.com/p/368ee4d4777781a3aebdf39aad8d3ca7">§12.7 C6：マルチタスク学習（Multi-Task Learning）</page>
	<page url="https://app.notion.com/p/368ee4d477778141803ee9543b053265">§12.8 E3：自己教師あり学習（SSL）</page>
	<page url="https://app.notion.com/p/368ee4d477778168bcb7ef858c877971">§12.10 B2：術具検出（Surgical-specific Instrument Detection）</page>
	<page url="https://app.notion.com/p/368ee4d47777810d9879e6aa6ba2945b">§12.11 B3：手検出・手姿勢推定（Hand Detection & Pose Estimation）</page>
	<page url="https://app.notion.com/p/368ee4d477778198b022f5306622ab7f">§12.12 B4：セグメンテーション（Instance / Semantic / Panoptic Segmentation）</page>
	<page url="https://app.notion.com/p/368ee4d4777781a38647df4b4617698e">§12.13 B7：HOI（Human-Object Interaction Detection）</page>
	<page url="https://app.notion.com/p/368ee4d47777812aa1c0f321b2d275a6">§12.14 C1：空間 backbone（Spatial Backbone）</page>
	<page url="https://app.notion.com/p/368ee4d4777781b7ae14d7935af236df">§12.15 C3：時系列モデル（TCN / Transformer / SSM-Mamba）</page>
	<page url="https://app.notion.com/p/368ee4d47777819890c1f2de4633c654">§12.16 D1：短期時間モデリング（Short Clip Modeling）</page>
	<page url="https://app.notion.com/p/368ee4d4777781269287e50faa6199d0">§12.17 D2：長距離時間文脈（Long-Range Temporal Context）</page>
	<page url="https://app.notion.com/p/368ee4d477778173a3e7d9037118c96f">§12.18 E2：事前学習・Foundation Models（Pre-training & Foundation Models）</page>
	<page url="https://app.notion.com/p/368ee4d4777781fda80cf3d26e29fc06">§12.19 E5：半教師あり学習（Semi-Supervised Learning）</page>
	<page url="https://app.notion.com/p/368ee4d4777781619c8bcaf165833792">§12.20 F1：クラス不均衡対応（Class Imbalance / Long-Tailed Recognition）</page>
	<page url="https://app.notion.com/p/368ee4d4777781de9385c120a08f6a84">§12.21 サーベイ結果の横断的知見（全 22 サーベイ）</page>
	<page url="https://app.notion.com/p/368ee4d477778188832aef679b02f05c">§12.22 C2：検出 / 分割ヘッド（Detection / Segmentation Head）</page>
	<page url="https://app.notion.com/p/368ee4d4777781319d9fe1070f143611">§12.23 C4：物体中心表現 / Slot Attention（Object-Centric Representation）</page>
	<page url="https://app.notion.com/p/368ee4d47777819c9464fe08428cb57f">§12.24 G4：手術ドメイン既存ベンチマーク（Surgical Benchmarks）</page>
	---
	### 11.21 サーベイ結果の横断的知見（全 22 サーベイ）
	2026/05/18 実施分 8 件（A1, A2, A4, B1, B5, B8, C6, E3）、2026/05/20 追加分 11 件（B2, B3, B4, B7, C1, C3, D1, D2, E2, E5, F1）、さらに C2, C4, G4 の 3 件を加えた計 22 サーベイを横断して得られた主要な知見を以下にまとめる。
	**本研究の新規性のフック（サーベイで確認された空白領域）**：
	1. **一人称視点 × 開放手術 × マルチタスク（検出 + 工程 + 関係）の同時認識**：A1/A2 サーベイで先行例なしを確認。B2/B3/B4 サーベイでも、形状類似ペア対策・glove 下手検出・SAM 系セグメンテーションがいずれも腹腔鏡 EndoVis 評価に偏り、open surgery × egocentric では未検証であることが裏付けられた。
	2. **Object-centric temporal representation を Phase head の主入力とする設計**：B5 サーベイで先行例がほぼないことを確認（結合効果②の新規性）。C3/D2 サーベイで、検出由来の object token 列を長距離 SSM/Transformer に流し込む surgical 論文が 2026.05 時点で皆無であることが追加確認された。
	3. **Detection + Phase + Relation の三位一体 MTL**：C6 サーベイで既存文献は tool + phase の 2 タスクが最大であることを確認。E5 サーベイで、検出 × phase × 関係を同時に半教師ありで学習する公開研究も皆無であることが判明。
	4. **手術 OR での Ego-Exo view-consistent SSL**：A4 サーベイで手術 setting での先行例なしを確認（Exo＝Phase-2 の新規性）。D1/E2/E5 サーベイで、0.5 fps Ego ↔ 25 fps Exo の極端な fps 差をブリッジする手法が空白であり、Quattrocchi et al.（ECCV 2024）の exo→ego 蒸留が最も近い前例であることが特定された。
	5. **Segmentation マスクからの hand-tool 関係疑似ラベル自動生成**：B8 サーベイで先行例がほぼないことを確認（関係結合＝Phase-2 関連）。B7 サーベイで、検出マスクから interaction triplet を自動生成する surgical HOI 論文も未発表であることが裏付けられた。
	6. **hand-tool-guided MAE**：E3 サーベイで object-centric SSL × masked modeling の交差領域に先行例なしを確認。
	7. **EgoSurgery-Phase に対する長距離時系列モデルの未ベンチマーク**：D2/C3 サーベイで、Surgformer・LoViT・SR-Mamba・SKiT・MuST・HID-SSM の EgoSurgery-Phase 数値が未発表であり、これらの初ベンチマーク自体が明確な publishable 貢献となることを確認。
	8. **0.5 fps 低 fps × 異種マルチタスクでの長尾協調学習**：F1 サーベイで、検出 + セグメンテーション + 長距離時系列という異種マルチタスクの per-task 長尾協調学習、および低 fps 動画での Copy-Paste/Mixup 時系列一貫性が未開拓であることを確認。
	9. **surgical phase をトリガとした検出ヘッドへの query 条件付け**：C2 サーベイで、外部 phase token を Mask DINO / Mask2Former decoder に注入する研究例が MICCAI 2023–2025 範囲で発見できず、§4.6 の双方向補完が defensible な novelty であることを裏付け。
	10. **外部 detector の object token 列を SSM/Mamba に流す設計**：C4 サーベイで、SlotSSMs（NeurIPS 2024）以外に slot×Mamba の直接結合例がなく、「検出器出力 token 列を後段 Mamba で処理」する分離型設計は surgical も general video も未報告であり、C3-C4 結合がそれ自体論文の story になりうることを確認。
	11. **検出+工程+関係を三位一体で評価する手術ベンチマークの不在と Δ 指標の未標準化**：G4 サーベイで、open surgery で検出+工程+関係を同一データセットで評価するベンチマークが存在せず、SAR-RARP50/GraSP/PhaKIR 等が multi-task \> single-task を定性的に述べるのみで Δ（タスク結合の効果）指標を形式化した例がないことを確認—§7.1 の Δ 指標はモデルだけでなくベンチマーク方法論としても貢献となりうる。
	**実装・手法選定の横断的推奨（22 サーベイ統合版）**：
	- 空間 backbone：**DINOv2 ViT-L/14-with-registers** を主軸採用として確定（C1/E2/E3/B1 共通推奨）。register token で artifact patch を除去し形状類似ペア識別を改善。DINOv3 distilled 重みは公開揃い次第 ablation に追加。Stage A 必須 ablation として DINOv2 vs SurgeNetXL vs EndoViT vs Swin-L の backbone 比較表を作成（C1）。
	- PEFT：MTLoRA を plain ViT 用に porting し DoRA で強化、VeRA は head 増殖時に検討（C1/E2/C6）。heavy full fine-tuning は LIFT の知見に基づき回避（F1）。
	- 検出ヘッド：**Mask DINO + Learnable Query Proposal Distillation**（B1/B2 推奨）。SurgicalSAM の Contrastive Prototype Head を分類ヘッドに移植（形状類似ペア対策、B2）。VarifocalNet を baseline として必ず並走（EgoSurgery-Tool 実 SOTA、B2）。C2 サーベイでも query-based 統合ヘッドの妥当性が裏付けられ（object token 共有・時系列接続容易性・phase 条件付け適性）、Co-DETR を長尾対照候補、VFNet+Mask2Former 完全分離ヘッドを撤退候補とする。Phase→Detection 注入は STEP B で FiLM（§4.6 primary）vs Mask DINO decoder cross-attention（C2 推奨）を比較。
	- セグメンテーションヘッド：第 1 ライン **DINOv2 + EoMT decoder**、第 2 ライン DINOv2 + ViT-Adapter + Mask2Former（公式 SOTA 再現）、第 3 ライン Mask DINO、補助 SAM 2（B4 推奨）。
	- 手検出（S2）：own/other × L/R の 4 クラスに Mask DINO hand head を拡張、RoHan の Artificial Gloves augmentation + iterative 半教師ドメイン適応を再現。手姿勢推定は S3 以降に延期（B3）。
	- 時系列モデル：TeCNO をベースライン、SR-Mamba / SPRMamba / HID-SSM を SSM 系候補、SKiT を online 上限・低計算、Surgformer を offline 上限（B5/C3/D2 推奨）。object-centric token + Mamba の組合せ自体が論文の story（C3）。常に causal 版と bidirectional 版を並行訓練・評価（D2）。
	- 物体中心表現（object token 抽出）：Mask DINO object query + ROI Align/mask pooling を主トークン、DINOv2 上の VideoSAURv2/SlotContrast 風 unsupervised slot を ablation 対照・scene slot 補完・弱教師事前学習として併走。時系列化は SlotSSMs 風 block-diagonal Mamba を第1推奨、Slot-BERT 風 bidirectional masked Transformer を第2推奨、SlotContrast の object-level temporal contrastive loss を補助損失に併用（C4 推奨）。
	- HOI / 関係モジュール：Mask DINO query をノードとする two-stage GNN（PViC の cross-attention + SSG-Com/MCIT-IG の bipartite graph + hand-identity ノード）、HODN の stop-gradient で関係損失（Phase-2）が検出側（結合効果①）を汚染しないよう保護（B7/B8 推奨）。
	- MTL 最適化：FAMO + DB-MTL 対数変換、GCond の勾配蓄積、LibMTL の Δp 監視（C6 推奨）。
	- SSL 事前学習：VideoMAE v2 + hand-tool-guided MAE、Exo encoder は Hiera-B（VideoMAE V2 + Endo-FM warm-start）、Ego encoder は EgoVLPv2 初期化（E3/D1 推奨）。
	- 半教師あり：Stage C で Quattrocchi 方式の逆方向適用（Ego→Exo 蒸留）、Stage D で Consistent-Teacher（検出）+ SemiVT-Surge（phase）+ Polite Teacher（分割）統合（E5 推奨）。
	- クラス不均衡：post-hoc Logit Adjustment（全分類ヘッド）+ Seesaw Loss（p=0.8, q=2.0）+ RFS（t=0.001）+ Simple Copy-Paste + Balanced Softmax（工程ヘッド）+ Decoupled cRT（F1 推奨）。
	- Stage C 蒸留：AE2 / AlignEgoExo の temporal-alignment objective を plain L2 feature distillation の代わりに使用（E2/E5 推奨）。
	- 実装基盤：LibMTL（MTL）、microsoft/SoftTeacher + Adamdad/ConsistentTeacher + LiheYoung/UniMatch + IntraSurge/SemiVT-Surge（半教師あり）、IDEA-Research/MaskDINO・martius-lab/slotcontrast・PCASOlab/Xslot（検出・slot）（C6/E5/C2/C4 推奨）。
	- 評価ベンチマーク：EgoSurgery-\{Phase, Tool, HTS\} を主ベンチマークとして確定し、PhaKIR・GraSP・CholecT45・EgoExOR を転移・外部妥当性検証用に追加。Δ mAP（per-class、AP_rare/AP_common 分割）+ Δ macro-F1/Jaccard/Edit/Segmental F1@\{10,25,50\} を主報告指標とし、形状類似 sub-confusion matrix と Phase-conditional AP を Supplementary に、leave-one-surgeon-out + paired bootstrap 信頼区間を必須とする（G4 推奨）。
