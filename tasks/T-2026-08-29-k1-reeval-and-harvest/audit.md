# audit — T-2026-08-29-k1-reeval-and-harvest

実行ホスト `lecun` / repo `/home/ubuntu/slocal/m2` / 分岐 `feat/k1-reeval-and-harvest`。
`experiments/` `data/` へは読み取りのみ。`runindex/` は `make runindex` による収穫のみ。

命令とその出力を節ごとに全文で置く。RESULT.md からは節番号で指す。

---

## 1. Step A-1 事前記入値の照合

    $ git --no-pager log -1 --format="%h %ad" -- context/conventions.md
    a8c07e81 Tue Aug 25 15:30:37 2026 +0000

    $ git --no-pager log -1 --format="%h %ad %s" -- runindex/
    7918b5dd Sun Aug 16 00:12:23 2026 +0000 exp(s4): 60-seed deterministic sweep ...

    $ for f in index experiments verdicts; do echo "$f: $(($(wc -l < runindex/$f.csv)-1))"; done
    index: 1177 / experiments: 213 / verdicts: 1038

| 項目 | 事前記入値 | 実測 | 判定 |
|---|---|---|---|
| `conventions_rev` | `a8c07e81` | `a8c07e81` | 一致 |
| `runindex_commit` | `7918b5dd` | `7918b5dd` | 一致 |
| `counts` | 1177 / 213 / 1038 | 1177 / 213 / 1038 | 一致 |

**置換不要。**

`hostname` は `lecun`。GPU（Phase C 開始前の実測）:

    0, NVIDIA RTX A6000, 49140 MiB, used 35 MiB, free 48507 MiB, util 0 %
    1, NVIDIA RTX A6000, 49140 MiB, used 20 MiB, free 48521 MiB, util 0 %
    $ nvidia-smi --query-compute-apps=pid,used_memory --format=csv
    pid, used_gpu_memory [MiB]      ← 使用プロセス 0 件

🔴 **`plan.env.preflight` の `gpu_free` は検査されていない。** `tools/preflight_task.py` の
`CHECK_NAMES` は P1〜P9 の 9 語しか持たず、`LISTED_ONLY` は `cuda_ext_loaded` と
`deterministic_flags` の 2 語のみ。未知の名前を検出する分岐は無く、schema
（`tasks/_schema/spec.schema.json:196`）も `{"type":"array","items":{"type":"string"}}` で
任意の文字列を通す。**宣言しても黙って無視され、PASS になる。** 上の GPU の実測は
検査器ではなく実行者が行ったものである。

---

## 2. Step A-2 所在の確定（G1）

### 2.1 収穫対象の再実測と棚卸しの突き合わせ

収穫器と同じ走査定義（`EXPERIMENTS.rglob("metrics.json")` の親）で数え、索引の `path` と
差集合を取った。索引側の旧様式 29 件があるため両者を正規化してから比較した。

    走査 run=1209  索引 path=1177  追跡外=61
      b2a_det2phase_oracletool: 1 件
      b2a_lovo: 30 件
      b2a_seglovo: 30 件

**前契約の棚卸し（61 件 = 1 + 30 + 30）と件数・内訳ともに一致。増減なし。**

### 2.2 評価の実装経路

**新しい評価規則は作っていない。** 既存の実装をそのまま呼ぶ。

| 要素 | 実体 |
|---|---|
| 特徴の読み込み | `scripts/train_t1a.py` の `load_clips(split, region_only=False)` |
| 評価 | 同 `evaluate(model, clips, device)`（`@torch.no_grad()`） |
| 指標の定義 | `src/egosurgery/metrics/phase.py` の `PhaseEvaluator(num_classes, class_names)` |
| モデル | `src/egosurgery/models/heads/tecno_head.py` の `TeCNO` |
| 分割 | `data/processed/phase_manifest/val.json` |
| クラス | `data/processed/phase_manifest/phase_vocab.json`（9 クラス。`hemostasis` は index 6） |

当時の評価と同じ経路であることの根拠。六 checkpoint は
`scripts/run_when_gpu_free.sh` の Phase 3 が `scripts/train_t1a.py --epochs 50` で作った
（前契約 audit §6.2）。`train_t1a.py` は学習ループ内で同じ `evaluate()` を呼び、
その戻り値を checkpoint の `val` キーへ保存する。**再評価は同じ関数を同じ入力で呼ぶ。**

### 2.3 分割の所在（再定義していない）

    $ cat data/splits/ego_val.txt
    09
    10

    val.json の clip_id: ['09_1', '10_1', '10_2']   総フレーム数: 1515

**動画 09 と 10 で一致。** 1515 フレームは
`evidence/discarded_caches/t1a_regiontoken/...discarded_20260706.md` の
「val 1515 x 3840」とも一致する。分割は読むだけで、再定義していない。

acc の分母としても整合する: `0.8917491749174917 × 1515 = 1351.0`、
`0.9478547854785478 × 1515 = 1436.0`（いずれも整数）。

### 2.4 特徴キャッシュの所在と生成日

    relationdetr 側 (relation_detr_seed42):
      2026-06-16 17:07   79458316  stage1_features/relation_detr_seed42/train_gap.npz
      2026-06-16 17:07   12465940  stage1_features/relation_detr_seed42/val_gap.npz
      2026-06-16 18:43   35092940  stage1_features/relation_detr_seed42/test_gap.npz
      2026-06-20 18:21  148679688  t1a_regiontoken/relation_detr_seed42/train_regiontoken.npz
      2026-06-20 18:24   23325456  t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz
      2026-06-20 18:34   65664456  t1a_regiontoken/relation_detr_seed42/test_regiontoken.npz

    aligndetr 側 (aligndetr_s0frozen_seed42):  2026-07-10 17:39 / 17:41 / 17:47（前契約で実測）

`scripts/train_t1a.py:57-61` により、凍結源タグがそのまま経路になる。

    FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
    GAP_DIR    = .../stage1_features/FROZEN_SRC
    REGION_DIR = .../t1a_regiontoken/REGION_SRC

`run_when_gpu_free.sh` は relationdetr 側で `RELDETR_FROZEN_TAG=relation_detr_seed42`、
aligndetr 側で `RELDETR_FROZEN_TAG=aligndetr_s0frozen_seed42` を渡す。再評価も同じ値を使った。

### 2.5 checkpoint の入力次元（噛み合いの確認）

    $ python -c "... torch.load(...) ..."
    トップレベルのキー: ['tecno', 'epoch', 'val']
    stage1.conv_in.weight            -> (64, 5888, 1)      => in_dim = 5888
    refine_stages.0.conv_out.bias    -> (9,)               => num_classes = 9
    テンソル数: 72

**入力次元 5888 = GAP 2048 ⊕ region-token 3840。** `train_t1a.py` の既定（連結）であり、
`--region-only` の 3840 ではない。region-token 3840 次元を含んでいるため噛み合う。
`load_clips` が組み立てた特徴の次元も 5888 で、`load_state_dict(..., strict=True)` が
六件すべてで通った（欠落キー・余剰キーなし）。**escalate（次元の不一致）には当たらない。**

### 2.6 🔴 metrics は失われていなかった

checkpoint の `val` キーに、当時の best epoch における検証指標が入っていた。

    {"phase_accuracy": ..., "phase_macro_f1": ..., "phase_jaccard": ...,
     "phase_edit_score": ..., "phase_seg_f1_10/25/50": ...,
     "phase_per_class_f1": {9 クラス}, "phase_per_class_jaccard": {9 クラス}}

**前契約は `metrics.json` の不在だけを見て「run が無い・読めない」と結論した。
checkpoint を開いていなかった。** 成果物ファイルの不在は数値の不在を意味しない。

六件の保存値（`val`、best epoch）:

| side | seed | epoch | phase_accuracy | hemostasis F1 |
|---|---|---|---|---|
| relationdetr | 42 | 19 | 0.9478547854785478 | 0.7741935483870968 |
| relationdetr | 123 | 16 | 0.9478547854785478 | 0.8245614035087719 |
| relationdetr | 456 | 39 | 0.9471947194719472 | 0.8041237113402062 |
| aligndetr | 42 | 26 | 0.8917491749174917 | 0.25 |
| aligndetr | 123 | 24 | 0.8752475247524752 | 0.21875 |
| aligndetr | 456 | 28 | 0.8686468646864687 | 0.06779661016949151 |

**G1 の四項目（収穫対象の突き合わせ・評価経路・特徴と分割の所在・次元の噛み合い）は
すべて確定した。G1 = pass。**

---

## 3. Step A-3 退避 digest の記録

    退避中: sha256 70d40c63e387b497d599db54f594653150dbd6effeec102236428be28b3ddded  26565 バイト
    戻した後: sha256 70d40c63e387b497d599db54f594653150dbd6effeec102236428be28b3ddded  26565 バイト
    一致

前セッション開始時の `ls` 実測も 26565 バイトで一致する。**内容は一字も変えていない。**

### 3.1 伏せ字が効いていることの確認（規約 docs/sessions/README.md）

値は出さず形だけで判定した（`issuer_cautions` 注意 8）。

    32 文字以上の十六進（未伏せ）        : 0 件
    秘密を示す名前への代入で値が残る     : 0 件
    鍵らしき接頭辞 + 長い文字列          : 0 件

**0 件が「検査が働いていない」でないことを両方向で確かめた**（注意 3）。

    陽性対照（合成文字列。本物の値ではない）: 3 規則すべて 1 件ずつ検出
    陰性対照（伏せ字済みの表記 NAME=*** 等）: 3 規則すべて 0 件

**分母の確認**として追跡済み digest 36 件にも同じ検査を当てたところ 4 件で 6 件の該当が出た。
**何に一致したのかを見た**（注意 2）。いずれも `NAME=値` 形式で、値の長さ 8〜15、
文字種は英小文字と記号が中心。環境にある実際の資格情報（`NOTION_API_KEY` /
`WANDB_API_KEY` / `CLAUDE_CODE_MESSAGING_TOKEN`）と**完全一致 0 件・本文への出現 0 件**。
**実物の資格情報は含まれていない。** 本契約の検出規則 `(?!\*)` が伏せ字の一部表記を
拾ってしまう偽陽性である。既存の記録は書き換えていない（§7 禁止 6）。

---

## 4. Phase B 収穫

### 4.1 収穫前の記録

    index.csv:      1177 行  sha256=9ad4b5f1ce0c7cef...
    experiments.csv: 213 行  sha256=30111d27ee0d05d3...
    verdicts.csv:   1038 行  sha256=11d53f4a0c2c7a65...
    per_class.csv:  8370 行  sha256=2c807f5d145b03f5...
    runs/:          1177 ファイル

四つの csv と `runs/` をスクラッチパッドへ複製して控えた（比較の原本）。

### 4.2 dry-run

    $ make runindex-dry
    走査した run 数        : 1238
      警告なしで収穫       : 498
      警告ありで収穫       : 740
      収穫失敗             : 0
    除外フラグ付き         : 48
      解析対象             : 1190
    DRY-RUN: 何も書き出していない。

1238 = 現行索引 1177 + 追跡外 61。走査 1209（metrics.json の親）に旧様式 29 件
（`TRANSFER_LEGACY`、`*result*.json` から収穫）を足した数と一致する。

### 4.3 収穫の実行

    $ make runindex
    exit=0
    --- 回帰テスト（primary=val / per_class / experiments の整合）---
      [PASS] C1 primary = val (test を持つ run)
      [PASS] C2 val/test の乖離
      [PASS] C3 split 列と metrics の出所の一致
      [PASS] C4 index.csv と runs/*.json の 1:1
      [PASS] C5 per_class.csv の整合
      [PASS] C6 experiments.csv の整合
      [PASS] C8 paired_feasibility.csv
      [PASS] C9 seed の突き合わせ (dirname vs command.sh vs config.yaml)
      [PASS] C7 標準 JSON (裸の NaN/Infinity 無し)
    全項目 PASS。

**手編集はしていない。** `make runindex` のみ。

### 4.4 差分の検証（集合差。件数の一致だけで判定しない）

| 表 | 前 | 後 | 追加 | 削除 | **既存行の変更** |
|---|---|---|---|---|---|
| `index.csv` | 1177 | 1238 | **+61** | **0** | **0** |
| `experiments.csv` | 213 | 273 | +60 | 0 | **1** |
| `verdicts.csv` | 1038 | 1458 | +420 | 0 | **7** |
| `per_class.csv` | 8370 | 8919 | +549 | 0 | 0 |

鍵は `index` が `ledger_key`、`experiments` が `experiment_id`、
`verdicts` が (`experiment_id`,`metric`,`arm`,`control_of`,`delta_method`,`sigma_source`)、
`per_class` は行全体を鍵にした多重集合。

**追加行の path 集合と棚卸しの一覧の照合:**

    棚卸し 61 件 / 追加行の path 61 件
    一致: True
      追加にのみある: 0
      棚卸しにのみある: 0

### 4.5 🔴 escalate — 既存行の変更 8 件

契約 §4 と `escalate_if` は「追加以外が一件でも現れたら停止」と定める。**停止して報告した。**

変更 8 行は**すべて同一の experiment 群**に属する。

    transfer/b2a_det2phase_oracletool/b2a_det2phase_oracletool@val~relation_detr_seed42

原因は、追加 61 件のうち **1 件**（`b2a_det2phase_oracletool_009_..._seed42`）が
**既存の群へ加入**したことである。群の構成 run は 8 → 9 になった。

    n_runs               8 -> 9
    runs_per_seed_max    2 -> 3
    n_command_variants   2 -> 3
    task_ids             '' -> 'T-2026-08-26-oracle-ceiling-and-tool-drop'
    accuracy_mean        0.9575907590759076  -> 0.9573890722405574
    accuracy_pstd        0.003126616389685883 -> 0.003002492041138064
    accuracy_n           8 -> 9
    （edit_score / jaccard / macro_f1 / seg_f1_10 / seg_f1_25 / seg_f1_50 も同様に再計算）
    delta_accuracy       0.05978626434071984 -> 0.060006286342920045
    abs_delta_over_sigma_accuracy  11.423346198558852 -> 12.18532380074703

`verdicts.csv` の 7 行は上の群の 7 指標に対応し、変わった列は
`delta` `pstd` `sstd` `ratio_pstd` `ratio_sstd` の 5 列のみ。

**判定に関わる列は一つも変わっていない。**

    変更のあった 7 行のうち判定列（same_sign / verdict_pstd / verdict_sstd / agree /
    reason / n_seeds）で変わったもの: なし

    1σ 判定の推移（ratio_pstd）
      accuracy    11.423 -> 12.185   有意 -> 有意
      edit_score   3.737 ->  4.458   有意 -> 有意
      jaccard     14.015 -> 15.447   有意 -> 有意
      macro_f1    12.941 -> 13.565   有意 -> 有意
      seg_f1_10    4.552 ->  5.010   有意 -> 有意
      seg_f1_25    4.760 ->  5.206   有意 -> 有意
      seg_f1_50    4.104 ->  4.368   有意 -> 有意
    Δ の符号反転: なし

`n_seeds` が動かないのは、加入した 009 が seed42 で、その seed が群に既にあるためである
（004 と 006 が seed42）。

他の 60 件（`b2a_lovo` 30・`b2a_seglovo` 30）は**新規の群**を作るため追加のみだった
（experiments +60）。

**利用者の判断: 続行。** 判断は `tasks/inbox.d/` に記録した。

---

## 5. Phase C 再評価

### 5.1 実装

再評価器は `/tmp/.../scratchpad/reeval.py`。**既存実装を呼ぶだけである。**

- 凍結源は run 名から決める（`aligndetr` → `aligndetr_s0frozen_seed42`、
  そうでなければ `relation_detr_seed42`）。経路は import 時に決まるため、
  `RELDETR_FROZEN_TAG` を設定してから `train_t1a` を読み直し、
  `assert str(t1a.REGION_DIR).endswith(frozen_tag)` で経路を実測で確かめている
- モデルは `TeCNO(num_stages=2, num_layers=8, num_f_maps=64, in_dim=5888, num_classes=9)`
  （`train_t1a.py` の既定値 485-487 行）
- `load_state_dict(..., strict=True)`
- 評価は `t1a.evaluate(model, clips, device)` をそのまま呼ぶ

### 5.2 使った計算資源と所要時間

| 実行 | 装置 | 全体の実時間 |
|---|---|---|
| 1 回目 | CUDA（RTX A6000 1 枚） | 3.49 s |
| 2 回目 | CUDA（同上） | 実測（決定性の対照） |
| 3 回目 | CPU | 2.28 s |

**六 run 合わせて数秒である。**特徴キャッシュを読むだけで学習は行っていない。

### 5.3 再評価の結果（val, 1515 フレーム）

| side | seed | acc | hemostasis F1 |
|---|---|---|---|
| relationdetr | 42 | 0.9478547854785478 | 0.7741935483870968 |
| relationdetr | 123 | 0.9478547854785478 | 0.8245614035087719 |
| relationdetr | 456 | 0.9471947194719472 | 0.8041237113402062 |
| aligndetr | 42 | 0.8917491749174917 | 0.25 |
| aligndetr | 123 | 0.8752475247524752 | 0.21875 |
| aligndetr | 456 | 0.8686468646864687 | 0.06779661016949151 |

### 5.4 評価器の対照

    陽性（決定性）      : GPU 2 回が完全一致 = True
    陽性（異質な経路）  : CPU とも完全一致   = True
    陽性（保存値の再現）: 再評価 == checkpoint 内の保存値（差 < 1e-15）= True  ← 6/6
    陰性（別 ckpt で異値）: acc の相異なる値 5/6、hemostasis F1 の相異なる値 6/6

acc が 5/6 なのは relationdetr の seed42 と seed123 が完全同値だからである（§5.6）。
**hemostasis F1 は 6/6 すべて異なるため、「常に同じ値を返す壊れ方」ではない。**

### 5.5 Step C-2 第一層（seed 対応に依らない量）

許容差は記録の表示桁の丸め幅。再計算側は実測値（丸めていない）ので伝播は要らない。

| 量 | 再評価からの再計算 | 記録 | 許容差 | 判定 |
|---|---|---|---|---|
| relationdetr 平均 acc | 0.9476347635 | 0.9476 | ±5e-05 | 一致 |
| relationdetr acc pstd (ddof=0) | 0.0003111581 | 0.0003 | ±5e-05 | 一致 |
| relationdetr hemostasis F1 平均 | 0.8009595544 | 0.8010 | ±5e-05 | 一致 |
| relationdetr hemostasis F1 pstd | 0.0206839571 | 0.0207 | ±5e-05 | 一致 |
| aligndetr 平均 acc | 0.8785478548 | 0.8785 | ±5e-05 | 一致 |
| aligndetr acc pstd (ddof=0) | 0.0097159085 | 0.0097 | ±5e-05 | 一致 |
| aligndetr hemostasis F1 平均 | 0.1788488701 | 0.1788 | ±5e-05 | 一致 |
| aligndetr hemostasis F1 pstd | 0.0795554060 | 0.0796 | ±5e-05 | 一致 |
| 平均の差 (ali − rel) | −0.0690869087 | −0.06909 | ±5e-06 | 一致 |

**九量すべて一致。ばらつきの系統は ddof=0（pstd）で、前契約の確定と整合する。**

### 5.6 Step C-2 第二層（3×3 の全対応）

**順序を無視した照合では 2 通りが一致した。**

    rel42->ali42  rel123->ali123 rel456->ali456   一致
    rel42->ali123 rel123->ali42  rel456->ali456   一致
    （残り 4 通りは不一致）

縮退の原因は実測で特定できる。

    relationdetr seed42  acc = 0.9478547854785478
    relationdetr seed123 acc = 0.9478547854785478   ← 完全同値
    relationdetr seed456 acc = 0.9471947194719472

**acc が同値である以上、この 2 通りは acc からは区別できない。**

記録の三つ組は順序付きで書かれている（SPEC §1「paired 差（seed 対応）:
-0.0561 / -0.0726 / -0.0785」）。**並びが seed 42/123/456 の順だと解して照合すると一意になる。**

    rel42->ali42 rel123->ali123 rel456->ali456   差=[-0.056106, -0.072607, -0.078548]  一致
    （残り 5 通りは不一致）
    一致する対応: 1 通り（一意）

恒等対応での seed 別 paired 差（全量）:

| seed | 再評価 | 4 桁表示 | 記録 | 判定 |
|---|---|---|---|---|
| 42 | −0.05610561056105612 | −0.0561 | −0.0561 | 一致 |
| 123 | −0.0726072607260726 | −0.0726 | −0.0726 | 一致 |
| 456 | −0.07854785478547854 | −0.0785 | −0.0785 | 一致 |

**陰性対照（記録の並びを崩す）:**

    並びを [-0.0726, -0.0561, -0.0785] にすると一致 1 通り（恒等対応を含む — 記録側の
      入れ替えは対応側の入れ替えと同値なので当然。検査が並びに感応している証拠）
    並びを [-0.0561, -0.0785, -0.0726] にすると一致 0 通り

### 5.7 集計器の対照（前契約で確立した器）

    陽性: mean(記録の paired 三件)=-0.069067 区間=[-0.069117,-0.069017] 記録=-0.06909  一致
    陰性: 1 件目を除く mean=-0.075550 区間=[-0.075600,-0.075500] 不一致（期待どおり）
    陰性: 2 件目を除く mean=-0.067300 区間=[-0.067350,-0.067250] 不一致（期待どおり）
    陰性: 3 件目を除く mean=-0.064350 区間=[-0.064400,-0.064300] 不一致（期待どおり）

---

## 6. 判定 f — orphan の不変

作業後の md5 を前契約 audit の記録（作業前）と照合した。

    $ diff <(sort md5_before.txt) <(sort md5_after.txt)
    （差分なし）  => 6/6 一致

**照合器が空振りでないことの確認**（複製はスクラッチパッド上で行い、`experiments/` には触れない）:

    複製の md5（加工前） : 95fc689143841d80f021bbb89160e95f   ← 原本と同値
    1 バイト足した後      : 5d7e62b21c2e5304538205cda7f11a5f   ← 不一致（期待どおり）
    大きさ 2599650 -> 2599651 バイト
    複製は削除した（ls が No such file or directory を返す）

`experiments/` `data/` への書き込み:

    $ git status --porcelain | grep -E '^.. (experiments/|data/)' | wc -l
    0

**六 run のディレクトリへ metrics を書き戻していない**（§7 禁止 2）。

---

## 7. 変更範囲と検査

### 7.1 変更の全量

    $ git status --porcelain
     M runindex/anomalies.md
     M runindex/anomalies/dedup_sensitivity.csv
     M runindex/anomalies/determinism_audit.csv
     M runindex/anomalies/paired_feasibility.csv
     M runindex/anomalies/within_vs_between_seed.csv
     M runindex/experiments.csv
     M runindex/index.csv
     M runindex/per_class.csv
     M runindex/verdicts.csv
    ?? runindex/runs/transfer__b2a_*.json           （61 件）
     M docs/stage0/A7_k1_provenance.md
     M docs/stage0/stage0_summary.md
    ?? docs/sessions/digest/2026-08-25-6ae159a7-8526-4c86-98a8-2a1367c72a6a.md
     M context/auto/*                               （投影の再生成）
     M tasks/inbox.md
    ?? tasks/T-2026-08-29-k1-reeval-and-harvest/
    ?? tasks/inbox.d/T-2026-08-29-k1-reeval-and-harvest.md

絞り込みごとの件数（同じ絞り込みが場所によって違う値を返すこと自体が、絞り込みの動作確認になる）:

    experiments/|data/ : 0
    runindex/          : 70   （未追跡 61 + 変更 9）
    docs/              : 3
    context/auto/      : 4
    tasks/             : 3

`docs/stage0/` の 2 文書は**追記のみ**である（削除・置換なし。§7 禁止 6 を満たす）。

### 7.2 検査の結果（終了コードを個別に測った）

zsh は配列添字で終了コードを取れないため、各命令を単独で走らせて `$?` を取った。

    make task-validate    -> exit=0
    make taskindex-check  -> exit=0
    make inbox-check      -> exit=0
    make context-check    -> exit=0
    make docs-check       -> exit=0
    make agent-check      -> exit=0
    make forbidden-check  -> exit=2   ← 下記

### 7.3 🔴 forbidden-check が exit 2 になる理由

    $ python tools/check_forbidden.py
    base=origin/phase0  changed=87  checked=79  excluded=8  status=fail  violations=70
    違反の接頭辞別: {'runindex/': 70}
    experiments/ data/ transfer/ の違反: 0

**違反 70 件はすべて `runindex/` である。** これは本契約 §2 が
「`runindex/` 配下（**make runindex による収穫のみ**）」として明示的に許可した出力そのもので、
自分が測った `runindex/` の変更 70 件と**集合として完全一致**した。

    違反 70 件 / 自分が測った runindex 変更 70 件 / 集合一致: True

`tools/check_forbidden.py` の `FORBIDDEN_PREFIXES` は
`runindex/ context/auto/ experiments/ transfer/ data/` を固定で持ち、
**契約ごとの許可を受け取る引数を持たない**（`--base` だけである）。
生成物の除外は `excluded_paths` の 8 件（`context/auto/` 7 件と `tasks/inbox.md`）に限られ、
収穫の出力は除外されない。

**したがって、収穫を行う契約はこの検査を原理的に通せない。**
実質的な要件である「`experiments/` `data/` へ触れていないこと」は **0 件**で満たしている。

同型の既知の問題が `tasks/inbox.d/T-2026-08-26-lovo-decision-rule.md` に記録されている
（`outputs.destination` が `experiments/` 配下の分析契約では必ず失敗する）。

### 7.4 判定 b の空振り確認（生成物の改変）

    加工前 sha256 = e422714da204d214ae84397c5679225dce928bae458408cf5fdfc3c22da41f27
    $ printf 'X' >> context/auto/tasks_summary.csv
    加工後 sha256 = 0adef3111787f720494ef8201119519d22120f25aa6ff3628f57fe829588646e

      make taskindex-check -> exit=2      ← 対応する検査だけが非零
      make inbox-check     -> exit=0
      make context-check   -> exit=0

    $ make taskindex     （再生成で復元）
    復元後 sha256 = e422714da204d214ae84397c5679225dce928bae458408cf5fdfc3c22da41f27  （一致）
      make taskindex-check -> exit=0
      make inbox-check     -> exit=0
      make context-check   -> exit=0

### 7.5 判定 a の差分検出器の対照

    陽性（収穫前 vs 収穫後）        : 追加 61 / 削除 0 / 変更 0
    陰性（収穫後 vs 収穫後・同一入力）: 追加 0  / 削除 0 / 変更 0

**同一入力で 0 件を返すことを確かめたので、上の 61 件は「何でも追加と言う壊れ方」ではない。**
