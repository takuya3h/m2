# RESULT — T-2026-09-18-stage1-detector-towers

ホスト `efros`（RTX A6000 × 2 / driver 595.84 / nvcc 12.9 / torch 2.1.2+cu118）。2026-09-18〜21 JST。

## 判定

`verdict: pass`。**両塔を 5 折りで確定した。14 run 全て完走し、再現も成立した。**

| Gate | 判定 | 何を実測したか |
|---|---|---|
| G1（A の後） | pass | 凍結源の処方を `command.sh`・`config.yaml`・`metrics.json` から**全項目**特定（UNKNOWN 0 件）。折りごとの注釈を生成し **全 15 分割で集合差 0**、折り A は公式ファイルと sha256 一致。装置は compute プロセス 0 件 |
| G2（B の後） | pass | 折り A seed42 の D\*-COCO は **0.724414**、凍結源 0.729749 との差 **−0.53 mAP**。事前登録の「1 mAP 以内 = 再現」に該当 |
| G3（D の後） | pass | test の評価は **ちょうど 10 回**（台帳 10 行、checkpoint の sha256 つき）。10 を超えていない |

## 1. 解決された参照

- `inputs.denominator.ref` = `exp:baselines/s0/relationdetr_bbox@val` → n_runs 3 / n_seeds 3 /
  seeds 42,123,456 / split val / `eval_recipe_id` `b66459018a92` / host philip。
  **mAP 平均 0.7267943333・pstd 0.0033960155・sstd 0.0041592526**。AP_rare 平均 0.7483483333。
  `require`（n_seeds ≥ 3・sigma present・split val）を**満たす**。**分母は動いていない**
- `inputs.sigma_policy`（省略）→ `conventions#sigma` の既定を継承（`series: pstd`）。**本契約は散らばりの
  比較に実際に適用した**
- `inputs.frozen_source` → sha256 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` /
  195,421,066 bytes。**規約の記載と一致**（L3 の P5 PASS）。凍結源は変更していない
- `contract.inject_verbatim` 7 件（`prohibitions` / `issuer_cautions` / `folds` / `split` /
  `eval_recipe` / `frozen_source` / `sigma`）。原文は `context/conventions.md` rev
  `e7a5100597a79b3b9c60935bf38d232f8ae96822` の該当アンカー。要約していない
- 占位の差し替え: `conventions_rev` 同上、`runindex_commit` `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5`、
  `counts` index 1266 / experiments 285 / verdicts 1506
- `prereg.commit` = `fa9cc5466e0bee7646a0010b06413e6da853e03d`（2026-09-17T22:11:38+00:00）。
  **最初の学習の起動（22:26:42）より 15 分前**

## 2. 完了判定

| # | 判定 | 実測 |
|---|---|---|
| a | 処方の特定と差分 | **達成。** 全項目を出所つきで特定（UNKNOWN 0 件）。差分は **0 項目**。🔴 ただし契約が言う「TF32 を除く」は成立しない——**凍結源は fp16 で学習されており**、利用者の判断で fp16 に揃えた（下記 4） |
| b | 折り表に従う | **達成。** 全 5 折り × 3 分割で**集合差 0**。分割間の重なり 0、動画の和 15、画像合計 15,437 が全折りで保存。折り A は公式ファイルと **sha256 一致**。陰性対照は差 **2**（🔴 契約は「差 1」と書くが 1 本入れ替えの対称差は 2） |
| c | 折り A の再現 | **達成。** 0.724414 対 0.729749、差 **−0.53 mAP**。分母の 3 seed 平均とは **0.70σ** |
| d | 表 | **達成。行数 14。** 2 塔 × 5 折り、折り A は 3 seed。欠けなし |
| e | test は折りごとに一度 | **達成。台帳 10 行ちょうど。** 確定塔以外 0 件（折り A は seed 42 を確定塔とした） |
| f | TF32 と所要時間 | **一部未達。** 🔴 **TF32 では回していない**（凍結源が fp16 のため。利用者の判断）。所要時間は全 14 run に記録（7:48:59〜9:13:30、平均 8.353 h）。計算器に実測が入り `measured: True`、`--check-doc` 差 0 件 |
| g | 刻印と収穫 | **達成。** 14/14 に `task_id`。収穫で `baselines/d{coco,imagenet}_fold{A..E}` として現れた。🔴 空振り確認の「行数の差 = 新実験数」は**成り立たない**（下記 4） |
| h | PR | 送出節を参照 |

## 3. 実測

### 凍結源の処方（出所つき・UNKNOWN 0 件）

`accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed42.py
--seed 42 --mixed-precision fp16`（run の `command.sh`）。12 epoch / `MultiStepLR(milestones=[10], gamma=0.1)` /
per-GPU batch 2 × 2 枚 = 実効 4 / lr 1e-4 / `AdamW(wd=1e-4, betas=(0.9,0.999))` / `max_norm 0.1` /
`presets.detr` / `freeze_indices=(0,)` / COCO 1x 初期化・class head 91→15 再初期化。

### 2 塔 × 5 折り

| 塔 | 折り | seed | val mAP | val AP_rare | test mAP | test AP_rare | 所要 |
|---|---|--:|--:|--:|--:|--:|--:|
| D\*-COCO | A | 42 | 0.7244 | 0.7382 | 0.5117 | 0.6147 | 7:48:59 |
| D\*-COCO | A | 123 | 0.7254 | 0.7581 | — | — | 7:55:51 |
| D\*-COCO | A | 456 | 0.7208 | 0.7259 | — | — | 7:54:21 |
| D\*-COCO | B | 42 | 0.4762 | 0.6049 | 0.4384 | 0.5551 | 8:02:00 |
| D\*-COCO | C | 42 | 0.4385 | 0.6004 | 0.5011 | 0.6685 | 8:54:40 |
| D\*-COCO | D | 42 | 0.4967 | 0.6665 | 0.5558 | 0.6131 | 8:42:00 |
| D\*-COCO | E | 42 | 0.5272 | 0.6611 | 0.5841 | 0.7659 | 9:13:30 |
| D\*-ImageNet | A | 42 | 0.6853 | 0.7743 | 0.4724 | 0.6108 | 7:55:30 |
| D\*-ImageNet | A | 123 | 0.6774 | 0.7411 | — | — | 7:52:28 |
| D\*-ImageNet | A | 456 | 0.6660 | 0.7561 | — | — | 7:53:37 |
| D\*-ImageNet | B | 42 | 0.4084 | 0.5130 | 0.4064 | 0.4889 | 8:01:44 |
| D\*-ImageNet | C | 42 | 0.4093 | 0.5820 | 0.4802 | 0.5583 | 8:53:38 |
| D\*-ImageNet | D | 42 | 0.4801 | 0.6999 | 0.5164 | 0.6229 | 8:35:16 |
| D\*-ImageNet | E | 42 | 0.4538 | 0.6381 | 0.5655 | 0.7683 | 9:12:56 |

### 散らばり

| 塔 | 折り A の seed 間 pstd | 折り間 pstd（B〜E） | 比 |
|---|---:|---:|---:|
| D\*-COCO | 0.001984 | **0.032249** | **16.3×** |
| D\*-ImageNet | 0.007892 | **0.030500** | **3.9×** |

### 予測の当たり外れ

| # | 予測 | 判定 | 実測 |
|---|---|---|---|
| 1 | 折り A seed42 の D\*-COCO は凍結源と 1 mAP 以内 | **当たり** | −0.53 mAP |
| 2 | D\*-ImageNet は全折りで低く、差は 5〜15 mAP | **部分的に外れ** | 方向は 5/5 当たり。幅は **1.66〜7.33 mAP** で 5〜15 に入るのは **2/5 折り**。**予測より差が小さい** |
| 3 | 折り間 SD > 折り A の seed 間 SD | **当たり** | 16.3× と 3.9× |
| 4 | D\*-ImageNet は最良 epoch が後ろに寄る | **外れ** | 最良 epoch は 11〜12 番目で D\*-COCO と同じ |

予測 4 の補足: **「後ろに寄る」は外れだが「収束が遅い」は支持される。** 最後の 1 epoch の伸びは
D\*-ImageNet +0.0067 対 D\*-COCO +0.0004 で **5.2 倍**。D\*-ImageNet は最終 epoch が最良で、
**12 epoch で打ち切られている可能性が高い**。🔴 **epoch を増やせば伸びるかは測っていない（UNKNOWN）。**

### 所要時間と日数

14 run 平均 **8.353 h**（7.816〜9.225。折りにより train が 9,657〜11,182 枚と違う）。
**14 × 8.353 ÷ 2 枚 = 58.5 h** は実際の経過 58.7 h（9/17 22:26:42 → 9/20 09:09:57 UTC）と一致。
同時実行は **2 本が最適**（1 本 1.805 step/s → 2 本 2.17 → 3 本 2.19 で頭打ち。実測）。

`det_tower_train` を **8.00 h（代理）→ 8.35 h（実測・measured True）**。計算器の UNKNOWN は 10 → 9 件。

| 前提 | 更新前 | 更新後 |
|---|---:|---:|
| 24h/日・Stage 1 + Tier 1〜3・縮退なし | 87.5〜116.6 日 | **87.9〜117.0 日** |
| 12h/日・Stage 1 + Tier 1・縮退なし | 159.9〜218.2 日 | **160.5〜218.8 日** |
| 同・縮退段 3 | 96.2〜131.2 日 | **96.6〜131.6 日** |

**日数はほぼ動かなかった（+0.4%）。** 代理の置き方が妥当だったことの確認になる。締切の判定も変わらない。

## 4. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | `prereg.md` §2 と SPEC §1 は「**凍結源は fp32 で学習されている**」を前提に全 run を TF32 と定めるが、凍結源 run の `command.sh` の実測は `--mixed-precision fp16` である。指示どおり TF32 で回すと処方の差分が 0 にならず、完了判定 a を満たせない |
| `asserted_without_measuring` | SPEC §2 が `inputs.code.entrypoints` に `scripts/train_t1b.py` を挙げるが、**検出塔のフル学習の入口は `third_party/Relation-DETR/main.py`（accelerate）である**。`train_t1b.py` は P→D 界面の学習器で別物。指示どおり進めると入口を取り違える |
| `check_does_not_check` | 契約は Task C で `experiments/` 配下へ書く 14 run を必ず伴うのに `contract.allow_write` を宣言していないため、Task E-1 が求める `make forbidden-check` が必ず失敗する。**前契約 `T-2026-09-17-amp-compile-timing` と同じ誤りの再発**である |
| `asserted_without_measuring` | 完了判定 b の空振り確認が「test 動画を一本入れ替えた注釈で**差 1**」とするが、1 対 1 の入れ替えの対称差は **2** である。実測は 2（通常は 0）。差が 0 でないことを示す目的は達するが、期待値の記載が誤っている |
| `self_contradiction` | §4 禁止事項 6 は `runindex/**` の手編集を禁じる一方 **`make runindex` は可**と明記するが、Task E-1 が求める `make forbidden-check` は `runindex/` の変更を禁止領域として弾く（実測 70 経路）。**契約が許した操作が、契約の求める検査で落ちる。** `contract.allow_write` に `runindex/` を足して整合させた |
| `check_does_not_check` | 完了判定 g の空振り確認「収穫前後の**行数の差 = 新実験数**」は、この repo では成り立たない。収穫器は既存行も更新し、同期で届いた退避物も拾うため、実測は index +52 に対し新 run 27 件（うち本契約 14）だった。`task_id` での照合に替えた |

## 5. 逸脱

1. `judgement` — **G2 の評価を待たずに Task C の run を並行で始めた**（利用者の「GPU の空きを使って早めて」の指示による）。再現が 3 mAP 超で外れていれば回した分を捨てることになったが、処方は完全に特定でき折り A の注釈は公式と sha256 一致だったため危険は低いと判断した。結果として G2 は通過した
2. `judgement` — 同時実行は **2 本**に決めた。1/2/3 本を実測し、3 本目が総処理量を 1% しか増やさないことを確かめたうえでの判断（`audit.md` に表）
3. `judgement` — 折り A の test 評価は **seed 42** を確定塔とした。折り A だけ 3 seed あり、契約は「折りごとに一度」としか書いていないため選ぶ必要があった。凍結源と同じ seed を採った
4. `spec_defect` — `scripts/make_fold_annotations.py` `scripts/run_stage1_dtower.sh` `scripts/stage1_dtower_queue.sh` `scripts/eval_stage1_dtower.sh` `scripts/write_stage1_dtower_evidence.py` を新設し、`scripts/eval_relation_detr_map.py` に `--split` を足した（**既定は従来どおり**）。§3 は「コマンドは書かない」とするが `scripts/` への新設は明示の対象外である
5. `spec_defect` — `third_party/Relation-DETR/configs/train_config_egosurgery_stage1_imagenet_seed{42,123,456}.py` を新設した。COCO 版との差は `resume_from_checkpoint` の 1 箇所だけであることを diff で示した
6. `environment` — 折りごとの注釈は `data/annotations/egosurgery_tool_folds/` へ置いた（`.gitignore:10` で追跡外）。公式の `egosurgery_tool/instances_*.json` は 118 行目で追跡対象のため、**別ディレクトリにして取り違えを防いだ**
7. `judgement` — 本 run の完了後、利用者の常設の指示に従い GPU の仮占有プロセスを戻した。そのため**報告時点の preflight は P11 `gpu_free` が FAIL する**（GPU 作業は完了済み）
8. `spec_defect` — `contract.allow_write` に `experiments/baselines/stage1_dtower/` と `runindex/` を
   追補した。前者は Task C が必ず書く成果物、後者は §4-6 が明示的に許す `make runindex` の生成物である。
   **どちらも手編集していない。**
9. `judgement` — `origin/phase0` を統合した（基点が 34 commit 古く、検査が実質を測れなかったため）。
   衝突 6 件のうち `runindex/` の 4 件は生成物で、phase0 側を土台に採ってから再生成し、
   **両契約の run が残ることを実測で確かめた**（本契約 14 件・ilya の工程塔 72 + 168 件）。
10. `judgement` — 学習ログ（1.6〜1.9 MB × 14 本）を版管理へ入れず、引用に要る行を
    `train_summary.log`（各 17 KB 程度）へ抜いた。`.gitignore` に除外を足した。
11. `judgement` — 契約と無関係な `docs/experiment_settings.md`（利用者の求めで作成した実験設定の索引）を同じ分岐に含めた

## 6. 想定外・UNKNOWN

1. **D\*-ImageNet を 12 epoch より延ばしたときの到達点。** 最終 epoch が最良で末尾の傾きが
   D\*-COCO の 5.2 倍あり打ち切りが疑われるが、**測っていない**
2. **予測 2 の差が小さかった理由。** 両塔とも打ち切られている可能性があるが、切り分けていない
3. **折り C・D・E で test mAP が val mAP を上回る理由**（例: 折り E は val 0.5272 → test 0.5841）。
   折りごとの難しさが val と test で逆向きに出ている。原因は調べていない
4. **P3 `deterministic_flags` は宣言したのに SKIP された**（判定基準が未確定・backlog B-20）。
   宣言しても検査されない項目がある
5. Stage 1 の正式な工程塔の処方（ilya の契約が確定中）

## 7. 送出

| 項目 | 値 |
|---|---|
| `make task-validate` | exit 0（`OK` / 0 failed） |
| `make task-preflight` | 実行前は **exit 0**（10 PASS / 0 WARN / 2 SKIP / 0 FAIL）。報告時点は P11 `gpu_free` が FAIL（ダミーを戻したため。逸脱 7） |
| `make spec-check` | exit 0 / `"status": "pass"` |
| `make forbidden-check TASK=...` | **status pass / violations 0 / permitted 268 / rejected 0**（`allow_write` の追補後。宣言前は fail で 70 経路が `runindex/` として弾かれた） |
| `--check-doc`（B1） | **差 0 件** |
| `make runindex` | exit 0。本契約の 14 run が `task_id` つきで現れた |
| `make taskindex-check` / `make inbox-check` | exit 2（§4 禁止事項 5 により再生成しない。契約が「想定どおり」と明記） |
| 分岐 | `feat/stage1-detector-towers` |
| PR | 送出節の追記を参照（base は `phase0`） |
