# 同期処理の設定をどう組み立てるかを実装から確定する

**task_id:** `T-2026-08-24-syncthing-config-survey`  **kind:** `analysis`
**depends_on:** `T-2026-08-24-philip-keeper-autosync`
**実行ホスト:** `philip`（中心）  **repo:** `~/slocal2/m2`

## Goal

**保守作業で全サーバーが初期化された。** 再構築は次まで進んだ。

| 済 | 内容 |
|---|---|
| 済 | 五台で実行環境と論理名が揃った |
| 済 | 同期処理の実体を導入し、**識別子を発行して版管理へ公開**した |
| 済 | 各ノードが**中心宛の鍵を作り、公開鍵を版管理へ公開**した |
| 済 | 常駐処理を配置・起動し、**版管理の自動同期が動いている** |
| 済 | 秘匿情報の合言葉を作り直し、**契約の取り込みと返送が戻った** |
| **未** | **同期処理の相互登録、中継、共有フォルダの定義** |

**起票者は同期処理の設定の組み立て方を把握していない。** 推測で書くと**五台の設定を壊す。**
**本契約は読み取りのみで、次の実装契約に必要な事実を確定する。**

### 確定させること

1. **設定を変える手段は何か。** 常駐させずに変えられるか
2. **設定の構造。** 相手と共有フォルダがどう表されるか
3. **共有フォルダをどう定義し直すか。** 旧構成の定義は失われている
4. **登録と起動の順序。** 中心が先か、ノードが先か

**設定を変更してはならない。同期処理を常駐させてはならない。**

## 0. 前提と禁止事項

**取り込みは台帳から行う。** 合言葉が戻ったため通常の経路が使える。

    cd ~/slocal2/m2
    git --no-pager status --porcelain | grep -c ''
    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-start TASK=T-2026-08-24-syncthing-config-survey

**作業ツリーが汚れていると分岐が作られない。** 先に片付けるか、
**未追跡が残る場合はその件数を控えてから進む。**

**分岐が `feat/` で始まることを確かめる。**

    git branch --show-current
    git --no-pager log -1 --format='%h %s'

| # | 禁止 |
|---|---|
| 1 | **同期処理の設定を変更する**（相手の登録、共有フォルダの追加、設定要素の書き換え） |
| 2 | **同期処理を常駐させる。待ち受けを立てる** |
| 3 | **中継の目印を作る。中継を張る** |
| 4 | 常駐処理を停止・再起動する |
| 5 | 他ホストへ接続する。他ホストの状態を変更する |
| 6 | 鍵を生成・変更・削除する |
| 7 | **生成物を再生成する**（`make taskindex` `make inbox` を実行しない） |
| 8 | 未追跡の成果物を削除・移動・commit する |
| 9 | 秘匿の値を出力・記録する。**識別子と指紋は秘匿ではない** |
| 10 | 装置を使う |
| 11 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 12 | `experiments/**` `transfer/**` `data/**` を変更・削除する |

**禁止 1 と 2 が要である。** 本契約が終わったとき、**設定は開始時と同一**でなければならない。
**要約値で確かめる。**

**禁止 7 の理由。** 生成物は全契約で共有され、**並行や連続で更新すると版管理で衝突する**
（実測で四回起きた）。**統合の後に一台で一度だけ再生成する。**

### 確定した事実（再測定は不要）

| 事実 | 値 |
|---|---|
| 同期処理の実体 | `~/bin/syncthing`。版 `v1.27.10` |
| 設定の場所 | **`~/.local/state/syncthing/`。`--home` で明示する。既定ではない** |
| 識別子の取り方 | `serve --home ... --device-id`。**`device-id` という下位命令は無い** |
| 五台の識別子 | `scripts/sync/device_ids/*.txt` に公開済み |
| 五台の公開鍵 | `scripts/sync/hub_keys/*.pub` に公開済み（中心を除く四台） |
| 中心 | **philip（本ホスト）**。住所 `192.168.196.150`、SSH は `50072` |
| 直接の接続 | **できない。** 外側から中まで届く口は SSH のものだけ |
| よって構成 | **中継が要る。星型。** 各ノードが中心へ SSH し、その中を同期処理が通る |
| 旧構成の中継 | `-L 22001:127.0.0.1:22000`。中心側の `22000` へ転送していた |
| 除外規則の正本 | `.stglobalignore`（版管理にある）。常駐処理が `.stignore` へ反映する |

### 起票者からの申し送り

**推測で手順を書かない。** 起票者は設定の構造も、変更の手段も読んでいない。
**読めない部分は `UNKNOWN` とする。**

| # | 注意 |
|---|---|
| 1 | **判断の前に、いま見ているものが最新かを確かめる** |
| 2 | **無い**ことと**読めない**ことを区別する |
| 3 | **対照は両方向で取る。** 存在しない語が零を返すだけでは足りない。**実在する語で一以上を返すことも確かめる** |
| 4 | **`/proc/*/cmdline` の部分一致は実行基盤の包み込みを拾う。** 引数の要素で照合する |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **無変更は要約値で確かめる。** 表示属性では足りない |
| 7 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 8 | 出力は要約せず `audit.md` へ貼る |

申し送り 3 と 4 は前契約の指摘に対応する。**片方向の対照は「常に零を返す壊れ方」と
区別できない。** 部分一致は自分を包む処理を拾う。

`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 設定の現状と構造を読む

**Files:** Create: `tasks/T-2026-08-24-syncthing-config-survey/audit.md`

- [ ] **Step 1: 設定の在り処と大きさを記録する**

    ls -la ~/.local/state/syncthing/ 2>&1
    for f in ~/.local/state/syncthing/*; do
      test -f "${f}" && echo "$(sha256sum "${f}") $(stat -c '%s %a' "${f}")"
    done

**要約値と権限を控える。** 本契約の終わりに同じであることを確かめる。

- [ ] **Step 2: 設定の構造を読む**

**秘匿の値を出さない。** 鍵や証明の中身は記録しない。
**要素の名前と、相手や共有フォルダの定義がどう表されているかを記録する。**

    ls ~/.local/state/syncthing/
    for f in ~/.local/state/syncthing/*.xml; do
      echo "=== ${f}"; grep -c '' "${f}"
      grep -o "<[a-zA-Z][a-zA-Z0-9]*" "${f}" | sort | uniq -c | sort -rn | head -20
    done

**要素名の一覧と出現数を記録する。** これで構造が分かる。

**相手と共有フォルダの定義を、値を伏せて記録する。**

    grep -c "device id=" ~/.local/state/syncthing/config.xml 2>&1
    grep -c "folder id=" ~/.local/state/syncthing/config.xml 2>&1
    grep -o 'folder id="[^"]*"' ~/.local/state/syncthing/config.xml 2>&1
    grep -o 'path="[^"]*"' ~/.local/state/syncthing/config.xml 2>&1

**ファイル名が `config.xml` でなければ、実在する名前に読み替える。**
**自分自身の登録が一件あるはずである。** それ以外があれば記録する。

- [ ] **Step 3: 待ち受けと外向きの設定を読む**

    grep -n -E "listenAddress|globalAnnounceEnabled|relaysEnabled|localAnnounceEnabled" \
      ~/.local/state/syncthing/config.xml 2>&1

**旧構成では外部への告知も中継も無効だった。** 新しい設定の既定値を記録する。
**中継を通す構成では、待ち受けの住所が意味を持つ。**

| # | 完了判定 |
|---|---|
| 1 | 設定の在り処と要約値と権限を記録した |
| 2 | 要素の名前と出現数を記録した（秘匿の値は含めない） |
| 3 | 相手と共有フォルダの定義の件数と識別子を記録した |
| 4 | 待ち受けと外向きの設定の既定値を記録した |

---

## Task 2 (Phase A): 設定を変える手段を確かめる

**Files:** Modify: `tasks/T-2026-08-24-syncthing-config-survey/audit.md`

**変更してはならない。** 何ができるかを読むだけである。

- [ ] **Step 1: 下位命令の一覧を読む**

    ~/bin/syncthing --help 2>&1 | head -40
    ~/bin/syncthing cli --help 2>&1 | head -40

**`cli` が在るか。** 在れば、その下に何が並ぶかを記録する。

- [ ] **Step 2: 常駐なしで使えるかを確かめる**

**多くの実装で、命令列は動いている本体へ問い合わせる。** 本体が止まっていれば失敗する。

    ~/bin/syncthing cli --home ~/.local/state/syncthing config devices list 2>&1 | head -20
    echo "exit=$?"

**失敗しても異常ではない。** どう失敗するかを記録する。
**「本体へ繋がらない」と言うなら、常駐が要るということである。**

**成功した場合、それは設定ファイルを直接読んでいる可能性がある。** どちらかを判定する。

- [ ] **Step 3: 設定ファイルを直接編集する道があるかを読む**

    ~/bin/syncthing generate --help 2>&1 | head -20

**設定を作る命令に、相手や共有フォルダを足す機能があるかを確かめる。**

- [ ] **Step 4: 手段を三つに分けて評価する**

`audit.md` に表を作る。**それぞれの可否と、要る前提を書く。**

| 手段 | 使えるか | 前提 | 危険 |
|---|---|---|---|
| 命令列（常駐が要る） | | | |
| 設定ファイルの直接編集 | | | |
| 画面（`8384`）から操作 | | | |

**画面は中継が無いと外から届かない。** 局所からなら使えるが、
**本契約では待ち受けを立てない**（禁止 2）。**読めた範囲で評価する。**

| # | 完了判定 |
|---|---|
| 5 | 下位命令の一覧を記録した（`cli` の有無） |
| 6 | 常駐なしで設定を読めるかを実測した（成否と失敗の様子） |
| 7 | 設定を作る命令の機能を記録した |
| 8 | 手段を三つに分けて可否と前提を評価した |

---

## Task 3 (Phase B): 共有フォルダをどう定義し直すかを決める

**Files:** Modify: `tasks/T-2026-08-24-syncthing-config-survey/audit.md`

**旧構成の定義は失われている。** 何を共有すべきかを、版管理の記録から復元する。

- [ ] **Step 1: 旧構成の記録を探す**

    grep -rn "claude-sync\|folder id\|sendreceive\|stignore" \
      docs/ context/ tasks/ README.md 2>/dev/null | grep -v "\.venv" | head -30

**旧構成では二つの共有フォルダがあった**という記録がある。
**それぞれの識別子、位置、共有相手、除外規則を、書かれている範囲で復元する。**

**見つからないものは `UNKNOWN` とする。推測で埋めない。**

- [ ] **Step 2: 除外規則の正本を読む**

    ls -la .stglobalignore 2>&1
    grep -c '' .stglobalignore 2>&1
    head -30 .stglobalignore 2>&1

**常駐処理がこれを `.stignore` へ反映する。** どこへ置くかを実装から確かめる。

    grep -n "stignore\|stglobalignore" ~/bin/keeper.sh

- [ ] **Step 3: 共有すべきものを決める**

`audit.md` に表を作る。**判断の材料を書き、決めきれないものは `UNKNOWN` とする。**

| 候補 | 位置 | 共有する理由 | 大きさ | 判断 |
|---|---|---|---|---|
| 設定の共有領域 | `~/claude-sync/` | | | |
| 版管理の作業場所 | repo | **版管理で配れる。二重に配る必要があるか** | | |

**repo を同期処理でも配ると、版管理と二重になる。** 旧構成がそうしていたなら、
**なぜそうしていたかを記録から探す。** 見つからなければ `UNKNOWN` とする。

- [ ] **Step 4: 現在の中身を測る**

    du -sh ~/claude-sync/ 2>&1
    ls -la ~/claude-sync/ 2>&1 | head -10
    find ~/claude-sync/ -type f 2>/dev/null | grep -c ''

**保守で失われ、常駐処理が作り直した。** ほぼ空のはずである。
**中身が無いものを同期しても意味がない**ため、**何を入れるべきかを次の判断に回す。**

| # | 完了判定 |
|---|---|
| 9 | 旧構成の共有フォルダの定義を、版管理の記録から復元できた範囲で記録した |
| 10 | 除外規則の正本と、その反映先を実装から確かめた |
| 11 | 共有すべきものを表にした（決めきれないものは UNKNOWN） |
| 12 | 現在の中身の大きさと件数を測った |

---

## Task 4 (Phase B): 登録と起動の順序を決める

**Files:** Modify: `tasks/T-2026-08-24-syncthing-config-survey/audit.md`,
Create: `tasks/T-2026-08-24-syncthing-config-survey/handoff.md`

**次の実装契約はこの手順書に従う。** ここで決まらなかったことは次でも決まらない。

- [ ] **Step 1: 中継と同期処理の関係を実装から読む**

    grep -n -E "tunnel_to|22001|22000|50072" ~/bin/keeper.sh

**中継は局所の `22001` を中心の `22000` へ繋ぐ。** ノード側の同期処理は
**`127.0.0.1:22001` を相手の住所として設定する**ことになるはずである。
**実装から読み取れる範囲で確かめ、読み取れなければ `UNKNOWN` とする。**

- [ ] **Step 2: 順序を決める**

**次を判定し、根拠を書く。**

| 問い | 判定 |
|---|---|
| 中心と一般ノード、どちらの設定を先に入れるか | |
| 中継を張るのは設定の前か後か | |
| 同期処理を常駐させるのは全台同時か、一台ずつか | |
| 一台目で確かめてから次へ進むべきか | |

**「全台同時に動かして失敗すると、遠隔から直せない」**ことを前提に判断する。

- [ ] **Step 3: 手順書を書く**

`handoff.md` に、**中心用**と**一般ノード用**の手順を書く。各手順は次を含む。

| 項目 | 内容 |
|---|---|
| 事前の記録 | 何を測ってから始めるか（要約値を含む） |
| 控え | 設定をどこへ退避するか |
| 変更 | 何をどう変えるか（Task 2 で選んだ手段で） |
| 中継 | 目印を何と書き、いつ置くか |
| 起動 | どう常駐させるか |
| 確認 | 何をもって成功とするか |
| 戻し方 | 失敗したとき何を実行するか |

**実際には実行しない。手順を書くだけである。**

- [ ] **Step 4: 疎通の確認方法と失敗の様式を書く**

**何をもって「動いた」とするか**を、示すことと示さないことに分けて書く。

| 確認 | 示すこと | 示さないこと |
|---|---|---|

**最も強い確認は「ファイルが実際に届くこと」である。** その測り方も書く。

**失敗の様式も列挙する。**

| 失敗 | 症状 | 検出方法 | 戻し方 |
|---|---|---|---|

**「五台とも止まって遠隔から直せない」状態をどう避けるか**を必ず含める。

| # | 完了判定 |
|---|---|
| 13 | 中継と同期処理の関係を実装から読んだ（読めない部分は UNKNOWN） |
| 14 | 順序を判定し、根拠を書いた |
| 15 | 中心用と一般ノード用の手順を書き出した（実行していない） |
| 16 | 疎通の確認方法を、示すことと示さないことに分けて書いた |
| 17 | 失敗の様式と戻し方を列挙した |

---

## Task 5 (Phase C): 無変更を確かめ、報告する

**Files:** Create: `tasks/T-2026-08-24-syncthing-config-survey/RESULT.md`,
`tasks/T-2026-08-24-syncthing-config-survey/result.yaml`,
`tasks/inbox.d/T-2026-08-24-syncthing-config-survey.md`

- [ ] **Step 1: 完了判定 17 項目を表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

- [ ] **Step 2: 開始時と同一であることを要約値で確かめる**

    for f in ~/.local/state/syncthing/*; do
      test -f "${f}" && echo "$(sha256sum "${f}") $(stat -c '%s %a' "${f}")"
    done
    ls -a ~/ | grep -c '^\.tunnel_to_'

**Task 1 Step 1 と一致すること。** 目印が零件であること。
**一致しなければ停止して報告する。**

- [ ] **Step 3: 稼働しているものを数える**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    def count(word, exact=False):
        n = 0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: raw = open("/proc/%s/cmdline" % d, "rb").read()
            except OSError: continue
            args = raw.decode("utf-8", "replace").split("\x00")
            hit = any(a == word for a in args) if exact else any(word in a for a in args)
            if hit: n += 1
        return n
    for w in ("syncthing", "keeper.sh", "ssh"):
        print("%s(partial)=%d" % (w, count(w)))
    print("zzz_none=%d" % count("zzz_no_such_process"))
    print("python(exact_arg)=%d" % count("python", exact=True))
    PY

**同期処理が零件であること**（禁止 2）。**常駐処理は一件のはず。**
**存在しない語が零、実在する語が一以上**の両方向で対照を取っている。

- [ ] **Step 4: 検証を通す**

    source .venv/bin/activate && source scripts/load_env.sh \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-validate TASK=T-2026-08-24-syncthing-config-survey; echo "validate_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-preflight TASK=T-2026-08-24-syncthing-config-survey; echo "preflight_exit=$?"

    source .venv/bin/activate && make forbidden-check; echo "forbidden_exit=$?"

**生成物の検査が差分を報告しても再生成しない**（禁止 7）。**記録するだけでよい。**

- [ ] **Step 5: 変更範囲を確かめ、送出する**

    git --no-pager status --porcelain > /tmp/scs_wt.txt
    grep -c '' /tmp/scs_wt.txt; cat /tmp/scs_wt.txt

**開始時の未追跡がすべて残っていること。**
**変更が契約のディレクトリと受け皿に限られること。**

    git add tasks/T-2026-08-24-syncthing-config-survey/ \
            tasks/inbox.d/T-2026-08-24-syncthing-config-survey.md
    git commit -m "docs(sync): survey syncthing config structure and decide setup order"
    git --no-pager log -1 --format='%h %s'
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

- [ ] **Step 6: 報告を台帳へ返す**

**合言葉が戻ったため、通常の経路が使える。**

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-report TASK=T-2026-08-24-syncthing-config-survey; echo "report_exit=$?"

**これが台帳への返送の実証になる。** 失敗した場合、**それ自体が測定結果である。記録する。**

| # | 完了判定 |
|---|---|
| 18 | 17 項目すべてに実測値または UNKNOWN がある |
| 19 | 設定が開始時と要約値で一致し、目印が零件 |
| 20 | 同期処理が零件（両方向の対照つき） |
| 21 | 変更が契約の範囲に限られ、分岐が送出され PR が存在する |
| 22 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **設定が変わってしまった** | **停止して報告。** 読み取りのみの契約である。元に戻そうとしない |
| **同期処理が常駐してしまった** | **記録して報告。** 止めるかは次の判断 |
| 設定のファイル名が想定と違う | **実在する名前に読み替えて記録する** |
| 命令列が常駐を要求する | **記録する。** 次の契約で起動の順序に影響する |
| 旧構成の共有フォルダの定義が見つからない | **`UNKNOWN` とする。** 新規に決めることを次の判断に回す |
| 共有すべきものを決めきれない | **候補と材料を書いて `UNKNOWN`。** 判断はユーザーが行う |
| 生成物の検査が差分を報告した | **再生成しない。記録するだけ**（禁止 7） |
| 台帳への返送が失敗した | **記録して報告する。** 経路の問題を切り分ける |
| 未追跡が減った | **停止して報告。** 版管理外の成果物を失っている |

**言い訳をしない。事実と、測れなかったことを書く。**
