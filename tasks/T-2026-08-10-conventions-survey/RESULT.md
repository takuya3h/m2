# RESULT — T-2026-08-10-conventions-survey

**実行ホスト:** `lecun`
**実行分岐:** `integrate/wiring-work-20260809`
**最終調査基準:** `a55f479`
**実行日:** 2026-08-08 UTC
**判定:** **PASS（G1 は承認済み UNKNOWN、逸脱あり）** — 実装は行わず、変更前の依存関係を `survey.md` に記録した。

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `meta.depends_on` | `T-2026-08-09-scoped-integration` | `a84ddfd` は `origin/phase0` の祖先。exit 0 |
| `inputs.denominator.ref` | 記載なし | 対象外 |
| `inputs.sigma_policy` | 記載なし | 規約既定の `series=pstd`、`sigma_source=paired_delta`、`delta_sigma_source=paired` を継承。数値判定は行わない |
| `inputs.frozen_source.ref` | 記載なし | 対象外。`kind=impl` のため preflight P5 は SKIP |
| `contract.conventions_rev` | `1201f4f` | 現在の `d422b08` へ実測解決 |
| `contract.inject_verbatim` | `conventions#prohibitions`、`conventions#naming` | 下記に原文を転記 |

`1201f4f..d422b08` の差分は `frozen_source` の検査適用範囲と変更履歴であり、注入対象 2 節の原文に差分は無かった。

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

転記元: `README.md` の「命名規則」。
```

## 2. Phase A — 作業一覧の更新経路

結論は **UNKNOWN**。このホストへ内容を配る直接経路は `keeper.sh` から起動される `m2-sync.sh` の fast-forward と実測できたが、元内容を作成した主体は特定できなかった。Git author 名は主体の種類を区別できない。

### 生の出力

```text
SNAPSHOT_START=a55f479
-rw-rw-r-- 1 ubuntu ubuntu 26847 Aug  8 05:50 tasks/todo.md
312 tasks/todo.md
8083d5d takuya3h 2026-08-08T04:57:02+00:00 docs(tasks): record the third host verification
67c8171 takuya3h 2026-08-05T10:27:41+00:00 docs: update operation and task documentation
eb58a9e takuya3h 2026-08-05T06:52:13+00:00 docs(tasks): mark bootstrap delivery complete
cc75a1c takuya3h 2026-08-05T06:50:37+00:00 feat(tasks): self-apply the contract to the bootstrap task
56e7808 takuya3h 2026-08-05T06:27:14+00:00 feat(tasks): add tasks/ skeleton and contract conventions
076c2f1 takuya3h 2026-08-02T08:01:52+00:00 docs(efros): experiment_log +109 lines, README, todo, hts_audit reports
0ea33ca takuya3h 2026-07-28T05:58:35+00:00 feat(artifacts): 検出側 run の成果物を experiments/transfer/ へ永続化し predictions を既定保存
a697d90 takuya3h 2026-06-20T19:32:40+00:00 feat(stepB): 比較の三角形 STEP B 結合実験一式（B2a/T1a 有意・B1/T1b 実装・再現体制）
tracked_refs=1
tracked_write_like_refs=0
local_bin_todo_refs=0
crontab_lines=0
user_timer_nonheader_lines=0
SNAPSHOT_END=a55f479
```

追跡下の 1 参照は session digest に記録された `tail` コマンドであり、書込みではない。`~/bin/keeper.sh` と Syncthing の常駐は確認したが、両ファイルに `todo.md` 参照は無い。

G1 の失敗条件に従い、利用者へ調査範囲と `UNKNOWN` を提示した。利用者から続行指示を得た。

## 3. Phase B — ホスト固有の追跡物

3 分類の全表は `survey.md` §2 に記録した。確定した「分離すべきもの」は 0 件。派生物と session digest は別の追跡方針が必要なため判断保留とした。

### 生の出力

```text
SNAPSHOT_START=a55f479
host_in_name=282
host_in_content=2500
absolute_path_refs=173
gpu_refs=80
runindex_files=765
context_auto_files=4
session_digest_files=6
server_txt_files=704
remote_exp_refs=12
tasks/todo.md: unique_blob_states=3 missing=0
tasks/inbox.md: unique_blob_states=2 missing=7
OPERATION.md: unique_blob_states=2 missing=2
docs/TODO.md: unique_blob_states=1 missing=0
configs/default.yaml: unique_blob_states=1 missing=0
runindex/index.csv: unique_blob_states=4 missing=0
context/auto/STATE.md: unique_blob_states=3 missing=6
SNAPSHOT_END=a55f479
```

生成経路の実装上の根拠は次のとおり。

```text
tools/harvest_runindex.py:13: Stage 1: experiments/**/metrics.json -> runindex/runs/<ledger_key>.json
tools/harvest_runindex.py:14: Stage 2: runindex/runs/*.json -> runindex/index.csv
tools/build_context.py:2: runindex から軽量ビュー context/auto/ を冪等に生成する
tools/session_digest.py:29: DIGEST_DIRNAME = Path("docs") / "sessions" / "digest"
tools/session_digest.py:245: root / DIGEST_DIRNAME / <一意名>.md
```

分岐間で blob が異なる事実だけでは「複数ホストが独立に書き換えた」と証明できない。`tasks/todo.md`、`tasks/inbox.md`、`OPERATION.md` の直近履歴は共有 commit であり、12 分岐の差にはファイル自体がまだ存在しない古い分岐も含まれる。

## 4. Phase C — 分岐名への依存

`survey.md` §3 に一致した全 34 ファイルと行番号を記録した。致命は次の 5 経路。

1. `.github/workflows/auto-draft-pr.yml`
2. `scripts/sync/new_experiment_branch.sh`
3. `scripts/sync/setup_host_autosync.sh`
4. `src/egosurgery/utils/git_autosync.py`
5. `tests/test_git_autosync.py`

### 生の出力

```text
.github/workflows/auto-draft-pr.yml:4:    branches: ['exp/**']
scripts/sync/new_experiment_branch.sh:24:branch="exp/${server}-${theme}-${date_tag}"
scripts/sync/setup_host_autosync.sh:158:  exp/*)
src/egosurgery/utils/git_autosync.py:174:    if not branch or branch == "HEAD" or not branch.startswith("exp/"):
src/egosurgery/utils/git_autosync.py:175:        return _skipped("current branch is not exp/* ...")
tests/test_git_autosync.py:37:EXP_BRANCH = "exp/efros-test-theme"
all_tracked_files=34
restricted_extension_files=33
outside_restricted_extensions=1
outside_restricted=runindex/runs/baselines__s0_041_wiring_verification_seed42.json
PHASE_C_WIP_FUNCTIONAL_COUNT=0
```

追跡外対象は存在した。一次検索は接頭辞依存に該当せず、別角度の検索で汎用分岐処理を確認した。

```text
/home/ubuntu/bin/keeper.sh exists
該当なし
/home/ubuntu/bin/m2-sync.sh exists
該当なし
/home/ubuntu/bin/m2-sync.sh:32:BR=$(git symbolic-ref --short HEAD 2>/dev/null)
/home/ubuntu/bin/m2-sync.sh:83:if [ "$BR" != "$MAIN" ] && git rev-parse --verify -q "origin/$BR" >/dev/null; then
/home/ubuntu/bin/m2-sync.sh:86:    if git push -q origin "$BR" 2>/dev/null; then
```

G2 の別手段検索で JSON 1 件の漏れを実際に検出し、生成済み記録として全表へ追加した。これにより G2 は通過。

## 5. Phase D — 計算機の識別子

重複原因は、philip と ilya の隔離環境が同じ生 hostname `aolab` を返し、過去証跡の生成時に論理名が得られなかったこと。論理名の解決経路は既に存在する。

### 生の出力

```text
hostname=lecun
etc_hostname=lecun
dockerenv=present
cgroup=0::/
pid1_comm=sshd
ip_command=target_missing
hostnamectl=present rc=1
rows=751
host=lecun:467, efros:206, (空):41, philip:31, andrew:3, bengio:3
host_raw=lecun:467, efros:206, (空):31, philip:31, aolab:10, andrew:3, bengio:3
aolab_rows=10
aolab_normalized_empty=10
aolab_step=s0:10
```

```text
src/egosurgery/utils/server_name.py:8: 1. SERVERNAME
src/egosurgery/utils/server_name.py:9: 2. EGOSURGERY_SERVER_NAME
src/egosurgery/utils/server_name.py:11: 3. logging.server_name
src/egosurgery/utils/server_name.py:12: 4. socket.gethostname()
tools/harvest_runindex.py:182: aolab は philip と ilya の双方が返すコンテナ内 hostname
```

過去 10 行の `aolab` を philip または ilya に割り当てる証拠は無いため、正規化値は `UNKNOWN` 相当の空値を維持する。推測による補完は行わない。

## 6. Phase E — 外部記録との連携

設定所在と状態の全表は `survey.md` §5 に記録した。資格情報の値と外部 API は一切取得していない。

### 生の出力

```text
scripts/load_env.sh exists
.env.gpg exists
.venv/bin/wandb exists
.venv/.netrc target_missing
/home/ubuntu/.netrc target_missing
PHASE_E_ENV_NAMES
該当なし
configs/default.yaml:90: wandb_project
configs/default.yaml:91: wandb_entity
configs/default.yaml:92: wandb_enabled: false
configs/stage/s0_frozen.yaml:100: wandb_enabled: true
configs/stage/s0_tool_baseline.yaml:100: wandb_enabled: true
configs/stage/s2_hand.yaml:111: wandb_enabled: true
configs/stage/s2_hand_independent.yaml:128: wandb_enabled: true
configs/stage/s3_phase_frame.yaml:80: wandb_enabled: true
configs/stage/s4_phase_baseline.yaml:108: wandb_enabled: true
rows=751
external_record_columns=該当なし
wandb_root_exists=True
experiment_wandb_dirs=13
```

無効化経路の実装確認。

```text
src/egosurgery/engines/phase_trainer.py:392: if not logging.wandb_enabled: return
src/egosurgery/engines/mmdet_trainer.py:860: if not logging.wandb_enabled: return
src/egosurgery/utils/tracking.py:27: 資格情報名の環境変数が空なら false
src/egosurgery/utils/logging.py:105: enabled により online または offline
PHASE_E_SPEC_PATTERN_MATCHES=0
```

SPEC の一次 pattern は実際の `wandb_enabled` を検索できず 0 件だったため、実装で使われる名前へ検索を拡張した。G3 の秘密値代入候補は記録作成前 0 件。記録作成後の再検査結果は自己検証節へ記録する。

## 7. 対象なしと該当なし

### 対象なし

- `.venv/.netrc`
- `/home/ubuntu/.netrc`
- `ip` command
- `.github/workflows/*.yaml`。workflow directory と `.yml` 1 件は存在する。

### 対象は存在するが該当なし

- 追跡下の `tasks/todo.md` 書込み実装
- `~/bin/` 内の `tasks/todo.md` 参照
- crontab entry
- user timer entry
- `~/bin/keeper.sh` と `~/bin/m2-sync.sh` の `exp/`、`wip`、指定された分岐取得語への一次一致
- code と config における case-insensitive `wip` 機能依存
- 現プロセスの `WANDB_*` 環境変数名
- `runindex/index.csv` の wandb、run URL、tracking 相当列
- SPEC が指定した `WANDB_MODE`、`wandb.*disabled`、`use_wandb`、`enable_wandb` pattern

### 存在するが利用不能または未使用

- `hostnamectl` は存在するが exit 1。
- `.env.gpg` は存在確認のみで未読。
- 外部 W&B は問い合わせ禁止のため未測定。

## 8. 特定できなかったもの

| 項目 | 結果 | 理由 |
|---|---|---|
| `tasks/todo.md` の元内容を作成した主体 | UNKNOWN | Git author identity が共通で、追跡下、ローカル script、cron、user timer に writer がない |
| `tasks/todo.md` と `tasks/inbox.md` の分離要否 | 判断保留 | 分岐差は実測したが、独立書換えを実証できない |
| runindex と context の将来の正本・追跡方針 | 判断保留 | 派生物であり、ホスト分離とは別の設計判断が必要 |
| session digest の追跡継続 | 判断保留 | 一意名で衝突回避済みだが、ローカル session 記録を共有する方針が未決定 |
| 過去 `host_raw=aolab` 10 行の実ホスト | UNKNOWN | philip と ilya の双方が同じ raw 値を返し、追加識別証拠がない |
| 外部 W&B run 件数と runindex との対応 | UNKNOWN | 索引に対応列がなく、外部問い合わせを行っていない |

## 9. 完了判定

| # | 判定 | 実測 | 結果 |
|---|---|---|---|
| 1 | 更新主体を特定または UNKNOWN | 元 writer は UNKNOWN。配布経路は m2-sync | PASS |
| 2 | ホスト固有候補を3分類 | `survey.md` §2 | PASS |
| 3 | 分岐名依存を列挙 | 34 ファイルを行番号付きで列挙 | PASS |
| 4 | 致命を明示 | 5 経路 | PASS |
| 5 | 別手段で漏れ確認 | JSON 1 件の漏れを検出し追加 | PASS |
| 6 | 識別子重複の原因 | 共有 raw hostname と論理名欠落 | PASS |
| 7 | 外部連携の所在 | `survey.md` §5 | PASS |
| 8 | 秘密値を含まない | 作成前後とも代入候補 0 件。値は未出力 | PASS |
| 9 | 記録以外の変更がない | task 外は開始前からの untracked digest 1 件のみ。hash 不変 | PASS |
| 10 | 契約検証 | 0 failed、exit 0 | PASS |
| 11 | 実行前検査 | 4 PASS、4 SKIP、0 FAIL、exit 0 | PASS |

### 最終自己検証の生の出力

```text
WARN [L2-6] conventions.md が 1201f4f 以降に変更されています。差分を確認してください
WARN [L2-8] index.csv: 起票時 749 → 現在 751（分母が動いています）
WARN [L2-8] experiments.csv: 起票時 206 → 現在 207（分母が動いています）
OK   T-2026-08-10-conventions-survey
1 task(s), 0 failed
task_validate_exit=0
P1 venv_active            PASS
P2 cuda_ext_loaded        SKIP plan.env.preflight に記載なし
P3 deterministic_flags    SKIP plan.env.preflight に記載なし
P4 prereg_committed       SKIP kind=impl のため対象外
P5 frozen_source_hash     SKIP kind=impl のため対象外
P6 decisions_answered     PASS
P7 destination_writable   PASS
P8 contract_valid         PASS
RESULT: 4 PASS / 4 SKIP / 0 FAIL
task_preflight_exit=0
secret_assignment_candidates=0
table_width_errors=0
```

task 外で開始前から存在した untracked digest の SHA-256 は前後とも
`edcfbb35d023f989af406d9c3134a9ce6a19168a359e9542cf3aeff6fdec1210`。本 task では変更していない。

## 10. deviations

1. `contract.conventions_rev=1201f4f` は現在の `d422b08` と異なった。差分を確認し、注入対象 2 節が同一であることを確認して現 revision を使った。
2. G1 は writer を特定できなかった。契約どおり `UNKNOWN` として調査範囲を提示し、利用者の続行指示を得た。
3. zsh で remote ref 一覧を command substitution に入れた初回比較は改行分割されず、無効な集計になった。`while IFS= read` と最終的には Python の `subprocess` に置換し、`rev-parse --verify` 成功時だけを数えた。RESULT には最終集計だけを採用した。
4. workflow の初回 glob は `.yaml` が存在しないため zsh の `nomatch` で command 全体が失敗した。directory の存在を確認して `find` と `rg` で再実行し、`.yml` 1 件を得た。
5. `hostnamectl` の stdout と stderr の byte 数を確認するため、一時的に `/tmp/conventions-survey-hostnamectl.out` と `/tmp/conventions-survey-hostnamectl.err` を作成してしまった。`unexpected_write_detected` として即時報告し、利用者の承認後にその 2 ファイルだけを削除、対象なしを確認した。repository file は変更していない。
6. 標準 sandbox は `bwrap: No permissions to create a new namespace` で読み取り command も実行できなかった。各 command は目的と非秘密性を示して read-only の escalated 実行へ切り替えた。
7. 調査中の 2026-08-08 05:50:42 UTC に常駐 `m2-sync.sh` が HEAD を `bcde0a0` から `a55f479` へ fast-forward した。`unexpected_write_detected` として即時報告し、記録作成を停止して reflog を確認した。旧 HEAD の 749 行、29 ファイルという途中結果は破棄し、最終基準 `a55f479` 上で Phase A/B を再測定し、Phase C 以降も同 HEAD を確認した。
8. G2 の拡張子限定検索は JSON 1 件を漏らした。拡張子なし検索で検出し、理由と経路を表へ追加した。
9. Phase E Step 4 の指定 pattern は実際の無効化 key `wandb_enabled` を含まず 0 件だった。`wandb_enabled`、資格情報名、online/offline mode へ検索を拡張した。
10. `CLAUDE.md` は duplicate context loading を禁じる上位指示により再読しなかった。外部連携の判断には code、config、`scripts/load_env.sh`、既に許可された docs の所在を使用した。
11. プロジェクト一般手順は計画を `tasks/todo.md` に書くが、本 task は task 記録以外の全変更を禁止する。より具体的な契約を優先し、進捗は実行時 plan のみで管理した。
12. 最終 validate は起票時分母から `index.csv` が 749 から 751、experiments が 206 から 207 へ変化したと警告した。調査中の `phase0` fast-forward による基準更新であり、数値比較には使用していない。最終調査は 751 行の `a55f479` に統一した。
13. 最終 RESULT 更新では `apply_patch` が bwrap 制約で 2 回失敗し、`git apply` も hunk を適用できなかった。完全一致する箇所だけを `perl -0pi` で機械的に置換し、直後に再読・再検証した。

## 11. 起票者へ伝えるべき注意点

- `host/<name>` へ先に rename すると、trainer の auto commit と push、host setup、Draft PR workflow が停止または不整合になる。code、test、script、CI を同時に切り替える必要がある。
- `m2-sync.sh` 自体は接頭辞非依存だが、同名の remote branch が存在することを前提にする。各 host の switch より先に remote ref を用意する。
- 過去 task、実験 notes、runindex record にある `exp/` は履歴証拠であり、現在手順と一括置換しない。
- `tasks/todo.md` の配布経路は観測できたが、元 writer は UNKNOWN。分離や自動生成停止を行う前に writer 側を特定する別調査が必要。
- runindex と context はホスト固有設定ではなく派生物。分離、untrack、正本ホストの選択を同じ問題として扱わない。
- raw hostname `aolab` を過去記録で推測補完しない。今後は各 host の論理 `SERVERNAME` を実行前に検証する。
- W&B の外部 run 数は UNKNOWN。ローカル directory 数 13 を外部 run 数として扱わない。backfill や外部照合は、資格情報読込みと外部書込みを明示した別 task にする。
- 本 task は push、PR、外部記録更新、GPU 実行、実装変更を行わない。
