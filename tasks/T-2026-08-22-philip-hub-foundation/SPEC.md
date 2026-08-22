# 中心の基盤を作り、識別子を公開する（philip）

**task_id:** `T-2026-08-22-philip-hub-foundation`  **kind:** `impl`
**depends_on:** なし
**実行ホスト:** `philip`（中心）  **repo:** `~/slocal2/m2`

## Goal

**保守作業で全サーバーが初期化された。** 家の直下の設定、常駐処理、同期処理、鍵、
識別子がすべて失われた。**復旧ではなく新規構築である。**

実測で確定したこと。

| 事実 | 実測 |
|---|---|
| 同期処理の識別子 | **全台で失われた。** 全部発行し直す |
| 直接接続 | **できない。** 待ち受けを立てて外から叩いても中まで届かない |
| 外側の転送 | **`50072` から内側の `22` だけ。** 他の口は転送されていない |
| よって構成 | **中継が要る。星型。** 単純化の余地はない |
| 同期処理の入手 | **可能**（配布物を取得・展開できることを確認済み） |
| 到達性 | philip / lecun / bengio / andrew / ilya は相互に `50072` が開いている |

**本契約は中心の基盤だけを作る。** 他ホストは触らない。

### この契約が置かれた状況

**契約システムの一部が動かない。** 秘匿情報の合言葉が失われ、
`scripts/load_env.sh` が失敗する。よって次が使えない。

| 使えないもの | 代替 |
|---|---|
| `make task-start`（台帳から取得） | **手で分岐を切り、契約を配置する** |
| `make task-report`（台帳へ返送） | **`RESULT.md` を commit して push する** |
| `source scripts/load_env.sh` | **`source .venv/bin/activate` だけを使う** |

**秘匿の検査も送信経路の中にあったため働かない。** 本契約では
**送信前に自分で検査すること**を求める。

## 0. 前提と禁止事項

**取り込みは手で行う。** 次のとおり。

    cd ~/slocal2/m2
    git --no-pager status -sb
    git fetch origin
    git checkout -b feat/philip-hub-foundation origin/phase0
    mkdir -p tasks/T-2026-08-22-philip-hub-foundation

**その後、配られた本文から `spec.yaml` と `SPEC.md` を上のディレクトリへ置く。**

**現在の分岐は `exp/philip-wip-20260703` で、`origin/phase0` より三週間古い。**
**未追跡が七件ある。** これらは版管理外の成果物であり、**一切触らない。**
`git checkout -b` は未追跡を保持したまま分岐を切る。**消えないことを確認してから進む。**

| # | 禁止 |
|---|---|
| 1 | **未追跡の七件を削除・移動・commit する** |
| 2 | `experiments/**` `transfer/**` `data/**` を変更・削除する |
| 3 | **他ホストへ接続する。他ホストの状態を変更する** |
| 4 | **鍵を他ホストへ配る。他ホストの鍵を受け入れ一覧へ入れる**（次の契約で行う） |
| 5 | **中継を張る。目印を作る**（中心は目印を持たない） |
| 6 | **常駐処理を起動する**（次の契約で行う） |
| 7 | **同期処理の設定で他ホストを登録する**（識別子が揃ってから） |
| 8 | 秘匿の値を出力・記録する |
| 9 | 装置を使う |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `runindex/**` `context/auto/**` を手で編集する |
| 12 | 学習・評価コードを変更する |

**禁止 5 の理由。** 中心は入られる側であり、自分へ中継を張らない。
正本は**目印が無いノードでは中継を起こさない**形になっている。

**禁止 6 と 7 の理由。** 他台の識別子が揃っていない段階で動かすと、
**定まらない状態で同期が走る。** 起動は全台の準備が済んでから。

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | **無い**ことと**読めない**ことを区別する |
| 2 | 先頭がドットのものを落とさない |
| 3 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 4 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 5 | **取得したものは要約値で照合する。** 大きさだけでは足りない |
| 6 | 対照は両方向で取る。期待値を実測前に一点へ固定しない |
| 7 | `成功 && echo OK || echo NG` は表示側の失敗も NG にする。判定は別命令で |
| 8 | 出力は要約せず `audit.md` へ貼る |

**`load_env.sh` は失敗する。** `make` を含む命令には
`source .venv/bin/activate` だけを同じ命令に含める。

`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 開始状態を記録し、repo を更新する

**Files:** Create: `tasks/T-2026-08-22-philip-hub-foundation/audit.md`

- [ ] **Step 1: 開始状態を記録する**

    ls -la ~/ 2>&1
    echo "home_entries=$(ls -a ~/ | grep -c -v '^\.\{1,2\}$')"
    ls -la ~/.ssh/ 2>&1
    ssh-keygen -lf ~/.ssh/authorized_keys 2>&1
    cat ~/.zshenv 2>&1
    git --no-pager status --porcelain > /tmp/phf_wt0.txt
    grep -c '' /tmp/phf_wt0.txt; cat /tmp/phf_wt0.txt

**未追跡の件数を控える。** 本契約の終わりに同じ数であることを確かめる。

- [ ] **Step 2: 分岐を切ったあと、未追跡が保たれていることを確かめる**

    git branch --show-current
    git --no-pager status --porcelain > /tmp/phf_wt1.txt
    grep -c '' /tmp/phf_wt1.txt

**Step 1 の件数と一致すること**（契約のディレクトリが増える分を除く）。
**減っていれば何かを失っている。停止して報告する。**

- [ ] **Step 3: 実行環境を作る**

    ls -la .venv 2>&1 || echo "venv なし"
    grep -n -A 15 "推奨セットアップ" README.md

**README の手順に従う。** 起票者は手順を把握していないため指定しない。
**素の `pip` が別の環境へ入る事故が記録されている**ため、README のとおりにする。

    source .venv/bin/activate && python -V && which python

**`load_env.sh` は通さない。** 合言葉が無いため失敗する。

| # | 完了判定 |
|---|---|
| 1 | 開始状態を記録した（家の直下、鍵、受け入れ、未追跡の件数） |
| 2 | 分岐を切っても未追跡が失われていない（件数の一致） |
| 3 | 実行環境が作られ、経路が `.venv` を指している |

---

## Task 2 (Phase A): 論理名を設定する

**Files:** Modify: `~/.zshenv`

**このホストの `hostname` は `aolab` を返す。** ilya も同じ値を返すため、
**論理名を明示しないと区別できない。**

- [ ] **Step 1: 現在の状態を確かめる**

    grep -n "SERVERNAME" ~/.zshenv ~/.profile 2>&1 || echo "該当なし"
    echo "SERVERNAME=${SERVERNAME:-unset}"
    hostname

- [ ] **Step 2: 版管理の道具を読む**

    cat scripts/sync/setup_host_servername.sh

**中身を読み、何をするかを記録してから使う。** 実行する場合は、
**変更前後で `~/.zshenv` の差分を記録する。**

道具を使わず手で追記してもよい。**その場合も追記内容を記録する。**

**`.zshenv` は zsh の全形態で読まれる。** `.profile` は bash のログイン時のみである。
**両方に置くのが規約である。**

- [ ] **Step 3: 新しいシェルで解決されることを確かめる**

    zsh -c 'echo "SERVERNAME=${SERVERNAME:-unset}"'
    bash -lc 'echo "SERVERNAME=${SERVERNAME:-unset}"' 2>&1

**両方で `philip` が出ること。** 出なければ置き場所が誤っている。

| # | 完了判定 |
|---|---|
| 4 | 論理名の設定前の状態を記録した |
| 5 | 追記内容を記録した（道具を使った場合はその差分） |
| 6 | 新しいシェルで論理名が解決される（zsh と bash の両方） |

---

## Task 3 (Phase B): 同期処理を導入し、識別子を発行する

**Files:** Create: `~/bin/syncthing`,
`scripts/sync/device_ids/philip.txt`

**識別子は鍵から導出される。** 一度発行したら**変えない。**
変えると他台から「別の機械」に見える。

- [ ] **Step 1: 配布物を取得し、照合する**

    mkdir -p ~/bin
    cd /tmp && curl -sSL -o st.tar.gz \
      "https://github.com/syncthing/syncthing/releases/download/v1.27.10/syncthing-linux-amd64-v1.27.10.tar.gz"
    ls -la /tmp/st.tar.gz
    sha256sum /tmp/st.tar.gz
    tar tzf /tmp/st.tar.gz | head -5

**要約値を記録する。** 他台でも同じ値を得るはずであり、**次の契約の照合に使う。**

**版は起票者が指定した値である。** 取得できない場合は、
**取得できた版を記録して続行する。** 全台で同じ版を使うことが重要である。

- [ ] **Step 2: 展開して配置する**

    cd /tmp && tar xzf st.tar.gz
    cp /tmp/syncthing-linux-amd64-v1.27.10/syncthing ~/bin/syncthing
    chmod 755 ~/bin/syncthing
    sha256sum ~/bin/syncthing
    ~/bin/syncthing --version

**展開物と配置物の要約値が一致すること。**

- [ ] **Step 3: 識別子を発行する**

    ~/bin/syncthing generate --home ~/.local/state/syncthing 2>&1 | tail -20

**`generate` は設定と鍵を作るが、常駐しない。** 起動してはならない（禁止 6）。

**すでに設定が在る場合は上書きしない。** その旨を記録して次へ進む。

- [ ] **Step 4: 識別子を読み取る**

    ~/bin/syncthing --home ~/.local/state/syncthing device-id 2>&1

**この値が識別子である。秘匿ではない。** 記録してよい。

**取れない場合は設定の中を探す。** 要素名は実装によるため、
**何を見たかを記録する。**

- [ ] **Step 5: 識別子を版管理へ公開する**

    mkdir -p scripts/sync/device_ids
    ~/bin/syncthing --home ~/.local/state/syncthing device-id > scripts/sync/device_ids/philip.txt
    cat scripts/sync/device_ids/philip.txt
    grep -c '' scripts/sync/device_ids/philip.txt

**一行であること。** 前後の空白や改行の乱れがあれば整える。

**これを他台が読んで登録する。** 逆に、他台が同じ場所へ置いた識別子を
**次の契約で本ホストが読む。**

- [ ] **Step 6: 待ち受けが立っていないことを確かめる**

    python3 - <<'PY'
    ports=set()
    for f in ("/proc/net/tcp","/proc/net/tcp6"):
        try: ls=open(f).read().splitlines()[1:]
        except OSError: continue
        for ln in ls:
            x=ln.split()
            if len(x)>3 and x[3]=="0A": ports.add(int(x[1].split(":")[1],16))
    print("count=%d"%len(ports))
    for q in (22,22000,22001,8384): print("port_%d=%s"%(q,"LISTEN" if q in ports else "-"))
    PY

**`22000` と `8384` が待ち受けていないこと。** 起動していれば禁止 6 に触れている。
**記録して報告する。**

| # | 完了判定 |
|---|---|
| 7 | 配布物を取得し、要約値を記録した（版も記録） |
| 8 | 配置物と展開物の要約値が一致し、版が表示できる |
| 9 | 識別子を発行した（既存があれば上書きしていない） |
| 10 | 識別子を読み取り、版管理へ一行で公開した |
| 11 | **同期処理が起動していない**（待ち受けが無い） |

---

## Task 4 (Phase C): 記録し、送出する

**Files:** Create: `tasks/T-2026-08-22-philip-hub-foundation/RESULT.md`,
`tasks/T-2026-08-22-philip-hub-foundation/result.yaml`,
`tasks/inbox.d/T-2026-08-22-philip-hub-foundation.md`

- [ ] **Step 1: 完了判定 11 項目を表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

**あわせて、次の契約で使う情報を記す。**

| 項目 | 内容 |
|---|---|
| 同期処理の版と要約値 | 他台が同じものを使うため |
| 識別子 | 版管理の場所 |
| 論理名の設定方法 | 他台で再現するため |
| 実行環境の作り方 | README のどの手順が通ったか |
| つまずいた点 | 他台で同じことが起きうる |

- [ ] **Step 2: 送信前に自分で秘匿を検査する**

**送信経路の検査が働かないため、自分で行う。**

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|token" \
      tasks/T-2026-08-22-philip-hub-foundation/*.md \
      tasks/T-2026-08-22-philip-hub-foundation/*.yaml 2>&1

**判定するのは件数ではなく形である。** 一致を一件ずつ確かめる。

| 判定 | 扱い |
|---|---|
| 鍵の書き出し行、語に区切りと値が続く形 | **削る** |
| 説明文・変数名に語が現れただけ | 差し支えない。その旨を記す |

**陽性対照**: 囮の行を含む一時ファイルに同じ検査をかけ、**一以上を返すこと**を確かめる。
**囮は版管理へ入れない。**

**識別子は秘匿ではない。** 削らない。

- [ ] **Step 3: 検証を通す**

    source .venv/bin/activate \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate \
      && make task-validate TASK=T-2026-08-22-philip-hub-foundation; echo "validate_exit=$?"

    source .venv/bin/activate \
      && make forbidden-check; echo "forbidden_exit=$?"

**`make task-preflight` は資格情報を要する場合がある。** 失敗したら記録して続行する。

- [ ] **Step 4: 生成物を再生成する**

    source .venv/bin/activate && make taskindex && make inbox
    source .venv/bin/activate && make taskindex-check; echo "taskindex_exit=$?"
    source .venv/bin/activate && make inbox-check; echo "inbox_exit=$?"

- [ ] **Step 5: 変更範囲と未追跡を確かめる**

    git --no-pager status --porcelain > /tmp/phf_wt2.txt
    grep -c '' /tmp/phf_wt2.txt; cat /tmp/phf_wt2.txt

**開始時の未追跡七件がすべて残っていること。** 減っていれば失っている。
**変更が契約のディレクトリと識別子と生成物に限られること。**

- [ ] **Step 6: commit し、push する**

    git add tasks/T-2026-08-22-philip-hub-foundation/ \
            tasks/inbox.d/T-2026-08-22-philip-hub-foundation.md \
            scripts/sync/device_ids/philip.txt \
            context/auto/ tasks/inbox.md
    git commit -m "feat(sync): build hub foundation and publish device id on philip"
    git --no-pager log -1 --format='%h %s'
    git push -u origin HEAD
    git --no-pager status -sb

**`git add` は明示したものだけ。** `-A` は使わない（未追跡を巻き込む）。

    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**台帳へは返さない。** 合言葉が無いため送れない。**起票者は版管理から読む。**

| # | 完了判定 |
|---|---|
| 12 | 11 項目すべてに実測値または UNKNOWN がある |
| 13 | 送信前の秘匿検査を自分で行った（陽性対照つき） |
| 14 | **開始時の未追跡七件がすべて残っている** |
| 15 | 変更が契約の範囲に限られる |
| 16 | 分岐が送出され、PR が存在する（番号） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **未追跡が減った** | **停止して報告。** 版管理外の成果物を失っている |
| 実行環境が作れない | **停止して報告。** README の手順と出力を貼る |
| 配布物を取得できない | **停止して報告。** 経路の問題である |
| 指定の版が無い | **取得できた版を記録して続行。** 全台で同じ版にする |
| 同期処理の設定が既に在る | **上書きしない。** 記録して続行 |
| 識別子を読み取れない | 設定の中を探す。**何を見たかを記録する。** 取れなければ停止 |
| **同期処理が起動してしまった** | **記録して報告。** 止めるかは次の判断 |
| 論理名が新しいシェルで解決されない | 置き場所を見直す。**両方の形態で確かめる** |
| 検証が資格情報を要して失敗する | **記録して続行。** 合言葉が無いのは既知である |
| push できない | **記録を repo に残し、状況を報告する** |

**言い訳をしない。事実と、測れなかったことを書く。**
