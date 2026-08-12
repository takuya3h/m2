# RESULT — T-2026-08-10-analysis-artifact-integration

**実行ホスト:** `efros`
**repo の場所:** `/home/ubuntu/slocal/m2`（標準候補の一つと一致。他候補は未探索）
**分岐:** `feat/analysis-artifacts`（作業開始時点で既に `origin/phase0` から作成済みだった）
**実行日:** 2026-08-09 UTC
**判定:** **PASS（契約基準・利用者承認込み）** — 重い中間生成物を除いて分析成果物87ファイルを共有可能にした。G3ゲートで索引変化を検出したが、原因が本taskのコミット対象ではないことを実測で切り分け、利用者の承認を得て継続した。

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | 記載なし | 対象外 |
| `inputs.sigma_policy` | 記載なし | 対象外。数値の改善判定を行わない |
| `inputs.frozen_source.ref` | 記載なし | 対象外。preflight の P5 も `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | `d422b08` へ実測置換 |
| `contract.inject_verbatim` | `conventions#prohibitions`, `conventions#naming` | 下記に原文を転記 |

### `conventions#prohibitions`（原文）

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `conventions#naming`（原文）

```
<a id="naming"></a>
## naming

実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

    {step}_{seq:03d}_{description}_seed{seed}

- `step`: `s0`〜`s9`、または `a1`〜`a7`
- `seq`: 同一 category と step 内の3桁ゼロ埋め連番
- `description`: 実験内容の短い説明
- `seed`: 乱数シード。既定42
```

`1201f4f..d422b08` の差分（`290da51`）は `frozen_source` アンカーへの「検査の適用範囲」追記のみであり、上記2アンカーの原文には差分が無かった。

## 2. Phase A — 棚卸しと除外の確定

`git status --porcelain | grep '^??'` で未追跡19経路を列挙し、`du -sh` と `find -size +1M` で容量を実測した（詳細は `artifact_inventory.md`）。

- **取り込み対象:** 14経路・約3.2M・87ファイル（`experiments/analysis/*` の REPORT.md・csv・json・env・subsets・decisions、`experiments/audit/*`、`experiments/hand2det_dev/audit/`）
- **除外対象:** `delta_convention_2026-07-29/reextract/`（45M、val_regiontoken.npz と val_regiontoken_run2.npz の2ファイル）。特徴量再抽出結果のバイナリキャッシュで、`.gitignore:212` の `*.npz` にも該当し再生成可能
- **判断に迷ったもの:** `delta_convention_2026-07-29/csv/d1_all_runs.csv`（1.6M）。単一ファイルで1M超だが、REPORT.md §7 が直接参照する分析結果表（他の小表の元データ）と判断し取り込んだ

**G1: PASS。** 対象・除外対象を容量つきで列挙し、除外理由を実測で示した。除外1件（想定どおり「重い中間生成物を含む1経路」）。

## 3. Phase B — 秘匿と肥大の検査

環境設定を保存したディレクトリは `delta_convention_2026-07-29/env/`（pip freeze・torch診断・nvidia-smi・repo状態・system情報・.venv構造、計8ファイル）のみだった。全文を目視し、資格情報・APIキー・トークン・パスワードの類は含まれていないことを確認した。

`API[_-]?KEY|SECRET|TOKEN|PASSWORD|PRIVATE[_-]?KEY` への一致は9件。一致内容を目視した結果、すべて `SAME_TOKEN` / `frac_SAME_TOKEN` / `n_SAME_TOKEN` という研究用語（DETR query token の一致率を表す統計変数名。T1a診断・再現性検証レポートで使用）であり、認証トークンではないと判別した。SPEC.md 自身への一致は、Step2 のコマンド例文中の正規表現パターン文字列そのものへの一致で、偽陽性だった。

32文字以上の文字列は4,756件ヒットしたが、件数では判断せず、`env/` を重点確認し、他はCSVヘッダ・実験run名・設定パス・罫線であることをサンプル目視で確認した。高エントロピーなランダム文字列は見当たらなかった。

**G2: PASS。** 秘匿らしき値は見つからなかった。

## 4. Phase C — 取り込みと索引への影響

`.gitignore:212` の `*.npz` が除外対象を既にカバーしていたため、`.gitignore` への追加は不要だった。`git add` は Phase A で確定した14経路を個別指定し（`git add .` は使用せず）、87ファイルをステージした。

- 既存追跡物への差分: `git diff --cached --name-status | grep -vE "^A"` は空 → **追加のみ**
- 1M超ファイル: `d1_all_runs.csv`（1.6M）のみ検出。Phase A で取り込み判断済みの対象と一致、reextract の混入なし
- commit: `abda94d`（`docs(analysis): share analysis reports and tables from a single host`）

### G3ゲート — 索引不変性

再生成前後で `index.csv` が **751 → 788（+37）** に変化した。原因を切り分けた結果、新規収穫された37件はすべて `experiments/baselines/_aborted_codetr_no_config/`・`_failed_num_workers_zero/`・`_smoke_prior_simplehead/`・`_smoke_v2_part3/`、`experiments/transfer/_smoke_*`、`experiments/_smoke_prior/`（`s0_040_wiring_verification` は除く）系のディレクトリ由来で、**本taskがコミットした `experiments/analysis/`・`experiments/audit/` とは無関係**だった。これらのディレクトリはいずれも `git status --porcelain --ignored` で `!!`（`.gitignore` 済み）と確認でき、収穫器（`make runindex`）が `.gitignore` を無視してファイルシステムを直接スキャンしていることが原因と判明した。

作業ツリーは `git checkout -- runindex/ context/auto/` に加え、新規untracked化した `runindex/runs/*.json`（37件）を削除して完全復元した。復元後の `git status --porcelain` は本taskの成果物（`tasks/T-2026-08-10-analysis-artifact-integration/`）以外に差分なし。

`on_fail: ask` の規約に従い、この実測結果（索引は変化したが原因は本taskのコミット対象ではない）を利用者に提示し、「本taskは継続、原因を RESULT.md に詳記」の承認を得た。収穫器が `.gitignore` を無視する挙動そのものは本taskのスコープ外の問題として §6 に申し送る。

## 5. 完了判定

| # | 判定 | コマンド／実測 | 結果 |
|---:|---|---|---|
| 1 | 一覧が容量つきで作られた | `artifact_inventory.md` | 表が埋まっている |
| 2 | 重い中間物が入っていない | Task3 Step4 | 1M超は `d1_all_runs.csv` のみ（判断済み・取り込み対象）。reextractの混入は0件 |
| 3 | 秘匿の検査を目視で行った | 本RESULT §3 | `SAME_TOKEN`（研究用語）と判別、一致内容を記録 |
| 4 | 追加のみ | Task3 Step3 | 追加以外なし |
| 5 | 索引が不変 | Task3 Step6 | **変化した（751→788）が、原因は本taskのコミット対象ではないと実測で切り分け、復元済み。利用者承認済み** |
| 6 | 索引を記録していない | `git diff --name-only origin/phase0...HEAD \| grep -c runindex` | 0 |
| 7 | 手順書に触れていない | `git diff --name-only origin/phase0...HEAD \| grep -cE "OPERATION.md\|README.md\|tasks/README.md\|host_autosync"` | 0 |
| 8 | 契約検証が通る | `make task-validate` | exit 0（WARN 3件、利用者承認済み） |
| 9 | 実行前検査が通る | `make task-preflight` | exit 0（4 PASS / 4 SKIP / 0 FAIL） |
| 10 | 試験が不変 | `python -m pytest tests/ -q` | 開始前（`HEAD~1` へ事後的に一時復元して測定）: 5 failed, 243 passed, 4 skipped。現在HEAD: 同一。**不変** |
| 11 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- data/splits/ context/conventions.md src/ tools/` | 出力なし |

### 取り込んだ報告書の表題一覧（何が読めるようになったか）

1. Δ 分母規約の確定・間引き規則の確認・GPU 環境と bit-exact 検証（`delta_convention_2026-07-29`）
2. EgoSurgery-HTS ─ tool mask 分母確定と G-2 実験 実測レポート（`g2_main_2026-07-29`）
3. EgoSurgery-HTS の tool/phase に対するカバレッジ監査（`hts_coverage_2026-07-30`）
4. EgoSurgery-HTS ─ 分母確定・リーク検査・クラス対応 実測レポート（`hts_next6_2026-07-29`）
5. l0b — raw bundle 来歴監査 REPORT（2026-07-29）（`hts_raw_provenance_2026-07-29`）
6. 再現性の根本原因特定と Δ 規約の再構成（`repro_variance_2026-07-29`）
7. T1a 差分の機構診断・checkpoint 同一性・oracle-tool 正本固定（`t1a_diag_2026-07-29`）
8. egosurgery_tool（術具 bbox）の split × クラス分布 監査（`tool_class_distribution_2026-07-31`）
9. HTS(Hand-Tool-Seg) 公式GT完全版 受け入れ監査（`l0_hts_acceptance/acceptance_report.json`、REPORT.md無し）
10. hand2det l0 監査（4ch/5ch, seed42、gradient flow等の合否記録。`hand2det_dev/audit/`、REPORT.md無し）

## 6. 残る未検証項目と申し送り

- **重い中間生成物はこのホスト（efros）にのみ残っている。** 除外した `delta_convention_2026-07-29/reextract/`（45M）に加え、棚卸し中に `repro_variance_2026-07-29/reextract/`（115M、`.npz`×5）の存在を確認した。後者は最初から `.gitignore` 済みのため本taskの棚卸し対象（未追跡19経路）に含まれず、取り込み・除外の判断対象にもならなかった。いずれも再生成可能だが、必要なら別途取得手段を検討すること。
- **収穫器（`make runindex`）が `.gitignore` を無視してファイルシステムを直接スキャンする。** `experiments/baselines/_aborted_*`・`_failed_*`・`experiments/transfer/_smoke_*` 等、既に `.gitignore` 済み（`!!`）の実験ディレクトリが37件、収穫器には新規に見えて索引へ混入した。本taskはこれを実行せず（`runindex/` を記録しない規約のため作業ツリーへ加えていない）、事実の確認と復元のみ行った。**正本の索引が同じ経路で再生成されると、同様の混入が起きうる。** 正本ホストでの `.gitignore` との整合性確認を推奨する。
- 同様の探索で、このホストには `.gitignore` 済みの `*.npz`（`experiments/g2_main_2026-07-29/features/` 等、計258M超）・`*.pth`（`experiments/baselines/`・`experiments/detector_improve/` 等の checkpoint、計3.4G超）が他にも多数存在することを確認した。いずれも既存の `.gitignore` ルールで無視されており、本taskの棚卸し範囲（未追跡パス）には現れないため取り込み判断の対象外である。
- `make task-validate` の WARN（`conventions.md` の起票後変更、`index.csv`/`experiments.csv` の分母増分）は、`prohibitions`/`naming` アンカーへの差分が無いことを確認した上で利用者承認を得て続行した。

## 7. deviations

1. SPEC.md「0. 前提と禁止事項」の候補パス探索コマンド（`for c in ~/slocal/m2 ...`）とブランチ作成コマンドは実行しなかった。作業開始時点で既に `feat/analysis-artifacts` ブランチ上（`origin/phase0` から分岐済み）にあり、repo の場所も `/home/ubuntu/slocal/m2` で確定していたため。
2. 上記により「応答しないマウント」の事実確認も実施していない。本セッション中にマウント関連のエラーは観測されなかった。
3. 完了判定 #10「試験が不変」は SPEC.md の指示どおり作業開始前に計測すべきだったが、Phase C 完了（commit後）まで着手を失念した。気づいた時点で `HEAD~1`（commit前の内容）へ working tree のみを一時的に復元して事後的にベースラインを測定し、その後現在の HEAD（`abda94d`）へ戻して再測定して同一結果（5 failed, 243 passed, 4 skipped）であることを確認した。git のコミット履歴・ブランチは変更していない。
4. G3ゲートで索引が変化（751→788）した。原因は本taskのコミット対象ではなく、既存の `.gitignore` 済み実験ディレクトリ（37件）を収穫器が拾ったことによるものと実測で切り分けた（詳細は §4）。作業ツリーは完全復元。`on_fail: ask` の規約に従い利用者へ提示し、「本taskは継続、原因を RESULT.md に詳記」の承認を得た。
5. `artifact_inventory.md` 初稿で `g2_main_2026-07-29` の取り込みファイル数を14と記載したが、うち `preregistration/g2_prediction.md` は既にコミット `904c578` で追跡済みであり新規追加ではなかった。`git diff --cached --name-only | wc -l`（87）で実測し、inventory を13に修正した（差分1件）。
6. `d1_all_runs.csv`（1.6M）は除外基準1（単一ファイルが1M超の中間生成物）に字面上該当するが、報告書が直接参照する分析結果表と判断して取り込んだ。「判断に迷ったもの」として `artifact_inventory.md` に理由を記録済み。

## 8. 証拠 commit

| commit | 内容 |
|---|---|
| `abda94d` | 分析成果物87ファイルの取り込み（reextract除外、docs(analysis)） |
