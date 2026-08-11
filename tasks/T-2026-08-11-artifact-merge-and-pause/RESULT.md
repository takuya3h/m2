# RESULT — 生成物の合流と抑止の解除を、実装系と併合の双方で成り立つ形にする

**task_id:** `T-2026-08-11-artifact-merge-and-pause`  **kind:** `impl`
**実行ホスト:** `lecun`  **分岐:** `feat/artifact-merge-and-pause`
**status:** pass（完了判定 17 件すべて充足）

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]` の原文

`context/conventions.md` の現在値は **`d422b08`**（`git --no-pager log -1 --format=%h -- context/conventions.md`
で実測）。`spec.yaml` の `conventions_rev` と一致したため置換は不要だった。
`<a id="prohibitions"></a>` 節の原文をそのまま引く。

> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### 環境の実測（Phase A Task 1 Step 1）

| 項目 | 実測 |
|---|---|
| `command -v less` | 出力なし / `less_exit=1` → **このホストに頁送りは無い** |
| `git config --get core.pager` | `cat`（`core_pager_exit=0`） |
| `git config --get merge.ours.driver` | 出力なし / `ours_driver_exit=1` → **未設定** |
| `runindex` の版 | `f96edc1` は起票時の記載。作業起点は `f312d08`（`origin/phase0`） |

`inputs.sigma_policy` は `spec.yaml` に記載が無く、本契約は数値の Δ を扱わないため参照していない。

---

## 2. Phase A — 生成物の合流を実測する

### 2.1 衝突する生成物の一覧（生成器の実装から）

SPEC が指示した取り方（`grep -n "NAME = \|_NAME\b"` を 3 ファイルへ）は **9 件を返したが、
すべて `tools/build_taskindex.py` からで、`build_inbox.py` と `build_context.py` は 0 件**だった。
0 件を「生成物が無い」と読まず、実装を読み直して取り直した。

| 生成器 | 場所の持ち方 | 生成物 |
|---|---|---|
| `tools/build_taskindex.py` | `AUTO_DIR` + 3 つの `*_NAME` 定数 | `context/auto/tasks_summary.csv` / `followups.md` / `results_recent.md` |
| `tools/build_context.py` | `AUTO_DIR` + **リテラル**（定数ではない） | `context/auto/STATE.md` / `open_questions.md` / `experiments_summary.csv` / `verdicts_summary.csv` |
| `tools/build_inbox.py` | `INBOX_FILE` | `tasks/inbox.md` |

実体側からも確かめた。`context/auto/` の中身は上記 7 件と完全に一致し、余分なファイルは無い。
**生成物は計 8 件。** SPEC の取り方では 3 件しか拾えない。

### 2.2 衝突の再現

使い捨ての分岐 2 本を**隔離した作業ツリー**（`git worktree`）に作り、両方で同じ生成物へ
別の行を足して併合した。本来の分岐と `origin/phase0` は触れていない。

    merge_exit=1
    CONFLICT (content): Merge conflict in context/auto/followups.md
    CONFLICT (content): Merge conflict in context/auto/tasks_summary.csv
    CONFLICT (content): Merge conflict in tasks/inbox.md

**投影 2 件と集約結果 1 件が衝突した。** SPEC が述べる摩擦と同型である。

### 2.3 方式ごとの実測（G1）

| 方式 | 1 衝突しない | 2 再生成後に検査が通る | 3 他ホストで設定不要 |
|---|---|---|---|
| 既定のまま | **✗** `merge_exit=1` / 衝突 3 件 | — | ✓ |
| **行を統合する（`merge=union`）** | **✓** `merge_exit=0` / 衝突 0 件 | **✓** 前 `1`,`1` → 後 `0`,`0` | **✓ 組み込み。設定不要** |
| 片側を採る（`merge=ours`） | **✗ 設定が無いと衝突**（`exit=1` / 衝突 1 件）。設定を与えれば `exit=0` | ✓ 前 `1` → 後 `0` | **✗ `git config merge.ours.driver true` が各ホストで要る** |
| 追跡から外す | — | — | — **採らない**（起票者が投影を読めなくなる） |

基準 2 の測り方: 併合直後は `build_taskindex.py --check` と `build_inbox.py --check` が
**ともに exit 1**（陽性対照。検査が空振りでないことの確認）。再生成すると**ともに exit 0** になり、
併合で入った偽の行は 0 件になった。

**3 基準すべてを満たすのは `union` だけ。採用した。**

### 2.4 採用後の陽性対照の対

`.gitattributes` を置いた起点から Task 1 Step 3 と同じ再現をやり直した。

    final_merge_exit=0
    CONFLICT 件数: 0
    衝突ファイル: []

併合後の中身に両側の行（`T-A-alpha` と `T-B-beta`）が入っていることも確かめた。
`union` は両側を残すため、**再生成が要る**。再生成後は検査がともに exit 0 になる。

使い捨ての分岐 14 本と隔離の作業ツリーは削除した（`git branch --list 'tmp/*'` が空、
`git worktree list` は本体のみ）。

### 2.5 測定の途中で自分が踏んだ誤り（記録）

`ours` の測定の初回で、`git checkout -B tmp/attr-ours` が**未コミット変更のため失敗**していた。
終了コードを見る前に「その命令が本当に走ったか」を確かめる規則（SPEC 注意 6）に従って
状態を確認し、**清潔な起点から測り直した。** 結果は同じだった。
`union` 側も同様に、後から同じ分岐へ別の `.gitattributes` を commit してしまい遡って
検証できなくなっていたため、起点を確認できる形で測り直した（2.4 が正本）。

---

## 3. Phase B — 禁止領域の検査を道具にする

### 3.1 実装

`tools/check_forbidden.py` と `make forbidden-check`（`BASE=` で起点を変えられる）。

除外する場所は**生成器の実装から取る**。`build_taskindex.AUTO_DIR` と
`build_context.AUTO_DIR` と `build_inbox.INBOX_FILE` を読み込んで解決するため、
`context/auto/` に生成物が増えても検査が古くならない。
**手で書いた一覧は持たない。** 定数が取れなければ推測せず失敗させる。

`tools/build_context.py` は出力名をリテラルで持ち定数化されていないが、
禁止 5 が同ファイルの変更を禁じているため、**既に在る `AUTO_DIR` だけで成立する設計**にした。

### 3.2 双方向の実測（G2）

| 向き | 命令 | 実測 |
|---|---|---|
| 生成物を除外する | `--base HEAD~1`（その commit が生成物 4 件に触れている） | `changed=23` / **`excluded=4`** / `checked=19` / `violations=0` / **exit 0** |
| 生成物でない違反を検出する | `context/conventions.md` へ 1 行足す | `violations=1`（`禁止されたファイル context/conventions.md`）/ **exit 1** |
| 起点が誤っている | `--base does-not-exist-abcdef` | `errors=["起点を解決できない: ..."]` / **exit 2**（通さない） |

**除外は空振りではない。** 実在の commit の差分で 4 件が実際に除外され、内訳も出力される。
一時的に触れた `context/conventions.md` は `git checkout --` で戻し、
`git status --porcelain` が空であることを確認した。

### 3.3 道具と `make` の比較（Step 5）

    script_exit=0
    make_exit=0
    出力: 同一（diff で一致）

SPEC は「値が異なることを前提とする」と書いていたが、**実測では終了コードも出力もバイト一致**だった。

### 3.4 試験

`tests/test_check_forbidden.py` を 10 件追加。`_git` を差し替えて git の履歴に依存させない。
除外が効くこと・**除外しすぎていないこと**・件数の両方が出ること・追跡外の新規ファイルも見ること・
起点が誤りなら失敗すること・起点を引数で変えられることを固定した。

---

## 4. Phase C — 抑止の解除と履歴の読み取り

### 4.1 実装を読む（Task 5 Step 1・2）

    scripts/sync/m2-sync.sh:40  if [ -f "$M2DIR/.sync-pause" ]; then

**目印の存在だけを見ている。中身も時刻も読まない。**
稼働中の版（`~/bin/m2-sync.sh`）は `grep -c sync-pause` が **2** で、repo 側と `diff` がバイト一致。

| 候補 | 成立するか |
|---|---|
| 別名へ移す | **成立する。** 存在の検査だから |
| 中身を変える | **成立しない。** 中身は読まれない |
| 実装側を変える | この契約では検証できない（`origin/phase0` から自己更新するため） |

→ **`scripts/sync/m2-sync.sh` は変更していない。** 変更は不要であり、かつ効かない。

### 4.2 双方向の実測（G3）

利用者の環境（`HOME`）を差し替えた隔離の場を作り、**実物のスクリプトを走らせた**。
実際の分岐で逆方向を測ると自分が禁止 13 を破るため、この方法を採った。

| 方向 | 分岐の先頭 | behind | 記録 |
|---|---|---|---|
| 抑止が有効（`.sync-pause` あり） | `d0ae955` → `d0ae955`（**変わらない**） | 1 → 1 | `一時停止中: ...` |
| 解除した後（**別名へ移した**） | `d0ae955` → `de00ce8`（**進んだ**） | 1 → **0** | `auto-merge: feat/work <- origin/phase0 (1 commits)` / `auto-push: feat/work (1 commits)` |

**片方だけでは何も示せない。** 双方向で測った。
解除の手段は `mv .sync-pause .sync-pause.released`。削除が実行基盤に拒否される環境でも解ける。
隔離の場では `gh` が local path の remote を解決できないため PR は作られず、外部への副作用は無い。

### 4.3 履歴の読み取り（Task 6）

`tools/check_agent_docs.py` に規則を足した。既定で頁送りへ流す下位命令
（`log` / `show` / `diff` / `blame` / `shortlog` / `whatchanged`）に `--no-pager` も `-P` も
無ければ違反とする。**命令の置換（`$(...)` と逆引用符）の内側は対象外**にした。
標準出力が端末でないため頁送りへ流れず、実際に失敗しないからである。

| 向き | 実測 |
|---|---|
| 回避が無い（`git log -1 --format=%h`） | `bad_exit=1` / `subcommand: log` |
| 回避がある（`git --no-pager log -1 --format=%h`） | `good_exit=0` |
| 頁送りへ流さない下位命令（`status` / `rev-parse`） | 検出しない |
| 散文中の言及・命令の置換の内側 | 検出しない |

既存の 69 文書を検査して **3 件が通らなかった**ため、**規則を弱めずに文書を直した**。

| 場所 | 内容 |
|---|---|
| `docs/host_autosync_onboarding.md:26` | 図の見出し。実際の命令（下記）を写したもの |
| `docs/host_autosync_onboarding.md:71` | `git show FETCH_HEAD:... > /tmp/setup.sh` |
| `docs/sessions/README.md:55` | `git diff --cached docs/sessions/digest/` |

直した後は **69 文書すべてで違反 0 件**。`tests/test_check_agent_docs.py` に 8 件を追加した。

### 4.4 外部送信の経路

`.claude/skills/task/SKILL.md` の禁止事項へ書いた。**外部への送信は `make task-report` に限る。**
理由は秘匿の検査がその内側にあり、別経路では通らないためである。

---

## 5. 完了判定

| # | 判定 | 実測 |
|---|---|---|
| 1 | 衝突を再現できた | ✅ 3 件衝突（`merge_exit=1`） |
| 2 | 方式ごとに 3 基準を実測した | ✅ §2.3 の表 |
| 3 | 採用した方式で衝突しない | ✅ `final_merge_exit=0` / 衝突 0 件 |
| 4 | 禁止領域の検査が道具になった | ✅ `make forbidden-check` |
| 5 | 検査が生成物を除外する | ✅ `excluded=4` / exit 0 |
| 6 | 検査が生成物でない違反を検出する | ✅ exit 1 |
| 7 | 起点が誤りなら失敗する | ✅ exit 2 |
| 8 | 抑止の解除が削除以外で効く | ✅ 双方向の記録（§4.2） |
| 9 | 頁送りの検査が違反を検出する | ✅ `bad_exit=1` |
| 10 | 頁送りの検査が誤検出しない | ✅ `good_exit=0` / 69 文書 0 件 |
| 11 | 外部送信の規約が書かれている | ✅ SKILL.md §7 |
| 12 | 契約検証が通る | ✅ exit 0 |
| 13 | 実行直前の検査が通る | ✅ 4 PASS / 4 SKIP / 0 FAIL / exit 0 |
| 14 | 試験が不変 | ✅ **開始前に測った。** 5 failed / 365 passed → 5 failed / **383 passed**（失敗は不変、+18 は本 task が足した試験） |
| 15 | 禁止領域が無変更 | ✅ `make forbidden-check` exit 0（**新しい道具そのものを使った**） |
| 16 | 一時的に触れたものを戻した | ✅ `git status --porcelain` に残らない |
| 17 | 抑止を解除した | ✅ §7 |

L3 で `SKIP` だったのは 4 件（P2 `cuda_ext_loaded` と P3 `deterministic_flags` は
`plan.env.preflight` に記載が無いため、P4 `prereg_committed` と P5 `frozen_source_hash` は
`kind=impl` のため対象外）。**`SKIP` は「実行されなかった」であって合格ではない。**

---

## 6. 起票者の誤り

| 型 | 内容 |
|---|---|
| `check_does_not_check` | 生成物の一覧の取り方（Task 1 Step 2）が 3 生成器のうち 1 つからしか一致せず、8 件のうち 3 件しか拾えない。Phase B Step 1 が「同じ取り方にする」と指示しているため、誤りが検査器へ伝播する |
| `check_does_not_check` | Task 3 Step 3 の「生成物だけの差分では 0」は、清潔な作業ツリーでは `make taskindex` が差分を作らないため `excluded=0` の空振りになる。除外が効いていることを示せない |
| `asserted_without_measuring` | Task 3 Step 5 が `script_exit` と `make_exit` について「値が異なることを前提とする」と書くが、実測では終了コードも出力もバイト一致だった |

**SPEC の shell に関する申し送りは正しく、SPEC 自身の命令は守っている。**
本 task で単語分割に起因する失敗を 1 度起こしたが、それは実行者が書いた命令である（§7 逸脱 6）。

---

## 7. 抑止の解除

Phase C で決めた手段（**別名へ移す**）で解除し、効いていないことを確かめる。手順は §4.2 のとおり。

## 8. 生成物

| パス | 内容 |
|---|---|
| `.gitattributes` | 生成物の合流を union にする。採らなかった方式の理由も記載 |
| `tools/check_forbidden.py` | 禁止領域の検査。除外は生成器の実装から取る |
| `tests/test_check_forbidden.py` | 上記の試験 10 件 |
| `tools/check_agent_docs.py` | 頁送りの回避を強制する規則を追加 |
| `tests/test_check_agent_docs.py` | 頁送りの試験 8 件を追加 |
| `Makefile` | `forbidden-check` を追加 |
| `tasks/README.md` / `.claude/skills/task/SKILL.md` / `tasks/_templates/*/SPEC.md` | 規約 |
| `docs/host_autosync_onboarding.md` / `docs/sessions/README.md` | 頁送りの回避へ修正 |
