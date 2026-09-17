# RESULT — T-2026-09-17-amp-compile-timing

ホスト `efros`（RTX A6000 × 2 / driver 595.84 / nvcc 12.9 / torch 2.1.2+cu118）。2026-09-17 JST。

## 判定

`verdict: pass`。問いに答えが出て、完了判定 a〜h を実測で埋めた（a の基準側の時間だけ UNKNOWN）。

| Gate | 判定 | 何を実測したか |
|---|---|---|
| G1（A の後） | pass | `train_t1b.py` に autocast / GradScaler / 半精度 / `torch.compile` が**各 0 件**であることを語の走査で示した。基準の step 時間を同じ道具で取り直し 0.4946 s（前契約 0.4937 s、差 +0.18%） |
| G2（B の後） | pass | 5 条件 + TF32 を同一バッチ列（要約値で確認）で測り、短長の測定で倍率が一致した。最良条件は **tf32** |
| G3（C の後） | pass | 主指標の差は best で **0.030σ**、全 epoch で最大 **0.138σ**。散らばりの内側 |

## 1. 解決された参照

- `contract.inject_verbatim` = `conventions#prohibitions` / `conventions#issuer_cautions` /
  `conventions#frozen_source`。原文は `context/conventions.md` rev
  `e7a5100597a79b3b9c60935bf38d232f8ae96822` の該当アンカー。要約していない。
- `inputs.sigma_policy` は省略のため `conventions#sigma` の既定値を継承
  （`series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired`）。
  **本契約は主指標の比較に使うため実際に適用した**（σ は pstd を採る）。
- 凍結源は `conventions#frozen_source` の記載と実測が一致
  （sha256 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` / 195,421,066 bytes）。変更していない。
- 占位の差し替え: `conventions_rev` = `e7a5100597a79b3b9c60935bf38d232f8ae96822`、
  `runindex_commit` = `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5`、
  `counts` = index 1266 / experiments 285 / verdicts 1506。

## 2. 完了判定

| # | 判定 | 実測 |
|---|---|---|
| a | 現行の精度の特定 | **達成。** `autocast` `GradScaler` `float16` `bfloat16` `half` `fp16` `bf16` `torch.compile` `channels_last` が**各 0 件**。`amp` の 3 件は `GroupedBatchSampler`/`DataLoader`/`RandomSampler` の語中一致、`dtype` の 3 件は 96・135・199 行の `np.zeros(..., dtype=np.float32)`。学習ループ 364〜378 行は素の `model()`→`backward()`→`step()` |
| b | 条件ごとの step 時間 | **達成。** 下表。同一バッチは形の列の要約値で示した（40 step の 3 走行がいずれも `17bef89b…`）。保持バッチ数を変えると要約値も倍率も変わる（`7355892c…`、bf16 1.204→1.174） |
| c | 計時の妥当性 | **達成。** 短(40)と長(200)で倍率が一致（tf32 1.195/1.182、bf16 1.204/1.174、fp16 1.176/1.169）。同期を取らない値も併記し、見かけの短縮が条件ごとに 1.2〜12.3% と**異なる**ことを示した |
| d | 主指標の比較 | **達成。** best の差 +0.0001364288 = **0.030σ**、全 epoch 最大 0.138σ。σ=0.004540 の出所は `t1b_filmonly_seed{42,123,456}`（mAP 0.736802/0.731410/0.725682、pstd） |
| e | 数値の異常 | **達成。** Task B の全条件・Task C とも**非有限 0 件・中央の 3 倍超 0 件**。Task C は損失 150 点、中央 14.9115。ただし**基準 run の step 別の損失は記録に無く**、並べられるのは epoch 別 val mAP まで |
| f | 日数の差し戻し | **達成。** 単精度 159.9〜218.2 日 → 最良条件 135.3〜184.7 日（12h/日・Stage 1 + Tier 1・縮退なし）。`--check-doc` 差 **0 件** |
| g | 一時領域 | **達成。** 前契約の終了時点 6,827,503,447 bytes、本契約の開始時点 **0 bytes**（前契約の報告時に提示し、利用者の指示で削除済み） |
| h | PR | **達成。** #182・base `phase0`・`isDraft: false`・分岐 `feat/amp-compile-timing` |

## 3. 実測

**答え: 数値精度は効く。計算グラフの最適化は使えない。**

### 条件ごとの step 時間（W1 長 200 step / W2 短 40 step）

| 条件 | W1 1 step | W1 倍率 | W1 記憶の山 | W2 1 step | W2 倍率 | W2 記憶の山 |
|---|---:|---:|---:|---:|---:|---:|
| fp32（現行） | 0.4611 s | 1.000× | 14,590,299,648 B | 0.5652 s | 1.000× | 13,619,660,288 B |
| **tf32** | **0.3902 s** | **1.182×** | 14,589,924,864 B | **0.4396 s** | **1.286×** | 13,613,707,264 B |
| bf16 | 0.3927 s | 1.174× | 12,726,704,640 B | 0.4503 s | 1.255× | 9,929,365,504 B |
| fp16 | 0.3945 s | 1.169× | 12,726,155,776 B | 0.4613 s | 1.225× | 9,920,399,360 B |
| compile 系 3 条件 | **完走しない** | — | — | — | — | — |

TF32 は記憶の表現を変えないため山も変わらない（−0.003%）。半精度は W1 で 12.8%、W2 で 27.1% 減る。
**W2 のほうが効く**（学習対象が 266,880 → 25,505,568 param で逆伝播の行列積が増えるため）。

### Task C（最良条件 tf32 で折り A を 6 epoch）

| 指標 | 基準 fp32 | tf32 | 差 | abs(差)/σ |
|---|---:|---:|---:|---:|
| init | 0.7302938995 | 0.7302930990 | −0.0000008004 | 0.0002 |
| best | 0.7335755045（ep2） | 0.7337119334（ep2） | +0.0001364288 | **0.0301** |
| final（ep5） | 0.7313710102 | 0.7313652919 | −0.0000057183 | 0.0013 |

全 epoch の最大は 0.138σ（ep0）。最良 epoch も ep2 で一致。**ビット一致ではない**
（TF32 は評価にも効くため恒等点でも −0.0000008 出る）が、差は σ の 1/5000 である。

| 量 | 実測 |
|---|---:|
| tf32 run の壁時計 | 13,466 s = **3.7406 h**（11:29:54 → 15:14:20 UTC） |
| tf32 run の GPU 時間 | **3.7406 GPU 時間**（GPU 0 を占有。走行中 GPU 1 の compute プロセス 0 件） |
| tf32 run 内の 1 step | **0.4225 s**（2.367 it/s） |
| 同一ホストの fp32 の 1 step | 0.4946 s（2.022 it/s） |
| run 内での実測倍率 | **1.171×**（Phase B の予測 1.182× と 1% 以内で一致） |

### Tier 1 の日数

`det_iface_w2` を 4.00 h → **4.82 h** に直し（前契約の実測比 1.205 から導出。`measured` は False のまま）、
`docs/stage0/B1_tier1_cost_estimate.md` の 8 区画を再生成した（`--check-doc` 差 0 件）。
検出側の行が GPU 時間の **99.9%** を占めるため、全行へ倍率を当てる近似の誤差は 0.2% 未満である。

| 前提 | 単精度 | 最良条件（tf32・1.182×） |
|---|---:|---:|
| 24h/日・Stage 1 + Tier 1〜3・縮退なし | 87.5〜116.6 日 | **74.0〜98.7 日** |
| 12h/日・Stage 1 + Tier 1・縮退なし | 159.9〜218.2 日 | **135.3〜184.7 日** |
| 12h/日・Stage 1 + Tier 1・縮退段 3 | 96.2〜131.2 日 | **81.4〜111.0 日** |

締切の判定が 2 箇所で変わる。縮退なしの MICCAI 2027 が「収まらない」→「読みにより分かれる」、
縮退段 3 の IPCAI long abstract が「読みにより分かれる」→**「収まる」**。
IPCAI intention（残 39 日）はどちらでも収まらない。**W1 の倍率を全行に当てた控えめな値である。**

### 前契約の日数の訂正

前契約 `C1` §7 と `RESULT.md` は「縮退なし（K=3・装置 2・**24h/日**）: 153.1〜208.7 日」と書いたが、
**括弧の前提が誤り**である。153.1〜208.7 は `deadline_sensitivity` 節（**12h/日・Stage 1 + Tier 1 のみ**）
の値で、24h/日・全体なら 84.1〜111.9 日が正しい
（`stage1_plus_tier1.wall_low = 1836.74 ÷ 12 = 153.06`、`all.wall_low = 2017.53 ÷ 24 = 84.06`）。
数値は計算器の出力のままで、誤っているのは添えた前提の記述である。

## 4. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | SPEC §2 は「前契約は `scripts/profile_t1b_step.py` を新設した。本契約でも使える」と書くが、`make task-start` は `origin/phase0` を起点に分岐を作り、前契約の PR #181 は未併合（`mergedAt: null`）のため**本分岐に存在しなかった**。指示どおり進めると Task A-4（同じ道具での取り直し）が実行できない |
| `check_does_not_check` | `plan.env.preflight` が `venv_active` のみのため、**GPU を使う契約でありながら** P2 `cuda_ext_loaded` と P11 `gpu_free` が SKIP になる。指示どおり実行すると、CUDA 拡張が読めるかも装置が空いているかも検査されないまま実行に入る。実際に開始時の装置は 2 枚とも占有されていた |
| `asserted_without_measuring` | SPEC §2 は「`torch.compile` は 2.1 系では動くが、DETR 系の動的な形に**弱い場合がある**」と書くが、実測では 3 条件とも例外で**動かない**。回避設定でも非数が出る。「弱い場合がある」ではなく完走しない |
| `asserted_without_measuring` | SPEC §3 Task B の条件表は数値精度の手当てを半精度 2 種だけに限るが、実装は**行列積の TF32 を無効にしたまま**であり（`allow_tf32` の既定は matmul False / cudnn True）、**そこが最良条件だった**。表のとおりに測ると最良条件を取り逃す |

## 5. 逸脱

1. `judgement` — 前契約の `scripts/profile_t1b_step.py` を
   `git checkout feat/frozen-feature-cache-timing -- <path>` で取り寄せた（取り寄せ後の差分 0 行）。
   分岐の統合はしていない。PR #181 が先に併合されても同一内容のため衝突しない。
2. `judgement` — 条件表に `tf32` を足した。SPEC §3 の表には無いが、Task A-3 で
   行列積の TF32 が無効と分かったため。結果として最良条件だった。
3. `spec_defect` — `scripts/bench_t1b_precision.py` を新設し、`scripts/train_t1b.py` に
   `--tf32` と `--amp {no,bf16,fp16}` を足した。**既定は従来と同一の経路**
   （`--tf32` なしでは設定に触れず、`--amp no` では autocast も scaler も作らない）。
4. `environment` — `pkill -f bench_t1b_precision` が**自分の命令行に一致して自滅**した（exit 144）。
   `conventions#issuer_cautions` 6 の実例。以後は部分一致を使っていない。
5. `environment` — `main()` 内の `import torch._dynamo` が `torch` を局所名にして module 側を隠し、
   `UnboundLocalError` で tf32 の測定が 1 度落ちた。`from torch import _dynamo` へ直した。
6. `judgement` — `--tf32` は過程全体の設定のため**評価にも効く**。学習だけに限る実装も可能だったが、
   採用の判断材料としては run 全体で一貫させるほうが正しいと判断した。
7. `judgement` — `det_iface_w1` を 4.00 h のまま据え置いた。本ホストの実測は 4.18 h だが
   出所の「約 4 時間」の精度の内側であり、1 ホストの計時で正本を動かすのは過剰と判断した。
8. `judgement` — Task C は GPU 0 のみを使い、GPU 1 は空いたままにした。`train_t1b.py` は
   単一プロセス実装で DDP 起動の記述がリポジトリに無く、1 run を 2 枚へ分散できないため。

## 6. 想定外・UNKNOWN

1. **基準 run の壁時計と GPU 時間。** 証跡に時間の列が無く、本ホストで fp32 の 6 epoch を
   回していない。step 実測から積むと 4.23 h だが**導出値であり実測ではない**。
2. **基準 run の step 別の損失。** 記録に存在しない。並べられるのは epoch 別の val mAP まで。
3. **`torch.compile` の上乗せ分。** 実装を改変しないと完走しないため測っていない（利用者の判断）。
4. **bf16 / fp16 での折り A の主指標。** Task C は最良条件（tf32）の 1 本のみ。
5. **半精度で減った記憶領域のぶんバッチを増やした場合の倍率。** 処方の変更にあたるため測っていない。
6. 工程側（TeCNO 系）に同じ手当てが効くか。本契約は検出側だけを測った。

## 7. 送出

| 項目 | 値 |
|---|---|
| `make task-validate` | exit 0（`OK` / 0 failed） |
| `make task-preflight`（`.venv-relation-detr`） | **exit 0**。6 PASS / 0 WARN / 6 SKIP / 0 FAIL。SKIP は P2・P3・P4・P5・P11・P12 |
| `make forbidden-check TASK=...` | **status pass / violations 0 / permitted 9 / rejected 0**（宣言なしでは fail・violations 9） |
| `make spec-check` | exit 0 / `"status": "pass"` / 規則 8 件・該当 0 |
| `--check-doc`（B1） | **差 0 件** |
| 試験 | 変更前 6 failed / 536 passed / 14 skipped → 変更後 6 failed / 550 passed。**失敗の増加 0** |
| `make taskindex-check` / `make inbox-check` | **exit 2（差分あり）。§4 禁止事項 4 により再生成しない。契約が「想定どおりであり失敗ではない」と明記** |
| 分岐 | `feat/amp-compile-timing` |
| commit | `af53fff0` |
| PR | **#182**（base `phase0` / head `feat/amp-compile-timing` / `isDraft: false` / `state: OPEN`） |
