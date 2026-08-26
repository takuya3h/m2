# 変更範囲の一覧

基準: origin/phase0（9963035 Merge pull request #152 from takuya3h/feat/oracle-ce）
分岐: feat/lovo-decision-rule
生成時刻: 2026-08-26 11:02:59 JST

## 本契約が加えた commit

- 55218c2 analysis(lovo): re-judge every LOVO conclusion under rules that drop the independence assumption
- 0fc8b36 fix(lovo): correct the finite-population term in the replicated-LOVO variance
- 7e5d49a feat(lovo): capture per-loop fold values and add the replicated-LOVO rule
- 2af12fe fix(lovo): sweep the negative control until each rule flips
- 9139e01 feat(lovo): apply every rule to every conclusion and check both controls
- d2ca436 docs(lovo): enumerate the existing conclusions to be re-judged
- 3cfb6a5 feat(lovo): add the harness that recovers per-fold values without touching the scripts
- 5c7f267 docs(lovo): record the rule-selection criteria before any new rule exists

## 本契約が触れたファイル（f844994..HEAD）

     .../analysis/lovo_decision_rule/CRITERIA.md        |    64 +
     experiments/analysis/lovo_decision_rule/REPORT.md  |   446 +
     experiments/analysis/lovo_decision_rule/analyze.py |   119 +
     .../analysis/lovo_decision_rule/compute_r2.py      |    54 +
     .../analysis/lovo_decision_rule/conclusions.py     |    79 +
     .../analysis/lovo_decision_rule/dump_folds.py      |    71 +
     .../analysis/lovo_decision_rule/dump_folds_loop.py |    97 +
     .../lovo_decision_rule/folds/capacity_control.json |   708 +
     .../lovo_decision_rule/folds/capacity_of_head.json |   570 +
     .../folds/capacity_of_head_denoise.json            |   570 +
     .../lovo_decision_rule/folds/denoise_variants.json |   708 +
     .../lovo_decision_rule/folds/flicker_scaling.json  |  1666 +++
     .../lovo_decision_rule/folds/gap_vs_presence.json  |   571 +
     .../lovo_decision_rule/folds/noise_structure.json  |   708 +
     .../lovo_decision_rule/folds/noise_testonly.json   |   708 +
     .../lovo_decision_rule/folds/presence.json         |   434 +
     .../folds/prune_across_sources.json                |  1666 +++
     .../lovo_decision_rule/folds/prune_by_entropy.json |  1667 +++
     .../lovo_decision_rule/folds/prune_ubiquitous.json |   571 +
     .../folds/receptive_field_denoise.json             |  1118 ++
     .../folds/receptive_field_prune.json               |  1118 ++
     .../lovo_decision_rule/folds/recommended.json      |   571 +
     .../lovo_decision_rule/folds/signal_form.json      |   571 +
     .../analysis/lovo_decision_rule/make_report.py     |   303 +
     .../lovo_decision_rule/r2/capacity_control.json    |     1 +
     .../lovo_decision_rule/r2/capacity_of_head.json    |     1 +
     .../r2/capacity_of_head_denoise.json               |     1 +
     .../lovo_decision_rule/r2/denoise_variants.json    |     1 +
     .../lovo_decision_rule/r2/flicker_scaling.json     |     1 +
     .../lovo_decision_rule/r2/gap_vs_presence.json     |     1 +
     .../lovo_decision_rule/r2/noise_structure.json     |     1 +
     .../lovo_decision_rule/r2/noise_testonly.json      |     1 +
     .../analysis/lovo_decision_rule/r2/presence.json   |     1 +
     .../r2/prune_across_sources.json                   |     1 +
     .../lovo_decision_rule/r2/prune_by_entropy.json    |     1 +
     .../lovo_decision_rule/r2/prune_ubiquitous.json    |     1 +
     .../r2/receptive_field_denoise.json                |     1 +
     .../r2/receptive_field_prune.json                  |     1 +
     .../lovo_decision_rule/r2/recommended.json         |     1 +
     .../lovo_decision_rule/r2/seedcheck_seed42_a.json  |     1 +
     .../lovo_decision_rule/r2/seedcheck_seed42_b.json  |     1 +
     .../lovo_decision_rule/r2/seedcheck_seed43.json    |     1 +
     .../lovo_decision_rule/r2/signal_form.json         |     1 +
     .../analysis/lovo_decision_rule/r2_aggregate.py    |    66 +
     .../analysis/lovo_decision_rule/r2_results.json    |  2882 ++++
     .../analysis/lovo_decision_rule/r2_stability.json  |  1357 ++
     .../analysis/lovo_decision_rule/replicate_lovo.py  |    60 +
     .../analysis/lovo_decision_rule/results.json       | 13770 +++++++++++++++++++
     experiments/analysis/lovo_decision_rule/rules.py   |    78 +
     .../analysis/lovo_decision_rule/run_dumps.sh       |    18 +
     .../analysis/lovo_decision_rule/run_dumps2.sh      |    14 +
     .../analysis/lovo_decision_rule/run_dumps3.sh      |    12 +
     experiments/analysis/lovo_decision_rule/run_r2.sh  |    14 +
     .../analysis/lovo_decision_rule/run_r2_loop.sh     |    11 +
     .../analysis/lovo_decision_rule/run_seedcheck.sh   |    15 +
     .../lovo_decision_rule/seedcheck_summary.json      |    20 +
     56 files changed, 33494 insertions(+)

## 本契約が触れていない未追跡（同期で到着した他ホストの成果物）

    ?? experiments/analysis/error_shape_selectivity/
    ?? tasks/T-2026-08-26-lovo-decision-rule/

## 禁止領域の検査の内訳

    本契約の成果物（契約の outputs.destination）        56 件
    他ホストの契約 error_shape_selectivity（未追跡）      7 件
    origin/phase0 に在り私の HEAD に無い分（PR a4a95cf） 7 件

検査は experiments/ 全体を禁止領域とし、契約の outputs.destination を除外しない。
本契約が禁止領域へ触れたものは一件も無い。
