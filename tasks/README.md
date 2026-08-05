# tasks/ — TASK 契約

Claude アプリ等で起票された作業依頼を、機械検証可能な契約として置く場所。

## ディレクトリ

    tasks/<task_id>/
    ├── spec.yaml    機械可読の契約（検証対象）
    ├── SPEC.md      人が読む本文
    ├── prereg.md    kind=exp のみ。学習開始より前に commit する
    └── RESULT.md    CLI が埋めて返す

## task_id

書式: `T-YYYY-MM-DD-<slug>`

連番は使わない。11 サーバ・13 ブランチで並行起票されるため、連番は必ず衝突する
（backlog B-30〜B-32 が実例）。日付と slug なら採番のために全ブランチを走査する必要がない。

slug は英小文字・数字・ハイフンのみ。3〜60 文字。

## 中核の原則

1. **参照 > 逐語** — 分母の数値や規約の原文を spec.yaml に書かない。参照 ID だけを書き、
   CLI が実行直前に repo から解決する。書いた瞬間に古くなる問題を構造的に消す。
2. **名前空間必須** — `exp:transfer/s4_base_tecno` のように書く。裸の名前は reject する
   （backlog B-34 の ledger_key 名前空間衝突と同型の事故を防ぐ）。
3. **検証できない項目は載せない** — 各フィールドには検証方法が定義されている。
4. **commit 後は不変** — 変更は `meta.amendments` に追記する。上書きしない。
5. **判断は載せず、要求として載せる** — CLI が決めてはいけないことは
   `governance.decisions_required` に置く。未回答なら実行を止める。

## 検証

    make task-validate                 # tasks/ 配下すべて
    make task-validate TASK=<task_id>  # 1 件だけ

検証は 3 層。

| 層 | 内容 | 依存 | 所要 |
|---|---|---|---|
| L1 | スキーマ・書式・パイプ混入・task_id 一意 | なし | 1 秒 |
| L2 | 参照解決（分母・凍結源・split・規約版・sigma_policy 継承） | runindex | 数秒 |
| L3 | 実行直前（venv・CUDA 拡張・prereg commit 時刻・decisions 回答） | GPU ホスト | 数十秒 |

L1・L2 は GPU 不要。起票直後に回すこと。

## prompts/ との関係

`prompts/` は**型テンプレート専用**として残す。既存の指示書は移設しない（履歴が壊れるため）。
新規の作業依頼は `tasks/` に起票する。
