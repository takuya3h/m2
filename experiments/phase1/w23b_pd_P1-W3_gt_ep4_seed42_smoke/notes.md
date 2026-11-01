# 非公式（T-2026-11-01-stage2-w23-bengio） PD P1 FiLM（P1） W3 gt seed 42

受け取り手は D*-COCO 折り A seed 42 の検出塔。学習範囲 W3（--trainable all。界面 ＋ 設定の凍結以外の検出器の全体）。1 epoch 学習し途中で止めない。結果は 1 epoch 目（epoch 0）の状態で、最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。

- overall mAP 0.878707、標的群 AP 0.878707、陰性対照群 AP None、AP50 0.905556（群に欠けたクラス: 標的群 ['Bipolar Forceps', 'Scalpel', 'Syringe', 'Raspatory']、陰性対照群 ['Gauze', 'Mouth Gag', 'Suction Cannula', 'Tweezers']）
- 学習前 mAP 0.891661、学習前の出力と塔単独の差: None
- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {-1: 0.8916611661166115, 0: 0.8787066676592472}
- epoch ごとのゲート: {-1: None, 0: None}
- 動画ごとの mAP: {'09': 0.8787066676592472}
- 凍結部の要約値の前後一致: True
- 予測は /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/pd_preds/w23b_pd_P1-W3_gt_ep4_seed42_smoke へ移した（predictions_moved.json）
