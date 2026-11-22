# audit — T-2026-11-22-dtower-class-error-breakdown

記号: **$O** = `experiments/analysis/dtower_class_error_breakdown`（本契約の出力と道具。allow_write の接頭辞）、
**$S** = `/home/ubuntu/slocal2/stage2pilot_store`（版管理と同期の外。読むだけ）。時刻は JST。ホスト andrew、repo `~/slocal2/m2`。
道具はすべて本体の `.venv`（Python 3.11、pycocotools 2.0.11、numpy 1.26.4）で動かした。GPU・学習・推論は使っていない。

## 0. 始める（2026-11-22 12:4x JST）

    $ git branch --show-current ...（skill「0. 始める」の読み取りの命令）
    feat/grasp-hand-irn-hice-htt-pilot / 作業ツリーの汚れ 0 / feat/dtower-class-error-breakdown は手元にも遠隔にも無い /
    tasks/T-2026-11-22-dtower-class-error-breakdown の履歴なし / tasks/<id>/ なし / .sync-pause なし
    $ git fetch origin && python3 scripts/task_start_classify.py
    [task-start] 分類（比較先 origin/phase0 6953d6e4）  追跡下の変更 0 件 … [task-start] 分類: 通す
    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-11-22-dtower-class-error-breakdown
    [task-start] 分岐を作成: feat/dtower-class-error-breakdown（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-11-22-dtower-class-error-breakdown END=complete）
    OK   T-2026-11-22-dtower-class-error-breakdown   1 task(s), 0 failed
    [task-start] 完了。分岐 feat/dtower-class-error-breakdown で契約 T-2026-11-22-dtower-class-error-breakdown の作業を開始できます

目印は本契約の task-start が**作成**した。同じ台に配布された別の契約 T-2026-11-22-conv-epoch-history-extract の処理は
走っていなかった（`ps` に python の処理なし、`nvidia-smi --query-compute-apps` は 0 件）。同時には走らせていない。

## A. 開始状態と材料（Task A、G1）

### A-1 検証とプリフライト

    $ make task-validate TASK=T-2026-11-22-dtower-class-error-breakdown   → OK、0 failed、rc 0（WARN なし）
    $ source .venv/bin/activate && make task-preflight TASK=T-2026-11-22-dtower-class-error-breakdown   → rc 0
    P1 venv_active PASS / P6 decisions_answered PASS（decisions_required は空）/ P7 destination_writable PASS /
    P8 contract_valid PASS / P9 spec_lint PASS（規則 9 件、該当なし）/ P10 preflight_names_known PASS
    SKIP: P2 cuda_ext_loaded・P3 deterministic_flags・P11 gpu_free（plan.env.preflight に記載なし）、
          P4 prereg_committed・P5 frozen_source_hash・P13 symmetry_table_complete・P14 proposal_card_checked（kind=analysis で対象外）、
          P12 refs_resolved（解決前提の参照なし）
    RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL

### A-2 参照の解決

- `meta.created_from` を起点で測った（`git log -1 --format=%h -- runindex/`、件数は `csv.DictReader`）: runindex 036d6a60、
  index 2668・experiments 1347・verdicts 2067。契約の値と同じなので差し替えていない
- `contract.conventions_rev`: `git log -1 --format=%h -- context/conventions.md` = 2d946b07（契約と同じ）
- `inputs.data.split_files`（`data/splits/ego_val.txt`）は**参照しなかった**（SPEC §0。使った分割は conventions#folds の各 Fold の val と train。
  Fold の表は正本 `docs/stage0/A1_fold_table.md` と conventions#folds の表の両方から読んで一致を確かめた。C-3）
- `inputs.denominator`・`inputs.frozen_source`・`inputs.sigma_policy` は契約に無い
- `contract.inject_verbatim` の 7 節の原文（`context/conventions.md`、2d946b07）は本書の末尾「付録 規約の原文」に置いた

### A-3 開始状態（`$O/start/a_start.json`、`tools/a_start.py`）

    分岐 feat/dtower-class-error-breakdown（feat/ で始まる）、HEAD = origin/phase0 = merge-base = 6953d6e4
    未追跡 8 件（すべて本契約: tasks/<id>/SPEC.md・spec.yaml、$O/start の 4 件、$O/tools の 2 件）
    前提のファイル 23/23 が在る（SPEC §1.1・§3 が名指すもの。test のファイルは名指していない）。$S の塔 2 の予測と塔 1 の runs/ も在る
    仮想環境: .venv → pycocotools 2.0.11・numpy 1.26.4 / .venv-relation-detr → pycocotools 2.0.11・numpy 1.26.4
              /nonexistent/zzz_no_such_venv → python 無し（pycocotools null。対照 a）
    使った仮想環境: /home/ubuntu/slocal2/m2/.venv（新しい依存は入れていない）

試験（`CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors`、
`$O/start/pytest_start.txt`）: 6 failed, 985 passed, 5 skipped（37.59 s）。失敗の名前（`$O/start/pytest_fail_names_start.txt`）:
`test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`、`test_fetch_task.py::test_rejects_unknown_file_name`、
`test_research_logger.py` の `test_log_run_idempotent`・`test_run_logging_invokes_log_run_on_finally`・
`test_run_logging_no_double_post_on_normal_exit`・`test_run_logging_swallows_exception_in_user_block`（前回の契約の開始時と同じ名前）。

### A-4 材料の目録（完了判定 b）

| 対象 | 経路 | sha256 | バイト | 画像（予測がある / val の注釈） | 予測 | run の名前と frozen_towers.json |
|---|---|---|---|---|---|---|
| 塔 1 Fold A | `$S/T-2026-11-07-dtower-rerun/runs/dtowerrerun_p12_dcoco_foldA_seed42/eval_val.detections.json.gz` | 5311de9753f187cf516a7477c6e905df92f07c121ea2b3086e22297f13173816 | 13,892,154 | 1515 / 1515 | 454,500 | 一致 |
| 塔 1 Fold B | 同 `..._foldB_seed42/eval_val.detections.json.gz` | 49dd0b6b2fb1b845457135b4cc2dd541b8a473f05f39a35827a97438724198e7 | 15,149,071 | 1861 / 1861 | 558,300 | 一致 |
| 塔 1 Fold C | 同 `..._foldC_seed42/...` | db8a4c966dc9704dd7960a5221e5e1b2f71b07cc420d775e4af61de4a04562f7 | 17,117,478 | 1988 / 1988 | 596,400 | 一致 |
| 塔 1 Fold D | 同 `..._foldD_seed42/...` | 8689a1c1eea6bbb1d5fea977a2ecd5db6f80f7efaa7b4e3dc2369271201c0dab | 23,159,750 | 2554 / 2554 | 766,200 | 一致 |
| 塔 1 Fold E | 同 `..._foldE_seed42/...` | 110cbbe1f79637cbe815877cc5a2dfef195850ecf117d5d16d5f34a3eabe6dc5 | 14,572,265 | 2131 / 2131 | 639,300 | 一致 |
| 塔 2 Fold A | `$S/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/identity/plain_val_preds.json.gz` | 323805234ad09bb35c6fd4518d9dc83a2eaf059c2abaf0d885dc53f31404ba3c | 26,929,542 | 1515 / 1515 | 454,500 | （対象外） |

- 様式: 塔 1 は `{"images", "categories", "detections"}`（eval_dump.py の出力）。画像の id と file_name の対応は各 Fold の
  `data/annotations/egosurgery_tool_folds/<Fold>/instances_val.json` と完全に一致、カテゴリも一致。塔 2 は pd_eval.py の `preds["results"]`
  （loadRes を経た `segmentation`・`area`・`id` が付いた結果の並び）で、画像の id はすべて Fold A の val の注釈の中。
  どちらも足切りなし、画像あたり 300 件、score と枠はすべて有限
- 塔 1 の 5 本は run のフォルダの名前が `frozen_towers.json` の `run` と、checkpoint の置き場が予測の置き場と一致。欠けた材料は無い（UNKNOWN 0 件）
- 対照: 塔 1 Fold A の予測の写しの末尾から 100 バイト目を反転 → sha256 の照合が食い違う（False）、本物は一致（True）。
  存在しない run の名前 `dtowerrerun_p12_dcoco_foldZ_seed42` → frozen_towers.json で 0 件・runs/ で 0 件（本物の名前は 1 件）。写しは scratchpad に置いて消した

### A-5 G1（`$O/start/g1_reads.json`）

    $ .venv/bin/python $O/tools/check_reads.py
    {"rows": 13, "files": 12, "test_files": [], "by_kind": {"material": 11, "record": 1}}
    $ .venv/bin/python $O/tools/check_reads.py --inject .../egosurgery_tool_folds/A/instances_test.json   （対照）
    "test_files": [".../egosurgery_tool_folds/A/instances_test.json"]

G1 **pass**: 凍結した塔の Fold A の val の予測の保存が在り、読んだ材料の一覧に test の予測と注釈が 0 件。

## B. 再現（Task B、G2。`$O/b/b_repro.json`・`b_repro.log`、`tools/b_repro.py`）

保存済みの予測の全件と各 Fold の val の注釈から、記録と同じ COCOeval（area all、maxDets 100、クラス別 AP は precision[:, :, k, 0, -1] の
p > -1 の平均、id 0 の注釈もそのまま）で計算し直した。比べた記録: 塔 1 は `frozen_towers.json` の val_mAP・val_AP_target・val_AP_negative と
run の `eval_val.json` の AP・AP50・AP75・クラス別 AP。塔 2 は SPEC §1.1 の 7 桁の値（0.7273450・0.7950748・0.6726632）、
`per_class_ap.json`、`experiments/analysis/stage2_pilot_fix/identity/pd_plain.json` の AP・AP50。

    T1 A equal_4dp True max_abs_diff 0.0 AP 0.7196251 sig 0.8044362 neg 0.6781757 missing ['Retractor']
    T1 B equal_4dp True max_abs_diff 0.0 AP 0.4755093 sig 0.4900046 neg 0.625058 missing ['Electric Cautery', 'Hook']
    T1 C equal_4dp True max_abs_diff 0.0 AP 0.4427707 sig 0.5353497 neg 0.5068293 missing []
    T1 D equal_4dp True max_abs_diff 0.0 AP 0.5062879 sig 0.7086117 neg 0.5581371 missing []
    T1 E equal_4dp True max_abs_diff 0.0 AP 0.5226365 sig 0.6778409 neg 0.4792723 missing ['Electric Cautery', 'Mouth Gag']
    T2 A equal_4dp True max_abs_diff 2.4839842849289084e-08 AP 0.727345 sig 0.7950748 neg 0.6726632 missing ['Retractor']
    G2_pass True max_abs_diff_over_all 2.4839842849289084e-08
    対照（塔 1 Fold A、画像 id 0 の 300 件の score の並びを逆にした写し）: all_equal_4dp False、max_abs_diff 0.0092、
      食い違った行 AP・AP50・AP75・signature・negative・Gauze・Skewer、AP の差 0.000295

G2 **pass**（6 対象とも overall・群・クラス別のすべてが小数第 4 位で一致。塔 2 の差 2.5e-8 は記録が 7 桁の表示であることによる）。
Fold E の negative control は Mouth Gag が val に無いので 3 クラスの平均（frozen_towers.json の値と同じ扱い）。

## C. 分解と表（Task C）

### C-1 GT の側と予測の側の分解（`$O/c/decomp_*.json`・`c_decomp.log`、`tools/c_decomp.py`。完了判定 d・e）

score 0.05 以上の予測だけ。IoU は pycocotools の bbox の IoU。全 6 対象で、読み 1・読み 2 の四区分の和がクラスごとの GT の数と一致、
取り違えの表の行の和が「取り違え」の件数と一致、予測の側の六区分の和が足切りを通った予測の数と一致（`all_sums_ok` True × 6）。

    T1_A n_gt 4707 n_pred 26246  r1 正解 4289・取り違え 239・位置 134・見落とし 45 / r2 正解 4473・取り違え 55
    T1_B n_gt 4922 n_pred 44320  r1 4110・612・164・36 / r2 4560・162
    T1_C n_gt 7516 n_pred 53334  r1 5697・926・359・534 / r2 6443・180
    T1_D n_gt 5751 n_pred 57233  r1 4901・670・133・47 / r2 5358・213
    T1_E n_gt 8750 n_pred 137080 r1 5290・2006・613・841 / r2 7071・225
    T2_A n_gt 4707 n_pred 26830  r1 4272・261・134・40 / r2 4492・41

対照（`$O/c/decomp_controls.json`。作り物: 画像 3 枚・GT 5 個）: GT と同じ枠・同じクラスの予測だけ → 読み 1・読み 2 とも正解 5、当たり 5。
クラスを一つ変えた → 取り違え 1（両方の読み）、予測の側の取り違え 1。枠を 60 px ずらした（IoU ≈ 0.14）→ 位置のずれ 1。予測を一つ除いた → 見落とし 1。
同じ枠の予測を二つ → 重複 1。GT から離れた予測を足した → 背景 1。pass True。

読み 1 の決め方: IoU が同じ予測が複数あれば score 最大、それも同じなら保存の並びで先（score も同じだった GT は全対象で 0 件）。

### C-2 直した場合の上限の目安（`$O/c/fix_*.json`・`c_fix_*.log`、`tools/c_fix.py`。完了判定 g）

- 直す前の値は Task B の `b/eval_<塔>_<Fold>.json` と完全に一致（`before_equals_taskB` True × 6）
- 予測ごとの「IoU 最大の GT」が同値で二つ以上あった予測: 塔 1 Fold D で 11 件、ほかは 0 件（注釈の並びで先の GT を取った）
- 対照（`$O/c/fix_controls.json`。作り物: 画像 4 枚・GT 7 個・工程 2 つ）: GT をそのまま予測 → 五つとも平均 AP の差 0.0。
  クラスだけを回した → (b) +1.0、ほか 0.0。在否の違う画像に予測を足した → (d) +0.25・(c) 0.0（(e) も +0.167。足した組の一部が工程で在り得ない組）。
  工程で在り得ない組の予測を足した → (e) +0.111。pass True

**工程の正解の出所と利用者の判断（(e)）。** 出所は `data/processed/phase_manifest`（前回の予備測定の正解の腕と同じ。
`scripts/stage2pilot/common.py` の `phase_sequences`、`phase_signals.py` の `p2f`）。このマニフェストは公式分割ごとのファイルで、
Fold B〜E では公式の test の動画 04・05・07 の工程の注釈（test.json）が train か val に要り、train.json・val.json には各 Fold の test の動画の項目も入る。
1 回目（`c_fix_run1.log`。`c_fix.log` は同じ内容）は test.json を開かず、Fold B〜E の (e) を UNKNOWN にした。
選択肢（test.json も開く／Fold A だけで (e) を出す／clip ごとの CSV を使う）を示し、利用者が「test.json も開く」を選んだ（2026-11-22、選択式）。
spec.yaml の `meta.amendments` に記録し、`task-validate` で OK を確かめてから `--allow-manifest-test` で回した（`c_fix_run2.log` は Fold B〜E、
`c_fix_final.log` は除いた組に当たる val の GT の数を足した最終の道具で 6 対象。(a)〜(d) の値は 3 回とも同じ）。

| Fold | 開いたマニフェスト | 使った動画 | 使わなかった動画（= その Fold の test） | train の注釈の画像（工程なし） | val の画像（工程あり） | 除いた組 |
|---|---|---|---|---|---|---|
| A | train・val | 01 02 03 06 08 09 10 11 12 13 14 15 | なし | 9657（0） | 1515（1515） | 70 |
| B | train・val・test | 02 04 05 06 07 08 09 10 11 12 13 15 | 01 03 14 | 9764（0） | 1861（1861） | 66 |
| C | train・val・test | 01 03 04 05 06 07 09 10 12 13 14 15 | 02 08 11 | 10834（0） | 1988（1988） | 52 |
| D | train・val・test | 01 02 03 04 05 07 08 09 10 11 12 14 | 06 13 15 | 10262（0） | 2554（2554） | 52 |
| E | train・test | 01 02 03 04 05 06 07 08 11 13 14 15 | 12 | 11182（0） | 2131（2131） | 69 |

Fold A の共起の数え上げは前回の P2F の表（`experiments/analysis/stage2_pilot_folda/signals/p2f_table.json`）と、工程のフレーム数・
共起の数・工程の並び・train のフレーム数 9657 まで一致（`$O/c/phase_source_vs_p2f.json`）。

### C-3 表（`$O/c/tables.json`・`c_tables.log`、`tools/c_tables.py`。完了判定 f・h）

- 5 Fold とも、train と val の注釈の画像の動画の集合が正本の表と conventions#folds の表に一致、test の動画との共通 0、
  クラスごとの box の数が注釈の並びの数え上げと pycocotools の索引（getAnnIds）の数え上げで一致
- 動画ごとのクラス別 AP: 塔 1 は eval_val.per_video.json と 24・23・27・26・22 値を比べて差の最大 0.0。塔 2 は pd_plain.json の動画ごとの mAP（09・10）と差 0.0
- AP50 ≥ AP は 6 対象の全クラスで成り立つ
- 対照 h: Fold A の val の注釈から一つ除いた写し → Skewer の box 103 → 102。Fold B の val の動画 02 の画像を混ぜた写し → 動画の集合 [02, 09, 10] が表と不一致
- 対照 f: 塔 1 Fold A の予測の枠を一律に x へ 8 px ずらした写し → AP75 の平均 0.7703 → 0.7395（14 クラス中 10 クラスで下がる）

### C-4 道具の整え（ruff）

`.venv/bin/ruff check $O/tools/` の指摘 6 件（変数名 `O` 2、置き換えの無い f 文字列 3、`not in` の書き方 1）を直し、0 件にした。
直した道具で直し方・報告・実測の表を回し直し、出力（fix_*.json 6 件・REPORT.md・summary.json・csv 8 件・result_tables.md）が直す前と
バイトまで同じことを `cmp` で確かめた（`c_fix_after_ruff.log`）。

## D. 集計と検査（Task D）

### D-1 報告（`tools/make_report.py` → `$O/REPORT.md`・`summary.json`・`csv/*.csv`（utf-8-sig）、`tools/result_tables.py` → `$O/d/result_tables.md`）

表は記録から道具で作った（手で写していない）。RESULT.md の「実測」の表は `d/result_tables.md` をそのまま入れた。

### D-2 test を読まない・変えていない（`$O/d/d_checks.json`、`tools/d_checks.py`。完了判定 i・j）

    読んだファイル 36 件（材料 19・記録 17。一覧は d_checks.json の reads.files_list、全行は $O/reads.jsonl）
    i: 検出の test のファイル 0 件。マニフェストの test.json を読んだ目的は Fold B・C・D・E の (e) だけ（Fold A では開いていない）
       Fold ごとの val の画像の動画と test の共通 0、工程の正解に使った動画と test の共通 0、使わなかった動画はすべてその Fold の test
       対照: 一覧の写しに instances_test.json を混ぜる → 1 件。Fold A の val の動画に 04 を混ぜる → 共通 [04]
    j: 一覧の 36 件の今の sha256 が最初に読んだときと一致（変化 0、一覧の中の食い違い 0）。$S のファイル 16 件を含む
    i_pass True、j_pass True

試験（終了時、`$O/d/pytest_end.txt`）: 6 failed, 985 passed, 5 skipped（32.32 s）。失敗の名前は開始時と同じ（`diff` 空）。

    $ source .venv/bin/activate && make forbidden-check TASK=T-2026-11-22-dtower-class-error-breakdown
    status pass、changed 65、permitted 65（すべて「契約の allow_write experiments/analysis/dtower_class_error_breakdown/ により許可」）、violations 0
    $ make forbidden-check   （対照: TASK なし）
    status fail、本契約の 65 件が「禁止領域 experiments/ の内側」として名指される

（README.md・docs/experiment_log.md・tasks/ の記録は禁止領域の外。最後の commit の前に同じ検査を回し直した結果は「送出」に置く）

## 送出

（commit・push・PR・task-report の後に追記する）

## 付録 規約の原文（contract.inject_verbatim、context/conventions.md 2d946b07）

#### conventions#prohibitions（原文）

    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

#### conventions#issuer_cautions（原文）

    ## issuer_cautions

    **起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
    実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

    | # | 注意 |
    |---|---|
    | 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
    | 2 | 一致 0 件なら別の異質な方法でも確認する |
    | 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
    | 4 | 仕組みの挙動は実装を読んでから信じる |
    | 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
    | 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
    | 7 | **丸めた表示を実数として扱わない** |
    | 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
    | 9 | 無変更は要約値で確かめる。表示属性では足りない |
    | 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
    | 11 | 測定の副作用が禁止領域へ触れないか確かめる |
    | 12 | **判断の前に、いま見ているものが最新かを確かめる** |
    | 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
    | 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

    **注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
    確かめると 3 件とも実在した。

    **注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
    （`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

    **注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
    （自分の命令行にその語が含まれるため）。

    **注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

    **シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
    一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

    **命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

#### conventions#env_p0（原文）

    ## env_p0

    学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
    activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
    数値が変わったまま完走する。

        source .venv-relation-detr/bin/activate   # 検出系
        source .venv/bin/activate                 # 解析・工程系

    拡張のロード確認をログに残すこと。

#### conventions#folds（原文）

    ## folds

    動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
    本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。

    | 折り | test（3） | val（2） |
    |---|---|---|
    | A | 04, 05, 07 | 09, 10 |
    | B | 01, 03, 14 | 02, 08 |
    | C | 02, 08, 11 | 06, 12 |
    | D | 06, 13, 15 | 04, 05 |
    | E | 09, 10, 12 | 07, 15 |

    train はその折りの test と val を除いた 10 本である。
    **折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
    各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。

    ### 追加 6 動画

    工程の注釈がある追加動画は次の 6 本である。

        17, 18, 19, 20, 21, 22

    **22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
    旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
    出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
    `tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。

    **用途は訓練のみである。どの折りの test にも val にも現れない。**
    15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。

    ### 規律

    **選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
    test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。

    出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。

    ### val と test の重なり

    各折りの val 2 本（計 10 本）は、どれもほかの折りの test に現れる。上の表から読める対応は次のとおり。

    | val の動画 | val に使う折り | test に持つ折り |
    |---|---|---|
    | 09, 10 | A | E |
    | 02, 08 | B | C |
    | 06 | C | D |
    | 12 | C | E |
    | 04, 05 | D | A |
    | 07 | E | A |
    | 15 | E | D |

    **val に一度も入らないのは 01・03・11・13・14 の 5 本**である。test としては折り B に 3 本（01・03・14）、
    C に 1 本（11）、D に 1 本（13）、A と E には 0 本。

    val で設定・処方・構造・型・止め方を選ぶ段（両塔の学び直しと Stage 2 以降）では、次の三つを守る。

    1. この重なりを prereg と報告に明記する
    2. test の値を報告するときは、val に一度も入らない 5 動画だけで集計した値を副次として添える。
       各動画の値は、その動画を test に持つ折りのモデルが出す。集計の仕方は prereg に書く
    3. 副次の値は、判定・関門・選定のどれにも使わない

    選ぶ規則（規律の小節。その折りの val で選ぶ）は変えない。

    出所: 利用者の決定 2026-10-19（契約 `T-2026-10-21-ops-taskstart-resume-folds-val` SPEC §2）、上の折りの表、
    `docs/stage1/design_val_subsets.md` 223 行。

#### conventions#split（原文）

    ## split

    論文準拠 split の動画 ID は次のとおり。

    - train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
    - val: `09`, `10`
    - test: `04`, `05`, `07`

    転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
    実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。

#### conventions#eval_recipe（原文）

    ## eval_recipe

    転記元: `src/egosurgery/utils/eval_recipe.py`。

    - `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`
    - `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`
    - `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`

    比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため `UNKNOWN（転記元未特定）`。

#### conventions#det_groups（原文）

    ## det_groups

    検出の co-primary と陰性対照の集合。研究方針 v2 §7.3（2026-06-19 に EDA から事前登録。結果を見て選んだ群ではない）。

    | 群 | クラス | 用途 |
    |---|---|---|
    | 標的群 | Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory | 検出の co-primary（標的群 AP = 5 クラスの AP の平均） |
    | 陰性対照群 | Gauze、Mouth Gag、Suction Cannula、Tweezers | Δ ≈ 0 であるべき群。動いたら交絡を疑う |

    - クラス名は検出塔の注釈と完全一致で照合する
    - ある折りの評価集合に出現しないクラスは、その折りの群 AP から除き、除いたことを明記する。0 で埋めない
    - AP rare（Skewer、Syringe）は副次指標として別に報告する

