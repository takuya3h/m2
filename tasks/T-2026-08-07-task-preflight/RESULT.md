# RESULT — T-2026-08-07-task-preflight

**実行者:** aolab / feat/task-preflight / 19341085eadeccfa2e5a5ee2bb885e3e257dbd05
**実行日時:** 2026-08-07T11:08:19Z
**判定:** PASS

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy | なし | 自己契約では未使用 |
| frozen_source | なし（inputs に記載なし） | 契約側の参照は無し。ただし P5 の実装のため conventions#frozen_source の正本を実測（下記） |
| conventions_rev | `1201f4f` | 実測 `git log -1 --format=%h -- context/conventions.md` = `1201f4f`。**一致したため置換不要** |
| depends_on | `T-2026-08-06-make-context` | PR #45 マージ済み（`8fcbe69`）。依存は満たされている |

`contract.inject_verbatim` の原文（要約せず転記）。

**`conventions#env_p0`**

    学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
    activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
    数値が変わったまま完走する。

        source .venv-relation-detr/bin/activate   # 検出系
        source .venv/bin/activate                 # 解析・工程系

    拡張のロード確認をログに残すこと。

**`conventions#frozen_source`**

    比較の三角形で認める凍結源は Relation-DETR seed42 完走 checkpoint。
    同定パスは `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。
    転記元: `docs/experiment_log.md` の STEP 0-2、および `configs/stage/s4_phase_baseline.yaml`。

    凍結源を変更してはならない。変更が必要な場合は別 task で判断を記録し、同じ凍結源を使う比較群と分母を再構成する。

    checkpoint の正本 SHA-256 は次のとおり。

        03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824

    サイズは 195421066 bytes。転記元は 2026-08-06 に実施した11ホストの ssh 一括監査であり、
    11 ホスト全てで SHA-256 が一致し、mtime もナノ秒まで同一であった。
    `third_party/` は git の追跡対象外だが、実体はホスト間で同期されている。

    `verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は
    `no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。
    skip する経路は設けない。

**`conventions#prohibitions`**

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

## 2. Task 1 の実測（Phase A・読み取りのみ）

### 2.1 agent 設定の現状

| 項目 | 実測 |
|---|---|
| `.claude/` の git 追跡 | **追跡済み。21 ファイル**（`skills/task/SKILL.md` を含む）。PR / auto-merge 経路で 11 台へ伝播する |
| `.gitignore` の `.claude` 関連 | `settings.local.json`（139 行）/ `worktrees/`（141 行）/ `hooks/*.log`（192 行）のみ。いずれもローカル状態・ログであり除外が妥当 |
| `.codex/` | 本 task 実行前は**存在しなかった** |
| `.stignore` / `.stglobalignore` | 27 行目で `.claude` を Syncthing 除外。git が運ぶため伝播には影響しない |
| Codex の版 | `codex-cli 0.146.0` |
| 既存の symlink 手法 | `AGENTS.md -> CLAUDE.md` が実在。同じ手法を `.codex/skills/task` に用いた |

`.claude/` が追跡済みだったため、SPEC Task 5 Step 3 の「追跡設定を直す」は条件が成立せず、
`.gitignore` は変更していない。

### 2.2 venv の検出方法（G1 の一部）

| 実行条件 | `VIRTUAL_ENV` | `sys.prefix` | `which python` |
|---|---|---|---|
| activate なし | `(空)` | `/home/ubuntu/.pyenv/versions/3.11.4` | `~/.pyenv/shims/python` |
| `.venv` を activate | `/home/ubuntu/slocal2/m2/.venv` | `/home/ubuntu/slocal2/m2/.venv` | `.venv/bin/python` |
| **activate せず `.venv/bin/python` 直叩き** | **`(空)`** | **`/home/ubuntu/slocal2/m2/.venv`** | — |
| `.venv-relation-detr` | **このホストに存在しない** | — | — |

3 行目が設計原則 2（検査器自身が環境を固定しない）の実証である。`sys.prefix` は
インタプリタの実体を指すため、activate していなくても venv の python を直接起動すれば一致する。
このため Makefile では `.venv/bin/python` を使わず PATH 上の `python` を使う実装にした。

### 2.3 CUDA 拡張の同定方法（G1 の一部）

| 項目 | 実測 |
|---|---|
| `import MultiScaleDeformableAttention` | **失敗**（`ModuleNotFoundError`）。トップレベル module ではない |
| 実際の import 経路 | `sys.path.insert(0, "third_party/Relation-DETR")` → `os.chdir(...)` → `import models.bricks.relation_transformer`（`scripts/run_hc_seeds_lecun.sh:83-86` の warmup と同一） |
| 起動に使う venv | `.venv-relation-detr/bin/python`（`run_hc_seeds_lecun.sh:45`） |
| このホストでの検証可否 | **不可**。`third_party/Relation-DETR/` は `checkpoints/` のみで `models/` が無く、`.venv-relation-detr` も存在しない |

import 名は**実測で特定できた**ため、SPEC の「推測した名前で import を書かない」に抵触せず
P2 を実装した。ただし後述のとおり、このホストでは P2 の PASS 経路を実地検証できていない。

### 2.4 決定性フラグの現状

| 項目 | 実測 |
|---|---|
| `src/egosurgery/utils/seed.py:33-34` | `torch.backends.cudnn.deterministic = True` / `benchmark = False` を設定 |
| 同 `:29` | `os.environ["PYTHONHASHSEED"]` を設定 |
| `torch.use_deterministic_algorithms` | **本番コードに呼び出しなし**（`scripts/analysis/diag_same_seed_variance.py` の検出用正規表現にのみ登場） |
| `CUBLAS_WORKSPACE_CONFIG` | **未設定**（環境変数・コードとも） |

いずれも `seed_everything()` が**実行プロセス内で**設定するものであり、別プロセスである
検査器からは観測できない。何をもって合格とするかは backlog **B-20**（🔴・未解決）が
「CUDA を使う 13 本のうち決定性を制御している本は 0 本」として残しているとおり未確定である。

### 2.5 凍結源の同定方法

| 項目 | 実測 |
|---|---|
| ckpt の実在 | あり |
| サイズ | `195421066` bytes（conventions の記載と一致） |
| SHA-256 実測 | `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824`（**conventions の正本と完全一致**） |
| 算出所要 | 0.39 秒（`sha256sum` 実測） |
| 節の書式 | `<a id="frozen_source"></a>` から次の `<a id=` まで。SHA は 4 スペース字下げのコードブロック、パスはバッククォート内 |

## 3. UNKNOWN として常時 SKIP にした検査

| 検査 | 扱い | 理由 |
|---|---|---|
| **P3 `deterministic_flags`** | **常時 SKIP** | 判定基準が実測で定まらない。決定性設定は実行プロセス内で行われ、別プロセスの検査器からは観測できない。外部から見える `CUBLAS_WORKSPACE_CONFIG` を基準にすると repo の規約に無い基準を発明することになる。backlog B-20 が未解決である以上、何を合格とするかは決まっていない |

P2 は常時 SKIP にしていない（import 名を実測で特定できたため）。契約の
`plan.env.preflight` に `cuda_ext_loaded` が列挙されたときだけ実行し、import に
失敗すれば **FAIL** とする。無言で CPU へフォールバックする事故を防ぐのが目的であり、
読み込めない環境で実行を許すと目的を達しないため SKIP にはしない。

## 4. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（環境変数と凍結源の同定方法を実測で確認） | PASS | §2.2 §2.3 §2.4 §2.5 のとおり |
| **G2**（未実施と合格を区別して出力することを実行して確認） | PASS（**コマンド訂正あり・後述**） | (a) impl task → `4 PASS / 4 SKIP / 0 FAIL` exit=0、(b) venv 完全無効化 → `3 PASS / 4 SKIP / 1 FAIL` exit=1 |
| **G3**（二つの実装系で出力が一致することを実行して確認） | PASS | `diff` の結果 `AGENT PARITY OK`（9 行完全一致） |

### 4.1 G2 で見つかった SPEC 内の矛盾（ユーザー判断を仰いで解決した）

SPEC には両立しない 2 つの記述があった。

- line 93-95: 「`$VIRTUAL_ENV` と `sys.prefix` の**片方でも一致すれば PASS**、両方外れれば FAIL」
- line 380-384（G2 の検証コマンド）: `env -u VIRTUAL_ENV python tools/preflight_task.py ...` で
  **`P1` が `FAIL`、`exit=1`** を期待

実測すると次のようになり、G2 の期待どおりにならなかった。

| 実行条件 | `which python` | `sys.prefix` | P1 | exit |
|---|---|---|---|---|
| activate 済み | `.venv/bin/python` | `.venv` | PASS | 0 |
| **SPEC の G2 コマンド**（activate 後に `env -u VIRTUAL_ENV`） | **`.venv/bin/python`** | `.venv` | **PASS** | **0** |
| PATH も外して完全に無効化 | `~/.pyenv/shims/python` | `~/.pyenv/versions/3.11.4` | **FAIL** | **1** |

原因は `env -u VIRTUAL_ENV` が環境変数を消すだけで、`source .venv/bin/activate` が
PATH 先頭に付けた `.venv/bin` を残すことである。そのため `python` が `.venv/bin/python`
のままとなり、line 95 の OR 規則により `sys.prefix` 側で PASS した。
**検査器の実装は正しく、SPEC の検証コマンドが「venv 無効化」を実現できていなかった。**

`escalate_if: [venv_detection_unreliable]` に該当するため gate `on_fail: stop` に従って停止し、
ユーザーへ判断を戻した。**回答は「OR 維持して G2 コマンドを訂正」**であり、次のとおり訂正して
再実行し PASS を確認した。

    env -u VIRTUAL_ENV PATH="/home/ubuntu/.pyenv/shims:/usr/local/bin:/usr/bin:/bin" \
      python tools/preflight_task.py --task T-2026-08-06-make-context
    -> P1 FAIL / exit=1

実運用では `make task-preflight` が PATH 上の `python` を使うため、activate を忘れた状態は
正しく FAIL する（実測済み）。本 task が防ごうとした事故モードは防げている。

## 5. スクリプト単体と `make` 経由の終了コードの差

| 条件 | `python tools/preflight_task.py` | `make task-preflight` |
|---|---|---|
| 全て PASS / SKIP | `0` | `0` |
| FAIL が 1 件以上 | **`1`** | **`2`** |

`make` はレシピ失敗時に自身の終了コード 2 を返し、子プロセスの終了コードは
`make: *** [Makefile:101: task-preflight] Error 1` というメッセージ側にのみ現れる。
前 task の `make context-check` と同じ GNU Make の標準動作であり、実装の不具合ではない。
この差は `tasks/README.md` に明記した。

## 6. Task 5 の実測（二つの実装系）

### 6.1 G3 の diff 結果

`AGENT PARITY OK`。両側 9 行が完全一致した（差分なし）。

**抽出条件は SPEC から調整した。** SPEC の手順は第一実装系の生出力（`pf_a.txt`）と
Codex 出力から grep したもの（`pf_b.txt`）を直接 diff するが、生出力には `RESULT:` 行の前に
空行があり、grep 後の側には無いため必ず差分になる。また Codex の生ログには**同じ出力が 3 回**
現れる（exec 結果・codex の発話・最終回答。一致行の総数 27 行）。そこで**両側に同一の正規化**
（ANSI 除去 → `^P[0-9] |^RESULT:` 抽出）を適用し、Codex 側は最終ブロックを `tail -9` で取った。

### 6.2 Codex が手順を実行できるか

**手順 5 へは進まなかった。** Codex が実際に実行したコマンドは次のとおりで、手順 1 → 2 → 3 → 4 の順に対応する。

1. `sed -n '1,240p' tasks/README.md && sed -n '1,260p' .codex/skills/task/SKILL.md && find tasks ...`（手順 1・**symlink 経由で SKILL.md を読めている**）
2. `sed ... tasks/T-2026-08-06-make-context/{spec.yaml,SPEC.md,RESULT.md}`（手順 1）
3. `make task-validate TASK=T-2026-08-06-make-context`（手順 2）
4. conventions のアンカー抽出と `git log -1 --format=... -- context/conventions.md`（手順 3・参照解決）
5. `source .venv/bin/activate && make task-preflight TASK=T-2026-08-06-make-context`（手順 4）

Codex の最終回答は「手順 1〜4 を完了しました。手順 5（実行フェーズ）は実施していません」であり、
**「SKIP は未実行項目であり、合格扱いにはしていません」と自発的に述べた**。縮約後の SKILL.md が
意図どおり伝わっている。実行後の `git status` にも repo の変更は無く、停止したことを裏づけている。

**環境上の注記**: このホストでは Codex のサンドボックス（bubblewrap）が非特権ユーザー名前空間を
作れず（`kernel.unprivileged_userns_clone` 未許可）、初回実行が失敗して権限昇格のうえ再実行された。
検査結果そのものには影響していないが、Codex を常用するホストでは設定が要る。

## 7. 散文の判断が残っている箇所とその理由（Task 4 Step 4）

SPEC 指定の `grep -n "確認する|判断する|守ること|注意する"` は**該当なし**だった。
より広い語（`してはならない` `尋ねる` `提示` `決める` `評価する` `記録する` 等）で再走査し、
残った各行がコマンドへ置き換えられるかを検討した結果は次のとおり。

| 箇所 | 内容 | 置き換え可否と理由 |
|---|---|---|
| §2（WARN 時） | 内容をユーザーに提示して続行可否を尋ねる | **不可**。人への判断委譲そのものであり、機械が代行したら目的に反する |
| §3 | 参照解決の結果を `RESULT.md` へ原文で記録する | **不可**。検査ではなく生成作業 |
| §5 | `plan.gates` を該当フェーズ直後に評価する | **不可**。gate の `check` は task ごとの自由文であり、汎用の機械検証にするには gate 記述用の DSL が要る（本 task の範囲外） |
| §6 | `RESULT.md` の記述要件（`deviations` を空にしない等） | **不可**。生成作業 |
| §7 | 禁止事項（`runindex/` を手で編集しない等） | 一部は将来機械化可能（例: `git diff` で禁止領域の変更を検出）。本 task の範囲外 |

## 8. 完了判定

| # | 判定 | 結果 |
|---|---|---|
| 1 | 検査器が動く | PASS（`make task-preflight TASK=T-2026-08-06-make-context` exit 0） |
| 2 | SKIP と PASS が区別される | PASS（P2 P3 P4 P5 が SKIP、`4 PASS / 4 SKIP / 0 FAIL`） |
| 3 | FAIL で非ゼロ | PASS（venv 完全無効化でスクリプト exit 1） |
| 4 | テストが全 pass | PASS（**7 passed**） |
| 5 | 契約検証が通る | PASS（`5 task(s), 0 failed`、exit 0） |
| 6 | 全体テストが不変 | PASS（**5 failed / 189 passed**。失敗は実行前と同じ 5 件。passed が 182 から 189 へ増えたのは本 task が足した 7 件） |
| 7 | symlink が実体を複製していない | PASS（`task -> ../../.claude/skills/task`、git 上は mode `120000`・内容 25 bytes） |
| 8 | 二実装系で出力一致 | PASS（`AGENT PARITY OK`） |
| 9 | Codex が手順を実行できる | PASS（手順 1〜4 を実行し 5 の手前で停止） |
| 10 | 手順書に散文の判断が残っていない | PASS（残存分と理由を §7 に記録） |
| 11 | 禁止領域が無変更 | PASS（`git diff --name-only origin/phase0...HEAD -- ...` の出力なし） |

本ブランチが変更したファイルは 6 つ。
`.claude/skills/task/SKILL.md` / `.codex/skills/task` / `Makefile` / `tasks/README.md` /
`tests/test_preflight_task.py` / `tools/preflight_task.py`

## 9. 受入基準の充足

| acceptance | 結果 |
|---|---|
| `make task-preflight` が契約を読み、検査結果を機械可読な形式で出力する | PASS（`<ID> <name> <STATUS> <detail>` の固定書式 + `RESULT:` 行） |
| 契約に列挙されていない検査は未実施として明示され、合格と区別される | PASS（`SKIP` として理由付きで出力。`summarize` が PASS と別に数える） |
| 検査が一つでも失敗すれば終了コードが非ゼロになる | PASS（スクリプト exit 1・`make` 経由 exit 2） |
| 手順書が検査器の呼び出しへ置き換えられ、散文による判断が残っていない | PASS（§4 を置換。残存分は §7 に理由付きで記録） |
| 第二の実装系からも同じ手順で契約を実行できる | PASS（Codex が symlink 経由で手順 1〜4 を実行） |
| 二つの実装系で検査器の出力が一致する | PASS（`AGENT PARITY OK`） |
| `make task-validate` が exit 0 | PASS |

## 10. deviations（指示書どおりにしなかった箇所）

- 指示: G2 ゲートの検証コマンドとして `env -u VIRTUAL_ENV python tools/preflight_task.py ...` で `P1` が FAIL することを期待していた。
- 実際: そのコマンドでは P1 が PASS した（activate 後は PATH に `.venv/bin` が残るため）。gate `on_fail: stop` と `escalate_if: [venv_detection_unreliable]` に従って停止し、ユーザーへ判断を戻した。回答に従い **OR 規則（SPEC line 95）を維持**し、検証コマンドを `PATH` も外す形へ訂正して再実行し PASS を確認した。
- 理由: SPEC 内部に両立しない 2 つの記述があり、実装ではなく検証コマンドが「venv 無効化」を実現できていなかった。詳細は §4.1。
- 分類: SPEC の欠陥（ユーザー承認済み）

- 指示: `tests/test_preflight_task.py` のコード例に `import pytest` が含まれていた。
- 実際: `import pytest` を書かなかった。
- 理由: 7 件のテストのいずれも `pytest` を参照しておらず、import すると `pyproject.toml` の `[tool.ruff.lint] select = ["E","F","W","I"]` の F401（未使用 import）に抵触する。`ruff check` は変更後 `All checks passed`。
- 分類: SPEC の欠陥

- 指示: Task 5 Step 4 で第一実装系の生出力と、Codex 出力を grep したものを直接 diff する。
- 実際: **両側に同一の正規化**（ANSI 除去 → `^P[0-9] |^RESULT:` 抽出）を適用し、Codex 側は `tail -9` で最終ブロックを取ってから diff した。
- 理由: 生出力には `RESULT:` の前に空行があり grep 後の側には無いため必ず差分になる。また Codex の生ログには同じ出力が 3 回現れ（一致行 27 行）、SPEC の grep だけでは 9 行に絞れない。SPEC 自身が「抽出できない場合は抽出条件を実測に合わせて調整し、RESULT に記録する」と定めており、それに従った。
- 分類: 判断が必要だった

- 指示: Task 5 Step 3 で `.claude/` が git 追跡外なら `.gitignore` の追跡設定を直す。
- 実際: `.gitignore` を変更していない。
- 理由: `.claude/` は既に追跡済み（21 ファイル）で条件が成立しなかった。除外されているのは `settings.local.json` / `worktrees/` / `hooks/*.log` のみで、いずれもローカル状態・ログであり除外が妥当。
- 分類: 環境差（条件不成立）

- 指示: なし（想定外の観測）。P7 の probe が `context/auto/` に一時ファイルを作る。
- 実際: 作成後に削除し、削除できたことまで確認する実装にした。実行後に `ls -a context/auto/` と `git status` で残骸ゼロを確認済み。
- 理由: `context/auto/**` は本 task の禁止領域（手で編集しない）。検査器が触るのは避けられないため、痕跡を残さないことを実装と実測の両方で担保した。
- 分類: 判断が必要だった

## 11. 未解決・申し送り

- **`.claude/` `.codex/` が 11 台へ伝播するかは未検証。** `.claude/` が git 追跡済みであることは実測したが、実際に他ホストへ届いて Codex から使えるかは本 task では確認していない（次 task の対象）。あわせて `.stignore` / `.stglobalignore` の 27 行目が `.claude` を Syncthing 除外している一方 `.codex` は除外指定が無いという非対称がある。Syncthing は既定で symlink を同期しないため実害は想定されないが、方針として揃えるかは未決。
- **P2（`cuda_ext_loaded`）の PASS 経路はこのホストで未検証。** `third_party/Relation-DETR/` に `checkpoints/` しか無く `.venv-relation-detr` も存在しないため、import が成功する経路を実地で通せていない。FAIL 経路（import 失敗）のみ実装・確認済み。検出系ホスト（lecun / efros）での確認が要る。
- **P3（`deterministic_flags`）は常時 SKIP のまま。** 判定基準は backlog B-20 の解決を待つ。B-20 が決着したら P3 を実装し直すこと。
- **P5 と conventions の緊張関係。** conventions#frozen_source は「skip する経路は設けない」と定めるが、SPEC の適用規則は P5 を `kind: exp` のみ対象としている。本実装では「適用されるときは決して SKIP へ落とさない（読めない・一致しないは全て FAIL）」と解釈して両立させた。`kind: impl` での SKIP は逃げ道ではなく対象外である旨を detail に出しているが、この解釈でよいかは確認が要る。
- **`make context-check` が現在 FAIL する（本 task の変更とは無関係）。** `context/auto/` の `generated_from_commit` が `2b353f6` のままで、PR #45 のマージコミット `8fcbe69` を指していないため。生成物の中身（runindex の集計値）に差は無く、スタンプだけの差分である。`context/auto/**` は本 task の禁止領域のため再生成していない。マージコミットが作られるたびに同じ状態になる構造的な問題であり、別途扱う必要がある。
- 全体テストの既存 5 件の失敗（`tests/test_engines.py` 1 件、`tests/test_research_logger.py` 4 件）は本 task 範囲外の既存不整合であり、実行前から存在し件数も不変。
- 実行前から存在する未追跡ファイル（`experiments/transfer/_smoke_artifacts_ctrl/` 等 3 件）と、`tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md` の未 commit 変更（行末空白の除去のみ・本 task 開始前から存在）には触れていない。

## 12. 数値の出所

すべての数値は当該コマンドの stdout / stderr、または正本ファイルから実測した。
`sha256sum` の値、テスト件数、行数、終了コード、`git ls-files` の件数はいずれも実行結果である。
未測定の項目は §3 と §11 に UNKNOWN として明示した。
