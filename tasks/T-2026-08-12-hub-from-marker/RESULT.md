# RESULT — T-2026-08-12-hub-from-marker

## 1. 解決された参照

`contract.inject_verbatim: conventions#prohibitions` は `context/conventions.md` の commit `d422b08` から次の原文を解決した。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

## 2. 結論

正本 `scripts/sync/keeper.sh` から固定中心名と固定住所を除き、`.tunnel_to_*` のファイル名から中心を導出する形へ変更した。目印が無いノードは張らず、複数時は辞書順の最初の一件を選ぶ。旧形式は 1 行目の鍵パスとファイル名由来の SSH 別名を使い、新形式は任意の 2 行目に住所を持てる。

偽 HOME の四対照はすべて期待どおりだった。変更前後とも `ssh -N -L=0`、`keeper.sh=1`、陰性対照 `0` であり、稼働版と本物の目印のサイズ・mtime も不変だった。正本の配置、稼働版の置換、目印の変更、常駐処理の再起動は行っていない。

## 3. 完了判定

| # | 判定 | 変更前 | 変更後・実測 |
|---|---|---|---|
| 1 | 正本と稼働版 | 各 34 行 / 2250 bytes | 変更前の差分出力 0 行 |
| 2 | 中心関連箇所 | 5 行 | 汎用解決処理 15 行。固定中心名・旧住所は 0 件 |
| 3 | 変更前挙動 | 旧目印のみ張る、新名のみ・無しは張らない | `audit.md` に実装読解を記録 |
| 4 | 自ホストの目印 | `.tunnel_to_philip` 1 件、43 bytes | 不変 |
| 5 | 固定中心の除去 | 名前・住所を判定に使用 | `grep_exit=1`、一致 0 件 |
| 6 | 構文 | 変更前スクリプト | `sh -n` exit 0、shellcheck 不在 |
| 7 | 複数目印 | 未定義 | 辞書順の最初の一件を選択 |
| 8 | 四対照 | 未実装 | legacy=philip、新形式=lecun、無し=no_tunnel、複数=lecun |
| 9 | 張らない検証方法 | 該当なし | resolver 関数だけを抽出し偽 HOME で Bash 評価 |
| 10 | 中継数 | `ssh -N -L=0`, `keeper.sh=1`, 陰性=0 | 同じ三値 |
| 11 | 稼働版・目印 | keeper 2250 bytes、目印 43 bytes | サイズ・mtime とも不変 |
| 12 | 11 項目の実測 | 未記録 | 本表と `audit.md` に記録 |
| 13 | 次契約の情報 | 未記録 | §4 に書式・配置・再起動手順を記録 |
| 14 | 試験 | 5 failed / 434 passed | 5 failed / 434 passed、失敗名も同一 |
| 15 | 変更範囲 | 契約取り込み前 | 正本・契約成果物・判断受け皿・上位指示の文書のみ |
| 16 | 分岐送出 | 未実施 | `origin/feat/hub-from-marker` を追跡、ahead 0 |
| 17 | PR | 未作成 | `#94`、OPEN、Draft ではない |
| 18 | 同期抑止 | `.sync-pause` あり | `released`、repo 直下から消失 |
| 19 | 台帳返却 | 未実施 | `verdict=pass`、`report_exit=0` |

## 4. 次契約に必要な情報

### 目印の書式

- ファイル名: `.tunnel_to_中心名`。lecun を中心にするノードでは `.tunnel_to_lecun`。
- 1 行目: そのノードから中心へ入るための秘密鍵パス。
- 2 行目: そのノードから到達できる中心の住所。SSH 別名で住所解決できない環境では必須。
- 旧形式: 2 行目を持たない `.tunnel_to_philip` は引き続き利用でき、`philip` を SSH 別名として解決する。
- 複数存在時: 辞書順で最初の通常ファイルだけを使う。移行時に旧目印を残すと選択結果が名前順に依存する。

### lecun の扱い

中心自身は目印を置かない。現在の lecun にある旧目印をどう外すかは、稼働版を配置する次契約で対象とする。本契約では変更していない。

### 配置と再起動

1. `origin/phase0:scripts/sync/keeper.sh` を一時ファイルへ展開し、構文・差分・権限を確認してから `~/bin/keeper.sh` へ置く。
2. `/proc/*/cmdline` から稼働中 keeper の PID を一件ずつ特定し、広域 `pkill` を使わず対象 PID だけを停止する。
3. `nohup ~/bin/keeper.sh >/dev/null 2>&1 &` で起動し、`flock`、keeper 一件、中継数、ログ進行を確認する。
4. 各非中心ノードでは新書式の目印を配置し、中心 lecun では目印を置かない。鍵や目印の生成・配布・変更は次契約の明示範囲で行う。

## 5. 試験

`origin/phase0` commit `6ed77e9` の一時 worktreeと変更後の双方で全体 pytest を実測した。

- 変更前: `5 failed, 434 passed, 22 warnings in 24.68s`
- 変更後: `5 failed, 434 passed, 22 warnings in 23.69s`
- 既存失敗: `tests/test_engines.py` 1 件、`tests/test_research_logger.py` 4 件
- 新規失敗: 0 件

陽性対照では、破損構文を `sh -n` が exit 2 で拒否し、固定中心文字列を検索が exit 0 で検出し、空鍵の目印を resolver が拒否した。

## 6. 逸脱・起票者欠陥

- 上位指示により `tasks/todo.md`、`tasks/lessons.md`、`README.md` を更新した。契約 Files 欄外だが、計画記録、修正学習、コード変更後の実装状態記録として必須だった。
- Codegraph は初期化済みだったが、導入版には `watch` コマンドが無く `unknown command` で終了した。
- resolver の最初の偽 HOME 評価を対話シェル zsh で行うと未一致 glob がエラーになった。対象の shebang と同じ Bash で四件すべて再測定した。
- `grep ...; echo "count=$?"` は一致件数でなく終了コードを出す。固定値なしは `grep_exit=1` と `grep -c` の一致 0 件を分けて記録した。
- 一時 worktree の最初の削除確認で、後続の `|| echo` が削除失敗を隠した。実在を再確認後、対象を限定して削除し、パスと登録の不在を別々に検証した。

## 7. 版管理

- commit: `f6ac77b feat(sync): derive hub from marker instead of hardcoded constant`
- commit: `4186eb7 docs(task): record hub marker PR and verification`
- commit: `b090043 docs(task): finalize hub marker result`
- PR: `#94`（OPEN、`isDraft=false`）
- phase0 への取り込み: 未実施

## 8. 未解決

- lecun が他ノードから到達可能な住所は本契約では再測定していない。新目印の 2 行目は次契約で各ノードから実測する。
