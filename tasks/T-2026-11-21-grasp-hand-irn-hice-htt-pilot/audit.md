# audit — T-2026-11-21-grasp-hand-irn-hice-htt-pilot

ホスト andrew（容器の中）。時刻は JST。`$S` = `/home/ubuntu/slocal2/stage2pilot_store`、`$O` = `$S/grasp_hand_graph`（前回の契約の保存先。読むだけ）、
`$T` = `$S/grasp_hand_irn_hice_htt`（本契約の保存先）。道具は `experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/`。

## 0. 始める（手順書 0〜4）

    $ git branch --show-current → feat/grasp-hand-graph-t2p-match（作業ツリーは清浄、feat/grasp-hand-irn-hice-htt-pilot は手元・遠隔とも無い、tasks/<本契約> の履歴なし、.sync-pause なし）
    $ git fetch origin && python3 scripts/task_start_classify.py
    [task-start] 分類（比較先 origin/phase0 4cb85a02）
    [task-start]   追跡下の変更: 0 件 / 未追跡・起点に在り中身が同じ: 0 件（通す）/ 未追跡・起点に在り中身が違う: 0 件 / 未追跡・起点に無い: 0 件
    [task-start]   無視・起点に在り中身が同じ: 0 件（通す）/ 無視・起点に在り中身が違う: 0 件 / 無視・起点に無い: 数えない（触れない）
    [task-start] 分類: 通す
    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-11-21-grasp-hand-irn-hice-htt-pilot
    [task-start] 分岐を作成: feat/grasp-hand-irn-hice-htt-pilot（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-11-21-grasp-hand-irn-hice-htt-pilot END=complete）
    OK   T-2026-11-21-grasp-hand-irn-hice-htt-pilot（取り込み）
    [task-start] 完了。分岐 feat/grasp-hand-irn-hice-htt-pilot で契約 T-2026-11-21-grasp-hand-irn-hice-htt-pilot の作業を開始できます

- 目印: task-start が「`.sync-pause を作成`」と表示した（この契約が置いた目印）
- `make task-validate`: OK（0 failed、WARN なし）
- `make task-preflight`（1 回目）: 6 PASS / 0 WARN / 7 SKIP / 1 FAIL。P6 decisions_answered が「未回答 3 件: 停止条件に当たったときの続け方（実行者は決めない）;
  三つの型の定義（SPEC の型の定義の節）を変えないと実装できない場合の変え方; 確かめの run が一致せず、SPEC が値の流用を許す条件を満たさない場合の回し方」で FAIL。
  利用者に 3 項目を選択式で示した。回答（2026-11-21）: (1)「前回と同じく任せる」(2)「最小の変更で進める」(3)「省いた run を回して埋める」。
  `spec.yaml` の `meta.amendments` 1 件目に原文の読みを記録し、`decisions_required` を [] にした
- `meta.created_from` を起点で測って差し替えた（amendments 2 件目）: `git log -1 -- runindex/` → 036d6a60（2026-11-09 17:59 UTC）、
  csv.DictReader の行数 index 2668・experiments 1347・verdicts 2067。`git log -1 -- context/conventions.md` → 2d946b07（= contract.conventions_rev、差し替えなし）
- `make task-validate`（2 回目）: OK。`make task-preflight`（2 回目）: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL
  - SKIP（実行されなかった）: P2 cuda_ext_loaded・P3 deterministic_flags（plan.env.preflight に記載なし）、P4 prereg_committed・P5 frozen_source_hash・
    P13 symmetry_table_complete・P14 proposal_card_checked（kind=analysis のため対象外）、P12 refs_resolved（解決前提の参照なし）
  - P9 spec_lint: 規則 9 件を検査し該当なし

### 解決された参照（手順書 3）

- `contract.inject_verbatim` の 7 節（prohibitions・issuer_cautions・env_p0・folds・split・crossfit・symmetry）は `context/conventions.md`（2d946b07 = 契約の
  conventions_rev）の原文を適用した。`inputs.denominator`・`frozen_source`・`sigma_policy` の参照は無い
- `inputs.data.split_files`（`data/splits/ego_val.txt`）は参照しなかった（SPEC §0。使う分割は conventions#folds の Fold A）

## Task A — 開始状態（G1）

記録の原本は `$T/start/`。印 `$T/start/STARTED_MARKER` を 2026-11-21 14:53:33 JST に置いた。

### A-1 分岐・起点・前提の道具と記録（`$T/start/a1.txt`）

    $ git branch --show-current; git rev-parse HEAD; git merge-base HEAD origin/phase0; git rev-parse origin/phase0
    feat/grasp-hand-irn-hice-htt-pilot
    4cb85a02d38805ad5c266f0cb8deaf916e639fd9（3 つとも同じ）
    $ git log origin/phase0 | grep 'Merge pull request #(312|315) '
    90a12ab0 #312 grasp-hand-graph-pilot（2026-11-21 09:58 JST）、be49c44f #315 grasp-hand-graph-t2p-match（2026-11-21 14:45 JST）
    $ git ls-tree --name-only -r origin/phase0 -- <前回の道具と記録>
    dp_train.py・dp_model.py・ghg_graph.py・ghg_tower.py・proc_enum.py・grasp_hand_graph_pilot/{REPORT.md, signals_manifest.json, tools/ の 8 件} がすべて在る
    class ToolHandGraph 1 件、TYPES の "GR": ( 1 件、add_argument("--converge" 1 件
    腕の run experiments/phase1/grasp_hand_graph_arm_* 96 件（起点で追跡 96 件）
    前提の契約 4 件（11-20 graph-pilot・11-09 roitoken-transition-pilot・11-09 pilot-converge・10-18 pilot-folda）とも RESULT.md と result.yaml が起点に在る

### A-2 開始前から在る未追跡（`$T/start/a2_untracked.txt`）

- 取り込んだ契約の 2 ファイル（SPEC.md・spec.yaml）と、本契約の道具 2 件（a_check.py・listing.py。A-7・A-8 の前に書いた）だけ
- 本契約の置き場は開始時に空: `experiments/phase1/grasp_hand_irn_hice_htt_*` 0 件、`experiments/analysis/grasp_hand_irn_hice_htt_pilot` 無し、`$T` 無し

### A-3 compute プロセス（`$T/start/a3_procs.json`、`a3_a6.txt`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py                                         → n_processes 34、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh                → count 5
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9    → count 0
    $ nvidia-smi --query-gpu=index,memory.used,utilization.gpu → GPU 0・1 とも 16 MiB、0 %
    $ nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory → 行 0 件（全体の使用量とプロセスの一覧の差は 0）
    $ nvidia-smi -i 7 --query-compute-apps=pid                 → No devices were found（存在しない GPU の番号）

### A-4 保存先の空き

    $ df -B1 /home/ubuntu/slocal2 → Available 1,572,432,932,864 B（使用 80%）

### A-5 試験と仮想環境（`$T/start/a5_pytest_start.txt`・`a5_fail_names.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped（29.17 s）
    失敗の名前（6）: test_engines::test_mmdet_trainer_eval_recipe_in_metrics、test_fetch_task::test_rejects_unknown_file_name、
      test_research_logger の 4 件（test_log_run_idempotent・test_run_logging_invokes_log_run_on_finally・
      test_run_logging_no_double_post_on_normal_exit・test_run_logging_swallows_exception_in_user_block）。前回の契約の開始時と同じ 6 件
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0（108 行）
    .venv-relation-detr a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090（72 行）（前回の契約の A-5 と同じ値）

### A-6 GPU の電力の上限

    0, NVIDIA RTX A6000, 300.00 W（既定 300.00 W、最大 300.00 W）
    1, NVIDIA RTX A6000, 300.00 W（既定 300.00 W、最大 300.00 W）

### A-7 保存先の信号と前回の組み立ての出力の照合（`$T/start/a_check.json`、道具 `tools/a_check.py`）

    $ .venv/bin/python tools/a_check.py --out $T/start/a_check.json --scratch $T/start/ctrl
    {"manifest": true, "assemble": true, "n": 26, "n_mismatch": 0, "receiver": true, "control_n_mismatch": 1}

- 目録 `signals_manifest.json` の sha256 24d9139d…（前回の RESULT §3 と一致）。目録が名指す 26 ファイル（グラフ 14・検出の配列 4・G3・H4 の推論 8）がすべて一致
  - グラフ（先頭 8 桁）: train D 91b29184・DG 1ddbaba6・DH 68268e73・DGH 2911d85a・DGH-U 1cf2d53c・DGH-noCF 0a2ae309・DGH-GT 61fe62fb（各 9,657 フレーム）、
    val D 95a6cd20・DG 2eba5871・DH 658ef060・DGH 5743b114・DGH-U 67f1ae0e・DGH-noCF 5743b114・DGH-GT ffcb1b59（各 1,515 フレーム。val の DGH と DGH-noCF は
    どちらも確定の塔なので同じ）
- 組み立ての報告 `$O/graph/assemble_report.json` 1e0f052f3bd6…（前回の RESULT §3 の 1e0f052f… と一致）
- 工程塔の重み 0d76d446…・特徴のキャッシュ c402e214…（前回のグラフの run の config の値と一致）
- 対照: `$O/graph/D_val.npz` の写しを 1 バイト変えると、照合が外れ 1 を数える

### A-8 既存の中身の一覧（完了判定 j の基準。`$T/start/j_listing_start.json`、道具 `tools/listing.py`）

`$O`、`$S/grasp_hand_graph_t2p`、`$S/T-2026-10-18-stage2-pilot-folda`（工程塔の重みとキャッシュを含む）、`$S/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`、
`experiments/analysis/` の `grasp_hand_graph_pilot`・`grasp_hand_graph_t2p`、`third_party`、`data/raw`・`data/external`・`data/annotations`、
`experiments/phase1/` の `grasp_hand_graph_*`・`stage2fix_dp_*`・`grasprt_tw_*`・`grasprc_*`（根 539）のファイル 246,201 件（46,786,385,550 B）の大きさと mtime_ns。

### A-9 回し直しの run の選び方（SPEC §5.2 の「型 TW の run 1 本」）

- 型 TW の run（`grasprt_tw_*`・`grasprc_tw_*` など 138 本）はすべて bengio で回したもので、材料の置き場 `--tw-dir $S/T-2026-11-09-grasp-roitoken-transition-pilot`（`seq/`）が
  andrew に無い。`find /home/ubuntu/slocal2 -maxdepth 5 -name 'seq_*_k*' -o -name '*roitoken-transition*'` で見つかったのは
  `$HOME/slocal2/stage2_pilot_viz_cache/bengio_only/store/T-2026-11-09-grasp-roitoken-transition-pilot`（284 KB、`b4/has_gt_val.npy` と図の材料だけで `seq/` が無い）だけ
- 利用者の回答 (1)（停止は gate の FAIL などに限る）により実行者が決めた: 型 TW の代わりに、andrew で回し材料が andrew に在る型の run
  `stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42`（T→P の D1-L1、`--fixed-epochs 4`）を回し直す。前回のグラフの型からは、受け取り手の全体を学ぶ経路・N 30・L 2・辺を通る
  `grasp_hand_graph_arm_093_GR-W3-N30-L2_DGH_conv_seed42`（andrew、収束規則、`--save-last-probs`）を選んだ

### G1 — pass

起点に前回の契約の道具・記録・目録が在り（A-1）、保存先の信号と組み立ての出力が目録と一致し（A-7）、本契約以外の compute は 0 件（A-3）、空き 1.57 TB（A-4）。

## Task B — トークン（G2）

### B-1 トークンの中身・持ち手の一致・腕の表・test（`$T/b/b_tokens.json`、道具 `tools/b_tokens.py`）

本契約は前回の組み立ての出力 `$O/graph/<腕>_<part>.npz`（x (F, 32, 27)）をそのまま読む（SPEC §3。作り直していない）。型には dp_train の `Signals`（kind `gr`）が
行 [0, N) と行 30・31 を切り出して渡す。三つの型は辺の重みの 3 列（24..26）を使わない（§3 のトークンの中身に辺は入らない）。

    $ CUDA_VISIBLE_DEVICES="" .venv/bin/python tools/b_tokens.py --out $T/b/b_tokens.json --types GR IRN HiCE HTT
    train {"agree": {"boxes": 21021, "agree": 20433, "rate": 0.972027972027972}, "control_swapLR": {"boxes": 21021, "agree": 1933, ...}, "equals_prior": true}
    val   {"agree": {"boxes": 3807, "agree": 3610, "rate": 0.9482532177567639}, "control_swapLR": {"boxes": 3807, "agree": 424, ...}, "equals_prior": true}
    {"content_n": 128, "content_equal": 128, "content_control_detected": 128, "table_violations": 0, "table_control_violations": 4,
     "agreement": {"train": [20433, 21021, true, 1933], "val": [3610, 3807, true, 424]}, "test_overlap": {"train": 0, "val": 0, "control_04_mixed": 1}}

- 中身: 4 型（GR・IRN・HiCE・HTT）× 8 腕 × N 10・30 × train・val = 128 組で、型に渡る配列が npz の行と**ビットまで一致**（A0 は同じ形の全部 0）。
  対照: 1 フレームの術具のトークンの得点を 1e-6 ずらした写しで 128/128 が不一致を出す
- 持ち手の一致（前回の `ghg_graph.grasp_agreement` に DGH-GT の配列の持ち手の列を渡した）: train 20,433/21,021・val 3,610/3,807 で前回の報告と同じ。
  対照: 左右を入れ替えた写しで train 1,933・val 424 に下がる
- 腕の表（SPEC §5.1 の術具のトークン・持ち手（非零）・手のトークン、DGH-U の持ち手が 3 列とも同じ）: 2 part × 2 N で外れ 0。対照: D に DH の配列を置いた写しで外れ 4（各 1）
- test: train の動画の集合・val の動画の集合と {04, 05, 07} の共通 0。対照: train のフレームに `04_1_0001` を混ぜると共通 1
- 道具の変数名 `O` を ruff の指摘で `GRAPH_STORE` に改めた後に回し直した（値は改める前の回と同じ）

### G2 — pass

全腕・全設定のトークンの中身が前回のグラフの節と一致し、正解の腕の持ち手の一致の数が前回の報告と同じ。腕ごとの在否が §5.1 の表と一致。

## Task C — 型（G3）

### C-1 dp_model.py・dp_train.py に足したもの（既定の挙動は変えない）

- `dp_model.py`: `masked_attention`・`CrossAttention`・`_TokenIface`・`IRNIface`・`HiCEIface`・`HTTIface` を足し、`TYPES` に irn・hice・htt、`DPReceiver` に構築と
  入力の経路を足した。消えた行は 2 行（`TYPES` の 1 行と、forward の graph の経路の条件の 1 行。どちらも同じ値に新しい型を足しただけ）
- `dp_train.py`: `TYPES` に `"IRN"`・`"HiCE"`・`"HTT"`（kind `gr`。材料・腕・引数は GR と同じ `--gr-dir`・`--gr-N`・`--gr-L`）を足し、冒頭の説明に節を足した。消えた行 0
- 実行者が決めたもの（SPEC §4.1。全型・全腕・全設定で同じ）:
  - 注意は 4 head（K 64、1 head 16）。問い合わせと鍵の射影は bias つき、**値と注意の出力の射影は bias なし**（学ぶ定数を値と r_t に入れない）
  - 残差: 段ごとに問い合わせへその段の注意の出力を足す。r_t（IRN は z_s）は各段の注意の出力の和で、問い合わせそのもの（e_s・g_t）を含まない。正規化の層と FFN は置かない
  - トークンの埋め込みは前回のグラフの節と同じ形の MLP（入力 → 64 → 64、ReLU）。在否の印で掛けて、無いトークンは 0
  - e_s は N(0, 0.02²) の 2 × 64 の学ぶ埋め込み（RT・TW の学ぶ定数と同じ初期化の大きさ）
  - IRN: 術具のトークンの埋め込みは持ち手 3 列を含む 23 次元から。統合の鍵 {z_左, z_右} はフレームに術具のトークンが在るときだけ置く
  - HiCE: m は持ち手を除いた 20 次元（クラス・得点・枠）から。**ω は正規化しない**（Σ_i w_is m_i のまま）。W_ω は bias なしの線形（ω = 0 なら 0）。
    **側 s の鍵は「手のトークン s が在る」か「Σ_i w_is > 0」のときだけ置く**（A0・D は構成上鍵 0 で r_t = 0、§4.3 の「D は入力が A0 と同じ」を満たす）
  - HTT: x_t（76）= ［クラスごとの得点の最大 15｜左手 8｜右手 8｜クラスごとの持ち手の最大 左・右・両手 各 15］。MLP は（線形 → ReLU）を L 段の後に線形 64 → 64。
    術具のトークンも手のトークンも無いフレームは r_t = 0（掛けて切る）
  - 三つの型とも零初期化の層は `iface.out`（Linear(64, 2048)、重みと bias を零）。r_t = 0 でも out を通す（A0 は bias だけが学ばれる）

### C-2 型の定義（完了判定 c。`$T/c/c_types.json`、道具 `tools/c_types.py`。val 1,515 フレーム、seed 42 の初期化、float64）

    $ CUDA_VISIBLE_DEVICES="" .venv/bin/python tools/c_types.py --out $T/c/c_types.json
    {"rows": 96, "all_finite": true, "no_input_zero": true, "A0_zero": true, "control_A0_given_DGH_min": 0.04797491575038332,
     "hice_A0_D_keys_max": 0, "hice_D_r_abs_max": 0.0, "zero_content_g_change_max": 8.326672684688674e-17, "zero_content_ok": true,
     "control_values_with_side_min_over_arms_with_input": 3.471617676949505e-05, "control_values_with_side_rows": 48,
     "hice_unheld_change_max": 0.0, "hice_control_all_tools_min_over_arms_with_unheld": 0.36080586909191154, ...}

- 問い合わせと鍵の数（フレームごと、平均（最小〜最大））:
  - IRN: 側の問い合わせ 2。術具の鍵は A0 0、D〜DGH-noCF は N（10 か 30）、DGH-GT 3.107（1〜8）。統合は問い合わせ 1・鍵 2（A0 は 0）
  - HiCE: 問い合わせ 1。側の鍵は **A0・D 0**、DG・DH・DGH・DGH-U・DGH-noCF 2（全フレーム）、DGH-GT 1.95（0〜2）
  - HTT: x_t の次元 76（全腕）。入力の在るフレームは A0 0、ほかの腕は全フレーム
- 入力の無いフレームで r_t = 0: A0 の 1,515 フレームで完全に 0（他の腕は val に入力の無いフレームが無い）。対照: A0 の型に DGH の入力を入れると r_t の最大 0.0480〜2.3281
- 送り手の中身を零にした入力（在否の列 0 を残し列 1..26 を 0）で g_t を別のフレームの特徴（半分ずらし）に替えた r_t の差: 最大 8.3e-17（判定の上限 1e-9 を
  先に決めた。重みの和が 1 からずれる丸めの分）。対照: 注意の値に e_s を足した写しでは、中身を零にしても鍵が残る 48 行（IRN の A0 を除く 7 腕 × 4 設定、
  HiCE の DH・DGH・DGH-U・DGH-noCF・DGH-GT × 4 設定）で 3.47e-5〜5.60e-5 変わる。HiCE の DG は中身を零にすると持ち手が 0 になり鍵が無くなるので写しでも 0。
  HTT は g_t を使わないので差は 0（写しは作らない）
- HiCE の持たれていない術具（持ち手 3 列とも 0）の中身（列 1..20）に乱数を足しても r_t は変わらない（差 0.0）。対照: 持ち手の重みに 1 を足して持たれていない術具も
  ω（鍵）に入れた写しでは 0.3608〜2.0296 変わる。持たれていない術具のトークンの数: D 15,150（N 10）・45,450（N 30）、DG・DGH 491・1,993、DGH-GT 783
- 界面のパラメータ数（設定 s1 / s2 / s3 / s4。N は数に効かない）: IRN 307,840 / 324,352 / 307,840 / 324,352、HiCE 295,232 / 311,744 / 295,232 / 311,744、
  HTT 142,208 / 146,368 / 142,208 / 146,368。うち g の線形（2048 → 64）131,136 と out（64 → 2048）133,120（グラフの型は 4K → 2048）

### C-3 既定の挙動が変わらない（完了判定 d。`$T/c/repro_compare.json`、`tools/run_repro.sh`・`tools/c_checks.py repro`）

    $ GPU=1 bash tools/run_repro.sh → repro gr rc=0 / repro tp rc=0
    $ .venv/bin/python tools/c_checks.py repro --out $T/c/repro_compare.json
    {"gr": {"all_equal": true, "same_inputs": true, "host_new": "andrew", "host_old": "andrew", "control_probs_shift_1e-6_equal": false, "control_jaccard_shift_1e-6_equal": false},
     "tp": {"all_equal": true, "same_inputs": true, "host_new": "andrew", "host_old": "andrew", "control_probs_shift_1e-6_equal": false, "control_jaccard_shift_1e-6_equal": false}}

- `grasp_hand_irn_hice_htt_repro_gr_001_GR-W3-N30-L2_DGH_conv_seed42` と前回の `grasp_hand_graph_arm_093_…`: J 0.676068481449154・acc 0.8825082508250826・最良の回 14・
  総 epoch 30・打ち切り 30 が同じ。val の確率は最良・最後とも差 0.0
- `grasp_hand_irn_hice_htt_repro_tp_001_D1-L1_pred_noCF_ep4_seed42` と `stage2fix_dp_004_…`: J 0.7808396679473972・acc 0.8785478547854786 が同じ、確率の差 0.0
- 対照: 確率を 1 か所 1e-6 ずらした写し・記録の J を 1e-6 ずらした値は、どちらも一致しない
- 型 TW の run の代わりに T→P の D1-L1 を選んだ理由は A-9

### C-4 学習前の一致と陽性対照（完了判定 e。`$T/identity/`、`$T/c/identity_summary.json`、`tools/run_identity.sh`・`tools/c_checks.py identity`）

    $ GPU=0 bash tools/run_identity.sh → 36 回とも rc=0（3 型 × 3 W × 4 設定、各 8 腕）
    $ .venv/bin/python tools/c_checks.py identity --out $T/c/identity_summary.json
    {"n": 288, "n_ok": 288, "identity_diff_max": 0.0, "identity_jaccard": [0.7762185528074379], "positive_range": [0.12118864059448242, 0.6558995246887207],
     "positive_changed": 288, "perturbed_params": [["iface.out.weight", "iface.out.bias"]], "n_receiver_trainable": [["W2", 36], ["W3", 72]]}

- 288 組み合わせ（3 型 × 8 腕 × 4 設定 × 3 W）で学習前の出力が塔単独とロジットの差 0.0、J 0.7762185528074379（塔単独の記録と同じ）
- 陽性対照: out の重みと bias を N(0, 0.05²) にすると 288/288 で出力が変わる（IRN 0.1323〜0.1442、HiCE 0.1393〜0.6559、HTT 0.1212〜0.2349）。bias も乱数にするので、
  入力の無い A0 でも変わる（前回の契約の T→P の空の腕のような空振りは無い）
- W2・W3 の学ぶ集合は定義（名前の接頭辞）と一致し、定義の外の名前を一つ混ぜると一致しない。受け取り手の側の学ぶテンソルは W2 36・W3 72

### C-5 試走（SPEC §6。`$T/smoke/`、`tools/run_smoke.sh`）

各型 1 本（W3・N 30・L 2・DGH、`--fixed-epochs 3 --smoke`、GPU 1 に 1 本）:

    smoke IRN rc=0 wall=4.1s peak_mem_MiB=976   （所要 0.90 s / 3 epoch、val J 0.5681 → 0.5940 → 0.6618）
    smoke HiCE rc=0 wall=4.4s peak_mem_MiB=848  （0.98 s、0.5677 → 0.5979 → 0.6542）
    smoke HTT rc=0 wall=4.2s peak_mem_MiB=776   （0.79 s、0.5670 → 0.5823 → 0.6599）

- 1 epoch 0.3 s 前後、GPU の使用量の最大 1 GB 未満（nvidia-smi の 0.5 秒ごとの値。CUDA の文脈を含む）。最初の `--max-epochs 3` の試みは
  「--scope W2・W3 は --fixed-epochs と組で使う」で 3 本とも rc 1（何も書かずに終わった）。引数を直して回し直した

### G3 — pass

三つの型が SPEC §4 の定義どおりで（C-2）、既定の挙動が変わらず（C-3）、学習前の出力が全組み合わせで塔単独と一致し、陽性対照で変わる（C-4）。

## Task D — 腕（G4）

### D-1 run の一覧と回し方（`tools/jobs.py`・`tools/run_jobs.sh`、記録 `$T/logs/all/events.log`）

- `jobs.py all` = 確かめ 5 本（接頭辞 `grasp_hand_irn_hice_htt_chk`）＋腕 243 本（`grasp_hand_irn_hice_htt_arm`。IRN 87・HiCE 69・HTT 87）= 248 本。回し直しの 2 本
  （`grasp_hand_irn_hice_htt_repro_{gr,tp}`）と合わせて SPEC §5.2 の 250 本。名前の重複 0。試走 3 本（`grasp_hand_irn_hice_htt_smoke`）は数えない
- 引数はどれも `--gr-dir $O --converge --save-last-probs --seed 42 --task-id <本契約> --ckpt-dir $T/dp_ckpt`、W&B は offline（`WANDB_MODE=offline`）
- 並行: GPU 2 枚 × 4 本（`NW=8`、worker w は GPU w % 2）。前回の腕の 96 本と同じ並行の数

      [jobs] all jobs 248 workers 8 start 2026-11-21T06:10:32Z（15:10:32 JST）
      [jobs] all all done 2026-11-21T07:04:16Z（16:04:16 JST。壁時計 53 分 44 秒）
      rc=0 248 件、rc≠0 0 件、skip 0 件

### D-2 終わりの数え上げ（完了判定 f。`$T/d/ends.json`、`tools/c_checks.py ends`）

    {"n": 248, "missing": [], "n_complete": 248, "n_converge": 248, "n_stopped_by_rule": 248, "n_cap": 0, "n_lr_ok": 248, "hosts": ["andrew"],
     "test_overlap": [], "elapsed_range": [4.84542616084218, 236.61332258675247], "control_nonexistent_name": 0, "control_existing_name": 1}

- 248 本とも収束規則の打ち切りで止まり、上限 120 に張り付いた run 0。248 本とも metrics.json・metrics_last.json・最良と最後の val の確率が在る
- config の学習率と weight decay が写した値（界面 5e-4・0.01、W2・W3 の受け取り手 5e-4・0.01）に 248/248 で一致。run の train・val の動画と {04, 05, 07} の共通 0
- 対照: 存在しない腕の名前（`IRN-W1-N10-L1_NO_SUCH_ARM_conv`）で 0 件、在る名前（`IRN-W1-N10-L1_DGH_conv`）で 1 件
- 最良の回の中央（W1〜W3 込み）: IRN 4・HiCE 11.5・HTT 14。最良の回が epoch 1 の run: IRN 26・HiCE 0・HTT 24（多くは W1。REPORT §2）。総 epoch 17〜68

### D-3 確かめの run（完了判定 g。`$T/d/chk_compare.json`、`tools/c_checks.py chk`）

最良と最後の回の val の確率を比べた。14 組とも**一致**（最大の差 0.0）。対照: 確率を 1 か所 1e-6 ずらした写しは 14/14 で一致しない。

| 確かめ | 一致 |
|---|---|
| IRN・HiCE・HTT の A0 の s4 と s1（W1） | 3/3 |
| HiCE の D と A0（s1・W1） | 一致 |
| HiCE の DH の s3 と s1（W1） | 一致 |
| IRN・HiCE・HTT の A0 とグラフの型の A0（s1、W1・W2・W3） | 9/9 |

SPEC §5.2 の流用の条件を満たしたので、A0 の s2〜s4（3 型 × 3 W × 3 = 27）、HiCE の D（W1 の s1 を除く 11）、HiCE の DH の s3・s4（3 W × 2 = 6）の 44 組み合わせに
流用先の値を使った。利用者の回答 (3) の「省いた run を回して埋める」（`jobs.py fill`）は要らなかった。

### G4 — pass

SPEC §5.2 の表の 248 本（と回し直しの 2 本）が収束規則で終わり、確かめの run の一致・不一致（14 組とも一致）が記録されている。

## Task E — 集計と報告

### E-1 塔単独（`$T/b/tower_alone.json`、`tools/tower_alone.py`。前回の道具の識別子と置き場だけ変えた写し）

    {"phase_jaccard": 0.7762185528074379, "phase_accuracy": 0.8712871287128713, "six_phase_mean": 0.7773831834035493, "equals_record": true}

### E-2 集計（`$T/e/summary.json`、`tools/aggregate.py`）

    {"n_runs": 384, "n_borrowed": 44, "recompute_max_dev": 0.0, "recompute_control_all_detected": true, "j7_equals_phase_jaccard_all": true, "n_recomputed": 340,
     "counts": {"GR": {"n_diffs_best": 96, "n_unreadable_best": 66, "n_metrics_identical_best": 2, "n_sign_flip": 31},
                "IRN": {"n_diffs_best": 96, "n_unreadable_best": 85, "n_metrics_identical_best": 23, "n_sign_flip": 40},
                "HiCE": {"n_diffs_best": 96, "n_unreadable_best": 76, "n_metrics_identical_best": 12, "n_sign_flip": 27},
                "HTT": {"n_diffs_best": 96, "n_unreadable_best": 67, "n_metrics_identical_best": 1, "n_sign_flip": 35}}}
    missing 0 []

- 測り直し: 本契約の 244 本（確かめのうち A0 の s4・HiCE の DH の s3 の 4 本は比べにだけ使う）と前回のグラフの 96 本の計 340 本で、val の確率から測り直した
  値（最良の回の J・acc・工程別、最後の回の J・acc。6 工程の平均は工程別から作る）と記録のずれの最大 0.0。1e-6 ずらした写しを 340/340 で検出。7 工程の平均 = 記録の phase_jaccard（340/340）
- グラフの型の数え（±0.015 の中 66・指標が同じ 2・符号が変わった 31）は前回の RESULT §3 と同じ
- 初回に 2 回、道具の誤りで止まり直した: numpy の真偽値が json に書けない（`bool()` で包んだ）、流用した run のパラメータ数が型の表に混ざる（流用を除いた）。値は変えていない

### E-3 報告（`experiments/analysis/grasp_hand_irn_hice_htt_pilot/REPORT.md` 740 行・`diffs.csv` 1,920 行（UTF-8 BOM つき）、`tools/make_report.py`）

- 型の中の差 4 型 × 8 種 × 4 設定 × 3 W × 最良・最後 = 768 行、同じ腕どうしの型の差 6 対 × 8 腕 × 4 設定 × 3 W × 最良・最後 = 1,152 行
- REPORT は記録から道具で作った（手で写していない）。採否・順位は書いていない

### E-4 IRN の手のトークンの効き（想定外の確かめ）

IRN では手のトークンの有無で確率がほとんど変わらない（W1 N10 L1 の D と DH の val の確率の最大の差 7.4e-6、DG と DGH 7.2e-6、W2 で 4.3e-4・4.0e-4。argmax は全フレームで一致）。
配線の誤りかを確かめた: seed 42 で作った IRN（N 10・L 1）に val 300 フレームの DG と DGH を入れると r_t の差の最大 6.1e-5（|r_t| の最大 0.047）で、手のトークンは r_t に届いている。
相互作用の注意の重みは初期化で 0.098〜0.102（10 個の術具にほぼ一様）で、手のトークンは問い合わせを通して重みを変えるだけなので効きが小さい。学習を長くすると効くかは測っていない

### E-5 変えていない（完了判定 j。`$T/e/j_unchanged.json`、`$T/e/pytest_end.txt`）

    $ python3 tools/listing.py compare --out $T/e/j_unchanged.json
    {"n_start": 246201, "n_now": 246201, "n_changed": 0, "n_removed": 0, "n_added": 0, "control_added": 1}
    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped（28.65 s）。失敗の名前は開始時の 6 件と同じ（diff 空）
    .venv 9c7be5c9…・.venv-relation-detr a74c9c78…（開始時と同じ）
    $ find $O third_party data/raw data/external data/annotations -newer $T/start/STARTED_MARKER -type f | wc -l → 0

- 対照: 本契約の新しいファイルを一つ加えた一覧は追加 1 として拾う
- 既存の道具は `dp_model.py`・`dp_train.py` に足す形だけ（C-1）。既定の挙動は回し直しの 2 本で記録と一致（C-3）
- `make forbidden-check TASK=<本契約>`: status pass、changed 2,293・checked 2,293、allow_write の 2 経路で許可 2,288 件、違反 0。
  残りの 5 件は禁止領域の外（`scripts/stage2pilot/dp_model.py`・`dp_train.py`、`tasks/<本契約>/` の 3 件）。
  対照: TASK を渡さないと status fail、本契約の 2,288 件が違反として名指される
- 本契約の保存先 `$T` は 565 MB（界面の重み・恒等性・確かめの出力）。run の記録は `experiments/phase1/grasp_hand_irn_hice_htt_*` の 253 フォルダ（248 本・回し直し 2・試走 3）
