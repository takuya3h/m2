# audit — T-2026-11-02-bengio-align-andrew

時刻は UTC（JST = UTC+9）。出力の置き場 `$D = experiments/analysis/bengio_align_andrew`。repo の外の置き場 `$S = ~/slocal2/stage2pilot_store/T-2026-11-02-bengio-align-andrew`（評価の予測）。
andrew へ送った命令は全件 `andrew_cmds.log`（13 行）。包み `tools/A.sh`（前の契約と同じ。`StrictHostKeyChecking=yes`・`UpdateHostKeys=no`・`BatchMode=yes`）。
前の契約の道具（`tasks/T-2026-11-02-bengio-andrew-env-survey/tools/` の `tree_files.py`・`stat_tree.py`・`data_inventory.py`・`lists.json`・`leftovers.py`）をそのまま使った。

## 0. 始める

- 12:1x UTC。開始時の分岐 `feat/bengio-andrew-env-survey`、作業ツリーは清浄。分類 `scripts/task_start_classify.py`（比較先 origin/phase0 d145854e）→ **通す**。
- `make task-start`: 分岐 `feat/bengio-align-andrew` を作成、**`[task-start] .sync-pause を作成`**、契約を取り込み `[task-start] 完了。`。
- `grep -c sync-pause ~/bin/m2-sync.sh` → 2。`make task-validate` → OK。`make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL
  （SKIP: P2・P3・P4・P5・P12・P13・P14。P9 spec_lint 該当なし、P11 gpu_free PASS）。
- 参照: 起票時の `conventions_rev` b59081e0 は phase0 の #282 の統合の commit（2026-11-02 20:58 JST）で、`context/conventions.md` の最後の commit は 2d946b07。
  `git diff b59081e0 origin/phase0 -- context/conventions.md` は空（中身は同じ）。runindex 68befc3b・2363/1130/1736 は起票時と同じ。注入の 3 アンカーの原文は `resolved_refs.md`。

## Task A — 開始状態（G1）

- `$D/start/a_state.txt`（12:13:57）: 分岐 `feat/bengio-align-andrew`、HEAD = origin/phase0 = merge-base = d145854e。未追跡 5（本契約のもの）。
  worktree 4（本体、m2-four、m2-s2fix-bengio、wt_phase0）。空き `/dev/sdb1` 1,415,039,631,360 B、overlay 1,400,457,428,992 B。GPU 0・1 とも 39・20 MiB、使用率 0%、compute アプリ 0。
- `proc_enum.py`: n_compute 1（中身は計数の結果を受けた私自身の `python3 -c`。本契約以外は 0）、gpu_pids []。陽性 zsh 8、陰性（存在しない経路）0。
- 要約値（`reldetr_digest.py`、`$D/start/`）: andrew main 142/2f08e5213cb5c377…・155/20f15c061b435ce4…・72/8f08a245…、
  bengio main 127/3ade18f0709362fa…・140/89dc93b4a82f1e06…、重ねの BODY 142/2f08e521…・155/20f15c06…。**調査と一致。**
- andrew の Stage 2 の材料 17 件（`tools/stage2_17.txt`、調査の `d/data_compare.json` から）: `sha256sum` と `stat` を andrew で読み、**17/17 が調査の記録と一致**（`$D/start/andrew_stage2_17.txt`）。
- 前の値: `checkpoints` 12 件（`$D/start/bengio_main_files.json`）、仮想環境の列（`.venv` 108 9020a519…、`.venv-relation-detr` 72 8f08a245…）、
  データ（`$D/start/data_digest.json`。調査と同じ `data_inventory.py`・`lists.json`。B1 15,437・45ee4cc2…、固定記録 32,670 経路の要約値 bb1fd0e9…）、
  stat の木（`$D/start/stat_before.json`。data 08729bb0…、.venv c6ec6a75…、.venv-relation-detr f2c740b0…、stage2pilot_store ad08d931…、入れ子の third_party a319509d…）、
  `~/slocal2` 直下の大きさ（`$D/start/slocal2_sizes.tsv`）、試験（`$D/start/pytest.txt`、名前 12 件 = 調査時と同じ集合）。
- 試験は 12:14:47〜12:15:33 で、Task B の写し（12:15:28）と終わりの 5 秒が重なった。収集（`test_stage1_dtower_convergence.py` の収集の失敗を含む）は写しの前に済み、
  結果（11 failed・965 passed・1 error、名前 12）は調査時と同じ。

### G1 の判定

分岐 feat/、起点 origin/phase0。3 か所の Relation-DETR の要約値と andrew の材料 17 件が調査と一致。**通過。**

## Task B — Relation-DETR を揃える（G2）

- B-1（scratchpad）: 調査の `b/andrew_copies/*.py.txt`（andrew の版）に `b/diffs_bengio_vs_andrew.patch` を `patch -p1 --binary` で当てると、
  **8/8 が今の bengio の版と sha256 一致**。対照: 戻した `main.py` の 100 バイト目を変えると不一致。
- B-2（12:15:28）: 重ねの BODY（12:14 に andrew main と全 155 件一致を確かめた）から、調査の三分類の「andrew だけ」15 件と「違う」8 件の計 23 件（`tools/align_23.txt`）を
  `cp -p` で bengio main へ写した。除外の最上位（checkpoints・入れ子の third_party・`__pycache__`）には触れていない。
- B-3: 揃えた後 source 142・all 155 が andrew main と一致（`$D/b/bengio_reldetr_after.json`）。三分類（andrew だけ、bengio だけ、違う）は (15,0,8) → (0,0,0)。
  `checkpoints` 12 件は前後一致。

### G2 の判定

source と all が andrew main と一致、checkpoints 前後一致。**通過。**

## Task C — 拡張と評価（G3）

- 今のビルド物を scratchpad の `ext_before/` へ写した（`$D/c/ext_before.txt` に要約値）。
- 作り直し（12:15:58〜12:17:45）: `cd third_party/Relation-DETR` で `.venv-relation-detr` の python から `from models.bricks import ms_deform_attn`
  （上流の JIT。`CUDA_VISIBLE_DEVICES=0 CUDA_HOME=/usr/local/cuda`、PATH に venv の bin）。`[2/2]` のコンパイルとリンクが走り、`EXT_LOADED True`（`$D/c/ext_build_log.txt`）。
- `build.ninja` は andrew の `build.ninja`（調査の `c/andrew_build.ninja`）と**差 0 行**（2,706 B、f72b62a0…。27 行目は `~/slocal2/m2/third_party/...` の `.cu`）。
  `.so` 1,655,680 B・1a05ed5b47e1b041…（andrew は 79b55a8ab270ed6d…。**不一致**）。`.o` 43cf653ce752d990…。
- 評価（12:18:26〜12:21:36、GPU 0）: `pd_eval.py --cfg plain`、`EGO_BODY=EGO_ROOT/EGO_ANN_DIR` は bengio main、checkpoint は絶対経路
  `~/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth`（30d199b1…）。予測は `$S/plain_val_preds_seed42.json.gz`（0936a4c2…）。
  `env_check_det.txt`: `ms_deform_attn_ext True`、`.so` は上の置き場。ログに `Loading extension module MultiScaleDeformableAttention...`・`ninja: no work to do.`・
  `[t1b] warm-start from <checkpoint>`・`"missing": []`。
- 群の AP（`scripts/stage2pilot/det_metrics.summary`、`$D/c/eval_summary.json`）: AP 0.7273450248398429（差 0.0）、標的群 0.7950748008550897（差 −4.49e-11）、
  陰性対照群 0.6726631817581498、AP50 0.851807431425236。
- 評価の後もビルド物の要約値は作り直し直後と同じ。
- 入口の選択: `pd_eval.py --cfg plain` は前の契約（w23-bengio B-2）が標的群 AP の記録値を出した入口と同じで、`scripts/stage2pilot/pd_eval.py` が自分の repo の
  `third_party/Relation-DETR` を使うため bengio main を確かめられる。
- 陰性対照（checkpoint の経路を存在しない経路にする）は回していない（GPU は評価一本の決定のため）。既知の挙動として、相対経路では読み込みを飛ばして AP 0 を返す（env-facts の装置の節、契約 §4 の申し送り）。

### G3 の判定

`build.ninja` が bengio main の `.cu` を指し、読み込めた。overall 差 0.0、標的群差 −4.49e-11（許容 1e-6）。**通過。**

## Task D — Stage 2 の材料

- 置き先 17 件は開始時すべて無い（`test -e`）。
- 12:22:35 の一回目: 8 件（案 A の信号）は bengio の `copied/` の写しから `cp -p`。andrew から読む 9 件の 1 件目で、andrew 側の `~` が単一引用符で展開されず `cat` が失敗し、
  さらに ssh が while の標準入力を読んで繰り返しが止まった。0 バイトのファイル 1 件（本契約が作ったもの）が残った。`rm` が対話の確認の別名で止まったので `/bin/rm -f` で消した。
- 12:25:07〜12:27:18 の二回目: `cat "$HOME/<経路>"` を `< /dev/null` で送り、9 件 13,497,919,828 B を受け取った（`andrew_cmds.log` 4〜12 行）。
- 照合（`$D/d/stage2_17_check.tsv`）: **17/17 がバイト数と sha256 で andrew と一致。** 存在しない経路 `.../signals/no_such_file.npz` は「無い」。

## Task E — 片付け

調べた条件（12:3x、読むだけ）:

| 項目 | 実測 |
|---|---|
| m2-four | 追跡下の変更 0、未追跡 1（`.venv` の記号リンク 29 B）、無視された未追跡 441（m2 本体に無いもの: 実験の出力 74 件 314,363,184 B、wandb のオフライン run 23 本、configs と scripts 6 件）。遠隔か phase0 に無い commit 0。cwd のプロセス 0 |
| m2-s2fix-bengio | 追跡下 0、未追跡 0、無視された未追跡 14（m2 本体に無い predictions 6 件 50,824,611 B）。遠隔か phase0 に無い commit 0。プロセス 0 |
| wt_phase0 | 追跡下 0、未追跡 3（`tasks/T-2026-10-07-drop-projection-check-in-contracts/` の SPEC.md・audit.md は phase0 と同じ中身、spec.yaml は違う中身 4,119 B）。commit 0。プロセス 0 |
| 分岐 | E1・E2 の分岐は上流あり・未到達 0。`chore/evidence-map-a-place-start`（39dd92d6）は上流なし・未到達 0・phase0 の祖先 |
| 重ねの BODY | `build.ninja` の参照 0、記号リンクの参照 0、cron 0。**版管理下の台本 4 本が経路を既定値に持つ**（`scripts/grasppilot/d_aggregate.py:27`、`d_extra_aggregate.py:129`、`run_d_arm.sh:15`、`scripts/w23/run_pd_w23_bengio.sh:24`） |
| 除外の行 | 外すと現れるのは 23 行目 `experiments/phase1/stage2pilot_*/` の 192 件 873,052,232 B だけ（`$D/e/e6_unignored_if_removed.txt`、`git check-ignore -v --no-index`）。他の 4 行は 0 件 |
| `/tmp` | 調査の 514 件のうち道具の実行時の置き場を除く 39 件を `tasks/`・`docs/` の記録で `grep -F`（`$D/e/e10_candidates.tsv`）。作った契約が 1 つに特定できたもの 22 件（`$D/e/e10_remove.tsv`）。fd と cwd のプロセス 0 |

利用者の決定（12:3x〜12:4x UTC）: E1・E2 は「両方残す」、E3 は「残す」、E6 は「よくわかんないから残しておいて」（5 行とも残す。よって E7 も残す）。

片付け（12:50:32）: 前の記録 `$D/e/removal_before.txt`（30 行。経路・大きさ・sha256）。`git branch -D chore/evidence-map-a-place-start`（was 39dd92d6）、
`__pycache__` 4 件、`.venv-relation-detr/pyvenv.cfg.before_s2fix`、`/tmp/pyvenv.cfg.bak`、`/tmp` の 22 件（`/bin/rm`）。
後の記録 `$D/e/removal_after.txt`: 片付けたファイル 28 件はすべて `test -e` と `find`、分岐 1 本は `rev-parse` と `for-each-ref` の二通りで無い。残した 6 項目は在る。worktree 4 行、除外の行 5、分岐 2。

## Task F — 検証

- 試験（`$D/f/pytest.txt`）: 11 failed・974 passed・5 skipped・0 error。名前 11 件（`$D/f/fail_names.txt`）。開始時との差は `tests/test_stage1_dtower_convergence.py` の収集の失敗が消えた 1 件だけ
  （`util/convergence.py` が Task B で入った）。passed の +9 はこの試験ファイルの分。対照: 終了時の集合に名前を 1 つ足すと差に出る。
- 前後比較（`$D/end/`）: data の stat の木・`.venv`・入れ子の third_party は一致。`checkpoints` 12 件一致。仮想環境の列は二つとも一致。
  データの項目表の差は Task D で置いた 17 件だけ（B1・画像・ディレクトリは一致）。`.venv-relation-detr` の stat の木は 20,981 → 20,980（E9 の控え 1 件）。
  `stage2pilot_store` は Task D と評価の新しい置き場を除くと一致、全体は 1,152 → 1,170 ファイル（17 件と予測 1 件）。`~/slocal2` 直下の大きさの差は `m2`（本契約の出力など）と `stage2pilot_store` だけ。
  対照: 同じ取り方で bengio main の Relation-DETR は 89dc93b4… → 20f15c06… と違う値。同期で届いたものによる差は無かった。
- 同期: 本契約の出力（`$D`）を `.stignore` の近似の照合（前の契約の `leftovers.py`）にかけ、同期の対象に当たるもの 0 件（対照 `experiments/x/foo.py` は当たる）。
  andrew（12:52:33）: `experiments/analysis/bengio_align_andrew` は `ls` と `find` の二通りで無い。既知の `experiments/analysis/bengio_andrew_env_survey` は在る。HEAD a78e2f3c・未追跡 41 は調査と同じ。
- andrew に送った命令 13 行: 読み取り（`sha256sum`・`stat`・`cat`・`ls`・`find`・`git`）と標準入力で渡した python（`-B -I`）だけ。
  `2>&1`・`2>/dev/null` を除いて `>`・`mv`・`rm`・`cp`・`tee`・`touch`・`mkdir`・`uv`・`pip`・`pytest` を grep すると 0 行。
- `make forbidden-check TASK=T-2026-11-02-bengio-align-andrew` → pass、changed 46、violations 0、permitted 39。

## 変更範囲

- 版管理: `tasks/T-2026-11-02-bengio-align-andrew/`、`experiments/analysis/bengio_align_andrew/`、`tasks/inbox.d/T-2026-11-02-bengio-align-andrew.md`
- 版管理の外（契約が求めた変更）: `third_party/Relation-DETR` の 23 件と `__pycache__` 4 件の削除、`~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/` の作り直し、
  `~/slocal2/stage2pilot_store/` の 17 件の追加と `T-2026-11-02-bengio-align-andrew/`（予測 1 件）の追加、`.venv-relation-detr/pyvenv.cfg.before_s2fix` の削除、
  手元の分岐 1 本の削除、`/tmp` の 23 件の削除
- scratchpad: 戻せることの確かめ（`restore/`）、作り直す前のビルド物（`ext_before/`）、データの項目表の生の出力

## 送出

- PR #284（base phase0、head feat/bengio-align-andrew、isDraft false、OPEN）。
- `make task-report`: 終了コード 0。台帳の応答 `verdict pass`、`n_issuer_defects 2`、`report_sha256 0be336712da02fca…`、`report_bytes 6608`、`replaced_blocks 0`。
