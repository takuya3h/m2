# 非公式（T-2026-11-21-grasp-hand-irn-hice-htt-pilot） DP HiCE DGH-U seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 8（学習率を落とした epoch 16）。test は通していない。
best epoch 8 / val macro Jaccard 0.7705822881295418 / accuracy 0.8838283828382838
epochs 24（停止 24）、学習前 Jaccard 0.7762185528074379
