# 再現性の根本原因特定と Δ 規約の再構成

- 実施日: 2026-07-29 / ホスト: efros / 出力: `experiments/analysis/repro_variance_2026-07-29/`
- 実行範囲: **N1・N2・N3 すべて完了**。学習は 1 本も行っていない（N2 は推論による特徴抽出のみ）
- 数値はすべて実測値。推測値 0 件。統計量には n と分母の定義を併記
- **規約・正本は決定していない**（推奨に留める。決定はユーザが行う）

---

## 0. 想定外の発見（最優先）

### 0.1 【最重要】T1a 特徴の再現性問題は解決した — 原因は私の手順ミスだった

**旧キャッシュと完全に bit-exact 一致する再抽出に成功した（1,515 / 1,515 フレーム、max_abs_diff = 0.0）。**

| 原因 | 内容 |
|---|---|
| 機構 | `models/bricks/ms_deform_attn.py` は import 時に `torch.utils.cpp_extension.load()` で **MSDeformAttn の CUDA 拡張を JIT ロード**する。失敗すると警告を出して **PyTorch フォールバック実装**に落ちる |
| 失敗条件 | JIT ロードには **`ninja` が PATH 上にある**必要がある。`ninja` は **`.venv-relation-detr/bin` にのみ存在**する |
| 私の誤り | `source .venv-relation-detr/bin/activate` せず **`.venv-relation-detr/bin/python` を直接呼んだ**ため PATH に `ninja` が無く、拡張ロードが失敗してフォールバックで走っていた |
| 影響 | MSDeformAttn は**全デコーダ層**で使われるため、フォールバックだと全層で数値が変わる |
| 実測エラー | `RuntimeError: Ninja is required to load C++ extensions` |

`docs/t1a_server_b_runsheet.md` STEP 2 は `source .venv-relation-detr/bin/activate` を指定しており、
**手順書どおりに実行すれば再現する**。

**この 1 点で、これまでの複数の「未解明」がまとめて説明される:**

| 過去の判定 | 実際 |
|---|---|
| 2026-07-29 D3: bit-exact **FAIL**（max_abs_diff 1.5553） | フォールバックで抽出していた |
| 同 T1: **UNEXPLAINED**（SAME_TOKEN 97.56% / FLIPPED 0.93% / norm_ratio 中央値 1.000007） | 実装差による全層の微小な数値差と、その結果としての argmax 反転 |
| 同 T2: **PROVENANCE_UNVERIFIABLE**（checkpoint 差を否定も肯定もできない） | **checkpoint は同一**。ckpt md5 `6a898a768eed…` のままで bit-exact 再現した |

→ **既存の T1a 特徴キャッシュは再現可能であり、作り直す必要はない。**

### 0.2 【重大】「系統」は「実験」と同じではない — R-all 規約は成立しない

N3 の R-all（各系統の標準 seed 全 run）を実行するにあたり、系統プールの構成を実測した。

| 系統 | 実験 family 数 | val run 数 | 均質か |
|---|---:|---:|---|
| s4 | **3** | 43 | ✗（base 37 / `_neck` 3 / `_necktransfer` 3） |
| b2a | **73** | 257 | ✗ |
| t1a | **53** | 123 | ✗ |
| h6 | **6** | 18 | ✗ |
| oracle-tool | **1** | 8 | ✓ |

**5 系統中 4 系統で、R-all は複数の別実験を束ねてしまう。**

とくに h6 の内訳（val, 各 n=3）:

| family | acc 範囲 |
|---|---|
| `haux_hand_count_oracle` | 0.8950–0.9050 |
| `haux_hand_geom_oracle` | 0.9056–0.9142 |
| `haux_hand_own_other_oracle` | 0.8977–0.9010 |
| `haux_hand_presence_oracle` | 0.8904–0.9142 |
| `haux_hand_presence_oracle_shuffle` | 0.8871–0.9056 |
| **`haux_hand_presence_oracle_withtooloracle`（= H-6 本体）** | **0.9545–0.9584** |

→ R-all における h6 の有意判定の変化は「**n を増やした統計的効果ではなく、別実験を混ぜた artifact**」である。
そこで「同一実験のまま n を増やす」比較のために **R-family**（代表 3 run と**厳密に同じ family key**の
標準 seed 全 run）を追加した。

---

## 1. タスク別ステータス

| Task | 内容 | ステータス | 判定 |
|---|---|---|---|
| N1 | 同一 seed 非再現の原因特定 | 完了 | **CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM（両立）** |
| N2 | TF32 仮説の検証 | 完了 | **TF32_REJECTED** → 真因は **MSDeformAttn 拡張**（EXT_CONFIRMED） |
| N3 | 全 run 基準での Δ・誤差の再計算 | 完了 | 有意判定が **2 系統**で規約により反転 |

合成データによる検出能力の確認（N1-5 ほか）は全スクリプトで実施し **PASS**。

---

## 2. N1: 同一 seed 非再現 — 判定 CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM

### 2.1 3 ペアの config 差分（N1-1）

**3 ペアとも、比較した 59 キー中 7 キーが差分。比較不能キーは 0 件。**

| seed | run A | run B | val acc 差 |
|---:|---|---|---:|
| 42 | `_004`（lecun） | `_006`（efros） | 0.003961 |
| 123 | `_003`（lecun） | `_007`（efros） | 0.001320 |
| 456 | `_005`（lecun） | `_008`（efros） | 0.003300 |

差分キー（3 ペア共通）:

| source | key | A → B |
|---|---|---|
| config | `server_name` | **lecun → efros** |
| eval_recipe | `eval_recipe.server_name` | **lecun → efros** |
| meta | `git_commit` | **c4228eddc07a → 1a52c6fde812** |
| meta | `server` | **lecun → efros** |
| meta | `generated_at` | 2026-06-29 → 2026-07-02 |
| meta | `command_line` | `--seed N --epochs 50 --tool-source oracle` → `--tool-source oracle --seed N` |
| meta | `epoch`（best epoch） | 47→40 / 45→47 / 44→37 |

**つまり「同一 seed の反復」ではなく、別ホスト・別コミットの run だった。**
`--epochs 50` の有無は `config.yaml` の `train.epochs` が両者 **50** で実効差なし（確認済み）。
コミット間で `train_b2a.py` は 133 行追加の変更（oracle 経路の追加等）がある。

### 2.2 分散分解（N1-2）

| 系統 | seed 数 | 重複あり | n | sd_between | sd_within | ICC |
|---|---:|---:|---:|---:|---:|---:|
| oracle-tool | 3 | 3 | 6 | 0.002445 | 0.001536 | **0.7170** |
| s4 | 3 | 3 | 43 | 0.002911 | 0.009874 | 0.0800 |
| h6 | 3 | 3 | 18 | 0.003594 | 0.021316 | 0.0276 |
| t1a | 3 | 3 | 115 | 0.000955 | 0.017245 | 0.0031 |
| b2a | 3 | 3 | 255 | 0.000866 | 0.021286 | 0.0017 |

> ⚠️ **重要な但し書き**: oracle-tool 以外のプールは §0.2 のとおり複数 family を含む不均質集合である。
> したがって `var_within_seed` は「非決定性」ではなく「**設定差 + 非決定性**」を混合して測った値であり、
> 純粋な再現性の指標としては解釈できない。設定を確認済みなのは oracle-tool の 3 ペアのみ。

### 2.3 非決定性の制御（N1-3）

| 項目 | 有無 | 場所 |
|---|---|---|
| `torch.manual_seed` | ✓ | `scripts/train_b2a.py:235` |
| `np.random.seed` | ✓ | `scripts/train_b2a.py:234` |
| `random.seed` | ✓ | `scripts/train_b2a.py:233` |
| `DataLoader num_workers` | ✓ | `src/egosurgery/engines/phase_trainer.py:104` |
| `DataLoader shuffle` | ✓ | `src/egosurgery/engines/phase_trainer.py:106` |
| **`torch.cuda.manual_seed_all`** | **✗** | — |
| **`torch.use_deterministic_algorithms`** | **✗** | — |
| **`cudnn.deterministic`** | **✗** | — |
| **`cudnn.benchmark`** | **✗** | — |
| **`DataLoader worker_init_fn`** | **✗** | — |
| **`DataLoader generator`** | **✗** | — |
| **`PYTHONHASHSEED`** | **✗** | — |

### 2.4 判定（N1-4）

判定表は CONFIG_DIFF と UNCONTROLLED_NONDETERMINISM を排他として扱うが、
**実測では両方の前提が成立する**（§6 に従い表に当てはめず記録）。

1. ペアは別ホスト・別コミットであり**同一条件の反復ではない** → 混ぜずに分けて集計する必要がある
2. seed は設定されているが**決定性制御が無い** → 条件を揃えても bit-exact 再現は保証されない

→ 「重複 run を独立反復として扱ってよい」とも「条件を揃えれば再現する」とも言えない。

---

## 3. N2: TF32 仮説 — 判定 TF32_REJECTED（真因は MSDeformAttn 拡張）

### 3.1 現在の既定値（N2-1）

| 項目 | 値 |
|---|---|
| torch / CUDA | 2.1.2+cu118 / 11.8 |
| `matmul.allow_tf32` | **False** |
| `cudnn.allow_tf32` | **True** |
| `cudnn.benchmark` / `cudnn.deterministic` | False / False |
| `float32_matmul_precision` | highest |
| device / cuDNN | NVIDIA RTX A6000 / 8700 |

抽出スクリプト・config は TF32 を**明示設定していない**。
ただし抽出は `torch.autocast(device_type="cuda", dtype=torch.float16)` の下で走る（`:140`）。

### 3.2 スイープ結果（N2-2 / N2-3）

| ID | matmul TF32 | cudnn TF32 | 実装 | bit-exact | frames_eq | SAME_TOKEN | FLIPPED | rel_err median (\|A\|>0.1) | absmax |
|---|---|---|---|---|---|---:|---:|---:|---:|
| P00 | False | False | fallback | ✗ | 0/1515 | 0.9756 | 0.0093 | 7.148e-03 | 4.091495 |
| P01 | False | True | fallback | ✗ | 0/1515 | 0.9756 | 0.0093 | 7.148e-03 | 4.091495 |
| P10 | True | False | fallback | ✗ | 0/1515 | 0.9756 | 0.0093 | 7.148e-03 | 4.091495 |
| P11 | True | True | fallback | ✗ | 0/1515 | 0.9756 | 0.0093 | 7.148e-03 | 4.091495 |
| **with_cuda_ext** | False | True | **CUDA 拡張** | **✓** | **1515/1515** | **1.0000** | **0.0000** | **0.0** | **4.117701** |

**4 つの TF32 設定は互いにバイト単位で完全に同一**（全指標が一致）。TF32 の影響は **ゼロ**。
fp16 autocast 下で走るため TF32（fp32 matmul の低精度化）が効かないことと整合する。

### 3.3 判定（N2-4）

| 判定 | 内容 |
|---|---|
| **TF32_REJECTED** | 4 設定とも現状と同程度（かつ互いに同一）。TF32 仮説は棄却 |
| **EXT_CONFIRMED**（次候補の特定） | MSDeformAttn の CUDA 拡張をロードした場合のみ **bit-exact 一致**。原因確定 |

N2-5（`cudnn.benchmark` の追加 2 本）は、TF32 4 設定が完全に同一で
かつ真因が bit-exact 再現によって特定できたため**不要と判断し実施していない**。

### 3.4 運用ルール（提案・決定はしない）

- 抽出・推論は必ず `source .venv-relation-detr/bin/activate` してから実行する
  （`.venv-relation-detr/bin/python` の直接呼び出しは禁止）
- 実行時に `Failed to load MultiScaleDeformableAttention C++ extension` の警告が出たら**中断する**
- 抽出成果物の隣に「拡張がロードされたか」を記録する
- `scripts/analysis/reextract_precision_sweep.sh` に `EXT_MODE=cuda|fallback` を実装し、
  既定で PATH に venv/bin を載せるようにした（対照実験時のみ `fallback` を選ぶ）

---

## 4. N3: 全 run 基準での Δ と誤差 — 有意判定が 2 系統で反転

### 4.1 4 規約での Δ（N3-1 / N3-2）

MDE 式: `MDE = t(0.975, n-1) × pooled_sd × sqrt(2/n)`（n = min(系統 n, 分母 n)）。
分母はすべて s4（規約ごとに選択が変わる）。

| 規約 | 分母 s4 | b2a | t1a | h6 | oracle-tool |
|---|---|---|---|---|---|
| **R-triple**（代表 3 run） | n=3, 0.898570 | Δ+0.038284 MDE0.00908 **✓** | Δ+0.049725 MDE0.00937 **✓** | Δ+0.058306 MDE0.00993 **✓** | Δ+0.062046 MDE0.00878 **✓** |
| **R-family**（同一 family 全 run） | n=37, 0.902703 | Δ+0.034151 MDE0.03565 **✗** | Δ+0.045592 MDE0.03566 **✓** | Δ+0.054173 MDE0.03567 **✓** | Δ+0.053843 MDE0.01459 **✓** |
| **R-all**（系統の標準 seed 全 run） | n=43, 0.903477 | Δ+0.036297 MDE0.00876 **✓** | Δ+0.038891 MDE0.00684 **✓** | Δ+0.007781 MDE0.01037 **✗** | Δ+0.053069 MDE0.01446 **✓** |
| **R-all-dedup** | n=3, 0.903103 | Δ+0.036675 MDE0.00924 **✓** | Δ+0.039218 MDE0.00932 **✓** | Δ+0.008155 MDE0.01407 **✗** | Δ+0.053443 MDE0.01157 **✓** |

**MDE は n を増やしても縮むとは限らない**（N3-2 の重要な実測）:

| 系統 | n（triple→all） | MDE（triple→all） | 比 |
|---|---|---|---:|
| s4 | 3 → 43 | 0.011900 → 0.004457 | 0.37× |
| t1a | 3 → 115 | 0.009372 → 0.006840 | 0.73× |
| b2a | 3 → 255 | 0.009080 → 0.008760 | 0.96× |
| h6 | 3 → 18 | 0.009929 → 0.010368 | **1.04×（拡大）** |
| oracle-tool | 3 → 6 | 0.008779 → 0.014460 | **1.65×（拡大）** |

n を増やすと同時に**異質な run が入って sd が増える**ため、MDE が拡大する系統がある。

### 4.2 有意判定が反転する系統（N3-3）

| 系統 | R-triple | R-family | R-all | R-all-dedup | 紐づく既存の結論 |
|---|---|---|---|---|---|
| **b2a** | ✓ | **✗** | ✓ | ✓ | B2a の tool-presence 注入効果 |
| **h6** | ✓ | ✓ | **✗** | **✗** | **H-6 の +0.0004 →「手は術具に対して冗長」** |

- **b2a** が R-family で非有意になるのは、分母 s4 の family（n=37, sd 0.0104）が大きく
  pooled_sd を押し上げ MDE が 0.0357 に膨らむため（Δ 0.0342 がそれを下回る）。
- **h6** が R-all / R-all-dedup で非有意になるのは §0.2 のとおり **別実験 5 family を混ぜた artifact**。
  同一実験に限定した R-family では**有意のまま**（Δ+0.054173 > MDE 0.03567）。

### 4.3 H-6 を分母別に評価（N3-4）

| 分母 | 分子 | n | H-6 Δ | MDE | 超過 |
|---|---|---:|---:|---:|---|
| oracle-tool 0.958196（固定値） | R-all | 18 | −0.046938 | 0.011062 | ✓ |
| oracle-tool 0.956436（固定値） | R-all | 18 | −0.045178 | 0.011062 | ✓ |
| oracle-tool（R-all） | R-all | 18 | −0.045288 | 0.029106 | ✓ |
| S4（R-all） | R-all | 18 | +0.007781 | 0.010368 | ✗ |
| **oracle-tool 0.956436（固定値）** | **R-triple** | **3** | **+0.000440** | 0.009929 | **✗** |

> ⚠️ ここでの「R-all の H-6」は **6 family を束ねた平均 0.911258** であり、
> H-6 本体（`withtooloracle`、平均 0.956876）とは別物である。したがって上 4 行は
> 「n を増やした H-6」ではない。**H-6 本体の n は 3 のままであり、n を増やす余地は無い**
> （同一 family の canonical-seed run は 3 本しか存在しない）。

→ **「R-all で n が増えれば H-6 の効果が MDE を超えるようになるか」への答えは NO。**
H-6 本体の run が 3 本しか無いため、n を増やすには**追加実験が必要**。

### 4.4 正誤表 v2（N3-5）

| 引用値 | 引用 | R-triple | R-family | R-all | R-all-dedup | status |
|---|---:|---:|---:|---:|---:|---|
| S4 base accuracy | 0.8986 | 0.898570 | 0.902703 | 0.903477 | 0.903103 | **CHANGED** |
| B2a Δ | 0.0383 | +0.038284 | +0.034151 | +0.036297 | +0.036675 | **SIGNIFICANCE_FLIPPED** |
| T1a Δ | 0.0497 | +0.049725 | +0.045592 | +0.038891 | +0.039218 | **CHANGED** |
| H-6 Δ | 0.0004 | +0.058306※ | +0.054173 | +0.007781 | +0.008155 | **SIGNIFICANCE_FLIPPED** |
| oracle-tool acc | 0.9583 | 0.960616 | 0.956546 | 0.956546 | 0.956546 | **CHANGED** |
| oracle-tool macro-F1 | 0.823 | — | — | — | — | NOT_RECOMPUTED |
| S0-frozen mAP | 0.7051 | — | — | — | — | NOT_RECOMPUTED |

※ H-6 Δ はここでは**分母 S4** の値。引用値 +0.0004 は分母 oracle-tool のときの値（§4.3 最終行）。
**分母が系統ごとに異なる問題は未解決のまま**である。

### 4.5 規約案（N3-6・決定はしない）

| 規約 | 利点 | 欠点（実測） |
|---|---|---|
| **R-triple** | 条件が最も近い（同一 family・連番）。引用値を残差 <5e-5 で再現する唯一の規約 | n=3 で sd・MDE が不安定。run 選択が恣意的に見える。**N1 より、その 3 本すら同一条件とは限らない** |
| **R-family** | 同一実験のまま n を増やせる。§0.2 の混入問題が無い | 分母 s4 の family が n=37 と大きく、pooled_sd が支配的になり MDE が膨らむ（b2a が非有意化） |
| R-all | n が最大 | **5 系統中 4 系統で別実験を混ぜる**（§0.2）。規約として成立しない |
| R-all-dedup | seed 数 3 を保ちつつ重複を吸収 | 同上の混入問題は残る |

**N1 の判定が規約の妥当性に与える影響**:
N1 は「CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM の両立」だった。したがって

- R-triple は「同一条件 3 反復」ではない（別ホスト・別コミットが混ざりうる）ため、**分散を過小評価する**
- R-all / R-all-dedup は別実験を混ぜるため、**分散を過大評価する**
- **どちらも「真の再現ばらつき」を測っていない**。それを測るには、決定性制御を入れたうえで
  同一ホスト・同一コミットで反復する追加実験が必要

**書き換えが必要な記述**: 規約を R-triple 以外に変えると、正誤表 v2 の **CHANGED / SIGNIFICANCE_FLIPPED
5 件**すべてが対象になる（S4 base / B2a Δ / T1a Δ / H-6 Δ / oracle-tool acc）。
R-triple を維持すれば書き換えは 0 件だが、上記の過小評価の問題が残る。

**決定はユーザが行う。**

---

## 5. 完了条件

- [x] N1–N3 がステータス付きで記録され、判定がある
- [x] N1: 3 ペアの config 差分（比較不能キー 0 件を明記）と分散分解（ICC）
- [x] N2: 4 設定の比較結果と判定（+ CUDA 拡張版の bit-exact 一致）
- [x] N3: 4 規約 × 5 系統の Δ / sd / n / CI / MDE 表と、有意判定が反転する箇所の一覧
- [x] 合成データによる検出能力の確認（N1-5 ほか）
- [x] 数値はすべて実測値
- [x] **規約・正本を決定していない**

---

## 6. 成果物

| パス | 内容 |
|---|---|
| `json/n1_same_seed.json` / `csv/n1_config_diff.csv` / `csv/n1_variance_decomp.csv` | N1 |
| `json/n2_precision_sweep.json` / `csv/n2_sweep_results.csv` | N2 |
| `json/n3_delta_allrun.json` / `csv/n3_delta_by_convention.csv` / `csv/n3_errata_v2.csv` | N3 |
| `reextract/val_P0{0,1}.npz`, `val_P1{0,1}.npz` | TF32 スイープ出力（フォールバック実装） |
| **`reextract/val_with_cuda_ext.npz`** | **旧キャッシュと bit-exact 一致した再抽出** |

```bash
export OUT=experiments/analysis/repro_variance_2026-07-29
python3 scripts/analysis/diag_same_seed_variance.py  --self-test && python3 scripts/analysis/diag_same_seed_variance.py  --out $OUT
bash    scripts/analysis/reextract_precision_sweep.sh $OUT val      # EXT_MODE=fallback で対照
source .venv-relation-detr/bin/activate                            # ★ 必須（ninja を PATH に載せる）
RELDETR_FROZEN_TAG=__tmp python scripts/extract_t1a_regiontoken.py --subset val
deactivate
python3 scripts/analysis/n2_compare_precision.py     --out $OUT
python3 scripts/analysis/delta_allrun_recompute.py   --self-test && python3 scripts/analysis/delta_allrun_recompute.py --out $OUT
```

### 変更していないもの

元データ・split・クラス体系・凍結源・**依存関係**（`pip install` 未実行）／既存の実験結果・キャッシュ
（再抽出はすべて別ディレクトリ）／**学習は 1 本も実行していない**。
誤生成された `.venv`（Python 3.12・CUDA 不可）は使用していない。
