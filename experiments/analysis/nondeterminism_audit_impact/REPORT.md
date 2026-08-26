# 非決定性を含む揺らぎの上に下された既存の判定 — 棚卸しと再測定の優先順位

**task_id:** T-2026-08-26-nondeterminism-audit-impact **kind:** analysis **server:** bengio
**実行:** 2026-08-26 07:07 JST 開始 / Phase E 07:29 JST（締切 21:07 JST に対し 22 分）
**判定:** G1 PASS / G2 PASS / G3 PASS / G4 PASS

---

## 0. 報告会で最初に知るべき三つ

### 1) 現存する判定は、一件残らず非決定な run の上に立っている

`runindex/verdicts.csv` の判定 **1038 件のうち 1038 件**が、決定性を制御せずに
走った run に基づく（実測）。**決定化して走った 360 run は、判定を一つも持っていない。**

決定化された run は 6 つの実験行に集約されているが、その 6 行の `delta_*` 列は
すべて空で、`verdicts.csv` に対応する行が無い。**決定化への投資は、まだ一つの
判定も生んでいない。**

### 2) 確定した事実として扱えるものは、738 件中 18 件しかない

| 区分 | significant 判定 | 割合 |
|---|---:|---:|
| **頑健** | **18** | 2.4% |
| 要注意 | 511 | 69.2% |
| **脆い** | **209** | 28.3% |

**しかもこの 18 件にも留保が要る。**（第 4 節）

### 3) 陽性対照 #111 と同型の判定が 22 件ある

**#111 の脆さは「比が小さかったから」ではない。比は 5.345 で大きい方だった。**
脆さの実体は、判定に使った σ（`pstd` 0.000823）が偶然小さく出たことである。
後に同じ入口で実測された真の σ_d は 0.0054519 で、**6.6 倍**大きかった。

同じ印（σ が同 metric 群の中央値の 0.25 倍未満）を持つ significant 判定が
**22 件**ある。**比の大きさは、これらを守らない。**

---

## 1. 母集団（Phase A・実測）

| 対象 | 起票時の記載 | **実測** | 差 |
|---|---:|---:|---|
| `runindex/index.csv` | 751 | **1177** | +426（索引が更新されている） |
| `runindex/experiments.csv` | 207 | **213** | +6（同上） |
| `runindex/verdicts.csv` | 1038 | **1038** | 一致 |
| `runindex/runs/*.json` | 記載なし | **1177** | index.csv と一致 |

SPEC 第 6 節・第 8 節-1 の指示に従い、**実測の側を採った。**

### 決定性の制御を欠く run（実測）

判定の根拠は run JSON の `metrics_nested.determinism` ブロックの有無である。

| | 件数 | 割合 |
|---|---:|---:|
| 決定性の記録がある | 360 | 30.6% |
| **決定性の記録を欠く** | **817** | **69.4%** |
| 合計 | 1177 | 母集団と一致 |

**入口ごとの内訳（欠く / 全体）。主要な入口のほとんどが該当する。**

| 欠く | 全体 | 入口 |
|---:|---:|---|
| 60 | 420 | `scripts/train_grasp_phase_injection_variants.py`（唯一 360 本が決定化済み） |
| 262 | 262 | `scripts/train_b2a.py` |
| 146 | 146 | （命令の記録が無い） |
| 129 | 129 | `scripts/train_t1a.py` |
| 61 | 61 | `scripts/train_s4_tecno.py` |
| 24 | 24 | （命令を解析できない） |
| 21 | 21 | `scripts/train_hand2det.py` |
| 18 | 18 | `scripts/train_haux.py` |
| 15 | 15 | `scripts/train_taux.py` |
| — | — | 残り 15 入口はすべて全数が欠く（`classification.csv` に全件） |

**合計の検算:** 817 + 360 = 1177 で母集団を超えない。数え方は誤っていない。

### 既存の監査と一致した（独立な二つの方法）

`runindex/anomalies.md` 26 節に、**静的解析による入口ごとの内訳が既にある**（影響 953 run）。
本契約は run の記録（`metrics_nested.determinism` の有無）から独立に数えた。
**11 入口すべてで全体の件数が一致する。**

    入口                                        26節   実測全体  実測欠く
    train_grasp_phase_injection_variants.py     420      420       60
    train_b2a.py                                265      265      265
    train_t1a.py                                132      132      132
    train_s4_tecno.py                            61       61       61
    train_hand2det.py                            21       21       21
    train_haux.py                                18       18       18
    train_taux.py                                15       15       15
    train_grasp_phase_injection.py                6        6        6
    train_t1a_regiontraj.py                       6        6        6
    train_t1b.py                                  6        6        6
    train_t1a_boundary.py                         3        3        3
    合計                                        953      953      593

**差 953 − 593 = 360 は、決定化された run そのものである。**
26 節が 420 全数を「欠落」と数えているのは、静的解析がファイル単位で委譲を 1 段しか
追わず、別モジュールの `enable_determinism` 呼び出しを捕まえられないためである。
**二つの方法が独立に同じ母集団を指した。**

### 実装を読んで分かったこと

主要 5 入口（`train_b2a` `train_t1a` `train_s4_tecno` `train_taux` `train_haux`）は
`torch.manual_seed` を呼ぶが、**これは CPU 側だけである。**
`torch.cuda.manual_seed_all` `torch.use_deterministic_algorithms` `cudnn.deterministic` は
**5 入口とも 0 件**で、`enable_determinism` も呼ばない
（`anomalies.md` 26 節の「CPU 側 3 種のみで GPU 側の制御が 1 つも無い」と一致）。

`src/egosurgery/engines/mmdet_trainer.py:501` は `deterministic=False` を**直書き**している。

第三者の入口については `anomalies.md` 26.2.1 が、Relation-DETR に完全な決定性ブロックが
あるもののフラグでゲートされ、該当 run の `command.sh` が渡していないことを記録している。

---

## 2. 揺らぎの出所と解釈の突き合わせ（Phase B・実測）

全件の表は `crosswalk_verdicts.csv`（1038 行）と `crosswalk_experiments.csv`（213 行）。
**記録が欠けている欄は `(記録なし)` として残し、推定で埋めていない。**

### 分布

| 揺らぎの解釈（実験行 213） | 件数 |
|---|---:|
| **`mixed_with_nondeterminism`** | **123（57.7%）** |
| `unknown` | 82（38.5%） |
| `seed_effect` | 8（3.8%） |

| 揺らぎの出所（判定行 1038） | 件数 |
|---|---:|
| `paired_delta` | 1027 |
| `within_run_seed_spread` | 11 |

| 種の数（判定行 1038） | 件数 |
|---|---:|
| 3 | 946 |
| 1 | 3 |
| （記録なし） | 89 |

**種の数の実測最大値は 3 である。** 母集団に「種が多い」判定は存在しない。

### 両立しない組み合わせ

| # | 組み合わせ | 件数 |
|---|---|---:|
| **X1** | 解釈が `seed_effect`（種の効果）と確定しているのに、run が決定性を制御していない | **8** |
| **X2** | 解釈が確定しているのに出所の記録が無い | **0** |
| **X3** | 同一の実験行に決定化あり／なしの run が混在している | **6** |
| **X4** | `significant` なのに種の数が 1 または記録なし | **0** |

**X1 の 8 件**は `transfer/b2a_det2phase_toolpresence`（4）と
`transfer/t1a_3seed_det{123,456}_{aug,frozen}`（4）である。
**「種の効果」と言い切れる根拠が無い。** 非決定分が混ざり得る。

**X3 の 6 件**は `phase1/s4_grasp_injection/*` で、決定化 60 本と非決定 10〜13 本を
同じ行に集約している（`task_ids` が 2〜3 契約）。**集約の鍵に決定化の有無が入っていない。**

**X2・X4 が零件であることの確認。** `sigma_source` が空の 65 行は解釈が全件
`unknown` であり、条件が構造的に起きない配置である。種の数が 1 または記録なしの
92 行は判定が全件 `undecidable` である。**同じ探索式が同じ列で非零を返すため、空振りではない。**

---

## 3. 脆さの分類（Phase C）

**基準は分類より前に `CRITERIA.md` へ記録した**（基準 07:25:59 / 分類 07:26:47、
`evidence/criteria_timestamp.txt` と `evidence/classify_timestamp.txt`）。
六つの軸に加点し、合計 6 以上を脆い、2 以下を頑健とする。

### 対照は両方向で通った

| 対照 | 対象 | 合計 | 区分 | 期待 | 結果 |
|---|---|---:|---|---|---|
| **陽性** | #111（−0.0044、比 5.345、`pstd` 0.000823、n=3） | **7** | **脆い** | 脆い | **PASS** |
| **陰性** | `transfer/t1a_3seed_det456_frozen` の jaccard（比 14.54、σ/中央値 1.086、n=3） | **2** | **頑健** | 頑健 | **PASS** |

**分離 5 点。片方向では「すべて脆い」「すべて頑健」と区別できないため、両方向で取った。**

**陰性対照の選定で外したもの。** 比が母集団最大（172.27）の判定は σ/中央値が
**0.0644** で、陽性対照 #111 の 0.2278 よりさらに σ が小さい。
**比が大きいことは頑健さの証拠にならない。** 陽性対照が示したのと同じ事実である。

### 全件の分類（1038 件、未分類 0 件）

| 区分 | 全判定 | significant のみ |
|---|---:|---:|
| 脆い | 490（47.2%） | **209（28.3%）** |
| 要注意 | 530（51.1%） | 511（69.2%） |
| 頑健 | 18（1.7%） | **18（2.4%）** |

**脆い 209 件すべてで軸 1（出所）は 0 点、軸 2（種の数）は 1 点、軸 3（解釈）は 2 点、
軸 6（決定性）は 1 点である。** 分離を作っているのは軸 4（比の余裕）と軸 5（σ の過小疑い）。

---

## 4. 確定した事実として扱えるもの — その留保

**頑健と分類された 18 件はすべて 5 つの実験群に由来する。**

`transfer/b2a_det2phase_toolpresence`（7）、`transfer/t1a_3seed_det123_aug`（5）、
`transfer/t1a_3seed_det123_frozen`（1）、`transfer/t1a_3seed_det456_aug`（2）、
`transfer/t1a_3seed_det456_frozen`（3）。

🔴 **この 5 群は X1 の 8 実験行そのものである。**
頑健と出た理由の一つは、解釈が `seed_effect` で軸 3 が 0 点だったことである。
**その `seed_effect` という解釈が、決定性を制御していない run に付けられている。**

したがって **18 件を「確定した事実」と呼ぶには留保が要る。**
言えるのは「**現存する判定の中で最も条件が良い 18 件**」までである。
効果量は大きく（比 3.26〜14.54）、σ は群の中で小さくない（0.79〜3.02 倍）。
**σ が偶然小さく出たことによる見かけの有意ではない。** そこは陽性対照が捉える印を持たない。

---

## 5. 再測定の優先順位（Phase D）

### 順序を決めた観点（実測できるものだけを使った）

1. **σ の過小疑い（軸 5 が 3 点）** — 陽性対照 #111 と同型。**最優先。**
2. **比の余裕の無さ（軸 4 が 2〜3 点）** — 基準 1σ に近い。
3. **記録での言及回数** — 方針への効きの代理。`context/auto/` と `tasks/inbox.md` を実測。
4. **同じ入口で束ねられるか** — まとめて測り直せる単位。

観点 3 は**実測したが分離にほとんど効かなかった**（92 群中 91 群が言及 0〜1 回）。
順序は主に観点 1 と 2 が決めている。**これも記録しておく。**

### 上位 10 群（全 92 群は `priority.csv`）

| 順 | 群 | 脆い判定 | σ疑い | 比僅少 | 入口 |
|---:|---|---:|---:|---:|---|
| 1 | `transfer/b2a_regiononly_mask_14` | 4 | **3** | 0 | `train_b2a.py` |
| 2 | `transfer/t1a_region_mask_10` | 3 | **3** | 0 | `train_t1a.py` |
| 3 | `transfer/b2a_ro_oracle_noise000` | 6 | 1 | 1 | `train_b2a.py` |
| 4 | `transfer/hires_relation_detr_augstrong_seed42` | 5 | 1 | 1 | `train_t1a.py` |
| 5 | `transfer/t1a_3seed_det42_aug` | 5 | 1 | 1 | `train_t1a.py` |
| 6 | `transfer/b2a_det2phase` | 4 | 1 | 1 | `train_b2a.py` |
| 7 | `transfer/t1a_3seed_det42_frozen` | 4 | 1 | 1 | `train_t1a.py` |
| 8 | `transfer/b2a_base_oracle_top3noise_p030` | 2 | 1 | 1 | `train_b2a.py` |
| 9 | `transfer/t1a_region_mask_05` | 2 | 1 | 1 | `train_t1a.py` |
| 10 | `transfer/t1a_region_mask_06` | 2 | 1 | 1 | `train_t1a.py` |

### 束ねる単位（観点 4）

| 脆い判定 | 入口 | 一本あたり所要 |
|---:|---|---|
| 115 | `scripts/train_b2a.py` | **UNKNOWN**（`elapsed_seconds` の記録が無い） |
| 75 | `scripts/train_t1a.py` | **UNKNOWN**（同上） |
| 7 | `scripts/train_taux.py` | **UNKNOWN**（同上） |
| 4 | `scripts/train_haux.py` | **UNKNOWN**（同上） |
| 残り 8 件 | 4 入口 | **UNKNOWN**（同上） |

**この二つの入口を直せば、脆い significant 209 件のうち 190 件（90.9%）が一度に片付く。**

🔴 **再測定に要する規模は書けない。** 所要時間が実測できるのは
`train_grasp_phase_injection_variants.py`（中央値 33.5 秒、n=420）と
`train_grasp_phase_injection.py`（6.9 秒、n=6）だけで、**再測定が要る入口では
記録が無い。** 推測を数値で書くことは禁止 3・7 に触れる。

---

## 6. 外挿していないことの明示

**決定化の実測値は特定の入口のものである。他の入口へ当てはめていない。**

`T-2026-08-15-training-determinism` が実測した値は次のとおりで、いずれも
`train_grasp_phase_injection_variants.py` の経路で測られた。

- 決定化後の σ_d = 0.0054519
- 検出下限 Δ_min: n=3 で 0.0062953、n=10 で 0.0034481
- 減速 2.15×（6.82 → 14.69 秒/本）

**本報告はこれらを他の入口へ当てはめていない。**
「決定化すれば σ がこう下がる」「この結論はこう変わるはずだ」とは一切書いていない。

**書けることは一つだけある。実測された構造の共通性である。**
非決定源として特定されたのは cuDNN の畳み込みカーネル選択であり、その舞台は
`egosurgery.models.heads.tecno_head.TeCNO`（`nn.Conv1d` を 4 箇所使う dilated 1D 畳み込みの積層）である。
**脆い判定を出した 5 入口はすべて同じ `TeCNO` を import している**（実測: b2a=8, t1a=9,
s4_tecno=16, taux=7, haux=13 箇所）。決定化が実測された経路も同じ `TeCNO` を使う。

**同じ非決定源が構造として存在することは言える。σ がいくつになるかは言えない。**

---

## 7. 判定を覆していないこと

**本報告は既存の判定を一つも書き換えていない。**
`runindex/verdicts.csv` `runindex/experiments.csv` `runindex/index.csv` は読み取りのみで、
値の変更・行の追加削除を行っていない（第 5 節 禁止 4・5・6）。

**本報告が出したのは「どれを疑うべきか」の順序である。覆すのは再測定である。**

---

## 8. 起票者へ返す事実

1. **母集団の件数は起票時から動いている**（index +426 / experiments +6）。実測を採った。
2. **「種も多く」を満たす判定は母集団に存在しない。** 種の数の実測最大値は 3 である。
   陰性対照は「n=3（母集団最大）かつ効果量が大きい」で構成した。
3. **陽性対照 #111 の判定行は現在の索引に存在しない。** 決定化ありの run と同じ
   実験行に再集約された結果、`delta_*` 列が空になっている（X3）。
   記録（`tasks/T-2026-08-15-training-determinism/RESULT.md:109`）の値を分類器へ入力して対照とした。
4. **本契約が分母に指定した実験自体が該当当事者である。**
   `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` は
   `sigma_interpretation='unknown'`、`sigma_source` 空、17 run 全数が決定性を制御していない。
