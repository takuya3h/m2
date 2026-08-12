# root-level stray files 棚卸し

調査日: 2026-08-05。対象ファイルの移動・変更・削除は行っていない。
参照件数は `.git`、`.venv`、`third_party`、対象自身、このtaskのSPECを除外した参照ファイル数。

| ファイル | 参照件数 | 参照元 | 初出 commit | 提案 |
|---|---:|---|---|---|
| `auto_logging_implementation.md` | 5 | `docs/auto_logging.md`, `src/egosurgery/utils/{run_logging,research_logger}.py`, `prompts/files111/setup_auto_logging.sh`, `scripts/draft_master_update.py` | `5dcfe1705f19b482a4b03ee2fd88a98d345efbf8` | `archive` |
| `aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py` | 24 | root・`scripts/`・`scripts_philip_deploy/` の抽出/実行スクリプト、`evidence/`、`third_party_snapshot/` | `891953c211c17ad2e775869cf2f79975d80419e9` | `archive` |
| `extract_stage1_features_aligndetr.py` | 7 | `scripts/run_when_gpu_free.sh`, `scripts_philip_deploy/`, `evidence/` | `891953c211c17ad2e775869cf2f79975d80419e9` | `archive` |
| `extract_t1a_regiontoken_aligndetr.py` | 6 | `scripts/run_when_gpu_free.sh`, `scripts_philip_deploy/`, `evidence/` | `891953c211c17ad2e775869cf2f79975d80419e9` | `archive` |
| `run_s0_frozen_aligndetr.sh` | 3 | root・`scripts/`・`scripts_philip_deploy/` の `run_when_gpu_free.sh` | `891953c211c17ad2e775869cf2f79975d80419e9` | `move-scripts` |
| `run_when_gpu_free.sh` | 3 | root・`scripts/`・`scripts_philip_deploy/` の関連ランチャー | `891953c211c17ad2e775869cf2f79975d80419e9` | `move-scripts` |

## 根拠

- `auto_logging_implementation.md` は `prompts/auto_logging_implementation.md` と SHA-256 が一致する。
- AlignDETR config は `scripts_philip_deploy/` の同名ファイルと SHA-256 が一致する。
- rootの2抽出スクリプトは `scripts/` の同名ファイルとそれぞれ SHA-256 が一致する。
- rootの2ランチャーは `scripts/` の同名ファイルと SHA-256 が一致せず、統合方針の判断が必要。

## ゲート

全6件に参照があるため、このtaskでは移動・削除を実行しない。
`archive` 4件は正規配置コピーとの同一性を再確認したうえで、参照元への影響を扱う別taskで実施する。
`move-scripts` 2件は既存 `scripts/` 版との差分を解決する別taskとして起票する。
