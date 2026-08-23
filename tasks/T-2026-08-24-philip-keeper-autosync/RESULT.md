# RESULT — T-2026-08-24-philip-keeper-autosync

**判定: PARTIAL**  **ホスト:** `philip`（`hostname=aolab` / `SERVERNAME=philip`）
**分岐:** `feat/philip-keeper-autosync`  **repo:** `~/slocal2/m2`
**実行:** 2026-08-24 JST

常駐処理は配置・起動され、版管理の自動同期の経路は生きている。中継も同期処理も零件である。
PARTIAL としたのは 2 点。**契約の `sh -n` による構文検査は非零を返した**（正本は bash であり、
解釈系が違う）。**完了判定 11 は、契約の手順のままでは達成できず、実行者が回避策を取って達成した**。
どちらも下の表と逸脱に実測で記す。

生の出力は要約せず `audit.md`（申し送り #9）に貼ってある。

---

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]` の原文（`context/conventions.md:98-107`）。
**要約せず、そのまま写す。**

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

`conventions_rev` は実測して照合した（SPEC「実行者が実測して置換する」）。

| 項目 | spec の記載 | 実測 | 判定 |
|---|---|---|---|
| `contract.conventions_rev` | `d422b08` | `git log -1 --format=%h -- context/conventions.md` → `d422b08` | **一致。置換不要** |

`inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は本契約で**使用していない**。
常駐処理の配置と起動のみを扱い、データにも `experiments/**` にも触れていない（禁止 8）。
`inputs.denominator` `inputs.frozen_source` `inputs.sigma_policy` は spec に**記載が無い**ため解決対象外。

## 2. 検証とプリフライト

| 検査 | 結果 |
|---|---|
| `make task-validate` | `OK` / `1 task(s), 0 failed` / **exit=0**。WARN なし |
| `make task-preflight` | **exit=0** / 4 PASS / 1 WARN / 4 SKIP / 0 FAIL |
| P9 spec_lint（WARN） | 4 件該当: `separated_source@SPEC.md:329,332,335`（`source .venv/bin/activate \` の行継続）、`host_mismatch@SPEC.md:5` |
| SKIP された項目 | P2 `cuda_ext_loaded`、P3 `deterministic_flags`（`plan.env.preflight` に記載なし）、P4 `prereg_committed`、P5 `frozen_source_hash`（`kind=impl` のため対象外） |

**SKIP は合格ではない。** 4 件は実行されていない。

## 3. ゲート

| ゲート | 判定 | 何を実測したか |
|---|---|---|
| **G1**（Phase A 後） | **PASS** | `git rev-list --left-right --count origin/phase0...HEAD` = `0 0`（最新）。`marker_count=0`、`.zshrc` の `keeper` 該当 `0` 件（全 77 行）、未追跡 `6` 件。稼働計数は自己と祖先 15 件を除外し、陽性対照 `zsh=4` / 陰性対照 `zzz_none=0` を添えて全項目 0。分岐の範囲を `keeper.sh` の行番号つきで記録し、`m2-sync.sh` の発火条件（抑止 40-43 / auto-merge 60-88 / auto-push 103-112）を読んだ |
| **G2**（Phase B 後） | **PASS** | 配置物と正本の sha256 が一致（`keeper_match=yes` / `m2sync_match=yes`）。構文は `bash -n` で両方 0（`sh -n` は後述の理由で非零）。`keeper.sh=1 [72428]`、`ssh -N -L=0`、`syncthing=0`。`~/.keeper.lock` が作られ、二つ目を起動しても `keeper.sh=1` のまま（flock が実効）。`~/claude-sync/sync-alerts.log` に「一時停止中」が 1 行、`auto-merge=0` `auto-push=0`、`ahead/behind = 0/0` |

## 4. 完了判定 19 項目（実測値。未測定は UNKNOWN）

| # | 判定 | 実測 |
|---|---|---|
| 1 | 開始状態を記録した | `marker_count=0`（`.tunnel_to_` で計数。`tunnel_any_count=0`）／`.zshrc` の `keeper` 該当 `0` 件、`zshrc_lines_before=77`／`~/.keeper.lock` **不在**／`~/claude-sync/` **不在**（`exists=no readable=no`）／未追跡 `6` 件／`HEAD=3c4c5a6`／`~/bin/` には `syncthing` のみ |
| 2 | 稼働しているものを数えた（対照つき） | `keeper.sh=0` `m2-sync=0` `syncthing=0` `ssh -N -L=0`。陰性対照 `zzz_none=0`、**陽性対照 `zsh=4`（実行者が追加）**。自己と祖先 15 プロセスを除外、`/proc` 全 38 件を走査 |
| 3 | 正本の要約値と分岐を行番号つきで記録 | `keeper.sh` 52 行 `9fe9c423…dd90`／`m2-sync.sh` 133 行 `bcf46ba9…25f`。**両方とも `origin/phase0` の中身と一致**。分岐: 中継 33-38（`resolve_tunnel` が偽で動かない）、syncthing 41-43、自己更新 45-46、除外規則 48-49、版管理の同期 50、周期 51（1800 秒）、錠 25-26 |
| 4 | 版管理の同期の発火条件 | 記録先 `LOG=~/claude-sync/sync-alerts.log`（11 行）。抑止 40-43（**fetch の手前で `exit 0`**）。auto-merge 60-88（behind>0 かつ追跡変更 0 件かつ未追跡が阻害しない）。auto-push 103-112（**`origin/$BR` が存在するときのみ**）。auto-PR 115-（`gh` があるときのみ） |
| 5 | 配置物と正本の要約値が一致 | `keeper_match=yes` `m2sync_match=yes`（sha256 の突き合わせ。表示属性ではなく中身で判定） |
| 6 | 構文検査が両方とも通った | **契約どおりの `sh -n` では通らない。** `keeper_syntax=0` だが **`m2sync_syntax=2`**（`m2-sync.sh: 75: Syntax error: "(" unexpected`）。`/bin/sh` は `dash`、正本の shebang は `#!/bin/bash`、74-75 行がプロセス置換 `<(…)` を使う。**正しい解釈系 `bash -n` では両方 0**。壊した写しで `broken_syntax=2` を確認したので検査器自体は働いている |
| 7 | 目印が零件 | `marker_count=0` |
| 8 | 抑止を置き、対応版であることを確認 | `.sync-pause` 作成（0 バイト）。`grep -c sync-pause ~/bin/m2-sync.sh` = **2**（40・41 行）。陰性対照 `zzz_none_marker=0`。`.gitignore:240` で無視されるため版管理に現れない |
| 9 | 起動行を追記した（既存があれば追記しない） | 追記前 `0` 件のため追記した。77 → 81 行。内容は下記 |
| 10 | 常駐処理が一件だけ（識別子つき） | `keeper.sh=1 ['72428']` |
| 11 | 中継が零件、同期処理が零件 | `ssh -N -L=0 []`、`syncthing=0 []`。**ただし契約の手順のままでは達成できない**（逸脱 1） |
| 12 | 多重起動を防ぐ錠 | `~/.keeper.lock` が作成された（起動 1 秒後に出現）。**二つ目を起動して実測**したところ `keeper.sh=1 ['72428']` のままで、二つ目は `flock -n` を取れず去った |
| 13 | 同期が一周し、抑止が効いている | `~/claude-sync/sync-alerts.log` が**新規に作られ** 1 行: `2026-08-23 17:28:56 [philip] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）`。`automerge_lines=0` `autopush_lines=0` `fetch_fail_lines=0`、陽性対照 `philip_lines=1`、陰性対照 `zzz_none_lines=0`。`ahead/behind = 0/0`、`HEAD=3c4c5a6` のまま。除外規則も反映され `.stignore` の sha256 が `origin/phase0:.stglobalignore` と一致 |
| 14 | 全項目に実測値または UNKNOWN | 本表のとおり |
| 15 | 送信前の秘匿検査（陽性対照つき） | `hits=1`。中身は `SPEC.md:319` にある検査の正規表現そのもので、鍵の書き出し行でも語＋区切り＋値の形でもない（**件数ではなく形を一件ずつ目視した**）。陽性対照 `control_hits=3`、陰性対照 `neg_hits=0`。囮は `/tmp` にのみ置き削除した（**版管理へ入れていない**）。環境の資格情報 `NOTION_API_KEY` `WANDB_API_KEY` `NOTION_DB_ID` `GITHUB_TOKEN` `GH_TOKEN` はすべて unset で照合対象なし |
| 16 | 開始時の未追跡がすべて残っている | 開始時 6 件すべて `exists=yes`。commit 前の未追跡は 7 件で、増えた 1 件は本契約が作った `tasks/inbox.d/T-2026-08-24-philip-keeper-autosync.md`。**減っていない** |
| 17 | 変更が契約の範囲に限られる | 追跡変更は `tasks/T-2026-08-24-philip-keeper-autosync/` と `tasks/inbox.d/<task_id>.md` のみ。`~/bin/` `~/.zshrc` は版管理の外、`.sync-pause` は `.gitignore:240`、`.stignore` は `.gitignore:192` で無視されるため `status` に現れない。**`make forbidden-check` は `exit=2` で fail**。違反 4 件はすべて `data/annotations/**` の**未追跡ファイルで mtime は 2026-07-31**、本契約の 3 週間以上前から在り、Phase A で記録した未追跡 6 件に含まれる。`tools/check_forbidden.py` は `origin/phase0` を起点に未追跡も列挙するため作業ツリーに在る限り必ず fail する。**禁止 5 が削除・移動・commit を禁じているので通すために消さない。記録のみ**。`make taskindex-check` `make inbox-check` は**禁止 4 により実行していない（UNKNOWN）** |
| 18 | 分岐が送出され、PR が存在する | §8 に実測を記す |
| 19 | 抑止が repo 直下から消えている | §8 に実測を記す |

### 追記した起動行（そのまま）

```
# 常駐スーパーバイザ: 版管理の自動同期（flock で多重起動を防ぐため毎回呼んで安全）
# 設定: T-2026-08-24-philip-keeper-autosync (2026-08-24)
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
```

## 5. 起票者の誤り

| 型 | 箇所 | 何が誤っていたか / 指示どおり実行すると何が起きたか |
|---|---|---|
| `self_contradiction` | SPEC「分岐」表（39-50 行を「これを動かす」）と 禁止 2・完了判定 11 | `keeper.sh` の 41-43 行は**目印とは無関係**に `[ -x ~/bin/syncthing ]` だけを見て syncthing を起動する。philip では前契約 `T-2026-08-22-philip-hub-foundation` が `~/bin/syncthing` を mode 755 で配置し設定も生成済みのため、**指示どおり keeper を起動すると syncthing が必ず起動し、禁止 2 に触れ、完了判定 11「同期処理が零件」が同時に不成立になる**。契約の中で両立しない |
| `shell_assumption` | SPEC Task 2 Step 2（`sh -n ~/bin/m2-sync.sh`。「両方が零であること」） | 正本の shebang は `#!/bin/bash` で、`m2-sync.sh` 74-75 行が bash 固有のプロセス置換 `<(…)` を使う。`/bin/sh` は `dash` であるため、**指示どおり実行すると `exit=2` と `75: Syntax error: "(" unexpected` が出る**。正常な正本が不合格に見え、完了判定 6 が原理的に満たせない |
| `asserted_without_measuring` | SPEC Task 3 Step 5「`~/claude-sync/` は失われている。記録の置き場所が無ければ、別の場所を探すか `UNKNOWN` とする」 | 開始時に不在だったのは事実だが、`m2-sync.sh` 22 行が `mkdir -p "$(dirname "$LOG")"` で**自分で作る**。実測では一周目で `~/claude-sync/sync-alerts.log` が生成された。「探すか UNKNOWN」という前提は不要で、放置すれば UNKNOWN と誤記される |
| `check_does_not_check` | SPEC Task 1 Step 2「存在しない語が零を返すことが対照である」 | 存在しない語が 0 を返すのは**陰性対照のみ**で、全項目が 0 の状況では検出器が壊れていても同じ出力になる。**指示どおりだと「全部 0」が検出器の空振りか本当に不在かを区別できない**。実行者が陽性対照 `zsh=4` を追加して初めて区別できた |

## 6. 逸脱（deviations）

1. **`~/bin/syncthing` の実行権を一時的に落とした（`chmod 755` → `644`）。** 上の `self_contradiction` を回避するため。`keeper.sh` 41 行の `-x` 判定を偽にして syncthing の起動だけを止め、版管理の同期は動かす。**中身は変えていない**（sha256 は変更前後とも `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` で一致。表示属性ではなく要約値で確認 — 申し送り #5）。設定・鍵・識別子には触れていない。**戻し方は `chmod 755 ~/bin/syncthing` の 1 行**。ユーザーへ 3 案（実行権を外す／そのまま起動して記録する／Phase A で停止して差し戻す）を提示し、**「実行権を一時的に外す」の選択を得て実施した**。
2. **完了判定 6 の根拠を `sh -n` から `bash -n` へ置き換えた。** 上の `shell_assumption` による。`sh -n` の結果も非零のまま記録し、隠していない。
3. **稼働計数に陽性対照 `zsh` を追加した。** 契約は陰性対照しか求めていないが、申し送り #6「対照は両方向で取る」に従った。
4. **構文検査に陽性対照を追加した。** 壊した写しが `exit=2` を返すことを確かめ、検査器の空振りを排除した。
5. **`flock` の実効を実測で確かめた。** 契約は「錠が作られていること」しか求めていないが、二つ目を起動して `keeper.sh=1` のままであることを確認した。錠の存在は錠が効いていることを意味しない。
6. **実行者の測り方に誤りがあり、訂正した。** `grep -c PATTERN FILE || echo UNKNOWN` は該当 0 件のとき `grep` が exit 1 を返すため、`0` と `UNKNOWN` を**両方**出力していた（申し送り #4・#7 の罠そのもの）。「読めない」と「0 件」を区別する形で測り直し、訂正の経緯ごと `audit.md` に残した。
7. **`make taskindex` `make inbox` `make taskindex-check` `make inbox-check` を実行していない。** 禁止 4（生成物を再生成しない）による。`task` スキルは投影の確認を求めるが、**本契約の禁止が優先する**。したがって本報告が `context/auto/` に現れることは**確かめていない（UNKNOWN）**。全台の統合後に一台で一度だけ再生成すること。
8. **前契約の未追跡 3 件（`experiments/transfer/_smoke_*`）が `git status` から消えたが、失われていない。** 実測で `exists=yes tracked=no`、`.gitignore:174-176` が上流で追加されたため表示されなくなっただけ。無視物を含めた未追跡は 1093 件。**escalate_if「版管理外の未追跡の成果物が失われた場合」には該当しない。**
9. **`make task-report` を実行していない。** 合言葉が失われ `scripts/load_env.sh` が使えないため（SPEC が明記）。`outputs.report_to` も空である。
10. **`git checkout -b` を実行していない。** 分岐 `feat/philip-keeper-autosync` は本セッション開始時に既に存在し `origin/phase0` と `0/0` で一致していた。作り直す必要が無い。

11. **`make forbidden-check` を通せていない（`exit=2`）。** 違反 4 件はすべて `data/annotations/**` の未追跡ファイルで、mtime は 2026-07-31。本契約が作ったものでも触ったものでもない。`tools/check_forbidden.py` は `origin/phase0` を起点に未追跡も列挙するため、これらが作業ツリーに在る限り必ず fail する。**禁止 5 が削除・移動・commit を禁じているので、通すために消さない。記録のみとした。**
12. **実行者が終了コードの取り方を誤り、訂正した。** `${PIPESTATUS[0]}` を使ったが、**このシェルは zsh** で配列添字が効かず空文字になった。SPEC の「全台で確定した事実」と申し送り #8 が明示していた罠に落ちた。パイプを使わず出力をファイルへ落として直後に `$?` を取る形で測り直し、訂正の経緯ごと `audit.md` に残した。

## 7. 次の契約への申し送り

| 項目 | 内容 |
|---|---|
| **記録の置き場所** | `~/claude-sync/sync-alerts.log`（`m2-sync.sh` 11 行）。**不在でも `mkdir -p` で自分で作る**（22 行）。開始前に無いことを理由に UNKNOWN と書かないこと |
| **起動行の内容** | `( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null`。`flock` があるので毎回呼んで安全 |
| **目印を置いたときの見込み** | `~/.tunnel_to_<hub名>` の 1 行目が秘密鍵パス、2 行目が中心の住所（省略時は名前を SSH 別名に使う）。`resolve_tunnel` は**辞書順で最初の 1 件**を選ぶ。中継は `ssh -N -L 22001:127.0.0.1:22000 -p 50072`。`ExitOnForwardFailure=yes` なので相手が受け付けなければ即座に落ちる |
| **`~/bin/syncthing` の実行権を戻すこと** | philip では本契約が `644` へ落とした。**識別子の登録が済んで同期処理を立ち上げる契約で `chmod 755 ~/bin/syncthing` が要る**。忘れると keeper が永遠に syncthing を起動しない |
| **他台でも同じ矛盾が起きる** | `~/bin/syncthing` を配置済みの台では、keeper を起動した瞬間に syncthing が立つ。**philip 以外の 4 台で同じ判断が要る** |
| **`sh -n` を使わないこと** | 正本は bash。`bash -n` で検査する |
| **auto-push は最初の push まで発火しない** | `origin/$BR` が存在するときだけ動く（103 行）。**最初の 1 回は手で push する必要がある** |
| **`.stignore` は毎ループ上書きされる** | keeper 48-49 行が `origin/phase0:.stglobalignore` から再生成する。手で編集しても 30 分以内に消える |
| **抑止は 1 台にだけ効く** | `.sync-pause` は `.gitignore:240` と `.stignore` の総取り規則の両方に落ちる |
| **`forbidden-check` は全台で fail するはず** | `data/annotations/**` の未追跡 4 件（mtime 2026-07-31）が原因。禁止 5 で触れないため実行者側では解消できない。**起票側で扱いを決めてほしい** |
| **auto-merge は阻害されない** | `m2-sync.sh` 73-75 行と同じ式で測って `BLOCKED=0`。抑止を外せば次の周回から統合が動く |
| **つまずいた点** | `pgrep -af` は自分のコマンド行を拾う（本セッションでも再現した）。`/proc` 走査で自己と祖先を除外する方式が確実。`${PIPESTATUS[0]}` は zsh では効かない（本セッションで再現した） |

## 8. 送出と抑止の解除

（本節は commit 直前に確定した値で記す。push の結果は `audit.md` の Phase C に実測を貼る。）

| 項目 | 実測 |
|---|---|
| 送出先 | `https://github.com/takuya3h/m2.git`（**`git@` ではないので配備鍵は不要**） |
| `gh` の有無 | `gh_present=yes` |
| `origin/feat/philip-keeper-autosync` | 開始時 **不在**（auto-push が発火しない状態） |
| git 身元 | `user.name=takuya3h`、`user.email` は設定済み、`~/.gitconfig` **存在**（前契約時は不在だった。ユーザーが復旧済み） |
