# T-2026-08-15-grasp-injection-effect — RESULT

## 1. 解決された参照

### `inputs.denominator.ref`

出所: `runindex/experiments.csv`

```text
experiment_id=phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
split=val
n_runs=17
n_seeds=3
seeds=42,123,456
accuracy_mean=0.8973014948553679
accuracy_pstd=0.005917073407586465
accuracy_sstd=0.006099179663503103
accuracy_n=17
```

### `inputs.sigma_policy`

契約内で明示済み:

```yaml
series: pstd
sigma_source: paired_delta
delta_sigma_source: paired
```

### `inputs.frozen_source.ref`

指定なし。

### `contract.inject_verbatim`: `conventions#prohibitions`

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

## 2. 結論

事前登録の予測「推論結果を渡した腕が無情報な腕を上回る」は**外れた**。
同じ seed の差 `inj - ctrl` は3本すべて負で、平均 `-0.004400440044004379`。
事前登録の絶対値ルールは PASS したため方向性のある効果は検出されたが、その方向は
**改善ではなく悪化**である。把持信号の注入は平均 accuracy を約0.4400 percentage point 下げた。

これは「検出できず」でも「効果なし」でもない。**逆方向の効果を検出し、改善仮説を棄却した。**

## 3. 主たる終点

出所: 6 run の `metrics.json`。計算と再検証結果は `audit/effect.json`。

| seed | ctrl | inj | inj - ctrl |
|---:|---:|---:|---:|
| 42 | 0.8963696369636963 | 0.8930693069306931 | -0.0033003300330032292 |
| 123 | 0.8924092409240925 | 0.8871287128712871 | -0.005280528052805322 |
| 456 | 0.8996699669966997 | 0.8950495049504951 | -0.0046204620462045876 |

- paired delta mean: `-0.004400440044004379`
- paired pstd, ddof=0: `0.0008232469497852892`
- `abs(mean) / pstd`: `5.345224838248179`
- signs: `[-1, -1, -1]`
- same non-zero sign: `true`
- preregistered rule: PASS
- hypothesis supported: `false`

## 4. 把持推論の出来

phase へ実際に信号を渡した inj arm の3 seed平均を線形下見と比較した。

| dimension | inj mean | inj pstd | linear probe | difference |
|---|---:|---:|---:|---:|
| left_hand | 0.9848084656061552 | 1.1102230246251565e-16 | 0.645 | +0.3398084656061552 |
| right_hand | 0.9665345850362487 | 0.0003113633231338767 | 0.759 | +0.20753458503624866 |
| left_hand_tool | 0.8756054618819492 | 0.04422678280907723 | 0.829 | +0.04660546188194925 |
| right_hand_tool | 0.8560105728872124 | 0.010498997302844997 | 0.743 | +0.11301057288721239 |
| two_hands_tool | 0.8837516564516599 | 0.0 | 0.793 | +0.09075165645165983 |

5次元すべてで下見を上回った。したがって「推論が偶然並みで信号に情報が無い」という
escalation 条件には該当せず、負方向の効果を推論 accuracy の不足だけでは説明できない。

## 5. 従たる終点

### ctrl と既存基準点

- ctrl 3 seed mean: `0.8961496149614963`
- 既存基準点 17 run mean: `0.8973014948553679`
- ctrl minus baseline: `-0.0011518798938716657`

対にできない比較なので参考値であり、有意性の主張には使わない。

### 工程ごとの分解

6 best checkpoint を同じ val 評価器で再評価し、保存済み全体指標との完全一致を確認した。
全9工程の値は `audit/effect.json` と `audit/effect.md` に記録した。最大の悪化は hemostasis で、
F1差 `-0.15578752562792192`、Jaccard差 `-0.10863993908861323`。anesthesia は
F1差 `+0.0068824893205429545`、Jaccard差 `+0.017041159898302755` だった。
disinfection / dressing / irrigation は両腕とも F1・Jaccard が0で、方向を評価できない。
既知の注釈欠損率 anesthesia 6.81%、irrigation 8.47% を踏まえ、この2工程は割り引いて読む。

## 6. 所要時間

各 `metrics.json` の実測 `elapsed_seconds`:

| run | seconds |
|---|---:|
| ctrl seed42 | 6.478691497119144 |
| inj seed42 | 7.339944418985397 |
| ctrl seed123 | 6.914426580071449 |
| inj seed123 | 6.815076003083959 |
| ctrl seed456 | 6.6095304801128805 |
| inj seed456 | 6.91641585691832 |

平均 `6.845680806048525` 秒、最小 `6.478691497119144` 秒、最大 `7.339944418985397` 秒。

## 7. 起票時の見込みとの照合

- ctrl/inj の重み総数 528919、基準点397138、差131781: 実測で裏づけた。
- 信号到達性: inj の入力変更で最大差 `0.0577579140663147`、ctrl は `0.0` と再測定した。
- 評価条件: ctrl/inj は分母と一致し、偽 temporal 条件では不一致と実測した。
- 母集団: train 9657 / val 1515 / test 4265、欠落・余剰0を実測した。
- 五つの把持次元は線形下見以上: 実測で裏づけた。
- 推論信号を渡すと accuracy が上がる: 否定された。全 seed で下がった。
- Phase B 推定10時間: 実測は6本合計の `elapsed_seconds` 合計で約41.1秒だった。

## 8. 次にすべきこと

### 効果があった場合

方向性のある効果はあったが負方向なので、現設計を有望手法として進めない。まず hemostasis の
悪化を frame/segment 単位で局在化し、predicted sigmoid の較正・連結後のスケール・phase head の
過適合を調べる。

### 検出できなかった場合

今回は該当しない。全 seed 同符号かつ比5.3452で検出したため、種を増やすより設計変更を優先する。

### 推論の出来が低かった場合

今回は該当しない。5次元は下見以上だった。次は教師対応の再確認より先に、信号の形、confidence
calibration、ゲート／正則化、phase に有用な相互情報量を疑う。

## 9. ゲートと検証

- G1: PASS。実装・特徴・教師・重み同数・事前登録固定・GPU空きを実測。
- G2: PASS。6 run完走、必須証跡・条件・母集団・task_id・索引6行を実測。
- G3: PASS。事前登録の paired pstd / ddof=0 / 符号条件を変更せず適用。
- L3: `7 PASS / 0 WARN / 2 SKIP / 0 FAIL`。SKIP は未指定の `cuda_ext_loaded` と `deterministic_flags`。
- 近接テスト: `25 passed in 0.85s`。
- `audit/effect.json` と生データの再照合: 6 run / 9工程 / 5次元すべて一致。

## 10. Deviations

1. generic task 手順では L3 が Phase A より先だが、P4 は Phase A の prereg commit 後でなければ
   通らない。初回 FAIL で停止し、ユーザー選択1により SPEC 固有順序を優先して再開した。
2. 原設定の task_id が旧実装契約のままで CLI 上書きも無いため、禁止された `configs/**` を変えず、
   task 配下に task_id だけ置換した実行用コピー2件を作った。その他の内容が原本と一致することを検証した。
3. detached 起動は実行基盤が子 process を回収し、run未生成・log 0 byteだった。継続PTYへ切り替えた。
4. runindex harvester が新 step の `arm` と `phase_accuracy` を拾わないため、Phase C は生 metrics と
   checkpoint 再評価で行った。変更禁止の harvester は直していない。

## 11. Issuer defects

1. `self_contradiction`: generic task 手順は L3非0で停止を要求するが、本契約は L3が要求する
   prereg commit を Phase A で作る。指示順に実行すると必ず `P4 prereg_committed FAIL` となり、
   ユーザー判断なしでは Phase A に到達できない。
2. `check_does_not_check`: validate/preflight は `outputs.stamp.task_id_in` を検査するが、指定された
   原設定2件の task_id が旧契約のままであることを検出しなかった。原設定で実行すると6 runが
   今回 task と結び付かず、expected_runs の索引条件を満たせない。
3. `self_contradiction`: decision rule は差の絶対値を使い、満たせば「効果あり」とする一方、仮説と
   意思決定は inj が ctrl を上回る改善を問う。今回のように全 seed で負でも文字どおりには
   「効果あり」となるため、方向を含む verdict 語彙が必要である。

## 12. Positive controls

- recipe照合: temporal layers を1つ変えた偽条件は不一致、実在 ctrl/inj は一致。
- decision rule: `[0.019, 0.020, 0.021]` は PASS、符号混在 `[0.020, -0.010, 0.020]` は FAIL。

## 13. Unknowns

- 把持推論 accuracy が高いのに phase accuracy が下がる因果機構は本契約では特定していない。
- disinfection / dressing / irrigation は両腕とも工程別 F1・Jaccard が0で、注入効果は UNKNOWN。
