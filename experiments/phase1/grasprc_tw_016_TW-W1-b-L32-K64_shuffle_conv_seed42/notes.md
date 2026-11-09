# 非公式（T-2026-11-09-grasp-pilot-converge） DP TW shuffle seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 9（学習率を落とした epoch 17）。test は通していない。
best epoch 9 / val macro Jaccard 0.779128476438582 / accuracy 0.8818481848184818
epochs 25（停止 25）、学習前 Jaccard 0.7762185528074379
