# audit — T-2026-09-27-stage2-prep

ホスト aolab、分岐 `feat/stage2-prep`（起点 `origin/phase0` = 1ac2d2c9）。GPU は使っていない。

## 開始

- 利用者の指示のパス `~/slocal/m2` はこのホストに無く、`~/slocal2/m2` で実行した
- 未追跡の session digest 4 件を `git stash push -u -m "session digests before T-2026-09-27-stage2-prep" -- docs/sessions/digest` で退避（`feat/stage1-phase-tower-r3` 上）
- `git checkout phase0 && git pull --ff-only` → Already up to date、清浄
- `make task-start TASK=T-2026-09-27-stage2-prep` → 分岐作成、`.sync-pause` 作成、取り込み OK
- `~/bin/m2-sync.sh` の `sync-pause` の出現 2 件（抑止に対応済み）
- `make task-validate` → OK。`make task-preflight` → 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
  （SKIP: P2 cuda_ext_loaded、P3 deterministic_flags、P4 prereg_committed、P5 frozen_source_hash、P11 gpu_free、P12 refs_resolved、P13 symmetry_table_complete、P14 proposal_card_checked）。P9 spec_lint は該当なし

## Task A

- 規約のアンカー 11 件（split, eval_recipe, frozen_source, sigma, prohibitions, env_p0, naming, issuer_cautions, proposal_gate, folds, symmetry）
- 注釈 `data/annotations/egosurgery_tool_folds/{A..E}/instances_{train,val,test}.json` の categories は 15 件で全 15 ファイル同一。9 クラスは完全一致で全件存在 → G1 pass
- 評価集合での欠落: A val Retractor、B val Electric Cautery・Hook、C test Electric Cautery、D test Hook、E val Electric Cautery・Mouth Gag（per_class_ap の NaN と一致）
- 計算器の現行: K 既定 3、装置 2、24 h/日、精度は単精度（TF32 の倍率なし）。det_iface_w1 4.00 h、W2 4.82 h、det_tower_train 14.13 h、W3 8.35 h
- 試験（変更前）: 6 failed / 669 passed / 収集エラー 1（`--continue-on-collection-errors`）
- 占位: runindex_commit 2fb7c905…、counts 1911/718/1506、conventions_rev 4369cf5e…

## Task B

- 末尾に det_groups・crossfit 節を追加、変更履歴に 1 行。節ごとの sha256（先頭 16 桁）を前後で比較し、末尾空白を除いて naming 以外は同一。naming の差は履歴の 1 行のみ
- L2: `det_groups`・`crossfit` 解決、`det_group`・`crossfitt` で L2-5

## Task C

- `python scripts/build_stage1_group_ap.py` → `docs/stage1/D_group_ap.md`、`experiments/baselines/stage1_dtower_r2/group_ap.json`
- 群に掛かる欠落は E val の Mouth Gag（陰性対照群を 3 クラスで平均）のみ

## Task D

- 付録 C を雛形の一覧表＋見出しの様式で `docs/proposals/2026-09-27-ptower-20.md` に置いた。付録 C の全行が本文に含まれることを機械で照合
- `check_proposal.py` 検出 0 件 → G2 pass。#6 の数字を消した写しで検出 1 件

## Task E

- 計算器の履歴: d63ab0aa（9/16 初版）→ af53fff0（9/17、W2 4.00→4.82）→ 5681ab5b（9/21、det 8.00→8.35、W3 8.00→8.35）→ f8ce187f（9/27、det 8.35→14.13）。TF32 を入れた commit は無い
- 前提を戻した再計算: 9/16 84.1〜111.9、9/17 単精度 87.5〜116.6、9/17 TF32 74.0〜98.7、9/21 K3 87.9〜117.0、9/27 K3 92.9〜122.1、9/27 K2 88.8〜118.0（報告値と全一致）
- 交差適合の二行: 検出 20 本 × 14.13 h = 282.6、工程 20 本 × 81.0/28 h = 57.9、計 340.5 GPU 時間
- `--check-doc docs/stage0/B1_tier1_cost_estimate.md` 差 0、B2 は `--doc-sections history,crossfit` で差 0。`--check-sources` 0、`--check-coverage` 0、`--control` PASS

## Task F

- `make task-validate` OK
- `make forbidden-check TASK=T-2026-09-27-stage2-prep` pass、違反 0（許可: context/conventions.md、group_ap.json）
- `make spec-check TASK=T-2026-09-27-stage2-prep` pass
- `make docs-check` 1 件（`docs/proposal-gate.md:41`）。`origin/phase0` の一時 worktree でも同じ行が出る既存のもの
- 試験（変更後）: 6 failed / 673 passed / 収集エラー 1。失敗は変更前と同一
- `ruff check` 変更した Python 3 ファイルで All checks passed
