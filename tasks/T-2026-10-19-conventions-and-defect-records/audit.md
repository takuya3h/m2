# 実行監査

## 開始

開始前は feat/evidence-maps-revise、作業ツリー清浄、対象分岐・契約履歴はなし、.sync-pause なし。task-start が origin/phase0=5a8baa790fa31ced4c8b891f7ee5ed5906c9d775 を起点に feat/conventions-and-defect-records と本契約所有の .sync-pause を作成し、契約を取り込んだ。task-start exit 0、完了表示あり。

make task-validate TASK=T-2026-10-19-conventions-and-defect-records: exit 0、OK、1 task(s), 0 failed。

## プリフライト

命令: source .venv/bin/activate && CUDA_VISIBLE_DEVICES='' make task-preflight TASK=T-2026-10-19-conventions-and-defect-records

make 終了コード 2。出力（省略なし）:

```text
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   FAIL ディレクトリではありません: context/conventions.md
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 9 件を検査し該当なし
P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
P12 refs_resolved          SKIP 解決前提の参照は無い
P13 symmetry_table_complete SKIP kind=impl のため対象外（exp のみ）
P14 proposal_card_checked  SKIP kind=impl のため対象外（exp のみ）

RESULT: 5 PASS / 0 WARN / 8 SKIP / 1 FAIL
make: *** [Makefile:179: task-preflight] Error 1
```

task スキル第4節の非零終了時の停止規則に従い、Phase A〜G は未実行。規約・折り表・環境記録・既存の欠陥記録・検査器は変更していない。試験・実験・他ホスト接続は実行していない。

## 再開前の確認

利用者から起票者の是正指示を受領。分岐 feat/conventions-and-defect-records、HEAD と origin/phase0 はともに 5a8baa790fa31ced4c8b891f7ee5ed5906c9d775。前回停止時から HEAD は変化していない。

```text
?? tasks/T-2026-10-19-conventions-and-defect-records/RESULT.md
?? tasks/T-2026-10-19-conventions-and-defect-records/SPEC.md
?? tasks/T-2026-10-19-conventions-and-defect-records/audit.md
?? tasks/T-2026-10-19-conventions-and-defect-records/result.yaml
?? tasks/T-2026-10-19-conventions-and-defect-records/spec.yaml
?? tasks/inbox.d/T-2026-10-19-conventions-and-defect-records.md
```

同期ログの対象分岐の行を rg -n -F で検索: exit=1、一致0行。auto-merge の記録はなく、先頭の前後は同じ。ログの不在だけで全同期処理の不実行を断定しない。

git ls-remote --heads origin refs/heads/feat/conventions-and-defect-records: exit 0、出力なし。gh pr list --head feat/conventions-and-defect-records --state all: exit 0、[]。遠隔分岐・PRはない。 .sync-pause は存在しなかった。

再開は task スキルの再開規則を適用し、本契約の記録は退避しない。所有情報つきの .sync-pause を作成。

### 再開時 task-validate

```text
OK   T-2026-10-19-conventions-and-defect-records

1 task(s), 0 failed
exit=0
```

### 再開時 spec-check

```text
{
  "errors": [],
  "findings": [],
  "hits": 0,
  "hits_by_rule": {
    "allow_write_incomplete": 0,
    "forbidden_vs_output": 0,
    "gate_requires_report_before_end": 0,
    "host_mismatch": 0,
    "integration_prohibited_without_pause": 0,
    "reverify_contradiction": 0,
    "separated_source": 0,
    "truncation_in_measurement": 0,
    "unquoted_glob": 0
  },
  "rules_checked": 9,
  "status": "pass",
  "targets": 1
}
exit=0
```

### 再開時 task-preflight

```text
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-10-19-conventions-and-defect-records/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 9 件を検査し該当なし
P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
P12 refs_resolved          SKIP 解決前提の参照は無い
P13 symmetry_table_complete SKIP kind=impl のため対象外（exp のみ）
P14 proposal_card_checked  SKIP kind=impl のため対象外（exp のみ）

RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
exit=0
```

## Task A 変更前の基準

Python は CUDA_VISIBLE_DEVICES が空の状態で実行し、学習・推論は起動しない。データ配下は読まない。開始時の他契約の変更は0、前回の本契約記録だけのため退避0件。

```json
{
  "head": "5a8baa790fa31ced4c8b891f7ee5ed5906c9d775",
  "sections": {
    "split": "5b99f4f08e05d29c6d8198539a30afc42b6f7a872be8884cb51e37241420af13",
    "eval_recipe": "afd64bcbed262cb26ba4ec699939179769fde830974d81b446dfb5612c3b4435",
    "frozen_source": "9a06b1e529f63712964a1f3495c50ae99256cea0230f927347858a66e73377d6",
    "sigma": "5e8a8c10eb44b8d02ec894ad895edb8dde12b72870299c2abaefef3637a7d2c5",
    "prohibitions": "c49c636a26ed20831a43b72162d517767d4ec3cc53f1cb8558ed4616809955c3",
    "env_p0": "93eed5b3863c3073959c6ea8a93614697b566c7ac7e53f30cc9b8c103bc2412a",
    "naming": "a05b7816a8c4f39cfe13c49ca4867f0107e78429a8bac7290b2d9894e1aa22cc",
    "issuer_cautions": "6cee9470af9a077a41b1f6247b2f1b2f503bd28a1eeafc13235789b1def08c43",
    "proposal_gate": "0334fe900927ecff5b201c728ecc6b7986c24a93bcbc3bc46b47ff9f8e5ca30f",
    "folds": "8ddf520b8af467d43abc2c65a81c5ab256961afa55c5810c5f14662660b68936",
    "symmetry": "884a70648c6737921e744e5ccff8895228ddb1867d92ec11c3aee6ec7a1e37dc",
    "det_groups": "63947bc5e8612e3ff9918bac4eeecc33f029c3b1373133a00162b7373f48a4ab",
    "crossfit": "c9e73a2f9c4aea77f73be6da369525cc998fcc3aff9a92f10b55eba6257d85d8",
    "frame_sets": "ed8f488cb3836d623b1eba940d9d953aa1fa544446b172a6ca2b588a6f2fe422"
  },
  "anchors": [
    "split",
    "eval_recipe",
    "frozen_source",
    "sigma",
    "prohibitions",
    "env_p0",
    "naming",
    "issuer_cautions",
    "proposal_gate",
    "folds",
    "symmetry",
    "det_groups",
    "crossfit",
    "frame_sets"
  ],
  "known_hosts": {
    "/home/ubuntu/.ssh/known_hosts": "179b5d2ac1b63b7d634f66928d1e6835b161536346f7b78a1d20d514705ede05",
    "/home/ubuntu/.ssh/known_hosts2": null
  },
  "spec_md_sha256": "218651ec318cabbfc1f3e3ebc3a99115ebf2078202554b838feab8669289f5bb",
  "conventions_rev": "b12eda6cf0f53f4f0d09e5b6c53bb3afde9831ac",
  "runindex_commit": "63ae65da8c7d32df591f5e2ee4358286b72c726b",
  "counts": {
    "index": 1961,
    "experiments": 750,
    "verdicts": 1506
  }
}
```

命令: nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used --format=csv,noheader

```text
0, NVIDIA RTX A6000, 100 %, 5604 MiB
1, NVIDIA RTX A6000, 47 %, 18916 MiB
exit=0
```

命令: nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader

```text
exit=0
```

命令: .venv/bin/python tools/check_proposal.py docs/proposals/2026-09-27-ptower-20.md --json

```text
{
  "status": "pass",
  "path": "docs/proposals/2026-09-27-ptower-20.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 0,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 0
  },
  "findings": [],
  "errors": []
}
exit=0
```

命令: .venv/bin/python -m pytest tests/test_validate_task.py tests/test_preflight_task.py tests/test_check_proposal.py tests/test_check_forbidden.py --continue-on-collection-errors --junitxml=tasks/T-2026-10-19-conventions-and-defect-records/tests-before.xml -q

```text
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 4.64s
exit=0
```

Task A-5: 起票時の版・件数と実測が全て一致。更新なし。

## 関門 G1・G2

G1 pass: 分岐・起点・所有情報が一致、他契約の変更なし。装置を利用しない実行条件と基準試験96 pass、カード検査exit 0を記録した。

G2 pass: 変更節は symmetry / folds / crossfit / naming、新設 precision。既存アンカー削除・重複なし、全アンカーが正規表現で解決。

|節|変更前 SHA-256|変更後 SHA-256|
|---|---|---|
|crossfit|c9e73a2f9c4aea77f73be6da369525cc998fcc3aff9a92f10b55eba6257d85d8|758dd9bfae6160e5c9290463252c85f673194859b73261316bdfec76524693fb|
|det_groups|63947bc5e8612e3ff9918bac4eeecc33f029c3b1373133a00162b7373f48a4ab|63947bc5e8612e3ff9918bac4eeecc33f029c3b1373133a00162b7373f48a4ab|
|env_p0|93eed5b3863c3073959c6ea8a93614697b566c7ac7e53f30cc9b8c103bc2412a|93eed5b3863c3073959c6ea8a93614697b566c7ac7e53f30cc9b8c103bc2412a|
|eval_recipe|afd64bcbed262cb26ba4ec699939179769fde830974d81b446dfb5612c3b4435|afd64bcbed262cb26ba4ec699939179769fde830974d81b446dfb5612c3b4435|
|folds|8ddf520b8af467d43abc2c65a81c5ab256961afa55c5810c5f14662660b68936|19251e44541355cbed8b95d3a0194060856596109574b36f4aa586b5dda3c5da|
|frame_sets|ed8f488cb3836d623b1eba940d9d953aa1fa544446b172a6ca2b588a6f2fe422|ed8f488cb3836d623b1eba940d9d953aa1fa544446b172a6ca2b588a6f2fe422|
|frozen_source|9a06b1e529f63712964a1f3495c50ae99256cea0230f927347858a66e73377d6|9a06b1e529f63712964a1f3495c50ae99256cea0230f927347858a66e73377d6|
|issuer_cautions|6cee9470af9a077a41b1f6247b2f1b2f503bd28a1eeafc13235789b1def08c43|6cee9470af9a077a41b1f6247b2f1b2f503bd28a1eeafc13235789b1def08c43|
|naming|a05b7816a8c4f39cfe13c49ca4867f0107e78429a8bac7290b2d9894e1aa22cc|50a0127a97a38e3d19fbcc254735ec1868cd0b2c1a5e322a918b558aa25dcb7c|
|precision|新設|d7d3f5c87d19e3422c94221d6ca76f63285df2ebd95b452c8ee9145edebf5903|
|prohibitions|c49c636a26ed20831a43b72162d517767d4ec3cc53f1cb8558ed4616809955c3|c49c636a26ed20831a43b72162d517767d4ec3cc53f1cb8558ed4616809955c3|
|proposal_gate|0334fe900927ecff5b201c728ecc6b7986c24a93bcbc3bc46b47ff9f8e5ca30f|0334fe900927ecff5b201c728ecc6b7986c24a93bcbc3bc46b47ff9f8e5ca30f|
|sigma|5e8a8c10eb44b8d02ec894ad895edb8dde12b72870299c2abaefef3637a7d2c5|5e8a8c10eb44b8d02ec894ad895edb8dde12b72870299c2abaefef3637a7d2c5|
|split|5b99f4f08e05d29c6d8198539a30afc42b6f7a872be8884cb51e37241420af13|5b99f4f08e05d29c6d8198539a30afc42b6f7a872be8884cb51e37241420af13|
|symmetry|884a70648c6737921e744e5ccff8895228ddb1867d92ec11c3aee6ec7a1e37dc|65035f6f85bc909129ec24a1df5b2fa6ca4f9683d84c86ed55fa8d5611149265|

提案カード検査のコマンドは Task A と同じ。終了コード・stdout・stderr がバイト単位で前後一致。

```json
{
  "status": "pass",
  "path": "docs/proposals/2026-09-27-ptower-20.md",
  "only": "both",
  "words_checked": 15,
  "card_items": 16,
  "numeric_items": [
    5,
    6,
    10
  ],
  "hits": 0,
  "hits_by_kind": {
    "forbidden_word": 0,
    "missing_heading": 0,
    "missing_number": 0
  },
  "findings": [],
  "errors": []
}
```

## 内容の突き合わせと出所（Task B〜F）

|SPEC項目|規約の一致した文言|規約の行|
|---|---|---|
|5.1-1|入力の縮小規則（短辺の目標と長辺の上限）|367|
|5.1-2|画面の残る割合（切り出し）が両腕で同じ|368|
|5.1-3|入力の切り出し（画面の残る割合）|369|
|5.1-4|切り出しの行は「揃える」、縮小規則の行は「意図的に変える」で理由 3|373|
|5.1-5|1333×749（pad 後 1344×768）、工程塔は 800×1422|374|
|5.1-6|同じ塔の変種どうし|371|
|5.1-7|入力の縮小規則の出所: 利用者の決定 2026-10-18|376|
|5.2-1|評価 recipe／ホストと装置型|382|
|5.2-2|ホストの行は「揃える」以外にしない。理由 1〜3 のどれも使わない|386|
|5.2-3|同じ設定を両方のホストで回した対照を置き|387|
|5.2-4|efros 0.7762、ilya 0.7066、差 +0.0696|390|
|5.2-5|標本 SD 0.0186 の 3.7 倍|391|
|5.2-6|利用者の決定 2026-10-06 と 2026-10-17|392|
|5.3-1|Tier 1 の全腕（分母の空入力界面を含む）|454|
|5.3-2|fp16 の autocast。凍結源と同じ|455|
|5.3-3|`torch.compile` は使わない|457|
|5.3-4|その学習が fp32 で始まることを実測する|458|
|5.3-5|計算器の日数は単精度の値|460|
|5.3-6|工程塔の学習の精度は本節で定めない|461|
|5.3-7|W1 で 1.182 倍、W2 で 1.286 倍速く、主指標の差は 0.030σ|462|
|5.3-8|torch.backends.cuda.matmul.allow_tf32 = True|459|
|5.4|22 はフレーム画像が無く使えない|310|
|5.5|20 件すべてで 3pt を超え、最小 +0.1254|428|

### 出所の引用


検出入力 — tasks/T-2026-10-17-tower-reselect-prereq/RESULT.md

```text
8: **縮小後 1333×749、pad 後 1344×768**（W×H）で、これまでの計算値 1333×750 とは縮小後の高さが 1 違う。
38: | g | 評価時の入力の大きさ | 達成 | 原寸 (H,W) = (1080,1920)（注釈 21 ファイル延べ 108,059 枚すべて）→ 縮小後 (749,1333)、pad 後 (768,1344)。val の 3 枚で実測 | 陽性: (1080,1080)→800×800、(1920,1080)→(1333,749)/(1344,768)、(480,640)→(800,1066)/(800,1088)。陰性: 同じ入力を二度通してテンソル同一（audit 305-335） |
48: | 評価時の入力の大きさ（W×H） | 原寸 1920×1080 → 縮小後 **1333×749** → pad 後 **1344×768**。`REPORT.md:200` の 1333×750 は丸めの違い（実装は `.to(int)` で切り捨て、`base_detector.py:49-50`） |
49: | 評価時の前処理 | `EvalResize(800, 1333)` → float 化 → ImageNet 正規化 → 32 の倍数へ右下を 0 で pad。`presets.detr`（学習時の多尺度）は `train_dataset` だけ |
```

工程入力 — tasks/T-2026-09-19-stage1-phase-tower-r3/RESULT.md

```text
34: | c | 全画面・短辺 800 | **達成** | 1920×1080 → `(3, 800, 1422)`。**残る割合 100.0%** | `EVAL_TRANSFORM` に `Crop` の行が無い。二周目の preset は `crop_size=[224]` で横に 49.2% しか残らない |
```

ホスト差 — tasks/T-2026-09-27-stage1-ptower-20/RESULT.md

```text
28: | G2（C の後） | **ask → 利用者の決定で続行** | efros 0.7762 / ilya 0.7066、差 **+0.0696**、閾値 0.0372（SD 比 3.7） |
37: | c | ホスト差 | **達成（判定は不合格）** | efros 0.7762 / ilya 0.7066、差 +0.0696 | SD の出所は三周目の `_059_` / `_064_` / `_069_`（0.7066 / 0.6884 / 0.7255）、標本 SD 0.0186。規則は結果前に `host_control_rule.json` へ |
```

TF32実測・fp32・compile — tasks/T-2026-09-17-amp-compile-timing/RESULT.md

```text
11: | G1（A の後） | pass | `train_t1b.py` に autocast / GradScaler / 半精度 / `torch.compile` が**各 0 件**であることを語の走査で示した。基準の step 時間を同じ道具で取り直し 0.4946 s（前契約 0.4937 s、差 +0.18%） |
33: | a | 現行の精度の特定 | **達成。** `autocast` `GradScaler` `float16` `bfloat16` `half` `fp16` `bf16` `torch.compile` `channels_last` が**各 0 件**。`amp` の 3 件は `GroupedBatchSampler`/`DataLoader`/`RandomSampler` の語中一致、`dtype` の 3 件は 96・135・199 行の `np.zeros(..., dtype=np.float32)`。学習ループ 364〜378 行は素の `model()`→`backward()`→`step()` |
36: | d | 主指標の比較 | **達成。** best の差 +0.0001364288 = **0.030σ**、全 epoch 最大 0.138σ。σ=0.004540 の出所は `t1b_filmonly_seed{42,123,456}`（mAP 0.736802/0.731410/0.725682、pstd） |
50: | fp32（現行） | 0.4611 s | 1.000× | 14,590,299,648 B | 0.5652 s | 1.000× | 13,619,660,288 B |
51: | **tf32** | **0.3902 s** | **1.182×** | 14,589,924,864 B | **0.4396 s** | **1.286×** | 13,613,707,264 B |
54: | compile 系 3 条件 | **完走しない** | — | — | — | — | — |
109: | `asserted_without_measuring` | SPEC §3 Task B の条件表は数値精度の手当てを半精度 2 種だけに限るが、実装は**行列積の TF32 を無効にしたまま**であり（`allow_tf32` の既定は matmul False / cudnn True）、**そこが最良条件だった**。表のとおりに測ると最良条件を取り逃す |
119:    `--tf32` と `--amp {no,bf16,fp16}` を足した。**既定は従来と同一の経路**
120:    （`--tf32` なしでは設定に触れず、`--amp no` では autocast も scaler も作らない）。
125: 6. `judgement` — `--tf32` は過程全体の設定のため**評価にも効く**。学習だけに限る実装も可能だったが、
```

TF32設定 — scripts/train_t1b.py

```text
356:     # TF32。**既定 off では設定に触れない**（触れること自体が既定値の再確認になり、
357:     # 将来 torch の既定が変わったときに挙動が固定されてしまうため）。
358:     if args.tf32:
359:         torch.backends.cuda.matmul.allow_tf32 = True
360:     # 自動混合精度。既定 no では autocast を張らず scaler も作らないため、経路は従来と同一。
361:     amp_dtype = {"bf16": torch.bfloat16, "fp16": torch.float16}.get(args.amp)
362:     scaler = torch.cuda.amp.GradScaler() if args.amp == "fp16" else None
```

cuDNN既定・評価 — tasks/T-2026-09-17-amp-compile-timing/audit.md

```text
73: 補足の実測: torch の既定では `torch.backends.cuda.matmul.allow_tf32` が False、
74: `torch.backends.cudnn.allow_tf32` が True である。すなわち**畳み込みは TF32 を使うが行列積は使っていない**。
75: これも数値精度の設定であるため、条件表へ `tf32` を加えた（SPEC §3 の表には無い条件。追加した理由を逸脱に記す）。
350: 🔴 `--tf32` は過程全体の設定であるため、**学習だけでなく評価にも効く**。
```

検出塔fp16 — tasks/T-2026-09-18-stage1-detector-towers/RESULT.md

```text
37: | a | 処方の特定と差分 | **達成。** 全項目を出所つきで特定（UNKNOWN 0 件）。差分は **0 項目**。🔴 ただし契約が言う「TF32 を除く」は成立しない——**凍結源は fp16 で学習されており**、利用者の判断で fp16 に揃えた（下記 4） |
42: | f | TF32 と所要時間 | **一部未達。** 🔴 **TF32 では回していない**（凍結源が fp16 のため。利用者の判断）。所要時間は全 14 run に記録（7:48:59〜9:13:30、平均 8.353 h）。計算器に実測が入り `measured: True`、`--check-doc` 差 0 件 |
50: `accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed42.py
51: --seed 42 --mixed-precision fp16`（run の `command.sh`）。12 epoch / `MultiStepLR(milestones=[10], gamma=0.1)` /
```

計算器 — tasks/T-2026-09-27-stage2-prep/RESULT.md

```text
67: 両端は報告値と一致した（試験 `test_history_reproduces_the_reported_values`）。**TF32 は計算器に一度も入っていない。**
68: 9/17 の 74.0〜98.7 日は計算器の外で W1 の倍率 1.182 を全行へ当てた値だった。W2 の補正（4.00 → 4.82 h）は両方に入っている。
70: ### Tier 1 の日数（交差適合、単精度、24 h/日、2 枚）と締切
```

追加動画 — tasks/T-2026-09-27-stage1-ptower-20/audit.md

```text
45: | 動画 22 | 注釈 22_1〜22_3 が `data/raw/OpenSurgery_Dataset/.../annotations/phase/` に在る。フレームは 0 件 |
100: `verify_folds` が 5 折りすべてで「train に増えたのは 17〜21 だけ、val・test は不変、22 は無い」を確かめた。
```

工程送り手の差 — tasks/T-2026-09-27-stage1-ptower-20/RESULT.md

```text
39: | e | 送り手の train と val の差 | **達成** | 4 塔 × 5 折り = 20 件、全件閾値超え | train 動画は run の config に刻まれた train と assert で一致（20/20）。gap で計算した val J は学習時の val J と最大差 0。壊した入力での確認は UNKNOWN |
80: | COCO | P\*-15 | +0.2521 | +0.1254 | +0.3259 | 5/5 |
81: | COCO | P\*-20 | +0.2510 | +0.1871 | +0.3376 | 5/5 |
82: | ImageNet | P\*-15 | +0.3968 | +0.2887 | +0.5626 | 5/5 |
83: | ImageNet | P\*-20 | +0.3449 | +0.2438 | +0.4622 | 5/5 |
85: frame accuracy の差も 20 件中 20 件が 0.03 を超えた（最小 +0.0477）。主指標と co-primary は食い違わない。
107: | 4 | 送り手の train と val の差は 3pt を超える | **当たり** | 20/20、最小 +0.1254 |
```

旧測定 — tasks/T-2026-08-22-philip-hub-foundation/audit.md

```text
419: ### Step 6: 待ち受けが立っていないことを確かめる
420: ```
421: count=5
422: port_22=LISTEN
423: port_22000=-
424: port_22001=-
425: port_8384=-
426: listening_ports=[22, 34399, 40935, 41913, 57098]
427: ```
```

旧測定の範囲 — tasks/T-2026-08-24-syncthing-config-survey/audit.md

```text
887: 中心が SSH を受けられるか（ノードの中継はここへ来る）。**局所の観測のみ。他ホストへは接続しない。**
890: 172.17.0.13 
920: 50072 待ち受け=no
930: | この中で SSH が待つ口は **22** | `port=22` が待ち受け中。**`50072` は待っていない** | philip は Docker の中にある。**`50072` は外側の写像**（外の `50072` → 中の `22`）であり、中からは見えない。契約の「SSH は `50072`」は**外から見た値として矛盾しない** |
933: | 契約の中心の住所 `192.168.196.150` | **局所からは検証できない** | 容器の外側（Docker ホスト）の住所と考えれば矛盾しない。**他ホストへ接続できない**ため（禁止 5）到達性は **UNKNOWN** |
```

新到達性 — tasks/T-2026-10-17-tower-reselect-prereq/audit.md

```text
150: ### C-1 経路
152: - `~/.ssh/config.d/aolabnet.conf` の `Host efros`（192.168.196.227:50072）へ andrew から**直接**届いた。中継は使っていない
153: - `context/env-facts.md` と SPEC §3 は「直接接続は不可で中継が要る」と書くが、実測では直接届いた（`hostname` → `efros`）
154: - 既知のホスト: `ssh-keygen -F "[192.168.196.227]:50072"` → 既知。念のため `~/.ssh/known_hosts` の写しを scratchpad に作り、
155:   `-o UserKnownHostsFile=<写し> -o StrictHostKeyChecking=yes -o BatchMode=yes` で接続した。`~/.ssh/known_hosts` の sha256 先頭 16 桁は前後とも `1e5ff1f5e8af7b7c`
156: - 資格情報は既存の鍵で足り、パスワードは求められなかった
```

欠陥1・2 — tasks/T-2026-10-17-tower-reselect-prereq/RESULT.md

```text
62: | asserted_without_measuring | §3 は「直接接続は不可で中継が要る（中心は philip）」と書くが、andrew から efros:50072 へ直接届いた。従うと不要な中継を組むことになる（audit 150-156） |
63: | asserted_without_measuring | Task D-4 は「検出器の専用の環境で試験が収集され全件通る」を求めるが、`.venv-relation-detr` に pytest が無い。従うと依存の追加が要る。本体 `.venv` で回した |
```

欠陥3 — tasks/T-2026-10-17-tower-reselect-prereq/spec.yaml

```text
13:   amendments:
14:     - date: "2026-10-17"
15:       reason: "L3 プリフライト P6 decisions_answered が FAIL（未回答 2 件）。利用者が回答した。決定1（efros に届かない、または収束規則の実装が二周目の写しと一致しない場合に andrew にどの版を置くか）: 事前に版を決めず、発火した時点で停止して諮る（SPEC §8 と同じ扱い）。決定2（どの snapshot にも無い andrew だけの改変が見つかった場合）: 残す（上書きしない。SPEC §4 Task D-3 と同じ）。二周目の学習に要るファイルと重なる場合だけ停止して諮る（SPEC §8）"
16:       diff: "governance.decisions_required の 2 件を回答済みとして空にした（回答は本 amendment の reason に記録）"
```

欠陥3再発 — tasks/inbox.d/T-2026-08-29-k1-verify-policy-place.md

```text
1: - [ ] 2026-08-29 [cc] **lecun の追跡外 run は索引へ収穫しない**（本契約は棚卸しのみ。収穫は別契約）と利用者から回答を得た。契約 §3 A-3 および §6 禁止 2 が既に同じ内容を定めており、本文が答えている問いを decisions_required に重ねて置いたため L3 の P6 が FAIL した（T-2026-08-26-lovo-decision-rule で提案済みの規約と同型の再発）。回答は spec.yaml の meta.amendments へ記録し decisions_required を空にした（T-2026-08-29-k1-verify-policy-place）
```

欠陥4 — tasks/T-2026-09-19-stage1-phase-tower-r3/prereg.md

```text
33: | 入力 | 短辺 256 → 中央 224 | **短辺 800、全画面（切り出しなし）** | D\* の評価解像度と同じ。画面の残る割合 100% |
63: | 入力解像度と切り出し（残る割合） | 短辺 480〜800、全画面 100% | 短辺 800、全画面 100% | 揃える | D の評価解像度に固定。多尺度は増強の行 |
```

欠陥5の実装 — scripts/stage1_ptower_r3.py

```text
129: def stem_eval(model):
130:     """Keep the frozen stem's batch statistics fixed while the rest trains."""
131:     model.train()
132:     model.conv1.eval()
133:     model.bn1.eval()
211:         stem_eval(model)
```

### 保持・陽性対照

折り表の変更前の行集合 − 変更後の行集合 = []。識別子6本、重複0件、陽性対照の行は全て保持。crossfit の3pt閾値の行は前後完全一致。

```json
[
  {
    "judgement": "a: SPEC5.1との対応",
    "breaking_input": "メモリ上の規約の写しから入力の縮小規則の使える行の項目だけを除く",
    "observed": "5.1-1 の対応が不一致になった。原文では全23項目が一致した。"
  },
  {
    "judgement": "f: 節ハッシュ",
    "breaking_input": "メモリ上の規約の写しの sigma 見出しを一文字変える",
    "observed": "sigma だけが追加の変更節として検出された。"
  },
  {
    "judgement": "d: 折り表の既存行保持",
    "breaking_input": "既存行が一件でも消えれば集合差で検出する",
    "observed": "既存行の集合差は空。注記を追加した。"
  },
  {
    "judgement": "P7 destination",
    "breaking_input": "既存ファイルを destination に指定する（是正前）",
    "observed": "是正前 FAIL、起票者指定の是正後 PASS（初回と再開時の実測ログ）。"
  }
]
```

### 対照の初回の空振りと再測定

allow_write を外した写しへの check_spec は初回 exit 0 / hits=0 となり、対照の assert が失敗した。rule_allow_write_incomplete の完了済み契約除外（tools/check_spec.py:510-514）が、前回停止報告の gates.verdict を完了扱いにしていた。再開した result.yaml を partial / gates=[] に更新した（停止までの記録は本auditに保持）。検査器は変更しない。

命令: make spec-check TASK=T-2026-10-19-conventions-and-defect-records

```text
{
  "errors": [],
  "findings": [],
  "hits": 0,
  "hits_by_rule": {
    "allow_write_incomplete": 0,
    "forbidden_vs_output": 0,
    "gate_requires_report_before_end": 0,
    "host_mismatch": 0,
    "integration_prohibited_without_pause": 0,
    "reverify_contradiction": 0,
    "separated_source": 0,
    "truncation_in_measurement": 0,
    "unquoted_glob": 0
  },
  "rules_checked": 9,
  "status": "pass",
  "targets": 1
}
exit=0
```

命令: .venv/bin/python tools/check_spec.py --path tasks/T-2026-10-19-conventions-and-defect-records/SPEC.md --spec tasks/T-2026-10-19-conventions-and-defect-records/positive-without-destination-allowance.yaml

```text
{
  "errors": [],
  "findings": [
    {
      "detail": "contract.allow_write context/conventions.md が覆っていない: outputs.destination tasks/T-2026-10-19-conventions-and-defect-records/。指示どおり実行すると make forbidden-check が落ちるか、どこへ書く契約かが宣言から読めない",
      "file": "tasks/T-2026-10-19-conventions-and-defect-records/positive-without-destination-allowance.yaml",
      "line": 56,
      "rule": "allow_write_incomplete",
      "rule_class": "structural",
      "task": "T-2026-10-19-conventions-and-defect-records"
    }
  ],
  "hits": 1,
  "hits_by_rule": {
    "allow_write_incomplete": 1,
    "forbidden_vs_output": 0,
    "gate_requires_report_before_end": 0,
    "host_mismatch": 0,
    "integration_prohibited_without_pause": 0,
    "reverify_contradiction": 0,
    "separated_source": 0,
    "truncation_in_measurement": 0,
    "unquoted_glob": 0
  },
  "rules_checked": 9,
  "status": "fail",
  "targets": 1
}
exit=1
```

### 禁止領域検査の陰性対照（repo外の隔離した写し）

場所: /tmp/m2-forbidden-control-sul12p6f。既存の検査器と生成物の場所を読むモジュール、Makefile、specの写しと既存venvへのリンクだけを用意。生成物の再生成はしない。
命令: make forbidden-check BASE=HEAD TASK=T-2026-10-19-conventions-and-defect-records

```text
{"base": "HEAD", "changed": 0, "checked": 0, "declared_allowances": ["context/conventions.md", "tasks/T-2026-10-19-conventions-and-defect-records/"], "effective_allowances": ["context/conventions.md", "tasks/T-2026-10-19-conventions-and-defect-records/"], "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "permitted": [], "rejected_allowances": [], "status": "pass", "task": "T-2026-10-19-conventions-and-defect-records", "violations": []}
exit=0
```

### 禁止領域検査の陽性対照（repo外の隔離した写し）

場所: /tmp/m2-forbidden-control-sul12p6f。既存の検査器と生成物の場所を読むモジュール、Makefile、specの写しと既存venvへのリンクだけを用意。生成物の再生成はしない。
命令: make forbidden-check BASE=HEAD TASK=T-2026-10-19-conventions-and-defect-records

```text
{"base": "HEAD", "changed": 1, "checked": 1, "declared_allowances": ["context/conventions.md", "tasks/T-2026-10-19-conventions-and-defect-records/"], "effective_allowances": ["context/conventions.md", "tasks/T-2026-10-19-conventions-and-defect-records/"], "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "permitted": [], "rejected_allowances": [], "status": "fail", "task": "T-2026-10-19-conventions-and-defect-records", "violations": [{"path": "data/forbidden-control.txt", "reason": "禁止領域 data/ の内側"}]}
make: *** [Makefile:159: forbidden-check] Error 1
exit=2
```

### Task G 検証

命令: .venv/bin/python -m pytest tests/test_validate_task.py tests/test_preflight_task.py tests/test_check_proposal.py tests/test_check_forbidden.py --continue-on-collection-errors --junitxml=tasks/T-2026-10-19-conventions-and-defect-records/tests-after.xml -q

```text
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 3.64s
exit=0
```

### Task G 検証

命令: make task-validate TASK=T-2026-10-19-conventions-and-defect-records LEVEL=l1

```text
OK   T-2026-10-19-conventions-and-defect-records

1 task(s), 0 failed
exit=0
```

### Task G 検証

命令: make task-validate TASK=T-2026-10-19-conventions-and-defect-records LEVEL=l2

```text
OK   T-2026-10-19-conventions-and-defect-records

1 task(s), 0 failed
exit=0
```

### Task G 検証

命令: make forbidden-check TASK=T-2026-10-19-conventions-and-defect-records

```text
{"base": "origin/phase0", "changed": 18, "checked": 18, "declared_allowances": ["context/conventions.md", "tasks/T-2026-10-19-conventions-and-defect-records/"], "effective_allowances": ["context/conventions.md", "tasks/T-2026-10-19-conventions-and-defect-records/"], "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "permitted": [{"path": "context/conventions.md", "reason": "契約の allow_write context/conventions.md により許可"}], "rejected_allowances": [], "status": "pass", "task": "T-2026-10-19-conventions-and-defect-records", "violations": []}
exit=0
```

### Task G 検証

命令: make spec-check TASK=T-2026-10-19-conventions-and-defect-records

```text
{
  "errors": [],
  "findings": [],
  "hits": 0,
  "hits_by_rule": {
    "allow_write_incomplete": 0,
    "forbidden_vs_output": 0,
    "gate_requires_report_before_end": 0,
    "host_mismatch": 0,
    "integration_prohibited_without_pause": 0,
    "reverify_contradiction": 0,
    "separated_source": 0,
    "truncation_in_measurement": 0,
    "unquoted_glob": 0
  },
  "rules_checked": 9,
  "status": "pass",
  "targets": 1
}
exit=0
```

### Task G 検証

命令: git diff --check

```text
exit=0
```

### Task G 検証

命令: nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used --format=csv,noheader

```text
0, NVIDIA RTX A6000, 99 %, 3364 MiB
1, NVIDIA RTX A6000, 100 %, 18916 MiB
exit=0
```

### Task G 検証

命令: nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader

```text
exit=0
```

### 試験失敗・収集エラーの名前集合と接続記録

変更前=[]、変更後=[]、増加集合=[]。両方96 passed。

/home/ubuntu/.ssh/known_hosts: before=179b5d2ac1b63b7d634f66928d1e6835b161536346f7b78a1d20d514705ede05 / after=179b5d2ac1b63b7d634f66928d1e6835b161536346f7b78a1d20d514705ede05 一致。内容は出力しない。

/home/ubuntu/.ssh/known_hosts2: before=None / after=None 一致。内容は出力しない。

本契約の操作で他の計算ホストにSSH接続した件数は0。GitHubへの分岐・PR照会等は契約手順の外部サービス利用である。既知ホスト記録の不変性だけでは既知鍵を使った接続の不在を証明しないため、実行した操作の記録と併せて確認した。

### 折り表の保持判定の陽性対照

メモリ上の写しから識別子（6 本）の行だけを除くと、変更前 − 写し の集合差はその一行だけ。実ファイルは変えず、実ファイルとの集合差は0行。

### 現行の完了判定

a: SPEC5.1の全項目が対応表で一致。b: ホスト規則・全数値・出所一致。c: precision各行の引用と実装確認済み。d: 正本の既存行の集合差0。e: 3pt閾値行は完全一致。f: 意図した節のみ変更、アンカーは既存集合+precision。g: 元の経路不明を明記し直接到達の別経路と区別。h: 欠陥5件の出所・対処とstem_evalの本体を記録。i: GPU計算起動0、実repoのdataアクセス0、他計算ホスト接続0。j: PR起票後に記録。

## 中断後の再開と変更履歴の確定

中断後の分岐 feat/conventions-and-defect-records、HEAD be3e16bea38038a36accd15807c2832c3a0b8b72、作業ツリー清浄、同期抑止は本契約の所有。PR照会は[]。

規約の変更履歴に実装commit be3e16beを記入。この記入による変更節はnamingだけ。Task Aとの比較は既存4節の変更とprecisionの新設だけのまま。全アンカー解決、既存カードの出力・終了コードはTask Aと完全一致。SPEC.md要約値は取り込み時と一致。

最終naming SHA-256: 34f4804503355f6166b9c92025d5fa601420b98bd78c2afd9edaec5322b7ee2b。全節の最終値は sections-after.json。

## PR・最終報告

git push -u origin feat/conventions-and-defect-records: exit 0。gh pr create --base phase0 --head feat/conventions-and-defect-records --title <題名> --body-file /tmp/conventions-and-defect-records-pr.md: exit 0。
gh pr view の応答:

```json
{
  "number": 237,
  "url": "https://github.com/takuya3h/m2/pull/237",
  "baseRefName": "phase0",
  "headRefName": "feat/conventions-and-defect-records",
  "isDraft": false,
  "state": "OPEN"
}
```

result.yamlは結果schemaで検証済み。origin/phase0との差分経路集合を許可範囲と照合し、範囲外0件（18件）:

```text
context/conventions.md
context/env-facts.md
docs/issuer-defects.md
docs/stage0/A1_fold_table.md
tasks/T-2026-10-19-conventions-and-defect-records/RESULT.md
tasks/T-2026-10-19-conventions-and-defect-records/SPEC.md
tasks/T-2026-10-19-conventions-and-defect-records/audit.md
tasks/T-2026-10-19-conventions-and-defect-records/baseline.json
tasks/T-2026-10-19-conventions-and-defect-records/positive-controls.json
tasks/T-2026-10-19-conventions-and-defect-records/positive-without-destination-allowance.yaml
tasks/T-2026-10-19-conventions-and-defect-records/result.yaml
tasks/T-2026-10-19-conventions-and-defect-records/resume-spec-before.yaml
tasks/T-2026-10-19-conventions-and-defect-records/resume-spec-md.sha256
tasks/T-2026-10-19-conventions-and-defect-records/sections-after.json
tasks/T-2026-10-19-conventions-and-defect-records/spec.yaml
tasks/T-2026-10-19-conventions-and-defect-records/tests-after.xml
tasks/T-2026-10-19-conventions-and-defect-records/tests-before.xml
tasks/inbox.d/T-2026-10-19-conventions-and-defect-records.md
```

最終のforbidden-checkは契約指定でexit 0 / violations=[]、git diff --checkはexit 0。
