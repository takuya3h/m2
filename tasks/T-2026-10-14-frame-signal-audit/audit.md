# 監査 — T-2026-10-14-frame-signal-audit

ホスト andrew（`/home/ubuntu/slocal2/m2`、`context/env-facts.md` の記載どおり）。実行者 Claude Code。
時刻は JST。装置は使っていない（学習も推論もしていない）。出力の全文が長いものは末尾だけを写し、
全文は `experiments/analysis/frame_signal_audit/` の JSON / CSV にある。

## 1. Task A — 開始状態（2026-10-14 20:08〜20:10）

    cd "$(git rev-parse --show-toplevel)" && git branch --show-current && git --no-pager status --porcelain --untracked-files=all \
      && git branch --list "feat/frame-signal-audit" && git --no-pager ls-remote --heads origin "refs/heads/feat/frame-signal-audit" \
      && git --no-pager log --all --oneline -1 -- "tasks/T-2026-10-14-frame-signal-audit"; ls -d "tasks/T-2026-10-14-frame-signal-audit"; cat .sync-pause

- 分岐 `feat/ubuntu24-cuda129-env`（統合済み）、作業ツリー清浄（0 行）、契約の分岐は手元にも遠隔にも無し、履歴無し、契約ディレクトリ無し、`.sync-pause` 無し → 清浄
- `source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-14-frame-signal-audit`
  → `[task-start] 分岐を作成: feat/frame-signal-audit（起点 origin/phase0）`、**`[task-start] .sync-pause を作成`**（この契約が置いた目印）、
  `OK T-2026-10-14-frame-signal-audit`、`[task-start] 完了。`
- 開始前から在る未追跡: **0 件**（task-start 後の未追跡 2 件は契約本体 `SPEC.md` / `spec.yaml`）。退避なし
- 起点: HEAD = `origin/phase0` = `57717f6cb2d1e61d15478482de2cba832f873bdb`（`git merge-base` も同じ）。起票者の起点 `8b331ac6` は本日 `#226` の統合で進んだもの。
  `conventions_rev` 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`（一致）、`runindex_commit` 実測 `63ae65da8c7d32df591f5e2ee4358286b72c726b`（一致）、
  行数 index 1961 / experiments 750 / verdicts 1506（一致）→ `meta.amendments` は不要
- 注釈の版管理下のファイル（46 件）: `git diff --stat origin/phase0 -- data/annotations/egosurgery_phase data/annotations/egosurgery_tool` 空。
  木の要約値 HEAD = origin/phase0: `egosurgery_phase` `4bc3bfffff51b2743813d4a5174f0072c420f5b2`、`egosurgery_tool` `6bedcd36488a72ec7abc820d5499fcced4e94592`。作業ツリー = HEAD
- 装置（開始 20:09:47）: `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv` → 0 行。GPU 0 / 1 とも使用 16 MiB。
  `/proc/<pid>/exe` の解決対象なし。本シェル pid 1340857
- 要約値（開始）: 工程 CSV 全体 `f1b7c70c…`、術具 JSON 3 本 `6db26c3a…`、manifest15 `fab14502…`、manifest20 `53c89cd4…`
  （`scratchpad/fsa/digests_start.txt`。命令は §7）
- 試験（開始前）: `CUDA_VISIBLE_DEVICES="" .venv/bin/python -m pytest tests/ -q -p no:cacheprovider --continue-on-collection-errors`
  → **6 failed, 793 passed, 1 error**（error は `tests/test_stage1_dtower_convergence.py` の収集。`third_party/Relation-DETR/util/convergence.py` が無い。
  `--continue-on-collection-errors` を付けないと収集で止まり全件が走らない）。失敗 6 件: `test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`、
  `test_fetch_task.py::test_rejects_unknown_file_name`、`test_research_logger.py` の 4 件
- **関門 G1: pass**

## 2. 検証とプリフライト

- `make task-validate TASK=…` → `OK T-2026-10-14-frame-signal-audit`、`1 task(s), 0 failed`
- `make task-preflight TASK=…` → `RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL`。SKIP: P2 cuda_ext_loaded・P3 deterministic_flags・P11 gpu_free（宣言なし）、
  P4・P5・P13・P14（analysis は対象外）、P12（参照なし）。P7 は `experiments/analysis/frame_signal_audit/` の作成可を確認、P9 spec_lint 9 規則該当なし
- 参照の解決: `inject_verbatim` の 5 アンカー（prohibitions / issuer_cautions / folds / split / crossfit）を `context/conventions.md` の原文で読んだ
  （12-23、98-108、150-188、284-319、376-384 行）。`denominator` `sigma_policy` `frozen_source` の参照は契約に無い

## 3. Task B — 四つの集合（方法 A と方法 B）

方法 A: `.venv/bin/python experiments/analysis/frame_signal_audit/tools/audit_frames.py`（23.5 秒、復号 16 プロセス）。
方法 B: `bash experiments/analysis/frame_signal_audit/tools/count_shell.sh <scratchpad>/fsa/method_b`。

    方法 B: totals: phase=27694 tool=15437 host=25898 m15=15437 m20=25898 zero=123 phase_minus_tool=12257 tool_minus_phase=0
    照合: clips 43 cells compared 860 mismatches []

- 最初の方法 B は 4 区間（03_2・06_1・14_2・15_1）の「枠 0 個」が方法 A と 1 ずつ違った。原因は awk が COCO の `images` 要素で `id` が
  `file_name` より後に来ると仮定していたこと（実物は `id` → `width` → `height` → `file_name`）。直して再実行し 860 セル一致。**方法の照合が道具の誤りを捕まえた**
- 集合差の合計（方法 A）: phase−tool 12,257 / tool−phase 0 / phase−host 1,796 / host−phase 0 / tool−host 0 / host−tool 10,461 /
  phase−m15 12,257 / m15−phase 0 / phase−m20 1,796 / m20−phase 0 / m15−tool 0 / tool−m15 0 / m20−host 0 / host−m20 0
- 1,796 の所在: `01_frames/initial_videos` に 1,796 / HTS2 `images` に 0 / どちらにも無いもの 0。`find -L` の区間ごとの枚数は REPORT §1.3。
  1,796 枚の復号: `undecodable: 0`、すべて 1920×1080
- 復号（`data/raw/ego/` 25,898 枚）: `undecodable 0`、`sizes {'1920x1080': 25898}`、`bytes_total 4079408682`、
  要約値 `fb0b620e42e5c3690dbe9fb96405949a340cdf0bb26dc2178c059da9d67fae68`。動画ごとは `summary_method_a.json`
- 対照（`summary_method_a.json` の `controls`）: フレーム `01_1_0124` を抜いた写しで tool−phase 0 → **1**、phase−tool 12,257 → **12,258**（陽性）。
  phase−phase 0、tool−tool 0（陰性）。manifest15 の 01_1 から番号 125 を抜いた写しで飛び 52 → **53**（陽性）。3 つの assert が通った
- 起票者 §3.2 との照合: 全 14 項目と動画ごと 15 行が一致（`issuer mismatches: [] []`）
- 配布物の生フレームの番号: `01_frames/initial_videos` 26 区間すべてで 1 から枚数まで連続（`all contiguous from 1: True`）
- fps の出所: `git grep "0.5 fps"` → `docs/evidence/2026-09-16-A-phase-tower-candidates.md:30`（arXiv 2405.19644 を引用）、
  `docs/m2_plan_rewrite/m2_plan_v2_full.md:32,102`。配布物の文書（OpenSurgery README / AUDIT / SCALE_VERIFICATION、HTS2 README、`egosurergyhts_open`）に fps の記載なし。
  JPEG: `Image.open(...).getexif()` → `{}`、`applist` は APP0 のみ
- **関門 G2: pass**（二通り一致、§3.2 と一致）

## 4. Task C — 塔が扱うフレーム列

- run の記録: `experiments/phase1/stage1_ptower_r3_004_ft_coco_lr0.0001_foldA_seed42/config.yaml` 29-30, 53-54（`manifest_dir: data/processed/phase_manifest`、
  `train_frames: 9657`、`val_frames: 1515`）、`…_r3_029_features_…/config.yaml` 29-30、`…_r3_059_P15_C_L8_w0.15_h30_foldA_coco_lr0.0001_seed42/config.yaml`
  （`data.videos`、`receptive_field: 1021`、`cache_sha256 aa4aa85e…`）、`command.sh`（`python scripts/stage1_ptower_r3.py … action=train …`）。
  P\*-20: `stage1_ptower_20_007_ft_…foldA…/config.yaml` 60-61（20118 / 1515）、`_012_…foldB…`（20225 / 1861）、`_036_P20_C_L8_w0.3_h30_foldA_coco_…/command.sh`
  （`python scripts/stage1_ptower_20.py data_setting=P20 …`）
- キャッシュ: `r3_coco_lr0.0001_foldA_seed42/all_gap.npz` features (15437, 2048)、`all_gap.json` の `video_counts` 合計 15,437；
  `p20_coco_lr0.0001_foldA_seed42/all_gap.npz` (25898, 2048)、`video_counts` 合計 25,898（20 動画）
- 実装の行は REPORT §2。`predictions/` ディレクトリ: `ls …_r3_059_…/predictions` → 空。帰属解析の出力先 `/home/ubuntu/local/ptower_attribution_20261005` は本ホストに無い
  （`result.yaml` の host は dlsta）。`experiments/analysis/ptower_attribution/summary.json` は折り A の全体値のみ → C.5 は UNKNOWN

## 5. Task D — 送り手信号

- キャッシュの形（`np.load`、val）: `phase_context/relation_detr_seed42/val_phasectx.npz` ctx (1515, 9)；`b2a_detsignal/relation_detr_seed42/val_toolpresence.npz` signal (1515, 15)；
  `t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz` region (1515, 3840)；`oracle_toolpresence/val_oracletool.npz` (1515, 15)；
  `oracle_handfeature/val_oraclehand_presence.npz` (1515, 4)、`_geom` (1515, 16)；`stage1_features/relation_detr_seed42/val_gap.npz` (1515, 2048)。
  すべて frame_ids は 1,515 件で重複なし、並びは manifest と同一。COCO val の `images` の stem の並びも manifest と同一
- `.venv/bin/python experiments/analysis/frame_signal_audit/tools/time_alignment_check.py` → 6 経路すべて `verdict=同時刻`、ずらした写しは `ずらし(-1)`、`control_ok=True`
  （値は REPORT §3.2、全文 `time_alignment_val.json`）。最初の版は対照の期待を +1 と書いていて `control_ok=False` になった。写しは名前 t の行に t−1 の情報を持つので
  −1 が正しい。期待の符号を直し、符号の定義を docstring に書いた。データ側の判定値は変えていない
- 検出塔の形の出所: config の 23・24・25・26・28・30・38・40-41・84・91 行、`models/backbones/resnet.py:448-450`、`models/necks/channel_mapper.py:43-55`、
  `models/bricks/post_process.py:22-43`、`models/detectors/relation_detr.py:110`、`base_detector.py:45-47`。推論は 0 回
- 「一つ前の時刻まで」の規則: `git grep -n -i "一つ前の時刻\|ひとつ前の時刻\|前の時刻まで" -- docs/ context/ tasks/` → 0 件（該当は過去ラグ特徴の記述のみ）

## 6. Task E・F

- メタデータの探索の命令: `grep -rn -i "surgeon|術者|procedure|術式|operating room|手術室|撮影日|recorded|撮影|camera|GoPro|device|duration"` を
  `data/README.md`、配布物の README / AUDIT、HTS2 README、`egosurergyhts_open`、`data/annotations/*.md` に。該当は `egosurergyhts_open:8,10`（10 種類・8 人）と
  `data/README.md:45`（`surgeon_folds.json` は空）だけ。COCO の `info` / `videos` / `images` のキーは REPORT §4。`00_master_annotations/…/01/annotations.json` の `info` は
  Keio University / 2022-02-22、`videos` 無し。`git grep -i "gopro|tobii|eyewear|glasses|head-mounted|撮影機器|カメラ"` は他データセットの説明のみ
- 動画の長さの表: `video_length_from_annotations.csv`（工程 CSV の `gaps_phase_csv.csv` と `01_frames` の枚数から）
- Task F の要約値: `sha256sum` → COCO 初期化の重み `2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff`（196,140,106 B）、
  凍結源 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824`（195,421,066 B）。検出塔 `work/best_ap.pth`（各 195,421,066 B、`done.txt` rc=0）:
  dcoco A `30d199b15201cf3c` / B `be84c64bea271eae` / C `a46b37e8c5e9e458` / D `340b5628de86b9f1` / E `b0468f3692a400bf`、
  dimagenet A `c90db5af0b45f692` / B `73c5883535f21f7b` / C `15a453c5408bdf1a` / D `2f51a646e4be7c18` / E `68217bc69df2161d`（先頭 16 桁）
- `find -L /home/ubuntu -maxdepth 6 -type f -name main.py -path '*Relation-DETR*'` → `/home/ubuntu/slocal2/m2/third_party/Relation-DETR/main.py` のみ。
  `find /home/ubuntu -maxdepth 4 -name pyvenv.cfg` → 5 件（本 repo は `.venv` と `.venv-relation-detr`）。`.venv-relation-detr/bin/python -c` → 3.11.16 / torch 2.1.2+cu118
- `git ls-files` で工程塔の道具 7 本が在る。`df -B1`: `/home/ubuntu/slocal2` 空き 1,697,382,440,960 B、`/` 空き 1,516,562,481,152 B
- Syncthing: `pgrep -a syncthing` 2 件、`~/.syncthing.log` 末尾は `sync-alerts.log` の同期のみ

## 7. Task G — 検証（2026-10-14 20:25〜20:31）

- 要約値（終了）: 開始と**同一**（`diff digests_start.txt digests_end.txt` → DIGESTS UNCHANGED）。命令:
  `cat data/annotations/egosurgery_phase/*.csv | sha256sum; cat data/annotations/egosurgery_tool/instances_{train,val,test}.json | sha256sum;
  cat data/processed/phase_manifest/{train,val,test}.json data/processed/phase_manifest/phase_vocab.json | sha256sum;
  cat data/processed/stage1_features/p20_manifest/{train,val,test}.json …/phase_vocab.json …/audit.json | sha256sum`
- `git status --porcelain -- data/` → 空。`make forbidden-check TASK=…` → `status: pass`、permitted 17 件すべて `experiments/analysis/frame_signal_audit/` 配下、violations 0
- `make spec-check TASK=…` → `status: pass`、`rules_checked: 9`
- 試験（事後）: **6 failed, 793 passed, 1 error**（開始前と同一の集合）
- 装置（終了 20:30:18）: `nvidia-smi --query-compute-apps=pid` → 0 行
- 変更範囲: 新規 `experiments/analysis/frame_signal_audit/`（REPORT.md、CSV 11、JSON 2、tools/ 3）、`tasks/T-2026-10-14-frame-signal-audit/`（契約 2 + 報告 4）、
  `tasks/inbox.d/T-2026-10-14-frame-signal-audit.md`。既存ファイルの変更 0

## 8. 送出

（commit / push / PR / 台帳の応答は RESULT.md §送出と、下に追記する）
