# 結果 — T-2026-10-17-tower-reselect-prereq

andrew で、検出塔の二周目の収束規則と設定を動かせる状態に戻し、評価時の入力の大きさを前処理だけで実測し、
規約に二つの決定を置いた。装置は使っていない。命令と出力は `audit.md`（以下「audit NNN」は行番号）。

**status: pass。** efros の実体は二周目の写しと要約値・行の両方で一致し、andrew に戻した後で収束規則の試験は
9 件収集・9 件 PASS。変えてはいけない 19 ファイルは前後で一致。評価時の入力は原寸 1920×1080 から
**縮小後 1333×749、pad 後 1344×768**（W×H）で、これまでの計算値 1333×750 とは縮小後の高さが 1 違う。

## 1. 解決された参照

| 記載 | 解決先 |
|---|---|
| `contract.inject_verbatim` | `context/conventions.md`（`073f9dc0`）の prohibitions / issuer_cautions / env_p0 / symmetry を原文のまま適用（audit 44） |
| `contract.conventions_rev` | 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`（起票時と一致） |
| `meta.created_from` | runindex `63ae65da8c7d32df591f5e2ee4358286b72c726b`、1961 / 750 / 1506（一致。差し替え不要。audit 72） |
| `governance.decisions_required` | 利用者の回答を `meta.amendments` に記録して空にした（audit 32）。**2 件とも発火しなかった** |
| `inputs.frozen_source` | 契約に無し。凍結源は `conventions#frozen_source` の正本 `03936318…` と一致（audit 114） |

## 2. 関門

| 関門 | 判定 | 実測 |
|---|---|---|
| G1（A の後） | **pass** | 分岐 `feat/tower-reselect-prereq`、HEAD = `origin/phase0` = `31af81e7`、装置の開始時の状態、失敗 6 件と収集エラー 1 件の名前を記録（audit 51-100） |
| G2（C の後） | **pass** | efros に直接届き、`util/convergence.py` の sha256 が写しと一致、`main.py` が写しの抜粋 23 + 61 行を行番号ごと含む（audit 177） |
| G3（D の後） | **pass** | 収束規則の試験 9/9 PASS。ext 5・ckpt 12・weights 2 の要約値が前後で一致（audit 253-286） |

## 3. 完了判定

| # | 判定 | 結果 | 実測 | 空振りでないことの確認 |
|---|---|---|---|---|
| a | 収束規則の実装と設定が andrew に在る | 達成 | andrew の `util/convergence.py` = `299597a2…` = 写し。`main.py` は抜粋 23/23・61/61 一致。D\*-COCO の設定 `train_config_egosurgery_seed42.py` は在り、二周目の命令行と設定を検出器の環境で解釈できた | 1 文字変えた写しで sha 不一致、抜粋 22/23（rc=1）。変更前の `main.py` に抜粋を当てると 0/61（audit 186-195） |
| b | 取り寄せ元 | 達成 | 比較元 = 写し `experiments/baselines/stage1_dtower_r2/impl/`、比較先 = efros `~/slocal2/m2/third_party/Relation-DETR/`（HEAD `b485955c`）。sha と行が一致 | 同上。efros で使った操作はすべて読むだけ（audit 158-175） |
| c | 上書きと追加の一覧 | 達成 | 上書き 1（`main.py` `6c14063a…` → `ffbd6deb…`）、追加 4。退避先 `~/m2-evacuated/T-2026-10-17-tower-reselect-prereq/third_party/Relation-DETR/main.py` | 前の値は Task B で先に取った。退避した版の sha256 = 前の値（audit 236-251） |
| d | 変えてはいけないものの不変 | 達成 | 拡張の生成物 5、checkpoints 12（凍結源を含む）、COCO 初期化の重み 2 の計 19 件が前後で一致 | 同じ道具が src では `main.py` の変化と追加 4 件を検出した。凍結源は正本とも一致（audit 600-） |
| e | 試験 | 達成 | 収束規則の試験 9 件収集・9 件 PASS。全体は 6 failed / 802 passed / error 0。失敗の名前の集合は前後で同じ 6 件 | 開始時は同じ試験が収集エラー（`util/convergence.py` が無い）。802 = 793 + 9（audit 80-100、392-398） |
| f | 新しい snapshot | 達成 | `third_party_snapshot/efros/2026-10-17/Relation-DETR/`（patch 4 件、tarball 35 件、一覧、sha256 39 件、出所、2026-08-02 版との差）。差は追加 4・変更 1 | 既存の snapshot 65 件の sha が前後で一致。repo の tarball を展開した一覧 = `tar_contents.txt`、組み立てた木が sha 39 件に一致、1 文字変えると FAILED（audit 197-232） |
| g | 評価時の入力の大きさ | 達成 | 原寸 (H,W) = (1080,1920)（注釈 21 ファイル延べ 108,059 枚すべて）→ 縮小後 (749,1333)、pad 後 (768,1344)。val の 3 枚で実測 | 陽性: (1080,1080)→800×800、(1920,1080)→(1333,749)/(1344,768)、(480,640)→(800,1066)/(800,1088)。陰性: 同じ入力を二度通してテンソル同一（audit 305-335） |
| h | 規約 symmetry | 達成 | 理由 3、使える比較・行・条件、使えない行、変種への不適用、理由の欄の書き方、出所 | SPEC §5.1 の 10 項と規約の行を一行ずつ突き合わせた（audit 339-357） |
| i | 規約 frame_sets | 達成 | 用途の表 5 行、規則 4 項、変更履歴の行 | 数 17,233 / 15,437 / 1,796 が `REPORT.md:14,15,22,43` と一致。アンカーが `validate_task` で引ける（audit 358-366） |
| j | 装置・efros・data | 達成 | 装置の使用 0、efros への書き込み 0、`data/` への書き込み 0 | 装置は開始時と終了時の二回（同じ他プロセス 2 件だけ、exe と argv0 の完全一致 0）。efros の操作の一覧（audit 61-70、158-175、400-412） |
| k | PR | 達成 | PR #229、base `phase0`、head `feat/tower-reselect-prereq`、draft false、OPEN | `gh pr view --json number,isDraft,baseRefName,headRefName,state` の実測 |

## 4. 実測（次の契約で使う値）

| 項目 | 値 |
|---|---|
| 評価時の入力の大きさ（W×H） | 原寸 1920×1080 → 縮小後 **1333×749** → pad 後 **1344×768**。`REPORT.md:200` の 1333×750 は丸めの違い（実装は `.to(int)` で切り捨て、`base_detector.py:49-50`） |
| 評価時の前処理 | `EvalResize(800, 1333)` → float 化 → ImageNet 正規化 → 32 の倍数へ右下を 0 で pad。`presets.detr`（学習時の多尺度）は `train_dataset` だけ |
| andrew の検出器 | `/home/ubuntu/slocal2/m2/third_party/Relation-DETR/`（git 作業ツリー、上流 `b485955c`）。環境は `.venv-relation-detr` |
| 拡張の生成物 | `~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/`（JIT。`torch.cuda.is_available()` が真のときだけ読み込む） |
| 新しい snapshot | `third_party_snapshot/efros/2026-10-17/Relation-DETR/`。`bash scripts/restore_relation_detr_source.sh efros/2026-10-17 <dest>` で指定できる |
| 2026-08-02 版との差 | 追加 `util/convergence.py`、`configs/train_config_egosurgery_stage1_imagenet_seed{42,123,456}.py`。変更 `main.py`（CRLF→LF を除いて 72 行） |
| 収束規則の引数 | `--convergence-schedule`（store_true）、`--plateau-patience`（既定 4）、`--plateau-factor`（既定 0.1）、`--max-epochs`（既定 None = config の 12） |
| 二周目の D\*-COCO の起動 | `EGO_ANN_DIR=<折りの注釈>` `RELDETR_OUTPUT_DIR=<出力>`、`accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36` |
| 試験 | 6 failed / 802 passed（失敗は以前からの 6 件） |

## 5. 起票者の誤り

| 型 | 内容 |
|---|---|
| asserted_without_measuring | §3 は「直接接続は不可で中継が要る（中心は philip）」と書くが、andrew から efros:50072 へ直接届いた。従うと不要な中継を組むことになる（audit 150-156） |
| asserted_without_measuring | Task D-4 は「検出器の専用の環境で試験が収集され全件通る」を求めるが、`.venv-relation-detr` に pytest が無い。従うと依存の追加が要る。本体 `.venv` で回した |

## 6. 逸脱

- 収束規則の試験は本体 `.venv` の pytest で回した（検出器の環境に pytest が無く、依存の追加は無断で行えないため）。試験は torch を import しない。検出器の環境では `main.py --help`、引数の解析、設定の解釈を行った
- Python の処理の一部（`accelerate` の import の確認、注釈 json の読み取り、`make` の検査道具）は `CUDA_VISIBLE_DEVICES=""` を付けずに動かした。いずれも装置を使う処理ではなく、終了時の装置の状態に本契約の処理は無い。検出器の処理はすべて装置を隠した
- andrew に置くものとして、D\*-COCO に要るもの（`convergence.py`、`main.py`）に加え、二周目の D\*-ImageNet の設定 3 件も置いた。追加だけで既存を変えず、andrew を efros と同じ版にするため
- 新しい snapshot は `per_class_coco_map` の json を含めない（SPEC C-4 の「評価の出力の json」）。2026-08-02 版は 12 件を含めていた
- 開始時の試験は素の pytest が収集エラーで全体を中断したため、前後とも `--continue-on-collection-errors` を付けて測った
- efros への命令のうち 2 回は手元のシェルの誤り（zsh の単語分割、ssh が heredoc を読む）で一部が実行されなかった。記録に残した（audit 158-175）。efros への書き込みは無い

## 7. 想定外・UNKNOWN

- `context/env-facts.md` の「直接接続は不可能」が何を指すかは確かめていない。andrew → efros は直接届いた
- SPEC §5.2 の「追加動画 17〜21」と `conventions#folds` の「追加 6 動画 17〜22」が食い違う。規約には SPEC の文言どおりに置いた。動画 22 を Stage 2 の主測定から外すかは文言からは読めない
- 評価時の大きさは前処理だけで測った。モデルの forward の中の特徴の大きさ（168×96 など）は計算値のままである
- 検出塔の学習（逆伝播を含む）は andrew で流していない（本契約は学習しない）

## 8. 送出

| 項目 | 値 |
|---|---|
| PR | #229（base `phase0`、draft false）https://github.com/takuya3h/m2/pull/229 |
| commit | `2da88a8f`（本体）、続く 1 件（規約の変更履歴の commit の欄と本報告の PR 番号の記入） |
| 台帳 `make task-report` | 終了コードは inbox.d と最後の応答に記す |
