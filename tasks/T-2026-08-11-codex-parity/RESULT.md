# T-2026-08-11-codex-parity — 完了報告

Codex だけで、契約の検証、シェル差の実測、手順書修正、機械検査、PR起票、
台帳返却まで実行した。完了判定は `pass` とする。

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]` — `context/conventions.md` の
`#prohibitions` アンカーの原文（`conventions_rev: d422b08`、実測で一致・置換不要）:

> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

分母、sigma policy、凍結 checkpoint の参照は本契約に無い。

## 2. 契約検証とプリフライト

| 段階 | 実測 |
|---|---|
| `make task-validate` | exit 0、WARN 0 件 |
| `make task-preflight` | 4 PASS / 4 SKIP / 0 FAIL |

SKIP は `P2 cuda_ext_loaded`、`P3 deterministic_flags`（契約指定なし）、
`P4 prereg_committed`、`P5 frozen_source_hash`（`kind: impl` のため対象外）。

## 3. Phase A — 実装系と環境の差

### シェル状態

| 測定 | 実測 |
|---|---|
| Codexで別命令として `export` と `source` 後に確認 | `PROBE=未設定 VENV=未設定` |
| Codexで1命令に連結 | `VENV=/home/ubuntu/slocal/m2/.venv` |
| 保持した対話zshへ2回に分けて入力 | `PROBE=yes VENV=/home/ubuntu/slocal/m2/.venv` |
| venvなしのプリフライト | venv FAIL、makeの `exit=2` |
| `source .venv/bin/activate && make task-preflight` | 4 PASS / 4 SKIP、`exit=0` |

G1 は PASS。状態を保持しない実装系と保持するシェル、連結時の陽性対照をすべて測った。

### 隔離・権限・通信

| 項目 | 実測 |
|---|---|
| `kernel.unprivileged_userns_clone` | `1` |
| `kernel.apparmor_restrict_unprivileged_userns` | このカーネルに項目なし |
| `/proc/sys/user/max_user_namespaces` | `255599` |
| `sudo -n true` | パスワード要求、`exit=1` |
| 一時sysctl変更 | sudo不可のため契約どおりSKIP |
| 資格情報なしHTTPS到達 | GitHub APIが `HTTP/2 200`、`exit=0` |
| 通信時の承認入力 | `approval_policy=never` のため要求なし |

### 手順書の棚卸し

`git ls-files` で69文書を列挙し、`.claude/skills/task/SKILL.md` が含まれることを確認した。
`source ` を含む行は180件。散文・履歴・単独操作を除き、前行の状態へ依存する実行例は
8件（skill 1件、tasks/README 2件、Makefile 1件、その他docs 4件）だった。

## 4. Phase B — 文書修正と機械検査

- skill と tasks/README に「命令の書き方」と実装系差3点を追加した。
- `task-notion`、`task-start`、`task-preflight`、`task-report` の例を単独で完結させた。
- 履歴例を `git --no-pager` にした。
- `tools/check_agent_docs.py` と専用試験を追加し、`make agent-check` へ配線した。
- 全69文書で検出された追加4件の環境手順も、明示pythonまたは1命令へ直した。

検査の実測:

| 対照 | 終了コード |
|---|---|
| 分離された `source` と `make task-notion` | 1 |
| 同じ行へ連結した適合例 | 0 |
| 明示的な対象0件 | 1 |
| `python tools/check_agent_docs.py` | 0（69文書、違反0） |
| `make agent-check` | 0（69文書、違反0） |
| 専用pytest | 6 passed |

変更前後のskill内 `make` 操作集合は差分なし（`diff` exit 0）。G2 は PASS。

## 5. 試験と禁止領域

全テストの開始前は `355 passed / 5 failed / 4 skipped`、変更後は
`361 passed / 5 failed / 4 skipped`。既存失敗5件は同一で、新規失敗は0件。
既存失敗は評価レシピ期待値1件と ResearchLogger 4件であり、本変更では直していない。

禁止領域の差分検査は出力なし。`context/conventions.md` とsysctl値は変更しておらず、
演算装置も使用していない。

## 6. コミットとG3

実装コミット:

- `e13291f` — 手順書の命令を自己完結化
- `fbf7bad` — 機械検査と文書修正
- `3cd3cf7` — フェンス内の空行・コメント越し検査を固定
- `fdcacc5` — 契約、実測報告、索引、判断記録を版管理へ記録
- `3d88e0f` — Draft PR #80 を報告へ記録

Draft PR #80 を `feat/codex-parity` から `phase0` へ起票した。統合と自動統合は行っていない。
`source scripts/load_env.sh && make task-report TASK=T-2026-08-11-codex-parity` は exit 0。
初回返却は `replaced_blocks=0` で、手元と台帳の本文SHA-256
`47ee3a9e2e3a273c2059bbd6408b5ed3b11685b918b9f55376f6b286a86ad00e` が一致した。
G3 は PASS。最終版は同じ台帳行を置換更新する。

## 7. 逸脱と起票者の誤り

- `environment`: 非対話sudoが使えず、契約指定どおりsysctl一時変更をSKIPした。
- `environment`: 現在の `approval_policy=never` では通信時の承認入力がなく、起票時の期待と異なった。
- `spec_defect`: Task 4のFiles欄は2文書だけだが、同じ対象集合を走査する検査は他の4文書にも
  真陽性を出した。G2を通すため、検査を弱めず追加文書を最小修正した。

起票者の誤り:

- `shell_assumption`: 現行手順は前命令の仮想環境・資格情報が次命令へ残る前提だった。
- `self_contradiction`: 修正対象ファイル一覧と、全69文書を対象にする検査要件が一致していなかった。
- `check_does_not_check`: sysctlを常に1へ設定する手順は、開始値が既に1なら隔離失敗の原因を測れない。

未測定値は書いていない。同期抑止は最終検証と台帳の最終版照合後に解除する。
