# audit — T-2026-11-21-grasp-hand-graph-t2p-match

ホスト andrew（容器の中。`/.dockerenv` が在る）、repo `~/slocal2/m2`、分岐 `feat/grasp-hand-graph-t2p-match`。時刻は JST。
`$S` = `/home/ubuntu/slocal2/stage2pilot_store`、前回の保存先 `$O` = `$S/grasp_hand_graph/`（読むだけ）、
本契約の保存先 `$T` = `$S/grasp_hand_graph_t2p/`（開始時に無く、本契約が作った）。

## 0. 始める（手順書 0〜4）

- 開始時の分岐 `feat/grasp-hand-graph-pilot`（前回の契約。HEAD = origin = ca518ea0）。`feat/grasp-hand-graph-t2p-match` は手元にも遠隔にも無く、
  `tasks/T-2026-11-21-grasp-hand-graph-t2p-match` の履歴も無い。`.sync-pause` は無い
- 分類器（`scripts/task_start_classify.py`、比較先 origin/phase0 ce9c4094）: 6 分類すべて 0 件 → 「通す」。
  利用者の指示「汚れはgit info excludeへ」は、汚れが 0 件のため使っていない（`.git/info/exclude` は変えていない）
- `make task-start`: 分岐を origin/phase0 ce9c4094 から作成、`[task-start] .sync-pause を作成`（本契約が置いた目印。中身は task_id と branch の 2 行）、
  契約を台帳から取り込み `OK`、`[task-start] 完了。`
- `make task-validate`: `OK`（終了コード 0、WARN なし）
- `make task-preflight` 1 回目: 6 PASS / 0 WARN / 7 SKIP / 1 FAIL。FAIL は P6 decisions_answered（未回答 3 件）。3 件を利用者に示した
- 利用者の回答（2026-11-21、原文）「とにかく進めてくれ / しばらく見れないからなんとかしてとにかく実験回して」。判断を実行者に委ねた回答と読み、
  3 件の扱いを前もって決めて `meta.amendments` に記録し、`decisions_required` を空にした（決めた中身は spec の amendments の reason）
- `make task-preflight` 2 回目: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。SKIP は P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、
  P4・P5・P13・P14（exp のみ）、P12（解決する参照なし）。P9 spec_lint は「規則 9 件を検査し該当なし」
- 稼働中の `~/bin/m2-sync.sh` は目印に対応済み（`grep -c sync-pause` = 2）

### 解決された参照（手順書 3）

`contract.inject_verbatim` の 7 節（prohibitions・issuer_cautions・env_p0・folds・split・crossfit・symmetry）は `context/conventions.md`
（`git log -1 -- context/conventions.md` = 2d946b07 = `contract.conventions_rev`）の原文を読んだ。原文はその版の該当アンカー
（`split` 12 行〜、`prohibitions` 98 行〜、`env_p0` 109 行〜、`issuer_cautions` 154 行〜、`folds` 297 行〜、`symmetry` 367 行〜、`crossfit` 457 行〜）にあり、
要約せずに従う。denominator・frozen_source・sigma_policy の参照は無い。`inputs.data.split_files`（`data/splits/ego_val.txt`）は SPEC §0 のとおり
参照しなかった（使う分割は conventions#folds の折り A。`stage2pilot.common.fold_a()`）。

### meta.created_from の差し替え（SPEC §0）

    $ git log -1 --format=%h -- runindex/            → 036d6a60（origin/phase0 でも同じ）
    $ csv.DictReader の行数（見出し行を除く）         → index 2,668・experiments 1,347・verdicts 2,067
    （起票時の値 b524173e・2,647・1,327・1,977 から PR 312 などの統合で変わっていた。差し替えて amendments に記録）
    $ git log -1 --format=%h -- context/conventions.md → 2d946b07（差し替えなし）

## Task A — 開始状態（G1）

記録の原本は `$T/start/`。印 `$T/start/STARTED_MARKER` を 2026-11-21 10:08:36 JST に置いた（変更の検査の基準）。

### A-1 分岐・起点・前提の道具と記録（`$T/start/a1.txt`）

    $ git branch --show-current; git rev-parse HEAD; git merge-base HEAD origin/phase0; git rev-parse origin/phase0
    feat/grasp-hand-graph-t2p-match
    ce9c409454125267865eb0d017201dbacff7c321（3 つとも同じ）
    $ git log --oneline origin/phase0 | grep 'Merge pull request #(312|278|311) '
    90a12ab0 #312 grasp-hand-graph-pilot（2026-11-21 09:58 JST に統合）、7fdc514f #311、23192416 #278
    $ git ls-tree --name-only -r origin/phase0 -- <PR 312 の道具>
    dp_train.py・dp_model.py・ghg_graph.py・ghg_tower.py・proc_enum.py・grasp_hand_graph_pilot/tools/ の 8 件・signals_manifest.json がすべて在る
    class ToolHandGraph 1 件、TYPES の "GR": ( 1 件
    前提の契約 5 件（11-20 graph-pilot・10-19 fix-epoch4-shuffle・11-01 w23-bengio・10-18 pilot-folda・11-09 pilot-converge）とも RESULT.md と result.yaml が起点に在る

### A-2 開始前から在る未追跡

- `git status --porcelain --untracked-files=all` は契約の 2 ファイル（取り込んだ SPEC.md・spec.yaml）だけ
- 本契約の置き場は開始時に空: `experiments/phase1/grasp_hand_graph_t2p_*` 0 件、`experiments/analysis/grasp_hand_graph_t2p` 無し、`$T` 無し

### A-3 compute プロセス（`$T/start/a3_procs.json`、`a3_a6.txt`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py                                         → n_processes 34、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh                → count 5
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9    → count 0
    $ nvidia-smi --query-gpu=index,memory.used,utilization.gpu → GPU 0・1 とも 16 MiB、0 %
    $ nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory → 行 0 件（全体の使用量とプロセスの一覧の差は 0）
    $ nvidia-smi -i 7 --query-compute-apps=pid                 → No devices were found（存在しない GPU の番号）

### A-4 保存先の空き

    $ df -B1 /home/ubuntu/slocal2 → Available 1,573,500,612,608 B（使用 80%）

### A-5 試験と仮想環境（`$T/start/a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped（29.38 s）
    失敗の名前（6）: test_engines::test_mmdet_trainer_eval_recipe_in_metrics、test_fetch_task::test_rejects_unknown_file_name、
      test_research_logger の 4 件（test_log_run_idempotent・test_run_logging_invokes_log_run_on_finally・
      test_run_logging_no_double_post_on_normal_exit・test_run_logging_swallows_exception_in_user_block）。前回の契約の開始時と同じ 6 件
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0（108 行）
    .venv-relation-detr a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090（72 行）（前回の A-5 と同じ値）

### A-6 GPU の電力の上限

    0, NVIDIA RTX A6000, 300.00 W（既定 300.00 W、最大 300.00 W）
    1, NVIDIA RTX A6000, 300.00 W（既定 300.00 W、最大 300.00 W）

### A-7 既存の中身の一覧（完了判定 k の基準。`$T/start/k_listing_start.json`）

`$O`、`$S/T-2026-10-18-stage2-pilot-folda`、`$S/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`、`experiments/phase1/` の `grasp_hand_graph_*`・`stage2fix_*`・`w23b_*`、
`experiments/analysis/` の `grasp_hand_graph_pilot`・`stage2_pilot_fix`・`stage2_w23_bengio`、`third_party`、`data/raw`・`data/external`・`data/annotations` の
ファイル 241,412 件（46,234,458,030 B）の大きさと mtime_ns。

### G1 — pass

起点に PR 312 の道具と前提の契約の記録が在り（A-1）、本契約以外の compute は 0 件（A-3）、空き 1.57 TB（A-4）。

## Task B — 材料と学習設定（G2）

記録の原本は `$T/b/`。道具 `experiments/analysis/grasp_hand_graph_t2p/tools/b_check.py`（読むだけ。書くのは `$T/b/` だけ）。

### B-1 照合（`$T/b/b_check.json`）

    $ .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/b_check.py --out $T/b/b_check.json --scratch $T/b/controls
    {"graph_manifest_ok": true, "tp_shuffle_ok": true, "tp_runs_files_ok": true, "tp_runs": 36, "tp_settings_disagree": {"W1": [], "W2": [], "W3": []}, "controls_detect": true}

- 前回の目録 `signals_manifest.json` の sha256 24d9139d…bbd（前回の RESULT §3 の値と一致）。目録が名指す 26 ファイル
  （グラフ 7 腕 × train・val の 14、検出の配列 4、G3・H4 の推論 8）の sha256 が 26/26 で一致
- T→P の入れ替えの記録（`experiments/analysis/stage2_pilot_fix/shuffle/shuffle_record.json`）: 元の信号と入れ替えた信号（D0・D0-RT・D0-INST-UQ × train・val）
  12/12 一致。対応表の sha256（`shuffle_signals.mapping_stats` と同じ取り方）は train c62727fa…・val ad9dec09… で一致。
  train 9,657 フレーム（不動点 0.0、同じ動画から 0.11536、全単射）、val 1,515（不動点 0.00132、同じ動画から 0.55644、全単射）。動画は train 10・val 09・10
- T→P の参照の腕の run 36 本（W1 = andrew の `stage2fix_dp_*`、W2・W3 = bengio の `w23b_dp_W2/W3_*`。4 型 × 空・予測-noCF・入れ替え）の config が名指す
  信号・受け取り手の重み（0d76d446…）・特徴のキャッシュ（c402e214…）の sha256 がすべて一致。test の動画との共通 0
- 対照（1 バイト変えた写し、`$T/b/controls/`）: グラフ D_val 95a6cd20… → 5e459fdd…、入れ替えた D0_val ee6c21da… → db93a588…、
  対応表の一組を入れ替えた写し ad9dec09… → a86651b3…。3 つとも食い違いとして出た

### B-2 塔単独の val（`$T/b/tower_alone.json`。道具は前回の tower_alone.py の識別子だけ変えた写し）

    $ CUDA_VISIBLE_DEVICES=0 .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/tower_alone.py --out $T/b/tower_alone.json
    {"phase_jaccard": 0.7762185528074379, "phase_accuracy": 0.8712871287128713, "six_phase_mean": 0.7773831834035493, "equals_record": true}

記録（`stage2pilot.common.PT_RECORD`）と完全に一致（差 0.0。許容 0.005）。

### B-3 T→P の学習設定の写し（SPEC §3.2。`b_check.json` の `tp_settings_by_scope`・`graph_prev_settings`）

| 項目 | W1（stage2fix 12 本） | W2（w23b 12 本） | W3（w23b 12 本） | 前回のグラフ（収束規則） |
|---|---|---|---|---|
| 界面の学習率・weight decay | 5e-4・0.01 | 同じ | 同じ | 同じ |
| optimizer | AdamW（界面だけ） | AdamW、受け取り手は界面と別の群 | 同じ | 同じ |
| 受け取り手の学習率・weight decay | —（凍結） | 5e-4・0.01 | 5e-4・0.01 | 同じ |
| 学習率の予定 | constant | constant | constant | constant、8 epoch 停滞で × 0.1 を一度 |
| 長さ | fixed_epochs 4 | 4 | 4 | 収束規則（上限 120） |
| 受け取り手の扱い | frozen, eval（dropout off） | trained（最後の段）, eval | trained（時間ヘッド全体）, eval | 同じ |
| 受け取り手の側の学ぶ名前 | 0 | 36（head.refine_stages.0.*） | 72（head.*） | W ごとに T→P と同じ集合 |

- W ごとに 4 型の間で食い違いは 0。T→P とグラフの基本の値（STOP・RECEIVER の定数）は同じで、違うのは学習の長さの規則だけ
- 1 歩の単位: `dp_train.cmd_train` の学習の輪は train の動画 1 本ごとに `opt.step()`（train 10 本 → 1 epoch 10 歩）。4 epoch で 40 歩
- 学習率の予定が全体の長さに依るか: 依らない。`--fixed-epochs` の経路は学習率を変える処理を持たない（`ConvergeRule` の × 0.1 は `--converge` のときだけ。
  scheduler は無い）。したがって SPEC §3.1 の副次（同じ run を 16 epoch まで続けて 8・12・16 を記録する）を行う

### G2 — pass

前回のグラフと信号・T→P の信号と入れ替えた信号と対応表・工程塔の重みと特徴のキャッシュの要約値が記録と一致し（B-1）、塔単独の val が記録と一致し（B-2）、
T→P の学習設定が W ごとに型の間で一つに決まる（B-3）。

## Task C — 道具と確かめ（G3）

### C-1 noCF・CF・入れ替えのグラフ（`$T/c/graphs_report.json`、道具 `tools/c_graphs.py`、材料 `$T/graph/`）

    $ .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/c_graphs.py --out-dir $T/graph --report $T/c/graphs_report.json   （6.7 s）

- 前回の信号（`$O/signals/det` の検出の配列 4、`$O/signals/raw` の G3・H4 の推論 8。読むだけ）から、前回の道具 `ghg_graph` の部品
  （tool_rows・hand_rows・holder・pred_hands）で 5 腕 × {noCF, CF} を組んだ。グラフの定義は変えていない
- 組み直した CF の 5 腕（D・DG・DH・DGH・DGH-U）と DGH-noCF は、前回の `$O/graph` の配列と train・val ともビットまで一致（フレームの順も同じ）。
  したがって前回のファイルを指す記号のリンクを置いた（D-CF・DG-CF・DH-CF・DGH-CF・DGH-U-CF・DGH-noCF・DGH-GT と、空の腕の形・陰性対照に使う D・DGH）
- 新しく書いたのは D-noCF・DG-noCF・DH-noCF・DGH-U-noCF と X-S（5 腕）の train・val の 18 ファイル。val の noCF は確定の塔なので CF と同じ値
  （D-noCF_val の sha256 95a6cd20… = 前回の D_val）。train の noCF と CF はフレームごとに 100 % 違う（同じフレームの割合 0.0）
- 出どころ: noCF の train は 9,657 フレームとも {det_final, G3_all, H4_all}、CF の train は {det_cfH1, G3_H1, H4_H1} か {det_cfH2, G3_H2, H4_H2}、val はどれも確定の塔。
  noCF・CF それぞれの 5 腕で、術具の行（有無・クラス・得点・枠）が DGH と同じ、持ち手が DG・DGH で同じ、手の行が DH・DGH・DGH-U で同じ、
  DGH-U の持ち手 = DGH の持ち手の最大の 3 列複製 → 外れ 0（train・val）
- 表（SPEC §5.1）: 15 腕 × train・val の術具・持ち手・手・辺の在否、DGH-U の持ち手が 3 列とも同じ、DGH と DGH-U の辺 = 持ち手 → 外れ 0
- 対照: 表と違う腕（D-noCF に DH-noCF の配列）→ 外れ 1。noCF の腕（DG-noCF）の先頭 1 割（train 965 フレーム）に CF の信号を混ぜた写し → 外れ 2（tool_rows・holder）。
  val は CF = noCF なので同じ対照で外れ 0（期待どおり）
- 入れ替え（SPEC §4.2）: T→P の対応表 `mapping_{train,val}.json`（seed 42、「frame f gets the value of mapping[f]」）のキーの集合がグラフのフレームの集合と
  train 9,657・val 1,515 で一致したので、新しく作らずそれを 5 腕すべてに使った（T→P の入れ替えと同じ並べ替え）。対応表の sha256 train c62727fa…・val ad9dec09…。
  値の移り先は同じ part の動画だけ（part をまたぐ 0）。5 腕とも、入れ替えた行 = 元の行[mapping]、逆の並べ替えで元に戻る、値の集合（行を並べ直した要約値）が元と同じ。
  元と同じフレームに同じグラフが来る割合 train 0.0・val 0.00132（2 フレーム）、同じ動画から来た割合 train 0.11536・val 0.55644。
  対照: 恒等の並べ替えで不動点の割合 1.0
- test: グラフの train の動画 01・02・03・06・08・11・12・13・14・15、val 09・10、{04, 05, 07} との共通 0。対照: train のフレームに 04_1_0001 を混ぜると共通 1 件 [04]

### C-2 dp_train.py に足したもの（既定の挙動は変えない）

- GR の腕の名前 `GR_ARMS_T2P`（D・DG・DH・DGH・DGH-U × -noCF・-CF・-S。DGH-noCF は従来の名前）。材料のファイル名がそのまま腕の名前
- `--record-epochs E ...`（`--fixed-epochs` と組。1〜fixed の範囲を検査）: epoch E ごとに `predictions/val_probs_ep<E>.npz` と `metrics_ep<E>.json`
  （6 工程の計算に要るクラス別 Jaccard・動画ごと・frame accuracy・7 工程の Jaccard、零初期化の層の L2 と最大、群ごとの学習率と weight decay）。
  config に `record_epochs`・`steps_per_epoch`・`optim_groups`（群ごとの学習率・weight decay・パラメータの名前）・`iface_last_init` を書く
- 渡さなければ何も変わらない（C-3 で記録と一致）

### C-3 既定の挙動が変わらない（SPEC §2。`$T/c/repro_compare.json`、`tools/run_repro.sh`・`tools/c_checks.py repro`）

新しい引数を渡さずに、前回のグラフの run 1 本と T→P の run 1 本を本契約の識別子で回し直した（andrew、GPU 1）。

    grasp_hand_graph_t2p_repro_gr_001_GR-W1-N10-L1_DGH-noCF_conv_seed42 vs grasp_hand_graph_arm_009_GR-W1-N10-L1_DGH-noCF_conv_seed42
      J 0.7770627880253497 = 同じ、frame accuracy 0.8811881188118812 = 同じ、最良の回 8・24 epoch = 同じ、動画ごと = 同じ、metrics_last = 同じ、
      val_probs_best・val_probs_last の差の最大 0.0
    grasp_hand_graph_t2p_repro_tp_001_D1-L1_pred_noCF_ep4_seed42 vs stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42
      J 0.7808396679473972 = 同じ、frame accuracy 0.8785478547854786 = 同じ、動画ごと = 同じ、val_probs_best の差の最大 0.0
    陽性対照: val の確率を 1 か所 1e-6 ずらした写し → equal false（差 9.98e-7）。記録の J を 1e-6 ずらした値 → 一致しない

前回の契約で UNKNOWN（回していない）だった陽性対照を、本契約で回した。

### C-4 恒等性（`$T/identity/`、`$T/c/identity_summary.json`、`tools/run_identity.sh`・`tools/c_checks.py identity`）

    グラフ 17 腕（A0・15 腕・DGH-GT）× 4 設定 × W1・W2・W3 = 204 組、T→P 4 型 × 3 腕（空・予測-noCF・入れ替え）× 3 W = 36 組、計 240 組
    学習前の出力の塔単独とのロジットの差の最大 0.0（240/240）、J = 0.7762185528074379（240/240）
    陽性対照（零初期化の層を N(0, 0.05²)）で出力が変わった 231/240（ロジットの差 0.105〜3.135）

- 変わらなかった 9 組は T→P の D1-L1・D1-L2・D3-L2 の空の腕（3 型 × 3 W）。D1 の零初期化の層は `Conv1d(S, maps, 1, bias=False)` で入力が全部 0 のとき出力に効かず、
  D3 の空の腕はトークンが 0 個で界面が出力に届かない。構造上変わらないもので、同じ型の予測-noCF・入れ替えの腕では変わる（0.258〜2.726）。
  D2（bias を持つ）とグラフの空の腕は変わる。逸脱（判断）として記録した
- 学ぶ範囲: W2・W3 の 160 組（グラフ 17 × 4 × 2 = 136、T→P 12 × 2 = 24）の学ぶ名前の集合が定義と一致し、定義の外の名前を混ぜた写しで一致しない。
  受け取り手の側の学ぶ名前の集合はグラフと T→P で W2 36 個・W3 72 個とも同じ一つの集合（W1 は 0 個）

### G3 — pass

入れ替えたグラフの値の集合が元と同じで（C-1）、腕ごとの節・特徴・辺の在否が表と一致し（C-1）、学習前の出力が全腕で塔単独と一致し、
陽性対照で変わる（C-4。構造上変わらない 9 組は同じ型の別の腕で変わることを示した）。

## Task D — 腕（G4）

### D-1 run の一覧と回し方（`tools/jobs.py`・`tools/run_jobs.sh`、記録 `$T/logs/all/events.log`）

    $ python3 experiments/analysis/grasp_hand_graph_t2p/tools/jobs.py all | wc -l → 189（重複 0）
      ep4chk 12（4 epoch で止める確かめ 6 と、比べる続けた run 6）＋ main 177
    $ NW=8 bash experiments/analysis/grasp_hand_graph_t2p/tools/run_jobs.sh all
    [jobs] all jobs 189 workers 8 start 2026-11-21T01:18:11Z … all done 2026-11-21T01:40:52Z（10:18:11〜10:40:52 JST、22 分 41 秒）
    rc=0 189 件、rc≠0 0 件、skip 0 件

- 続けた run は `--fixed-epochs 16 --record-epochs 4 8 12 16`、4 epoch で止める確かめは `--fixed-epochs 4 --record-epochs 4`。どれも `--seed 42 --task-id 本契約
  --ckpt-dir $T/dp_ckpt`、W&B は offline（`WANDB_DIR=$T/wandb`）。並行は GPU 2 枚 × 4 本（NW 8）
- 接頭辞: グラフ `grasp_hand_graph_t2p_gr`（147 本 = A0 3・辺の無い 9 腕 × s1・s3 × 3 W = 54・DGH と DGH-U の 6 腕 × 4 設定 × 3 W = 72・DGH-GT 12・§5.3 の確かめ 6）、
  T→P `grasp_hand_graph_t2p_tp_W1/W2/W3`（36 本）、4 epoch で止める確かめ `grasp_hand_graph_t2p_ep4chk`（3）と `grasp_hand_graph_t2p_ep4chk_tp_W1/W2/W3`（3）。
  既定の挙動の回し直し 2 本（`grasp_hand_graph_t2p_repro_*`）は表の外
- 4 epoch で止める確かめを一覧の先頭に置いた。続けた run は比べの結果によらず副次に要るので、比べを待たずに全部を回した（D-2 の結果で 4 epoch で止める run の全腕は不要になった）

### D-2 4 epoch で止めた run と続けた run（SPEC §3.1。`$T/d/ep4_compare.json`、`tools/c_checks.py ep4`）

    W ごとに グラフ DGH-noCF s1・T→P D1-L1 予測-noCF の 6 組: 4 epoch 目の val の確率の差の最大 0.0（6/6 で一致）、J も一致、零初期化の層の大きさも一致
    対照: 続けた run の 4 epoch 目と 8 epoch 目の確率 → 差 0.052〜0.855（6/6 で違いを拾う）

一致したので、主の値は続けた run の 4 epoch 目の状態から取った（学習率は一定で長さに依らない。audit B-3）。

### D-3 省いた run（SPEC §5.3。`$T/d/omitted_compare.json`、`tools/c_checks.py omitted`）

    W ごとに A0 s4 vs A0 s1、D-noCF s2 vs D-noCF s1 の 6 組: epoch 4・8・12・16 の val の確率がすべて一致（W1・W2・W3 とも）
    対照: D-noCF s1 vs DG-noCF s1 → 3 W とも違いを拾う

一致したので、省いた run は回さず、A0 は s1 の値を 4 設定に、辺の無い 9 腕は s1 → s2・s3 → s4 の値として使った（出所は summary の table_source）。

### D-4 学習設定が optimizer に届いた（完了判定 c。`$T/d/optim_check.json`、`tools/c_checks.py optim`）

    189/189 本で、config の optim_groups（群ごとの学習率・weight decay・パラメータの名前）が写した値（界面 5e-4・0.01、W2・W3 は受け取り手 5e-4・0.01 の別の群）と一致し、
    群の中身が界面（iface.*）と受け取り手（head.*）で、epoch 4・8・12・16 の記録の学習率も同じ
    受け取り手の側の学ぶ名前の集合はグラフと T→P で W2・W3 とも一つの同じ集合
    対照: 実際の run（grasp_hand_graph_t2p_ep4chk_002_GR-W2-N10-L1_DGH-noCF_ep4_seed42）の群の受け取り手の学習率だけ 5e-5 にした写し → 検査を通らない

### G4 — pass

189 本が rc 0 で終わり（D-1）、記録する epoch の `metrics_ep<E>.json` と `predictions/val_probs_ep<E>.npz` が 189/189 本でそろう（E-1 の end_check）。

## Task E — 集計と報告

### E-1 集計（`$T/e/summary.json`、`tools/aggregate.py`）

    $ .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/aggregate.py --out $T/e/summary.json   （8.4 s）
    n_runs 183（グラフ 147・T→P 36）、測り直し 732 組（183 本 × 4 epoch）: 記録とのずれの最大 0.0、1e-6 ずらした写しを 732/732 で検出
    end_check: 189/189 本、記録がそろう 189、存在しない名前（GR-W1-N10-L1_NO_SUCH_ARM）0 件・在る名前 1 件、missing 0
    run の動画 01・02・03・06・08・09・10・11・12・13・14・15、{04, 05, 07} との共通 0（04 を混ぜた対照で [04]）
    7 工程の Jaccard（val に現れる 7 工程の平均）は PhaseEvaluator の phase_jaccard と 732/732 で一致（差 0）

### E-2 報告（`experiments/analysis/grasp_hand_graph_t2p/REPORT.md` 1,044 行・`diffs.csv` 1,344 行、`tools/make_report.py`）

    $ python3 experiments/analysis/grasp_hand_graph_t2p/tools/make_report.py --summary $T/e/summary.json --checks-dir $T \
        --out experiments/analysis/grasp_hand_graph_t2p/REPORT.md --csv experiments/analysis/grasp_hand_graph_t2p/diffs.csv

### E-3 変えていない（完了判定 k）

    $ python c_checks.py unchanged → 開始時の一覧 241,412 件と今の同じ根: 変更 0・削除 0・追加 0（対照: 新しいファイルを一つ加えた一覧で追加 1）
    $ find <前回の保存先 3・third_party・data/raw・external・annotations・前回の集計 3> -newer $T/start/STARTED_MARKER | wc -l → 0
    $ find experiments/phase1 の前回の run（grasp_hand_graph_*〔本契約の t2p を除く〕・stage2fix_*・w23b_*）-newer STARTED_MARKER | wc -l → 0
    $ b_check.py をやり直し（$T/e/b_check_end.json）→ 材料の要約値が全部一致のまま、対照も食い違いを出す
    $ uv pip list --format freeze | sha256sum → .venv 9c7be5c9…・.venv-relation-detr a74c9c78…（開始時と同じ）
    $ pytest（$T/e/pytest_end.txt）→ 6 failed, 985 passed, 5 skipped。失敗の名前は開始時と同じ 6 件（diff 0）
    $ make forbidden-check TASK=T-2026-11-21-grasp-hand-graph-t2p-match → status pass、changed 2,283、permitted 2,279（allow_write の 2 経路）、violations 0
    $ make forbidden-check（TASK なし、対照）→ status fail、本契約の経路が「禁止領域 experiments/ の内側」として名指される

- 既存の道具は dp_train.py に足す形だけ（C-2）。既定の挙動は前回のグラフ 1 本・T→P 1 本の回し直しで記録と完全に一致（C-3）
- `b_check.py` は B-1 で回した後に、使っていない変数 `O` を一行消した（ruff E741）。照合の中身は変わらず、E-3 でやり直して同じ結果
