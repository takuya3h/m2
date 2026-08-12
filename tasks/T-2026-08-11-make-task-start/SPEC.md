# 契約の取り込み開始を一つの操作にまとめる

**task_id:** `T-2026-08-11-make-task-start`  **kind:** `impl`  **depends_on:** なし
**実行ホスト:** `lecun`

> **本契約は配布後に一度差し替えている。** 初回配布分は `inputs.data.split_files` が
> 空配列でスキーマ検証に落ちた。データに触れない契約であっても最低 1 件を要求される
> ため、慣行に従いプレースホルダを 1 件置いた。**この欄は本契約の作業対象ではない。**
> なお「データに触れない契約が意味のないプレースホルダを書き続けている」問題は実在
> するが、**本契約の対象外とする**（理由は Task 4 Step 2 の判断事項に記す）。

## Goal

契約を受け取るたびに、次の 6 行を手で並べている。

    git fetch origin
    git checkout -b feat/<slug> origin/phase0
    touch .sync-pause
    source .venv/bin/activate
    source scripts/load_env.sh
    make task-notion TASK=<task_id>

**このうち 4 行を一つの操作にまとめる。** `source` の 2 行は、make がサブシェルで動く
以上、呼び出し元のシェルに環境を返せないため対象外である。到達点は次の 2 行になる。

    source .venv/bin/activate && source scripts/load_env.sh
    make task-start TASK=<task_id>

**手数を減らすことが目的ではない。** 分岐名を手で打つ限り、契約の識別子と分岐名が
ずれる余地が残る。ずれた分岐で作業すると、統合の際にどの契約の成果か辿れなくなる。
**識別子から分岐名を機械的に導き、人が打たないようにすることが本題である。**

### 満たすべき不変条件

| # | 条件 |
|---|---|
| 1 | **途中で失敗したら、実行前の状態に戻る。** 分岐も、一時ファイルも残さない |
| 2 | 既存の Makefile レシピを変更しない。追記のみ |
| 3 | 資格情報の値を出力にも記録にも残さない。**存在の真偽だけを扱う** |
| 4 | 二度実行しても壊れない |

**条件 1 が最も重要である。** 中途半端に分岐だけが残ると、次回以降「分岐が既にある」で
止まり続け、手で片付ける必要が生じる。まとめた意味が失われる。

## 0. 前提と禁止事項

    cd "$(git rev-parse --show-toplevel)"
    git fetch origin
    git checkout -b feat/make-task-start origin/phase0
    touch .sync-pause
    source .venv/bin/activate
    source scripts/load_env.sh

| # | 禁止 |
|---|---|
| 1 | `runindex/**` `context/auto/**` を手で編集する（生成は可） |
| 2 | `experiments/**` `transfer/**` `data/**` を変更・削除する |
| 3 | `tools/harvest_runindex.py` `tools/build_context.py` を変更する |
| 4 | `context/conventions.md` を変更する |
| 5 | 学習・評価コードを変更する（`src/**` `configs/**`） |
| 6 | 資格情報の値を出力・記録する |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | GPU を使う。本 task に GPU を要する処理は無い |
| 9 | 統合する。自動統合を有効化する |
| 10 | **既存の Makefile レシピの中身を変更する。既存ターゲットの削除・改名も含む** |
| 11 | **`scripts/` の既存ファイルを変更する** |

### 本 task に限り解禁するもの

- **`Makefile` への新規ターゲットの追記**（既存レシピには触れない）
- **`scripts/` への新規ファイルの追加**
- 文書への追記（`README.md` または `tasks/README.md`。実態を見て決める）

`conventions_rev` には `d422b08` を入れてある。**Task 1 で現在値を確認し、変わっていれば
置換すること。これは逸脱ではなく手順である。**
常駐処理による統合は**実行者の逸脱ではない。事実として記録する。**

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 19 task 連続で発生している。
直近では `Path.rglob` が symlink を辿らないことを知らずに走査を書き、**実行すれば
画像 0 枚が返って「健全」と誤結論する**指示を出した。実行者が総件数の照合で気づいた。

**加えて本契約の初回配布分は、スキーマを確認せずに欄を空にしてスキーマ検証に落ちた。**
起票者が起票前に回している自己検査は 3 項目のみで、**スキーマ検証を含んでいない。**
落ちる欄は取り込み時まで分からない。

**本 task の起票者は Makefile の構造も `task-notion` の実装も見ていない。**
以下に書く実装の姿は推測である。**実装を読み、食い違えば実装に従い、その旨を記録すること。**

実行環境の対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。**
配列の添字による終了コードの取得は使えない。単語分割も起きない。

| # | 注意 |
|---|---|
| 1 | 検査が空振りでないことを陽性対照で確かめる。**「通ること」だけを確かめない** |
| 2 | 件数が 0 のとき、別の探し方でも 0 になることを直接確認で裏づける |
| 3 | 仕組みの挙動は実装を読んでから信じる |
| 4 | `make` 経由の終了コードは make 自身のもの（失敗時 2）。**スクリプト単体と両方を記録する** |
| 5 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 6 | 環境変数の確認にパイプを使わない。部分シェルができる |
| 7 | 差分の検出は集合差で求める。名前の部分一致で探さない |

---

# Phase A — 既存の仕組みを実測する

## Task 1: 何があるかを測ってから設計する（G1）

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 環境と現在値を確認する**

        pwd; git branch --show-current; ls -la .sync-pause; which python
        git log -1 --format=%h -- context/conventions.md
        git log -1 --format='%h %cI' -- runindex/

  `conventions.md` の値が `d422b08` と異なれば `spec.yaml` を置換する。
  runindex の commit で `created_from.runindex_commit` の `UNKNOWN` を置き換える。

- [ ] **Step 2: Makefile の構造を測り、追記位置を決める（G1）**

        grep -n "^[a-zA-Z0-9_.-]*:" Makefile | cut -c1-120
        echo "--- 総行数 ---"; wc -l Makefile
        echo "--- task 系ターゲットの前後 ---"
        grep -n "task-" Makefile | cut -c1-120

  **追記位置を行番号で決め、その行が既存レシピの内側でないことを確かめる。**
  レシピ行はタブで始まる。追記位置の直前の行がタブで始まっていないことを確認すること。

        sed -n '<決めた位置の前後 5 行>p' Makefile | cat -A | cut -c1-100

  `cat -A` でタブが `^I` として見える。**これを確認せずに挿入しない。**
  確認できなければ G1 は `stop`。

- [ ] **Step 3: `task-notion` の実装を読む**

        grep -n "task-notion" Makefile | cut -c1-160
        ls -la scripts/ | grep -i -E "task|notion"

  実体のスクリプトを開き、次を確定する。**推測で書かない。**

  | 確認事項 | なぜ要るか |
  |---|---|
  | 引数の受け取り方（`TASK=` か位置引数か） | 呼び出し方が決まる |
  | 失敗時の終了コード | 巻き戻しの判定に使う |
  | 既に `tasks/<task_id>/` がある場合の挙動 | 二度実行したときの挙動が決まる |
  | 必要な環境変数の名前 | **値ではなく名前だけを記録する** |
  | 展開先のパスと、失敗時に残るものの有無 | 巻き戻しの範囲が決まる |

- [ ] **Step 4: 分岐名の導出規則を実測で裏づける**

  起票者は「識別子から日付までを剥がしたものが分岐名」と考えているが、**これは
  過去の分岐名からの推測である。** 実際の対応を測る。

        git branch -a --format='%(refname:short)' | grep -E "^(origin/)?feat/" | sort -u
        ls -1d tasks/T-* 2>/dev/null | sort

  **両者を並べ、対応が規則的かを確かめる。** 規則から外れる例があれば列挙し、
  導出規則をどう定めるかを RESULT に書く。**外れ値を無視して規則を決めない。**

- [ ] **Step 5: 前提の確認方法を実測する**

  実装が停止すべき状況を、どう検知するかを決める。**それぞれ実際に測ってから使う。**

        echo "--- 作業ツリーの汚れ ---"
        git status --porcelain | wc -l
        echo "--- 分岐の存在確認 ---"
        git rev-parse --verify --quiet "refs/heads/feat/make-task-start" && echo "ある" || echo "ない"
        echo "--- 仮想環境の有効性 ---"
        python -c "import sys; print(sys.prefix != sys.base_prefix)"
        echo "--- 資格情報の存在の真偽のみ ---"
        python -c "import os; print({k: bool(os.environ.get(k)) for k in ('<Step 3 で判明した変数名>',)})"

  **最後の行は真偽だけを出す。値を出力してはならない。**
  変数名は Step 3 で実測したものを使う。**起票者は名前を知らない。**

- [ ] **Step 6: 契約の欄のうち、最低 1 件を要求するものを実測で列挙する**

  **本契約は初回配布時に `inputs.data.split_files` が空でスキーマ検証に落ちた。**
  同型の欄が他にもあれば、起票のたびに同じ失敗が起きる。**列挙して記録する。**

        python - <<'PY'
        import json, pathlib
        p = pathlib.Path("tasks/_schema/spec.schema.json")
        print("スキーマの所在:", p, "存在" if p.exists() else "無し")
        if not p.exists():
            raise SystemExit("実在する場所を探してから使うこと")
        sch = json.loads(p.read_text(encoding="utf-8"))
        found = []
        def walk(node, path=""):
            if isinstance(node, dict):
                if node.get("minItems"):
                    found.append((path, node["minItems"]))
                for k, v in node.items():
                    nxt = path if k in ("properties", "items", "$defs") else f"{path}.{k}"
                    walk(v, nxt)
            elif isinstance(node, list):
                for x in node: walk(x, path)
        walk(sch)
        print("最低件数を要求する欄:", len(found))
        for f in found: print("  ", f)
        PY

  **キーの辿り方は起票者の推測である。** スキーマの構造を一度目で見て、
  `minItems` の総数が上の走査で拾えているかを `grep -c minItems` と突き合わせること。
  **数が合わなければ走査が漏れている。**

        grep -c "minItems" tasks/_schema/spec.schema.json

  続けて、既存の契約がその欄をどう埋めているかを測る。

        python - <<'PY'
        import yaml, pathlib
        for d in sorted(pathlib.Path("tasks").glob("T-*")):
            f = d / "spec.yaml"
            if not f.exists(): continue
            s = yaml.safe_load(f.read_text(encoding="utf-8"))
            sf = (s.get("inputs", {}).get("data", {}) or {}).get("split_files")
            bl = ((s.get("intent", {}).get("related", {}) or {}).get("backlog"))
            print(f"{d.name}: kind={s.get('meta',{}).get('kind')} split_files={sf} backlog={bl}")
        PY

  **データに触れない契約が、意味のないプレースホルダを何本書いているかを数える。**
  この結果は Task 4 の判断事項の材料になる。**本 task では直さない。**

| Phase A 完了判定 | 期待 |
|---|---|
| 現在値の確認と置換 | 実測値 |
| 追記位置の行番号とタブ確認 | 実測値。既存レシピの内側でないこと |
| `task-notion` の 5 項目 | 実装から確定 |
| 分岐名の導出規則と外れ値 | 実測値。外れ値があれば列挙 |
| 前提の確認方法 | 実測値。資格情報は真偽のみ |
| 最低 1 件を要求する欄の一覧 | 実測値。既存契約の充足状況も |

---

# Phase B — 取り込み開始の操作を実装する

## Task 2: `task-start` を実装する

**Files:** Create `scripts/task_start.sh`（名前は Phase A の慣例に合わせてよい）,
Modify `Makefile`（**追記のみ**）

- [ ] **Step 1: スクリプトを実装する**

  次の順で動くこと。**各段階の前に前提を確認し、満たさなければ何もせずに停止する。**

  | 順 | 動作 | 満たさないときの扱い |
  |---|---|---|
  | 1 | 識別子の形式を検証する | 使い方を出して停止 |
  | 2 | 仮想環境が有効かを確認する | 有効化の方法を出して停止 |
  | 3 | 必要な環境変数が**存在するか**を確認する | 読み込みの方法を出して停止。**値は出さない** |
  | 4 | 作業ツリーが汚れていないかを確認する | 状況を出して停止 |
  | 5 | 分岐が既に存在しないかを確認する | 状況を出して停止 |
  | 6 | `git fetch origin` | 失敗なら停止 |
  | 7 | 分岐を作って切り替える | 失敗なら停止 |
  | 8 | `.sync-pause` を作る | — |
  | 9 | 契約を取り込む | **失敗なら 7 と 8 を巻き戻して停止** |

  **巻き戻しの範囲に注意する。**

  - `.sync-pause` が**実行前から存在していた**場合、巻き戻しで消してはならない。
    実行前の有無を記録し、自分が作った場合にのみ消す
  - 分岐の巻き戻しは、元の分岐へ戻してから新しい分岐を削除する
  - **元の分岐名を最初に控えておくこと**

  形式の検証は `T-YYYY-MM-DD-slug`（slug は小文字英数とハイフン、3〜60 文字）。

- [ ] **Step 2: Makefile に追記する**

  Phase A Step 2 で決めた位置に、**新しいターゲットだけを**追記する。
  既存レシピの内側に入れない。`TASK` が空のときは使い方を出して停止すること。

- [ ] **Step 3: 既存レシピが変わっていないことを差分で示す**

        git diff --stat
        git diff Makefile | cat

  **`Makefile` の差分が追加行のみであることを確認する。** 削除行（`-` で始まる行）が
  1 行でもあれば禁止事項 10 に触れている。

        git diff Makefile | grep -c '^-[^-]' || echo "削除行 0"

  **件数を必ず出す。** `grep -c` は 0 件のとき終了コード 1 を返すため、
  `|| echo` で潰さないと後続が止まる場合がある。実際の挙動を見て書くこと。

| Phase B 完了判定 | 期待 |
|---|---|
| スクリプトが 9 段階を持つ | あり |
| 実行前の `.sync-pause` の有無を記録している | あり |
| 元の分岐名を控えている | あり |
| Makefile の差分が追加のみ | 削除行 0 |

---

# Phase C — 正常系と異常系を陽性対照つきで検査する

## Task 3: 検査する（G2）

**Files:** Create `tasks/T-2026-08-11-make-task-start/audit/`

**「通ること」だけを確かめない。止まるべきときに止まることを確かめる。**

- [ ] **Step 1: 異常系を一つずつ検査する**

  次の 5 通りを実際に起こし、**それぞれについて (a) 停止すること (b) 痕跡が残らないこと**
  を測る。**痕跡の確認は毎回行う。** 停止しても分岐が残っていれば失敗である。

  | # | 起こす状況 | 期待 |
  |---|---|---|
  | 1 | 識別子を空にする | 使い方を出して停止 |
  | 2 | 識別子の形式を崩す（例: 日付が無い） | 停止 |
  | 3 | 作業ツリーを汚す（一時ファイルを追加） | 停止。**検査後にその一時ファイルを消す** |
  | 4 | 同じ識別子で二度実行する | 二度目は停止 |
  | 5 | 台帳に無い識別子を渡す | 停止し、**分岐が残らない** |

  各回の後に必ず次を記録する。**記録を作ってから表示すること。**

        A=tasks/T-2026-08-11-make-task-start/audit
        {
          echo "case=<番号>"
          echo "branch_now=$(git branch --show-current)"
          echo "branch_exists=$(git rev-parse --verify --quiet refs/heads/feat/<slug> && echo yes || echo no)"
          echo "sync_pause=$(test -e .sync-pause && echo yes || echo no)"
          echo "task_dir=$(test -d tasks/<task_id> && echo yes || echo no)"
          echo "porcelain=$(git status --porcelain | wc -l)"
        } > "${A}/case_<番号>.txt"
        cat "${A}/case_<番号>.txt"

  **5 番が本命である。** ここで分岐が残れば、条件 1 が成立していない。

- [ ] **Step 2: 陽性対照 — 検査そのものが働くことを確かめる**

  **上の痕跡確認が空振りでないことを示す。** 意図的に分岐を作った状態で同じ確認を回し、
  `branch_exists=yes` が出ることを確認する。

        git branch feat/__probe_only__
        git rev-parse --verify --quiet refs/heads/feat/__probe_only__ && echo "検出できた"
        git branch -D feat/__probe_only__
        git rev-parse --verify --quiet refs/heads/feat/__probe_only__ && echo "まだある" || echo "消えた"

  **「検出できた」と「消えた」の両方が出ること。** 出なければ、痕跡確認は
  何も見ていないことになる。G2 は `stop`。

- [ ] **Step 3: 正常系を検査する**

  実在する契約で一度通す。**本 task 自身の識別子は使わない**（既に取り込み済みのため）。
  台帳にある未取り込みの契約を使うか、それが無ければ検査用に一つ選ぶ。
  選んだ識別子と理由を記録すること。

  実行後に次を確認する。

  | 確認 | 期待 |
  |---|---|
  | 現在の分岐 | 導出された名前と一致 |
  | `.sync-pause` | 存在する |
  | `tasks/<task_id>/` | 展開されている |
  | 展開されたファイル | `spec.yaml` と `SPEC.md` が存在 |
  | `make task-validate` | 通る |

  **検査後、作った分岐と展開物を片付けること。** 元の作業分岐へ戻る。

- [ ] **Step 4: 終了コードを両系統で記録する**

  **`make` 経由の終了コードは make 自身のものである。**

        bash scripts/task_start.sh <引数>; echo "script=$?"
        make task-start TASK=<識別子>; echo "make=$?"

  正常系と異常系の両方で、**スクリプト単体と `make` 経由の両方を記録する。**

- [ ] **Step 5: 二度実行しても壊れないことを確かめる**

  正常系を通した直後に同じ操作を繰り返し、**壊れずに停止すること**を確認する。
  実行前から `.sync-pause` があった場合に、それが消えないことも併せて確認する。

| Phase C 完了判定 | 期待 |
|---|---|
| 異常系 5 通りの停止と痕跡 | 全件で停止。痕跡なし |
| 痕跡確認の陽性対照 | 検出できることと消えることの両方 |
| 正常系の 5 項目 | 全て確認 |
| 終了コード（両系統・正常異常） | 実測値 |
| 二度実行の挙動 | 壊れずに停止。既存の `.sync-pause` が消えない |

---

# Phase D — 文書化と総括

## Task 4: 記録し、片付ける

**Files:** Modify 文書（Phase A で決めた先）, Create `RESULT.md`, `result.yaml`,
`tasks/inbox.d/T-2026-08-11-make-task-start.md`

- [ ] **Step 1: 文書に追記する**

  契約を受け取ったときの手順を、新しい操作を使う形に書き換える。
  **`source` の 2 行が残ることを明記する。** なぜ残るのか（make がサブシェルで動くため）
  も書く。書かないと、次に読む者が同じ疑問を持つ。

- [ ] **Step 2: `RESULT.md` を書く。次を必ず含める**

  1. 実装した操作の使い方と、成功後の状態
  2. **異常系 5 通りの実測結果（停止したか・痕跡が残ったか）**
  3. 終了コードの実測（スクリプト単体と `make` 経由）
  4. **起票者の推測のうち、実測で裏づけられたものと否定されたもの**
     - 特に分岐名の導出規則と、`task-notion` の失敗時挙動
  5. 判断が要る事項。**次を必ず含める。**
     - **データに触れない契約が、意味のないプレースホルダを書き続けている件。**
       Phase A Step 6 の実測（該当欄と、既存契約が何本それを書いているか）を示し、
       スキーマを緩めるか、`kind` に応じて必須を分けるか、慣行として残すかの
       三択を提示する。**本 task では直していない。** 理由は、スキーマの変更が
       既存契約の検証結果を変えうるため、性質の異なる変更を同じ PR に混ぜないこと

- [ ] **Step 3: 全完了判定を検証する**

  Phase A から C の完了判定の表を読み直し、**各項目に実測値または UNKNOWN が
  対応していることを確かめる。** 対応していない項目は RESULT に明記する。

        git status --porcelain | cut -c1-120
        git diff origin/phase0 --stat | cat

  Expected: 変更は `Makefile`、新規スクリプト、文書、`tasks/` 配下のみ。
  **`src/` `configs/` `experiments/` `data/` `runindex/` に変更が無いこと。**
  検査で作った一時ファイルと検査用分岐が残っていないこと。

- [ ] **Step 4: 同期の抑止を解除する**

        rm -f .sync-pause
        ls -la .sync-pause || echo "解除済み"

- [ ] **Step 5: PR を作る**

  base は `phase0`。**マージはしない。**

| Phase D 完了判定 | 期待 |
|---|---|
| 文書の追記（`source` が残る理由を含む） | あり |
| RESULT に 5 点 | あり |
| 全完了判定の対応 | あり |
| 変更範囲と残骸の確認 | 想定内のみ |
| `.sync-pause` の削除 | あり |
| PR | 作成済み。未マージ |

---

## 想定外が起きたときの扱い

| 事象 | 扱い |
|---|---|
| 追記位置が既存レシピの内側にしか取れない | **G1 は `stop`。** 既存レシピの変更は禁止事項 10 |
| 巻き戻しが成立しない | `escalate_if` に該当。**どこまで戻せてどこから戻せないかを記録して停止する** |
| 分岐名の導出規則が実例と合わない | 外れ値を列挙し、規則をどう定めるかを RESULT に書く。**外れ値を無視して決めない** |
| 実装が SPEC の記述と食い違う | **実装に従う。** SPEC のどこが誤っていたかを書く |
| 痕跡確認が陽性対照で働かない | **G2 は `stop`** |
| 検査に使える未取り込みの契約が無い | 選んだ識別子と理由を記録する。**検査後に必ず片付ける** |
| 資格情報を出力しないと検査できない項目がある | **実施しない。** 何が測れなかったかを `UNKNOWN` として記録する |
| 常駐処理が作業分岐へ統合を行った | **実行者の逸脱ではない。事実として記録する** |
