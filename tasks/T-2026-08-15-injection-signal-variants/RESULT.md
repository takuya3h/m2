# RESULT — T-2026-08-15-injection-signal-variants

**実行者:** andrew / feat/injection-signal-variants
**実行日時:** 2026-08-15T11:58Z 開始
**判定:** PASS

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| conventions_rev | `d422b08` | 現在値も `d422b08`。差分なし。置換不要 |
| created_from.runindex_commit | `44697d9` | 現在値は `592a4e1`。ただし `created_from.counts`（index 791 / experiments 217 / verdicts 1038）は現状と一致しており、**起票者は更新後の索引を見ている。記載の commit だけが古い**（逸脱 1） |
| inputs.code.entrypoints | 3 件 | すべて実在 |
| contract.inject_verbatim | `conventions#prohibitions` | 錨は実在。原文を下に転記 |

`context/conventions.md#prohibitions` の原文（要約せず転記）。

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

## 2. 既にあった形と、足した形

**四つとも無かった。それどころか `signal` キーは実装のどこからも読まれていなかった。**

前の実験の設定の `signal: predicted_sigmoid`（inj）/ `signal: zeros`（ctrl）は注釈にすぎず、
実挙動は `arm` で決まっていた。記述と挙動の一致は偶然である（`audit/phase_a.md`）。
どんな値を書いても黙って無視される —— G1 で確定した「黙って既定になる」欠陥の最強形であり、
**SPEC の指示どおり直した**: モデルが `signal` を読み、未知の値は `ValueError` で落ちる。

| 形 | 設定の値 | 実装 |
|---|---|---|
| （既存の形） | `predicted_sigmoid` | sigmoid の予測（既定。挙動不変） |
| （既存の注釈） | `zeros` | 全零の信号（ctrl の注釈を実挙動として受理） |
| 押しつぶす前 | `raw_logits` | **足した** |
| 揃えた値 | `standardized` | **足した** |
| 正解 | `oracle_upper_bound_only` | **足した** |
| 段階を分ける | `staged: true`（信号は既存形と直交） | **足した**（新規スクリプトの学習順序） |

変更箇所: `src/egosurgery/models/temporal/grasp_inference_injection.py`（形の選択と検証）、
`scripts/train_grasp_phase_injection_variants.py`（新規。教師の受け渡しと二段階の学習順序）、
`configs/stage/` に新規 4 件、`tests/test_injection_signal_variants.py`（新規 21 件）。
**既存のスクリプト・設定・試験は無変更**（要件 2 / 禁止 11）。

## 3. 五つの腕の重みの総数（G3）

実寸（input 2048 / hidden 64 / phases 9 / TeCNO 2×8×64）で数えた（`audit/phase_c.json`）。

| 腕 | 学習可能な重みの総数 |
|---|---:|
| inj:predicted_sigmoid | 528919 |
| inj:raw_logits | 528919 |
| inj:standardized | 528919 |
| inj:oracle_upper_bound_only | 528919 |
| ctrl:zeros | 528919 |
| （基準点 TeCNO） | 397138 |

**五つの腕が完全一致。基準点との差 131781 も契約の記載と一致。** 段階を分ける形は
学習の順序が違うだけで、固定は重みの総数を変えない（試験で固定）。

## 4. 信号の到達（G2）

同じ重みで零と一の信号を差し替え、工程側の最終段の出力の差を測った。

| 腕 | max abs Δ | mean abs Δ |
|---|---:|---:|
| inj:predicted_sigmoid | 0.004116 | 0.001316 |
| inj:raw_logits | 0.004116 | 0.001316 |
| inj:standardized | 0.004116 | 0.001316 |
| inj:oracle_upper_bound_only | 0.004116 | 0.001316 |
| **ctrl:zeros（対照）** | **0.000000** | **0.000000** |

四つの形すべてで信号が届き、無情報な腕では**ちょうど零**。対照は効いている。
（四形の Δ が同値なのは、到達検査が注入経路への上書き信号で測るためであり、
形ごとの候補値が違うことは §5 で別に示す。）

## 5. 形ごとに渡している値の違い（同じ重み・同じ入力の実測）

| 形 | min | max | 性質（試験で固定した不変条件） |
|---|---:|---:|---|
| predicted_sigmoid | +0.3249 | +0.6357 | sigmoid(logits) と厳密一致 |
| raw_logits | −0.7314 | +0.5569 | 零から一に収まらない。sigmoid を通すと predicted_sigmoid と一致 |
| standardized | −2.0193 | +1.5286 | 記録した定数どおりの affine（(p̂−center)/scale）と厳密一致 |
| oracle_upper_bound_only | +0.0000 | +1.0000 | 教師ありのフレームで教師と完全一致。値は 0/1 のみ |

四つは互いに異なる値を渡している（全対で max|差| > 0 を試験が固定）。

## 6. 教師の無いフレームで正解を渡す形が何を渡すか

**学習側の正例率（次元ごとの定数）を渡す。** `oracle_missing_fill: [0.925502, 0.896323,
0.761971, 0.766994, 0.101753]`（出所 `audit/train_stats.json`、学習側の教師 9356 枚から実測）。

**零を選ばなかった理由。** 正例率 92.6% の左手の次元で零は大きく誤った値になり、
「教師が無い」ことが強い信号として漏れる。正例率なら中立な事前値になる。
**漏れは残る**: 埋め値は 0/1 でないため、教師の有無は下流から依然として区別できる。
この旨は実装の docstring・設定・試験（`test_oracle_missing_frames_receive_recorded_fill`）の
三箇所に記した。教師の無いフレームは学習側 301 枚 / 測る側 1 枚（実測）。

## 7. 揃えた値の中心と広がりの出所

**学習側の教師の統計から求めた定数**である。中心 = 学習側の正例率 p、広がり = √(p(1−p))。

| 次元 | 中心 | 広がり |
|---|---:|---:|
| left_hand | 0.925502 | 0.262579 |
| right_hand | 0.896323 | 0.304841 |
| left_hand_tool | 0.761971 | 0.425877 |
| right_hand_tool | 0.766994 | 0.422746 |
| two_hands_tool | 0.101753 | 0.302323 |

**測る側からは求めていない**（求めると漏れる）。予測の分布から求めない理由は、
予測は学習中に動くため定数として記録できないからである。定数は設定ファイルに
陽に書かれ、モデルは定数なしの `standardized` を拒む。

## 8. 正解を渡す形の歯止め（成果として報告してはならない）

**`oracle_upper_bound_only` は上限測定専用であり、成果として報告してはならない。**
測る側の教師そのものを注入するため、実際に使える手法ではない。答えるのは
「注入という機構自体に価値があるか」の上限だけである。

| 歯止め | 実装 |
|---|---|
| 名 | 形の名・設定ファイル名・run の description すべてに `oracle_upper_bound_only` |
| 明示の承認 | `oracle_upper_bound_acknowledged: true` が無いと**モデルが構築を拒む** |
| 実装の説明文 | モジュール docstring と分岐コメントに DO NOT REPORT を記載 |
| 記録に残る印 | 学習結果の JSON に `oracle_upper_bound_only_do_not_report: true` が入る（試走で実証） |

## 9. Phase C の七項目の実測

| # | 項目 | 結果 |
|---|---|---|
| 1 | 信号の到達（四つ）と不到達（無情報） | §4。五通りすべて数値で |
| 2 | 五つの腕の重みの総数 | §3。完全一致 |
| 3 | 形ごとに渡す値が違うこと | §5。実際の値で |
| 4 | 正解が教師と一致・欠落は記録どおり | 試験で固定（教師あり=厳密一致、欠落=埋め値、0/1 でないため識別可能） |
| 5 | 既定で既存の挙動が変わらない | `signal` を書かない設定 = `predicted_sigmoid` を明示した設定と**出力がビット単位で一致**（同じ重みを載せ替えて照合）。既存試験 9 件も無変更で通過 |
| 6 | 因果性 | 四つの形すべてで、未来のフレーム・未来の教師を差し替えても過去の出力が不変（`test_each_form_is_causal`） |
| 7 | 検査の失敗の集合 | **前 5 / 後 5 で識別子まで一致**。新規に落ちたもの・直ったもの、ともに無し。passed は 448 → 469（新規 21 件） |

破れるべきときに破れることも対で固定した: 未知の値・承認なしの oracle・定数なしの
standardized・教師なしの oracle forward の 4 つが**すべて落ちる**。

## 10. 試走（Phase D）

計算装置は 2 台とも空き（使用 10 MiB / 0%、他利用者のプロセス 0 件）。

| 腕 | 完走 | 装置 | 所要（2 世代・clip 各 1） |
|---|---|---|---:|
| ctrl:zeros | ○ | cuda | 1.72 s |
| inj:raw_logits | ○ | cuda | 1.51 s |
| inj:standardized | ○ | cuda | 1.49 s |
| inj:oracle_upper_bound_only | ○ | cuda | 1.90 s |
| inj:predicted_sigmoid（staged） | ○（**両段階**: stage1 2 世代 0.2 s + stage2 2 世代） | cuda | 1.53 s |

出力先は `tasks/.../smoke/` のみ。`make runindex` 後、**本契約の試走が索引に入った数 = 0**
（`tasks/` 配下を指す行も 0）。総行数 791 で不変。

## 11. 次の実験に必要な材料

| 材料 | 値 |
|---|---|
| 一本あたりの所要時間 | 本番規模（50 世代・全 clip）は**未測定（UNKNOWN）**。参考: 前の実験の既存形が約 7 秒/本、本契約の試走（2 世代・clip 1 本）が 1.5〜1.9 秒。staged は stage1 の分が加算される |
| 設定と腕の対応 | `s4_grasp_injection_ctrl.yaml` = 無情報（既存・無変更） / `..._raw_logits.yaml` / `..._standardized.yaml` / `..._oracle_upper_bound_only.yaml` / `..._staged.yaml`（いずれも凍結源 `relation_detr_seed42`・neck 無し） |
| 入口 | `scripts/train_grasp_phase_injection_variants.py`（既存スクリプト経由では新しい形は届かない） |
| 分母 | `exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` |

## 12. 起票者の推測のうち、実測で裏づけられたもの／否定されたもの

**裏づけられたもの。**

| 記載 | 実測 |
|---|---|
| 二つの腕の重み 528919、基準点 397138 | 一致（差 131781 も） |
| 学習一本あたり約七秒（既存形） | 再測定はしていないが、試走の規模感と矛盾しない |
| 教師の無いフレームがある | 実在（学習側 301 / 測る側 1） |

**否定された・補正されたもの。**

1. **「`signal` が列挙型なら他の値が既にあるかもしれない」→ 列挙型ですらなかった。**
   キーは実装のどこからも読まれておらず、注釈だった。四つの形はすべて新規に足した。
2. **教師の無いフレーム 460 枚（2.98%）は全 split 合算とみられる。** 本契約が触る範囲の
   実測は学習側 301 / 測る側 1。test 側は数えていない（本契約は val のみ）。
3. **`created_from.runindex_commit: 44697d9` は古い。** counts は現状一致。

## 13. 判断が要る事項

1. **staged の stage1 の世代数（既定 50）が適切かは未検証。** 本契約は回ることだけを確かめた。
2. **本番規模の所要時間が UNKNOWN のまま。** 次の実験の冒頭で 1 本実測してから見積もるべき。
3. **決定性監査が新規スクリプトを非決定と分類**（`cuda_manual_seed` 等が無い。原本と同一の
   プロファイル）。揃えるべきかは既存 34 本すべてに関わる backlog B-20 の範疇。

## 14. deviations（指示書どおりにしなかった箇所）

**空にしない。** 4 件ある。

1. **指示:** `created_from.runindex_commit: 44697d9`。
   **実際:** 現在値は `592a4e1`。counts が現状一致のため置換せず続行した。
   **分類:** SPEC の欠陥（記載が古い）
2. **指示:** Phase E の変更範囲は「`runindex/` に変更が無いこと」。
   **実際:** `runindex/anomalies.md` と `runindex/anomalies/determinism_audit.csv` に差分がある。
   **理由:** Phase D Step 3 が命じる `make runindex` の正当な生成物である。決定性監査が
   新規スクリプトを検出し 33→34 本目として記録した。索引本体（index.csv 等）は不変。
   手では編集していない（禁止 1 の「生成は可」）。
   **分類:** SPEC の欠陥（生成と無変更の期待が両立しない。前々契約の forbidden-check と同型）
3. **指示:** （明示なし）
   **実際:** 試走ループの初回が無音で失敗した（`/usr/bin/time` 不在 + 出力の濾過で不可視）。
   成果物の実在確認で捕まえ、濾過なしで再実行した。新規スクリプトの import 誤り 2 件と
   evaluate の写し間違い 1 件もこの過程で修正した。
   **分類:** 環境差 + 判断が必要だった
4. **指示:** smoke の段階を分ける形は両段階が回ること。
   **実際:** 確認した。ただし staged 設定の `epochs_stage1: 50` は smoke の上限 2 を超えるため、
   CLI に `--stage1-epochs` を追加して 2 に抑えた（新規スクリプト内の追加であり解禁範囲）。
   **分類:** 判断が必要だった

## 15. 数値の出所

| 数値 | 出所 |
|---|---|
| 受理値・既定・欠陥の実測 | `audit/phase_a.md` |
| 学習側の統計（中心・広がり・埋め値） | `audit/train_stats.json`（`audit/train_stats.py` が生成） |
| 到達量・重みの総数・値域 | `audit/phase_c.json`（`audit/phase_c.py` が生成） |
| 試験の前後 | `audit/pytest_before.txt` / `audit/pytest_after.txt` |
| 試走 | `smoke/*/smoke_metrics.json` と `smoke/*.log` |

未測定は `UNKNOWN` と明記した（本番規模の所要時間、test 側の教師なしフレーム数）。
