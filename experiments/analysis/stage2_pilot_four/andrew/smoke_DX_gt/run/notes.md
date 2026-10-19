# 非公式（T-2026-10-19-stage2-pilot-four-new-types） PD decoder-xattn（DX） gt seed 42

受け取り手は D*-COCO 折り A seed 42 の検出塔（凍結。学習範囲 W1 = 界面だけ、--trainable film）。1 epoch 学習し途中で止めない。結果は 1 epoch 目（epoch 0）の状態で、最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。

- overall mAP 0.891661、標的群 AP 0.891661、陰性対照群 AP None（群に欠けたクラス: 標的群 ['Bipolar Forceps', 'Scalpel', 'Syringe', 'Raspatory']、陰性対照群 ['Gauze', 'Mouth Gag', 'Suction Cannula', 'Tweezers']）
- 学習前 mAP 0.891661
- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {-1: 0.8916611661166115, 0: 0.8916611661166115}
- epoch ごとのゲート: {-1: {'tanh_alpha': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}, 0: {'tanh_alpha': [0.0011765925446525216, -0.0007764034671708941, -0.0012253454187884927, 0.0009191293502226472, -0.0006288318545557559, 0.0008163786842487752]}}
- 動画ごとの mAP: {'09': 0.8916611661166115}
- 凍結部の要約値の前後一致: True
