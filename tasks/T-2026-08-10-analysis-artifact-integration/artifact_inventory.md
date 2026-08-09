# 分析成果物の棚卸し（2026-08-10）

実行ホスト: efros（repo: `/home/ubuntu/slocal/m2`）
棚卸し方法: `git status --porcelain | grep '^??'` で未追跡対象を列挙し、`du -sh` で容量、`find -type f -size +1M` で1M超ファイルを実測。

## 取り込む対象

| 経路 | 容量 | ファイル数 | 内容の要点 |
|---|---|---|---|
| `experiments/analysis/delta_convention_2026-07-29/REPORT.md` | 20K | 1 | Δ 分母規約の確定・間引き規則の確認・GPU 環境と bit-exact 検証 |
| `experiments/analysis/delta_convention_2026-07-29/csv/` | 1.6M | 5 | 上記レポートが参照する表（全ラン棚卸し・規約別Δ再計算・正誤表・分割表） |
| `experiments/analysis/delta_convention_2026-07-29/json/` | 40K | 3 | 同上、JSON形式の監査結果 |
| `experiments/analysis/delta_convention_2026-07-29/env/` | 36K | 8 | 同上、実行時の環境記録（pip freeze・torch・nvidia-smi・repo状態等のテキスト） |
| `experiments/analysis/g2_main_2026-07-29/`（新規追加分） | 316K | 13 | EgoSurgery-HTS tool mask 分母確定と G-2 実験 実測レポート（subsets含む）。ディレクトリ内の `preregistration/g2_prediction.md` は既にコミット `904c578` で追跡済みのため新規追加には含まれない |
| `experiments/analysis/hts_coverage_2026-07-30/` | 384K | 4 | EgoSurgery-HTS の tool/phase に対するカバレッジ監査 |
| `experiments/analysis/hts_next6_2026-07-29/` | 324K | 17 | EgoSurgery-HTS 分母確定・リーク検査・クラス対応 実測レポート（decisions/subsets含む） |
| `experiments/analysis/hts_raw_provenance_2026-07-29/` | 76K | 13 | l0b raw bundle 来歴監査レポート |
| `experiments/analysis/repro_variance_2026-07-29/REPORT.md` | 20K | 1 | 再現性の根本原因特定と Δ 規約の再構成 |
| `experiments/analysis/repro_variance_2026-07-29/csv/` | 60K | 5 | 同上、表 |
| `experiments/analysis/repro_variance_2026-07-29/json/` | 68K | 3 | 同上、JSON監査結果 |
| `experiments/analysis/t1a_diag_2026-07-29/` | 188K | 8 | T1a 差分の機構診断・checkpoint 同一性・oracle-tool 正本固定 |
| `experiments/audit/l0_hts_acceptance/` | 12K | 1 | HTS(Hand-Tool-Seg) 公式GT完全版 受け入れ監査（acceptance_report.json） |
| `experiments/audit/tool_class_distribution_2026-07-31/` | 40K | 4 | egosurgery_tool（術具bbox）の split × クラス分布 監査 |
| `experiments/hand2det_dev/audit/` | 20K | 2 | l0 監査（4ch/5ch seed42、gradient flow等の合否記録） |

取り込み対象合計: 約 3.2M / 87 files（`git diff --cached --name-only | wc -l` で実測。うち1ファイルは既追跡のため差分ゼロ、実新規追加は87件）

## 除外する対象

| 経路 | 容量 | 除外の理由 |
|---|---|---|
| `experiments/analysis/delta_convention_2026-07-29/reextract/` | 45M（val_regiontoken.npz 23M、val_regiontoken_run2.npz 23M、計2ファイル） | 基準1（単一ファイルが1M超）・基準2（再生成できる特徴量）に該当。特徴量再抽出結果のバイナリキャッシュで、報告書の結論を読むのに不要かつ再生成可能。`.gitignore:212` の `*.npz` により個別にも無視される |

## 判断に迷ったもの

- `experiments/analysis/delta_convention_2026-07-29/csv/d1_all_runs.csv`（1.6M、5,171指標行）: 単一ファイルで1M超だが、`REPORT.md` §7 が明示的に参照する分析結果（全ラン棚卸し表）であり、他の小さい表（`d1_errata.csv`・`d1_reconciliation.csv`）の元データにあたる。SPEC.md記載の内訳表でも `csv/ 1.6M` は取り込み側に計上されていた。**中間生成物ではなく報告書の一部と判断し、取り込む。**

## 備考（棚卸し範囲外の事実）

- `experiments/analysis/repro_variance_2026-07-29/reextract/`（115M、.npz×5）は `.gitignore:212` の `*.npz` により最初から `git status --porcelain` の未追跡一覧（`??`）に現れず、本taskの棚卸し対象（19経路）に含まれていない。存在を確認したが、対象外のため取り込み判断も除外判断も不要。
- 同様の探索で、このホストには `.gitignore` 済みの `*.npz`（features/ 配下、計 258M）・`*.pth`（checkpoint、計 3.4G超）が他にも多数存在する。いずれも既存の `.gitignore` ルールで無視されており、本taskの棚卸し範囲（未追跡パス）には現れない。RESULT.md §6 で申し送る。
