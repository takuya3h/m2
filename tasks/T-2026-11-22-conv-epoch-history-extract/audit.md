# audit — T-2026-11-22-conv-epoch-history-extract

ホスト andrew、repo `~/slocal2/m2`、分岐 `feat/conv-epoch-history-extract`。時刻は JST。`$O` = `experiments/analysis/conv_epoch_history_extract`。
道具は `$O/tools/ceh.py`（集合・目録・取り出し・対・表・要約）と `$O/tools/controls.py`（陽性対照）。どちらも本体の `.venv` で、記録を読むだけ。
GPU・学習・評価・推論・checkpoint の読み込みは使っていない。

## 0. 始める（手順書 0〜4）

- 開始時の分岐 `feat/dtower-class-error-breakdown`（前回の契約。清浄）。`feat/conv-epoch-history-extract` は手元にも遠隔にも無く、
  `tasks/T-2026-11-22-conv-epoch-history-extract` の履歴も無い。`.sync-pause` は無い
- 分類器（`scripts/task_start_classify.py`、比較先 origin/phase0 8395be39）: 6 分類すべて 0 件 → 「通す」
- `make task-start`: 分岐を origin/phase0 8395be39 から作成、`[task-start] .sync-pause を作成`（本契約が置いた目印。中身は task_id と branch の 2 行）、
  契約を台帳から取り込み `OK`、`[task-start] 完了。`
- `make task-validate`: `OK`（終了コード 0、WARN なし）
- `make task-preflight` 1 回目: 5 PASS / 0 WARN / 8 SKIP / 1 FAIL。FAIL は P6 decisions_answered（未回答 2 件）。2 件を利用者に選択式で示した
- 利用者の回答（2026-11-25、選択式）: (1) 停止条件に当たったときの続け方 →「当たったら止めて尋ねる」、(2) 4・8 epoch 目が一致しなかった場合の表の読み方 →「SPEC §5.5 のとおり」。
  `meta.amendments` に記録し、`decisions_required` を空にした（中身は spec の amendments の reason）
- `make task-preflight` 2 回目: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL。SKIP は P2 cuda_ext_loaded・P3 deterministic_flags・P11 gpu_free（契約に記載なし）、
  P4・P5・P13・P14（exp のみ）、P12（解決する参照なし）。P9 spec_lint は「規則 9 件を検査し該当なし」
- 稼働中の `~/bin/m2-sync.sh` は目印に対応済み（`grep -c sync-pause` = 2）。`~/claude-sync/sync-alerts.log` の最後の「一時停止中」は 2026-11-21 06:59:51（前の契約のとき）で、
  本契約の間の行は出ていない（常駐処理が本契約の間に回ったかは確かめていない）

### 解決された参照（手順書 3）

`contract.inject_verbatim` の 5 節（prohibitions・issuer_cautions・env_p0・folds・symmetry）は `context/conventions.md`
（`git log -1 -- context/conventions.md` = 2d946b07 = `contract.conventions_rev`）の原文を読んだ。原文はその版の該当アンカー
（`prohibitions` 98 行〜、`env_p0` 109 行〜、`issuer_cautions` 154 行〜、`folds` 297 行〜、`symmetry` 367 行〜）にあり、要約せずに従う。
denominator・frozen_source・sigma_policy の参照は無い。`inputs.data.split_files`（`data/splits/ego_val.txt`）は SPEC §0 のとおり参照しなかった。
env_p0 は「学習・評価スクリプトを起動する前」の規約で、本契約は起動しない。読むだけの道具も `.venv` の python で回した。

### meta.created_from と conventions_rev の測り直し（SPEC §0）

    $ git log -1 --format=%h -- runindex/            → 036d6a60
    $ csv.DictReader の行数（見出し行を除く）         → index 2,668・experiments 1,347・verdicts 2,067
    $ git log -1 --format=%h -- context/conventions.md → 2d946b07
    起票時の値と一致。差し替えなし（amendments の diff に一致を記録）

## Task A — 開始状態と記録の確かめ（G1）

印 `$O/start/STARTED_MARKER` を 2026-11-25 10:54:57 JST に置いた（変更の検査の基準）。予測（SPEC §5.6）は集合と値を取り出す前の
10:59:17 に `$O/start/predictions.txt` へ写した。

### A-1 分岐・起点・未追跡（`$O/start/a1_git.txt`）

    $ git branch --show-current; git rev-parse HEAD; git merge-base HEAD origin/phase0; git rev-parse origin/phase0
    feat/conv-epoch-history-extract
    8395be39c4e32ea72cc6553192abd594a0ada87d（3 つとも同じ）
    $ git status --porcelain --untracked-files=all
    取り込んだ契約の 2 ファイル（SPEC.md・spec.yaml）と、直前に置いた $O/start/ の 3 ファイルだけ

### A-2 試験と仮想環境（`$O/start/a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_venv.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped（34.53 s）
    失敗の名前（6）: test_engines::test_mmdet_trainer_eval_recipe_in_metrics、test_fetch_task::test_rejects_unknown_file_name、
      test_research_logger の 4 件（test_log_run_idempotent・test_run_logging_invokes_log_run_on_finally・
      test_run_logging_no_double_post_on_normal_exit・test_run_logging_swallows_exception_in_user_block）。前回までの契約の開始時と同じ 6 件
    $ uv pip list --python .venv/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0（108 行。前回の契約の開始時と同じ）

### A-3 読む集合（`$O/start/sets.json`、`ceh.py sets`）

集合は名前の一部ではなく記録の欄で作った。`config.yaml` の `task_id`、`metrics.json` の `converge`（固定の長さは `metrics_ep4.json` の在否）、
`command.sh` の `--exp-prefix`。三つの契約の記録とは、run の一覧の道具（graph-pilot の `tools/run_arms.sh` の繰り返し、
irn-hice-htt-pilot の `tools/jobs.py` の `chk_jobs()+main_jobs()`、graph-t2p-match の `tools/jobs.py` の `graph_jobs(LONG)`・`tp_jobs(LONG)`）が作る
（接頭辞, 名前）の集合と、RESULT の本数で比べた。

    config.yaml の task_id で集めた run: graph-pilot 99、irn-hice-htt-pilot 253、graph-t2p-match 191
    収束規則の集合 344 本 = GP 96 + IHH 248、固定の長さの集合 183 本 = グラフ 147 + T→P 36
    {"GP": {"n_observed": 96, "n_record": 96, "n_record_count": 96, "equal": true, "n_only_observed": 0, "n_only_record": 0},
     "IHH": {... 248, 248, 248, true, 0, 0}, "T2P_GR": {... 147, 147, 147, true, 0, 0}, "T2P_TP": {... 36, 36, 36, true, 0, 0}}
    conv_history_missing [] / fixed_history_missing [] / fixed_ep_missing []

除いた 16 本（接頭辞が腕・確かめ・固定の長さの主の群でない）: graph-pilot の `grasp_hand_graph_chk` 2（試走、収束規則なし）・`grasp_hand_graph_repro` 1、
irn-hice-htt-pilot の `repro_gr` 1（**収束規則あり**。回し直しで、腕でも確かめでもない）・`repro_tp` 1・`smoke` 3、
graph-t2p-match の `ep4chk` 3・`ep4chk_tp_W1〜W3` 3（4 epoch で止める確かめ。`metrics_ep4.json` を持つ）・`repro_gr` 1・`repro_tp` 1。
`converge` の欄だけで集めると irn-hice-htt-pilot は 249 本、`metrics_ep4.json` だけで集めると固定の長さは 189 本になる（起票者の誤り 1）。

### A-4 読む記録の hash（`$O/start/hashes_start.json`、`ceh.py hashes`）

    {"n_files": 3188, "manifest_sha256": "60c5ff8fe9509195c9a472c62708526a95eee7fa7dde3d75593a6e4f392a8875"}

対象は 527 本の `config.yaml`・`command.sh`・`metrics.json`・`metrics_last.json`・`logs/history.json`・`metrics_ep{4,8,12,16}.json` と、
読んだ道具 4 件（前の二つの `jobs.py`、`run_arms.sh`、`scripts/stage2pilot/dp_train.py`）。

### G1 — pass

集合が三つの契約の記録と集合として一致し（4 群とも差 0）、収束規則の集合の 344 本すべてに `logs/history.json` が在り、
その記録が run の結果の記録と一致した（B-1。G1 の「一致する」は B-1 の突き合わせで確かめた）。escalate_if の 5 条件はどれも当たっていない。

## Task B — 取り出しと一致の確かめ（G2）

### B-1 取り出しと突き合わせ（`$O/epochs.csv`、`$O/b/checks.json`、`ceh.py extract`）

学習率を下げる前・後の印は `dp_train.py` の学習の繰り返し（735〜870 行）を読んで決めた: epoch E の評価の後に `ConvergeRule.step` が "drop" を返すと
学習率を 0.1 倍にし、`lr_drop_epoch = E`、history の E の行に `lr`（下げる前）と `lr_after` を書く。E までが下げる前、E+1 からが下げた後。
突き合わせは、history の `lr_after` の行が `lr_drop_epoch` の 1 行だけであること、最初に学習率が変わる行が E+1 であること、E までの学習率が初期値、
E+1 からが初期値の 0.1 倍であることの全部。

    {"n_runs": 344, "n_rows": 10012, "n_bad": 0, "all_reconcile": true, "epoch4_8_all_pre": true, "all_have_epoch16": true,
     "n_post": {"4": 0, "8": 0, "12": 80, "16": 145}, "lr_drop_min": 9, "lr_drop_max": 60, "epochs_run_min": 17}

突き合わせの 8 項目（epoch の数と並び、結果の回 = best_epoch、結果の回の J と acc、最後の回の番号、最後の回の J と acc、学習率を下げた回）が 344/344 本で一致。
値の比べは浮動小数のちょうどの一致（`==`）。`epochs.csv` の値は `repr` で書いた（controls f で history.json と差 0.0）。

### B-2 対と一致の確かめ（`$O/b/pairs.json`、`ceh.py pairs`）

対は config で作った: 型・W・N・L・信号の sha256 と正解の印の並び（train と val）が同じもの。そのうえで config を欄ごとに比べ、
長さの規則の欄（`stop_rule.*`・`record_epochs`・`steps_per_epoch`・`optim_groups*`・`iface_last_init*`・`result_selection`）と
識別子・置き場の経路の欄（`task_id`・`unofficial`・`arm`・`gr.dir`・`signals_*[i].path`）のほかの違いを数えた。

    {"n_pairs": 72, "n_conv_paired_unique": 72, "n_conv_multi_paired": 0, "n_config_other_diff": 0, "config_other_diff_keys": [],
     "arm_map": [[D, D-CF], [DG, DG-CF], [DGH, DGH-CF], [DGH-GT, DGH-GT], [DGH-U, DGH-U-CF], [DGH-noCF, DGH-noCF], [DH, DH-CF], [empty, empty]],
     "fixed_hist_equals_ep_all": true}
    epoch 4 : 対 72、J 同じ 72、acc 同じ 72、max abs ΔJ 0.0、Δacc 0.0、下げた後 0
    epoch 8 : 対 72、J 同じ 72、acc 同じ 72、max abs ΔJ 0.0、Δacc 0.0、下げた後 0
    epoch 12: 対 72、J 同じ 62、acc 同じ 63、両方 62、max abs ΔJ 0.0711、Δacc 0.0218、下げた後 10
    epoch 16: 対 72、J 同じ 51、acc 同じ 52、両方 51、max abs ΔJ 0.0576、Δacc 0.0178、下げた後 23
    下げる前の対: 12 epoch 目 62/62、16 epoch 目 49/49 が両方同じ。下げた後の対: 12 epoch 目 0/10、16 epoch 目 2/23（W1 の A0 の 2 対）が両方同じ

起票者の見込み（graph-pilot の A0・D・DG・DH・DGH・DGH-U ↔ graph-t2p-match の empty・D-CF・DG-CF・DH-CF・DGH-CF・DGH-U-CF、DGH-noCF・DGH-GT は同名）は、
信号の sha256 の一致で確かめた（`arm_map`）。対は最大 72 組の見込みどおり 72 組（A0 は s1・s4、D・DG・DH は s1・s3 だけ固定の長さの run が在る）。
固定の長さの run の history.json の 4・8・12・16 epoch 目は `metrics_ep*.json` と 72/72 で一致（追加の確かめ）。W・腕ごとの表は REPORT §5.1。

### B-3 流用の確かめ（完了判定 g。`$O/b/pairs.json` の `chk`・`chk_summary`）

| 契約 | 流用 | 比べた run | 4・8・12・16 epoch 目の一致 |
|---|---|---|---|
| irn-hice-htt-pilot | A0 の s2〜s4 ← s1 | IRN・HiCE・HTT の A0 の s4・W1（確かめ）と s1・W1 | 3/3 ずつ、差 0.0 |
| irn-hice-htt-pilot | HiCE の D ← HiCE の A0 | HiCE の D の s1・W1（確かめ）と A0 の s1・W1 | 1/1 ずつ、差 0.0 |
| irn-hice-htt-pilot | HiCE の DH の s3・s4 ← s1・s2 | HiCE の DH の s3・W1（確かめ）と s1・W1 | 1/1 ずつ、差 0.0 |
| irn-hice-htt-pilot（参考） | A0 とグラフの型の A0 | 3 型の A0 の s1 と GR の A0 の s1（W1〜W3） | 9/9 ずつ、差 0.0 |
| graph-t2p-match | 空の s2〜s4 ← s1 | 空の s4 と s1（W1〜W3） | 3/3 ずつ、差 0.0 |
| graph-t2p-match | 辺の無い腕の s2・s4 ← s1・s3 | D-noCF の s2 と s1（W1〜W3） | 3/3 ずつ、差 0.0 |

計 80 行（20 組 × 4 epoch）がすべて一致。収束規則の側は 12・16 epoch 目に下げた後の run を含むが、比べる二本は同じ値の列なので一致した。

### G2 — pass

72 組の全対で 4・8 epoch 目の J と acc の一致・不一致と最大の差が記録され、72/72 が両方ちょうど同じ（最大の差 0.0）。escalate_if に当たっていない。

## Task C — 表と報告

### C-1 表（`$O/REPORT.md`・`$O/c/tables.json`・`$O/c/summary.json`、`ceh.py report`・`ceh.py summary`）

    {"52": 384, "53": 384, "54": 204}（表の行の数。§5.2 は 4 型 × 3 W × 8 腕 × 4 設定、§5.3 は 4 型 × 3 W × 8 差 × 4 設定、§5.4 は 3 W × 68 行）

流用は SPEC §4 のとおり（収束規則: irn-hice-htt-pilot の 44 組み合わせ。固定の長さ: graph-t2p-match の空と辺の無い腕）。REPORT の ‡ がその印。
†（学習率を下げた後）は 4・8 epoch 目に 0 個。§5.5 の「一致しなかった W・腕」は 0 件で、表の読み方の印は付かない。

### C-2 陽性対照（`$O/c/controls.json`、`ceh.py controls`）

    {"a": {"nonexistent_count": 0, "zsh_count": 6},
     "b": {"base_all_equal": true, "added_equal_GP": false, "added_only_observed": [["grasp_hand_graph_arm", "GR-W9-N10-L1_DGH_conv"]], "missing_base": 0, "missing_after_removal": 1},
     "c": {"run": "grasp_hand_graph_arm_001_GR-W1-N10-L1_empty_conv_seed42", "base_all": true, "shift_result_jaccard_ok": false, "shift_last_accuracy_ok": false, "extra_epoch_n_epochs_ok": false},
     "d": {"mark_epoch4_drop3": "post", "mark_epoch4_real": "pre", "lr_marks_agree_after_edit": false, "lr_marks_agree_real": true},
     "e": {"n_eq_j_ep4_base": 72, "n_eq_j_ep4_shifted": 71, "wrong_W_dj_ep4": 0.05699218923818472, "wrong_W_da_ep4": -0.0013201320132013583,
           "wrong_W_config_other": ["receiver.mode", "receiver_optim.lr", ..., "scope", "scope_check.*", "trainable.*"（18 欄）], "wrong_W_in_pair_list": false},
     "f": {"n52": 1536, "n53": 1536, "n54": 816, "max_dev_52": 0.0, "max_dev_53": 0.0, "max_dev_54": 0.0, "max_dev_csv_vs_history": 0.0,
           "shifted_copy_dev": 1.000000000001e-06, "shifted_detected": true},
     "g": {"n_rows": 80, "n_eq": 80, "shifted_eq": false},
     "h": {"added_control": 1, "self_diff": {"added": [], "removed": [], "changed": []}}}

- a は `scripts/grasppilot/proc_enum.py --match-exe`。存在しない経路 `/nonexistent/bin/python9` で 0 件、`/usr/bin/zsh` で 6 件
- f の測り直しは `epochs.csv` と表の道具の流用の関数を通らない: 各 run の history.json と `metrics_ep*.json` を読み直し、流用を別に書き下して比べた
- 写しはすべてメモリの中で作った。記録のファイルは変えていない（C-3）

### C-3 変えていないこと（完了判定 h）

    $ ceh.py hashes <scratchpad>/hashes_end.json → {"n_files": 3188, "manifest_sha256": "60c5ff8f…"}（開始時と同じ）
    diff_manifest(開始, 終了) → {"added": 0, "removed": 0, "changed": 0}
    $ find experiments/phase1 /home/ubuntu/slocal2/stage2pilot_store experiments/analysis -newer $O/start/STARTED_MARKER（$O を除く） → 0 件
    $ pytest（A-2 と同じ命令） → 6 failed, 985 passed, 5 skipped（29.31 s）。失敗の名前は開始時と diff で同じ
    $ git diff --stat（commit の前） → 追跡下の変更なし（新しいファイルだけ）
    $ make forbidden-check TASK=T-2026-11-22-conv-epoch-history-extract
      {"status": "pass", "changed": 26, "checked": 26, "effective_allowances": ["experiments/analysis/conv_epoch_history_extract/"], "permitted": 18 件, "violations": []}（報告を書いた後、commit の前。報告の前の回は changed 19・許可 17）
    $ make forbidden-check   （対照: TASK なし。allow_write を読まない）
      {"status": "fail", "task": null, "violations": 18 件（本契約の $O の下の 18 ファイルが「禁止領域 experiments/ の内側」）}

`$O/tools/__pycache__`（controls が ceh を import して作った。無視の一覧に入り版管理の外）は allow_write の下に在る。消していない。

### C-4 ruff

    $ .venv/bin/ruff check $O/tools/ → All checks passed!
