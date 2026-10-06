# 監査 — T-2026-09-27-stage1-ptower-20

実測だけを書く。未測定は UNKNOWN と書く。時刻は UTC。

## 0. 検査の結果

| 層 | 命令 | 結果 |
|---|---|---|
| L1+L2 | `make task-validate` | 初回の取り込み（2026-10-02）は FAIL `[L2-5] アンカー crossfit が存在しません`。PR #198 の統合（10:59）後に取り込み直して OK。WARN 3 件（L2-8: created_from.counts が 0 のまま。index 0→1911 / experiments 0→718 / verdicts 0→1506）。利用者が承知のうえ続行を指示 |
| L3 | `make task-preflight` | 取り込み直後と Task F の二度とも exit 0（11 PASS / 0 WARN / 3 SKIP / 0 FAIL）。P13・P14 は二度とも PASS |
| 禁止領域 | `make forbidden-check TASK=…` | **status fail**。違反 20 件はすべて開始前から未追跡の `data/annotations/egosurgery_phase/17_1〜21_5.csv`（commit しない）。それ以外 0 件。宣言 `data/processed/stage1_features/` は上限により却下（.gitignore 対象で差分に出ない） |
| spec | `make spec-check TASK=…` | pass（規則 9 件） |
| 試験 | `pytest tests/` | 作業後 6 failed / 691 passed。起点 331525e8 の作業木（third_party が無いため dtower_convergence を除く）で 7 failed / 657 passed / 15 skipped。6 件は起点でも落ちる |
| 収穫 | `make runindex` | task_id で引いて 50 行 |

L3 の SKIP 3 件（「合格」ではなく「実行されなかった」）:

- P2 `cuda_ext_loaded` — `plan.env.preflight` に記載なし
- P3 `deterministic_flags` — 判定基準が未確定（backlog B-20）
- P12 `refs_resolved` — 解決前提の参照は無い

## 1. Task A

### A-1 prereg の固定

`0049f2fcf68028cccae2d184eab25b473b689055`、`2026-10-02T11:05:16+00:00`。占位の差し替え（A-5）は `7e8c719c`。
以後 spec.yaml は変更していない。全 50 run の `contract_sha256` は `ffdc99e0…` で現在の spec.yaml と一致。

### A-2 開始状態

| 項目 | 実測 |
|---|---|
| ホスト | `efros`（`hostname`）。指示の `~/slocal/m2` は存在せず実体は `~/slocal2/m2` |
| 分岐 | `feat/stage1-ptower-20`（`make task-start` が `origin/phase0` = 331525e8 から作成） |
| 作業ツリー | 開始前の未追跡 22 件（注釈 CSV 20 件・digest 2 件）を利用者の指示で `stash@{0}`（pre-T-2026-09-27-stage1-ptower-20）に退避。注釈 20 件は Task B のため作業ツリーへ未追跡のまま戻した |
| 装置 | RTX A6000 49,140 MiB × 2。**開始時に仮占有プロセス 2 本**（PID 696690 / 696691、2026-09-29 14:59 起動、各 GPU に 34.6 GiB を確保して行列積を回し続ける。cwd は本 repo）。停止して諮った。実行者の kill は実行基盤に拒否され、利用者が止めた |
| `.sync-pause` | `make task-start` が設置。稼働中の keeper は対応版（`grep -c sync-pause ~/bin/m2-sync.sh` = 2） |

### A-3 efros に揃っているもの

| 項目 | 実測 |
|---|---|
| 15 動画の工程フレームと manifest | `data/processed/phase_manifest/{train,val,test}.json` の 15,437 枚がすべて実在。三周目の数と一致 |
| 追加 17〜21 | 一度目: 17・18・19 のみ（20・21 のフレーム 0 件）→ 停止して移送を依頼。二度目: 20・21 が届き数が一致。のちに 19 の破損が判明（§2） |
| 動画 22 | 注釈 22_1〜22_3 が `data/raw/OpenSurgery_Dataset/.../annotations/phase/` に在る。フレームは 0 件 |
| COCO 検出 checkpoint | `data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`、196,140,106 bytes、sha256 `2d2c19a7…`。`build_backbone` が出す要約値 `a755b3eb…` が三周目と一致 |
| ImageNet-1K R50 | 要約値 `4f6b5b62…` が三周目と一致 |
| 三周目の時間ヘッドの確定構成 | `experiments/phase1/stage1_ptower_r3/selection.json`。COCO C/8/0.30/30、ImageNet B/8/0.00/30、lr 1e-4 |
| 三周目の確定塔の checkpoint と特徴 | 14 本とも efros に在る（送り手の差の計算に使用） |

### A-4 物理 batch と累積

決定性設定下、短辺 800（1422×800）、COCO 初期化、装置 47.4 GiB:

| batch | peak allocated | peak reserved | sec/iter | frames/s | 状態 |
|---|---|---|---|---|---|
| 32 | — | — | — | — | OOM |
| 16 | 26.97 GiB | 31.80 GiB | 1.124 | 14.2 | OK |

**物理 batch 16 × 勾配累積 4 = 実効 64**（三周目と同じ組）。ilya は 20.9 frames/s。

### A-5 占位の差し替え

| 項目 | 実測値 |
|---|---|
| `contract.conventions_rev` | `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6` |
| `meta.created_from.runindex_commit` | `2fb7c905b51aac5ec2b0ee5fe5c70e835f4024a8` |

`created_from.counts` は「起票時」の値なので差し替えていない（三周目と同じ扱い）。

## 2. Task B — 追加 5 動画の manifest

`scripts/build_phase_manifest_p20.py` → `data/processed/stage1_features/p20_manifest/`。15 動画の manifest は写すだけで変えず、
追加 20 clip（10,461 フレーム）を `train.json` にだけ足した。train は 9,657 → 20,118 フレーム（折り A の train 動画）。

| 動画 | clip（注釈 = 画像） |
|---|---|
| 17 | 17_1 56 |
| 18 | 18_1 388 / 18_2 558 |
| 19 | 19_1 1,364 / 19_2 437 / 19_3 1,245 / 19_4 106 / 19_5 561 / 19_6 1,466 |
| 20 | 20_2 473 / 20_4 414 / 20_5 335 / 20_6 278 / 20_7 20 / 20_8 40 |
| 21 | 21_1 69 / 21_2 464 / 21_3 862 / 21_4 1,122 / 21_5 203 |

工程ラベルは 9 語彙の内側（anesthesia 140 / closure 2,255 / design 428 / disinfection 115 / dissection 6,411 / dressing 196 /
hemostasis 329 / incision 332 / irrigation 255）。

### 動画 19 の破損

最初の manifest は数の照合だけで通った。P\*-20 の一本目が epoch 1 の途中で
`OSError: image file is truncated` で落ち、全数をデコードすると 1,932 枚（19_3 の 0645〜1488 の 737 枚、19_4 の 99、19_5 の 481、
19_6 の 615）が **すべて 262,144 バイト**で切れていた。`data/eval_staging/.../other(17~21)/19/` の写しも同じ 1,932 枚が壊れていた。
契約が `data/raw` への書き込みを禁じるため実行者は直さず、利用者が再送した。一度目の再送は 19 全体を消したあと途中で止まり
（3,618 / 5,179 枚、19_1・19_2・19_3 の前半が欠け）、二度目で揃った。

**manifest の生成に全数デコードを足した**（`undecodable`）。最終の生成で 10,461 枚すべてがデコードでき、20 clip すべてで
注釈のフレーム集合と画像のフレーム集合が一致した。

### 集合差の照合（完了判定 a）

`verify_folds` が 5 折りすべてで「train に増えたのは 17〜21 だけ、val・test は不変、22 は無い」を確かめた。

| 折り | train（P\*-20） | val | test |
|---|---|---|---|
| A | 15 動画 | 09 10 | 04 05 07 |
| B〜E | 15 動画 | 規約の表どおり | 規約の表どおり |

## 3. Task C — ホスト差の対照

規則は結果を見る前に `experiments/phase1/stage1_ptower_20/host_control_rule.json` へ固定した（2026-10-02T18:00:09Z）。
基準は ilya の `stage1_ptower_r3_059_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42`（val J 0.7066）。
閾値は三周目の折り A の 3 seed（0.7066 / 0.6884 / 0.7255）の標本 SD 0.0186 × 2 = 0.0372（母 SD 0.0152 も併記）。

| run | 実測 |
|---|---|
| fine-tune `_005_` | 最良 epoch 13、低下 17、打ち切り 21、val acc 0.8607、フレーム単位 val J 0.6523、16,076 秒、最大 27.06 GiB |
| 特徴抽出 `_008_` | 366 秒 |
| 時間ヘッド `_009_` | val J **0.7762**、val acc 0.8713、最良 epoch 8、終了 18 |

差 +0.0696 > 0.0372。**G2 不合格**。諮って「差を記録して続行」の決定を得た（2026-10-03）。

### 中断した run

| フォルダ | 設定 | 理由 |
|---|---|---|
| `_001_` | P15 対照 | 実行者が Bash の `run_in_background` で起こし、30 分の上限で子プロセスごと止まった（2 epoch） |
| `_003_` | P15 対照 | cgroup の OOM（10 epoch） |

いずれも metrics.json が空で、再開判定は完了と見なさない。再起動後の一本目と二本目で epoch 1・2 の loss と val acc が
小数第 6 位まで一致した（決定性）。

## 4. Task D — P\*-20 の学習

### OOM と pinned メモリ

| フォルダ | 設定 | 理由 |
|---|---|---|
| `_002_` | P20 COCO A 42 | 動画 19 の切れた画像で OSError |
| `_004_` | P20 COCO A 42 | cgroup の OOM（対照と同時） |
| `_006_` | P20 COCO A 42 | 実行者が止めた（下記） |

efros の cgroup `memory.max` は 55,834,574,848 bytes（52 GiB）、`memory.events` の oom_kill は 3。30 秒ごとの記録で、
P\*-20 の一本目は epoch 1 の終わり（checkpoint 書き込み 21:43:30）に親プロセスが 3.2 → 23.8 GiB に跳ねた。中身は
`/dev/zero` の共有マップ 256 MiB × 91 塊（val のバッチ数 95 に近い）。PyTorch 2.1 の pinned メモリのキャッシュで、
塊を OS に返さない。次の epoch の境界で 52 GiB を超え対照を巻き込む恐れがあったため `_006_` を止めた。

学習なしの再現（GPU 1、折り A の val）:

| 指定 | 塊の数 | 所要 | logits の要約値 |
|---|---|---|---|
| pin_memory=True | 8（別の回では 95） | 33.6 秒 | `f17d30ee416afe91` |
| pin_memory=False | 0 | 36.3 秒 | `f17d30ee416afe91` |

P\*-20 の設定だけ `pin_memory: false`。以後 2 本並べても全体 15〜16 GiB で安定し、oom_kill は 3 のまま。

### fine-tune 14 本

| 系統 | 折り | seed | 時間 | epoch | 最良 | 低下 | 打切 | val acc |
|---|---|---|---|---|---|---|---|---|
| coco | A | 42 | 6.15 | 14 | 6 | 10 | 14 | 0.8785 |
| coco | A | 123 | 4.84 | 11 | 3 | 7 | 11 | 0.8937 |
| coco | A | 456 | 6.25 | 14 | 6 | 10 | 14 | 0.8944 |
| coco | B | 42 | 5.78 | 13 | 9 | 5 | 13 | 0.7641 |
| coco | C | 42 | **8.56** | 18 | 10 | 14 | 18 | 0.7837 |
| coco | D | 42 | 6.45 | 14 | 10 | 9 | 14 | 0.7768 |
| coco | E | 42 | 6.30 | 13 | 9 | 6 | 13 | 0.8738 |
| imagenet | A | 42 | 6.18 | 14 | 10 | 6 | 14 | 0.8825 |
| imagenet | A | 123 | 6.27 | 14 | 10 | 7 | 14 | 0.8944 |
| imagenet | A | 456 | 7.94 | 18 | 10 | 14 | 18 | 0.8904 |
| imagenet | B | 42 | 4.06 | 9 | 1 | 5 | 9 | 0.7560 |
| imagenet | C | 42 | 6.57 | 14 | 10 | 6 | 14 | 0.7837 |
| imagenet | D | 42 | 6.54 | 14 | 10 | 9 | 14 | 0.7874 |
| imagenet | E | 42 | **8.11** | 17 | 13 | 12 | 17 | 0.8536 |

合計 90.0 GPU 時間。上限 36 への張り付き 0/14、低下 14/14、打ち切り 14/14。記憶領域の最大は全 run 27.06 GiB。
8 時間超の 2 本は利用者の承認済み（2026-10-03）。

### 特徴抽出と決定性

14 本。`p20_coco_lr0.0001_foldA_seed42` で `verify_determinism` を立て、二度の抽出が `233b14ca…` で一致、`conv1.weight` を 0 に
すると変わった（weight_change_detected: true）。各キャッシュの動画別フレーム数は manifest と一致（20 動画、17〜21 を含む）。

### 時間ヘッド 14 本

各系統の三周目の確定構成のみ（COCO C/8/0.30/30、ImageNet B/8/0.00/30）。1 本 12〜33 秒。

## 5. Task E

- 並置: `validation_runs.csv`（15 行）、`validation_summary.json`。`docs/stage1/ptower_20.md` に表
- test: 10 回（`test_<系統>_<折り>.json`、`test_access_*.json` 10 件 completed）。各ファイルに P\*-15 の同じ折りの test 値を並置
- 送り手の差: `sender_gap.csv`（20 行）。各行で、run の config に刻まれた train 動画と使った train 動画の一致を assert。
  gap で計算した val J は学習時の val J と最大差 0

## 6. 判断の記録

`tasks/inbox.d/T-2026-09-27-stage1-ptower-20.md`。G2 不合格を記録して続行、8 時間超の承認、pinned メモリの OOM、動画 19 の破損。
