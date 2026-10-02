# RESULT — T-2026-09-27-stage2-prep

**判定: pass**（完了判定 a〜h をすべて達成）
**ホスト:** aolab（GPU 不使用） **分岐:** `feat/stage2-prep`（起点 `origin/phase0` = `1ac2d2c9`）
**実行日:** 2026-10-02（JST）

## 1. 解決された参照

| 参照 | 解決 |
|---|---|
| `meta.created_from.runindex_commit` | `2fb7c905b51aac5ec2b0ee5fe5c70e835f4024a8`（`runindex/` を最後に変えた commit。占位を差し替えた） |
| `meta.created_from.counts` | index 1911 / experiments 718 / verdicts 1506（`wc -l` − 1。占位の 0 を差し替えた） |
| `contract.conventions_rev` | `4369cf5e7b82a3043b9b00b998911c4efb856f69`（`context/conventions.md` を最後に変えた commit。占位を差し替えた） |
| `contract.inject_verbatim` | `conventions#prohibitions` `#issuer_cautions` `#eval_recipe` `#proposal_gate` の原文を `context/conventions.md` から読んだ（L2-5 で 4 件とも解決） |
| `inputs.denominator` / `frozen_source` | 契約に無い（impl） |

## 2. 完了判定

| # | 判定 | 結果 | 空振りでないことの確認（実測） |
|---|---|---|---|
| a | 規約 2 節 | **達成**。アンカー 11 → 13。L2 で `conventions#det_groups`・`#crossfit` が解決。既存 11 節の本文は末尾空白を除いて不変。naming 節の範囲に入る変更履歴表へ 1 行を足した（§6 逸脱 2） | `det_group`・`crossfitt` で `[L2-5] アンカー … が存在しません` |
| b | クラス名の対応 | **達成**。9 クラスすべて注釈の 15 クラス名と完全一致（全 5 折り × 3 分割でクラス名一覧は同一）。対応表は `docs/stage1/D_group_ap.md` §1 | `Bipolar forceps`（1 文字変更）で `matched: None` |
| c | 群 AP の表 | **達成**。二周目 14 run の val、確定塔の test 10 件、一周目の同じ run、両塔の差（COCO − ImageNet） | dcoco_foldA_seed42 二周目 val 標的群を結果表の 3 桁値で手計算 0.7952、表 0.7951。dcoco_foldE_seed42 val 陰性対照群（3 クラス）を全桁で手計算 0.43860521730832785、json 0.43860521730832774 |
| d | カード | **達成**。`check_proposal.py` 検出 0 件（禁止語 15 語 / カード 16 件） | #6 の数字を消した一時文書で `missing_number` 1 件、exit 1 |
| e | 日数 | **達成**。4 通り、差の原因の表、締切との比較（`docs/stage1/B2_tier1_cost_with_crossfit.md`） | 交差適合の二行を外すと Tier 1 が 340.5 GPU 時間ちょうど減り「なし」の値に一致（試験 `test_removing_crossfit_rows_returns_to_the_no_crossfit_values`） |
| f | check-doc | **達成**。B1 差 0 件。B2 も `--doc-sections history,crossfit` で差 0 件 | B1 の crossfit 節の 109.2 を 109.3 にした写しで差 1 件、exit 1 |
| g | 試験 | **達成**。前 6 failed / 669 passed / 収集エラー 1 → 後 6 failed / 673 passed / 収集エラー 1 | 失敗 6 件と収集エラー 1 件は同一（§7）。合格 +4 は本契約の新規試験 |
| h | PR | **達成**。**PR #198**、`isDraft=false` / `base=phase0` / `head=feat/stage2-prep` / `state=OPEN`（`gh pr view 198 --json` の実測） | 分岐名は `feat/` で始まる |

ゲート: **G1 pass**（9 クラス完全一致）、**G2 pass**（検出 0 件）。

## 3. 実測

### クラス名の対応

| 群 | クラス（規約 = 注釈） |
|---|---|
| 標的群 | Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory |
| 陰性対照群 | Gauze、Mouth Gag、Suction Cannula、Tweezers |

評価集合に出現しないクラス（AP が NaN）は注釈の欠落と全 run・全分割で一致した。群に掛かるのは
**折り E の val の Mouth Gag だけ**で、そこでは陰性対照群 AP を 3 クラスで平均した。test では欠けなし。

### 群 AP の要点（二周目、`docs/stage1/D_group_ap.md`）

| | D*-COCO | D*-ImageNet | 差 |
|---|---|---|---|
| 標的群 val 折り A 3 seed 平均 (SD) | 0.8051 (0.0159) | 0.7571 (0.0099) | — |
| 標的群 val 5 折り平均（seed 42） | 0.6405 | 0.5909 | +0.0496 |
| 標的群 test 5 折り平均 | 0.5788 | 0.5621 | +0.0167 |
| 陰性対照群 val 5 折り平均 | 0.5594 | 0.5182 | +0.0411 |
| 陰性対照群 test 5 折り平均 | 0.5294 | 0.4854 | +0.0440 |

一周目の同じ量は標的群の差 val +0.0402・test +0.0322。二周目の test の標的群の差は折り B で −0.0325 と符号が反転した
（5 折り中 1 折り）。記述統計であり判定ではない。

### 日数の差の原因（全体、K・縮退なし、24 h/日、2 枚）

| 段 | 日数 | 差 |
|---|---|---|
| 9/17 の報告（TF32） | 74.0〜98.7 | — |
| TF32 の倍率を外す | 87.5〜116.6 | +13.5 / +18.0 |
| 検出塔 8.00 → 8.35 h | 87.9〜117.0 | +0.4 / +0.4 |
| 検出塔 8.35 → 14.13 h | 92.9〜122.1 | +5.1 / +5.1 |
| K 3 → 2（9/27 の報告） | 88.8〜118.0 | −4.1 / −4.1 |

両端は報告値と一致した（試験 `test_history_reproduces_the_reported_values`）。**TF32 は計算器に一度も入っていない。**
9/17 の 74.0〜98.7 日は計算器の外で W1 の倍率 1.182 を全行へ当てた値だった。W2 の補正（4.00 → 4.82 h）は両方に入っている。

### Tier 1 の日数（交差適合、単精度、24 h/日、2 枚）と締切

| seed | 交差適合 | 日数 | 使える 125 日との比較 |
|---:|---|---:|---|
| 5 | あり | 80.0〜109.2 | 収まる（残り 15.8〜45.0 日） |
| 5 | なし | 72.9〜102.1 | 収まる |
| 3 | あり | 50.8〜68.3 | 収まる |
| 3 | なし | 43.8〜61.3 | 収まる |

交差適合の二行は 340.5 GPU 時間（検出 20 本 × 14.13 h、工程 20 本 × 2.89 h）= 2 枚で 7.1 日。
締切は MICCAI 2027 を 2027-02 下旬（公式未発表）の代表 02-25 とし、今日から 146 日 − 執筆 21 日 = 125 日。
**Tier 1 だけの値である。** P\*-20（約 1 日）、Tier 2・3、設計変更（1 回 79.0〜108.2 日）は入っていない。
seed 5・交差適合ありの高い読みでは残り 15.8 日で、設計変更を一回挟めば収まらない。

B1 の Stage 1 + Tier 1（K=3、縮退なし、24 h/日）は 85.3〜114.5 → 92.4〜121.6 日になり、IPCAI long abstract
（残 121 日）の判定が「収まる」から「読みにより分かれる」に変わった。B1 §7 の地の文を直した。

## 4. 起票者の誤り

1. **asserted_without_measuring** — SPEC §2 の「P→D の W1 界面 run 約 3.6 h（TF32）」に出所が無い。repo の実測は
   `docs/stage0/C2_amp_compile_timing.md` §4 の 3.7406 h（run 内 1.171 倍）で、4.00 / 1.182 = 3.38 h とも合わない。
   指示どおりこの値を計算器へ入れると、実測の無い値が「実測」の行になる。本契約は計算器の W1 を単精度 4.00 h のまま残した。
2. **asserted_without_measuring** — SPEC §2 は「計算器 … 9 月 17 日に K=3・2 枚・24h で全体 74.0〜98.7 日（TF32）と出た」と書くが、
   計算器は TF32 を一度も持っておらず、74.0〜98.7 日は C2 §5 が計算器の外で倍率を当てた値である。
   指示どおり「計算器の前提の差」だけを探すと TF32 の寄与（+13.5〜+18.0 日、差の最大要因）を見落とす。
3. **self_contradiction** — 禁止事項 1「既存の規約の節の本文を変えない」と Task B-2「変更履歴に本契約の行」が両立しない。
   変更履歴表は `naming` 節のアンカーと `issuer_cautions` 節のアンカーのあいだにあり、アンカーで節を切ると naming 節に含まれる。
   指示どおり履歴に行を足すと naming 節の本文が 1 行変わる。本契約は Task B-2 を優先し、差がこの 1 行だけであることを実測で示した。

## 5. 申し送り

- P\*-20 の契約（T-2026-09-27-stage1-ptower-20）は本契約の PR の統合後に起動する（SPEC §8）。カードは
  `docs/proposals/2026-09-27-ptower-20.md`
- カード #1 の「問い」は「どう変わるか」で、雛形の見出し「yes/no で答えが出る一文」に合っていない。
  内容を変えない指示のためそのまま置いた。`check_proposal.py` は形しか見ないため検出しない
- 規約の変更履歴表が naming 節の範囲にある。履歴を末尾の独立した節へ移すか、節の切り出しが履歴を除く形にしないと、
  規約を改訂する契約は毎回「既存節の不変」と衝突する
- TF32 を採用するかは未決（C2 §7）。採用すれば Tier 1 の検出側の行が約 1/1.17〜1/1.18 になる。計算器には入れていない
- 計算器の行ラベル「受け取りは P\*-21」は M v2.1 で P\*-20 になった。本契約では直していない（ラベルだけで数値に影響しない）

## 6. 逸脱

1. **開始時の退避は stash で行った**（Task A-1 は「移動で退避」）。利用者の指示「汚れは退避すること」に従い、
   未追跡の session digest 4 件を `git stash push -u`（`stash@{0}: session digests before T-2026-09-27-stage2-prep`）へ退避した。
   退避時の分岐は `feat/stage1-phase-tower-r3`。戻し方は `git stash pop`
2. **規約の naming 節の範囲が 1 行変わった**（§4 誤り 3）。末尾空白を除けば他の 10 節は byte 同一
3. **allow_write の外へ書いた**: `scripts/build_stage1_group_ap.py`（群 AP の計算。既存の `scripts/build_stage1_dtower_r2_table.py` に倣った）、
   `tests/test_estimate_tier_cost.py`（試験 4 件）、`README.md`（プロジェクト規約が要求）、`tasks/T-2026-09-27-stage2-prep/spec.yaml`（占位の差し替え。Task A-4 の指示）。
   いずれも禁止領域ではなく `make forbidden-check` は pass
4. **計算器に `--doc-sections` と `Assumptions.hours_override` を足した**。B2 が計算器の節の一部だけを載せるため、
   また 9/17 の前提を再現するため。既定の挙動は変わらない
5. **B1 §7 の地の文を直した**（交差適合の追加で 24 h/日・縮退なしの判定が変わったため）
6. **締切の代表日**: 「2027-02 下旬」を 02-25 とした（B1 が IPCAI intention で採った「下旬 = 25 日」と同じ読み）
7. **試験は収集エラー 1 件を許して回した**（`--continue-on-collection-errors`）。このホストに `third_party/Relation-DETR/util/convergence.py` が無い

## 7. 想定外

- このホストの試験で `tests/test_stage1_dtower_convergence.py` が収集エラーになる（`third_party/` が追跡外で、このホストに収束基準の実装が無い）。変更前後で同一
- `make docs-check` は 1 件の食い違い（`docs/proposal-gate.md:41` の `docs/proposals/YYYY-MM-DD-slug.md`）で exit 1。
  `origin/phase0` の一時 worktree でも同じ行が出る既存のもので、本契約の変更ではない
- 既存の失敗 6 件（test_engines 1・test_fetch_task 1・test_research_logger 4）は前契約の記録と同一

## 8. 送出

- commit `001b4309`（本体）、`073f9dc0`（規約の変更履歴の commit 欄）、push は `origin/feat/stage2-prep`
- push は VS Code の askpass が古く失敗したため、`gh auth git-credential` を資格情報の経路にして送った
- PR #198（base phase0）
- 台帳への送出: `make task-report` 成功（verdict pass、起票者の誤り 3 件、報告 11,474 bytes、sha256 `f287a416…`、置換ブロック 0）。送出したのはこの行を書く前の版である
- `.sync-pause` は報告の後に `.sync-pause.released` へ移して解除した
