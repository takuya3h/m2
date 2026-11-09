# 非公式（T-2026-11-09-grasp-pilot-converge） DP RT pred_CF seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 6（学習率を落とした epoch 14）。test は通していない。
best epoch 6 / val macro Jaccard 0.7874177026794721 / accuracy 0.8858085808580858
epochs 22（停止 22）、学習前 Jaccard 0.7762185528074379
