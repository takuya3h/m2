# 定位置分岐の移行計画

## 対応表

| ホスト | 現在 | 移行後 |
|---|---|---|
| lecun | 作業分岐に滞留 | `exp/lecun` |
| philip | 未確認 | `exp/philip` |
| ilya | 作業分岐に滞留 | `exp/ilya` |
| bengio | `exp/Bengio-wip-20260703` | `exp/bengio` |
| andrew | `exp/Andrew-wip-20260703` | `exp/andrew` |
| he | `exp/he-wip-20260804` | `exp/he` |
| adam | `exp/adam-wip-20260804` | `exp/adam` |
| hinton | `exp/hinton-wip-20260804` | `exp/hinton` |
| ian | `exp/ian-wip-20260804` | `exp/ian` |
| dlsta | `exp/dlstation-wip-20260804` | `exp/dlsta` |
| efros | `exp/efros-wip-20260703` | `exp/efros` |

`philip` の現在値は未測定なので `UNKNOWN` として扱い、到達できるまで実施しない。

## 実施の順序

1. 本 task を `phase0` へ統合する。
2. 全ホストへ script と手順書が行き渡ったことを確認する。
3. 作業分岐に滞留しているホストは、先に作業を統合するか退避する。
4. 1 台で `--dry-run` を行い、表示順が remote 作成、remote-tracking ref 確認、local rename であることを確認する。
5. 同じ 1 台で実移行し、送出、Draft PR、自動同期が働くことを確認する。
6. 残りの到達可能なホストで実施する。
7. 全ホストで働くことを確認したあとに、古い遠隔参照の扱いを別途判断する。

## ホストごとのコマンド

作業ツリーを clean にしてから、対象ホストの論理名を渡す。

```bash
bash scripts/sync/rename_host_branch.sh --dry-run <logical-host>
bash scripts/sync/rename_host_branch.sh <logical-host>
```

helper は新しい `origin/exp/<logical-host>` を先に作り、remote-tracking ref の存在を確認してから local branch を改名する。旧 remote ref を削除しない。

## 注意

- 到達できないホストは実施を保留する。
- 作業ツリーが汚れているホストは、先に commit または stash する。
- 古い遠隔参照は当面残す。
- 大文字小文字だけが異なる改名では、helper が `exp/<logical-host>-case-rename-tmp` という一時 local branch を経由する。remote ref は最初から最終名で作る。
- `lecun` と `ilya` は滞留作業を先に処置し、`philip` は現在分岐を実測してから実施する。
- 本 task では各ホストの切替を実行しない。
