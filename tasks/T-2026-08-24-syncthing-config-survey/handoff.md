# handoff — 同期処理の登録と起動の手順（次の実装契約向け）

**この文書は実行していない。手順を書いただけである。**
根拠はすべて `audit.md` の実測にある。**推測で埋めた箇所は `UNKNOWN` と明記した。**

## 0. この構成で最初に理解すべき一点

`keeper.sh:41-43` は次の条件だけで同期処理を起動する。

    if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
      nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
    fi

**設定の中身も、中継の有無も、目印の有無も見ない。** ゆえに:

| 帰結 | 内容 |
|---|---|
| 起動の引き金 | **`~/bin/syncthing` の実行権**。戻した瞬間から最大 30 分で、そのときの設定のまま起動する |
| 順序が固定される | **設定を確定させてから実行権を戻す。** 逆順にできない |
| 安全装置 | **`chmod 644 ~/bin/syncthing`。** これ一つで全台の同期を止められる（既に動いている処理は別に終わらせる） |
| 現状 | philip は **644**（前契約 `T-2026-08-24-philip-keeper-autosync` の回避策）。**5 台とも同じ状態にしてから作業を始めること** |

## 1. 全台共通の前提値（`audit.md` の実測）

| 項目 | 値 |
|---|---|
| 実体 | `~/bin/syncthing` v1.27.10 |
| 設定の場所 | `~/.local/state/syncthing/`（**既定の場所である**。`--home` の明示は保険） |
| 設定ファイル | `config.xml` 平文 XML `<configuration version="37">` |
| 変更手段 | **設定ファイルの直接編集**（常駐が要らない唯一の手段） |
| 識別子 | `scripts/sync/device_ids/{andrew,bengio,ilya,lecun,philip}.txt`（版管理に公開済み） |
| 除外規則 | 正本 `origin/phase0:.stglobalignore` → 常駐処理が `$M2DIR/.stignore` へ反映（`keeper.sh:48-49`） |
| 中心 | philip。中継は `-L 22001:127.0.0.1:22000`、SSH は外から `50072`（容器の中では `22`） |

**旧構成から引き写してはならないもの**（`audit.md`「旧構成と現構成の差」）:
旧 11 台の識別子（**すべて作り直されている**）、登録名（現状は全台 `aolab` になりうる）、
静的な住所（philip の容器内住所は作り直すたびに変わる）。

## 2. 中心（philip）用の手順

### 2.1 事前の記録

    # 設定の要約値（変更前）
    for f in ~/.local/state/syncthing/*; do
      test -f "$f" && echo "$(sha256sum "$f") $(stat -c '%s %a' "$f")"
    done
    # 起動の引き金の状態
    ls -la ~/bin/syncthing; sha256sum ~/bin/syncthing
    # 常駐処理と稼働の有無
    pgrep -x syncthing >/dev/null && echo "syncthing=動作中" || echo "syncthing=停止"
    ls -a ~/ | grep -c '^\.tunnel_to_'      # 中心は 0 のはず
    # 除外規則が反映済みか
    sha256sum .stglobalignore .stignore

**基準**: 同期処理が停止、実行権が 644、目印 0 件、`.stignore` が正本と一致。
**一つでも違えば、その理由を確かめるまで先へ進まない。**

### 2.2 控え

    cp -a ~/.local/state/syncthing ~/.local/state/syncthing.bak.$(date +%Y%m%d-%H%M%S)

**repo の外へ置く**（repo 内に置くと同期対象・版管理の両方を汚す）。
要約値を控えと突き合わせて、控えが完全であることを確かめてから編集する。

### 2.3 変更（設定ファイルの直接編集）

**同期処理が停止していることを確認してから編集する**（動作中の書き換えは上書きされる）。
権限 600 を保つ。編集後に XML の妥当性を確かめる（`python -c "import xml.etree.ElementTree as E; E.parse(...)"`）。

| # | 変更 | 現状 | 変更後 |
|---|---|---|---|
| 1 | 自分の登録名 | `name="aolab"` | `name="philip"`（**philip と ilya が同じ OS ホスト名のため必須**） |
| 2 | 相手の登録 | 自分 1 件のみ | **andrew / bengio / ilya / lecun の 4 件を追加。**住所は `dynamic`（中心からノードへは掛けられない。ノードが中継越しに掛けてくる） |
| 3 | 共有フォルダ `m2` | 無い | `id="m2" path="/home/ubuntu/slocal2/m2" type="sendreceive"`、共有相手は自分＋4 台 |
| 4 | 共有フォルダ `claude-sync` | 無い | `id="claude-sync" path="/home/ubuntu/claude-sync" type="sendreceive"`、共有相手は自分＋4 台 |
| 5 | 自動生成の `default` | `path="/home/ubuntu/Sync"`（**実体は存在しない**） | **削除する** |
| 6 | 外部告知 | `globalAnnounceEnabled=true` | **`false`**（旧構成に合わせる） |
| 7 | 公開中継 | `relaysEnabled=true` | **`false`**（同上） |
| 8 | 局所告知 | `localAnnounceEnabled=true` | `true` のまま（旧構成も true） |
| 9 | 待ち受け | `listenAddress=default` | そのまま。`0.0.0.0:22000` を含み、中継の終端要求を満たす |
| 10 | 画面 | `127.0.0.1:8384`、`tls=false`、利用者名なし | **そのまま触らない。** 外から届かない。届かせるには別の中継が要る |

🔴 **6 と 7 を落とし忘れたまま起動すると、外部の探索網と公開中継へ出る。**
これは旧構成が明示的に無効化していた設定である（`T-2026-08-12-sync-audit-bengio/audit.md:225,227`）。

**共有フォルダの型は要判断（`UNKNOWN`）。** `~/claude-sync/` は philip 上で **8.0K / 1 ファイル**しか無い。
他 4 台の中身を測っていないため（禁止 5）、**空の側が `sendreceive` で参加すると中身を消しうる。**
中身を持つ台が判明するまで、`claude-sync` は**中身を持つ台を `sendonly`、他を `receiveonly`** で始めるのが安全である。

### 2.4 中継

**中心は目印を置かない。** `keeper.sh:31` の注記どおり、目印が無い中心自身は中継を張らない。
中心がやることは「ノードからの SSH（外から `50072`）を受けられる状態を保つ」だけである。
**SSH の設定には触れない**（触れて壊すと遠隔復旧経路そのものを失う）。

### 2.5 起動

    chmod 755 ~/bin/syncthing        # ← これが起動の引き金

常駐処理が**次の周（最大 1800 秒）で自動的に起動する。** 手で起動しない
（二重起動を避ける。常駐処理は `pgrep -x syncthing` で判定している）。

### 2.6 確認

    # 待ち受けが立ったか
    .venv/bin/python -c "print([int(l.split()[1].split(':')[1],16) for l in open('/proc/net/tcp').read().splitlines()[1:] if l.split()[3]=='0A'])"
    # 常駐が要る手段が使えるようになったか（設定を読むだけ）
    ~/bin/syncthing cli --home ~/.local/state/syncthing config devices list
    ~/bin/syncthing cli --home ~/.local/state/syncthing config folders list
    # 記録
    tail -20 ~/.syncthing.log

**成功の基準**: `22000` と `8384` が待ち受け中、`cli` が exit 0 で 5 件の相手と 2 件の共有フォルダを返す。

### 2.7 戻し方

    chmod 644 ~/bin/syncthing                       # 引き金を外す（再起動を止める）
    pkill -x syncthing                              # 動いている処理を終わらせる
    cp -a ~/.local/state/syncthing.bak.<刻>/. ~/.local/state/syncthing/   # 設定を戻す
    for f in ~/.local/state/syncthing/*; do test -f "$f" && sha256sum "$f"; done  # 2.1 と一致するか

**常駐処理（keeper）は止めない。** 引き金を外せば同期処理は再起動されない。

## 3. 一般ノード（andrew / bengio / ilya / lecun）用の手順

**中心が 2.6 まで通ってから着手する。一台ずつ。**

### 3.1 事前の記録

2.1 と同じものに加えて:

    ls -la ~/bin/syncthing                    # 実体があるか・権限は何か
    cat ~/.servername                         # 論理名（無ければ repo 直下の .servername）
    ls -a ~/ | grep -c '^\.tunnel_to_'        # 開始時は 0 のはず
    grep -c '' ~/.tunnel.log 2>/dev/null      # 過去の中継の記録

### 3.2 控え

2.2 と同じ。

### 3.3 変更

| # | 変更 | 変更後 |
|---|---|---|
| 1 | 自分の登録名 | **論理名**（`.servername` の値）。`aolab` のままにしない |
| 2 | 中心の登録 | philip の識別子（`scripts/sync/device_ids/philip.txt`）を追加し、**住所を `tcp://127.0.0.1:22001`** にする（旧構成と同じ形。`T-2026-08-12-sync-audit-bengio/audit.md:212`） |
| 3 | 他ノードの登録 | **最初は登録しない。** 星型のためノード間に経路が無く、中心を介して配られる。切り分けを単純に保つ |
| 4 | 共有フォルダ `m2` | `path="/home/ubuntu/slocal2/m2"`、共有相手は自分＋philip |
| 5 | 共有フォルダ `claude-sync` | `path="/home/ubuntu/claude-sync"`、共有相手は自分＋philip。**型は 2.3 の判断に従う** |
| 6 | `default` | 削除 |
| 7-9 | 告知・中継・待ち受け | 中心と同じ（`global=false` `relays=false` `local=true` `listen=default`） |

### 3.4 中継（**設定の後、起動の前**）

    printf '%s\n%s\n' "<中心宛の秘密鍵のパス>" "<philip へ届く住所>" > ~/.tunnel_to_philip

- 1 行目 = 秘密鍵のパス、2 行目 = 中心の住所（`keeper.sh:9-22`）。
- 常駐処理が**次の周（最大 1800 秒）で** `ssh -N -L 22001:127.0.0.1:22000 -p 50072` を張る。
- **2 行目に何を書くかは `UNKNOWN`。** 契約は `192.168.196.150` とするが、philip は Docker の中にあり、
  局所から観測できるのは容器内の `172.17.0.13` のみで、**外からの到達性を本契約では検証できない**（禁止 5）。
  **次の契約は、目印を置く前にノードから `ssh -p 50072 <住所>` の到達を実測すること。**

確認:

    pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null && echo "中継=あり" || echo "中継=なし"
    tail -20 ~/.tunnel.log

### 3.5 起動

**中継が張れたことを確かめてから** `chmod 755 ~/bin/syncthing`。
中継が無い状態で起動すると、相手の住所 `127.0.0.1:22001` に誰も居ないため接続に失敗し続ける。

### 3.6 確認 / 3.7 戻し方

確認は §4。戻し方は 2.7 に加えて `rm -f ~/.tunnel_to_philip` と
`pkill -f 'ssh.*-L 22001:127.0.0.1:22000'`（**目印を消さないと常駐処理が張り直す**）。

## 4. 疎通の確認方法（示すことと示さないこと）

| 確認 | 示すこと | 示さないこと |
|---|---|---|
| `ssh -p 50072 <住所>` が通る | SSH の経路が生きている | 同期処理が動くこと。中継が張れること |
| `pgrep -f 'ssh.*-L 22001'` が 1 件 | 中継の処理が存在する | **向こう側に何かが待っていること。** `ExitOnForwardFailure` は局所の束縛失敗しか見ない |
| ノードで `22001` が待ち受け中 | 中継が局所の口を開いた | 中心の `22000` に同期処理が居ること |
| 中心で `22000` が待ち受け中 | 同期処理が起動し待っている | 相手の登録が正しいこと |
| `cli config devices list` が 5 件返す | **設定が読める**（常駐が動いている） | 実際に繋がっていること。設定は願望でも書ける |
| `cli show connections` が相手を Connected と言う | 識別子と証明の握手が成立した | **共有フォルダが共有されていること。**除外規則が正しいこと |
| 共有フォルダが `Up to Date` | 索引が一致した | **中身が実際に届いたこと。**除外された結果として一致している場合がある |
| **小さなファイルを片方で作り、他方に同じ要約値で現れる** | **経路・登録・共有・除外規則がすべて成立していること** | 大きなファイルや帯域の問題。初回全量（概算 19G）の所要時間 |

**最も強い確認は最後の行である。測り方:**

    # 中心で（repo の外を使う。experiments/** を触らずに済む）
    echo "probe $(date -Is)" > ~/claude-sync/_probe_philip.txt
    sha256sum ~/claude-sync/_probe_philip.txt
    # ノードで（数分待ってから）
    sha256sum ~/claude-sync/_probe_philip.txt      # 中心と同じ値になること
    # 逆向きも同じ手順で測る。**片方向だけでは sendonly/receiveonly の取り違えを見逃す**

`~/claude-sync/` を使う理由は、`m2` 側で試すと `.stignore` の
「先にマッチした行が勝つ」規則の解釈まで同時に検証することになり、**失敗したとき原因を切り分けられない**ため。
`m2` 側は `!experiments/**/logs` に当たる位置（例 `experiments/_sync_probe/logs/probe.txt`）で**別に**測る。
**`experiments/baselines/_*` と `experiments/phase0/_*` は除外されている**ので、そこでは試さない。

## 5. 失敗の様式

| 失敗 | 症状 | 検出方法 | 戻し方 |
|---|---|---|---|
| 中継が張れない（鍵・住所・口の誤り） | ノードの同期処理が中心へ繋がらない | `~/.tunnel.log` にエラー。`pgrep -f 'ssh.*-L 22001'` が 0 件 | `rm -f ~/.tunnel_to_philip`（**消さないと常駐処理が張り直す**）＋ `pkill -f 'ssh.*-L 22001'` |
| 識別子の書き間違い | 相手が永久に Disconnected | `cli show connections`。`scripts/sync/device_ids/*.txt` と設定内の値を突き合わせる | 控えから設定を戻す |
| **XML の構文を壊した** | 同期処理が起動しない。**常駐処理が 30 分ごとに起動を試み続ける** | `~/.syncthing.log` に構文の誤り。`22000` が待ち受けにならない | **`chmod 644 ~/bin/syncthing`** で試行を止め、控えから戻す |
| 除外規則が効かず全量が流れる | 容量と帯域が急増。`.git` や `.venv` が相手に現れる | 相手側で `find` の件数。`sha256sum .stignore` が正本と不一致 | 実行権を外す＋処理を終わらせる。`.stignore` は `keeper` が正本から作り直す |
| 外部告知・公開中継を落とし忘れ | 登録していない相手からの接続要求。外部の中継を経由した通信 | `cli config options dump-json` で `globalAnnounceEnabled` `relaysEnabled` | 実行権を外す→設定を直す→戻す |
| `default` を消し忘れ | `/home/ubuntu/Sync` が作られ、意味の無い共有が増える | `cli config folders list` に `default` が残る | 設定から削除 |
| **空の側が中身を配る**（`claude-sync`） | 中身を持つ台のファイルが消える | 事前に全台の `find ~/claude-sync -type f \| grep -c ''` を測っておく | **版管理外のため復旧できない。**先に型で防ぐ（2.3 の `UNKNOWN`） |
| 二重起動 | 索引が壊れる | `pgrep -x syncthing` が 2 件以上 | 手で起動しない。常駐処理に任せる |

### 「五台とも止まって遠隔から直せない」をどう避けるか

1. **一台ずつ進める。** 中心＋ノード 1 台で §4 の最後の行（ファイルが実際に届く）まで通してから 2 台目へ。
2. **同期処理と SSH を独立に保つ。** 遠隔復旧の経路は SSH（外 `50072` → 中 `22`）だけである。
   **philip の SSH 設定には一切触れない。** ここが死ぬと全台が詰む。
3. **単一の安全装置を保つ。** `chmod 644 ~/bin/syncthing` だけで、その台の同期を止められる。
   **作業前に 5 台とも 644 であることを確かめる。**
4. **控えを取ってから編集する。** 控えは repo の外（同期対象にも版管理にも入らない場所）。
5. **中心を最後に壊さない。** 中心の設定変更は 1 回で確定させ、ノードの試行錯誤で中心を触り直さない。
6. **止まっていることが記録に出るようにする。** 常駐処理の記録（`~/claude-sync/sync-alerts.log`）は
   同期処理が死んでいても git の層で配られる。**同期処理の死活を同期処理で運ばない。**
