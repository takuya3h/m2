# Phase A audit

## Environment and revisions

- repository: `/home/ubuntu/slocal2/m2`
- branch: `feat/grasp-injection-effect`
- venv python: `/home/ubuntu/slocal2/m2/.venv/bin/python`
- conventions revision: `d422b08`（契約と一致）
- runindex revision: `44697d9 2026-08-11T08:41:54+00:00`（契約と一致）
- sync pause: 実行前に設置済み

## G1 existence checks

- training entrypoint: `scripts/train_grasp_phase_injection.py`
- model: `src/egosurgery/models/temporal/grasp_inference_injection.py`
- arm configs: `configs/stage/s4_grasp_injection_ctrl.yaml`, `configs/stage/s4_grasp_injection_inj.yaml`
- frozen features: `train_gap.npz`, `val_gap.npz`, `test_gap.npz`
- grasp supervision: `data/annotations/egosurgery_hts/hand_tool_seg/{train,val,test}.json`

## Structural audit

出所: `phase_a_structural.json`

- baseline trainable parameters: `397138`
- ctrl trainable parameters: `528919`
- inj trainable parameters: `528919`
- ctrl minus baseline: `131781`
- baseline recipe vs ctrl: `true`
- baseline recipe vs inj: `true`
- baseline recipe vs false temporal condition: `false`
- population: train `9657`, val `1515`, test `4265`
- structural audit: `all_pass=true`

## Preregistration and preflight

- preregistration commit: `34572bbddd7f37c0305b94b93192f8f136150e97`
- 初回 L3: `P4 prereg_committed FAIL` のため停止
- ユーザー選択 1 により、SPEC 固有手順で preregistration を固定し `spec.yaml` に刻印
- 再実行 L3: `7 PASS / 0 WARN / 2 SKIP / 0 FAIL`
- SKIP: `cuda_ext_loaded`, `deterministic_flags`（いずれも `plan.env.preflight` に指定なし）

## GPU availability

2026-08-15 09:28:00 UTC 時点:

- GPU 0: RTX A6000, 10 MiB / 49140 MiB, utilization 0%, compute process none
- GPU 1: RTX A6000, 10 MiB / 49140 MiB, utilization 0%, compute process none

## Task stamp compatibility

原設定2件の `task_id` は実装契約 `T-2026-08-11-grasp-inference-injection-impl` のままで、
entrypoint に `--task-id` は無い。本 task の `outputs.stamp.task_id_in: metrics.json` を満たし、
禁止された `configs/**` と学習コードを変更しないため、`audit/run_ctrl.yaml` と
`audit/run_inj.yaml` を作成した。原本との非 `task_id` 部分は完全一致し、両腕の差は
description / arm / signal のみであることを機械確認した。

## G1 verdict

PASS
