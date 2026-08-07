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

## 契約の受け取り

外部で起票された契約は次の一操作で取り込む。

    make task-fetch SRC=<path or url>

取得、展開、L1 と L2 の検証までを行う。検証に失敗した場合は展開を巻き戻すため、
`tasks/` に不完全な契約が残らない。成功した場合のみ次の操作が表示される。

入力は区切り付きテキスト（バンドル）。先頭行が形式と区切りを宣言し、
`spec.yaml` と `SPEC.md`（`kind: exp` では `prereg.md` も）を 1 ファイルへまとめる。

    #!TASK-BUNDLE v1 delim=<40 文字以上の区切り>
    <delim> FILE spec.yaml
    ...
    <delim> FILE SPEC.md
    ...
    <delim> END

区切りが本文と衝突した入力は受け付けずに失敗する。既存の契約から組み立て直すには
`python tools/fetch_task.py --pack tasks/<task_id>` を使う。

## 検証

    make task-validate                  # tasks/ 配下すべて
    make task-validate TASK=<task_id>   # 1 件だけ
    make task-preflight TASK=<task_id>  # 実行直前（L3）

検証は 3 層。いずれも機械検証であり、散文による判断は含まない。

| 層 | 内容 | 依存 | 所要 |
|---|---|---|---|
| L1 | スキーマ・書式・パイプ混入・task_id とディレクトリ名の一致 | なし | 1 秒 |
| L2 | 参照解決（分母・凍結源・split・規約版・sigma_policy 継承）と task_id の重複 | runindex, git | 数秒 |
| L3 | 実行直前（venv・拡張・prereg 時刻・凍結源・decisions・書き込み権限） | 実行環境 | 数秒 |

L1・L2 は GPU 不要。起票直後に回すこと。
L3 は実行環境そのものを検査するため、**実行するホストで、実行する直前に**回すこと。

### L3 の PASS と SKIP は違う

`make task-preflight` は各検査を `PASS` / `SKIP` / `FAIL` のいずれかで報告する。

| 状態 | 意味 |
|---|---|
| `PASS` | 検査を実行し、合格した |
| `SKIP` | **検査を実行していない。** 契約に列挙されていないか、その kind の対象外か、判定基準が未確定 |
| `FAIL` | 検査を実行し、不合格だった |

**`SKIP` を「合格」と読んではならない。** 終了コードは `FAIL` が 1 件でもあれば非ゼロ、
`SKIP` は終了コードを変えない。どの検査がどの条件で実行されるかは
`tools/preflight_task.py` の適用規則が決める（契約の `meta.kind` と
`plan.env.preflight` の記載に従う）。

`make` はレシピ失敗時に自身の終了コード 2 を返す。検査器そのものの終了コード
（`FAIL` があれば 1）を見たい場合は `python tools/preflight_task.py --task <task_id>`
を直接実行する。

## task_id の重複検出の範囲

L2-1 は `refs/remotes/origin` 配下の各 ref にある `spec.yaml` を読み、
`meta.created_at` が食い違う場合のみ衝突とみなす。
squash merge や rebase merge で同じ task が複数 ref に現れるのは正常なので発火しない。

**限界**: 衝突しているブランチを fetch していないホストでは検出できない。
検出は fetch 済みの範囲に限られる。偽陽性を避けるための意図的な設計である。

## prompts/ との関係

`prompts/` は**型テンプレート専用**として残す。既存の指示書は移設しない（履歴が壊れるため）。
新規の作業依頼は `tasks/` に起票する。

## ホスト環境の既知差

修正対象ではない。指示書を書くときに前提としないための記録。

| ホスト | 差分 | 影響 |
|---|---|---|
| efros | repo パスが他ホストの標準と異なる | ホスト横断スクリプトでパスを決め打ちすると失敗する。実行時に確認すること |

凍結源 ckpt は 2026-08-06 時点で 11 ホスト中 11 ホストに存在し、SHA-256 は全一致。
mtime もナノ秒まで同一である。`third_party/` は git の追跡対象外だが、実体は
ホスト間で同期されている。「git 追跡外イコール同期外」と仮定してはならない。
