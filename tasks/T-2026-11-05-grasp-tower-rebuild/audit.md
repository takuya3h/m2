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

### B0 の追加: bf16（利用者の追加の指示、2026-11-06）

- 1 回目（02:35 JST、commit aa8de639）: 6 水準すべて rc 1、1 ステップ目で `RuntimeError: "ms_deform_attn_forward_cuda" not implemented for 'BFloat16'`（mmcv 2.1.0）。ログは `$S/b0/bf16_try1/`
- 利用者の決定（選択肢 1）: 変形注意の入力が bf16 のときだけ fp32 に変換して計算し、出力を bf16 に戻す。ほかは bf16。仮想環境と third_party は変えない。学習でも同じ形を使う。`meta.amendments` に記録
- `g5_train.patch_msda_bf16()` を足した（mmcv の `multi_scale_deform_attn` モジュールが名前で引く `MultiScaleDeformableAttnFunction` を、この過程の中だけ包みに差し替える）。確かめ（`$S/b0/msda_patch_check.txt`）:
  包まない bf16 → not implemented、fp32・fp16 は素通しでビット一致、bf16 の出力は bf16・fp32 との差の最大 0.0041、勾配は bf16 で有限
- 2 回目（02:38〜02:43 JST、commit 61c364bd）: batch 2〜12 は収まり非数 0、batch 16 は 1 ステップ目で溢れた。表は `batch_probe.md`。再び止まって諮る

### C-1 本番の 3 本（2 回目。利用者の回答の後。起動 2026-11-06 02:5x JST、commit ff954d9f）

- 利用者の回答: batch 8、bf16（変形注意だけ fp32）、学習率 1e-4 のまま。GPU 0 に確定、GPU 1 に H1 の後 H2
- `g5_train.py` に `--batch`・`--amp none|bf16` を足した（既定は batch 2・単精度で従来どおり）。評価は単精度・batch 2 のまま
- 試走（`$S/logs/c0_smoke_b8bf16.txt`）: 1 epoch 1,169 ステップ、20 ステップの後の val 10 枚 0.5576、最大確保 25,634,898,432 B、COCO の重み 608 / 610、非数なし
- 起動前: 本契約以外の compute 0 件（数えた 1 件は確かめの命令の python 自身）、GPU 0・1 とも 39・37 MiB、run の置き場は空

      CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/g5_train.py --run-dir experiments/phase1/grasptower_G_all_seed42 --ckpt-dir $S/g/ckpt/all --ann-dir $S/g/ann --videos all --batch 8 --amp bf16
      CUDA_VISIBLE_DEVICES=1 （H1 → H2 の順）... --run-dir experiments/phase1/grasptower_G_{H1,H2}_seed42 --ckpt-dir $S/g/ckpt/{H1,H2} --videos {H1,H2} --batch 8 --amp bf16

### C-1 の途中: GPU 1 の共有（本契約の外、使用者は不明）

- 03:24 JST（ホストの時計 18:24 UTC）に気づいた: GPU 1 の全体の使用 47,250 MiB・使用率 100%・218 W に対し、本契約の H1 は 26,152 MiB。
  約 21 GB を `nvidia-smi` のプロセスの一覧に出ない使用者が使っている。起動の時点（02:53 JST）の GPU 1 は 37 MiB だった
- この機械から見える root のプロセスは 2 件だけ（コンテナか別の名前空間の中とみる）。使用者は UNKNOWN。
  `experiments/analysis/tower_batch_probe/tools/`（別の契約、同期で届いた。最終更新 02:30 JST、GPU の指定を含む）との関係も UNKNOWN
- 影響: H1 の 1 ステップが epoch 1 の 1.23 秒から epoch 2 は 2.27 秒（約 1.8 倍）。GPU 0 の確定の G は 1.27 秒で影響なし。値は変わらない見込み（記憶の領域は分かれ、cudnn.benchmark は無効）。記憶の余裕は約 1.9 GB
- 契約の停止の条件（本契約以外の compute プロセス）に当たるため、相手を止めずに利用者に諮った → **利用者の決定（03:5x JST）: このまま続ける**
- 監視（Monitor）は 2 回、出力を一件も届けずに切れた（`cut` のため込み、次に背景の部分シェル）。一本の `tail -F | awk`（fflush）に直した

### C-1 の結果（3 本、batch 8・bf16（変形注意だけ fp32）・学習率 1e-4）

| run | 選んだ epoch | 5 クラス mask mAP | 学習前 | 止まった epoch | 所要 | 最大確保 | COCO の重み | 最良の重みの sha256 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| grasptower_G_all_seed42 | 3 | 0.6460 | 0.0060 | 7 | 11664 秒 | 25,634,898,432 B | 608 / 610 | 5ea2cbf479254d78330664415e639929a86f704e5fe8b5ac8a485c7d3d9964d1 |
| grasptower_G_H1_seed42 | 3 | 0.5939 | 0.0060 | 7 | 7240 秒 | 25,634,898,432 B | 608 / 610 | 5cfa055cbc72329ca1eb8f0bd8a487b64af8eaa88daac5657067cba7b9cd17c7 |
| grasptower_G_H2_seed42 | 6 | 0.5814 | 0.0060 | 10 | 10069 秒 | 25,634,898,432 B | 608 / 610 | efdefccd4484fc6af0238e14044c89ec3010a83744db455734a019702377098b |

- 3 本とも終了コード 0、収束規則（最良が 4 epoch 更新されなければ打ち切り）で止まり、上限 36 に達していない。epoch ごとの記録は REPORT §2
- 起動 02:53 JST。H1 は 04:55 JST に終わり、続けて H2 を起動、H2 は 07:49 JST に終わった。確定の G は 06:08 JST ごろに終わった

### C-3 反転の整合（`$S/flip/c3_flip_*.json`、val 40 フレーム、seed 42）

    python scripts/grasppilot/g5_signals.py flipcheck --ckpt coco --label pre_coco ...
    python scripts/grasppilot/g5_signals.py flipcheck --ckpt $S/inputs/g2_ckpt/all/best.pth --num-classes 38 --label second_G_all ...
    python scripts/grasppilot/g5_signals.py flipcheck --ckpt $S/g/ckpt/all/best.pth --label after_all ...

| G | 入れ替えて比べる（soft IoU、クラス平均） | 入れ替えずに比べる（陽性対照） |
|---|---:|---:|
| 学習前 | 0.439 | 0.633 |
| 二本目の確定の G | 0.134 | 0.787 |
| 本契約の確定の G（epoch 3） | 0.693 | 0.118 |

### C-2・C-4 val の評価（`$S/evalval/*.json`、`g5_signals.py evalval`）

- 印を除いた値（1,514 フレーム）と、val の印のフレーム `10_1_0595` を注釈なしの画像として足した値（1,515）。確定 0.6460 / 0.6459、H1 0.5939 / 0.5937、H2 0.5814 / 0.5813、学習前 0.0060 / 0.0060
- 印を除いた値は 3 本とも学習中の記録と一致した

**G3: pass**

## Task D — 信号と標的

### D-1 推論（`$S/signals/raw/`、`g5_signals.py infer`、GPU 0、評価は単精度）

| 出力 | G | split | 動画 | フレーム | 枠 | 所要 | g の値の範囲 |
|---|---|---|---|---:|---:|---:|---|
| all_val | all（epoch 3、5ea2cbf479254d78…） | val | 09,10 | 1,515 | 4,707 | 282 秒 | [0.000, 0.995] |
| H1_on_H2 | H1（epoch 3、5cfa055cbc72329c…） | train | 02,03,08,13,14 | 5,582 | 18,071 | 1024 秒 | [0.000, 0.995] |
| all_train | all（epoch 3、5ea2cbf479254d78…） | train | 01,02,03,06,08,11,12,13,14,15 | 9,657 | 32,272 | 1700 秒 | [0.000, 0.996] |
| H2_on_H1 | H2（epoch 6、efdefccd4484fc6a…） | train | 01,06,11,12,15 | 4,075 | 14,201 | 697 秒 | [0.000, 0.997] |

### D-2 正解との比べ（`$S/compare/*.json`、二本目の `g_signals.py compare` をそのまま使った）

- 確定の G・val、H1→H2・train、H2→H1・train、確定の G・train（交差適合なし。conventions#crossfit の「交差適合版と非適用版の両方を記録」）。値は REPORT §5

### D-3〜D-6 組み立て（`g5_signals.py assemble`、08:09〜08:10 JST）

    python scripts/grasppilot/g5_signals.py assemble --raw $S/signals/raw --out $S/signals --manifest experiments/analysis/grasp_tower_rebuild/signals_manifest.json --g-run <3 本の config.json>

- 交差適合: train 9,657 フレームの外れ 0 件。動画ごとに作った G は 01・06・11・12・15 が H2、02・03・08・13・14 が H1（どれもその動画を学んでいない）。
  対照: 確定の G で作った信号を 5 フレーム混ぜた写しで外れ 5 件。val 1,515 フレームは確定の G（外れ 0 件）
- test 不使用: 各段（G の学習 3 本、推論 4 つ）の動画の集合と {04, 05, 07} の共通は 0 件。対照: 04 を混ぜた入力で共通 1 件
- q の確かめ: 3 つの表（交差適合の train、確定の G の train、確定の G の val）で、枠の欠け 0・余り 0・行の和の誤差の最大 4.5e-8・値の最小 0。対照: 値を一つ変えた写しで和の誤差 0.25、`ok: false`
- q の正規化（行の和が 1 を超えた枠を 4 値の和で割った）: 交差適合の train 16,021 / 32,272 枠（最大の和 1.546）、確定の G の train 16,089 / 32,272（1.634）、val 2,327 / 4,707（1.219）
- 入れ替え（g と m、split ごと、seed 42）: train は元と同じフレーム 0.000・同じ動画 0.115、val は 0.001・0.556。対照の seed 43: train 0.0001・0.118、val 0.0007・0.554（並べ替えの要約値も違う）
- 入れ替え（q、同じフレームの枠の間、seed 42）: 元と同じ枠の割合は train 0.300（枠が 2 個以上のフレームで 0.287）、val 0.318（0.289）。対照の seed 43: 0.284・0.284
- 目録 `experiments/analysis/grasp_tower_rebuild/signals_manifest.json`（host Bengio）

## Task E — 集計・検証

- 試験（`$S/final/pytest_end.txt`）: 11 failed・980 passed・5 skipped。失敗の名前の集合は A-5 と同じ（`diff` で差なし）
- 仮想環境の要約値: `.venv` 9c7be5c9…、`.venv-relation-detr` a74c9c78…。A-5 と一致
- `make forbidden-check TASK=T-2026-11-05-grasp-tower-rebuild`（作業ツリー、08:2x JST）: status fail、changed 64・violations 51
  - 24 件は同期で届いた別の契約のファイル（`experiments/analysis/dtower_batch_search/tools/`・`dtower_step_profile/tools/`・`tower_batch_probe/tools/`）。触れていない
  - 27 件は本契約の run の記録（`experiments/phase1/grasptower_G_*_seed42/`）。契約の `allow_write` に `experiments/phase1/grasptower` が無い（SPEC §4 と食い違う。起票者の誤り）。扱いを利用者に諮った
- 利用者の決定（選択肢 1）: `allow_write` に `experiments/phase1/grasptower` を足し、`meta.amendments` に記録した。validate OK
- 足した後の `make forbidden-check`（作業ツリー）: status fail、changed 67・violations 24・permitted 30。違反はすべて別の契約のファイル（dtower_batch_search 10・dtower_step_profile 7・tower_batch_probe 7）。本契約の経路（run の記録 27 件と `experiments/analysis/grasp_tower_rebuild/` の 3 件）は permitted

## 送出

- commit 959f8143 を push（遠隔の先頭と一致）
- 分岐の HEAD の写し（`git clone --shared` を作業用の場所へ、origin/phase0 89fe4a41 を取得）で `tools/check_forbidden.py --task T-2026-11-05-grasp-tower-rebuild` → status pass、changed 43・checked 43・violations []
- PR #289 は 2026-11-06 03:39 JST（18:39:53 UTC）に利用者（takuya3h）が統合済みだった（head ff954d9f、merge commit 6e28c49d）。残りの commit を PR #295 で起票した（base phase0、Draft でない）
- `git merge-tree --write-tree origin/phase0 HEAD` → README.md と docs/experiment_log.md が衝突。phase0 側の T-2026-11-06-tower-batch-probe・T-2026-11-06-dtower-step-profile（andrew）の末尾の追記と、本契約の末尾の追記。分岐では解いていない

## 解決された参照（手順書 3、`contract.inject_verbatim` の原文）

`context/conventions.md` の blob ceb7ef0f（`git log -1 -- context/conventions.md` = 2d946b07 = 契約の `conventions_rev`）から、6 節を原文のまま写す。denominator・frozen_source・sigma_policy の参照は契約に無い。

### conventions#prohibitions（98〜108 行）

> <a id="prohibitions"></a>
> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### conventions#issuer_cautions（154〜192 行）

> <a id="issuer_cautions"></a>
> ## issuer_cautions
>
> **起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
> 実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**
>
> | # | 注意 |
> |---|---|
> | 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
> | 2 | 一致 0 件なら別の異質な方法でも確認する |
> | 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
> | 4 | 仕組みの挙動は実装を読んでから信じる |
> | 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
> | 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
> | 7 | **丸めた表示を実数として扱わない** |
> | 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
> | 9 | 無変更は要約値で確かめる。表示属性では足りない |
> | 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
> | 11 | 測定の副作用が禁止領域へ触れないか確かめる |
> | 12 | **判断の前に、いま見ているものが最新かを確かめる** |
> | 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
> | 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |
>
> **注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
> 確かめると 3 件とも実在した。
>
> **注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
> （`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。
>
> **注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
> （自分の命令行にその語が含まれるため）。
>
> **注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。
>
> **シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
> 一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**
>
> **命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

### conventions#env_p0（109〜120 行）

> <a id="env_p0"></a>
> ## env_p0
>
> 学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
> activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
> 数値が変わったまま完走する。
>
>     source .venv-relation-detr/bin/activate   # 検出系
>     source .venv/bin/activate                 # 解析・工程系
>
> 拡張のロード確認をログに残すこと。

### conventions#folds（297〜366 行）

> <a id="folds"></a>
> ## folds
>
> 動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
> 本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。
>
> | 折り | test（3） | val（2） |
> |---|---|---|
> | A | 04, 05, 07 | 09, 10 |
> | B | 01, 03, 14 | 02, 08 |
> | C | 02, 08, 11 | 06, 12 |
> | D | 06, 13, 15 | 04, 05 |
> | E | 09, 10, 12 | 07, 15 |
>
> train はその折りの test と val を除いた 10 本である。
> **折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
> 各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。
>
> ### 追加 6 動画
>
> 工程の注釈がある追加動画は次の 6 本である。
>
>     17, 18, 19, 20, 21, 22
>
> **22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
> 旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
> 出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
> `tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。
>
> **用途は訓練のみである。どの折りの test にも val にも現れない。**
> 15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。
>
> ### 規律
>
> **選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
> test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。
>
> 出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。
>
> ### val と test の重なり
>
> 各折りの val 2 本（計 10 本）は、どれもほかの折りの test に現れる。上の表から読める対応は次のとおり。
>
> | val の動画 | val に使う折り | test に持つ折り |
> |---|---|---|
> | 09, 10 | A | E |
> | 02, 08 | B | C |
> | 06 | C | D |
> | 12 | C | E |
> | 04, 05 | D | A |
> | 07 | E | A |
> | 15 | E | D |
>
> **val に一度も入らないのは 01・03・11・13・14 の 5 本**である。test としては折り B に 3 本（01・03・14）、
> C に 1 本（11）、D に 1 本（13）、A と E には 0 本。
>
> val で設定・処方・構造・型・止め方を選ぶ段（両塔の学び直しと Stage 2 以降）では、次の三つを守る。
>
> 1. この重なりを prereg と報告に明記する
> 2. test の値を報告するときは、val に一度も入らない 5 動画だけで集計した値を副次として添える。
>    各動画の値は、その動画を test に持つ折りのモデルが出す。集計の仕方は prereg に書く
> 3. 副次の値は、判定・関門・選定のどれにも使わない
>
> 選ぶ規則（規律の小節。その折りの val で選ぶ）は変えない。
>
> 出所: 利用者の決定 2026-10-19（契約 `T-2026-10-21-ops-taskstart-resume-folds-val` SPEC §2）、上の折りの表、
> `docs/stage1/design_val_subsets.md` 223 行。
>
> ---

### conventions#split（12〜23 行）

> <a id="split"></a>
> ## split
>
> 論文準拠 split の動画 ID は次のとおり。
>
> - train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
> - val: `09`, `10`
> - test: `04`, `05`, `07`
>
> 転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
> 実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。

### conventions#crossfit（457〜469 行）

> <a id="crossfit"></a>
> ## crossfit
>
> 送り手の積み重ね漏れ（stacking leakage）の扱い。研究方針 v2 §9.4。閾値は利用者の決定（2026-09-27）。
>
> - 送り手が学習した train 動画で送り手が出す予測は過学習している。界面をその予測で学習すると、train と val・test で信号の質が違う
> - **送り手の train 動画と val 動画の主指標の差が 3pt を超えれば、交差適合を適用する**
> - 交差適合: 各折りの train 動画を動画単位で 2 分割し、一方で学習した送り手が他方に予測を出す。両方向で train 動画すべての予測を作る。
>   val・test への予測は train 全体で学習した確定塔が出す
> - 適用は送り手掃引の全点で統一する。主送り手だけに適用しない
> - 交差適合版と非適用版の送り手の主指標を両方記録する
> - 実測: 検出塔の送り手の差は約 11pt（Stage 0 の凍結検出器 1 本の値。確定塔 D\* の差は未測定）。工程塔の送り手の差は 20 件すべてで 3pt を超え、最小 +0.1254（`tasks/T-2026-09-27-stage1-ptower-20/RESULT.md` §4「送り手の train と val の差」）

