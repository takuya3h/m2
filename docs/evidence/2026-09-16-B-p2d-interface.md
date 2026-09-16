# 証拠地図 B — P→D の界面の型

**版:** v1
**元の報告:** repo に deep research の出力ファイルは無い。出所は本契約の契約書
`tasks/T-2026-09-16-evidence-map-ab/SPEC.md`（30894 バイト、sha256 先頭 c17c2d9961aeb979）の
付録 B。起票者が deep research（ChatGPT 一エンジン）の報告を行単位で地図の様式へ写したものである。
**照合日:** 2026-09-16（JST 2026-09-17 未明に実施）
**照合の手段:** Crossref REST API（`api.crossref.org/works/`）で DOI を、arXiv API
（`export.arxiv.org/api/query`）で arXiv ID を引いた。doi.org の解決も到達性の確認に使った。
**照合の結果:** 全 11 行が「実在・書誌一致」。不在 0 件、到達不能 0 件、書誌に差 0 件。
照合器が働いていることは対照で示した（実在 DOI 2 件が HTTP 200、架空 DOI が HTTP 404）。
問い合わせと応答の全文は `tasks/T-2026-09-16-evidence-map-ab/audit.md` にある。

**印の列の読み方。** 「未照合」「起票者確認」などは**起票時点の状態**であり、本契約は
これを書き換えていない。本契約の照合結果は同じ欄の末尾に `照合2026-09-16:` として**足してある**。

**この地図は判定ではない。** 数値は各文献の報告のままで、本契約は一字も書き換えていない。

---

問い: 凍結した工程塔 P から凍結した DETR 系検出塔 D へ、小さな学習可能な界面で工程情報を渡す。
機構の系統と送り手の信号段（予測ラベル／正解ラベル／確率分布／特徴ベクトル）をどう選ぶか。
利用者の決定（2026-09-16）: presence から box mAP への外挿は割引率を置かず、「presence の Δ は上限の目安、box の期待値は不明」と書く。

## B.1 文献行


| 系統 | 文献 | 設定（送り手→受け取り手、粒度、信号） | 効果（結合あり／なし。指標名は原文） | 距離 | 効かなかった・残したこと | 印 |
|---|---|---|---|---|---|---|
| 補助損失・共有表現 | Twinanda ほか 2017 IEEE TMI. arXiv 1602.03012（EndoNet） | Cholec80。phase の正解ラベルを学習時の教師に。受け取り手は frame-level tool presence（box ではない）。推論時に phase を読まない | 40 動画: ToolNet 80.9 → EndoNet 81.0 mean AP（+0.1、Table II）。10 動画: 65.9 → 62.0（−3.9）。20 動画 70.9→67.5（−3.4）、30 動画 73.6→77.5（+3.9）。差は multi-task EndoNet と single-task ToolNet の差で、phase 補助損失だけの isolated ablation ではない | 1 | 符号が学習量で変わる。逆方向 oracle（正解 tool→phase）は 75.2→75.3。時間モデルなし | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1602.03012） |
| 補助損失・共有表現 | Twinanda ほか 2016 M2CAI 技術報告. arXiv 1610.08851 | M2CAI16-tool、Cholec80 40 動画。同上 | ToolNet 73.9 → EndoNet 74.2 mAP（+0.3、Table 1）。著者が no significant improvement と記載 | 1 | 学習量の差の方が結果に出た、と著者 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1610.08851） |
| 特徴→事前分布の相関損失（新系統） | Jin, Li, Dou, Chen, Qin, Fu, Heng 2020 Medical Image Analysis. arXiv 1907.06099（MTRCNet-CL） | Cholec80。送り手は phase 側 LSTM の特徴ベクトル（10 s 系列）。受け取り手は frame-level tool presence。学習した行列で tool 事前分布へ写像し KL で整合 | MTRCNet 87.5 → MTRCNet-CL 89.1 tool mAP（+1.6、Table 1）。Table 2: label-space 写像 86.8、mutual 87.1、feature-space 89.1。事前分布と出力の平均 88.8、事前分布のみ 88.4 | 1 | ラベル空間の結合は特徴空間より低く、no-CL の 87.5 も下回る。相互写像は一方向より低い。数値は原典と一致（TS1 85.1、TS2 88.1 も）。構造は共有 encoder＋二分岐の joint training で、凍結塔＋界面ではない。L 軸の前例には使えるが凍結界面の効果量には使えない | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1907.06099） |
| FiLM（特徴の変調） | Perez, Strub, de Vries, Dumoulin, Courville 2018 AAAI. arXiv 1709.07871 | CLEVR。質問特徴→画像レベル分類（dense ではない） | Table 2: 97.4 ／ FiLM なし 21.4。β=0 で 96.9、γ=1 で 95.9、FiLM 層一つで 97.3 | 3 | CoGenT で分布の組み合わせに依存（A 98.3、B 75.6）。fine-tune 後の忘却 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1709.07871） |
| cross-attention 条件付け | Yang, Wang, Tang, Chen, Zhao, Torr 2022 CVPR. arXiv 2112.02244（LAVT） | RefCOCO。正解テキスト token →画素分割 | Table 2 RefCOCO val: なし oIoU 68.82／mIoU 68.87、PWAM のみ 70.78／71.96、full 72.73／74.46 | 2 | 置く場所で符号が変わる: Table 3 で 72.27→72.06、72.29→71.38。追加 decoder で 72.73→72.12 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2112.02244） |
| FiLM ＋ 小 decoder（凍結 encoder） | Lüddecke, Ecker 2022 CVPR. arXiv 2112.10003（CLIPSeg） | PhraseCut。CLIP 埋め込み（凍結）→画素分割。学習パラメータ 1,122,305（D=64） | FiLM on/off の対は number not available。Table 9: text mIoU 43.6／AP 76.7、CLIP 事前学習なし 13.1／12.6 | 2 | D=16 で 37.4／71.5、layer-3 のみ 31.9／64.9 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2112.10003） |
| 外部条件付き DETR | Kamath ほか 2021 ICCV. arXiv 2104.12763（MDETR） | 正解テキスト→box 集合予測 | 条件 on/off は number not available（タスク自体がテキスト条件付き） | 2 | 記載なし（要旨） | 未照合。要旨。片方。照合2026-09-16: 実在・書誌一致（arXiv 2104.12763） |
| タスク親和性・負の転移 | Standley, Zamir, Chen, Guibas, Malik, Savarese 2020 ICML. arXiv 1905.07553 | Taskonomy 由来の dense タスク。共有 backbone、推論時の送り手なし | Table 2 Setting 1: Depth→SemSeg +4.17%、SemSeg→Depth −5.41%、SemSeg→Normals −11.29%、→Edges −34.64%。五タスク同時は単独平均比 −19.00% | 3 | 親和性は方向・容量・データ量に依存。容量を変えると Table 2 と Table 5 の関係が大きく変わり、データ 5% でも変わる。共有 backbone MTL の前例であり、凍結界面では勾配衝突の経路が無い | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1905.07553） |
| 記憶バンク cross-attention ＋ 加算バイアス | Beery, Wu, Rathod, Votel, Huang 2020 CVPR. arXiv 1912.03538（Context R-CNN） | 固定カメラ。他フレームの ROI 特徴（Faster R-CNN 由来）で記憶バンクを構築→現フレーム box 検出へ attention で注入。attend したベクトルを proposal 特徴へ per-channel bias として加算。「凍結送り手→凍結検出器の間だけを学習」した研究ではない | Table 1: SS 37.9→55.9 mAP@0.5、CCT 56.8→76.3、CityCam 38.1→42.6。時間幅 1 min 50.3、1 h 52.1、1 day 52.5、1 week 54.1、1 month 55.6 | 2 | 多数決は 37.9→37.8（−0.1）。空間平均 39.6、単フレーム attention 44.9、短期 46.4、長期 55.6。数値は原典と一致 | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1912.03538） |
| 系列レベル意味集約 | Wu, Chen, Wang, Zhang 2019 ICCV. arXiv 1907.06390（SELSA） | ImageNet VID、EPIC-KITCHENS（±10 s の proposal 特徴）→現フレーム box 検出。行動ラベルは使わない | VID: 73.62→80.25 mAP。EPIC seen 36.57→37.97、unseen 31.86→34.80 | 2 | 同フレーム集約は高速動体で 51.53→51.43。Seq-NMS 追加で 82.69→82.48、84.30→83.73。EPIC は予備的で調整不十分と著者 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1907.06390） |
| グラフ推論の文脈精緻化（新系統） | Liu, Wang, Shan, Chen 2018 CVPR. arXiv 1807.00119（SIN） | VOC、COCO。場面特徴＋proposal 関係→box 検出 | number not available（要旨） | 3 | 記載なし（要旨） | 未照合。要旨。片方。照合2026-09-16: 実在・書誌一致（arXiv 1807.00119） |

## B.2 見つからなかったもの と 検索記録


同ドメインの検索語: surgical phase tool detection conditioning Cholec80／phase tool presence multi-task EndoNet／MTRCNet-CL correlation loss／phase information tool detector Cholec80 DETR／CholecT50 phase instrument triplet／CATARACTS／HeiChole／EgoSurgery phase tool detection／oracle／Rendezvous temporal phase tool interaction。
一般機構の検索語: FiLM conditional dense prediction／FiLM frozen backbone segmentation／cross attention conditioning dense prediction／conditional DETR external context query conditioning／MDETR／class prior conditioned object detection／task affinity dense tasks negative transfer／Which Tasks Should Be Learned Together／Taskonomy／gradient conflict multi task dense prediction。
隣接ドメインの検索語: scene label conditioned object detection／global scene context object detection／activity conditioned object detection egocentric／EPIC-KITCHENS action label object detection prior／Ego4D activity context object detection／video level context object detection／temporal context Faster R-CNN／Context R-CNN／SELSA EPIC Kitchens／object detection co-occurrence prior context。

見つからなかったもの:
- 凍結 P と凍結 D の間だけを学習する手術映像の研究
- DETR の object query を手術工程で条件付けする研究、phase 条件付きの anchor／class logit
- 予測 phase と phase 確率分布を同一検出器で直接比べた研究
- 正解 phase の oracle と予測 phase を box-level tool mAP で並べた研究
- 同一 frozen DETR で add／concat、FiLM、cross-attention、query 条件付け、class-logit prior を同一パラメータ予算で比べた研究
- EPIC／Ego4D で行動ラベル→box 検出の方向（見つかったのは逆方向ばかり）

報告が除外した種: Conditional DETR は外部文脈の条件付けではなく decoder 内部の空間条件付けであるため採用していない。

## B.3 機構の系統 × 送り手の信号段


| 系統 | 予測ラベル | 正解ラベル（oracle） | 確率分布 | 特徴ベクトル |
|---|---|---|---|---|
| 特徴の結合 add／concat | 未 | 未 | 未 | 正（Context R-CNN） |
| FiLM | 未 | 未 | 未 | 正（FiLM、CLIPSeg。ただし dense でない／対なし） |
| cross-attention | 未 | 未 | 未 | 正（LAVT、Context R-CNN） |
| DETR query 条件付け | 未 | 未 | 未 | 未（MDETR は別設定） |
| 出力 class prior・logit 再採点 | 未 | 未 | 零・負（MTRCNet-CL label-space 86.8） | 零・負（平均で 89.1→88.8） |
| 補助 phase 損失・共有 MTL | 未 | 零・負（EndoNet 10 動画 −3.9、M2CAI +0.3） | 未 | 未 |
| 蒸留・相関損失 | 未 | 未 | 未 | 正（MTRCNet-CL +1.6） |
| 時間履歴・窓 | 未 | 未 | 未 | 正（MTRCNet-CL、SELSA、Context R-CNN） |

本研究の設計（予測／正解／確率 × 凍結 DETR の界面）に当たる列は全て「未」。

## B.4 起票者の読み（地図から言えること。判定ではない）


## B.5 未検証の組み合わせ

B.3 の表で「未」と記された全セルが未検証の組み合わせである。
本研究の設計（予測／正解／確率 × 凍結 DETR の界面）に当たる列は全て「未」であり、
地図上で誰も埋めていない。
