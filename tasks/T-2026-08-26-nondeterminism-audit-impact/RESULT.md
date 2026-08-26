# RESULT — T-2026-08-26-nondeterminism-audit-impact

**実行者:** bengio / `feat/nondeterminism-audit-impact`
**実行:** 2026-08-26 07:07:24 JST 開始 / 07:29 JST Phase E（締切 21:07 JST に対し 22 分）
**判定:** PASS（G1・G2・G3・G4 すべて通過）
**成果:** `experiments/analysis/nondeterminism_audit_impact/REPORT.md`
**証跡:** `EVIDENCE.md`（本ファイルから行番号で指す）

## 冒頭に置く結論

**現存する判定 1038 件のうち 1038 件が、決定性を制御していない run の上に立っている。**
決定化して走った 360 run は判定を一つも持たない（`EVIDENCE.md:68`）。

**確定した事実として扱えるのは、`significant` 738 件のうち 18 件（2.4%）である。**
脆い 209 件（28.3%）、要注意 511 件（69.2%）。

**陽性対照 #111 と同型の判定が 22 件ある。** #111 の脆さは比が小さかったからではない
（比 5.345）。判定に使った σ が偶然小さく出たことによる。同じ印を持つ判定を
軸 5 が拾う（`EVIDENCE.md:105`）。

## 1. 解決された参照

| spec の記載 | 解決先 | 値 |
|---|---|---|
| `inputs.denominator.ref` | `runindex/experiments.csv` | `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` / n_seeds=3 / seeds 42,123,456 / split=val / accuracy_mean 0.8973014948553679 / accuracy_pstd 0.005917073407586465 / accuracy_sstd 0.006099179663503103 / n=17 |
| `inputs.sigma_policy`（省略） | `context/conventions.md#sigma` の既定を継承 | `series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired` |
| `contract.conventions_rev` | 実測 | `a8c07e813696d3720ceee648e8aa202224285955` |
| `created_from.runindex_commit` | 実測 | `7918b5dd9aab3d15b3c459f87aebdd9eb1653116` |
| `contract.inject_verbatim` | `conventions#sigma` `#prohibitions` `#issuer_cautions` の原文 | 判定規約は `abs(delta) / sigma >= 1 かつ 全 seed 同符号`。禁止は `no_split_redefine` / `no_raw_write` / `no_estimated_values`（未測定は UNKNOWN） |

**分母に指定された実験自体が該当当事者である。** `sigma_interpretation='unknown'`、
`sigma_source` 空、17 run 全数が決定性を制御していない。

## 2. 母集団（実測。契約の記載と食い違う）

| 対象 | 起票時 | 実測 | 採用 |
|---|---:|---:|---|
| `index.csv` | 751 | **1177** | 実測 |
| `experiments.csv` | 207 | **213** | 実測 |
| `verdicts.csv` | 1038 | **1038** | 一致 |

SPEC 第 6 節・第 8 節-1 に従い実測を採った。L2-8 WARN 2 件はユーザーへ提示し、
「実測側で続行」の回答を得た（`EVIDENCE.md:5`）。

決定性の記録を欠く run **817 / 1177（69.4%）**。合計は母集団と一致（`EVIDENCE.md:68`）。
**`anomalies.md` 26 節の静的解析（953 run）と 11 入口すべてで一致した**（`EVIDENCE.md:215`）。

## 3. 完了判定

| # | 判定 | 結果 | 空振りでないことの確認 |
|---|---|---|---|
| a | 索引の所在 | PASS | 存在しない 3 経路を同じ方法で調べ、3 件とも ABSENT が返った（`EVIDENCE.md:57`） |
| b | 母集団の件数 | PASS | 契約の記載と突き合わせ、index +426 / experiments +6 の食い違いを検出した |
| c | 決定性の内訳 | PASS | 817+360=1177 で母集団と**等号で**一致。超過も不足も無い |
| d | 出所と解釈の突き合わせ | PASS | 欠損は `(記録なし)` で残した。`crosswalk_verdicts.csv` に 7 列 1038 行分の欠損が残る |
| e | 両立しない組み合わせ | PASS | X1=8 / X3=6。X2・X4 は零件だが、同じ列で条件を緩めると 65 行・92 行が返る（`EVIDENCE.md:89`） |
| f | 基準を先に定めた | PASS | 基準 07:25:59 / 分類 07:26:47。記録が 48 秒早い（`EVIDENCE.md:105`） |
| g | 陽性対照 | PASS | #111 が合計 7 で脆いと分類された |
| h | 陰性対照 | PASS | 効果量が大きく σ が群並みの判定が合計 2 で頑健と分類された。分離 5 点 |
| i | すべて分類した | PASS | 1038/1038、未分類 0 件 |
| j | 優先順位 | PASS | 92 群すべてに根拠列（σ疑い/比僅少/言及/入口）がある |
| k | 判定を覆していない | PASS | `runindex/` の差分 0 行、M も D も 0 件（`EVIDENCE.md:175`） |
| l | 外挿していない | PASS | 決定化の実測値を他の入口へ当てはめていない。書いたのは構造の共通性のみ |
| m | 数値が実測へ遡れる | PASS | 全数値が `runindex/` と実装の grep に対応。CSV 4 本と JSON 2 本を同梱 |
| n | 変更範囲の一覧 | PASS | 13 件を一件ずつ列挙（`EVIDENCE.md:175`） |
| o | PR | **後述**（第 7 節） | — |
| p | 報告が二つ | PASS | `RESULT.md` と `EVIDENCE.md` |
| q | 締切に対する経過 | PASS | Phase A 13 分 / B 15 分 / C 18 分 / D 19 分 / E 22 分（840 分に対し） |

## 4. 次の契約で使う値

- 脆い `significant` の 90.9%（209 件中 190 件）が `scripts/train_b2a.py`（115）と
  `scripts/train_t1a.py`（75）の二つの入口に集まる。**この二つを直せば一度に片付く。**
- 再測定の規模は **UNKNOWN**。この二つの入口には `elapsed_seconds` の記録が無い。
  所要が実測できるのは `train_grasp_phase_injection_variants.py`（33.5 秒 / n=420）と
  `train_grasp_phase_injection.py`（6.9 秒 / n=6）だけである。
- 決定化の実測値（σ_d 0.0054519、Δ_min n=3 で 0.0062953 / n=10 で 0.0034481、減速 2.15×）は
  **`train_grasp_phase_injection_variants.py` の経路のもの。他へ当てはめていない。**
- 非決定源として特定された `TeCNO`（`nn.Conv1d` 4 箇所）を、脆い判定を出した 5 入口と
  決定化が実測された経路の**双方が使う**。**構造の共通性は言える。σ の値は言えない。**
- 頑健と分類された 18 件は X1 の 5 実験群に由来する。**「確定した事実」には留保が要る**（REPORT 第 4 節）。

## 5. 起票者の誤り

**第 8 節の申し送り 1・3・4・5・6 はすべて正確だった。** 1.1 の「入口ごとの内訳も出ている」も
`anomalies.md` 26 節に実在した。誤りは次の 2 件である。

1. **陰性対照の要件「種も多く」が母集団と合わない**（`asserted_without_measuring`）。
   種の数の実測最大値は 3 で、「種が多い」判定は存在しない。指示どおり要件にすると
   陰性対照が 0 件になり、G3 を満たせなくなる。n=3（母集団最大）で構成した。
2. **完了判定 c の確認が片側しか見ていない**（`check_does_not_check`）。
   「合計が母集団を超えていれば数え方が誤っている」は数え落としを検出しない。
   等号で確かめた（817+360=1177）。

## 6. 逸脱

1. **`make taskindex` / `make inbox` を実行しなかった**（judgement）。
   skill 手順書は投影の再生成と確認を求めるが、**SPEC 第 5 節 禁止 4 が明示的に禁じている**
   （「四台で別の契約が同時に走っており、これらは必ず衝突する。全ての PR が統合された後、
   一台で一度だけ回す」）。契約固有の禁止を優先した。**投影に現れることは未確認である。**
   `tasks/inbox.d/` への書き込みは契約ごとに別ファイルで衝突しないため実施した。
2. **`spec.yaml` を編集した**（judgement）。P6 が `governance.decisions_required` の空を要求し、
   3 件をユーザーへ提示して「行わない」の回答を得たため空にし、`meta.amendments` へ記録した。
   併せて `PENDING_EXECUTOR_MEASUREMENT` 2 件を実測値へ確定した。
   最初の書式がスキーマに合わず P8 が FAIL になったため、`tasks/_schema/spec.schema.json` を
   読んで `date` / `reason` / `diff` へ書き直した（`EVIDENCE.md:21`）。
3. **作業ツリーを退避しなかった**（judgement）。SPEC Task 1 Step 2 は「汚れていれば退避」と
   指示するが、**追跡下の変更は零件**であり、未追跡は本契約のディレクトリと
   開始前から在った `docs/sessions/digest/` の 1 件のみだった。退避すると作業対象を失う。
4. **`.sync-pause` は既に置かれていた**（environment）。契約配布時に置かれており、
   稼働中の keeper が対応済みであること（`grep -c sync-pause ~/bin/m2-sync.sh` → 2）を
   確かめたうえでそのまま使った。**報告後に移動で解除する。**
5. **`${PIPESTATUS[0]}` が空を返した**（environment）。対話シェルが zsh のため。
   以後は変数へ落として `$?` で取った。SPEC 第 6 節が予告していた事象である。
6. **`make forbidden-check` が fail を返すが契約違反ではない**（environment）。
   違反 10 件はすべて本契約の `outputs.destination` である。道具は `context/auto/` と
   `tasks/inbox.md` しか除外せず、契約が `experiments/` 配下へ成果を置くことを知らない。
   既知の欠陥で、`followups.md` に同じ指摘がある。**内訳を一件ずつ示した**（`EVIDENCE.md:175`）。
7. **REPORT の記述を 1 件訂正した**（judgement）。「種は届いている」は不正確で、
   `torch.manual_seed` は CPU 側のみ、`torch.cuda.manual_seed_all` は 5 入口とも無い
   （`EVIDENCE.md:240`）。

## 7. 想定外

- **陽性対照 #111 の判定行が現在の索引に存在しない。** 決定化ありの run と同じ実験行へ
  再集約され、`delta_*` 列が空になっている（X3）。記録
  （`tasks/T-2026-08-15-training-determinism/RESULT.md:109`）の値を分類器へ入力して対照とした。
- **比が母集団最大（172.27）の判定を陰性対照から外した。** σ/中央値が 0.0644 で、
  陽性対照 #111 の 0.2278 よりさらに小さい。**比の大きさは頑健さの証拠にならない。**

## 8. 送出

PR と台帳への送信は本ファイルの記録後に行う。結果を第 3 節 o 行と本節へ追記する。
