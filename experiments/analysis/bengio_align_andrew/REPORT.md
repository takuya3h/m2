# bengio を andrew に揃えた結果（T-2026-11-02-bengio-align-andrew）

2026-11-02 12:13〜12:53 UTC（21:13〜21:53 JST）、bengio。andrew は読むだけ。GPU は Task C の評価一本（GPU 0）だけ使った。
手続きと全件の記録は `tasks/T-2026-11-02-bengio-align-andrew/audit.md`。この置き場には同期の対象の型（`.py`・`.npy`・`logs` など）を置いていない。

## 揃えた後の値

| 項目 | 揃える前（bengio） | 揃えた後（bengio） | andrew |
|---|---|---|---|
| Relation-DETR source（件・要約値） | 127・3ade18f0709362fa… | 142・2f08e5213cb5c377… | 142・2f08e5213cb5c377… |
| Relation-DETR all | 140・89dc93b4a82f1e06… | 155・20f15c061b435ce4… | 155・20f15c061b435ce4… |
| 三分類（andrew だけ・bengio だけ・違う） | 15・0・8 | 0・0・0 | — |
| `checkpoints` 12 件 | — | 前後一致 | 一致（調査） |
| MS-Deform-Attn の `build.ninja` | 重ねの BODY の `.cu` を指す（2,721 B） | bengio main の `.cu` を指す（2,706 B・f72b62a067a6540a…） | 2,706 B・f72b62a067a6540a…（差 0 行） |
| 同 `.so` | b16285382d085e2b… | 1a05ed5b47e1b041… | 79b55a8ab270ed6d…（**不一致**） |
| Stage 2 の材料 17 件 | 無い | andrew と同じ経路、17/17 一致 | — |

揃える前の 8 件は、版管理下の `experiments/analysis/bengio_andrew_env_survey/b/` の andrew の版と差分から 8/8 戻せることを確かめてから揃えた。

## 検出塔の評価（D*-COCO 折り A seed 42、checkpoint 30d199b1…、val）

| 指標 | 値 | 記録 | 差 |
|---|---|---|---|
| overall AP | 0.7273450248398429 | 0.7273450248398429 | 0.0 |
| 標的群 AP | 0.7950748008550897 | 0.7950748009 | −4.49e-11 |
| 陰性対照群 AP | 0.6726631817581498 | — | — |
| AP50 | 0.851807431425236 | — | — |

入口 `scripts/stage2pilot/pd_eval.py --cfg plain`（bengio main の Relation-DETR と `.venv-relation-detr`）。拡張の読み込み（`ms_deform_attn_ext True`、`Loading extension module`）と checkpoint の読み込み（`warm-start from`、`missing []`）が評価の記録にある。
予測は repo の外 `~/slocal2/stage2pilot_store/T-2026-11-02-bengio-align-andrew/plain_val_preds_seed42.json.gz`（0936a4c27416ad1f…）。

## 片付け

| # | 対象 | 結果 | 理由 |
|---|---|---|---|
| E1 | worktree `~/slocal2/m2-four` | 残した | 無視された未追跡に m2 本体に無い中身（実験の出力 74 件 314,363,184 B、wandb の run 23 本など）。利用者の決定 |
| E2 | worktree `~/slocal2/m2-s2fix-bengio` | 残した | 同（predictions 6 件 50,824,611 B）。利用者の決定 |
| E3 | worktree `wt_phase0` | 残した | 未追跡の spec.yaml 1 件が phase0 と違う中身。利用者の決定 |
| E4 | 分岐 `chore/evidence-map-a-place-start` | 片付けた | 39dd92d6 は phase0 の祖先 |
| E4 | E1・E2 の手元の分岐 | 残した | worktree を残したため（worktree が使っている） |
| E5 | 重ねの BODY `~/slocal2/s2fix-bengio-body` | 残した | 版管理下の台本 4 本が経路を既定値に持つ（設定からの参照） |
| E6 | `.git/info/exclude` の 5 行 | 残した | 23 行目を外すと 192 件 873,052,232 B が現れる。利用者の決定で 5 行とも残す |
| E7 | `~/m2-git-info-exclude.bak-20261019` | 残した | E6 を残したため |
| E8 | `third_party/Relation-DETR` の `__pycache__` 4 件 | 片付けた | — |
| E9 | `.venv-relation-detr/pyvenv.cfg.before_s2fix`、`/tmp/pyvenv.cfg.bak` | 片付けた | `pyvenv.cfg` は変えていない |
| E10 | `/tmp` の 22 件 | 片付けた | 作った契約が記録から 1 つに特定できた（`e/e10_remove.tsv`） |
| E10 | `/tmp` のほか 17 件と道具の置き場 | 残した | 契約が特定できない、または複数に当たる（`e/e10_candidates.tsv`） |

## 試験

開始時 11 failed・965 passed・1 error（名前 12）→ 終了時 11 failed・974 passed・0 error（名前 11）。差は `tests/test_stage1_dtower_convergence.py` の収集の失敗が消えた 1 件だけ（`util/convergence.py` が揃えて入った）。

## 残った違い（変わったものだけ）

- 拡張の `.so` の要約値は andrew と違う（`build.ninja` は同一）
- `.venv-relation-detr/pyvenv.cfg` は変えていない（andrew とは違うまま。調査の Task C）
