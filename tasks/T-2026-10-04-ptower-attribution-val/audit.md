# audit — T-2026-10-04-ptower-attribution-val

実行ホスト dlsta（容器内のホスト名 `4f3861ae8d3b`、RTX A5000 × 5）。時刻は記載のない限り UTC。
RESULT.md からはこのファイルを節番号で指す。

## §1 開始状態（Task A-1〜A-3）

- 開始時の分岐 `feat/dlsta-host-fairness`（指示は phase0）。`origin/phase0` に対し ahead 0 / behind 31 で、
  未合流 commit は無かった。ローカル `phase0` は `origin/phase0` に対し ahead 0 / behind 44
- `git checkout phase0 && git merge --ff-only origin/phase0` → `331525e807279578a1bc3f0cea639932be000d6a`
- `make task-start` が `feat/ptower-attribution-val` を起点 `origin/phase0`（`331525e8`）で作成。分岐名は `feat/` で始まる
- 開始前から在った未 commit の変更 4 件（すべて `docs/sessions/digest/`）
  - 未追跡 3 件 → `mv` で scratchpad の `digest_moved/` へ退避（消していない）
    - `2026-09-25-a4eacf2b-24c0-4b75-8ad4-521aeeac3349.md`
    - `2026-09-25-c761ab38-cd6a-4c0b-9d04-5ebcac86fc2a.md`
    - `2026-10-03-08-16-04-01a100d5-a782-7043-b69e-a18be0a6c0ef.md`
  - 追跡済みの変更 1 件 `2026-09-20-1764ac44-ef2b-4d0b-bdb2-14bf9279f259.md` → `git stash push -m "pre-task digest 2026-09-20"`
  - 4 件の写しを scratchpad の `digest_backup/` にも取った。報告の後に元へ戻す
- `.sync-pause` は開始前から在った（`2026-09-22 09:03` 作成、0 バイト）。`make task-start` の出力
  「.sync-pause は実行前から存在するため触れません」。`~/bin/m2-sync.sh` の `sync-pause` 出現 2 行（対応版）
- `make task-validate`: exit 0、WARN `[L2-6] conventions.md が e7a51005 以降に変更`。利用者に提示し「現行版で続行」の回答を得た
- `make task-preflight`: exit 0。`6 PASS / 0 WARN / 8 SKIP / 0 FAIL`。
  SKIP: P2 cuda_ext_loaded、P3 deterministic_flags、P4 prereg_committed、P5 frozen_source_hash、P11 gpu_free、P12 refs_resolved、P13 symmetry_table_complete、P14 proposal_card_checked。P9 spec_lint は該当なし

## §2 装置（Task A-4）

`nvidia-smi`（2026-10-05 01:4x UTC）: GPU0 4397 MiB 使用・使用率 100%、GPU1〜4 は 22 MiB・0%。
`--query-compute-apps` は 0 行（容器の外のプロセスは見えない）。`/proc/PID/exe` で解決できるプロセスが無いため、
**GPU0 は他の利用者の処理が載っているものとして使わない。** 使うのは GPU1〜4。

## §3 参照の解決

- `contract.conventions_rev`: 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`（`context/conventions.md` を最後に変えた commit、2026-10-02）。
  契約の `e7a51005` の時点では注入対象の `det_groups` 節は存在しなかった（`001b4309` で追加）
- `meta.created_from.runindex_commit`: 実測 `2fb7c905b51aac5ec2b0ee5fe5c70e835f4024a8`（`runindex/` を最後に変えた commit、2026-09-29）
- 塔の入口: `scripts/stage1_ptower_r3.py`（run の `command.sh` に記録。契約の `entrypoints` は一周目と二周目のもの）
- 確定構成（`tasks/T-2026-09-19-stage1-phase-tower-r3/RESULT.md` §4）
  - COCO 系: 候補 C（TeCNO 2 段）/ 8 層 / 平滑 0.30 / 履歴 30（候補 C では使われない）/ ft lr 1e-4
  - ImageNet 系: 候補 B（TeCNO 2 段 + 因果の局所 Transformer、履歴 30）/ 8 層 / 平滑 0 / ft lr 1e-4
  - 入力: 短辺 800 の全画面（1920×1080 → 800×1422）、ImageNet の平均と標準偏差で正規化、layer4 の空間格子 25×45、GAP で 2048 次元
- 受容野（実装 `src/egosurgery/models/heads/tecno_head.py` から）: 1 段 = 2·Σ_{i<8} 2^i = 510 フレーム遡る。2 段で 1020。
  **候補 C は現フレームを含め 1021 フレーム**（記録の `receptive_field = 1+4·(2^L−1)` と一致）。
  **候補 B は注意の窓 30（距離 0〜29）が加わり 1050 フレーム**

## §4 対象の動画と折り（Task A-5）

`docs/stage0/A1_fold_table.md`（`conventions#folds` の正本）。公式 test は `data/splits/ego_test.txt` = {04, 05, 07}。

| 折り | val | 対象 | 塔 |
|---|---|---|---|
| A | 09, 10 | 09, 10 | 折り A |
| B | 02, 08 | 02, 08 | 折り B |
| C | 06, 12 | 06, 12 | 折り C |
| D | 04, 05 | なし | 使わない |
| E | 07, 15 | 15 | 折り E |

対象 = ⋃ val − 公式 test = {02, 06, 08, 09, 10, 12, 15}。対象 ∩ 公式 test = ∅（後で `scripts/ptower_attribution.py` の検査で集合演算として再掲）。

## §5 材料（Task A-6〜A-10）

探索は二通りで行った: (1) `experiments/` の `config.yaml` に契約 `T-2026-09-19-stage1-phase-tower-r3` を含むものを `grep -rl`（339 件）、
(2) `find experiments -path '*r3*'` で `.pt/.pth/.ckpt/.safetensors`（先頭がドットのものを含む `find`）。
`runindex/index.csv` にも同契約の行が 339 件ある。同期の途中の兆候（`.sync-conflict`、部分ファイル）は見なかった。

**折り A・B・C・E の両系統で、塔・特徴キャッシュ・画像・工程 GT・術具と手の枠の GT がすべて実在した。欠けた折りは無い。** 折り D は対象動画が無い。

| 折り | 系統 | 時間ヘッドの run | backbone の checkpoint（sha256 先頭 16） | 時間ヘッド（同） | 特徴キャッシュ（同） | 記録の val J / acc |
|---|---|---|---|---|---|---|
| A | coco | `stage1_ptower_r3_059_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42` | `stage1_ptower_r3_005_ft_coco_lr0.0001_foldA_seed42` `a90cf04de88fcd02` | `06385c663d908b59` | `aa4aa85e81d5bd39` | 0.7065837936961685 / 0.8415841584158416 |
| A | imagenet | `stage1_ptower_r3_131_P15_B_L8_w0.0_h30_foldA_imagenet_lr0.0001_seed42` | `stage1_ptower_r3_015_ft_imagenet_lr0.0001_foldA_seed42` `cad8b038c087e1d5` | `692f04a7c17e17b5` | `76470451b09ba86a` | 0.6578040565914204 / 0.858085808580858 |
| B | coco | `stage1_ptower_r3_074_P15_C_L8_w0.3_h30_foldB_coco_lr0.0001_seed42` | `stage1_ptower_r3_008_ft_coco_lr0.0001_foldB_seed42` `835d556855a4cd8c` | `bedcdcfe551f2afc` | `a063d9755cb23cd9` | 0.6717981995781513 / 0.84631918323482 |
| B | imagenet | `stage1_ptower_r3_146_P15_B_L8_w0.0_h30_foldB_imagenet_lr0.0001_seed42` | `stage1_ptower_r3_017_ft_imagenet_lr0.0001_foldB_seed42` `a38cde5322ab15ee` | `110c686e674771e4` | `fe1ef313d83c2a49` | 0.3584194967660744 / 0.7291778613648576 |
| C | coco | `stage1_ptower_r3_080_P15_C_L8_w0.3_h30_foldC_coco_lr0.0001_seed42` | `stage1_ptower_r3_009_ft_coco_lr0.0001_foldC_seed42` `7d74bf37bd4c4138` | `ff423ba336fe818d` | `60fe83727e99610f` | 0.6094239362074261 / 0.7821931589537223 |
| C | imagenet | `stage1_ptower_r3_151_P15_B_L8_w0.0_h30_foldC_imagenet_lr0.0001_seed42` | `stage1_ptower_r3_020_ft_imagenet_lr0.0001_foldC_seed42` `8f9818e54bbd3f89` | `ffbc2260d3b89aff` | `9b475ce29de7e519` | 0.4304956698012248 / 0.7947686116700201 |
| E | coco | `stage1_ptower_r3_090_P15_C_L8_w0.3_h30_foldE_coco_lr0.0001_seed42` | `stage1_ptower_r3_011_ft_coco_lr0.0001_foldE_seed42` `342e8dfaae15ba05` | `18e89377453e9006` | `51f27d767abfedc9` | 0.6757300829844042 / 0.8916001877053027 |
| E | imagenet | `stage1_ptower_r3_161_P15_B_L8_w0.0_h30_foldE_imagenet_lr0.0001_seed42` | `stage1_ptower_r3_022_ft_imagenet_lr0.0001_foldE_seed42` `7b4dedaca0396ccd` | `aca07a136fa4144c` | `f67075f3fdc49b44` | 0.5541974275812928 / 0.8305959643359925 |

- backbone は特徴抽出の run の `config.yaml` の `checkpoint` が指すもの（折り A COCO は `_005_`。同名の `_004_` もあるが使われていない）
- 時間ヘッドの記録の指標は val の 2 動画をまとめた値だけで、動画ごとの値は無い（`metrics.json`、`per_class_ap.json`、`predictions/` は空）
- 画像は `data/raw/ego/{train,val}/<動画>/`、工程 GT は `data/processed/phase_manifest/{train,val}.json`（`test.json` は開いていない）。
  術具と手の枠は `data/annotations/egosurgery_tool_hand/instances_{val,train}.json`（`instances_test.json` は開いていない）。
  動画ごとのフレーム数はマニフェストと枠の注釈の画像数が一致: 02 461 / 06 1379 / 08 1400 / 09 518 / 10 997 / 12 609 / 15 420（計 5784）。
  枠の数 02 2449 / 06 8850 / 08 6974 / 09 3008 / 10 6617 / 12 4676 / 15 3252（計 35826。手の枠は七動画すべてに在る）
- 特徴キャッシュは非圧縮の `np.savez`。`features.npy` の位置を zip の局所見出しから求め、**対象の行だけを memmap で読んだ**（test の行を配列にしていない）
- 既存の道具: `/home/ubuntu/local/phase_cam_dlsta_20261003/`（418,220,737 バイト）。`tools/visualize_phase_cam.py`（地図）と
  `outputs/bulk_analysis/analyze.py`（枠の照合）。要約値は §8 の前後の照合に含めた。`summary.json` の値は §3.3 と一致
  （1515 フレーム、9625 枠、正解 1275 / 1300、術具の内 0.7341 / 0.5349、差の最大 4.17e-06、正の地図なし 0）
- 記憶領域の空き（`df -B1`）: `/` 790,415,720,448 バイト、`/home/ubuntu/local` 4,476,089,311,232 バイト。
  大きな中間物の置き場は **repo の外** `/home/ubuntu/local/ptower_attribution_20261005/`
- 変更前の要約値: 塔・特徴の run の全ファイル、backbone の run の全ファイル、特徴キャッシュと監査 JSON、既存の道具の全ファイル、計 9652 件。
  全体の要約値 `726ed88e4430f7e6feb7b6bc3bf64c678287c14e90a006836025ad8ac0f5b5b4`

## §6 計算の前に決めた規則（完了判定 i）

**記録時刻: 2026-10-05T01:52:20Z（ファイルの mtime 実測）。この時点で地図・遮蔽・寄与の計算は一件も始めていない。**

### 6.1 Task D の隠し方

- 前処理（短辺 800 へ縮小、正規化）を済ませた入力の画素を **0 に置く**。0 は正規化後の値なので、
  元の画素では ImageNet の平均色（RGB 0.485, 0.456, 0.406）にあたる。学習時の正規化と同じ平均を使うため、
  入力の分布の中心から外れた値（黒や白）を持ち込まない
- 領域は元の解像度 1920×1080 の枠から作り、最近傍で 800×1422 へ縮める。面積は元の解像度で数える
- 面積を揃えた対照: 対象の領域の 2 値地図を、画像の上で巡回させて（上下左右を巻き戻す）ずらす。面積は構成上一致する。
  ずらし量は種 `20261005 + フレームの通し番号` の乱数で 64 通り引き、すべての枠の和集合との重なりが最小のものを採る。
  重なりの割合（対照の面積に占める、枠の和集合と重なる面積）を全件で記録する。
  **重なりが 5% を超える対照は「無関係な位置が取れない」として数え、集計では除いた値と含めた値を並べる**

### 6.2 Task E の入れ替え

- 入れ替える先の特徴は 2 通り。**主: 現フレームの特徴の複写**（過去を現フレームと同じ絵で置き換える）。**副: 零ベクトル**
- 範囲の形: 直近から順に k フレーム（t−k〜t−1）を入れ替える。k ∈ {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 全部}。
  「全部」が「現フレームより前をすべて入れ替える」にあたる
- 勾配に基づく寄与: 特徴キャッシュの系列で、時刻 t の点数（softmax の前）の勾配と特徴の要素ごとの積を取り、
  各時刻について正の項の和と負の項の和を別に保存する
- 対照（完了判定 h）: 受容野の外（遅れ ≥ 受容野）をすべて零に入れ替えて点数の変化の最大絶対値を取る。
  受容野の内側の直前（遅れ 1）を零にすると変わることを同じフレームで確かめる。対象は受容野より長い動画の、受容野以降の全フレーム

### 6.3 Task E-4 位置の寄与を調べる過去フレームの選び方

- 対象フレーム: 各対象動画の中で、動画内の通し番号 t（0 始まり、`load_fold` と同じ並び）が 100 の倍数かつ 100 以上のもの
- 対象クラス: GT クラス
- 過去フレーム（各対象フレームにつき）
  - 固定の間隔: 遅れ {1, 5, 15, 30, 60}（t − 遅れ ≥ 0 のもの）
  - 寄与の大きいもの: §6.2 の勾配に基づく寄与（GT クラス、正の項の和）が大きい順に 3 つ。遅れ 1 以上、受容野の内側。同点は遅れの小さい方
  - 両方に入る遅れは一度だけ計算し、両方の印を付ける
- 地図は §4 の定義（既存の道具と同じ Grad-CAM）を、過去フレーム τ の layer4 に対し時刻 t の点数で取る。照合する枠は τ 自身の枠

### 6.4 代表図の選び方（Task F-3）

**記録時刻はこの節を書いた時点（下の `date` 出力）。図はまだ一枚も作っていない。**

- 図 1: 両系統とも正解かつ標的群の術具が写るフレームのうち、COCO 系の GT クラスの地図の術具の枠の内側の寄与率が、
  COCO 系の全フレーム平均に最も近いもの（同点は動画・フレーム番号の昇順で先）
- 図 2: GT が hemostasis で Bipolar Forceps が写り、両系統とも dissection と予測したフレームのうち、
  同じ寄与率が、その部分集合の COCO 系の平均に最も近いもの
- 各図は 1 枚に 3 面（元画像に GT 枠、COCO 系の GT クラスの地図、ImageNet 系の GT クラスの地図）。地図は各面で最大値正規化。
  幅 960 の JPEG で `experiments/analysis/ptower_attribution/figures/` に置く
2026-10-05T04:45:24Z

## §7 実行の記録（Task B〜F）

すべて `CUDA_VISIBLE_DEVICES` で GPU1〜4 のいずれかを指定し、`PYTHONPATH=src .venv/bin/python` で実行した。
決定性の設定は `stage1_ptower.deterministic(42)`（TF32 無効、決定的アルゴリズム）。W&B は使っていない。

| 時刻（UTC） | 命令 | 出力の要点 |
|---|---|---|
| 01:56 | `scripts/ptower_attribution.py baseline`（GPU1） | 折り A・B・C の両系統で記録の val J と acc が全桁一致。折り E は 15 だけで J 0.7040 / 0.5589（記録は 07 と合わせた値で比較不能 = UNKNOWN）。対照: 折り B の COCO 塔を 09・10 に当てて J 0.9640 / acc 0.9848（記録 0.7066 と不一致）|
| 01:58 | 一フレームの差し替え（09 の位置 100 に位置 300 の特徴） | logits の要約値 COCO `cea52f2a…`→`59f80945…`、ImageNet `8a373c8a…`→`4763f77b…`。argmax が変わったフレームは COCO 0、ImageNet 1。J は COCO 不変、ImageNet 0.6578→0.6562 |
| 01:56〜03:54 | `run --fold {A,B,C,E} --chain {coco,imagenet}` | 動画ごとの所要: 02 542〜558 s、06 1802 s（ImageNet）/ 3674 s（COCO）、08 1813〜1825 s、09 628〜630 s、10 1274〜1305 s、12 802 s（ImageNet）、15 507〜676 s。失敗 0 |
| 02:1x〜04:4x | `positional --fold … --chain …` | 地図の数: COCO 02 28 / 06 94 / 08 93 / 09 38 / 10 68 / 12 43 / 15 28（計 392）、ImageNet 02 32 / 06 95 / 08 102 / 09 40 / 10 66 / 12 45 / 15 30（計 410）。印ごとの延べは両系統とも fixed 270 + top 162 |
| 04:43 | `scripts/ptower_attribution_summary.py` | exit 0。`summary.json` と `tables/*.csv` |
| 04:45 | 代表図（§6.4 の規則） | 図 1 `06_1_0881`（候補 1281、COCO 平均 0.71260、当該 0.71276）。図 2 `12_1_0592`（候補 30、部分集合平均 0.53705、当該 0.51913） |

待機の命令の一つが `pgrep -f "ptower_attribution.py run"` で自分自身の命令行に一致し、計算の終了後も止まらなかった
（conventions#issuer_cautions 注意 6 の型。実行者の誤り）。結果には影響しない。`TaskStop` で止めた。

## §8 検証

- 完了判定 a: 対象 {02, 06, 08, 09, 10, 12, 15} ∩ 公式 test {04, 05, 07} = ∅。04 を足すと {04}
- 完了判定 b / k: `reads.jsonl` 27 行。読んだ動画の集合 = 対象の七動画。`reads_outside` の結果は空（`control_b` の 1 行を除く）。
  読み込みの記録へ `{"kind":"run","fold":"A","videos":["04"]}` を足すと `[('run','A','coco','04')]` を返す
- 完了判定 l: 変更後の要約値 9652 件、変更 0・追加 0、全体の要約値 `726ed88e…` で一致。写しの 1 バイトを反転すると要約値が変わる
- 完了判定 d: 「何も隠さない」で予測が変わったフレーム 0（両範囲、両系統、5784×2）。全面を隠すと 14377 件（両範囲・両系統の延べ）
- 完了判定 e: 四領域の寄与率の和と 1 の差の最大 2.44e-15。試験 `test_synthetic_maps_give_one_inside_zero_outside` で内側だけ 1.0、外側だけ 0.0
- 完了判定 f: 組み替えの行数 23136 = 5784 フレーム × 2 系統 × 2 クラス。組み替えは同じ動画の中の固定点の無い置換（種 20261005 + 動画番号）。
  空振りでないことの確認: 15 の 21 フレーム（20 おき）で、組み替えずに同じフレームの枠を当てると、元の寄与率との差の最大は 0（完全一致）
- 完了判定 g: 対照の面積の差は全件 0。試験 `test_rolled_control_keeps_area_and_avoids_boxes` で半分の面積にすると一致しない
- 完了判定 h: 受容野の外を零にした変化の最大 COCO 9.54e-07、ImageNet 1.43e-06。直前の 1 フレームで全フレーム変化、最小 2.40e-03
- 完了判定 j: 折り A の正解数 1275 / 1300（既存報告と一致）。予測クラスの地図の術具の内の平均 0.7340980 / 0.5349167
  （既存 0.7340977 / 0.5349166、差 2.5e-07 / 8.3e-08）。正規化した地図そのものの差の最大 COCO 5.69e-03、ImageNet 1.89e-03。
  二系統を入れ替えると 0.7341 対 0.5349 で一致しない
- 完了判定 n: 変更前 6 failed / 673 passed / 1 error、変更後 6 failed / 681 passed / 1 error。失敗の一覧は同一（`diff` で差なし）。
  `make test` は使わず `python -m pytest -q -p no:cacheprovider --continue-on-collection-errors tests`
- `make forbidden-check BASE=331525e8… TASK=…`: status pass、changed 21、violations 0。TASK を外すと fail。
  BASE を付けないと、分岐の後に `origin/phase0` へ入った PR #199・#200 の `data/README.md` の差が違反に数えられた（実行者の変更ではない）
- `make spec-check TASK=…`: status pass、規則 9 件
- `make taskindex` / `make inbox` は **契約の禁止 5 により実行していない**
- 完了判定 i: 規則の記録 2026-10-05T01:52:20Z（audit.md の mtime）。最初の計算の開始は `reads.jsonl` の初行 01:56:05Z、
  E-4 の地図の計算はそれより後。06・COCO の t=700 で規則を手で当て直すと、寄与の大きい 3 つは遅れ 8, 4, 2、
  固定と合わせた集合 {1, 2, 4, 5, 8, 15, 30, 60} が記録と一致した
- 完了判定 m: 版管理への追加は §10 に記す。全件の地図・全件の画像は repo に置いていない（repo の外の 362,866,001 バイト）
