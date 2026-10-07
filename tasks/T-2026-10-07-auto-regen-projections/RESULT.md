# RESULT — T-2026-10-07-auto-regen-projections

**判定: partial。** 仕組みは作った。ただし契約の形（Actions が phase0 へ直接 push する）ではなく、**利用者が G1 で選んだ「自動 PR 型」**で作った。phase0 の保護が直接 push を許さないためである。統合後の動作は未確認で、確かめ方は §4 に書いた。
ホスト `philip`（`hostname` は `aolab`）、分岐 `feat/auto-regen-projections`、起点 `origin/phase0` = `b911810b`。実施日時は 2026-10-07 JST。証跡は `audit.md` にある。

## 1. 解決された参照

- `conventions_rev`: `context/conventions.md` の最終 commit を実測した。結果は `073f9dc0`（2026-10-02 19:46 JST）で、契約の記載 `073f9dc` と一致する。
- `inject_verbatim`: `conventions#prohibitions`（`context/conventions.md:98-107`）と `conventions#issuer_cautions`（`:150-187`）。原文はその行番号のとおりで、要約しない。本契約に効いたのは注意 3（対照を両方向で取る）、4（実装を読む）、8（検査が値を出さない）、11（測定の副作用）、14（狭い読み）である。
- `inputs.data`（`egosurgery_phase_v1`、`ego_val.txt`）は**参照しなかった**。生成の道具はデータを読まない。

## 2. 前提の測定結果（Phase A、`audit.md` §1-4）

| # | 前提 | 結果 |
|---|---|---|
| 1 | phase0 の保護 | **直接 push 不可。** クラシックの保護で PR が必須（承認 0 件）、`enforce_admins: true`。ルールセットは無い。Actions の既定権限は `read` で、`can_approve_pull_request_reviews: false`（`GITHUB_TOKEN` では PR を作れない） |
| 2 | 生成の依存 | 標準ライブラリと PyYAML だけ。Makefile が `.venv/bin/python` を直に呼ぶため、Actions で `.venv` を作る。最小構成での実測は UNKNOWN（PyYAML がキャッシュに無かった） |
| 2' | 読む範囲・書くファイル | 版管理の中で閉じている。書くのは 4 ファイルだけ（`find -newer` で実測） |
| 2'' | 出力の決定性 | **同じ入力で同じ出力になった。** 4 ファイルの sha256 が HEAD、別の作業ディレクトリ、`LC_ALL=C TZ=UTC`、`PYTHONHASHSEED` を 1・2・123 にした場合のすべてで一致した |
| 3 | 既存の workflow | `auto-draft-pr.yml` だけ。契機は `exp/**` で phase0 と重ならない。秘匿の名前は `AUTOSYNC_PR_TOKEN` |
| 4 | 自動の commit による起動 | 新しい workflow は phase0 ではなく `auto/regen-projections` へ push する。そこを契機にする workflow は無い（§3 自己起動） |
| D | 手元の `workflow` 権限 | 事前の確認（`gh auth status`）は実行基盤に拒否された。**初回の push で権限が無いことが判明した**（§6） |

**G1: ask。** escalate_if の「保護設定が自動の直接の書き込みを許さない」に当たった。利用者が「自動 PR 型」を選んだ（`tasks/inbox.d/T-2026-10-07-auto-regen-projections.md`）。

## 3. 作った仕組み（Phase B、完了判定 E）

`.github/workflows/regen-projections.yml`

| 要件 | どう満たしたか |
|---|---|
| 契機 | `push` / `branches: [phase0]` |
| 処理 | Python 3.11 で `.venv` を作り、`pyyaml==6.0.3` を入れる。`make taskindex` と `make inbox` を走らせる |
| 差分 | 4 つの生成物に差分が無ければ `changed=false` で終える（何もしない） |
| 対象 | `git add -- <4 ファイル>` だけを commit する。生成物以外に差分があれば commit せずに exit 1 で止める |
| 同時実行 | `concurrency: regen-projections`、`cancel-in-progress: false`。同時に一つだけ動き、後のものは待つ |
| 競合 | 試行ごとに `git fetch origin phase0` → `reset --hard origin/phase0` → 生成 → push。push に失敗したら一度だけやり直し、二度目も失敗したら exit 1 |
| 自己起動 | push 先は `auto/regen-projections` で、phase0 ではない。この分岐を契機にする workflow は無い。PR を統合すると phase0 への push になって一度起動するが、差分なしで止まる（G2 で実測） |
| 権限 | `contents: write` だけ。PR の作成は既存の `AUTOSYNC_PR_TOKEN`（Pull requests の Read and write だけ）で行う |
| 作成者 | `github-actions[bot]`、件名は `chore(auto): 生成物を作り直す（phase0 <sha>）` |

**G1 による形の変更。** 差分があるときは、`auto/regen-projections` を「phase0 の先頭 + 1 commit」に置き直して force push する。PR が無ければ作る。人の操作は「PR を統合する」だけになる。

## 4. 統合後の確かめ方（完了判定 I）

**本 PR を phase0 へ統合すること自体が最初の契機になる。** 本契約の記録で生成物が古くなっているためである。

| 確かめること | 方法 |
|---|---|
| 起動したか | 統合の直後に `gh run list --workflow regen-projections.yml --limit 3` を実行し、`push` / `phase0` の実行が一件現れることを確かめる |
| 何をしたか | `gh run view <id> --log` で「差分なし。何もしない」が出たか、push と PR 作成が行われたかを見る。PR は `gh pr list --head auto/regen-projections` で確かめる |
| 生成物だけか | `gh pr diff <PR> --name-only` が 4 ファイルの部分集合であること |
| 自己起動していないか | 自動 PR を統合した後、`regen-projections` の実行が一件だけ増えて「差分なし」で終わること。`auto/regen-projections` への push で実行が増えていないこと |
| 失敗したとき | Actions の画面で `regen-projections` の失敗した段を見る。`::error::` の文言は 3 種ある。生成物以外の差分、push に二度失敗、`AUTOSYNC_PR_TOKEN` が未設定。PAT が失効していれば `gh pr` の段が 401 になる |

## 5. 手元の試験（完了判定 F・G、G2: pass）

偽の origin（bare リポジトリ）を scratchpad に作り、workflow の `run` 部分を取り出して同じ順で実行した。`gh` は呼び出しを記録するだけの偽物に差し替えた。

| 場合 | 結果 |
|---|---|
| F: 差分なし | exit 0、`changed=false`、分岐も作られず、`gh` の呼び出しも 0 件 |
| G: 入力（`inbox.d` と `result.yaml`）だけを変えた commit | `auto/regen-projections` が phase0 の先頭 + 1 commit になった。差分は 4 ファイルの M だけ。`gh pr list` → `gh pr create` の順に呼ばれた |
| G2: 自動の commit を統合した後に再実行 | exit 0、`changed=false`（収束する） |
| 陽性対照: 生成物以外の未追跡ファイル | exit 1、commit しない |
| push を 1 回目だけ拒否 | 試行 2 で成功、`changed=true` |
| push を常に拒否 | exit 1、`changed` は出ない |

試した生成物は scratchpad の中にだけあり、記録には含めていない。作業ツリーの `git status --porcelain` は試験の前後で一致した。書式の検査（actionlint、yamllint）は**道具が無く UNKNOWN**。YAML として読めることだけ確かめた。

## 6. 送出

- 禁止語と秘匿の検査: §8 を参照。
- 初回の push は exit 1。`workflow` 権限が無いため拒否された。迂回せず利用者へ提示し、利用者が `gh auth refresh -s workflow` で権限を付与した。同じ commit `c110278f` を再送して exit 0。
- PR: **#208**（`feat/auto-regen-projections` → `phase0`）。台帳への送り返しは `make task-report` の終了コードで記録する。

## 7. 起票者の誤り

1. **entrypoints の取り違え。** 契約は `tools/build_context.py` を挙げるが、`make taskindex` と `make inbox` が呼ぶのは `build_taskindex.py` と `build_inbox.py` である。指示どおり `build_context.py` を読めば、生成の依存と書くファイルを誤って記録していた。
2. **保護設定を測らずに「phase0 へ commit して push」と設計した。** Goal の流れ図は直接 push を前提にしている。実際は PR が必須で、指示どおりに作れば初回から push が拒まれる。escalate_if に挙げてはあったため、停止はできた。
3. **P9 spec_lint の WARN 4 件。** `separated_source@SPEC.md:40` は `\` の継続行で `&&` につながっている。`host_mismatch@:5` は `hostname`（`aolab`）と `.servername`（`philip`）の差である。`integration_prohibited_without_pause@:50,:52` は `task_start.sh` が抑止を置くことを検出器が読まない。3 種とも、実行上の害は無かった。

## 8. 規約の適用判定・検査

- `proposal_gate` の禁止語: `tools/check_proposal.py --only forbidden` を送出物 5 件（RESULT.md、result.yaml、audit.md、inbox.d、workflow）に当てた。初回は RESULT.md:19 の 1 語（「同じ出力になる」の意味で使っていた語）に一致した。言い換えた後は 5 件とも exit 0。陽性対照（禁止語を 2 語含む合成文）では 2 件を検出し exit 1。
- `folds` と `symmetry` は**適用されない**（impl で、比較する腕が無い）。
- 秘匿: `tools/report_task.py` の `scan_secrets` を、資格情報を環境に読み込んだうえで同じ 5 件に当てた。結果は 0 件。陽性対照は二つで、鍵の形をした合成文字列は 1 件検出した。合成した環境値の直接照合も検出した。出力は種別だけで、値は出していない。
- その他の検査: `task-validate` exit 0、`forbidden-check` は pass（違反 0、検査 7 件）。`taskindex-check` と `inbox-check` は差分ありで exit 2（禁止 3 のため再生成しない）。`agent-check` は `docs/experiment_settings.md:155` で fail したが、phase0 の上でも exit 1 になる**既存の失敗**で、本契約では触れていない。

## 9. 逸脱・想定外・UNKNOWN

- **逸脱（判断）。** 直接 push 型ではなく自動 PR 型にした（G1 で利用者が判断）。
- **逸脱（環境）。** `gh auth status` と `gh secret list` が実行基盤に拒否された。迂回していない。秘匿の登録一覧は UNKNOWN。`workflow` 権限は無く、push が拒否された後に利用者が付与した。
- **想定外。** `make inbox-check` は exit 2 になる。本契約で `tasks/inbox.d/` に 1 行を足したためで、禁止 3 により再生成しない。統合後に仕組みが直す。
- **申し送り（Step 3、完了判定 H）。** PR の分岐では生成物が古いままで、`taskindex-check` と `inbox-check` が差分を報告し続ける。案は二つある。(a) 契約の検証から `*-check` を外し、phase0 の上での検査に限る。(b) 契約の分岐では「差分あり」を WARN 扱いにする。本契約では検査を変えていない。
- **申し送り。** 差分が無くなったとき、開いたままの自動 PR を閉じる処理は入れていない。人が手で作り直した場合などに、空の PR が残りうる。
- UNKNOWN: Actions 上での実際の動作、PyYAML だけの最小構成での動作、書式の検査。
