# audit — T-2026-10-07-auto-regen-projections

Phase A の測定記録。測定時点の本線は `origin/phase0` = `b911810b`、分岐 `feat/auto-regen-projections`、ホスト `philip`（`hostname` は `aolab`、`.servername` は `philip`）。

## 1. 生成の道具（Step 1 / 完了判定 A）

契約の `inputs.code.entrypoints` は `tools/build_context.py` を挙げるが、`make taskindex` と `make inbox` が呼ぶのは別の道具である（`Makefile:122-138`）。

| 対象 | 道具 | 読む範囲 | 書くファイル |
|---|---|---|---|
| `make taskindex` | `tools/build_taskindex.py` | `tasks/*/result.yaml` と同じ契約の `spec.yaml`（`_` で始まる名前は除く。`:95-106`） | `context/auto/tasks_summary.csv` `context/auto/followups.md` `context/auto/results_recent.md`（`:291-296`） |
| `make inbox` | `tools/build_inbox.py` | `tasks/inbox.d/*.md`（`:56`） | `tasks/inbox.md`（`:155`） |

- **読む範囲は版管理の中で閉じている。** `result.yaml` は追跡 116 件、実在 116 件。`inbox.d/*.md` は追跡 127 件、実在 127 件で一致した。未追跡は本契約の `spec.yaml` だけ（取り込み直後のため）。同期で運ばれるものは読まない。
- **書くファイルは 4 つだけ。** HEAD を書き出した複製で印のファイルを置き、生成の後に `find -newer` で測った。出てきたのは上の 4 ファイルだけだった。
- **依存。** import は標準ライブラリと `yaml`（PyYAML）だけ（`build_taskindex.py:28-36`、`build_inbox.py:16-21`）。装置もネットワークも要らない。手元は Python 3.11.16、PyYAML 6.0.3。
  - **Makefile は `.venv/bin/python` を直に呼ぶ**（`Makefile:123,135`）。Actions では `.venv` を作るか、道具を直に呼ぶ必要がある。`.venv` は `.gitignore:64` で無視されるため、作っても差分には出ない。
  - 最小の venv（PyYAML だけ）での実測は**できなかった**。`uv pip install --offline` はキャッシュに PyYAML が無く失敗した（ネットワークは使わなかった）。システムの python3 には `yaml` が無い。→ **最小構成で動くことは UNKNOWN**（import 文から推定できるだけ）。
- **出力の決定性。** 壁時計を使わない設計になっている（`build_taskindex.py:19-20`、`build_inbox.py:10-11`）。並びは `sorted` で決まる（`build_taskindex.py:95,150,160,222`、`build_inbox.py:56,86`）。実測は HEAD の複製 3 つで、4 ファイルの sha256 を比べた。

  | 条件 | tasks_summary.csv | followups.md | results_recent.md | inbox.md |
  |---|---|---|---|---|
  | HEAD に記録済み | de66c02b4986 | 8adb77d24683 | 7d13bc347121 | 0440b559156f |
  | r1: 複製の中で生成 | 同じ | 同じ | 同じ | 同じ |
  | r2: 別の作業ディレクトリ、`LC_ALL=C TZ=UTC PYTHONHASHSEED=123` | 同じ | 同じ | 同じ | 同じ |
  | r3: `PYTHONHASHSEED` を 1 と 2 にして連続 2 回 | 同じ | 同じ | 同じ | 同じ |

  **同じ入力では同じ出力になった。** 手元の `make taskindex-check` と `make inbox-check` も exit 0 だった。

## 2. GitHub の設定（Step 2 / 完了判定 B）— 読んだだけで、変えていない

`gh api` で読んだ。リポジトリは `takuya3h/m2`（PUBLIC、既定の分岐は `master`）。

- **phase0 にはクラシックの保護がある**（`branches/phase0/protection`）。
  - `required_pull_request_reviews` あり。`required_approving_review_count: 0`
  - `enforce_admins: true`
  - `required_status_checks` なし、`required_signatures: false`、`allow_force_pushes: false`
- ルールセットは `[]`。phase0 に当たる規則も `[]`。
- Actions は `enabled: true`、`allowed_actions: all`。
- 既定の workflow 権限は `default_workflow_permissions: read`、`can_approve_pull_request_reviews: false`。

**解釈。** PR が必須（承認は 0 件でよい）で、管理者にも適用される。したがって **phase0 への直接の push は、Actions の `GITHUB_TOKEN` でも管理者の資格でも拒まれる**。クラシックの保護には Actions を例外にする設定が無い。この点は push を試して確かめたわけではない（禁止 1 のため試さない）。API の応答と GitHub の仕様から読んだ結論である。
また `can_approve_pull_request_reviews: false` なので、`GITHUB_TOKEN` は PR も作れない。既存の workflow のコメント（`auto-draft-pr.yml:5-7`）にも同じことが書かれている。

## 3. 既存の workflow（Step 3 / 完了判定 C）

| ファイル | 契機 | 権限 | 同時実行 | 参照する秘匿（名前だけ） |
|---|---|---|---|---|
| `.github/workflows/auto-draft-pr.yml` | `push` / `branches: ['exp/**']`（`:2-4`） | `contents: read`（`:8-9`） | `auto-draft-pr-${{ github.ref }}`、取り消さない（`:11-13`） | `AUTOSYNC_PR_TOKEN`（`:25`）。コメントでは fine-grained PAT で、権限は Pull requests の Read and write だけ（`:23`） |

- **phase0 への push で動く workflow は無い。** 新しく作るものと契機は重ならない。
- 秘匿の値は読んでいない。`gh secret list` は実行基盤に拒否された（下記）ため、登録されている秘匿の名前の一覧は **UNKNOWN**。上の名前は workflow の本文から取った。
- 自動の commit が起こしうる常駐処理として、各台の `m2-sync.sh` がある。phase0 を ff で取り込み、作業分岐へ auto-merge する（`scripts/sync/m2-sync.sh` の auto-merge 節）。生成物の commit が phase0 に入れば、各台へ配られる。これは意図した結果である。

## 4. 手元の認証（Step 4 / 完了判定 D）

`gh auth status` と `gh secret list` を含むコマンドは**実行基盤に拒否された**。迂回はしていない。→ **`workflow` 権限の有無は UNKNOWN。** 利用者の確認を待っている。
