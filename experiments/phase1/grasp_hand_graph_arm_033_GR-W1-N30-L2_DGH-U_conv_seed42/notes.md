# 非公式（T-2026-11-20-grasp-hand-graph-pilot） DP GR DGH-U seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 16（学習率を落とした epoch 24）。test は通していない。
best epoch 16 / val macro Jaccard 0.7809312212234115 / accuracy 0.8745874587458746
epochs 32（停止 32）、学習前 Jaccard 0.7762185528074379
