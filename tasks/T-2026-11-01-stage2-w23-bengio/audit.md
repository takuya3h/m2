# audit — T-2026-11-01-stage2-w23-bengio（非公式の測定）

ホスト bengio。時刻は JST。`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio`。
重ねの BODY は `OV=/home/ubuntu/slocal2/s2fix-bengio-body`（三本目 T-2026-11-01-grasp-pilot-d と同じ。読むだけ）。

## 0. 始める（手順書の 0〜4）

### 0-1 一回目の `/task`（2026-11-01 23:5x 頃）

- 居た分岐 `feat/grasp-pilot-d`。`feat/stage2-w23-bengio` は手元・遠隔とも無し、`tasks/<id>` の履歴無し、`.sync-pause` 無し
- `scripts/task_start_classify.py`（比較先 origin/phase0 00f98c13）: **止める**。未追跡・起点に無い 11 件、すべて `experiments/` の下
  （`experiments/analysis/grasp_pilot_g/c3/c3_controls.py` と `experiments/phase1/grasppilot2_B_*_ep4_seed42/logs/{eval_meta_val,val_metrics_by_epoch}.json`。8.0K〜16K）
- 11 件は開いていた PR #274（`feat/grasp-pilot-g`、別ホストで実行中）の出力が同期で届いたもの。禁止領域なので退避の対象にしない
- 利用者の選択「2、exclude に足して」で `.git/info/exclude` に 12 行（注記 1・経路 11）を足した。**分類は変わらなかった。**
  `git check-ignore -v --no-index` で、`.gitignore:115` `!experiments/**/logs/val_metrics_by_epoch.json`、`:116` `!experiments/**/logs/eval_meta_*.json`、
  `:217` `!experiments/analysis/**/*.py` の打ち消しが `.git/info/exclude` より優先することを確かめた（`.gitignore` は exclude より強い）
- 利用者の判断で PR #274 の統合を待った

### 0-2 二回目の `/task`（2026-11-02 00:1x）

- `git fetch`: origin/phase0 00f98c13 → 392cf287。PR #274 は MERGED（2026-11-01T15:18:38Z = 11-02 00:18 JST）
- 分類（比較先 392cf287）: 未追跡・起点に在り中身が同じ 11 件（通す）→ **通す**
- 0-1 で足した exclude の 12 行は、11 件が phase0 に入ったので「phase0 に在る経路を無視の一覧で隠さない」に当たる。元から効いていなかった。
  控え（scratchpad の `exclude.bak`）を取ってから 26〜37 行目を外し、元の 25 行に戻した
- `source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-11-01-stage2-w23-bengio`:
  `[task-start] 分岐を作成: feat/stage2-w23-bengio（起点 origin/phase0）`、**`[task-start] .sync-pause を作成`**、`[task-start] 完了。`
- `.sync-pause` の中身: `task_id=T-2026-11-01-stage2-w23-bengio` / `branch=feat/stage2-w23-bengio`
- `grep -c sync-pause ~/bin/m2-sync.sh` → 2（稼働中の同期は抑止に対応）

### 0-3 検証とプリフライト

- `make task-validate`: `OK`、exit 0、WARN なし
- `make task-preflight`: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。
  SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（plan.env.preflight に記載なし）、P4・P5・P13・P14（kind=analysis で対象外）、P12（解決前提の参照が無い）

### 0-4 参照の解決（手順書の 3）

- `contract.conventions_rev` 2d946b07: `git log -1 -- context/conventions.md` = 2d946b07a57abebc4a8f66150d6dbaf2ccd22186。**一致**
- `meta.created_from`: runindex の最後の commit 68befc3b62ffc071077cca446df5d3c83b8c38b9（一致）。行数（見出しを除く）index 2363・experiments 1130・verdicts 1736（一致）。**差し替えなし、amendments なし**
- inject_verbatim の 7 アンカーの位置（`context/conventions.md`）: split 12、eval_recipe 24、prohibitions 98、env_p0 109、issuer_cautions 154、folds 297、det_groups 443

## Task A — 開始状態（G1）

### A-1 分岐と起点（`$S/start/a1_a2.txt`）

    branch: feat/stage2-w23-bengio
    HEAD = origin/phase0 = merge-base = 392cf287615b45f76829c7fa7f4e5cb39d4444c5
    origin/phase0 に在る: scripts/grasppilot、tasks/T-2026-11-01-grasp-pilot-d、tasks/T-2026-10-31-grasp-pilot-probe、tasks/T-2026-11-01-grasp-pilot-g
    PR 272 MERGED merge=c942fd13 → origin/phase0 の祖先
    PR 274 MERGED merge=5c7c2068 → origin/phase0 の祖先（二本目 grasp-pilot-g。Task D-3 の前提）
    PR 275 MERGED merge=5ffa91e5 → origin/phase0 の祖先（三本目 grasp-pilot-d）

二本目は起点に既に入っているので、Task D-3 の「phase0 を本分岐へ merge」は要らない（起点が統合後の phase0）。

### A-2 開始前から在る未追跡

    ?? tasks/T-2026-11-01-stage2-w23-bengio/SPEC.md
    ?? tasks/T-2026-11-01-stage2-w23-bengio/spec.yaml

（task-start が取り込んだ契約だけ。0-1 の 11 件は起点に入って追跡下になり、中身が同じ）

### A-3 compute プロセス（`$S/start/a3_procs.json`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py              → n_processes 54、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh             → count 8（自分のシェルを含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0

exe の basename に `python3.11` が 1 件あるのは列挙の道具自身（`proc_enum.py:63` で自分の PID を除く）。**本契約以外の compute は 0 件。**

### A-4 記憶領域・試験・仮想環境・GPU

- 空き（`$S/start/a4_df.txt`）: `/dev/sdb1` 7937302376448 B 中 使用 6117648420864、空き 1419559088128 B（1.3T、82%）
- GPU（`$S/start/a4_gpu.txt`）: 0 と 1 とも NVIDIA RTX A6000、49140 MiB、driver 595.84、**power.limit 220.00 W**（default・max 300 W）。
  UUID 0 = GPU-1b153400-9ec9-25fe-d601-7ddc39431aad、1 = GPU-525aae08-a3e0-1148-1887-8e541011ba04
- 試験（`$S/start/a4_pytest_start.txt`、`CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors`）:
  `11 failed, 965 passed, 5 skipped, 26 warnings, 1 error`。失敗と error の名前（`$S/start/a4_pytest_fail_names.txt`）は 12 件で、
  三本目の開始時（`stage2pilot_store/T-2026-11-01-grasp-pilot-d/start/a5_pytest_start.txt`）と同じ集合
- 仮想環境（`uv pip list --python <venv>/bin/python --format freeze`、`$S/start/a4_pkgs_summary.txt`）:
  `.venv` 108 行 sha256 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0、
  `.venv-relation-detr` 72 行 sha256 a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090（三本目の終わりの値と同じ）

### A-6 Relation-DETR と検出器の仮想環境（`$S/start/a6_reldetr_*.json`、道具 `scripts/grasppilot/reldetr_digest.py`。andrew は ssh で標準出力に出すだけ）

| 場所 | source_files | source_tree_sha256 | all_files | all_tree_sha256 | パッケージ |
|---|---|---|---|---|---|
| andrew main | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… | 72、8f08a2457e681d6d… |
| bengio main | 127 | 3ade18f0709362fa… | 140 | 89dc93b4a82f1e06… | 72、8f08a2457e681d6d… |
| bengio 重ねの BODY `$OV` | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… | 72、8f08a2457e681d6d…（`$OV/.venv-relation-detr` は main の venv へのリンク） |

**bengio main は andrew と違う。三本目と同じく重ねの BODY を使い、bengio main の `third_party` を変えない。** 検出の評価は重ねの BODY を指せる経路（`EGO_BODY=$OV`）で行う。

### G1 の判定

分岐 `feat/` で起点 origin/phase0 392cf287、前提の統合（PR 272・274・275）が起点に在る、本契約以外の compute 0 件、
空き・失敗の名前・仮想環境の要約値・電力の上限 220 W を記録した。**通過。**

## 設計の確かめ（Task C の前）

- `scripts/train_t1b.py:679-680` に `--lr`（既定 1e-4）と `--film-lr`（既定 5e-4）があり、
  `$OV/third_party/Relation-DETR/optimizer/param_dict.py:216` の `finetune_t1b` は名前に `phase` を含むパラメータを `film_lr` の群に分ける。
  §3.1 の受け取り手 1e-4・界面 5e-4 は既存の引数で渡せる（既存ファイルを変えない）
- `--trainable w2` は `pd_model.w2_parameter_names`（decoder の最終層とその層のクラスと box の頭）＋名前に `phase` を含むもの、
  `--trainable all` は設定の凍結以外のすべて（`train_t1b.py:284` `set_trainable`）
- **P3 の W1 は既に `--trainable w2` で回っている**: `scripts/stage2pilot/run_pd_fix.sh` の `P3) IFACE=query; TRAINABLE=w2`、
  `experiments/phase1/stage2fix_pd_P3_gt_ep4_seed42/config.yaml` の `trainable: w2`、`total_trainable: 1684883`。
  §3.1 の P3 の W2（界面 ＋ `--trainable w2`）は W1 の P3 と同じ集合になる
- W1 の腕（run の記録から）:
  - DP: D1-L1・D2・D3-L1・LC・TH・TH-NG は 6 腕（空・予測-noCF・正解・予測-CF・正解予測-CF・入れ替え）、D1-L2・D3-L2 は 4 腕（正解系なし）
  - PD: EQ（`stage2four_pd_EQ_*`）6 腕、P3（`stage2fix_pd_P3_*`）6 腕、P2L は `stage2fix_pd_P2L_shuffle` と `stage2pilot_pd_P2L_{empty,pred_noCF,gt,pred_CF,gtpred_CF}` の 6 腕
    （直しの契約の REPORT §535: P2L の 5 腕の値は前回の run の epoch 3 の記録）
  - GA: W1 は空・正解（`grasppilot_dp_00{1,2}_GA_*`）。予測の四腕は二本目（統合済み）

## 利用者の決定（2026-11-02 00:3x、本セッション）

- **P3 は W3 だけ回す。** P3 の W2（界面 ＋ `--trainable w2`）は W1 の P3 と同じ学ぶ集合なので回さない。W2 の欄には W1 の値を参考として置く。
  PD の本数は 36 → 30。`scripts/w23/run_pd_w23_bengio.sh` は `P3 W2` を拒む

## Task B — 材料と再現（G2）

### B-1 信号と checkpoint（`experiments/analysis/stage2_w23_bengio/material/material_check.json`、道具 `.../tools/material_w23.py`）

- 案 A の信号は bengio に無かった（`stage2pilot_store/T-2026-10-31-grasp-pilot-probe`・`T-2026-11-01-grasp-pilot-g` が無い）。
  andrew では読むだけで、本契約の置き場へ写した:

      $ scp andrew:.../T-2026-10-31-grasp-pilot-probe/signals/g_{train,val}.npz  $S/copied/grasp-pilot-probe/signals/
      $ scp 'andrew:.../T-2026-11-01-grasp-pilot-g/signals/A/g_*.npz'           $S/copied/grasp-pilot-g/signals/A/

- 参照の要約値: DP と案 A は W1 の run の `config.yaml`（`signals_train`・`signals_val`・`receiver.head_sha256`・`cache_sha256`。
  読んだ run は D1-L1 6、D1-L2 4、D2 6、D3-L1 6、D3-L2 4、LC 6、TH 6、TH-NG 6、GA 8 本）、PD は直しの契約の
  `material/material_check.json` と `bengio/input_digest_bengio.json`、EQ の `missed_train.json` は版管理下の写し
  （`experiments/analysis/stage2_pilot_four/xq/missed_train.json`、c312323d…。bengio の置き場の実物と `cmp` で一致。andrew には無い。EQ の W1 は 6 本とも bengio）
- 結果: **40 ファイルすべてが在り、要約値が記録と一致**（`all_exist: true`、`all_match: true`、PD の台本が読む信号で記録の無いもの 0 件）
- 陽性対照: 検出塔の重みの写しの中央の 1 バイトを変えると sha256 576df307… になり記録と不一致（`flip_control.matches_record: false`、写しは消した）

### B-2 塔単独の val（`experiments/analysis/stage2_w23_bengio/repro/run_repro.sh`、`b2_summary.json`、00:4x JST）

| 塔 | 値 | 記録（SPEC §2） | 差 |
|---|---|---|---|
| 検出塔 seed 42（30d199b1…） | overall 0.7273450248、標的群 0.7950748009、陰性対照群 0.6726631818、AP50 0.8518074 | 0.7273450・0.7950748・0.6726632 | 2.5e-8・8.6e-10 |
| 対照: 検出塔 seed 123 | overall 0.7288631、標的群 0.8234321、陰性対照群 0.6701777 | — | **+0.0015・+0.0284（標的群が許容差を超える）** |
| 工程塔（時間ヘッド 0d76d446…、特徴 c402e214…） | macro Jaccard 0.7762185528、frame accuracy 0.8712871287（09: 0.99317、10: 0.67537） | 0.7762186・0.8712871 | 0.0（`repro_ptower.py` の記録との差） |

- 検出は `pd_eval.py --cfg plain`、`EGO_BODY=$OV`（`env_check_det.txt`: `ms_deform_attn_ext True`）。予測を `$S/b/plain_val_preds_seed{42,123}.json.gz` に保存
- 群の AP は `scripts/stage2pilot/det_metrics.summary`

### G2 の判定

要約値が記録と一致、検出塔の overall と標的群の差がともに 0.005 以内、工程塔の差 0.0。**通過。**

## Task C — W2・W3 の実装と恒等性（G3）

### C-1 実装

- 既存のファイルで変えたのは `scripts/stage2pilot/dp_train.py` だけ（SPEC §5 Task C-1）。足したもの:
  `--scope {W1,W2,W3}`（train と identity。既定 W1）、`identity --arms`、下位命令 `scopes`、`apply_scope`・`scope_report`、`RECEIVER = {lr 5e-4, weight_decay 0.01}`。
  **新しい処理はすべて `scope != "W1"` のときだけ通る**（既定の経路の確かめは C-1b）。`GRASP_DIR` の読み方を `getattr` にした（`scopes` に引数が無いため。値は同じ）
- W2・W3 の最適化器は AdamW の 2 群（界面: STOP の 5e-4・0.01、受け取り手: RECEIVER の 5e-4・0.01）。時間ヘッドは W1 と同じく eval（`DPReceiver.train` が head を eval に保つ）。
  界面の重みの置き場に受け取り手の状態（`receiver`）も書く。`metrics.json` に `receiver_trained_changed`・`receiver_outside_scope_unchanged` を足す（`receiver_unchanged` は残す。W2・W3 では偽になる）
- 新しいファイル: `scripts/w23/run_pd_w23_bengio.sh`（PD。腕と信号の対応は `run_pd_fix.sh`・`run_pd_four.sh` を写した。`--lr 1e-4 --film-lr 5e-4` を明示、`--trainable w2|all`、EQ は `--missed-set`）、
  `scripts/w23/run_dp_w23_bengio.sh`（DP と案 A）、`experiments/analysis/stage2_w23_bengio/tools/{material_w23,pd_scopes,pd_w23_finalize}.py`、
  `.../taskC/run_{pd_identity,dp_identity,dp_default_check}.sh`
- PD の確定は `pd_fix_finalize.py`・`pd_four_finalize.py` を使わない（それぞれの契約の task_id を notes と metrics に書くため）。同じ計算をする `pd_w23_finalize.py` を新しく書いた
- `third_party/` は変えていない

### C-2 学ぶ集合

- DP（`taskC/dp_scopes.json`、`dp_train.py scopes`）: 9 型 × W1・W2・W3 のすべてで定義（名前の接頭辞 `iface.`、W2 は ＋`head.refine_stages.1.`、W3 は ＋`head.`）と一致。
  定義の外を一つ混ぜると不一致（W3 は外が無いので実在しない名前を混ぜた）。W1 の集合は従来の `trainable_report` と一致。
  要素数: W1 = 界面（D1・GA 1、D2 4、D3 8、LC 5、TH 9、TH-NG 8）、W2 = 界面 ＋ 36、W3 = 界面 ＋ 72
- PD（`taskC/pd_scopes.json`、`tools/pd_scopes.py`、`train_t1b.build_model` と `set_trainable`）: 3 型 × 3 範囲のすべてで定義と一致、混ぜると不一致。
  W1 の要素数は W1 の run の `total_trainable` と一致（P2L 150、P3 1,684,883、EQ 16,701）。
  W2: P2L 1,682,473、EQ 1,699,024、P3 1,684,883（**P3 の W2 は W1 と同じ集合**、`P3_W2_equals_W1: true`）。
  W3: P2L 48,471,350、P3 48,473,760、EQ 48,487,901。設定で凍結されるのは backbone の 11 個だけ（`frozen_all_backbone: true`）

### C-1b W&B の扱いと、既定の挙動の確かめ（`taskC/run_dp_default_check.sh`、`taskC/dp_default/`）

- 一度目（01:0x JST）: `run_dp_default_check.sh` が `scripts/load_env.sh` を読み込んでいたため、起点の版の `dp_train.py` の試走
  `experiments/phase1/w23b_chk_dpold_001_D1-L1_gt_ep1_smoke_seed42` が **W&B へオンラインで送られた**（`wandb_run.json`: run_id ntyprqmi、
  project egosurgery_multitask）。中身は config（経路・sha256・設定）と 1 epoch の指標で、資格情報は含まない。**契約 §7.10 の逸脱（実行者の確認不足）。**
  気付いた時点で台本を止めた（`pkill -f` の型が自分の命令の行にも当たり、裏の親ごと止まった。恒等性の台本の子は残って続いた）
- 利用者の決定: W&B は手元だけ（`WANDB_MODE=offline`、`WANDB_API_KEY=offline-placeholder`、`WANDB_DIR=$S/wandb`）。資格情報は読み込まない。
  送った 1 本は削除せず残す。`scripts/w23/run_dp_w23_bengio.sh`・`run_dp_default_check.sh` から `load_env.sh` を外し、`run_pd_w23_bengio.sh` からも外した（train_t1b.py は W&B を使わない）
- 一度目の試走の記録は `taskC/dp_default/train_D1-L1_old_online_ntyprqmi.log` に名前を変えて残した

## 利用者の指示（2026-11-02 01:1x JST、`meta.amendments` の 2 件目）

原文: 「(1) extra-queries の W2・W3 は回さない（W1 で足した出力が上位 300 に一度も入らず、W2・W3 でも仕組みが変わらないため）。
(2) P1（FiLM）の W3 を足す（andrew の契約から移す。腕と信号は直しの契約の run_pd_fix.sh の P1 と同じ。W1・W2 は andrew の値で、ホストをまたぐ参考の表に置く）。
(3) 工程から検出の W2・W3（P2L の W2・W3、P3 と P1 の W3）は、空・予測-noCF・正解・入れ替えの四腕だけ回す。検出から工程と案 A は六腕のまま。
(4) 全体が開始から 15 時間を超える見込みなら諮る。」

- `spec.yaml` の `meta.amendments` に 2 件（P3 の決定と本指示）を足した。`make task-validate` は OK
- PD の run は P2L W2・W3、P3 W3、P1 W3 の各 4 腕で 16 本。`run_pd_w23_bengio.sh` は表の外の組と腕を拒む（`EQ W2`、`P3 W2`、`P1 W2`、`P2L pred_CF W2` で拒むことを確かめた）
- P1 は `IFACE=film`、`configs/stage2pilot/pd_film_d9.py`（`run_pd_fix.sh` の P1-W1・P1-W2 と同じ界面）
- PD の恒等性は、指示の時点で P2L の 7 件と P3 の空が済んでいた。EQ と P3 の予測-CF・正解予測-CF を回さないよう、レーンの bash を止めて進行中の評価だけを終わらせ、
  `PD_TYPES="P3 P1" PD_ARMS="empty pred_noCF gt shuffle positive"` で残りを回した
- 開始の時刻: task-start 2026-11-02 00:2x JST。15 時間は 15:20 JST 頃

### C-1b（続き）既定の挙動の確かめ（オフライン、00:49〜00:51 JST、`taskC/dp_default/compare.json`、道具 `taskC/compare_default.py`）

- 起点の版（`git show 392cf287:scripts/stage2pilot/dp_train.py` → `$S/check/dp_train_old.py`）と変更後の版で、`--scope` を渡さない同じ命令を回した
- identity（D1-L1、TH）の JSON: 差 0 件
- 試走（`--fixed-epochs 1 --smoke`、正解の腕）`w23b_chk_dpold_002_D1-L1` 対 `w23b_chk_dpnew_001_D1-L1`、`w23b_chk_dpold_003_TH` 対 `w23b_chk_dpnew_002_TH`:
  metrics・config・history・クラス別・notes・val の確率・界面の重みの全テンソルが一致（違ってよい項目は経過時間と界面の重みの経路・sha256 だけ）。**`all_equal: true`**
- 陽性対照: 新しい版の metrics の phase_jaccard を 1e-9 ずらした写しは不一致として検出（`positive_control_detects: true`）
- 試走 5 本（`w23b_chk_dp{old,new}_*`）は腕に数えない。001（old・D1-L1）は C-1b の一度目でオンラインに送られたもの

### C-3 恒等性

- DP と案 A（`taskC/dp_identity/dp_<型>_<W>.json`、`run_dp_identity.sh`、00:4x〜00:51 JST）: 9 型 × W2・W3 の 18 ファイル、100 腕の行。
  **全 100 行で学習前のロジットの差の最大 0.0、Jaccard が塔単独（0.7762185528）と完全一致、学ぶ集合が定義と一致（混ぜると不一致）。**
  陽性対照（界面の最後の層を N(0, 0.05²)、TH はゲート α）で出力が変わったのは 90 行。変わらなかった 10 行は、
  D1-L1・D1-L2・D3-L1・D3-L2・GA の空の腕（各 W2・W3）。空の腕は入力が全部 0（concat は重み × 0）か、トークンが 0 個（D3）なので、
  界面の重みを変えても出力に届かない（構造上、この組では陽性対照が成り立たない）。同じ型の空でない腕ではすべて変わった
- PD（`taskC/pd_identity/pd_<型>_<腕>.json`、`run_pd_identity.sh`、00:3x〜01:08 JST）: 基準は B-2 の塔単独の予測。
  P2L 6 腕（空・予測-noCF・正解・予測-CF・正解予測-CF・入れ替え）、P3 6 腕、P1 4 腕（空・予測-noCF・正解・入れ替え）のすべてで
  **スコアの差 0.0・box の差 0.0 px・ラベルの不一致 0**、mAP 0.7273450248。陽性対照（`pd_eval.py --perturb`、正解の信号）で
  P2L スコアの差 0.046・mAP 0.7271786、P3 0.333・0.7272508、P1 0.511・0.7319521（変わった）。
  W は requires_grad だけを変え学習前の順伝播を変えないので、型と腕ごとの一回の評価が W2・W3 の両方の学習前に当たる（各 run の学習前と塔単独の差は pd_w23_finalize.py が run ごとにも記録）
- EQ の恒等性は指示（EQ を回さない）より前に始めた分も含め、出力が無い（評価の前にレーンを止めた）
- 注記: `pd_eval.py` の出力 JSON の `task_id` は道具の既定（T-2026-10-18-stage2-pilot-folda）が書かれる。置き場は本契約の `taskC/pd_identity/`
- P1 の学ぶ集合（`taskC/pd_scopes_P1.json`）: W1 266,880（W1 の run の記録と一致）、W2 1,949,203、W3 48,738,080。すべて定義と一致、混ぜると不一致

### G3 の判定

学ぶ集合が §3.1 と一致（DP 9 型・PD 4 型 × 3 範囲）、W1 の指定で W1 の集合と一致、全腕で学習前の出力が塔単独と一致、陽性対照で出力が変わる
（構造上成り立たない空の腕 10 行を除く）、既定の挙動が変わらない。**通過。**（01:09 JST）

## Task D — 学習

### D-1 検出から工程と案 A（`scripts/w23/run_dp_w23_bengio.sh`、4 列 = GPU 2 枚 × 2、01:10:08〜01:14:48 JST）

- 100 本すべて rc=0、`metrics.json` に `phase_jaccard` が在る、`code_sha256.txt` 100 本。W&B は offline（`$S/wandb`）
- 1 本の学習は 2 秒前後（特徴は保存済み）。同時に起きた run で ExperimentManager の通し番号が重なる（例 `w23b_dp_W2_001_` が複数）。名前の後半（型・腕）が違うので実験フォルダは重複しない
- 中間の表 `experiments/analysis/stage2_w23_bengio/INTERIM.md`（`tools/aggregate.py --part dp`）。commit c36ecf3f を push、Draft の PR #278

### D-1 工程から検出（`tools/pd_queue.sh`、8 列 = GPU 2 枚 × 4、01:15 JST から）

- 試走 `w23b_pd_P1-W3_gt_ep4_seed42_smoke`（1 epoch・6 ステップ・val 20 枚、01:10:35〜01:10:56）: rc=0、記憶の山 1 本 約 10.8 GiB。腕に数えない
- 一巡目は P2L の W2・W3 の 8 本。500 ステップの時点（01:36 JST）で 0.8〜1.1 it/s（W2 0.9〜1.1、W3 0.8〜0.9）、1 epoch 4,809 ステップの学習は 68〜87 分、GPU は 2 枚とも 100%・33 GiB
- 見込み: 1 本 約 6.3 時間（学習前の評価 約 12 分を含む）。一巡目 07:35、二巡目（P3・P1 の W3）14:10、報告まで 15:10 JST 頃。
  開始（00:20 JST）から 15 時間 = 15:20 JST に対し余裕 10 分ほど。1 epoch 目の評価の後に実測で見積もり直す
- 02:24 JST の見積もり直し: W3 は実測 0.82 it/s 前後、1 epoch の学習 約 98 分・評価を含め 約 110 分、1 本 約 7.5 時間（W2 は 約 6 時間）。
  一巡目 W2 07:15・W3 08:45、二巡目 14:45・16:15、報告まで 17:00 JST 頃（開始から 約 16.5 時間）。GPU は 2 枚とも 99〜100% で、本数を変えても速くならない見込み
- **利用者の決定（02:2x JST）: そのまま続ける。15 時間を超えることは逸脱にしない**
- 06:50・06:51 JST: P2L W2 の予測-noCF・入れ替えが終わった（rc=0、学習前と塔単独の差 0.0）。overall 0.724726・0.722051。列 1・3 は P3 W3 の予測-noCF・入れ替えへ移った
- **06:59 JST: P3 W3 の入れ替えが `torch.cuda.OutOfMemoryError` で止まった**（GPU 1、`exit_code.txt` 1）。W3 は学習中 1 本 約 13.5 GiB（試走の 10.8 GiB より多い）で、
  GPU 1 に W3 が 3 本（13.8・13.8・11.5 GiB）載っているところへ 4 本目を載せたため。列 3 の `pd_queue` の end 行の rc=0 は、台本の echo の書き方による誤表示（実際は 1）
- 07:08 JST: 列 2 が GPU 0 で P3 W3 の正解を始めた（GPU 0 にも W3 が 3 本）。同じ溢れで学習中の P2L W3 が落ちるのを防ぐため、**実行者の判断で列 2 の親と、始まって 56 秒の P3 W3 の正解を止めた**
- 利用者の決定（07:1x、回答の受け取りは 09:3x JST）: 枠が空き次第回す。止まった 2 本の実験フォルダは消さずに `$S/aborted/phase1/` へ移した（重みの置き場は作られていなかった）
- 06:50〜07:08 JST: P2L W2 の 4 本が終わった。08:04〜08:22 JST: P2L W3 の 4 本が終わった（8 本とも rc=0、学習前と塔単独の差 0.0）。列 4〜7 は P1 W3 の 4 本を自動で始め、W3 は 1 枚 3 本に収まった
- 09:3x JST: `tools/pd_sched.sh`（GPU ごとの run の起動台本を数え、1 枚 3 本まで）で、残りの P3 W3 の正解・入れ替えを、枠が空き次第始める
- 09:5x JST: `tools/aggregate.py` の PD の参考（W1・P1 の W2）を、直しの契約の `experiments/analysis/stage2_pilot_fix/report.json` の表から読むように直した（P2L の 5 腕と P1 の一部は前回の run の epoch 3 の記録で、行ごとの source に出所がある。ホストは run の server.txt）
- 13:00 JST: P3 W3 の予測-noCF が終わった（rc=0、学習前と塔単独の差 0.0、overall 0.698023）。13:01 に pd_sched.sh が GPU 1 で P3 W3 の正解を始めた（gpu0=3 gpu1=2）
- 13:3x JST: P3 W3 の空が終わった（rc=0、学習前と塔単独の差 0.0、overall 0.698119）。13:33 に pd_sched.sh が GPU 0 で P3 W3 の入れ替えを始めた（gpu0=2 gpu1=3）。待ち行列の 2 本はすべて始まった

## Task E — 集計・検証・報告（学習と並行して 13:5x〜14:3x JST に行った分。PD の残りが終わったら再集計する）

- g と e（`final/test_audit.json`、`tools/test_audit.py`）: 本契約の 110 本（その時点）で通した動画 {01,02,03,06,08,09,10,11,12,13,14,15}、{04,05,07} との共通 0 件。04 を混ぜると [04]。
  型ごとのホストの集合はすべて {bengio}。存在しない run の名前で 0 件
- h（`final/write_audit/`、`tools/write_audit.sh`）: 開始（2026-11-01 15:20 UTC = 11-02 00:20 JST）より後に変わったファイル。
  他の契約の置き場 4 つ・data/raw・data/external・data/annotations・third_party（main と重ね）・.venv・.venv-relation-detr・experiments/baselines・runindex は **0 件**（__pycache__ も 0）。
  experiments/phase1 の他 349・experiments/analysis の他 47・tasks の他 7 の計 403 件は、git の状態で分類すると、
  追跡下で HEAD と同じ 291 件（15:21 UTC = task-start の切り替えで git が phase0 の版を書いた grasp-pilot-g の出力）と、andrew の `w23a_*` の同期 112 件（未追跡 28・無視 84）（`classify.txt`）。
  陽性対照: 同じ探し方で本契約の置き場は experiments/phase1/w23b_* 1,430 件、stage2pilot_store/本契約 718 件
- `make forbidden-check TASK=T-2026-11-01-stage2-w23-bengio`（`final/forbidden_check.txt`、`final/forbidden_split.json`）: status fail、exit 2。
  changed 1,389、違反 28 件はすべて `experiments/phase1/w23a_*`（andrew の並行する契約の未追跡の出力が同期で届いたもの）。**本契約の経路の違反 0 件**
- 試験（`final/pytest_end.txt`）: `11 failed, 965 passed, 5 skipped, 1 error`。失敗と error の名前の集合は開始時と同じ（diff 0）
- 仮想環境（`final/pkgs_end_summary.txt`）: `.venv` 108 行 9c7be5c9…、`.venv-relation-detr` 72 行 a74c9c78…。開始時と同じ
- Relation-DETR（`final/reldetr_end_{main,overlay}.json`）: bengio main 3ade18f0…/89dc93b4…、重ねの BODY 2f08e521…/20f15c06…。開始時と同じ
- 報告: `REPORT.md` は `tools/make_report.py` が `final/aggregate.json`（`tools/aggregate.py --part all`）から作る。`RESULT.md`・`result.yaml`・`resolved_refs.md`（inject_verbatim の 7 アンカーの原文を機械で切り出した）、
  `README.md` と `docs/experiment_log.md` の項を書いた。PD の残り 6 本の値の箇所は「【終了後】」の印を置いた
- PD の参考の値（W1 と P1 の W2）は直しの契約の `report.json` の表から読んだ（`tools/aggregate.py`）
- 14:0x JST: P1 W3 の予測-noCF・入れ替えが終わった（rc=0、学習前と塔単独の差 0.0、overall 0.694144・0.688607）。GPU 1 は P3 W3 の正解 1 本だけになり、使用率 39%
- 14:42 JST: P1 W3 の空・正解が終わった（rc=0、学習前と塔単独の差 0.0、overall 0.669506・0.702851）。P1 W3 の 4 腕が揃った。pd_queue の 8 列はすべて終わり、残りは pd_sched.sh の P3 W3 の正解・入れ替え（各 GPU 1 本）
- 16:21 JST: P3 W3 の正解（回し直し）が終わった（rc=0、学習前と塔単独の差 0.0、overall 0.691882）。残りは P3 W3 の入れ替え（GPU 0）だけ

## 中止（利用者の指示、2026-11-02 16:5x JST、`meta.amendments` の 3 件目）

原文: 「本契約をここで止める。走っている run をすべて止め、新しい run を起動しない。止めた時点までの実測（終わった run の値、止めた run の名前と止めた epoch）を
RESULT.md と audit.md に書き、status は stopped とする。理由は「利用者の指示による中止（把持塔 G の設計の誤りが分かったため）」。止めた run の出力は消さずに残す。
commit・push・PR（base phase0）・make task-report まで行う。meta.amendments に利用者の指示として記録する。」（直前に「実験設定に不備があったので直ちに実験を中止して」）

- 止めた時点で走っていたのは `w23b_pd_P3-W3_shuffle_ep4_seed42` だけ（GPU 0。待ち行列 `pd_sched.sh` の最後の 1 本）。ほかの 115 本は終わっていた
  - 16:56:55 JST: `pd_sched.sh`（PID 3882866）、起動台本 `run_pd_w23_bengio.sh`（3971618・3971620）、確定 `pd_w23_finalize.py`（4046560）に SIGTERM。`train_t1b.py` の過程はもう無かった
  - 止めた epoch: 4 epoch 目（epoch 3）の学習と val の評価は終わっていた（train.log `[t1b] DONE best@ep3 mAP=0.6970 (init 0.7273)`）。
    確定の出力（`w23_metrics.json`・`notes.md`・`predictions_moved.json`）は 16:56:57 JST に書かれ、予測 2 ファイルは `$S/pd_preds/` へ移っていた（sha256 c5067147…・0ac1aae5…）。
    確定の過程は SIGTERM の後もしばらく残り、16:57 に二度目の SIGTERM で消えた
  - 起動台本を止めたので、この run には `end.txt` と `exit_code.txt` が無い（ほかの記録は揃っている）。出力は消さずに残した
- GPU の compute のプロセス 0 件を確かめた。15 分ごとの確認（このセッションの定期実行）も止めた
- 最終の集計（16:5x JST、`final/aggregate.json`）: PD 16/16、DP と案 A 100/100。`final/test_audit.json`: 116 本で test との共通 0、型ごとのホストはすべて {bengio}
- REPORT.md は `tools/make_report.py --status-note` で冒頭に中止の旨を置いて作り直した。予測 §6.3 の照合は (1) 外れ（W3 が W1 より大きい型は P1 だけ）、(2) 当たり（P2L −0.0372、P3 −0.0292、P1 −0.0578）
- 案 A（GA）の予測の腕（予測-noCF・予測-CF・正解予測-CF・入れ替え）の信号は、二本目（T-2026-11-01-grasp-pilot-g）の把持塔 G の予測から作られている（`$S/copied/grasp-pilot-g/signals/A/`）。中止の理由に関わる可能性がある
- 17:0x JST（最後）: `make forbidden-check` をもう一度回した（`final/forbidden_check_end.txt`）。status fail、exit 2、changed 1,474、違反 32 件はすべて `w23a_*`（andrew の同期）、**本契約の経路 0 件**
- 17:1x JST: `make task-report` exit 0（verdict stopped、n_issuer_defects 3、report_sha256 54cf0c4bf7f1…、report_bytes 10094、replaced_blocks 0）。PR #278 は Draft を外した（base phase0）
