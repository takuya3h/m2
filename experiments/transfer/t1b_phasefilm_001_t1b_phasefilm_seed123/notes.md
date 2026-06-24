# T1b Phase→Det FiLM 注入 (seed123)

warm-start=t1b_seed123 / 対照=有。
- 注入 mAP=0.7292 (init 0.7292)
- Δ_inj=+0.0000 / Δ_ctrl=+0.0000 / 注入純効果=+0.0000

分母=init mAP（FiLM恒等=warm-start S0-frozen, 同一eval）。①学習FiLM phase→det。Δ_det=best−init（init=warm-start S0-frozen, 同一eval）/ 注入純効果=Δ_inj−Δ_ctrl
