# <title>

**task_id:** <task_id>  **kind:** <kind>

## 背景

## 手順

（Task 単位・各 Step は 2〜5 分の 1 アクション。コードを書く Step にはコードを載せる）

## 完了判定

（spec.yaml の outputs.acceptance と一致させること）

**禁止領域に触れていないことは `make forbidden-check` で確かめる。**
契約ごとに検査の命令を書かない。生成物は禁止領域の内側にあるため、素朴に
「差分が空であること」を求めると生成と両立しない（道具は生成物を除外する）。
生成物への手編集は `make taskindex-check` と `make inbox-check` が捕まえる。

## 報告

`RESULT.md` を埋めて commit すること。deviations は必須。
