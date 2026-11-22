# 非公式（T-2026-11-21-grasp-hand-irn-hice-htt-pilot） DP HiCE DG seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 13（学習率を落とした epoch 21）。test は通していない。
best epoch 13 / val macro Jaccard 0.7736762284245359 / accuracy 0.8693069306930693
epochs 29（停止 29）、学習前 Jaccard 0.7762185528074379
