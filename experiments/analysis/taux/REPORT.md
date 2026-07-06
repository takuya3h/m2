# taux 系統 Δ_phase 集計レポート

対象: region-token 補助→工程（系統② det→phase・②特徴レベル / T1a 系）

走査元: `experiments/transfer/taux_*`（metrics.json 直読み・手打ち介入なし）。

分母（S4 base・固定値）: phase accuracy = **0.8986** / 公式 macro-F1 = **0.709**。
各手法の per-seed Δ = (実測 − base)。σ は per-seed Δ の母標準偏差 (`statistics.pstdev`)。
判定（§10.1）: `|mean(Δ)| > σ` かつ 全 seed 同符号 のとき ✓（有意）。seed<2 は判定不能 (n/a)。pp = ×100 表示。

## 該当実験なし

`experiments/transfer/` に `taux_*` の完了済み実験（metrics.json に phase_accuracy / phase_macro_f1 を持つもの）が見つかりませんでした（0 件）。実験を実行後に再生成してください。
