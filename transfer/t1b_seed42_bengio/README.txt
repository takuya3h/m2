T1b seed42 本走（server B = bengio / A6000）2026-06-21 完了
- injection_t1b_result.json : 注入本体（--trainable all --epochs 6）
- zeroctx_t1b_result.json   : §4.6 対照（--zero-ctx）
- t1b_seed42.log            : 注入の全学習ログ
- t1b_zeroctx_seed42.log    : 対照の全学習ログ
結果: 両者 init_mAP=0.7303 / best_epoch=-1 / best_mAP=0.7303 → Δ_detection=0.0000
解釈: 6ep warm-start fine-tune は S0-frozen 起点を超えず、phase 注入の検出改善なし（seed42）。
