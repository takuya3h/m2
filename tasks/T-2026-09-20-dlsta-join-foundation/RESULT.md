# RESULT — T-2026-09-20-dlsta-join-foundation

**同期の群れへ加わるための基盤を作り、鍵と識別子を版管理へ公開する**

実行ホスト `dlsta` / repo `~/local/m2` / 分岐 `feat/dlsta-join-foundation` / 2026-09-20（JST）
手続きの証跡は `audit.md`（554 行）。本書は行番号で指す。

## 判定

**verdict: pass**

| Gate | 判定 | 実測したこと |
|---|---|---|
| **G1** | **pass** | `.venv` 不在から作り直し、Python `3.11.16` / torch `2.1.2+cu118` / torchvision `0.16.2+cu118` / mmcv `2.1.0` が他台と一致。CUDA 可（RTX A5000 × 5）。依存 **18/18** 読み込み。論理名が zsh・bash の両形態で `dlsta`（空 `HOME` の陰性対照が `未設定`）。版管理の識別は `~/.gitconfig` に既設定で出所を記録 |
| **G2** | **pass** | 鍵の指紋を記録し、版管理へ置いたものが公開鍵だけであることを三検査＋囮で確認（囮は書き出し 2 件・7 行で検査に掛かった）。配布物・配置物の要約値が中心と一致。識別子を一行で公開。22000／8384 とも待ち受け 0 件で、**22000 番そのものに一時的な待ち受けを立てて 0→1→0** を確認 |

試験は変更前後とも **6 failed / 581 passed / 14 skipped**。失敗 6 件は既存で、
本契約は `src/` `tools/` `tests/` を一切変更していない（audit.md:527-554）。

## 完了判定

| # | 項目 | 実測値 | 証跡 |
|---|---|---|---|
| A | 開始時に何が無いか | `.venv` 不在 / uv `~/.local/bin/uv` / nvcc **12.9** / RTX A5000 × 5 driver 595.84 / `~/bin` 不在 / 空き 758G | :11 |
| B | 他台と同じ版 | Python `3.11.16`・torch `2.1.2+cu118`・torchvision `0.16.2+cu118`・mmcv `2.1.0` | :192 |
| C | 装置が使え mmcv が読める | `cuda.is_available()=True` / device 5 / cuda 上の行列積が完走 / **18 依存すべて OK** | :213, :251 |
| D | 検証に要るもの | `jsonschema 4.26.0` を `.venv` へ明示導入。`make task-validate` が **exit 0** | :235 |
| E | 設定前の状態 | `hostname=4f3861ae8d3b`（容器の識別子）/ `SERVERNAME` 未設定 | :87 |
| F | 追記内容 | `export SERVERNAME=dlsta` を標識付きで `~/.zshenv`:8-10 / `~/.profile`:32-34 / `~/.bashrc`:123-125 | :118 |
| G | 両形態で解決 | zsh 非対話・ログイン、bash ログイン・対話とも `[dlsta]`。`bash -c` 非対話のみ未設定（スクリプトが文書化した既知の限界） | :138 |
| H | 版管理の識別 | `~/.gitconfig`（global）に `takuya3h` / `daky.o7600@gmail.com`。**local は空**。新規設定はしていない | :35, :161 |
| I | 既存の鍵 | `*philip*` 一致 **0 件**（陽性対照 `*github*` → 2 件）。新規に作った | :294 |
| J | 鍵と指紋 | `SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4`。合言葉なし。**秘密鍵の中身は未出力** | :308 |
| K | 権限 | `~/.ssh` = 700 / 秘密鍵 = 600 | :321 |
| L | 公開鍵だけ | 先頭 `ssh-`=1 / 秘密鍵の書き出し=**0 件** / 行数=**1**。囮は 0 / **2 件** / **7** で検査に掛かった | :329 |
| M | 配布物の要約値 | `e8a08fdd…b96c4` 一致。同名の別物 3 件（1709 / 175 / **27045912**）を大きさで特定。陰性対照も合格 | :352 |
| N | 配置物 | 要約値一致 / permission `644` / `[ -x ]` 偽 = **起動の引き金なし** | :376 |
| O | 識別子の発行 | 既存設定 **無し**（上書きしていない）。`generate` `device-id` の実在を `--help` で確認してから使用 | :389 |
| P | 識別子の公開 | `BRPEYOX-MJ7HMGV-RR2XAUW-CVFVSED-DEMAG5M-EMQNVR6-77XWXPL-ZS26PAI`（64 bytes / 1 行 / 63 字。他台と同形） | :418 |
| Q | 起動していない | port 22000=**0 件** / 8384=**0 件**、プロセス `syncthing`/`m2-sync`/`keeper`=**0 件**。対照は三方向 | :434 |
| R | `env-facts.md` の訂正 | 7 箇所（下記） | — |
| S | 報告の構成と分量 | 本書（目安 150 行以内）／証跡は `audit.md` | — |
| T | 三つの規約の適用可否 | 下記 | :470 |
| U | 禁止語の検査 | 下記「送出」 | — |
| V | 秘匿検査 | 下記「送出」 | — |
| W | 変更が契約の範囲に限られる | 下記「送出」 | — |
| X | 台帳へ返した | 下記「送出」 | — |

## 後続で使う値

| 値 | 中身 |
|---|---|
| **鍵の指紋**（中心の受け入れ一覧に入れる） | `SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4` |
| 秘密鍵の場所（**このホストから出さない**） | `~/.ssh/id_ed25519_dlstatophilip`（600） |
| 公開鍵 | `scripts/sync/hub_keys/dlsta.pub`（注釈 `dlstatophilip`） |
| **識別子** | `BRPEYOX-MJ7HMGV-RR2XAUW-CVFVSED-DEMAG5M-EMQNVR6-77XWXPL-ZS26PAI` |
| 識別子の場所 | `scripts/sync/device_ids/dlsta.txt` |
| **同期処理の版** | `v2.1.3 "Hafnium Hornet"` / `e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4` |
| 実行ファイルの場所 | `~/bin/syncthing`（**644。実行権なし＝未起動**） |
| 設定の場所 | `~/.local/state/syncthing/`（`config.xml` / `key.pem` / `cert.pem`） |

## 規約の適用判定

| 規約 | 適用 | 根拠 |
|---|---|---|
| `proposal_gate` | **される** | 禁止語は「提案と**契約の本文**」が対象（conventions.md:219）。送出物へ検査を当てた |
| `folds` | **されない** | 学習も評価も行わない契約で、折りを選ぶ場面も val/test に触れる場面も無い |
| `symmetry` | **されない** | 節が「対象: **exp 契約のすべて**」（conventions.md:315）。本契約は `kind: impl`。L3 の P13 も同理由で SKIP |

SPEC の見込みは `folds`・`symmetry` については正しく、`proposal_gate` については当てはまらない。

## 訂正した記述（`env-facts.md`）

| 行 | 直した内容 |
|---|---|
| 到達性 | 「参加する **5 台**」→「参加する **6 台**（efros を含む）」 |
| 到達性 | **dlsta を七台目として追加**（基盤のみ。住所 `192.168.196.54` は容器の内側から照合できない旨を併記） |
| repo の位置 | **三種目 `~/local/m2`（dlsta のみ）** を追加 |
| 実行環境 | uv の python 実体が dlsta では**両方の名前が在り**、`.venv` は patch 番号を含む方を指す |
| 実行環境 | `~/.gitconfig` は dlsta では**残っていた**（local は空、global が効く） |
| 実行環境 | `pushurl` は dlsta では**未設定で `url` が既に HTTPS**。対処不要 |
| 実行環境 | `libGL.so.1` は **7 台で完了**（dlsta は 2026-09-20）。**導入は申告ではなく実測で確かめる** |
| 実行基盤 | `~/bin/**` `~/.local/state/**` への書き込みは dlsta では**拒まれなかった** |

`conventions.md` は触っていない。

## 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | 「版管理の識別は**未設定**」。実測では `~/.gitconfig` に設定済み。指示どおり「他台と同じ値を使う」を実行すると、既存値を上書きする不要な変更になった |
| `asserted_without_measuring` | 「論理名は dlsta である（…**住所の対応**による）」。容器の内側から見える住所は `172.17.0.12` のみで `192.168.196.54` と照合できない。住所で確かめるには外部接続（禁止 3）が要り、手段が無い |
| `asserted_without_measuring` | 0 節が `git checkout -b feat/dlsta-join-foundation origin/phase0` を指示するが、分岐は既に存在し HEAD も `origin/phase0` と同一。そのまま打つと `already exists` で落ちる |
| `self_contradiction` | Task 2 の Files 欄は `~/.zshenv` と `~/.profile` の 2 つだが、同じ Step が使えと指す `setup_host_servername.sh` は `~/.bashrc` にも書く（TARGETS は 3 つ）。指示に従うと Files 欄に無いファイルが変わる |
| `asserted_without_measuring` | 「現状」表の `~/.ssh/` の一覧に `id_ed25519_github.pub` が無いが実在する。5 件ではなく 6 件である |

**`check_does_not_check` と `shell_assumption` に該当する誤りは、契約の本文には無かった。**
なお `scripts/setup_env.sh:45` の `nvcc` 検査は prebuilt wheel 経路に対して不要な要求をしており
（手順 5 はソースビルドを行わない。audit.md:170-191）、これは**契約ではなく repo 側の欠陥**である。

## 逸脱・想定外・UNKNOWN

**逸脱**

1. **手順の順序を変えた。** L1+L2 検証と L3 プリフライトは `.venv` を要するが開始時に無く、Task 1 の後に実行した。SPEC 0 節が「Task 1 が済めば仕組みが使えるようになる」と明記しており、契約に沿う
2. **`git checkout -b` を実行しなかった**（分岐が既に存在）
3. **版管理の識別を新規設定しなかった**（既設定。「推測で設定しない」に従い出所のみ記録）
4. **`~/.bashrc` も変更された**（スクリプトの設計。Files 欄より 1 つ多い）
5. **`.sync-pause` を置かなかった。** `~/bin/` も `~/claude-sync/` も無く、`/proc` の計数も 0 件で、止める対象が存在しないため（SPEC の指示どおり）
6. **論理名の根拠を住所ではなく契約の記載に取った**（`task_id`・実行ホスト宣言・配置先ファイル名）
7. **`libgl1` の導入は利用者が実行した。** 一度目の完了申告の時点では 4 系統すべてが未導入を示したため、申告を根拠にせず実測を正とし、二度目で導入を確認した
8. **試験の「変更前」を HEAD の worktree で測った**（開始時に `.venv` が無く直接測れなかったため）

**想定外**

- **自分が立てた検査が 3 回壊れていた**（いずれも自分で捕まえて組み直した。audit.md:139-160, :294-307, :434-469）
  1. `/proc/net/tcp` の復号器が `strtonum`（gawk 専用／本ホストは mawk）で**全件 0 を返していた**。陰性対照だけでは「常に 0 を返す壊れ方」と区別できなかった
  2. `grep -c` の 0 件が終了コード 1 を返して `&&` の連鎖が切れ、**鍵の生成に到達していなかった**
  3. `SERVERNAME` の陰性対照 `env -i zsh` が `dlsta` を返した（zsh は `env -i` でも passwd から `HOME` を復元する）。空ディレクトリを `HOME` に与える形へ直した
- `P9 spec_lint` が `host_mismatch` で WARN。規則が `socket.gethostname()`（= `4f3861ae8d3b`）と宣言値を比べており、**本ホストでは必ず該当する**。既知の検査器の限界（`tasks/inbox.md`:121/190/302/342 に既出）

**UNKNOWN**

- **本ホストの外向きの住所が `192.168.196.54` であることは確認できていない。** 容器の内側からは `172.17.0.12`（gateway `172.17.0.1`）のみが見え、外部接続は禁止 3 に当たるため測れない
- 同期処理の**告知の既定値（公開の探索網・公開中継）を無効化していない。** 本契約は起動しないため対象外だが、**起動前に必要**（後続の契約へ申し送る）

## 送出

| 項目 | 結果 |
|---|---|
| `make task-validate` | **exit 0**（`1 task(s), 0 failed`） |
| `make task-preflight` | **exit 0**（5 PASS / 1 WARN / 7 SKIP / 0 FAIL） |
| `make forbidden-check` | **exit 0**（`status: pass` / `violations: []` / 生成物 4 件は道具が除外） |
| 禁止語の検査（送出物 6 件） | **全件 exit 0**。陽性対照の囮は **exit 1・3 件該当**。**`audit.md` に該当 1 件が出たため本文を直した**（規約の禁止語の一覧の末尾の語。**語そのものをここに引かない。検査は完全一致のため、報告に引くと報告が落ちる**）。**検査は無効にしていない**。なお集約 `tasks/inbox.md` は該当 8 件を持つが、**変更前と同数・同一で本契約の追加分は 0 件**（他契約の 2026-08 の行。技術用語の部分一致を含む） |
| 秘匿検査（自作・形で判定） | **全項目 0 件**。秘密鍵の本体 / 資格情報 5 件 / 合言葉 / 秘密鍵の塊。**標識の語を数える形は本証跡が検査を説明しているため偽陽性を出したので、塊を数える形へ直した**（audit.md:590-610）。**検査は長さと件数のみを出力し値を出力していない**。各項目に陽性対照（1 以上）つき |
| 変更の範囲 | **9 件すべて契約の範囲内**（範囲外 0 件。陽性対照で検出器の動作を確認） |
| `make taskindex-check` / `make inbox-check` | **ともに exit 0** |
| commit | `e4f80541`（本体）／ `02533e3c`（検査の記録） |
| push | **exit 0** |
| PR | **#187** |
| 台帳への送り返し | 下記 |
