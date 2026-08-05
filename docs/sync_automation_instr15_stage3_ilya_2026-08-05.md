# 指示書 #15 段 3 — auto-merge 実装報告

| | |
|---|---|
| 実施 | ilya（hostname `aolab` / `SERVERNAME=ilya`）, 2026-08-05 |
| ブランチ | `feat/sync-automation-20260805`（起点 `origin/phase0` = `37126cc`） |
| 対象 | `scripts/sync/m2-sync.sh` |
| commit | `3634594` feat(sync): add auto-merge before auto-push |
| 一次データ | 変更 0 件 |
| `keeper.sh` | 変更 0 件 |
| 自動 commit | 実装なし |

---

## 0. 位置づけ

指示書 #15（同期の自動化）の段 3。段 1（設計調査）・段 2（alert ヘルパー /
`.servername` 補完 / auto-push）に続き、`m2-sync.sh` に **auto-merge**
（`origin/phase0` の更新を作業ブランチへ自動で取り込む機能）を追加した。

---

## 1. 実装

auto-push の**前**、`BR`/`MAIN` の分岐直後に追加。

```bash
# --- auto-merge: phase0 の更新を作業ブランチへ取り込む ---
# auto-push より前に置く。merge してから push すれば 1 ループで両方片付く。
# 条件: 作業ブランチ上 / 追跡変更 0 件 / behind > 0 / 未追跡が阻害しない
# 安全策: rm は自動化しない（内容同一の判定と退避は人間が行う）。衝突したら即 abort。
if [ "$BR" != "$MAIN" ]; then
  BEHIND=$(git rev-list --count "HEAD..origin/$MAIN" 2>/dev/null || echo 0)
  if [ "$BEHIND" != "0" ]; then
    # grep -c は該当 0 件で exit 1 を返すため || true が要る。
    DIRTY=$(git status --porcelain | grep -vc '^??' || true)
    if [ "${DIRTY:-0}" != "0" ]; then
      alert "auto-merge skip: 追跡変更 ${DIRTY} 件 (behind ${BEHIND})"
    else
      # 未追跡ファイルが取り込み先にも存在すると git は上書きを拒む。
      # 事前に集合の積を取って判定する（rm はしない）。
      BLOCKED=$(comm -12 \
        <(git ls-files --others --exclude-standard | sort) \
        <(git ls-tree -r --name-only "origin/$MAIN" | sort) | wc -l | tr -d ' ')
      if [ "$BLOCKED" != "0" ]; then
        alert "auto-merge skip: 未追跡 ${BLOCKED} 件が阻害 (behind ${BEHIND}) 手動対応が必要"
      elif git merge --no-edit -q "origin/$MAIN" 2>/dev/null; then
        alert "auto-merge: ${BR} <- origin/${MAIN} (${BEHIND} commits)"
      else
        # conflicted state を残すと次ループから毎回失敗し続けるので必ず戻す。
        git merge --abort 2>/dev/null
        alert "auto-merge失敗(abort済): ${BR} <- origin/${MAIN} 手動対応が必要"
      fi
    fi
  fi
fi
```

前提の確認:

```
shebang               : #!/bin/bash（プロセス置換 <(...) が使える）✅
阻害判定の計算量       : comm によるソート済み集合の積 1 回（未追跡ファイルごとの
                          個別ループではない）
```

---

## 2. 検証結果

### 2.1 阻害判定の実測

```
阻害件数: 0
実行時間: 0.076 秒
  未追跡ファイル数         : 4
  origin/phase0 のファイル数: 7,176
```

7,176 ファイルとの比較でも 0.076 秒。30 分ループに対して無視できるコスト。

### 2.2 skip 条件 — 2 種類とも実測で確認

検証用に `origin/phase0~3` から一時ブランチ `tmp-automerge-test` を切り、
**behind 11** の状態を作った（詳細は §3 参照）。

| 条件 | 実測ログ | 結果 |
|---|---|---|
| **追跡変更あり** | `auto-merge skip: 追跡変更 1 件 (behind 11)` | behind 11 のまま（merge していない）✅ |
| **未追跡が阻害** | `auto-merge skip: 未追跡 1 件が阻害 (behind 11) 手動対応が必要` | behind 11 のまま ✅ |

いずれも `rm` は実行していない。スクリプトは skip してアラートを残すのみで、
削除は人間の判断に残されている。

### 2.3 auto-merge が実際に走ることの実測

```
実行前: HEAD 1b3b6f8 / behind 11 / 追跡変更 0 件 / 阻害 0 件
bash m2-sync.sh   （3.95 秒）
実行後: HEAD 37126cc / behind 0 / HEAD == origin/phase0 : YES

ログ: 2026-08-05 04:42:13 [ilya] auto-merge: tmp-automerge-test <- origin/phase0 (11 commits)
ログ増加: 1 行のみ
```

11 コミットを 1 回の merge で取り込み、アラートも 1 行に収まった。

### 2.4 `m2-sync.sh` 全体の実行時間

```
auto-merge なし（behind 0）  : 6.12 秒
auto-merge あり（11 commits）: 3.95 秒
```

大半は `git fetch origin` のネットワーク待ちで、auto-merge 追加による
有意な増加は見られない（fetch 所要時間の揺らぎの方が大きい）。

---

## 3. 判断に迷って独自に決めたこと

### 3.1 検証手順を変更した — `git reset --hard` を使わなかった

指示書は push 済みブランチに `git reset --hard HEAD~1` を当てて behind を
作る手順だったが、**それでは目的を達成できない**。`feat/sync-automation-20260805`
は `origin/phase0` の子孫なので、1 コミット戻しても `HEAD..origin/phase0` は
0 のままである。

代わりに次の方法を採った。

```bash
git switch -c tmp-automerge-test origin/phase0~3   # behind 11 が自然にできる
# ... 検証 ...
git switch feat/sync-automation-20260805
git branch -D tmp-automerge-test                    # 削除済み。git branch に残っていないことを確認
```

利点:
- push 済みブランチに破壊的操作（`reset --hard`）を当てずに済む
- `origin/tmp-automerge-test` が存在しないため auto-push が自動的にスキップされ、
  **auto-merge だけを切り分けて観測できた**

### 3.2 テスト対象ファイルを変更した

`OPERATION.md` は `origin/phase0~3` の時点に存在せず、`echo >>` が
未追跡の新規ファイルを作ってしまった（意図した「追跡変更あり」テストに
ならなかった）。誤って作られた `OPERATION.md`（1 行）は `/bin/rm -f` で削除
（通常の `rm` はエイリアスで対話プロンプトに入り 2 分タイムアウトしたため
フルパスで回避）。

そのブランチに実在する `docs/TODO.md` に対象を変更し、追跡変更 skip を
測り直した。なお、この取り違えの結果として**未追跡阻害の skip も
実データで検証できた**（`OPERATION.md` が `origin/phase0` に実在するファイル名
だったため、意図せず阻害条件そのものを再現していた）。

---

## 4. 既存動作への影響確認

| 項目 | 状態 |
|---|---|
| `keeper.sh` | 一切触っていない ✅ |
| 自動 commit | 実装していない ✅ |
| 既存 3 役割（fetch / ff-only merge / 参照更新） | 不変 ✅ |
| アラート書式・メッセージ文字列 | 不変（既存ログと grep 互換）✅ |
| `phase0` 上での不実行 | `[ "$BR" != "$MAIN" ]` で先頭ガード ✅ |
| `rm` の自動化 | していない（skip するのみ）✅ |
| conflicted state の放置 | `--abort` で必ず戻す ✅ |

---

## 5. 段 2 からの継続事項（参考）

段 2 で発見・修正した設計変更が段 3 の前提になっている。

- **`@{u}` 基準 → `origin/$BR` 基準への変更**（auto-push）:
  `git switch -c <new> origin/phase0` で作ったブランチは上流が `origin/phase0`
  のまま残るため、`@{u}` 基準だと push しても ahead が減らず無限ループする。
  実測で再現し、`origin/$BR` 基準に変更して解消済み。
- `alert()` ヘルパーを新設し、既存 3 箇所のインライン `echo` を置換
  （メッセージ文字列は不変、既存 432 行との grep 互換を維持）。
- サーバー名を 3 段（`SERVERNAME` → `$M2DIR/.servername` → `hostname`）で解決。
  稼働中の keeper（PID 73082、2026-07-04 起動）が `SERVERNAME` 設定前から
  動いているため、`.servername` を挟まないと philip と ilya が両方 `[aolab]`
  として記録される問題への対処。

---

## 6. 現在の状態

```
ブランチ  : feat/sync-automation-20260805
HEAD      : 3634594
push 状態 : ahead(origin/$BR) 1（このコミットは未 push）
作業ツリー: 追跡変更 0 件 / 未追跡 3 件（_smoke_* の除外規約該当）
```

## 7. 次の段（未着手）

- **段 4**: auto-PR の実装（auto-push の**後**に配置。push していないブランチに
  PR は作れないため）。`gh` の可用性は段 1 で実測済み（keeper の最小環境でも
  `command -v gh` / `gh auth status` とも OK）
- **段 5**: `third_party/` 同期の設計案（3 案の比較、実装なし）
- **段 7**: `.servername` の全台配布、PR 作成
