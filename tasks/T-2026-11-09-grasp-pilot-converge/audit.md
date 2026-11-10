# audit — T-2026-11-09-grasp-pilot-converge

ホスト bengio、分岐 `feat/grasp-pilot-converge`。時刻はホストの UTC を JST（+9 時間）に直して書く。
置き場: `$S = /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-pilot-converge`、`$A = experiments/analysis/grasp_pilot_converge`、
前の予備の保存先 `$P = /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot`（読むだけ）。
本体の .venv、`PYTHONDONTWRITEBYTECODE=1`。W&B は手元だけ（`WANDB_MODE=offline`、仮の鍵。資格情報は読み込まない）。

## 0. 始める（2026-11-09 12:3x JST）

- 分類「通す」。`make task-start` → `[task-start] .sync-pause を作成`、`[task-start] 完了。`。分岐は起点 origin/phase0 129e79b0 から作られた
- `make task-validate`: OK。`make task-preflight`: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL（SKIP: P2・P3 は plan.env.preflight に記載なし、P4・P5・P13・P14 は analysis で対象外、P12 は参照なし）
- **Task A-1 の停止**: 起点 129e79b0 に PR 307 の内容が無かった（PR 307 は OPEN、`git show origin/phase0:scripts/stage2pilot/dp_model.py | grep -c "transwin\|roitoken"` → 0）。
  SPEC §0 は「PR 307、統合済み」とするが事実と違った。停止して利用者に諮った（選択肢 1: 統合の後に早送り、2: 中止、3: PR 307 の分岐を起点）
- 利用者「mergeした」: PR 307 は MERGED（2026-11-09 12:43:11 JST、merge commit 26722ffd）。分岐は自分の commit を持たない（`git log origin/phase0..HEAD` 0 件）ので、
  選択肢 1 のとおり `git merge --ff-only origin/phase0` で早送りした → HEAD = origin/phase0 = 26722ffd。未追跡は取り込んだ契約のフォルダだけ

## 1. 解決された参照

- `contract.inject_verbatim` の 6 節（prohibitions・issuer_cautions・env_p0・folds・split・crossfit）は `context/conventions.md` の原文を適用した。
  `git log -1 -- context/conventions.md` = 2d946b07（契約の conventions_rev と一致）。denominator・frozen_source・sigma_policy の参照は無い

## Task A — 開始状態（G1。`$S/start/`）

### A-1 分岐・起点・PR 307（`a1_branch.txt`、2026-11-09 12:44:49 JST）

    $ git branch --show-current → feat/grasp-pilot-converge
    $ git merge-base HEAD origin/phase0; git rev-parse origin/phase0 HEAD → 26722ffd26df8247a85dd6f6bc368226a1b65acd（3 つとも同じ）
    $ git log --oneline -1 --grep "Merge pull request #307" origin/phase0 → 26722ffd Merge pull request #307 …
    $ git show origin/phase0:scripts/stage2pilot/dp_model.py | grep -c "class RoiTokens\|class TransWindow" → 2
    前の予備の RESULT.md・REPORT.md が起点に在る。experiments/phase1/grasprt_* 131 件
    $ git status --porcelain --untracked-files=all → 本契約の digests.py と取り込んだ契約（SPEC.md・spec.yaml）だけ

### A-2 GPU・記憶領域・仮想環境・規約と runindex（`a3_gpu_df_venv.txt`）

    GPU 0・1: 42・40 MiB、0 %、220 W。compute の一覧 0 件。存在しない GPU 7 → No devices were found（rc 6）
    proc_enum: /usr/bin/zsh 9 件、存在しない経路 0 件
    df /home/ubuntu/slocal2: Available 1,078,491,328,512 B（使用 86%）
    .venv 108 行 9c7be5c99d6b768a…、.venv-relation-detr 72 行 a74c9c787e79f014…（前の契約と一致）
    git log -1 -- context/conventions.md → 2d946b07（一致）。git log -1 -- runindex/ → b524173e、件数 2,647/1,327/1,977（meta.created_from と一致。差し替えなし）

- 全体量 42・40 MiB − 一覧の和 0 = 42・40 MiB（常駐分）。**本契約以外の使用なし**

### A-3 試験（`a4_pytest_start.txt`・`a4_fail_names.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped（失敗の名前は前の契約の開始時の 11 件と diff 0 行）

### A-4 禁止の場所の開始時の要約値（`$A/tools/digests.py` → `digests_start.json`、rc 0）

前の予備の digests.py の写しに、前の予備の集計・保存先と `experiments/phase1/grasprt_*`（glob で 131 根）を足した。計 157 根。
**`scripts` の根は dp_train.py を変える前に取った**（aaee4f90…、419 件）。

| 根 | ファイル | 大きさ B | sha256 の先頭 |
|---|---:|---:|---|
| third_party | 268 | 4,388,156,080 | ebfc6fe08c6f53ba |
| 重ねの BODY | 243 | 3,097,796 | 667933c84fdbaec3 |
| scripts | 419 | 4,033,684 | aaee4f9033aeae0c |
| configs | 104 | 153,073 | 8b6360005bf11707 |
| data/raw・external・annotations・processed・splits | 235,773・38・111・246・5 | — | 0048147d・37acfc82・3d1e52b1・45d582f1・a757e013 |
| tasks（本契約を除く） | 1,895 | 114,701,529 | 050321322ec374c4 |
| 前の予備の集計 experiments/analysis/grasp_roitoken_transition_pilot | 17 | 179,605 | 268f80f3f4f80024 |
| 前の予備の保存先 $P | 1,171 | 162,679,055,392 | 22231e043fbac14d |
| experiments/phase1/grasprt_*（131 根） | — | — | `digests_start.json` |
| その他（四本目・w23・survey・stage2_pilot_folda・G・P の run、前々の保存先 5 つ） | — | — | 前の契約と同じ値 |

- 重み: P_ft 79c2c478…、P_head 0d76d446…、P_cache c402e214…、G_all 5ea2cbf4…、G_H1 5cfa055c…、G_H2 efdefccd…

**G1: pass**（分岐 feat/、起点 origin/phase0 = 26722ffd に PR 307 の内容、本契約以外の GPU 使用なし、要約値を記録）

## Task B — 材料・口・殺し実験・恒等性（G2）

### B-1 材料の照合と塔単独（`$A/tools/b1_inputs.py`、`$S/b/b1.json`）

- 前の予備の b12_inputs.py の写しに、目録の A_g（案 A の pred_noCF・shuffle × train/val）と、前の予備の保存先の材料（空間特徴 4、トークン 16、
  枠 4、正解の地図 2、窓の列 22）の照合を足した。記録の値は前の予備の保存先の json（b3_record・b5_record・b4_record・b4_gtcheck・b6_record）
- **71/71 一致**（目録の B_m 16・A_g 4、前の予備の材料 48、P の重みとキャッシュ 3）。対照: 見取りの json を 1 ビット反転した写しで不一致
- 塔単独の val: J 0.7762185528074379・acc 0.8712871287128713、記録との差 0.0・0.0。対照: 別 seed 123 の塔の記録とは許容差 1e-6 を超える

### B-2 収束規則（`scripts/stage2pilot/dp_train.py`、`$A/tools/b2_rule_check.py`、`$S/b/b2_rule.json`）

- `dp_train.py` に `--converge`（`ConvergeRule`、`CONVERGE = {patience 8, lr_factor 0.1, max_epochs 120, min_delta 1e-4}`）を**足す形**で書いた。
  渡さなければ従来の経路のまま。結果と checkpoint は val の Jaccard が最良の epoch。epoch ごとに学習率・改善の印・出力射影の重みの最大の絶対値と L2・
  TW の相対時刻の埋め込みの標準偏差を history に、学習前・最良・最終のノルムを metrics に書く。W2・W3 でも `--fixed-epochs` の代わりに使える
- 人工の記録（学習と同じ `ConvergeRule` を通す）:

| ケース | 落とした epoch | 止めた epoch | 期待どおり |
|---|---|---|---|
| 1 一定 | 9 | 17 | はい |
| 2 +1e-3 ずつ上がる | — | —（上限 120 まで） | はい |
| 3 最良から 1e-4 未満の揺れ（0.7・0.70005 の交互） | 9 | 17 | はい |
| 3b +5e-5 ずつ上がる（累積で 1e-4 を超えるたびに改善） | — | —（120） | はい |
| 4 落とした後に改善 | 9 | 20 | はい |
| 陰性対照: patience を 9 にした規則（ケース 1） | 10 | 19 | 1 と違う |

- ケース 3 は最初「+5e-5 ずつ」で期待 9・17 と書いたが、規則どおりなら累積で 1e-4 を超えるたびに改善と数えるので期待の誤り（3b として残した）。規則は変えていない

### B-3 殺し実験の処方の直し（`$A/tools/b3_kill.py`・`b3_diag.py`、`$S/b/b3_kill.json`・`b3_kill_round2.json`・`b3_diag.json`）

- 前の予備の `c_kill.py` を読み込み、線形の層の当て方だけを差し替えた（行・特徴・殺す条件・事象の率は前の予備のまま、材料は $P を読むだけ）。
  候補は L2 つきの多項ロジスティック回帰（sklearn、lbfgs、class_weight balanced、標準化）

| 候補 | C | 陽性対照（P ＋ 正解の工程の one-hot）の val J / acc | 0.9 に届く |
|---|---|---|---|
| 1 | 1.0 | 0.6372 / 0.8277 | いいえ |
| 2 | 0.1 | 0.6834 / 0.8343 | いいえ |
| 3（利用者の決定で追加） | 1e-3 | 0.6568 / 0.8554 | いいえ |
| 4（同） | 1e-4 | 0.6434 / 0.8469 | いいえ |

- 診断（`b3_diag.py`、候補 1・2）: one-hot だけ（9 次元）の層は val J 1.0・acc 1.0（評価の経路は正しい）。P ＋ one-hot は**train の正解率 1.0**、
  重みの L2 のうち one-hot の 9 列の割合は 22.5%・25.9%。P は train で fine-tune した塔で、train の特徴だけで train が分け切れるため、足した列を主に使わない
- 候補 1・2 が届かず escalate の条件に当たり、停止して諮った。利用者「1のあと、学習にすすんで」: 候補 3・4 を試し（届かず）、
  殺し実験は「この特徴の上の線形の層では感度が出ない」と記録して学習へ進んだ。届かなかったので案 3・案 5 の殺し実験は測り直していない

### B-4 既定の挙動・回し直し・恒等性・規則の試走（`$A/tools/run_b4_check.sh`・`compare_default.py`・`compare_repeat.py`、`$S/b4check/`、GPU 0）

- 起点の版 `git show 26722ffd:scripts/stage2pilot/dp_train.py` → `$S/check/old/stage2pilot/`（dp_model.py は変えていない: cmp で一致）
- 29 行すべて rc=0
- 既定の挙動: GA 旗なし（空・予測-noCF・入れ替え）と D1-L1 の identity の差 0 件、GA 予測-noCF の 1 epoch の試走の全記録一致（all_equal true）
- `--fixed-epochs` の経路: 前の予備の `grasprt_rt_002_RT-layer4-roi_geo-K16_pred_CF_ep4_seed42` と `grasprt_tw_031_TW-W2-b-L8-K64_pred_CF_ep4_seed42` を、
  識別子と接頭辞だけ変えて本契約の版で回し直した（`grasprc_chk_rt_001`・`grasprc_chk_tw_001`）。metrics・history・クラス別・確率・界面と受け取り手の重みが一致。
  config の違いは task_id と unofficial の 2 欄だけ。1e-9 ずらした写しを検出（all_equal true）
- 恒等性: RT 8 設定 × 7 腕、TW 12 件 × 8 腕、GA 3 腕（新旧）、D1-L1 の 162 件で学習前のロジットと塔単独の差の最大 0.0。
  出力射影を N(0, 0.05²) にすると GA の空以外は 0.060 以上変わる。GA の空は入力が零で 0.0（記録のみ）
- 規則の試走（`grasprc_chk_conv_001_GA-noflag_empty_conv_seed42`、腕に数えない）: 学習率 epoch 8 まで [5e-4]、epoch 9 の後 [5e-5]（optimizer の群で落ちた）、
  epoch 17 で打ち切り、最良は epoch 1（入力が零で出力が変わらない）。出力射影のノルムは学習前・最良・最終とも 0.0

**G2: 殺し実験の陽性対照だけ届かない（4 候補）。** 他（材料 71/71、塔の再現、規則の対照、既定の挙動、恒等性）は満たした。利用者の決定で学習へ進んだ

## Task C — 学習（G3。`$A/tools/run_c.sh`、`$S/c/`）

    $ for w in 0..7: bash $A/tools/run_c.sh $((w % 2)) $w 8 &     （GPU 0・1 に 4 本ずつ）
    開始 2026-11-09 13:28:23 JST、終了 13:51:11 JST。127 本すべて rc=0（DP_RUN_COMPLETE）。止まった run 0 件（aborted/ は使っていない）

- run: `experiments/phase1/grasprc_rt_*`（56）・`grasprc_tw_*`（68）・`grasprc_ga_*`（3）、名前は `…_conv_seed42`。界面の重みは `$S/dp_ckpt/`
- 起動の直前の GPU 0 の全体量 309 MiB と一覧 0 件の差は、起動中の本契約の 1 本（一覧に出る前）で、落ち着いた後は全体量 − 一覧の和 = 63・61 MiB（常駐分と同じ程度）。本契約以外の使用なし
- 総 epoch 17〜54、上限 120 に届いた run 0。最良の epoch: W1（RT・TW W1・GA の 87 本）の中央 2、TW W2 の中央 4、TW W3 の中央 22
- **G3: 当たった（ask）**。checkpoint の出力射影の重みの最大の絶対値が前の予備の最大 0.021 を超えたのは 48/127 本（RT 10/56、TW W1 12/28、W2 6/20、W3 20/20、GA 0/3）。
  超えなかった 79 本の理由: 学ぶほど val の J が下がり（最終 − 最良の中央 −0.0203、最小 −0.0916）、規則が早い epoch を選ぶ。GA の空は入力が零で 0.0。
  最終の epoch の同じ値は RT 0.030〜0.094、TW W1 0.043〜0.147 で、学習そのものは進んでいる
- 利用者の決定（2026-11-09）: 「このまま報告へ進む」。規則の値と checkpoint の選び方は SPEC §6-11 により変えていない

## Task D — 集計・検証・報告

### D-1 集計（`$A/tools/d_aggregate.py`、`$S/d/summary.json`）と REPORT（`$A/tools/make_report.py` → `$A/REPORT.md`）

- 本契約の 127 本と前の処方の 127 本（案 3・5 は前の予備 `grasprt_*`、案 A は四本目 `grasparms_dp_*`）を同じ規則で読み、同じ差を並べた。
  前の処方の run のノルムはその run の界面の重み（前の予備の保存先と四本目の保存先の checkpoint）から読んだ（読むだけ）
- f: 127/127、全本が収束規則（result_selection best_val_jaccard）、存在しない run の名前 2 つで 0・0 件
- g: 差 708 個を確率から測り直してずれの最大 0.0、1e-6 ずらした写しを検出。指標がちょうど同じになった差: 本契約 6/118、前の処方 4/118
- h: 通した動画 01・02・03・06・08・09・10・11・12・13・14・15、test との共通 0 件、04 を混ぜると [04]
- W1 の受け取り手は不変、W2・W3 は学ぶ範囲が変わり範囲の外は不変
- 途中の状態で試したとき、走っている途中の run（記録が無い）で止まったので、記録の無い run を数えないよう直した（集計は全本の終了の後に回した）

### D-2 無変更・試験・禁止領域（`$S/end/`）

    $ pytest（A-3 と同じ命令） → 11 failed, 980 passed, 5 skipped（失敗の名前は開始時と diff 0 行）
    $ make forbidden-check TASK=T-2026-11-09-grasp-pilot-converge → status pass、changed 1,072、permitted 1,068、違反 0 件
    $ python $A/tools/digests.py --out $S/end/digests_end.json --files $S/end/digests_end_files.json   → rc=0
    157 根のうち 156 が開始時と一致。違う 1 根は scripts（stage2pilot/dp_train.py の 1 件だけ。本契約の --converge）。重み 6 件・仮想環境 2 つ一致。
    前の予備の保存先（163 GB）・前の予備の run 131 根・四本目の置き場も一致

- `tasks/inbox.d/T-2026-11-09-grasp-pilot-converge.md` は終わりの要約値を取り始めた後に書いたので、tasks の根の比べには入っていない（本契約の判断の受け皿の 1 件）
