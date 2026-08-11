# T-2026-08-11-s0-reevaluation-feasibility — 判断の受け皿

- **結論: S0 比較表の再評価は不要。** 同一検出器 `maskdino` が両系統で評価されており、差は **0.000333（0.05σ）**。検出器間の幅 0.029461（**約 4.6σ**）と比べて無視できる。**表は条件差を明記して載せればよい。**
- **三択の判断材料。**（1）作り直す＝**事実上できない**（首位 `relationdetr` を含む 9 検出器の重みが lecun に無い）／（2）**条件差を明記して載せる＝可能かつ推奨**（注記のみ）／（3）表を落とす＝実測上その必要が無い。**決めるのは起票者。**
- **重みは失われていない。このホストに無い。** 主要 9 検出器は `philip` で学習され、lecun へは 6 点証跡だけが転送されている。**`philip` に現存するかは lecun からは測れない（UNKNOWN）。** 確認するなら別ホストでの実測が要る。
- 「6 系統」は誤読。`eval_recipe_id` は split サイズと GPU 構成も含む 10 キーのハッシュ。**後処理で見ると 4 系統、実効 2 系統（NMS-free 33 run / NMS あり 14 run）。** しかも後処理は検出器の設計に属し、揃えること自体が意味を持たない。
- **表に載せる際の但し書き（実測）** — `sensex_codino` は **1 seed のみ**／`maskdino`・`varifocanet` の `#None` 側（`_wrong_split_8_2_3` 由来・全件除外）を混ぜない／0.05σ は **maskdino 1 検出器での測定**で一般化は UNKNOWN。
- 前 task の UNKNOWN が解けた。`maskdino_bbox@val` と `varifocanet_bbox@val` は `#<hash>` の分離子付きで `experiments.csv` に存在する。
- 予測 `.pkl` は**後処理の後**（300 箱・score 最小 0.0117）。**再採点の代替にならない。** 再評価経路 `scripts/reeval_s0_nms_free.py` は実在し codetr で実行済みだが、入力は `best.pth`。
