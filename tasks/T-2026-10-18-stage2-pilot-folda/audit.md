# audit — T-2026-10-18-stage2-pilot-folda

**非公式の予備測定（本 task_id）。** 命令と出力の記録。`RESULT.md` から行番号で指す。時刻は JST。
ホスト andrew（`hostname` = `Andrew`）、repo `/home/ubuntu/slocal2/m2`。

## 0. 始める（2026-10-18 14:00 頃）

### 0-1 状態の読み取り（task-start の前）

    $ git branch --show-current            → feat/tower-reselect-prereq
    $ git status --porcelain --untracked-files=all   → （空。清浄）
    $ git branch --list feat/stage2-pilot-folda      → （空）
    $ git ls-remote --heads origin refs/heads/feat/stage2-pilot-folda → （空。exit 0。鍵の警告 `id_Andrewdeploy not accessible` は無害）
    $ git log --all --oneline -1 -- tasks/T-2026-10-18-stage2-pilot-folda → （空）
    $ ls -d tasks/T-2026-10-18-stage2-pilot-folda → No such file or directory
    $ cat .sync-pause → No such file or directory

判定: 清浄（手順 0 の 5）。

### 0-2 task-start

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-18-stage2-pilot-folda 2>&1 | grep -vE '(sk-|secret_|ntn_|API_KEY=)'
    [load_env] .env をロード（WANDB_API_KEY=set / NOTION_API_KEY=set）
    OK   T-2026-10-18-stage2-pilot-folda
    1 task(s), 0 failed
    WARN [L2-6] conventions.md が 073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6 以降に変更されています。差分を確認してください
    取り込みました: tasks/T-2026-10-18-stage2-pilot-folda

**実行者の誤り（記録）**: 秘匿値を落とすために付けた濾過 `grep -v 'sk-'` が、`ta`**`sk-`**`start` / `ta`**`sk-`**`release`
を含む `[task-start]` の行をすべて落とした。そのため **「[task-start] 完了。」と「.sync-pause を作成」の文言を出力で確かめていない**
（Task A-7 は文言での記録を求める）。代わりに状態で確かめた。

    $ git branch --show-current → feat/stage2-pilot-folda
    $ cat .sync-pause
    task_id=T-2026-10-18-stage2-pilot-folda
    branch=feat/stage2-pilot-folda
    $ git status --porcelain → ?? tasks/T-2026-10-18-stage2-pilot-folda/SPEC.md, spec.yaml

`.sync-pause` は 0-1 で**実行前に無い**ことを確かめており、いまは所有の記録つきで在る。`scripts/task_start.sh:146-150` は
目印が無いときだけ作って「作成」と表示し、在れば触れない。したがって **目印はこの契約の task-start が作った（「作成」）**。
task-start は取り込みの成功（161 行）のあとに「完了」を出す。取り込みは成功した（「取り込みました」）。

### 0-3 検証（L1 + L2）

    $ make task-validate TASK=T-2026-10-18-stage2-pilot-folda
    WARN [L2-6] conventions.md が 073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6 以降に変更されています。差分を確認してください
    OK   T-2026-10-18-stage2-pilot-folda   / exit=0

WARN を利用者に提示し、続行の承認を得た（「続行」。選択肢 1: Task A-6 に従い差し替えて amendments に記録）。
差し替えの後の再検証: `OK` / exit=0、WARN なし。

### 0-4 プリフライト（L3）

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-10-18-stage2-pilot-folda
    P1 venv_active PASS / P6 decisions_answered PASS / P7 destination_writable PASS / P8 contract_valid PASS
    P9 spec_lint PASS（規則 9 件を検査し該当なし）/ P10 preflight_names_known PASS
    RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL   exit=0

SKIP 8 件: P2 cuda_ext_loaded、P3 deterministic_flags、P4 prereg_committed、P5 frozen_source_hash、
P11 gpu_free、P12 refs_resolved、P13 symmetry_table_complete、P14 proposal_card_checked。

### 0-5 自動同期の抑止

    $ grep -c sync-pause ~/bin/m2-sync.sh → 2（対応済み）

### 0-6 参照の解決

`contract.inject_verbatim` の 8 アンカー（prohibitions、issuer_cautions、env_p0、folds、split、eval_recipe、det_groups、crossfit）は
`context/conventions.md` の `b12eda6c` 版の原文を読んで適用する。原文は repo の当該版にあるため、ここに写さない。
`inputs.denominator`、`inputs.sigma_policy`、`inputs.frozen_source` は契約に無い。

## A. 開始状態

### A-1 分岐と起点（Task A-1）

    $ git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0
    40112290ed8e53165d9ea1a0dce6cdc7cddae2ce（3 つとも同じ）
    $ git log --oneline -1 --grep='#229' origin/phase0 → db222b7b Merge pull request #229 from takuya3h/feat/tower-reselect-prereq
    $ git merge-base --is-ancestor db222b7b origin/phase0 → 真

分岐 `feat/stage2-pilot-folda`（`feat/` で始まる）。起点 `origin/phase0` = `40112290`。**PR #229 は統合済み。**

### A-2 未追跡（Task A-2）

開始前の未追跡は 0 件（0-1）。退避は行わない。task-start が取り込んだ `SPEC.md` と `spec.yaml` は本契約のもの。

### A-3 compute プロセス（Task A-3、2026-10-18 14:05 JST）

道具: `experiments/analysis/stage2_pilot_folda/tools/proc_enum.py`（`/proc/PID/exe` の解決と、引数の要素の完全一致）。

    $ .venv/bin/python tools/proc_enum.py --summary
        9 None   ← exe を解決できない（権限）。引数は sshd 3 件と ssh-agent 6 件（下）
        8 .../node/v20.20.2/bin/node ／ 8 .../vscode-server/.../node ／ 8 /usr/bin/bash ／ 8 /usr/bin/zsh ／ 7 /usr/bin/dash
        4 .../zmx ／ 3 /usr/bin/sleep ／ 2 .../codex ／ 2 .../claude/versions/2.1.301 ／ 2 .../syncthing
        1 .../claude/versions/2.1.302 ／ 1 .../codex（musl）／ 1 .../copilot-runtime ／ 1 .../code-110a… ／ 1 .../code-6d62… ／ 1 /usr/bin/git ／ 1 /usr/bin/ssh
    --- python 系（exe の basename が python で始まる）→ 0 件
    $ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv → （見出しだけ。0 件）
    $ nvidia-smi --query-gpu=... → 0, RTX A6000, 16 MiB, 0 % ／ 1, RTX A6000, 16 MiB, 0 %
    exe 不明の 9 件: 1 sshd listener（uid 0）、1604279 sshd [priv]（uid 0）、1604290 sshd ubuntu@notty、ssh-agent -s × 6

**本契約以外の compute プロセスは 0 件。** 10-17 の 2 件（python3.12 の常駐）は居ない。

対照（完了判定 a の四列目）:

    陽性 1 回目: bash -c 'sleep 30' zzz_s2pilot_marker & → count=0。bash が単一の命令を exec で置き換え、exe=/usr/bin/sleep になったため（対照の作り方の誤り）
    陽性 2 回目: bash -c 'sleep 30; true' zzz_s2pilot_marker &（exe=/usr/bin/bash）
      $ proc_enum.py --exe /usr/bin/bash --argv zzz_s2pilot_marker → 1814862 / count=1
      $ proc_enum.py --exe /usr/bin/zsh  --argv zzz_s2pilot_marker → count=0
    陰性: $ proc_enum.py --exe /no/such/exe_zzz → count=0

### A-4 記憶領域（Task A-4）

    $ df -B1 /home/ubuntu/slocal2/m2 → /dev/sdc1 7937302376448 total, 5839774601216 used, 1697432907776 avail（78%）

見積もり（上限側）: 写し 0.22 GB（efros の実測 `du -sb`: 005 94,413,766 / 008 3,054 / 009 1,614,227 / 特徴 127,016,881）、
信号 1 GB 未満、交差適合用の検出塔 2 本 6.6 GB（確定塔の作業フォルダ 3,316,993,212 B × 2）、PD の run 60 本 36 GB 以下
（最良の checkpoint だけを残す前提）。計 60 GB 未満 ≪ 空き 1,697 GB。**足りる。**

### A-5 試験（Task A-5、開始時）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    6 failed, 802 passed, 22 warnings in 21.10s

失敗の名前の集合（6 件）は前契約の終了時（`tasks/T-2026-10-17-tower-reselect-prereq/audit.md` の試験）と同じ。

### A-6 起票時の値（Task A-6）

| 項目 | 起票時 | 実測 | 差し替え |
|---|---|---|---|
| `conventions_rev`（`git log -1 -- context/conventions.md`） | 073f9dc0 | **b12eda6cf0f53f4f0d09e5b6c53bb3afde9831ac** | **した**（`meta.amendments` の 2 件目） |
| `runindex_commit`（`git log -1 -- runindex/`） | 63ae65da | 63ae65da8c7d32df591f5e2ee4358286b72c726b | 不要 |
| index / experiments / verdicts（行数 − 1） | 1961 / 750 / 1506 | 1961 / 750 / 1506 | 不要 |

`073f9dc0..HEAD -- context/conventions.md` は 2 commit（`2da88a8f`、`b12eda6c`。PR #229）。節ごとの本文の sha256（先頭 12 桁）:

    $ .venv/bin/python scratchpad/anchor_cmp.py 073f9dc0 b12eda6c ...
    prohibitions eca28977acd6 eca28977acd6 SAME ／ issuer_cautions 5c0e35f2cfa7 同 SAME ／ env_p0 5072018fd411 同 SAME
    folds 02a8633f0c57 同 SAME ／ split c21380392d60 同 SAME ／ eval_recipe d8c14f8bb211 同 SAME ／ det_groups b27c34b84aec 同 SAME
    crossfit 89fb3d1905bc eb36d8fff508 DIFF ／ symmetry 8961a725f77d f6d8c5a35d6b DIFF ／ frame_sets <none> 85113ab06b75 DIFF
    crossfit の実差分（diff | cat -A）: 「12a13 > $」＝末尾の空行 1 行だけ

inject_verbatim の 8 節の本文は両版で同一。symmetry と frame_sets の DIFF は差分のある節を検出した陽性対照を兼ねる。

### A-7 抑止の目印（Task A-7）

0-2 のとおり。**この契約の task-start が作成した**（文言は実行者の濾過で落ちたため、状態で確かめた）。

### 関門 G1: **pass**

分岐 `feat/` で起点 `origin/phase0`、本契約以外の compute プロセス 0 件、空き 1,697,432,907,776 B、失敗の名前 6 件を記録した。

## B. 材料と再現

### B-1 efros の工程塔の写し（読むだけ）

道具: `experiments/analysis/stage2_pilot_folda/tools/copy_efros_ptower.sh`（efros 側で走るのは `sha256sum` と rsync の送り出しだけ）。
写し先（版管理と同期の外）: `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/efros_ptower/`（以下 STORE/efros_ptower）。

1 回目は zsh で `for p in $LIST` が単語分割されず（conventions#issuer_cautions「シェルの前提」）、何も写らなかった。
efros 側の前後は一致（`before==after: yes`）。自分の写し先にできた空のフォルダは削除せず `STORE/_aborted_attempt1/` へ移した。
2 回目（bash の台本）:

    efros files: 30  copy files: 30
    efros before==after: yes
    efros==copy: yes
    c402e214d28d32c68b396fe84bbefefffdf7577d9550c421364543af78f172da  .../p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz   （= 009 の config の cache_sha256）
    79c2c4782458c981b347e424a7b27dd81166e9721317d6dc569e8d92241acf6b  .../005_ft_.../checkpoints/best.pth              （= 008 の config の checkpoint_sha256）
    0d76d446796f855a51640d756d6d3436573ff40ed600915980021c5f4cc6ad6d  .../009_P15_C_.../checkpoints/best.pth

両端の一覧: `STORE/efros_ptower/{efros_sha256_before,efros_sha256_after,andrew_copy_sha256}.txt`。
陽性対照: 009 の best.pth を 1 バイト変えた複製 → `0d76d446796f855a` が `df7e96d30736afd4` に変わった。

**andrew には同じ 30 ファイルが既に在り、すべて efros と同一だった**（`SAME` 30 件）。SPEC §2 の「andrew には無いものとして扱う」は
実測と食い違う（conventions#issuer_cautions 注意 1。実測を正とした）。以後は STORE の写しを使う。

### B-2 検出塔の checkpoint

    $ sha256sum experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth
    30d199b15201cf3c03954852d8acc6fb58fe5349baef2fd200e877237ff682c4   （= SPEC §2 = test_access_ledger.csv 2 行目）

### B-3 塔単独の val の再現

工程塔（`scripts/stage2pilot/repro_ptower.py`、写した特徴と時間ヘッド、stage1_ptower.evaluate と同じ評価）:

    phase_jaccard 0.7762185528074379（記録 0.7762185528074379、差 0.0）／phase_accuracy 0.8712871287128713（記録と同値、差 0.0）
    動画ごと: 09 Jaccard 0.99317 / acc 0.99614、10 Jaccard 0.67537 / acc 0.80642。val 1,515 フレーム
    対照（P20 seed42 の時間ヘッド 036 を同じ特徴に当てる）: Jaccard 0.6379452、acc 0.8528053（値が変わる）

検出塔（`experiments/analysis/stage2_pilot_folda/repro/eval_dtower_val.sh` → `scripts/eval_relation_detr_map.py --split val`）:

1 回目は 10 分を超えて進行の行が出ず止まった（両 GPU 約 600 MiB・使用率 100%・CPU 100%。efros では同じ評価が 1 分 14 秒）。
自分の評価を止めるとき `pkill -f <命令行>` が自分のシェルにも当たり終了した（注意 6 の型）。PID で残存 0 件を確かめた。
torchrun の最小 all_reduce で切り分けた:

    （既定）           120 秒で打ち切り（止まる）
    NCCL_P2P_DISABLE=1 rank0/rank1 allreduce ok sum=3.0 0.21s
    nvidia-smi topo: GPU0–GPU1 = PHB、/sys/kernel/iommu_groups = 32

andrew は IOMMU が有効で GPU 間 P2P が止まる。以後の 2 プロセスの命令はすべて `NCCL_P2P_DISABLE=1`（計算は変わらない）。
2 回目: `Test: Total time: 0:01:05`、`mAP=0.7273`。

    overall mAP 0.7273450248398429（記録との差 0.0）、標的群 AP 0.7950748（記録 0.7951、差 −2.5e-5 は記録の丸め）、
    陰性対照群 AP 0.6726632（記録 0.6727、差 −3.7e-5 は丸め）。クラス別 AP は既存の eval_val.json と完全一致。欠けた群のクラス 0
    対照（seed 123 の checkpoint）: mAP 0.7288631、標的群 0.8234321、陰性対照群 0.6701777（値が変わる）

**関門 G2: pass**（差はどちらも 0.0。許容差 0.005 の内）。B-5（写した fine-tune の重みで特徴を作り直す）は「記録だけでよい」とされた任意の項で、行っていない。

## C. 確定塔の信号の保存

置き場: `STORE/signals/final/<信号>_<train|val>.npz`（frame_ids, x。D-GT-INST は count も）。記録: `record_{train,val}.json`、
`record_phase_{train,val}.json`（写しを `experiments/analysis/stage2_pilot_folda/signals/` に置く）。

- クラスの順序: 工程は phase_vocab の番号順（anesthesia, closure, design, disinfection, dissection, dressing, hemostasis, incision, irrigation）、
  術具は注釈の category id 0〜14（Bipolar Forceps … Tweezers）。全腕でこの順序
- 対象: 折り A の train 9,657 / val 1,515 フレーム（術具注釈の画像 = 工程マニフェストのフレーム。突き合わない件数 0 / 0）
- K = 11（折り A の train の 1 フレームあたりの正解の枠の数の最大。val の最大は 8）。枠 0 の train 画像 39 枚
- 検出側は fp32・eval・batch 1（`scripts/stage2pilot/extract_det_signals.py`）。拡張の読み込みを確認（`ms_deform_attn_ext=True`）
- **経路の同一性**: val の後処理後の出力（上位 300）を COCO の評価器に通した mAP = **0.7273450248398429**（Task B と同値）。
  後処理の上位と自前の top-k の不一致フレーム 0（train / val とも）
- 正解の枠の総数: train 32,272、val 4,707（注釈の件数と一致）

工程側（`scripts/stage2pilot/phase_signals.py signals`）: P0 の argmax で出した val の Jaccard 0.7762185528074379（Task B と同値）。

**D0-INST の読みの割れ（利用者に諮る）**: 後処理の出力は（query, クラス）の組ごとに並ぶため、上位 K 個の組には同じ query が
複数のクラスで入る。重複は train 48,087 / 106,227 枠（45%）、val 7,488 / 16,665 枠（45%）。val の先頭フレームでは
確信度 0.943 の Skewer の query 1 つが 11 枠中 7 枠を占めた。SPEC §3 の字面（組の上位 K = 読み (a)）と、重複しない query の
上位 K（読み (b)）の両方を保存した（D0-INST と D0-INST-UQ）。どちらを使うかは利用者の決定を待つ（注意 14）。

### C-5 / C-6 送り手の差と較正（工程塔）

| 分割 | macro Jaccard | frame accuracy |
|---|---|---|
| train（10 本、9,657） | 0.8309798 | 0.9578544 |
| val（2 本、1,515） | 0.7762186 | 0.8712871 |
| 差 | 0.0548（> 3pt） | 0.0866（> 3pt） |

較正（等幅 15 区間、最大確率）: 温度 1 の ECE は train 0.16963 / val 0.22933。val で当てた温度 0.55998（NLL 最小）で
train 0.02094 / val 0.05477。val の NLL 0.71350（温度 1）。

### C-7 P2F の表

`experiments/analysis/stage2_pilot_folda/signals/p2f_table.json`。折り A の train の正解だけ（9,657 フレーム、動画 10 本）。
工程ごとのフレーム数 [281, 3595, 245, 11, 3832, 12, 825, 763, 93]（時間ヘッドの config の class_counts と一致）。

### 利用者の決定（2026-10-18 15:3x JST）: D3 の予測トークン

SPEC §3 の「後処理後の出力のうち、スコアの上位 K 個」の読みを利用者に諮った（注意 14）。回答: **重複しない query の上位 K 個**
（読み (b)、`D0-INST-UQ`）。D3-L1 と D3-L2 の予測のトークンは全腕でこの版を使う。字面どおりの版（`D0-INST`）も保存してある。

### C-4 時刻（道具: `scripts/stage2pilot/time_check.py`。frame_signal_audit の judge / shifted_copy をそのまま使う）

`experiments/analysis/stage2_pilot_folda/signals/time_alignment_final.json`。

| 信号 | train | val | 名前を一つずらした写し |
|---|---|---|---|
| P-GT, D0, D-GT, D0-RT, D0-INST, D0-INST-UQ, D-GT-INST | 同時刻 | 同時刻 | −1（全件） |
| P0 | **ずらし(−1)** | **ずらし(−1)** | −2 |

P0 の一致率（train）: k=−2 0.9656、−1 0.9665、0 0.9579、+1 0.9377。この道具は「予測の argmax が何フレームずらした正解と最も
一致するか」で判定するため、切り替わりを遅れて捉える因果の予測（時間ヘッドは平滑化 0.3 で学んである）を −1 と判定する。
**情報の時刻と予測の遅れを区別できない。** そこで異質な方法（注意 2）で確かめた（`phase_signals.py construct-check`）:
各動画から等間隔に 40 フレーム t を選び、特徴の先頭から t までだけを時間ヘッドに通した出力と保存した P0[名前 t] を比べた。

    train（400 フレーム）: 差の最大 2.38e-7（許容 1e-5）→ 同時刻。ずらした写し: t での差の最小 8.55e-5、t−1 での差の最大 2.98e-7 → −1 と検出
    val （80 フレーム）: 差の最大 3.58e-7 → 同時刻。ずらした写し: t での差の最小 1.64e-3、t−1 での差の最大 1.79e-7 → −1 と検出

途中で道具が無言で落ちた（rc=137。共通部品 `load_signal` が npz の `d["x"]` を行ごとに読み直し、各行が全体の view として
全体を生かし続けたためのメモリ不足）。一度だけ読む形に直した（train_t1b.py の `load_signal_npz` も同じく読み直していたので直した）。

### C-5 送り手の差（検出塔）

`--check-map` つきで train を抽出し直し（`STORE/signals/final_recheck/`）、6 信号の sha256 が 1 回目と全件一致（決定性）。

| 分割 | overall mAP | 標的群 AP | 陰性対照群 AP |
|---|---|---|---|
| train（9,657） | 0.8388572 | 0.8528809 | 0.8475875 |
| val（1,515） | 0.7273450 | 0.7950748 | 0.6726632 |
| 差 | 0.1115（> 3pt） | 0.0578（> 3pt） | 0.1749 |

## D. 界面の実装と恒等性

### D-1 工程から検出の学習器

`scripts/train_t1b.py` に引数を足した（既定の経路は不変）: `--det-ckpt`、`--signal-train/--signal-val`（次元は信号から決まる）、
`--fixed-table`、`--eval-only`、`--patience`（学習率一定・停滞で停止）、`--best-excludes-init`、`--ckpt-dir`、`--save-trainable-only`、
`--trainable w2`。注釈は従来の `EGO_ANN_DIR`、モデル設定は従来の `T1B_MODEL_CFG`。
試験 `tests/test_train_t1b_stage2pilot_defaults.py`: 5 passed。既定を `best_ap50.pth` に変えた写しでは 2 failed（空振りしない）。

### D-2 / D-3 型の実装と設定

PD: `scripts/stage2pilot/pd_model.py`（RelationDETRStage2Pilot）、設定 `configs/stage2pilot/pd_{film,clsbias_lin,clsbias_fix,query}_d{9,18}.py`
（生成器 `make_pd_configs.py`。検出塔のモデル設定との差は検出器のクラスと引数の行だけ）。
DP: `scripts/stage2pilot/dp_model.py`（DPReceiver）、学習器 `dp_train.py`。

- 検出塔の W2 = `transformer.decoder.layers.5`、`class_head.5`、`bbox_head.5`。全層で共有の `decoder.norm` と `encoder_*_head` は含めない
- P3 の query: decoder の主経路の 900 個の object query（`tgt_embed`）に足す。denoising の query と学習時だけの hybrid の query には足さない（全腕で同じ）
- D1: `stage1.conv_in` は Conv1d(2048, 64, 1)（入力の線形写像）なので SPEC どおり Conv1d(S, 64, 1, bias=False) を零で足した（代わりの形は使っていない）
- D3: 注意の次元 64、頭数 4（学習対象 D3-L1 266,944 ≒ P1 266,880）。トークン 0 個は零
- 受け取り手の工程塔は凍結し、学習中も eval（dropout なし）で使う

### D-4 / D-5 恒等性と陽性対照

PD（`scripts/stage2pilot/pd_eval.py`。基準は塔単独を同じ評価経路に通した予測 `STORE/identity/plain_val_preds.json.gz`、mAP 0.7273450248398429）。
信号は 9 次元が P0 の val、18 次元が [P-GT, P0] の val。陽性対照は界面の最後の層を N(0, 0.05²)（P2F は Task C-7 の表 B）。

| 設定 | 学習前 mAP | score の差の最大 | 枠の差の最大 | ラベル不一致 | 欠けた鍵 | 陽性対照 mAP | score の差の最大 |
|---|---|---|---|---|---|---|---|
| P1 film d9 | 0.7273450 | 0.0 | 0.0 | 0 | 界面 4 個だけ | 0.7308222 | 0.4914 |
| P1 film d18 | 0.7273450 | 0.0 | 0.0 | 0 | 界面 4 個だけ | 0.7286071 | 0.6295 |
| P2L d9 | 0.7273450 | 0.0 | 0.0 | 0 | 界面 2 個だけ | 0.7272254 | 0.0445 |
| P2L d18 | 0.7273450 | 0.0 | 0.0 | 0 | 界面 2 個だけ | 0.7262620 | 0.0488 |
| P2F d9（B=0） | 0.7273450 | 0.0 | 0.0 | 0 | 表 1 個だけ | 0.7092860（表 B） | 0.8730 |
| P3 query d9 | 0.7273450 | 0.0 | 0.0 | 0 | 界面 2 個だけ | 0.7272018 | 0.3335 |
| P3 query d18 | 0.7273450 | 0.0 | 0.0 | 0 | 界面 2 個だけ | 0.7271757 | 0.4596 |

予想外の鍵（checkpoint にあってモデルに無い）は全設定で 0 件。

DP（`dp_train.py identity`。信号は val の予測と正解。陽性対照は界面の最後の層を N(0, 0.05²)）:

| 型 | 腕 | 次元 | 学習対象 | 学習前 Jaccard | ロジット差の最大 | 陽性対照 Jaccard | ロジット差の最大 |
|---|---|---|---|---|---|---|---|
| D1-L1 | 予測 / 正解 | 15 | 960 | 0.7762186（Task B と同値） | 0.0 / 0.0 | 0.761899 / 0.761871 | 0.3007 / 0.3320 |
| D1-L2 | 予測 | 3840 | 245,760 | 同値 | 0.0 | 0.590338 | 2.7262 |
| D2 | 予測 / 正解 | 15 | 267,264 | 同値 | 0.0 / 0.0 | 0.769094 / 0.768029 | 0.1687 / 0.1612 |
| D3-L1 | 予測 / 正解 | 20 | 266,944 | 同値 | 0.0 / 0.0 | 0.766811 / 0.757641 | 0.1401 / 0.2151 |
| D3-L2 | 予測 | 276 | 299,712 | 同値 | 0.0 | 0.751041 | 0.3647 |

（D3 の恒等性は字面どおりの版 D0-INST で測った。零初期化の出力射影の下ではトークンの中身によらず恒等である）

### D-8 test 不使用（`scripts/stage2pilot/test_audit.py`）

信号ファイルの frame_ids、学習と評価に渡した注釈の画像、DP の run の config から集めた動画の集合と {04, 05, 07} の共通: **全段 0 件**
（信号 12 本、PD 注釈 12 本、交差適合の注釈 12 本、DP 12 本、恒等性 2 本）。`--inject 04` で共通 1 件（['04']）。

### 関門 G3: **pass**

基準の型 P1-W1（film d9）と D2 が学習前に塔単独と同じ出力（差 0.0）を出し、陽性対照で出力が変わり、test の動画との共通は 0 件。

### D-9 試走（1 本の所要時間）

DP（3 epoch、`dp_train.py train --max-epochs 3`）: D1-L1 15 s、D1-L2 13 s、D2 13 s、D3-L1 16 s、D3-L2 14 s（読み込みを含む壁時計）。1 epoch 1〜2 秒。
検出の交差適合用の塔（H1 の先頭 40 枚、2 epoch、`run_cf_dtower.sh H1smoke`）: 3 分 33 秒、rc=0。損失 71.94 → 58.86、
`convergence.json` に val AP の推移、GPU 1 枚あたり記憶の山 9.4 GB。**andrew で検出塔の学習（逆伝播）が動いた**（E-4）。
PD（1 epoch、fp32、正解の腕）: P1-W1 は 06:11:46〜07:30 UTC。単独の間 2.6〜2.7 it/s（1 epoch 約 30 分の速さ）、検出塔 2 本と相乗りの後 1.2 it/s。
学習前 mAP 0.7273、1 epoch 後 0.7365。凍結部の要約値は前後で同じ。**rc=2 は実行者の誤り**: 走っている最中に `run_pd.sh` を
書き換えたため、bash が続きを読み違えて後処理（end.txt、exit_code.txt）の手前で落ちた。学習と結果の書き出し（t1b_result.json、予測）は完了している。
以後、走っている台本は書き換えない。

### 利用者の指示（2026-10-18 16:4x JST）: PD は seed 42 だけ

「早く終わらせたい」「PD は seed42 だけでよい。1/3 にして」。PD の 4 型の腕を seed 42 だけにした（20 本）。P2F の 2 本と DP の 63 本は変えない。
キューから seed 123・456 の PD の行を外した（外す前の写し `STORE/queues/gpu{0,1}.q.before_seed42only`）。`meta.amendments` の 3 件目に記録。
PD では R と規則 2 を出さない（集計の道具 `aggregate.py` の PD_SEEDS）。

### 数値精度の変更（PD の腕、最初の腕の前）

利用者の「できるだけ早く」を受け、PD の腕の学習の順伝播を bf16 の自動混合精度にした（`run_pd.sh` の `--amp bf16`。PD の全腕で同じ）。
評価は常に単精度（train_t1b.py の仕様）なので恒等性は塔の値と厳密に比べられる。試走は fp32。

### D3 の空の腕

トークンが 0 個で界面に入力が届かず、損失に勾配の道が無い（1 回目は `does not require grad` で落ちた。落ちた 3 run は
`STORE/failed_runs/` へ移した）。勾配の無い step は更新しない形に直し（`steps_without_grad` を記録）、回し直した。
D3-L1 の空の腕は 3 seed とも 0.7762186（塔単独と同値）。D1-L1 の空の腕も同じく 3 seed とも塔単独と同値（零の入力では足した重みに勾配が来ない）。
**D1 と D3 の空の腕は構造上 3 seed で同一になり R = 0 になる**（完了判定 k の四列目「空の腕の 3 seed の値が同一でない」は D1・D3 で成り立たない）。

### 検出の交差適合用の塔 H1 の 1 回目が記憶不足で落ちた（実行者の誤り）

H1（06:24:32〜07:51:42 UTC）は 3 epoch 目の学習中に GPU 1 の記憶不足で rc=1（`torch.cuda.OutOfMemoryError: ... GPU 1 has a total capacty of 47.40 GiB of which 61.00 MiB is free`）。
そのとき GPU 1 には PD の試走（P1-W2、fp32、20.67 GiB）と検出塔 2 本（12.26 GiB と 12.87 GiB）が相乗りしていた。**記憶の山を見積もらずに相乗りさせた実行者の誤り。**
気づいたのは 09:46 UTC（待ちの監視は 2 本の終了を待つ形で、1 本目の失敗を知らせなかった）。val AP は 0.3696 → 0.5293 → 0.5333 まで。
途中の重み（epoch 2 の best_ap.pth）を信号に使わないよう、証跡と作業フォルダを `STORE/failed_runs/stage2pilot_cf_dcoco_H1_seed42_oom_attempt1/` へ移した（消していない）。
同じ台本・同じ処方で 09:48:52 UTC に最初から学び直しを始めた（port 29791）。そのときの相乗りは PD（bf16、約 8 GiB）と H2（約 14 GiB）で、1 枚あたり約 36 GiB の見込み。
同じ時間帯の P1-W2 の試走の rc=2 は P1-W1 の試走と同じ原因（走っている最中の `run_pd.sh` の書き換え）。学習は最後まで済んでいる（`DONE best@ep0 mAP=0.7340 (init 0.7273)`）。

### 利用者の指示（2026-10-18 19:2x JST）: 締め切り 10/20 01:00 JST、PD の上限を 4 epoch に

見積もり（1 epoch は検出塔 2 本と相乗りで約 60 分、単独で約 34 分。1 本 3〜8 epoch）では、PD の平均が 5 epoch 以上だと締め切りに間に合わない。
利用者に四つの案（上限 4、上限 3、PD の交差適合の腕をやめる、締め切りで打ち切る）を示し、**上限 4** が選ばれた。`meta.amendments` の 4 件目に記録。
- `run_pd.sh` の MAX_EPOCHS を 8 から 4 へ。走っている bash を壊さないよう、別名の写しを直して `mv` で置き換えた（10:15 UTC。走っている 2 本は古い inode を読み続ける）。
- 上限 8 で起動済みの P1-W1 の空と予測-noCF は、`cap_watch.sh` が 5 epoch 目の始まり（`[t1b][ep4 0/`）を見つけたら、命令行を確かめた
  train_t1b.py の親プロセスだけを止める。結果は `cap_finalize.py` が、ログの各 epoch の val mAP と最良の重みの epoch から `cap_result.json` に書く
  （両者が食い違えば止まる）。最良の予測は 4 epoch 目の評価までの最良のまま残る。4 epoch 目までに止め方の規則で自分で終われば何もしない。
- 止めた run では凍結部の要約値（学習の終わりに書かれる）が UNKNOWN になる。
- 作業の誤り: 追記の Edit で `intent.question` 行の先頭を一度置き換え、直後に戻した（`git diff` が空であることを確かめた）。

## E. 交差適合用の塔（記録）

### E-1 train の二分割（`scripts/stage2pilot/crossfit_split.py` → `experiments/analysis/stage2_pilot_folda/crossfit/split.json`）

126 通り（動画 01 を含む側を H1）。d(H) = 工程のフレーム比率の全変動距離 + 術具の枠のクラス比率の全変動距離（`a1_fold_table.profile` /
`total_variation`、基準は train 10 本全体）。規則は max(d(H1), d(H2)) 最小 → 和 最小 → H1 の辞書順。最上位の同点は 1 件（同点なし）。

| 順位 | H1 | H2 | d(H1) | d(H2) | max | 和 |
|---|---|---|---|---|---|---|
| 1（選択） | 01 06 11 12 15 | 02 03 08 13 14 | 0.1469 | 0.1142 | 0.1469 | 0.2611 |
| 2 | 01 02 03 08 14 | 06 11 12 13 15 | 0.1191 | 0.1647 | 0.1647 | 0.2838 |
| 3 | 01 03 08 12 14 | 02 06 11 13 15 | 0.1076 | 0.1699 | 0.1699 | 0.2775 |
| 4 | 01 08 11 12 15 | 02 03 06 13 14 | 0.1706 | 0.1157 | 0.1706 | 0.2863 |
| 5 | 01 06 08 11 15 | 02 03 12 13 14 | 0.1748 | 0.1633 | 0.1748 | 0.3382 |

### E-3 検出の交差適合用の注釈（`make_cf_annotations.py` → `crossfit/annotations.json`。置き場 `STORE/ann_cf/{H1,H2}`）

元 `data/annotations/egosurgery_tool_folds/A/instances_train.json`（sha256 `fc63621e…`。変えていない）を動画単位で絞った。
H1: 画像 4,075、枠 14,201。H2: 画像 5,582、枠 18,071（計 9,657 / 32,272 = 元と一致）。val は折り A の val。test の注釈は置いていない。

### E-4 検出塔の学習（andrew で初めて）

試走は D-9（rc=0、逆伝播と収束規則の記録が働いた）。本番は H1・H2 とも 2026-10-18 06:24 UTC に起動（GPU 2 枚、2 プロセス、fp16、
`--convergence-schedule --max-epochs 36`、`NCCL_P2P_DISABLE=1`）。H1 は記憶不足で落ちて学び直した（上の「H1 の 1 回目」）。

## F. 測定（記録）

### F-1 DP の交差適合を要しない腕（39 本）と中間記録

D1-L1・D2・D3-L1 は空・予測-noCF・正解、D1-L2・D3-L2 は空・予測-noCF（各 3 seed）。06:31〜08:26 UTC（D3-L1 の空は回し直し）。
1 本の所要は平均 4.0 分、最大 7.3 分（metrics.json の elapsed_seconds）。`aggregate.py --interim` で `INTERIM.md` / `interim.json` を作り、
commit `00560d62` を `feat/stage2-pilot-folda` へ push した。

    $ git ls-remote --heads origin refs/heads/feat/stage2-pilot-folda → 00560d62d54b53ea932bed9729d824eac55a58c5（完了判定 m: 分岐の先頭）

### F-2 P2F（学習なし、`run_pd.sh P2F <pred|gt> 42`）

予測: overall mAP 0.7093（塔単独 0.7273 との差 −0.0180）。正解: 0.7325（+0.0052）。所要 4 分ずつ。

### F-3 PD の空の腕の陰性対照（`scripts/stage2pilot/run_pd_negctl.sh <型>` → `experiments/analysis/stage2_pilot_folda/negctl/`）

空の腕の重み（`STORE/pd_ckpt/<空の腕>/best_t1b.pth`）を `pd_eval.py --iface-state` で読み、(1) 零の信号で評価して run 自身の最良の予測と比べ、
(2) 零の代わりに確定塔の P0 の val を入れて (1) の予測と比べた。

| 型 | (1) mAP | (1) と run の予測の差 | (2) mAP | (2) の score の差の最大 | 標的群 / 陰性対照群（(2)） |
|---|---|---|---|---|---|
| P1-W1 | 0.7303425 | score 0.0、枠 0.0、ラベル不一致 0 | 0.7302817 | 0.5907 | 0.8028600 / 0.6743257 |

P1-W1（FiLM）の空の腕は、信号を入れ替えると出力が変わる（D2 と同じ構造: 零の入力では FiLM の最初の層の重みに勾配が届かず初期値のまま残るため）。

### F-4 上限 4 の当て方（P1-W1 の上限 8 で起動した 2 本）

- 空: 規則で ep2 に止まった（val mAP 0.7303 / 0.7275 / 0.7302、最良 ep0）。上限は効かず、見張りは何もしなかった（`[cap_watch] … は自分で終わった rc=0`）。凍結部の要約値は前後で一致
- 予測-noCF: val mAP 0.7320 / 0.7303 / 0.7336 / 0.7271。ep3 の後も規則で止まらず、`[t1b][ep4 0/` を 14:13:07 UTC に見つけて pid 1947794 を止めた（rc=143）。
  `cap_finalize.py`: 最良 ep2、0.7336（ログの 4 桁）、最良の重みの epoch 2 と一致。最良の予測 `val_inj_best.json.gz` は 12:50:50 UTC（ep2 の評価の時刻）のまま。
  上限 4 で起動していれば ep3 の後に上限で終わり、同じ最良を選ぶ。`cap_result.json` の mAP はログの 4 桁で、表の AP は最良の予測から計算し直す（aggregate.py）

### E-4 の続き: 検出の交差適合用の塔 H2 の終わり

H2: 06:24:33〜14:39:08 UTC、rc=0、学習 8:14:25。`convergence.json`: 学習率の低下 epoch 12、最良 epoch 13（val AP 0.6583943）、
打ち切り epoch 17（「学習率の低下（epoch 12）の後も 4 epoch 続けて最良を更新しなかったため打ち切る」）。**止め方の規則で止まった。**
val AP の推移: 0.4637 0.5556 0.5875 0.6294 0.6257 0.6353 0.6167 0.6339 0.6563 0.6214 0.6490 0.6421 0.6087 0.6584 0.6519 0.6532 0.6491 0.6497。
重み `STORE/cf_dtower/stage2pilot_cf_dcoco_H2_seed42/work/best_ap.pth`。

### F-5 GPU 1 枚で PD を 2 本ずつ回す試し（14:55 UTC〜）

H2 が終わった後（H1 だけと相乗り）の 1 枚 1 本の速さ（10 秒ごとの記録から、500 step の所要）: P1-W1 正解 260 s（1.92 it/s）、
P2L 空 170〜190 s（2.6〜2.9 it/s）。14:55:03 UTC に `gpu_queue.sh` の 2 本目を GPU ごとに起動した（同じキュー、flock で取り出す）。
2 本目が取ったのは P2L 予測-noCF（GPU 0）と P2L 正解（GPU 1）。計算の中身は変わらない（同じ台本・同じ引数）。
2 本とも学習に入った後（15:00〜15:12 UTC）の 500 step の所要: GPU 0 は P1-W1 正解 411 s（1.22 it/s、1 本のときの 0.63 倍）と P2L 予測-noCF 320 s
（1.56 it/s、0.56 倍）、GPU 1 は P2L 空 290 s と P2L 正解 290 s（各 1.72 it/s、0.62 倍）。**GPU ごとの合計は 1 本のときの 1.19 倍と 1.23 倍**
（P2L の 1 本の速さは 2.8 it/s として）。H1 の iter_time は 1.04〜1.33 s で目立った遅れは無い。1 枚 2 本を続ける。

### E-4 の続き: 検出の交差適合用の塔 H1（学び直し）の終わり

H1: 09:48:51〜17:38:06 UTC、rc=0、学習 7:49:05。`convergence.json`: 学習率の低下 epoch 12、最良 epoch 17（val AP 0.6127332）、
打ち切り epoch 21（「学習率の低下（epoch 12）の後も 4 epoch 続けて最良を更新しなかったため打ち切る」）。**止め方の規則で止まった。**
val AP の推移: 0.3723 0.5268 0.5212 0.5747 0.5649 0.5904 0.5705 0.6036 0.6048 0.5805 0.5710 0.5981 0.5636 0.6059 0.6071 0.6047 0.6107 0.6127 0.5995 0.6060 0.6122 0.6102。
**検出の交差適合用の塔は 2 本とも止め方の規則で止まった**（G4 の検出側）。

17:39 UTC: `run_cf_det_signals.sh` を GPU 0 で起動（H1 の塔 → H2 の動画、H2 の塔 → H1 の動画）。工程の交差適合用の塔は
`run_cf_ptower.sh H1` / `H2` を各 GPU のキューの先頭に入れた（fine-tune の確保の最大は efros の元の run で 29.05 GB。取り出し役が空いた時点で始まり、
相乗りの PD は 1 本になる。H1 の最中に入れると記憶が足りないため、H1 の後に入れた）。

### F-3 の続き: P2L の空の腕の陰性対照

| P2L | 0.7273490 | score 0.0、枠 0.0、ラベル不一致 0 | 0.7273490 | 0.0（変わらない） | 0.7950740 / 0.6726742 |

P2L（クラスの logit への線形）の空の腕は、信号を入れ替えても出力が変わらない（零の入力では信号にかかる重みに勾配が届かず零のまま。学ぶのはクラスごとの一定の値だけ）。
P2L の空の腕の val mAP は各 epoch で塔単独と 4e-6 以内（0.7273484 / 0.7273490 / 0.7273483 / 0.7273486。塔単独 0.7273450）。クラスごとの一定の値はクラスの中の順位を変えないため。

### E-5 工程の交差適合用の塔 H2 の記憶不足と立て直し（実行者の誤りを含む）

- 17:44 UTC に GPU 1 で始まった H2（キュー経由）は、始めは 33 GB、10 分後に **42.2 GB** に増えた（可変の大きさの画像で caching allocator の確保が膨らんだ。
  efros の元の run の確保の最大は 29.05 GB）。相乗りの P2L 正解 4.1 GB と合わせて 46.3 / 49.1 GB。P2L 正解の後に取り出し役が W2 の腕（約 8 GB）を取ると足りなくなるため、
  **GPU 1 の 2 本目の取り出し役（pid 2033634）の bash だけを止めた**（P2L 正解は親 pid 1 で走り続ける。その行は `.done` に残らない）。GPU 0 のキューの先頭の H1 も外した
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`（計算は変わらない。本体の torch 2.1.2 で受け付けることを確かめた）で H2 を学び直すことにし、キューの先頭に入れて元の python を止めた。
  **実行者の誤り**: 止めた python（41 GB）が解放し終わる前に取り出し役が学び直しを始め、学び直しが記憶不足で 8 秒で落ちた（rc=1）。取り出し役は次の P1-W2 予測-noCF を GPU 1 で始めた。
  落ちた 2 つの run（`stage2pilot_cf_ptower_001/002_ft_…_foldAH2_seed42`）は `STORE/failed_runs/cf_ptower_H2_attempts_1_2/` へ移した
- 17:59 UTC: H2 を設定つきでキューを通さずに GPU 1 で直接起動（`queues/cf_ptower_H2_run.log`）。見張り（`scripts/stage2pilot/ptower_watchdog.sh H2 34000` と同じ中身）が
  python の記憶が 34,000 MiB を超えたらその python だけを止める（PD の run を巻き込まないため）。起動直後 28,042 MiB
- 設定つきの H2 は 5 分間 28,372 MiB のまま増えなかった（設定なしでは 10 分で 42.2 GB）。GPU 1 は計 39.8 GB。
  H1 も同じ形で GPU 0 に入れるため、**GPU 0 の 2 本目の取り出し役（pid 2033633）の bash だけを止めた**（P2L 予測-noCF は孤児で走る）。

### E-5 検出の交差適合版の信号（`run_cf_det_signals.sh`、17:39〜18:15 UTC、GPU 0）

- H1 の塔 → 動画 02 03 08 13 14、H2 の塔 → 動画 01 06 11 12 15。**各塔が出した動画の集合は学習に使っていない半分と一致し、学習に使った半分との共通は 0 件**（完了判定 j）。
  合わせて train 10 本 9,657 フレーム（`STORE/signals/cf/{D0,D0-RT,D0-INST,D0-INST-UQ}_train.npz`）
- 時刻（`crossfit/time_alignment_cf_det.json`）: 4 信号とも train 9,657/9,657 が対応し「同時刻」、名前を一つずらした写しは −1
- 記録: `crossfit/record_det_from_{H1,H2}.json`、`extract_det_from_{H1,H2}.log`

### E-6 工程の交差適合用の塔 H1 の起動

18:16 UTC: H1 を `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` つきで GPU 0 に直接起動（`queues/cf_ptower_H1_run.log`）、見張り `ptower_watchdog.sh H1 34000`。
起動直後 28,372 MiB。GPU 0 は計 40.4 GB、GPU 1 は 39.8 GB。

### F-6 DP の交差適合を要する腕（24 本）

18:18 UTC: `run_dp_batch.sh - D1-L1:pred_CF D1-L1:gtpred_CF D1-L2:pred_CF D2:pred_CF D2:gtpred_CF`（GPU 1、15 本）と
`run_dp_batch.sh uq D3-L1:pred_CF D3-L1:gtpred_CF D3-L2:pred_CF`（GPU 0、9 本）。交差適合を要しない腕と同じ指定（D3 は重複しない query の版）。
G4 は工程の塔を含む 4 本の後に評価するが、DP の CF の腕が使うのは検出の塔 2 本の信号だけで、その 2 本は止め方の規則で止まり j も満たしたため先に回した（順序の判断）。

### E-5 の続き: 交差適合版の検出の送り手（`crossfit/cf_det_sender.json`）

2 本の予測（上位 300、後処理後）を合わせ、折り A の train 10 本の注釈で評価: overall mAP **0.4002144**、標的群 AP 0.4393237、陰性対照群 AP 0.4363991。
半分ごと（`--check-map`）: H1 の塔 → H2 の動画 0.3561550、H2 の塔 → H1 の動画 0.4534500。動画ごと: 01 0.667 / 02 0.594 / 03 0.222 / 06 0.430 / 08 0.332 / 11 0.523 / 12 0.238 / 13 0.432 / 14 0.246 / 15 0.486。
**確定塔の val（0.7273）よりかなり低い**（確定塔の train 0.8389 とは逆向きの差）。交差適合用の塔は train の半分で学び val AP も 0.6127 / 0.6584 に留まったため。
予測-CF の腕は、学習時は確定塔の val より弱い信号、評価時は確定塔の val の信号を受ける（REPORT の限界に書く）。

### F-1 の続き: 中間記録の更新（型ごとに交差適合を要しない腕が揃うたび）

- P1-W1: commit `dfe57511` を push（17:0x UTC。`git ls-remote` の先頭が `dfe57511`）
- P2L: commit `7c72edfd` を push（19:3x UTC。`git ls-remote` の先頭が `7c72edfd`）。P2L の正解と予測-noCF は上限 4 で停止（最良 ep3）、凍結部は前後で一致
- 19:44 UTC までに 24 本すべて rc=0（`queues/dp_cf_batch_{A,B}.log`）。**DP の 63 本が揃った。** 1 本の所要は工程塔と相乗りで 5〜14 分
