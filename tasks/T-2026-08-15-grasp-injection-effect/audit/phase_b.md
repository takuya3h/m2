# Phase B audit

## Runs

| arm | seed | run | completed | elapsed_seconds |
|---|---:|---|---|---:|
| ctrl | 42 | `s4_grasp_injection_001_frozen_tecno_grasp_inference_ctrl_seed42` | true | 6.478691497119144 |
| inj | 42 | `s4_grasp_injection_002_frozen_tecno_grasp_inference_inj_seed42` | true | 7.339944418985397 |
| ctrl | 123 | `s4_grasp_injection_003_frozen_tecno_grasp_inference_ctrl_seed123` | true | 6.914426580071449 |
| inj | 123 | `s4_grasp_injection_004_frozen_tecno_grasp_inference_inj_seed123` | true | 6.815076003083959 |
| ctrl | 456 | `s4_grasp_injection_005_frozen_tecno_grasp_inference_ctrl_seed456` | true | 6.6095304801128805 |
| inj | 456 | `s4_grasp_injection_006_frozen_tecno_grasp_inference_inj_seed456` | true | 6.91641585691832 |

全値の出所は各 run の `metrics.json`。

## G2 checks

- completed runs: 6
- arm/seed pairs: ctrl/inj × 42/123/456
- required artifacts: 全6本で欠落なし
- task_id: 全6本の `metrics.json` と `config.yaml` で `T-2026-08-15-grasp-injection-effect`
- frozen source: 全6本で `relation_detr_seed42`
- population: 全6本で train 9657 / val 1515 / test 4265
- evaluation recipe: 全6本で online_causal / jaccard strict
- trainable parameters: ctrl/inj とも 528919（Phase A の実測）
- denominator recipe vs ctrl/inj: true / true
- false temporal condition: false（positive control）
- runindex rows with task_id: 6

## Deviations and implementation mismatch

1. 最初の二回の detached 起動は、実行基盤がシェル終了時に子 process を回収したため、
   Python 開始前に消失した。run directory なし、log 0 byte、GPU process なしを確認し、
   継続 PTY で一本目を実行した。生成 run 数には数えない。
2. `make runindex` 後、`runindex/index.csv` には6行入ったが `arm=unknown`、
   `runindex/experiments.csv` の `accuracy_mean` は空欄だった。生 `metrics.json` には
   `arm` と `phase_accuracy` が存在するため、新 step に対する harvester の対応不足である。
   契約で変更禁止の `tools/harvest_runindex.py` は変更しない。

## G2 verdict

PASS
