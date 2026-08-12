# phase0 取り込み — lecun 実施記録（2026-08-02）

全サーバー共通タスク「phase0 を取り込む（efros / philip / lecun / Bengio / Andrew）」の
**lecun** における実施記録。統合済み phase0 を作業ブランチへ取り込む作業。

- ホスト: `lecun` / `/home/ubuntu/slocal2/m2` / ブランチ `exp/lecun-wip-20260703`
- 結果: **fast-forward で完了**（behind 64 → 0、HEAD = `213b52b`）
- 作成コミット: `2759a9b`（#09 実施記録の docs 追加のみ。merge 自体はコミット無し）

> ⚠️ **他ホストへの申し送り**: 本作業は 2 回失敗した。原因は lecun 固有ではなく、
> **Syncthing による削除の巻き戻し**と**フックによるログ再書き込み**の 2 つ。
> 回避策は §3 にまとめた。Andrew / Bengio でも同じ事象が起きる見込み。

---

## 0. 結果サマリ

| 項目 | 実測 | 期待値 |
|---|---:|---:|
| behind（merge 前 → 後） | **64 → 0** | 0 ✅ |
| merge の性質 | **fast-forward**（マージコミット無し） | FF ✅ |
| CONFLICT / unmerged | **0 / 0** | 0 ✅ |
| `runindex/index.csv` | **721 行（720 run）** | 721 ✅ |
| `runindex/experiments.csv` | 195 | 195 ✅ |
| `runindex/per_class.csv` | 5,896 | 5,896 ✅ |
| `runindex/verdicts.csv` | 1,028 | 1,028 ✅ |
| backlog B-24〜B-29 | **6 件** | 6 ✅ |
| `runindex/` 未コミット差分 | **0**（`make runindex` 未実行） | 0 ✅ |
| `third_party_snapshot/` | **5 ホスト** | 5 ✅ |
| GPU | 実行中プロセス 0（未接触） | — |

**3 数値**（統合により +33 run 到着）

| | 取り込み前 | 取り込み後 |
|---|---:|---:|
| ディスク上 `metrics.json` | 721 | **754** |
| 追跡済み `metrics.json` | 687 | **720** |
| 退避（ignored） | 34 | **34** |

---

## 1. 未追跡ファイル 54 件の衝突

### 1.1 事象
phase0 が新規追加する 541 ファイルのうち、**54 件が lecun のローカル未追跡ファイルと同名**だった。

```
error: The following untracked working tree files would be overwritten by merge:
	experiments/hand2det_dev/.../logs/eval_meta_val.json
	...
```

| 対象 | 件数 |
|---|---:|
| `experiments/hand2det_dev/*/logs/`（21 サブラン × 2） | 42 |
| `experiments/transfer/_p0_identity_{ctrl,inj}_seed{42,123,456}/logs/`（6 run × 2） | 12 |
| **合計** | **54** |

想定されていた `README.md` / `docs/experiment_log.md` の**内容衝突は 0 件**
（両側で変更されたファイルは 0）。発生したのは種類の異なる untracked 衝突だった。

### 1.2 情報損失が無いことの証明
```
SAME 54 / DIFF 0
```
`git hash-object <local>` と `git rev-parse origin/phase0:<path>` の blob hash 比較で
**全 54 件が一致・相違 0 件**。削除しても merge が同一バイトを復元するため損失は生じない。

さらに保険として tar バックアップを作成し、**展開して原本と全件バイト一致すること**を
削除前に検証した（54 ファイル / 28K）。

### 1.3 なぜ衝突したか
指示書 #09 の §3 調査時点で「未追跡だが Syncthing 層で保護されている」と報告した run 群が、
**他ホスト経由で phase0 に取り込まれた**結果、
「ローカルでは未追跡 / phase0 では追跡済み」という状態になった。

→ #09 §6 で保留としていた「`_p0_identity_*` と `hand2det_dev` の帰属」は、
**git に収載され永続化されたことで解消**した。

---

## 2. 2 度の失敗とその原因

| 試行 | 結果 | 原因 |
|---|---|---|
| 1 回目 | `Aborting` | `.claude/hooks/auto_notion_sync.log` にローカル変更（フックが再書き込み） |
| 2 回目 | `Aborting` | 削除した 54 件が **Syncthing により復元済み**（1 回目の中断中に発生） |
| 3 回目 | ✅ 成功 | `restore` → `rm` → `merge` を単一コマンド化して競合を回避 |

### 2.1 🔴 Syncthing が削除を巻き戻す
`rm` で 54 件を削除した直後、**約 40 秒後に Syncthing がすべて復元した**
（復元後の mtime `2026-08-02 19:35:54` を実測。当時の現在時刻 19:36:31）。

`.stignore:44` の `!experiments/**/logs` により当該パスは同期対象であり、
他ノードが原本を保持しているため、ローカルの削除が巻き戻される。

結果として「削除 →（別要因で merge 中断）→ 再 merge」という手順を踏むと、
**中断している間に復元され、2 回目の merge も同じ衝突で失敗する**。

### 2.2 削除の挙動は「起点」で変わる（2026-08-04 追記）

§2.1 で記録した「Syncthing が `rm` を約 40 秒で巻き戻す」現象には条件がある。

| 状況 | 結果 |
|---|---|
| **片側だけの削除**（他ホストが原本を保持している） | **約 40 秒で巻き戻される** |
| **同期された削除**（正規の削除操作として発信） | **伝播する。巻き戻らない** |

2026-08-04 の伝播テストで実測した。lecun が
`experiments/_smoke_proptest_20260804_223211/{checkpoints,logs}` を
削除したところ、6ms で完了し、60 秒後も巻き戻されなかった。

§2.1 の事例は「phase0 の merge を通すために、他ホストが原本を持ったまま
lecun のローカルだけを消した」ケースであり、Syncthing から見れば
**欠損**にあたるため復元が飛んできた。今回は削除自体が意図として
ピアへ伝播している。

**したがって §2.1 の回避策（`rm` と `merge` を単一コマンドで連続実行）が
必要なのは前者の場合のみである。** 実験成果を意図的に削除するときは
通常の `rm` でよい。

#### 伝播テストの実測値（参考）

| 層 | 到達時間 | 対象 |
|---|---|---|
| Syncthing | **28 秒で全 10 台**（md5 完全一致） | `checkpoints/*.pth` / `logs/*.log` |
| git | 未到達（phase0 未マージのため。設計どおり） | `metrics.json` / `server.txt` / `git_commit.txt` / `notes.md` |

`.stignore` が全 11 台で正しく効いており、git 管理の 4 証跡は
Syncthing で配られなかった。二層の境界が保たれていることを確認した。

### 2.3 `auto_notion_sync.log` の再書き込み
`.claude/hooks/auto_notion_sync.log` は Notion 同期フックが動作するたびに追記されるため、
`git restore` で破棄しても時間が経つと再び変更され、
`Your local changes to the following files would be overwritten by merge` で merge が中断する。

このファイルは phase0 で `.gitignore` に入るため、**merge さえ通れば以後は再発しない**。

---

## 3. 回避策（他ホストはこれを使うこと）

**Syncthing を停止する必要はない。** 復元まで約 40 秒の猶予があるため、
`git restore` → `rm` → `git merge` を **単一コマンド内で連続実行**すれば十分に先行できる。

```bash
cd <m2 のパス>
WD=<作業ディレクトリ>          # same.txt を置いた場所

# 3 つを 1 コマンドで連続実行する（間に他の処理を挟まない）
git restore .claude/hooks/auto_notion_sync.log
xargs -a "$WD/same.txt" rm --
git merge origin/phase0
```

lecun での実測タイミング:

```
開始       : 19:36:57.904
rm 完了    : 19:36:57.948
merge 完了 : 19:36:58.212     ← rm から 264ms
```

Syncthing の復元（約 40 秒）に対し **2 桁以上速く**、競合しない。
`auto_notion_sync.log` の再書き込みも同時に回避できる。

---

## 4. 実施手順と検証結果

### 4.1 対象の再特定（削除前）
```
54 SAME
 0 DIFF      ← DIFF が 1 件でもあれば停止する条件。該当なし
```

### 4.2 バックアップ
```
tar 内のファイル数 : 54
tar サイズ         : 28K
展開して原本と比較 : 一致 54 / 不一致 0
```

### 4.3 削除 → merge
```
削除後に残存する対象ファイル : 0 件
merge                        : fast-forward（HEAD == origin/phase0）
CONFLICT / unmerged          : 0 / 0
MERGE_HEAD                   : なし
```

### 4.4 復元確認
| 項目 | 結果 |
|---|---|
| 未復元 | **0 件** |
| 内容不一致（blob hash 再検証） | **0 件** |
| 54 件の追跡対象化 | **54 / 54** |

### 4.5 バックアップの破棄
全条件の通過をプログラムで判定してから破棄した（未通過なら保持する分岐を実装）。
`overlap_backup.tgz` / `same.txt` / `overlap.txt` の残存 **0**。

---

## 5. 成果物の到達確認

| 項目 | 状態 |
|---|---|
| `third_party_snapshot/` | **5 ホスト**（Andrew / Bengio / efros / lecun / philip） |
| `transfer/t1b_filmonly_seed{42,123,456}/` | 到達済み（README.txt / control_result.json / injected_result.json） |
| `runindex/`（index 720 run / backlog B-24〜B-29） | 到達済み |
| `evidence/` | lecun には該当なし |

---

## 6. 未コミット変更の扱い

| ファイル | 扱い |
|---|---|
| `.claude/hooks/auto_notion_sync.log` | 指示通り `git restore` で破棄（merge 後は `.gitignore` 化され追跡対象外） |
| `docs/sync_instr09_lecun_2026-08-02.md` | **commit `2759a9b` として push**（追加指示による） |
| `experiments/transfer/_smoke_*` 3 件 | 除外規約該当。未追跡のまま維持 |
| `node_modules/` / `package*.json` | 未追跡のまま維持（`.gitignore` 追加は規約変更のため未実施） |

---

## 7. push について

fast-forward のためマージコミットは発生せず、**merge 単体では push 不要**だった。
`docs/sync_instr09_lecun_2026-08-02.md` のコミットに伴う push で、
FF により前進した 64 commit 分のブランチ ref も併せて更新されている
（内容はすべて origin に既存のもの）。

```
0f6b565..2759a9b  exp/lecun-wip-20260703 -> exp/lecun-wip-20260703
```

---

## 8. 規則の遵守状況

| 規則 | 状況 |
|---|---|
| `make runindex`（書き出し）を実行しない | ✅ 未実行（`runindex/` 差分 0 で実証）。`runindex-dry` も不要のため未実行 |
| `git pull` を使わない | ✅ `git fetch` → `git merge` に分離 |
| `git rebase` / `--force` / `reset --hard` を使わない | ✅ 未使用 |
| `phase0` に直接 push しない | ✅ push 先は `exp/lecun-wip-20260703` のみ |
| 衝突が出たらその場で解決せず報告する | ✅ untracked 衝突の時点で停止し、承認後に再開 |
| GPU に触れない | ✅ 実行中プロセス 0 |

---

## 関連ドキュメント

- `docs/sync_instr09_lecun_2026-08-02.md` — 指示書 #09（調査・third_party 保全・film 6 run 回収・
  `/tmp` 棚卸し）の実施記録。B-25 / B-29 の発見経緯と `init_mAP` の時期交絡の実測はそちらにある。
  本作業の要約は同ファイル §11 にも収録。
