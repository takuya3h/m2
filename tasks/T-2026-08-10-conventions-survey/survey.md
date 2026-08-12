# 命名と配置と外部連携の実態（2026-08-10）

調査の最終基準は commit `a55f479`。本書は変更案を決定するものではなく、変更前の実測結果を記録する。

## 1. 作業一覧の更新経路

`tasks/todo.md` の内容を作成している主体は **UNKNOWN**。

- 対象は存在し、最終基準で 312 行。
- Git 履歴は 8 commit、記録上の author は全て `takuya3h`。この共通 identity から、人、agent、常駐処理の別は判定できない。
- 追跡下の `todo.md` 参照は session digest 内の読み取りコマンド 1 件のみ。書込み実装は 0 件。
- `.claude/`、`.codex/`、`~/bin/` に書込み実装は見つからず、cron と user timer も 0 件。
- `keeper.sh` は常駐している。調査中の 2026-08-08 05:50:42 UTC に `m2-sync.sh` が `origin/phase0` を fast-forward し、その結果 `tasks/todo.md` は 302 行から 312 行へ更新された。これはこのホストへ配る経路の特定であり、元内容を作った主体の特定ではない。

G1 は未達として利用者へ調査範囲を提示し、`UNKNOWN` のまま続行する承認を得た。

## 2. ホスト固有の内容を持つ追跡物

確実に「複数ホストが同じ経路を独立に書き換える」と実証できたものは 0 件。分岐間の blob 差だけでは、独立書換えと共有 commit の取り込み遅れを区別できないため、推測で分離対象にしない。

| 経路 | 判定 | 根拠 |
|---|---|---|
| `tasks/todo.md` | 判断保留 | 12 本の `origin/exp/*` で 3 blob 状態。共有 `phase0` の取り込みで実際に変化したが、元の書換主体は UNKNOWN |
| `tasks/inbox.md` | 判断保留 | 12 本中 7 本で対象なし、存在する分岐では 2 blob 状態。直近変更は共有 task commit で、独立書換えを実証できない |
| `OPERATION.md` | 記録として残すもの | 12 本中 2 本で対象なし、存在する分岐では 2 blob 状態。共有運用文書の履歴差であり、ホスト別設定ではない |
| `docs/TODO.md` | 記録として残すもの | 全 12 本で同一 blob。ホスト差なし |
| `configs/default.yaml` | 記録として残すもの | 全 12 本で同一 blob。論理ホスト名は環境変数から注入する共有設定 |
| `runindex/runs/` と `runindex/index.csv` | 判断保留 | `tools/harvest_runindex.py` が実験証跡から生成する派生物。分岐間で `index.csv` は 4 blob 状態だが、ホスト分離ではなく正本と再生成方針の判断が必要 |
| `context/auto/` | 判断保留 | `tools/build_context.py` が runindex から生成する投影。`STATE.md` は存在する 6 分岐で 3 blob 状態。派生物として扱うべきで、ホスト固有記録とは未確定 |
| `docs/sessions/digest/` | 判断保留 | `tools/session_digest.py` がローカル session から一意名で生成する追跡記録。既存方針でも追跡継続の是非が未決定 |
| `experiments/**/server.txt` | 記録として残すもの | 704 件。実験時の実行元を残す不変 provenance であり、同じ経路を複数ホストが独立更新する設定ではない |
| `experiments/**` の config、notes、metrics | 記録として残すもの | ホスト名、絶対経路、GPU 情報を含み得るが、実験時の条件と結果を保存する一次証拠 |
| `docs/` のホスト別調査記録 | 記録として残すもの | ホスト名を含むこと自体が目的の履歴証拠。現在設定として解釈しない |

## 3. 分岐名への依存

`exp/` は追跡下 34 ファイルに存在した。行は同一ファイル内の一致行番号。

| 経路 | 行 | 依存の内容 | 分類 |
|---|---|---|---|
| `.github/workflows/auto-draft-pr.yml` | 4 | push trigger が `exp/**` 限定 | 致命 |
| `scripts/sync/new_experiment_branch.sh` | 6, 24 | `exp/<server>-<theme>-<date>` を生成 | 致命 |
| `scripts/sync/setup_host_autosync.sh` | 11, 22, 158, 171, 176, 177 | `exp/*` のときだけ activate と merge を行う | 致命 |
| `src/egosurgery/utils/git_autosync.py` | 5, 88, 171, 174, 175, 260 | `branch.startswith("exp/")` を満たさないと commit と push を skip | 致命 |
| `tests/test_git_autosync.py` | 9, 37, 89, 119, 162, 165, 167, 341, 358 | `exp/*` guard を契約として固定 | 致命 |
| `OPERATION.md` | 60, 64, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 86, 114, 129, 159, 198, 224, 324, 353 | 現行運用コマンドと分岐例 | 表示 |
| `README.md` | 153, 418, 449, 1055, 1067, 1077, 1081, 1082, 1084, 1273 | 現行説明、同期手順、分岐例 | 表示 |
| `docs/host_autosync_onboarding.md` | 6, 22, 23, 34, 47, 49, 52, 103, 152 | 現行 onboarding 手順 | 表示 |
| `tasks/README.md` | 187 | 自動同期確認の現行例 | 表示 |
| `scripts/train_t1b.py` | 449 | docstring の運用説明 | 表示 |
| `src/egosurgery/engines/mmdet_trainer.py` | 291 | コメントの運用説明 | 表示 |
| `src/egosurgery/utils/experiment_manager.py` | 241 | docstring の運用説明 | 表示 |
| `docs/runindex_transfer_legacy_sigma_investigation_ilya_2026-08-04.md` | 6 | 過去調査の分岐記録 | 記録 |
| `docs/superpowers/specs/2026-07-10-experiment-git-autosync-design.md` | 5, 14, 30, 38, 43, 45, 46, 88, 120, 140, 167, 193, 198, 219 | 既存設計の履歴 | 記録 |
| `docs/sync_instr09_lecun_2026-08-02.md` | 6, 281, 350 | 過去同期の証跡 | 記録 |
| `docs/sync_phase0_merge_lecun_2026-08-02.md` | 6, 235, 247 | 過去同期の証跡 | 記録 |
| `experiments/baselines/s0_041_wiring_verification_seed42/notes.md` | 54 | 実験時の分岐記録 | 記録 |
| `runindex/anomalies/backlog.md` | 47 | 過去の自動同期事象 | 記録 |
| `runindex/runs/baselines__s0_041_wiring_verification_seed42.json` | 50 | 生成済み実験記録 | 記録 |
| `tasks/T-2026-08-05-l2-task-id-uniqueness-fix/RESULT.md` | 38 | 過去 task の結果 | 記録 |
| `tasks/T-2026-08-05-l2-task-id-uniqueness-fix/SPEC.md` | 150 | 過去 task の契約 | 記録 |
| `tasks/T-2026-08-06-frozen-source-and-sigma-notation/SPEC.md` | 410 | 過去 task の契約 | 記録 |
| `tasks/T-2026-08-09-run-wiring-verification/RESULT.md` | 3, 105, 171, 262, 289, 303 | 過去 task の結果 | 記録 |
| `tasks/T-2026-08-09-run-wiring-verification/SPEC.md` | 58 | 過去 task の契約 | 記録 |
| `tasks/T-2026-08-09-scoped-integration/RESULT.md` | 3, 90 | 過去 task の結果 | 記録 |
| `tasks/T-2026-08-09-scoped-integration/SPEC.md` | 6, 54, 109, 120, 172, 235, 244, 427 | 過去 task の契約 | 記録 |
| `tasks/T-2026-08-09-wiring-followup-and-integration/RESULT.md` | 3, 100, 118, 325, 470 | 過去 task の結果 | 記録 |
| `tasks/T-2026-08-09-wiring-followup-and-integration/SPEC.md` | 6, 35 | 過去 task の契約 | 記録 |
| `tasks/T-2026-08-10-third-host-verification/RESULT.md` | 4, 75 | 過去 task の結果 | 記録 |
| `tasks/T-2026-08-10-third-host-verification/SPEC.md` | 6, 43 | 過去 task の契約 | 記録 |
| `tasks/todo.md` | 172 | 過去項目内の分岐名 | 記録 |
| `tests/test_validate_task.py` | 205 | 過去 ref を使う validator fixture | 記録 |
| `third_party_snapshot/efros/Relation-DETR/README.md` | 7 | snapshot 内の過去手順 | 記録 |
| `tools/harvest_runindex.py` | 2958 | backlog へ出力する過去事象の本文 | 記録 |

### 名前を変える場合に同時に直すべき箇所

1. `src/egosurgery/utils/git_autosync.py` の guard と `tests/test_git_autosync.py` の契約を同じ変更で更新する。
2. `scripts/sync/setup_host_autosync.sh` の activate 条件と `scripts/sync/new_experiment_branch.sh` の生成規則を同じ変更で更新する。
3. `.github/workflows/auto-draft-pr.yml` の trigger を同じ切替時点で更新する。
4. 現行手順書の `OPERATION.md`、`README.md`、`docs/host_autosync_onboarding.md`、`tasks/README.md` を同期して更新する。

`~/bin/keeper.sh` と `~/bin/m2-sync.sh` は対象が存在した。`exp/`、`wip`、分岐取得語の一次検索は該当なしだった。別検索では `m2-sync.sh` が現在分岐を汎用的に取得し、同名の `origin/<branch>` が存在する場合に push と Draft PR を行うことを確認した。したがって接頭辞依存はないが、新しい remote ref を先に作る必要がある。

### 探索の漏れの確認

- 拡張子限定検索は 33 ファイル、拡張子なし全文検索は 34 ファイル。
- 漏れた 1 件は `runindex/runs/baselines__s0_041_wiring_verification_seed42.json`。生成済み実験記録として表へ追加した。
- code と config の case-insensitive `wip` 検索は 0 件。対象ファイル群は存在しており、機能依存は該当なし。
- workflow directory は存在し、workflow は `.github/workflows/auto-draft-pr.yml` 1 件。`*.yaml` は対象なし。

G2 は、拡張子なし検索で差を検出し、その 1 件を追加調査したため通過。

## 4. 計算機の識別子

自ホストは `hostname=lecun`、`/etc/hostname=lecun`。`/.dockerenv` が存在し、PID 1 は `sshd`、cgroup は `0::/` で、隔離環境の指標がある。

識別子の解決順は `SERVERNAME`、`EGOSURGERY_SERVER_NAME`、Hydra の `logging.server_name`、最後に `socket.gethostname()`。索引 751 行では `host_raw=aolab` が 10 行あり、全 10 行で正規化後の `host` は空である。収穫器自身が `aolab` を philip と ilya の双方が返すコンテナ内 hostname と定義している。

したがって、重複の原因は **隔離環境で共有された生 hostname と、証跡生成時に論理名が得られなかったことの組合せ**。OS hostname や過去証跡を変更せず、各ホストで論理名 `SERVERNAME` を設定する方向が整合する。過去 10 行の実ホストは証拠から一意に復元できないため `host=null` と `host_raw=aolab` を維持する。

## 5. 外部記録との連携

| 項目 | 所在 | 状態 |
|---|---|---|
| 暗号化された環境設定 | `.env.gpg` | 存在のみ確認。内容は未読 |
| 読込み入口 | `scripts/load_env.sh` | 存在。資格情報の変数名だけを確認 |
| W&B CLI | `.venv/bin/wandb` | 存在 |
| netrc | `.venv/.netrc`、`~/.netrc` | 両方とも対象なし |
| 現プロセスの W&B 環境変数 | 環境 | `WANDB_*` 名は該当なし。値は未表示 |
| 標準設定 | `configs/default.yaml` | `wandb_project`、`wandb_entity`、`wandb_enabled`。既定は無効 |
| 実験 stage 設定 | `configs/stage/` | s0、s2、s3、s4 の対象設定で `wandb_enabled` を有効化 |
| trainer の有効化条件 | `mmdet_trainer.py`、`phase_trainer.py` | `logging.wandb_enabled` が偽なら初期化しない |
| 共通追跡ラッパ | `src/egosurgery/utils/tracking.py` | 資格情報名が未設定、または wandb 未導入なら no-op |
| 二重ロガー | `src/egosurgery/utils/logging.py` | enabled に応じ online または offline。失敗時もローカル記録を継続 |
| 索引の外部記録列 | `runindex/index.csv` | 751 行。wandb、run URL、tracking に相当する列は該当なし |
| ローカル W&B 記録 | `wandb/`、実験配下 | root は存在。深さ 3 以内の実験 W&B directory は 13 件 |
| 外部 W&B run 件数 | 外部サービス | **UNKNOWN**。外部問い合わせを禁止したため未測定 |

G3 の秘密値代入候補検査は記録作成前に 0 件。記録作成後にも再検査する。

## 6. 変更を行う場合の順序

1. `host/<name>` の厳密な grammar と、現行分岐から新分岐への対応表を決める。
2. `git_autosync` guard、branch helper、setup script、tests、CI trigger を `phase0` 上の一つの整合した変更として実装・検証する。
3. 現行手順書を更新する。過去 task、実験証跡、snapshot は書き換えない。
4. 各ホストを切り替える前に、新しい remote ref を作成して `m2-sync.sh` の前提を満たす。
5. ホストごとに論理 `SERVERNAME` を確認してから setup、branch switch、autosync smoke を行う。
6. W&B は環境読込み、trainer 初期化、ローカル run 証跡、外部 run の対応を確認する。外部問い合わせや backfill は別 task で明示承認を得る。
7. 全ホストの push、Draft PR、CI、自動同期が新規則で動くことを確認した後にだけ旧 `exp/*` ref の扱いを判断する。
8. runindex と context の正本、再生成、追跡方針、および session digest の追跡継続は別の意思決定 task に分ける。

以上は安全順序の提案であり、実装と移行の決定は利用者へ委ねる。
