# 非公式（T-2026-11-09-grasp-pilot-converge） DP RT gt seed 42

受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。収束規則（停滞 8 epoch で学習率 × 0.1 を一度、再停滞で打ち切り、上限 120）。結果は val の Jaccard が最良の epoch 20（学習率を落とした epoch 18）。test は通していない。
best epoch 20 / val macro Jaccard 0.7855863729846181 / accuracy 0.8910171730515192
epochs 28（停止 28）、学習前 Jaccard 0.7770292529590558
