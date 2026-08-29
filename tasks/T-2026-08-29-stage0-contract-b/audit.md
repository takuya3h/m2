# audit — T-2026-08-29-stage0-contract-b

実行ホスト `lecun` / repo `/home/ubuntu/slocal/m2` / 分岐 `feat/stage0-contract-b`。
GPU は RTX A6000 を 1 枚のみ使用（Phase B）。`data/` へは読み取りのみ。
`runindex/` は `make runindex` による収穫のみ。

命令とその出力を節ごとに置く。RESULT.md からは節番号で指す。

---

## 0. 取り込みの初回失敗（記録）

初回の `make task-start` は **L1 検証で落ちて巻き戻った。**

    [L1-1] inputs.denominator.ref: 'exp:REPLACE-BY-EXECUTOR' does not match ...
    [L1-1] inputs.frozen_source.ref: 'run:REPLACE-BY-EXECUTOR' does not match ...
    [L1-4] inputs.denominator.ref: exp:<experiments.csv の experiment_id 列の完全形> が必要です
    [L1-4] inputs.frozen_source.ref: run:<group>/<run_name> の形式が必要です
    検証に失敗したため tasks/T-2026-08-29-stage0-contract-b を巻き戻しました
    make: *** [Makefile:205: task-start] Error 4

**参照の解決は取り込み後（手順 3）なのに、形式検査は取り込み前に走る。**
`tools/fetch_task.py` に検証を分離する引数は無い（`--src` `--pack` `--notion` のみ）。
巻き戻しは完全だった（分岐なし・作業ツリー 0 件・契約ディレクトリなし）。
利用者が台帳を置き直したのち、二度目の `make task-start` で取り込めた。
**再配布版では `denominator` に実値が入り、`frozen_source` の欄自体が外されていた。**

---

## 1. Step A-1 参照の解決

### 1.1 事前記入値の照合

    runindex 最終変更: 606d875e (Sat Aug 29 07:14:00 2026 +0000)
    conventions 最終変更: a8c07e81
    index.csv 1238 / experiments.csv 273 / verdicts.csv 1458

事前記入値（`606d875e` / 1238 / 273 / 1458 / `a8c07e81`）と**すべて一致。置換不要。**

### 1.2 分母

    experiments.csv での一致: 1 件
      experiment_id = phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
      split = val   n_runs = 17   accuracy_n = 17
      accuracy_mean = 0.8973014948553679
      accuracy_pstd = 0.005917073407586465   accuracy_sstd = 0.006099179663503103

`require` の三条件（`n_seeds >= 3` / `sigma: present` / `split: val`）を満たす。**一意。**

### 1.3 凍結源（欄の追加）

契約 §3 Step A-1 の指示により、実行者が `inputs.frozen_source` を追加した。**逸脱ではない。**

手掛かり 1（`frozen_source_tag == relation_detr_seed42`）は **903 件**に当たり、
**mAP 系の指標を持つ検出 run は 0 件**だった。これらは凍結源を**使う側**の run である。

手掛かり 2（凍結 ckpt の経路）から候補を絞った。索引で mAP を持ち `relation` を含む
seed42 の run は次の 3 件。

| run | step | mAP | 実体 |
|---|---|---|---|
| `baselines/s0_016_relationdetr_bbox_seed42` | `s0` | 0.729749 | **Relation-DETR seed42 完走**（COCO 1x 重みから 91→15 で再初期化して学習） |
| `baselines/s0_frozen_001_relationdetr_s0frozen_cocohead_seed42` | `s0_frozen` | 0.710008 | 派生 init から学習した**下流** |
| `baselines/s0_frozen_004_relationdetr_s0frozen_neck_cocohead_seed42` | `s0_frozen` | 0.715881 | 同上 |

下流である根拠（`s0_frozen_001` の notes.md と command.sh）:

    S0-frozen init: Relation-DETR seed42 frozen backbone + COCO-init transformer/head
    (merged checkpoint: .../data/external/weights/relation_detr_s0frozen_init_seed42.pth)
    RELDETR_S0FROZEN_INIT=.../relation_detr_s0frozen_init_seed42.pth

`s0_frozen_*` は**別ファイル（merged init）から学習**しており、凍結源そのものではない。
`configs/stage/s4_phase_baseline.yaml:8-9` も「凍結源（STEP 0-2 で確定, S0-frozen と共有）:
Relation-DETR seed42 **完走** ckpt」と記す。**したがって `s0_016` に一意。**

    inputs.frozen_source:
      ref: "run:baselines/s0_016_relationdetr_bbox_seed42"
      verify: ckpt_sha256

ckpt の照合:

    $ sha256sum third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    conventions#frozen_source の正本: 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    大きさ 195421066 バイト（正本 195421066）  → 一致

なお `verify: ckpt_sha256` は**記録用である。** P5 の実装（`tools/preflight_task.py:213-239`）は
conventions から経路と正本を読むだけで、`inputs.frozen_source.ref` を参照しない。

---

## 2. Step A-2 実装可否の実測

### 2.1 🔴 検出器の実装が無い

    $ ls third_party/
    Relation-DETR  outputs
    $ find third_party/Relation-DETR -type f | wc -l
    12                    ← checkpoints のみ
    $ ls third_party/Relation-DETR/models
    ls: cannot access ...: No such file or directory
    $ ls -d .venv*
    .venv                 ← .venv-relation-detr が無い

`third_party/` は `.gitignore:133` で**全体が版管理外**、submodule も無い
（`.gitmodules` が存在しない）。各ホストで clone する運用である
（`README.md:364-373`、`docs/reproduce_on_new_machine.md:80`）。

これが preflight の P2 FAIL の実体である。

    P2 cuda_ext_loaded FAIL models.bricks.relation_transformer を import できない:
                            ModuleNotFoundError: No module named 'models'

### 2.2 四項目の可否

| # | 項目 | 可否 | 根拠 |
|---|---|---|---|
| B1 | run 型ごとの所要時間 | **可能** | 索引に `elapsed_seconds` を持つ b2a/t1a run は 0 件のため、試走で実測した（§2.4） |
| B2 | 送り手の train/val mAP 差 | 🔴 **不能** | 検出器の実装と venv が無く、評価を実行できない |
| B3 D→P | 参照入力四段 | **三段は既存実装で可能・一段は最小追加** | §2.3 |
| B3 P→D | 参照入力四段 | 🔴 **不能** | 検出塔を W1 で学習できない（同上） |
| B4 | 強い工程塔 | 🔴 **要外部取得** | ImageNet-R50 の重みが無い。`~/.cache/torch/hub/checkpoints/` は `dinov2_vits14_reg4_pretrain.pth` のみ、`data/external/weights/` は検出器の COCO 重みのみ |

材料そのものは在る: 予測段 `data/processed/b2a_detsignal/relation_detr_seed42/`（3 ファイル）、
正解段 `data/processed/oracle_toolpresence/`（3 ファイル）、生画像 224,903 枚、
分割は train 10 / val 2 / test 3 動画。

**利用者の判断により縮退して続行した**（D→P 四段のみ実施。B2・P→D・B4 は不能として報告）。

### 2.3 D→P 四段の作り方

| 段 | 実現 | 可否 |
|---|---|---|
| 空 | `--tool-source oracle --mask-tool-dims 0,...,14` | 既存 |
| 予測 | `--tool-source pred` | 既存 |
| 正解 | `--tool-source oracle` | 既存 |
| 正解 ⊕ 予測 | `--tool-source both`（正解 15d ⊕ 予測 15d = 30d） | **最小追加** |

`--mask-tool-dims` は値を 0 にするだけで**次元を落とさない**
（`scripts/train_b2a.py` の `sig_by_frame[fid][d] = 0.0`）。
したがって空段も入力次元 2063 のままであり、**同一界面・同一容量の対照**として成立する。

追加した経路（W1 の「入力適合層と界面」の範囲。評価規則は一切変更していない）:

- `tool_dim(tool_source)` と `in_dim_of(tool_source, drop_gap)` を新設し、次元の決定を 1 箇所に集約
- `load_clips` に `tool_source == "both"` を追加。正解と予測を frame_id で突き合わせ、
  食い違いがあれば `KeyError` で止める（ダミー補完しない）。連結順は **正解 15 → 予測 15 に固定**
- `--tool-source` の `choices` に `both` を追加
- config / eval_recipe / notes / モデル構築の `IN_DIM` 直参照を実効値へ置換

読み込みだけでの検証（学習しない）:

    段                tool_source  mask       in_dim  先頭clip形状  tool部の非零率
    空                oracle       全15          2063  (518, 2063)  0.0000
    予測               pred         -            2063  (518, 2063)  0.9862
    正解               oracle       -            2063  (518, 2063)  0.1553
    正解⊕予測            both         -            2078  (518, 2078)  0.5708

    both の前半 == oracle : True
    both の後半 == pred   : True
    oracle と pred は別物 : True
    空段の tool 部が全 0 : True
    空段でも次元は 2063 のまま（容量対照）: 2063

`ruff check scripts/train_b2a.py` は I001（import 並び）を 1 件出すが、**HEAD でも同じ 1 件が出る。**
自分の変更由来ではないため直していない（指摘のみ）。

### 2.4 所要時間の試走（B1 の初期値）

証跡を残さない試走（`--no-evidence`）で測った。

    epoch 数   実時間
        5      5.08 s
       10      5.54 s
       20     12.26 s
       50     12.3 s  (tool-source=pred)
       50     26.8 s  (tool-source=both)

起動に約 4.5 秒、1 epoch あたり約 0.4 秒。**契約の見積もり（24h / 29 run ≒ 50 分/run）を
三桁下回る。** G2 の「見積もりの三倍以内」は大きく満たす。

---

## 3. Step A-3 prereg の commit

    $ git commit  （prereg.md / SPEC.md / spec.yaml / inbox.d / train_b2a.py）
    [feat/stage0-contract-b 7b1cff8b] exp(stage0-b): register the prereg and add the paired reference input rung
    $ git --no-pager show -s --format=%cI 7b1cff8b
    2026-08-29T13:52:50+00:00

commit と時刻は SPEC A-3 の指示どおり `spec.yaml` の `prereg` 欄へ記入した
（`prereg.md` 本文は commit 後に書き換えていない。§8 禁止 6）。

再度のプリフライト:

    P4 prereg_committed  PASS 7b1cff8b9e12478bf2638597f385565386d7aed6 committed_at=2026-08-29T13:52:50+00:00
    P5 frozen_source_hash PASS sha256=03936318f9d45ac9...
    RESULT: 7 PASS / 0 WARN / 1 SKIP / 1 FAIL   ← 残る FAIL は P2 のみ

🔴 **P2 は FAIL のまま実行した。** 理由と根拠:

- P2 が見るのは検出器の CUDA 拡張である。**D→P 四段はキャッシュ特徴の上で `.venv` だけで動き、
  Relation-DETR を import しない**（§2.3 の読み込み検証と §2.4 の 50 epoch 完走が実測）
- 検出器を使う B2 と P→D は**そもそも実施していない**（不能として報告）
- 利用者は検出器が無いことを含めて縮退の判断をしている

**契約が使う経路と preflight が見る経路がずれている。** 逸脱として報告する。

---

## 4. Phase B の実行（D→P 四段 × 三 seed = 12 run）

命令の形（12 run すべて同型。`--epochs 50` は `train_b2a.py` の既定）:

    python scripts/train_b2a.py --epochs 50 --seed <42|123|456> \
      --description-override <b2a_refin_{empty,pred,oracle,both}> \
      --task-id T-2026-08-29-stage0-contract-b \
      [--tool-source {pred|oracle|both}] [--mask-tool-dims 0,...,14]

### 4.1 run ごとの結果（val 分割）

| 段 | seed | phase_accuracy | phase_macro_f1 | in_dim | best epoch |
|---|---|---|---|---|---|
| 空 | 42 | 0.9141914191419142 | 0.7203113117644523 | 2063 | 50 |
| 空 | 123 | 0.897029702970297 | 0.688914917959103 | 2063 | 46 |
| 空 | 456 | 0.900990099009901 | 0.7130038820212301 | 2063 | 38 |
| 予測 | 42 | 0.9379537953795379 | 0.7964703147511466 | 2063 | 42 |
| 予測 | 123 | 0.9346534653465347 | 0.7845452728178792 | 2063 | 48 |
| 予測 | 456 | 0.9353135313531353 | 0.7812940437526282 | 2063 | 41 |
| 正解 | 42 | 0.9564356435643564 | 0.8207762300327278 | 2063 | 50 |
| 正解 | 123 | 0.9617161716171617 | 0.8274617813294055 | 2063 | 45 |
| 正解 | 456 | 0.9577557755775578 | 0.8244290508198192 | 2063 | 46 |
| 正解⊕予測 | 42 | 0.9564356435643564 | 0.8198864111066088 | 2078 | 43 |
| 正解⊕予測 | 123 | 0.9623762376237623 | 0.8275472937655582 | 2078 | 45 |
| 正解⊕予測 | 456 | 0.9610561056105611 | 0.828330773279605 | 2078 | 45 |

### 4.2 段ごとの集計（ばらつきは ddof=0。conventions#sigma の既定を継承）

| 段 | 平均 acc | pstd | 空段との差 | 平均 macro_f1 |
|---|---|---|---|---|
| 空 | 0.904070 | 0.007337 | +0.000000 | 0.707410 |
| 予測 | 0.935974 | 0.001426 | **+0.031903** | 0.787437 |
| 正解 | 0.958636 | 0.002244 | **+0.054565** | 0.824222 |
| 正解⊕予測 | 0.959956 | 0.002547 | **+0.055886** | 0.825255 |

**解釈は書かない**（§10）。

### 4.3 判定 a の空振り確認

    四段の平均 acc が全て同一でない -> True
      [0.904070407, 0.9359735974, 0.9586358636, 0.9599559956]
    12 run の acc の相異なる値: 11 / 12

11/12 なのは `正解 seed42` と `正解⊕予測 seed42` が同値（0.9564356435643564）だからである。
**測定は入力に感応している**（段の平均は四つとも異なる）。

### 4.4 所要時間の実測（B1）

| 段 | seed42 | seed123 | seed456 |
|---|---|---|---|
| 空 | 12.1 s | 12.7 s | 13.6 s |
| 予測 | （試走と同型・約 12 s） | 16.7 s | 16.3 s |
| 正解 | 13.6 s | 11.9 s | 19.1 s |
| 正解⊕予測 | 24.6 s | 30.0 s | 24.1 s |

すべて `rc=0`。**予測段 seed42 は命名確認のため単独で実行したため計時していない**（UNKNOWN）。
12 run の合計は約 3 分である。

---

## 5. Phase E 収穫

### 5.1 収穫前

    index.csv: 1238 行 / experiments.csv: 273 / verdicts.csv: 1458 / per_class.csv: 8919
    runs/: 1238 ファイル

### 5.2 収穫

    $ make runindex
    exit=0
    走査した run 数        : 1250
      警告なしで収穫       : 510
      警告ありで収穫       : 740
      収穫失敗             : 0
    [PASS] C1〜C9 全 9 項目

### 5.3 差分（集合差）

| 表 | 前 | 後 | 追加 | 削除 | 既存行の変更 |
|---|---|---|---|---|---|
| `index.csv` | 1238 | 1250 | **+12** | **0** | **0** |
| `experiments.csv` | 273 | 277 | +4 | 0 | **0** |
| `verdicts.csv` | 1458 | 1486 | +28 | 0 | **0** |
| `per_class.csv` | 8919 | 9027 | +108 | 0 | 0 |

    追加のうち本契約の run: 12 / 追加以外の混入: 0
    task_id が全件付いているか: True
    判定列（same_sign / verdict_pstd / verdict_sstd / agree / reason / n_seeds）で変わったもの: なし

**今回は集約表でも既存行の変更が 0 件だった。** 四段とも新規の experiment 群を作り、
既存の群へ加入した run が無いためである（先契約 `k1-reeval-and-harvest` では
1 run が既存群へ加入して集約が再計算された）。

追加 12 件（すべて `task_id=T-2026-08-29-stage0-contract-b`）:

    b2a_refin_both_001_b2a_refin_both_seed42        acc=0.956435
    b2a_refin_both_002_b2a_refin_both_seed123       acc=0.962376
    b2a_refin_both_003_b2a_refin_both_seed456       acc=0.961056
    b2a_refin_empty_001_b2a_refin_empty_seed42      acc=0.914191
    b2a_refin_empty_002_b2a_refin_empty_seed123     acc=0.897029
    b2a_refin_empty_003_b2a_refin_empty_seed456     acc=0.900990
    b2a_refin_oracle_001_b2a_refin_oracle_seed42    acc=0.956435
    b2a_refin_oracle_002_b2a_refin_oracle_seed123   acc=0.961716
    b2a_refin_oracle_003_b2a_refin_oracle_seed456   acc=0.957755
    b2a_refin_pred_001_b2a_refin_pred_seed42        acc=0.937953
    b2a_refin_pred_002_b2a_refin_pred_seed123       acc=0.934653
    b2a_refin_pred_003_b2a_refin_pred_seed456       acc=0.935313

---

## 6. 判定 b・e・f の実測

### 6.1 判定 b（prereg の時系列）

    prereg commit 7b1cff8b  committed_at = 2026-08-29T13:52:50+00:00

| run | config.yaml の作成時刻 |
|---|---|
| `b2a_refin_pred_001_..._seed42` | 2026-08-29 13:53:21 |
| `b2a_refin_pred_002_..._seed123` | 13:53:52 |
| `b2a_refin_pred_003_..._seed456` | 13:54:09 |
| `b2a_refin_oracle_001_..._seed42` | 13:54:25 |
| `b2a_refin_oracle_002_..._seed123` | 13:54:39 |
| `b2a_refin_oracle_003_..._seed456` | 13:54:51 |
| `b2a_refin_empty_001_..._seed42` | 13:55:18 |
| `b2a_refin_empty_002_..._seed123` | 13:55:30 |
| `b2a_refin_empty_003_..._seed456` | 13:55:43 |
| `b2a_refin_both_001_..._seed42` | 13:56:08 |
| `b2a_refin_both_002_..._seed123` | 13:56:33 |
| `b2a_refin_both_003_..._seed456` | 13:57:03 |

**最早の run（13:53:21）が prereg commit（13:52:50）の 31 秒後。全 12 run が後である。**

🔴 ただし §2.4 の**試走は prereg commit より前に走っている**（`--no-evidence` のため
run ディレクトリも索引の行も残らない）。契約 §3 Step A-2 が「最小の試走で見積もる」を
A-3 の前に置いているため、この順序は契約どおりである。逸脱として報告する。

### 6.2 判定 e（変更範囲・既存 run と data と分割の不変）

    data/ への変更                                  : 0
    既存 run（b2a_refin 以外の experiments/）への変更 : 0
    本契約 run の config に test の記載              : 0 件

分割ファイルの要約値（読み取りのみ。書き換えていない）:

    c28816de94c5ed83e4f1e47fd63b3a9e4f9e5ab970e8b38a85aeebc66922a8e2  data/splits/ego_train.txt
    f1bc456a0439b60674507a05484784065a1bdcbcb89274b5b83680a16cc093ea  data/splits/ego_val.txt
    7edeab6294574cfdb13b07f57c5ca71fe9e0eb878ec2d1b7fc0c5c22a6befaef  data/splits/ego_test.txt

### 6.3 判定 f（凍結源の不変）

    作業前 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    作業後 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    一致

---

## 7. 変更範囲と検査

### 7.1 検査の結果（終了コードを個別に測った）

zsh は配列添字で終了コードを取れないため、各命令を単独で走らせて `$?` を取った。

    make task-validate    -> exit=0
    make taskindex-check  -> exit=0
    make inbox-check      -> exit=0
    make context-check    -> exit=0
    make docs-check       -> exit=0
    make agent-check      -> exit=0
    make forbidden-check  -> exit=2   ← 既知の制約（下記）

### 7.2 forbidden-check の違反が許可分と一致すること（SPEC §7 の指示）

    base=origin/phase0  changed=122  checked=114  excluded=8  違反=104

`git status` はディレクトリ単位で出るが `check_forbidden.py` はファイル単位で出るため、
**両者をファイル単位に揃えて**照合した。

    違反 104 件 / 許可分（ファイル単位）116 件
    違反 ⊆ 許可分 : True
    許可分に無い違反: []

    違反の内訳:
      runindex/                 : 20   ← make runindex による収穫（§2 が許可）
      本契約の 12 run 配下        : 84   ← experiments/transfer/b2a_refin_*（§2 が許可）
      data/                     : 0
      それ以外                   : 0

**違反はすべて本契約が許可された対象の内側である。** 許可分 116 件のうち 104 件が違反として
出るのは、`check_forbidden.py` が `context/auto/` の生成物 8 件を除外し、
残りを禁止領域として数えるためである。

`tools/check_forbidden.py` の `FORBIDDEN_PREFIXES` は
`runindex/ context/auto/ experiments/ transfer/ data/` を固定で持ち、**契約ごとの許可を
受け取る引数が無い**（`--base` のみ）。run を生成する exp 契約はこの検査を原理的に通せない。
先契約 `k1-reeval-and-harvest` と同じ制約である。

### 7.3 判定 e の空振り確認（差分検出器の対照）

    陽性（収穫前 vs 収穫後）        : 追加 12 / 削除 0 / 変更 0
    陰性（先契約 k1-reeval-and-harvest の同じ器）: 集約表で変更 8 件を検出した実績がある

**同じ器が別の入力で非零を返しているため、今回の「変更 0 件」は
「常に 0 を返す壊れ方」ではない。**
