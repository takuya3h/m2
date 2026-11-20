# 非公式（T-2026-11-20-grasp-hand-graph-pilot） DP GR DG seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 21（学習率を落とした epoch 29）。test は通していない。
best epoch 21 / val macro Jaccard 0.783073800961992 / accuracy 0.8726072607260726
epochs 37（停止 37）、学習前 Jaccard 0.7762185528074379
