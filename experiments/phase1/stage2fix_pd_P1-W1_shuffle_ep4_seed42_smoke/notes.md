# 非公式（T-2026-10-19-stage2-pilot-fix-epoch4-shuffle） PD P1-W1 shuffle seed 42

受け取り手は D*-COCO 折り A seed 42 の検出塔（学習範囲 film、凍結部は学習しない）。1 epoch 学習し途中で止めない。結果（metrics.json、per_class_ap.json、stage2fix_metrics.json の群と動画ごとの値、val の best の予測、best_t1b.pth）は 1 epoch 目（epoch 0）の状態で、最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。

- overall mAP 0.890709、標的群 AP 0.890709、陰性対照群 AP None（群に欠けたクラス: 標的群 ['Bipolar Forceps', 'Scalpel', 'Syringe', 'Raspatory']、陰性対照群 ['Gauze', 'Mouth Gag', 'Suction Cannula', 'Tweezers']）
- 学習前 mAP 0.891661
- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {-1: 0.8916611661166115, 0: 0.8907087024491922}
- 動画ごとの mAP: {'09': 0.8907087024491922}
- 凍結部の要約値の前後一致: True
