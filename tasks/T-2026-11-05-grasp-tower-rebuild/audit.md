# audit — T-2026-11-05-grasp-tower-rebuild（非公式の測定。関門と設計の判断に使わない）

ホスト bengio（bengio 版の契約。andrew 版は利用者の指示で中止し、その audit は commit 2d87d79f に残る）。
時刻は JST（ホストの時計は UTC なので +9 時間して書く）。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild`（bengio）。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/hostdiff-bengio`、作業ツリーは清浄。`feat/grasp-tower-rebuild` は手元に無く、`ls-remote` でも遠隔に無く、
  契約の履歴も `.sync-pause` も無かった（2026-11-06 01:1x JST）
- `python3 scripts/task_start_classify.py` → 全区分 0 件、`分類: 通す`（比較先 origin/phase0 89fe4a41）
- `make task-start` → `分岐を作成: feat/grasp-tower-rebuild（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、契約を台帳から取り込み、`完了。`
  - 目印の中身: `task_id=T-2026-11-05-grasp-tower-rebuild` / `branch=feat/grasp-tower-rebuild`
- `make task-validate` → `OK`、`make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。SKIP: P2・P3（契約に記載なし）、
  P4・P5・P13・P14（kind=analysis で対象外）、P12（解決前提の参照なし）。P9 spec_lint は該当なし
- **分岐の重複を検出して停止**: 取得の後に `git ls-remote --heads origin` が `feat/grasp-tower-rebuild` 2d87d79f を返した。
  andrew 版の同じ契約（PR #289、OPEN、Draft でない。Task C の epoch 2 で利用者の指示により中止、status stopped）。
  andrew の手元も同じ分岐（ssh で読むだけ）。手順書 0 の規則 2 により停止し利用者に諮った
- **利用者の決定（選択肢 1）**: andrew の分岐の上に積み PR #289 を使い続ける。**実験自体はちゃんとやり直す**
  - 取り込んだ bengio 版の契約を作業用の場所へ写し（sha256 一致）、未追跡の契約フォルダを移してから
    `git merge --ff-only origin/feat/grasp-tower-rebuild`（89fe4a41 → 2d87d79f、早送り）
  - `spec.yaml`・`SPEC.md` を bengio 版で置き換え（4ce69dfb）。置き換えた契約で validate `OK`、preflight 7 PASS / 0 FAIL
  - andrew の途中の出力（andrew の `$S/aborted/try1/` の重み・注釈・反転の記録）は**使わない**。注釈・検査・学習はすべて bengio で作り直す。
    使うのは andrew 版で commit 済みのコード（`g5_build.py`・`g5_train.py`・`g5_flip_test.py`・`g5_signals.py`）だけ
  - バッチサイズは契約どおり 2（andrew は「バッチサイズについて検討する」として止めた。bengio 版の契約は「処方は二本目と同じ」）

## Task A — 開始状態（G1）

記録の原本は `$S/start/`。

### A-1 分岐と起点、二本目と三本目の内容（`$S/start/a12.txt`）

    $ git branch --show-current; git merge-base HEAD origin/phase0; git rev-parse origin/phase0
    feat/grasp-tower-rebuild
    89fe4a417e51ddc830e275ff8cd718a475ad36ba（merge-base と origin/phase0 が同じ）
    $ git log --oneline origin/phase0..HEAD
    4ce69dfb（bengio 版の契約）、2d87d79f・3aa9458e・ec05e4bd・3d348a22（andrew 版の 4 件）
    $ git ls-tree --name-only origin/phase0 -- tasks/T-2026-11-01-grasp-pilot-g tasks/T-2026-11-01-grasp-pilot-d scripts/grasppilot/{g_train,d_targets,g38_build,g_signals,grasp_signals}.py
    7 件すべて在る

### A-2 開始前から在る未追跡

    $ git status --porcelain --untracked-files=all | wc -l
    0
    $ find experiments/phase1 -maxdepth 1 -name 'grasptower_*'
    grasptower_G_all_seed42・grasptower_G_H1_seed42・grasptower_G_H2_seed42（いずれも 2026-11-06 01:06 JST 作成、中身 0 件の空のフォルダ）

- 空の 3 フォルダは andrew 版の run の置き場が同期で届いた残りとみる（git は空のフォルダを数えない）。消していない。本契約の run 名と同じなので、そこへ書いた

### A-3 compute プロセス（`$S/start/a3_procs.json`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 60、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh            → count 9
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0

### A-4 記憶領域と写し（`$S/start/a4_df.txt`・`a4_copied_sha256.txt`）

    $ df -B1 /home/ubuntu/slocal2
    Available 1,389,087,522,816 B（使用 82%）
    $ ssh andrew du -sb <二本目の保存先> <一本目の保存先>
    28,629,765,031 B・799,990,843 B（目安。本契約の生成物はこれ以下と見込み、空きの 2% 程度）

- bengio の二本目の保存先には `signals/` だけがあり G の重み（`g/ckpt`）も注釈も無い。一本目の保存先には `signals/g_{train,val}.npz` だけがあり COCO の重み（`e/weights`）が無い
- **写し先は本契約の保存先 `$S/inputs/`**（一本目・二本目の保存先へは書かない、§7-2）。andrew からは `scp` で読むだけ

| ファイル | 写し先 | sha256 | 照合先 |
|---|---|---|---|
| 二本目 G 確定 best.pth | `$S/inputs/g2_ckpt/all/best.pth` | 42c1f3bce6ed2027… | `experiments/phase1/grasppilot2_G_all_seed42/metrics.json` と一致 |
| 二本目 G H1 best.pth | `$S/inputs/g2_ckpt/H1/best.pth` | e702af3e096eeb72… | 同 H1 と一致 |
| 二本目 G H2 best.pth | `$S/inputs/g2_ckpt/H2/best.pth` | 52d4b3aa178433b5… | 同 H2 と一致 |
| COCO instance の重み | `$S/inputs/coco/mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth` | 41b088b62838c986… | 一本目 audit の 41b088b62838c986… と一致 |
| 一本目の正解の g（train・val）と summary.json | `$S/inputs/probe_signals/` | 741cecb5…・235e2c2b…・bf1cd898… | andrew の原本・bengio の一本目の保存先の既存の写しと 3 者一致 |

- 一本目の正解の m はファイルとして保存されていない（一本目の audit「m は保存しない。学習と評価のときに注釈から作る」）。比べは注釈から作る

### A-5 試験と仮想環境（`$S/start/a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped（48.10 s）
    失敗の名前: test_check_spec::test_teacher_detection_rate、test_engines::test_mmdet_trainer_eval_recipe_in_metrics、
      test_fetch_task::test_rejects_unknown_file_name、test_research_logger の 4 件、test_stage1_ptower_heads::test_existing_candidates_match_baseline[A,B,C,linear]
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768a…a6682f94c0（108 行）、.venv-relation-detr a74c9c787e79f014…ad5b090（72 行）。二本目の記録の値と一致

### A-6 GPU（`$S/start/a6_gpu_power.csv`）

    0, NVIDIA RTX A6000, 220.00 W（既定 300.00 W、最大 300.00 W）
    1, NVIDIA RTX A6000, 220.00 W（既定 300.00 W、最大 300.00 W）

### A-7 契約の版

- `contract.conventions_rev` 2d946b07 = `git log -1 -- context/conventions.md`（差分なし）
- `meta.created_from.runindex_commit` 68befc3b = `git log -1 -- runindex/`。件数 index 2,363・experiments 1,130・verdicts 1,736（見出し行を除く）で一致
- 食い違いが無いので `meta.amendments` は空のまま

**G1: pass**（分岐 feat/・起点 origin/phase0・二本目と三本目の内容が起点に在る・本契約以外の compute 0 件・空き・失敗の名前・要約値・電力の上限を記録）

## コードの変更（bengio で動かすため。f149c79d）

- `g5_train.py`: COCO の重みを `COCO_W = $S/inputs/coco/<同じファイル名>` から読む（以前は一本目の保存先の経路。bengio には無い）。sha256 の照合は従来どおり
- `g5_signals.py`: 目録の `"host"` を固定の `"andrew"` から `os.uname().nodename` へ
- 二本目・三本目の既存スクリプトは変えていない（§7-6）

## Task B — 注釈と反転の経路（G2）

### B-1・B-2 注釈（`$S/g/ann/g5_summary.json`、`$S/logs/b1_build.txt`）

    $ .venv/bin/python scripts/grasppilot/g5_build.py --out $S/g/ann --check-frames 16
    train 9657 9356 32408 {01:912, 02:460, 03:1068, 06:1355, 08:1305, 11:747, 12:485, 13:809, 14:1801, 15:414} restore_equal True class_viol 0 ctrl 1 lm_in 0 lm_ctrl 1
    val 1515 1514 5653 {09:518, 10:996} restore_equal True class_viol 0 ctrl 1 lm_in 0 lm_ctrl 1

| id | 名前（hand_tool_seg） | 反転で | train インスタンス / フレーム | val インスタンス / フレーム |
|---|---|---|---:|---:|
| 1 | First Person's Left Hand | 2 | 8,704 / 8,659 | 1,505 / 1,491 |
| 2 | First Person's Right Hand | 1 | 8,447 / 8,386 | 1,467 / 1,463 |
| 3 | Left Hand Tool | 4 | 7,129 / 7,129 | 1,231 / 1,231 |
| 4 | Right Hand Tool | 3 | 7,176 / 7,176 | 1,274 / 1,274 |
| 5 | Two Hands Tool | 5 | 952 / 952 | 176 / 176 |

- フレーム数 train 9,356・val 1,514 は被覆の文書（§2）の値と一致。sha256: g5_train.json aa88bee27f677348…、g5_val.json 762af7e824929902…
- 戻したマスク: 16 フレーム（seed 42）で元の注釈と画素で一致
- 対照: 手 4 クラスの注釈を 1 件混ぜた写しで対応表の検査が外れ 1 件
- 欠落の印: 一覧は train 301・val 1・test 158 行（test は行数だけ数えた）。工程の経路のうち注釈の無いフレームの集合は、印の集合と **train 301 = 301、val 1 = 1 で集合として一致**（印のフレームは注釈ファイルに 0 件）

### B-3 反転の経路の取り出し（`$S/flip/b3_flip_paths.json`、GPU なし、左右のラベルを持つ train 24 フレーム）

    G5Flip_swap        image_flipped 24 masks_flipped 24 labels_swapped 24 labels_unchanged 0
    G5Flip_noswap_copy image_flipped 24 masks_flipped 24 labels_swapped 0  labels_unchanged 24
    G38_second_path    image_flipped 24 masks_flipped 24 labels_swapped 0  labels_unchanged 24

### B-4 欠落の印が損失に入らないこと（`$S/logs/b4_lossmask_control.txt`）

- 印のフレームは注釈を持たず学ぶフレームに入らない（B-1）。`g5_train.py` は学ぶフレームに印のフレームがあれば学習を始めずに止める
- 対照: 印のフレーム `01_1_0698` を train の注釈に 1 件足した写し（作業用の場所）で `g5_train.py --smoke` →
  `RuntimeError: 欠落の印の付いたフレームが学ぶフレームに 1 件ある（['01_1_0698']）。学習を始めない`
- 「印のフレームだけの数歩で損失が 0」は測っていない。対象外にする形（§3.1 が許す「学習の対象から外す形」）で示した

**G2: pass**

## Task C — G の学習（G3）

### C-0 試走（`$S/logs/c0_smoke.txt`、GPU 0）

    $ CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/g5_train.py --run-dir $S/smoke/run_all --ckpt-dir $S/smoke/ckpt_all --ann-dir $S/g/ann --videos all --smoke
    学習前（val 10 枚）0.0006 → 20 歩の後 0.4845、COCO の重み 608 / 610、最大確保 9,846,922,752 B

### C-1 本番の 3 本（起動 2026-11-06 01:30 JST、commit f149c79d）

    CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/g5_train.py --run-dir experiments/phase1/grasptower_G_all_seed42 --ckpt-dir $S/g/ckpt/all --ann-dir $S/g/ann --videos all
    CUDA_VISIBLE_DEVICES=1 ... --run-dir experiments/phase1/grasptower_G_H1_seed42 --ckpt-dir $S/g/ckpt/H1 --videos H1
    CUDA_VISIBLE_DEVICES=1 ... --run-dir experiments/phase1/grasptower_G_H2_seed42 --ckpt-dir $S/g/ckpt/H2 --videos H2

- 1 枚に載せる本数: GPU 0 に確定の 1 本、GPU 1 に H1・H2 の 2 本（試走の最大確保 9.85 GB × 2 < 48 GB）
- 学ぶフレーム: 確定 9,356、H1 3,913、H2 5,443。val 1,514。COCO の重みは 3 本とも 608 / 610（cls_embed の 2 個は形が違い読まない）
- 起動直後: GPU 0 使用率 85%・211 W、GPU 1 使用率 99%・193 W（上限 220 W）

### C-1 の中止（利用者の指示、2026-11-06 01:42 JST 一時停止 → 01:59 終了）

- 01:42 利用者「一度学習止めてもらって良い？」→ 3 本の python（本体と worker の 27 プロセス）を SIGSTOP。止めた位置は 3 本とも epoch 1 の途中（確定 600 / 4,678 歩過ぎ）
  - 最初の `kill -STOP $pids` は zsh が一覧を一語として渡したため効かず（`illegal pid`）、`pgrep … | xargs kill -STOP` でやり直した
- 利用者が `/task` を再び呼んだ → 手順 0 は「再開」。プリフライトは **P11 gpu_free FAIL**（一時停止中の本契約の 3 本が GPU の記憶を持つ）で停止して諮った
- 利用者「よみなおし」→ 台帳の現在の版を `fetch_task.read_notion_bundle`（要約値の照合つき）で作業用の場所へ読み出して手元と比べた。
  台帳の版は Task B0（batch と数値精度の計測、12 水準）と G2b・完了判定 k を足していた（spec.yaml a386ecd6…、SPEC.md 97306ba1…）
- 旧版の条件で起動した 3 本は新しい版の Task C の条件に当たらないため、01:59 に SIGKILL で終了した（exit 137）。
  出力（run の記録、ログ、ckpt の置き場）は消さずに `$S/aborted/try1/` へ移した。epoch 1 を終えていないので、評価の値も重みも無い
- 台帳の版で `spec.yaml`・`SPEC.md` を置き換え（eb4c4925）→ validate OK、preflight 7 PASS / 0 FAIL（P11 PASS）

## Task B0 — batch と数値精度の計測（G2b）

    $ $S/b0/run_b0.sh     （GPU 0、水準ごとに GPU 0 の記憶 39 MiB・compute 0 件を確かめてから起動）
    CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/g5_batch_probe.py --batch <b> --amp none|fp16 --ann-dir $S/g/ann --out $S/b0/b<b>_<amp>.json [--no-weights]

- 12 水準 + 対照（batch 2・fp32・重みを読まない）。02:00:59〜02:13:42 JST。結果の表は `experiments/analysis/grasp_tower_rebuild/batch_probe.md`
- batch 16・fp16 は 1 回目が `CUDNN_STATUS_NOT_INITIALIZED` で記録なく終わった（rc 1、`$S/b0/b16_fp16_try1.log`）。道具がこの誤りも記録するよう直して（`g5_batch_probe.py`）02:16 に測り直し、1 歩目で再現（最大予約 50.40 GB）
- COCO の重みは全水準で 608 / 610 を読んだ（対照を除く）
- 表を commit・push して停止し、利用者に batch・数値精度・学習率を諮る（G2b）
