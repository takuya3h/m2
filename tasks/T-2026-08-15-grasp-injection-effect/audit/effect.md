# Phase C — grasp injection effect

数値の正本は `effect.json`。6つの `metrics.json` と6つの best checkpoint の val 再評価から測定した。
test split は使用していない。

## 主たる終点

差は `inj phase_accuracy - ctrl phase_accuracy`。同じ seed で対にした。

| seed | ctrl | inj | paired delta |
|---:|---:|---:|---:|
| 42 | 0.896370 | 0.893069 | -0.003300 |
| 123 | 0.892409 | 0.887129 | -0.005281 |
| 456 | 0.899670 | 0.895050 | -0.004620 |

- paired delta mean: `-0.004400440044004379`
- paired pstd (ddof=0): `0.0008232469497852892`
- `abs(mean) / pstd`: `5.345224838248179`
- signs: `[-1, -1, -1]`
- same non-zero sign: `true`
- preregistered decision rule: PASS

事前登録の絶対値ルールでは方向性のある効果を検出した。しかし方向は負であり、
予測「inj が ctrl を上回る」は外れた。推論信号の注入はこの構成で平均 accuracy を
`0.004400440044004379`（約0.4400 percentage point）低下させた。

差の絶対値は `0.010` 未満だが、decision rule 自体は低い実測 paired pstd と全 seed 同符号により
PASS したため、「検出できず」ではない。「改善効果あり」でもなく、**逆方向の悪化を検出**した。

## 把持推論の出来

実際に phase へ信号を渡した inj arm の3 seed平均。下見との比較も accuracy 同士である。

| dimension | inj mean | inj pstd | linear probe | difference |
|---|---:|---:|---:|---:|
| left_hand | 0.984808 | 0.000000 | 0.645 | +0.339808 |
| right_hand | 0.966535 | 0.000311 | 0.759 | +0.207535 |
| left_hand_tool | 0.875605 | 0.044227 | 0.829 | +0.046605 |
| right_hand_tool | 0.856011 | 0.010499 | 0.743 | +0.113011 |
| two_hands_tool | 0.883752 | 0.000000 | 0.793 | +0.090752 |

5次元すべてが線形下見を上回った。したがって今回の負方向効果を「把持推論が偶然並みだったため」
とは説明できない。次に疑うべきは、予測確率の形・detach後の連結方法・phase head が信号を使う際の
正則化／ゲート、および把持 accuracy が phase に有効な情報量を表しているかである。

## ctrl と既存基準点（非対応の参考値）

- ctrl mean: `0.8961496149614963`
- denominator mean (17 runs): `0.8973014948553679`
- ctrl mean - denominator mean: `-0.0011518798938716657`

これは対にできないため参考値であり、有意性の主張には使わない。

## 工程ごとの分解

各値は3 seed平均。delta は inj−ctrl。

| phase | ctrl F1 | inj F1 | delta F1 | ctrl Jaccard | inj Jaccard | delta Jaccard |
|---|---:|---:|---:|---:|---:|---:|
| anesthesia | 0.889358 | 0.896241 | +0.006882 | 0.802721 | 0.819762 | +0.017041 |
| closure | 0.926181 | 0.924573 | -0.001608 | 0.862511 | 0.859877 | -0.002635 |
| design | 1.000000 | 0.996764 | -0.003236 | 1.000000 | 0.993590 | -0.006410 |
| disinfection | 0.000000 | 0.000000 | +0.000000 | 0.000000 | 0.000000 | +0.000000 |
| dissection | 0.915100 | 0.914847 | -0.000253 | 0.843515 | 0.843167 | -0.000349 |
| dressing | 0.000000 | 0.000000 | +0.000000 | 0.000000 | 0.000000 | +0.000000 |
| hemostasis | 0.378988 | 0.223201 | -0.155788 | 0.243262 | 0.134622 | -0.108640 |
| incision | 0.855386 | 0.850050 | -0.005336 | 0.747584 | 0.744007 | -0.003577 |
| irrigation | 0.000000 | 0.000000 | +0.000000 | 0.000000 | 0.000000 | +0.000000 |

悪化の主成分は hemostasis。anesthesia は小幅改善した。契約の既知欠損率は anesthesia 6.81%、
irrigation 8.47% であるため、この2工程は割り引いて読む。disinfection / dressing / irrigation の
F1・Jaccard は両腕とも0であり、注入効果の方向を評価できない。

## 所要時間

- mean: `6.845680806048525` seconds/run
- min: `6.478691497119144`
- max: `7.339944418985397`

## Positive controls

- decision rule passing input `[0.019, 0.020, 0.021]`: PASS
- breaking input with mixed signs `[0.020, -0.010, 0.020]`: FAIL
- false temporal recipe: denominator と不一致

## G3 verdict

PASS。事前登録の式・ddof・符号条件・本数を結果確認後に変更していない。
