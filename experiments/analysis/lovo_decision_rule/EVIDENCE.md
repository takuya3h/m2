# 証跡の記録 — T-2026-08-26-lovo-decision-rule

事実の記録は `RESULT.md`。本書は命令とその出力である。行番号で指される。

## 1. 契約の検証（L1+L2）
```
$ make task-validate TASK=T-2026-08-26-lovo-decision-rule ; echo EXIT=$?
WARN [L2-8] index.csv: 起票時 751 → 現在 1177（分母が動いています）
WARN [L2-8] experiments.csv: 起票時 207 → 現在 213（分母が動いています）
OK   T-2026-08-26-lovo-decision-rule

1 task(s), 0 failed
EXIT=0
```

## 2. 起票時からの分母の動き（WARN の内訳）
```
$ for c in $(git --no-pager log --format=%h -12 -- runindex/experiments.csv); do ... git --no-pager show "${c}:runindex/..." | wc -l ...
7918b5d exp=213 idx=1177  exp(s4): 60-seed deterministic sweep
3e15d09 exp=221 idx=851   feat(exp): form sweep
592a4e1 exp=217 idx=791   feat(exp): grasp injection effect
64576f3 exp=207 idx=751   chore(runindex): regenerate on a host without leftovers  <- 起票時と一致
```
注: 変数と : を引用せずに書くと zsh が修飾子として解釈し、git show が空を返す。
    最初の測定は全て -1 になった。引用して測り直した値が上である。

## 3. 実行直前検査（L3）
```
$ source .venv/bin/activate && make task-preflight TASK=... ; echo EXIT=$?
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
P6 decisions_answered     FAIL 未回答 3 件: 採用する判定則を最終的に一つへ決めること; 既存の報告の記述を訂正すること; 対象とする既存結論の範囲を広げること
P7 destination_writable   PASS experiments/analysis/lovo_decision_rule/ は未作成だが作成可能（experiments/analysis へ書き込みと削除ができた）
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 8 件を検査し該当なし

RESULT: 4 PASS / 0 WARN / 4 SKIP / 1 FAIL
make: *** [Makefile:171: task-preflight] Error 1
(P6 FAIL のため利用者へ提示し、回答を meta.amendments へ記録して再実行)

P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS experiments/analysis/lovo_decision_rule/ は未作成だが作成可能（experiments/analysis へ書き込みと削除ができた）
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 8 件を検査し該当なし

RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
EXIT=0
```

## 4. 現行の則が既知の値を再現することの実測

### 4.1 §3.9 の fold ごとの表（15 動画 × 3 腕 × acc/edit = 90 値）
```
比べた値 90 個 / 不一致 0 個
空振り検査: fold を 1 つずらすと不一致 15/15 件（0 なら照合が働いていない）
```

### 4.2 §3.9 の集計
```
指標          腕                  Δ   |m|/SE    pos       σ_d
accuracy    オラクル         +0.0022     0.06   10/15    0.1461
accuracy    HMM          -0.0032     0.44    9/15    0.0280
macro-F1    オラクル         +0.0083     0.55   12/15    0.0579
macro-F1    HMM          +0.0027     0.27    9/15    0.0395
edit        オラクル         +5.8826     1.34    9/15   16.9458
edit        HMM          +9.1095     3.06   12/15   11.5354
seg-F1@50   オラクル         +0.0649     2.64   12/15    0.0953
seg-F1@50   HMM          +0.0675     3.15   12/15    0.0829
```
報告書 §3.9 の記録値（+0.0022・|m|/SE=0.06・10/15、+9.11・0.79σ・3.06・12/15 ほか）と全行一致。

### 4.3 §3.16(e) 受容野 4 段（台本の出力 vs 捕まえた値）
```
--- 台本の出力
K=0    | acc 全= 0.8658 Δ=+0.0161(2.37,8/15) | mF1 全= 0.8004 Δ=+0.0229(2.80,9/15)
K=8    | acc 全= 0.8606 Δ=+0.0116(1.89,11/15) | mF1 全= 0.7903 Δ=+0.0236(1.21,10/15)
K=32   | acc 全= 0.8578 Δ=+0.0111(1.58,8/15) | mF1 全= 0.7935 Δ=+0.0137(1.36,7/15)
K=128  | acc 全= 0.8421 Δ=+0.0297(1.37,9/15) | mF1 全= 0.7802 Δ=+0.0326(2.25,11/15)
--- 捕まえた値から同じ量を計算
K=0    | acc 全= 0.8658 Δ=+0.0161(2.37,8/15) | mF1 全= 0.8004 Δ=+0.0229(2.80,9/15)
K=8    | acc 全= 0.8606 Δ=+0.0116(1.89,11/15) | mF1 全= 0.7903 Δ=+0.0236(1.21,10/15)
K=32   | acc 全= 0.8578 Δ=+0.0111(1.58,8/15) | mF1 全= 0.7935 Δ=+0.0137(1.36,7/15)
K=128  | acc 全= 0.8421 Δ=+0.0297(1.37,9/15) | mF1 全= 0.7802 Δ=+0.0326(2.25,11/15)
```

### 4.4 §3.16(b) 6 凍結源
```
凍結源                                  acc(全)    acc(除去)     Δacc  |m|/SE   mF1(全)    mF1(除去)     ΔmF1  |m|/SE     落とす数
relation_detr_seed42                 0.8658     0.8819  +0.0161    2.37   0.8004     0.8233  +0.0229    2.80      4.9
relation_detr_seed123                0.8712     0.8875  +0.0162    2.21   0.8008     0.8167  +0.0159    1.89      4.9
relation_detr_seed456                0.8766     0.8980  +0.0213    2.02   0.7947     0.8152  +0.0205    1.55      4.9
relation_detr_augstrong_seed42       0.8563     0.8734  +0.0172    2.03   0.7896     0.7979  +0.0083    0.49      4.9
relation_detr_augstrong_seed123      0.8504     0.8698  +0.0194    2.06   0.7814     0.8152  +0.0338    1.88      4.9
relation_detr_augstrong_seed456      0.8536     0.8649  +0.0113    1.34   0.7831     0.7938  +0.0107    0.80      4.9

6 凍結源の Δacc: mean=+0.0169  正=6/6
6 凍結源の ΔmF1: mean=+0.0187  正=6/6
```
報告書の「Δacc は 6/6 で正・範囲 +1.13〜+2.13pt・5/6 で |m|/SE ≥ 2」と一致。

## 5. 対照の出力（両方向）
```
陽性対照 C01 phase_edit_score
    そのまま  : {'R0': True, 'R1': True, 'R3': True}
    差を零へ潰す: {'R0': False, 'R1': False, 'R3': False}
陽性対照 C01 phase_seg_f1_50
    そのまま  : {'R0': True, 'R1': True, 'R3': True}
    差を零へ潰す: {'R0': False, 'R1': False, 'R3': False}
陰性対照 C05 phase_accuracy 定数倍 x10 / x50
    そのまま/定数倍後 : いずれも {'R0': False, 'R1': False, 'R3': False}
    -> 定数倍では |m|/SE が不変（分子と分母が同じ倍率）。片方向では足りない。
陰性対照 C05 phase_accuracy 平行移動の掃引
    +0.0    {'R0': False, 'R1': False, 'R3': False}
    +0.05   {'R0': False, 'R1': False, 'R3': False}
    +0.075  {'R0': True,  'R1': False, 'R3': False}
    +0.1    {'R0': True,  'R1': False, 'R3': True}
    +0.15   {'R0': True,  'R1': True,  'R3': True}
    検出へ反転する移動量: R0=+0.07324  R1=+0.11018  R3=+0.08045
R2 の対照: 陽性 C01 edit [+20.8530, +43.5478] 検出 / seg-F1@50 [+0.2099, +0.4665] 検出
            陰性 C05 accuracy [-0.0733, +0.0776] 検出せず
```

## 6. 足場が結果を変えないことの実測（両方向）
```
部分集合を与えない : 比べた値 315 個 / 不一致 0 個
部分集合を与える   : fold 数 12、共通 fold の値 一致 51 個 / 相違 201 個
（相違が 0 なら差し替えが効いていないことになる）
修正後の足場でも   : 比べた値 315 個 / 不一致 0 個
```

## 7. 乱数の再現（両方向）
```
{
 "台本": "docs/analysis_scripts/proxy_lovo_noise_testonly.py",
 "反復数": 6,
 "m": 12,
 "同じ種42_部分集合が一致": true,
 "違う種43_部分集合が一致": false,
 "同じ種42_結果のsha256": [
  "9cf16f3050238a2547774981d2a79ca8d19efa81acef78ba37f47acd8d565700",
  "9cf16f3050238a2547774981d2a79ca8d19efa81acef78ba37f47acd8d565700"
 ],
 "違う種43_結果のsha256": "e629bebd574792e47f294a6e24a037b83e70f3a4dddd44e56665d5579788c871",
 "同じ種42_結果が完全一致": true,
 "違う種43_結果が完全一致": false,
 "成功した反復": {
  "seed42_a": 6,
  "seed42_b": 6,
  "seed43": 6
 },
 "注": "両方向を測った。片方だけでは常に同じ値を返す壊れ方と区別できない"
}```

## 8. 反復数への安定性
```
24 反復が揃った対: 100
16 反復と 24 反復の SE の相対差: 中央値 4.0%  平均 4.5%  最大 11.7%
16 反復と 24 反復で判定が変わった対: 1 / 100  (C21:phase_seg_f1_50)
```

## 9. 台本の実行時間
```
--- 素の値の取り出し（1 回目）
=== START gap_vs_presence 21:53:39
=== END   gap_vs_presence rc=0 21:55:54
=== START recommended 21:55:54
=== END   recommended rc=0 21:56:26
=== START noise_structure 21:56:26
=== END   noise_structure rc=0 21:57:01
=== START noise_testonly 21:57:01
=== END   noise_testonly rc=0 21:57:10
=== START signal_form 21:57:10
=== END   signal_form rc=0 21:57:47
=== START denoise_variants 21:57:47
=== END   denoise_variants rc=0 21:58:35
=== START capacity_control 21:58:35
=== END   capacity_control rc=0 21:59:21
=== START prune_by_entropy 21:59:21
=== END   prune_by_entropy rc=0 22:00:57
=== START prune_ubiquitous 22:00:57
=== END   prune_ubiquitous rc=2 22:00:57
=== START capacity_of_head 22:00:57
=== END   capacity_of_head rc=2 22:00:57
=== START capacity_of_head_denoise 22:00:57
=== END   capacity_of_head_denoise rc=2 22:00:57
=== START receptive_field_prune 22:00:57
=== END   receptive_field_prune rc=2 22:00:57
=== START receptive_field_denoise 22:00:57
=== END   receptive_field_denoise rc=2 22:00:57
=== START prune_across_sources 22:00:57
=== END   prune_across_sources rc=2 22:00:58
=== START flicker_scaling 22:00:58
=== END   flicker_scaling rc=2 22:00:58
ALL DONE 22:00:58
--- 周回の取り出し
=== START capacity_of_head_denoise 22:33:06
=== END   capacity_of_head_denoise rc=0 22:36:21
=== START prune_across_sources 22:36:21
=== END   prune_across_sources rc=0 22:39:16
=== START flicker_scaling 22:39:16
=== END   flicker_scaling rc=0 22:43:02
=== START receptive_field_prune 22:43:02
=== END   receptive_field_prune rc=0 22:51:27
=== START receptive_field_denoise 22:51:27
=== END   receptive_field_denoise rc=0 23:02:43
LOOP DUMPS DONE 23:02:43
```

## 10. 禁止領域の検査
```
$ source .venv/bin/activate && make forbidden-check ; echo EXIT=$?
EXIT=2
base=origin/phase0  changed=80  checked=80  violations=70  errors=[]
  1 本契約の成果物（契約の outputs.destination）: 56 件
  2 他ホストの契約の成果物（同期で到着・未追跡）: 7 件
  3 origin/phase0 に在り私の HEAD に無い分（PR a4a95cf）: 7 件
```
2 の作成時刻 2026-08-25 22:37:31（Phase A 開始は 21:49 UTC）。
3 は作業ツリーに実体が無く、origin/phase0 の a4a95cf が持つ。私の分岐が古いだけである。

## 11. 変更範囲の一覧

`CHANGES.md` を参照。
