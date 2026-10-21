# audit — T-2026-10-22-proposal-card-tower-reselect-search

ホスト dlsta（容器 `4f3861ae8d3b`、repo `/home/ubuntu/local/m2`）。2026-10-21 JST に実行。
scratchpad は repo の外（`/tmp/claude-1000/-home-ubuntu-local-m2/<session>/scratchpad`、以下 `$S`）。

## A. 開始状態

### A.0 手順書「0. 始める」

開始前の分岐は `feat/ptower-multigpu-syncbn`（清浄）。`feat/proposal-card-tower-reselect-search` は手元・遠隔とも無く、
`tasks/<task_id>` の履歴も無く、`.sync-pause` も無かった。

```
$ git fetch origin && python3 scripts/task_start_classify.py
[task-start] 分類（比較先 origin/phase0 7e30bdde）
[task-start]   追跡下の変更: 0 件
[task-start]   未追跡・起点に在り中身が同じ: 0 件（通す）
[task-start]   未追跡・起点に在り中身が違う: 0 件
[task-start]   未追跡・起点に無い: 0 件
[task-start]   無視・起点に在り中身が同じ: 0 件（通す）
[task-start]   無視・起点に在り中身が違う: 0 件
[task-start]   無視・起点に無い: 数えない（触れない）
[task-start] 分類: 通す

$ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-22-proposal-card-tower-reselect-search
[task-start] 分岐を作成: feat/proposal-card-tower-reselect-search（起点 origin/phase0）
[task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-10-22-proposal-card-tower-reselect-search END=complete）
OK   T-2026-10-22-proposal-card-tower-reselect-search
[task-start] 完了。分岐 feat/proposal-card-tower-reselect-search で契約 T-2026-10-22-proposal-card-tower-reselect-search の作業を開始できます
```

目印はこの契約が置いた（「作成」）。

### A.1 検証とプリフライト

```
$ make task-validate TASK=...      → OK（1 task(s), 0 failed）
$ make task-preflight TASK=...     → RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
  PASS: P1 venv_active, P6 decisions_answered, P7 destination_writable, P8 contract_valid, P9 spec_lint（規則 9 件・該当なし）, P10 preflight_names_known
  SKIP: P2 cuda_ext_loaded, P3 deterministic_flags, P11 gpu_free（宣言なし）, P4 P5 P13 P14（kind=impl）, P12（解決前提の参照なし）
```

### A.2 分岐・起点・作業ツリー

```
branch                     feat/proposal-card-tower-reselect-search
HEAD                       7e30bddeeae84fabea4e7237ec05a93f12f1c0db
origin/phase0              7e30bddeeae84fabea4e7237ec05a93f12f1c0db
merge-base HEAD phase0     7e30bddeeae84fabea4e7237ec05a93f12f1c0db
status --porcelain         ?? tasks/T-2026-10-22-.../{SPEC.md,critique_brief.md,proposal_card.md,spec.yaml}（契約のディレクトリだけ）
```

### A.3 docs/proposals/ の一覧と名前の確かめ

```
docs/proposals/2026-09-27-ptower-20.md   6954 bytes
docs/proposals/_template.md              2904 bytes
docs/proposals/briefs                    ls: No such file or directory
ABSENT docs/proposals/2026-10-21-tower-reselect-search.md
ABSENT docs/proposals/briefs/2026-10-21-tower-reselect-search-critique-brief.md
EXISTS docs/proposals/2026-09-27-ptower-20.md    ← 空振りでないことの確認（同じ命令で在る名前は EXISTS）
```

### A.4 試験の前の値（`PYTHONPATH=src python -m pytest tests -q -p no:cacheprovider -rfE`）

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
6 failed, 925 passed, 22 warnings in 70.95s
```

この試験は背景で回し、走っている間に Phase B の写しを置いた。`tests/` で `docs/proposals` を参照するのは
`tests/test_proposal_card_gate.py` だけで、参照は `_template.md` と固定の存在しない名前であり、置き場を走査しない（grep で確認）。

### A.5 追加ファイルの要約値（写す前）

```
671486dfd36f4b50ae5c322a1ada49de871edf3b5719c18fc1bb5321fb6049be  63215  tasks/.../proposal_card.md   （宣言と一致）
eef6a488028bc30cfecc3285713d9e57f3cb6e47c1a2e374f87f8cfecceb1ec5   5935  tasks/.../critique_brief.md  （宣言と一致）
```

## B. 配置

```
$ mkdir -p docs/proposals/briefs
$ cp tasks/.../proposal_card.md  docs/proposals/2026-10-21-tower-reselect-search.md
$ cp tasks/.../critique_brief.md docs/proposals/briefs/2026-10-21-tower-reselect-search-critique-brief.md
671486dfd36f4b50ae5c322a1ada49de871edf3b5719c18fc1bb5321fb6049be  63215  docs/proposals/2026-10-21-tower-reselect-search.md
eef6a488028bc30cfecc3285713d9e57f3cb6e47c1a2e374f87f8cfecceb1ec5   5935  docs/proposals/briefs/2026-10-21-tower-reselect-search-critique-brief.md
cmp（写す前と写した後）: 二つとも差なし（CMP_OK）
CR の数: 0 / 0。git check-attr -a: 属性なし（格納で改行が変換されない）
陽性対照: カードの写し（$S）の末尾に 'x' を 1 バイト足すと sha256 は cfe50dcc2a8a445ecc49028bdfe2dd1a0929434ed69f8806c31811f2d3525b53 に変わる。写しは消した
```

## C. 提案関門の検査（repo の根から実行）

```
C1 $ python tools/check_proposal.py docs/proposals/2026-10-21-tower-reselect-search.md
   規約から読んだ禁止語 15 語 / カード 16 件（数値必須 [5, 6, 10]）
   検出 0 件（禁止語 0 / 見出し欠落 0 / 数字欠落 0）  exit=0
   --json: status pass, hits 0, findings [], errors []

C2a 写し（$S/pc.ZffM/forbidden.md = カード + 末尾に「\n本命\n」）
   forbidden_word  .../forbidden.md:441  禁止語「本命」
   検出 1 件（禁止語 1 / 見出し欠落 0 / 数字欠落 0）  exit=1

C2b 写し（$S/pc.ZffM/noheading.md = 行「## 9. 最安の殺し実験」を消した。消えた行 1）
   missing_heading  .../noheading.md  カード #9（この案を殺せる最安の実験（GPU 一日以内））の見出しが無い
   検出 1 件（禁止語 0 / 見出し欠落 1 / 数字欠落 0）  exit=1
   写しの置き場 $S/pc.ZffM は検査の後に消した（removed: yes）

C3 陰性対照（同じカードの二度目）: 検出 0 件  exit=0
C4 既存のカード docs/proposals/2026-09-27-ptower-20.md: 検出 0 件  exit=0

C5 P14 の関数そのもの（tools/preflight_task.check_proposal_card、架空の task_id で completed/exempt を外す）
   intent.proposal_card = docs/proposals/2026-10-21-tower-reselect-search.md
     → PASS「検出 0 件（カード 16 件 / 禁止語 15 語を検査）」
   intent.proposal_card = docs/proposals/2026-10-21-tower-reselect-search-NOPE.md
     → FAIL「提案カードが無い」
```

### C.6 試験の後の値

```
6 failed, 925 passed, 22 warnings in 69.80s
失敗の名前の集合: A.4 と diff なし（SAME_FAIL_SET）
```

## D. 変更範囲と禁止領域

### D.1 forbidden-check

```
$ make forbidden-check（本体、起点 origin/phase0）
  status pass, changed 6, checked 6, violations []

陽性対照（本体の data/ に書かないため、$S に git clone した写しで行った）
  写し = 7e30bdde を checkout し、本体と同じ 6 件（二文書と契約のディレクトリ）を足したもの
  --base 7e30bdde: status pass, changed 6, violations []                         exit=0
  + data/_pc_control.txt: status fail, violations [data/_pc_control.txt「禁止領域 data/ の内側」] exit=1
  写しは消した（clone removed）
```

### D.2 参照の一致

```
git log -1 -- context/conventions.md = 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（契約の conventions_rev と一致）
git log -1 -- runindex/              = 63ae65da8c7d32df591f5e2ee4358286b72c726b（created_from.runindex_commit と一致）
runindex の行数（見出しを除く）: index 1961 / experiments 750 / verdicts 1506（counts と一致）
```

### D.3 追跡される変更の集合（commit の後に測る。下の「送出」に追記）

## 解決された参照（`contract.inject_verbatim` の原文）

`context/conventions.md`（`2d946b07`）の該当アンカーを、`sed` で切り出してそのまま下に置く。要約しない。

### conventions#prohibitions（98〜108 行）

````markdown
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

````

### conventions#issuer_cautions（154〜192 行）

````markdown
<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

````

### conventions#proposal_gate（193〜296 行）

````markdown
<a id="proposal_gate"></a>
## proposal_gate

手法・結合・補助信号・修正案の提案は、本節の関門を通ったものだけを契約に落とす。
関門は四つ。提案カードの充足／禁止語の不在／失敗時手順の履行／引用の照合。

### 提案カード（全項目が埋まるまで推奨を書かない）

| # | 項目 | 空欄を許す条件 |
|---|---|---|
| 1 | 問い。yes/no で答えが出る一文 | 許さない |
| 2 | 最も近い先行研究三件。著者・年・DOI か arXiv ID・設定・報告された効果量 | 三件未満なら「探して見つからなかった」と検索語を書く |
| 3 | 先行研究がこれをやらなかった／効かなかった理由の推定 | 許さない |
| 4 | 否定的な先行研究二件（効かなかった、負の転移の報告） | 同上の「探して見つからなかった」 |
| 5 | 期待効果量（点）。#2 のどの値から外挿したか | 許さない |
| 6 | 成功確率（主観。0.0 から 1.0） | 許さない |
| 7 | 成功の閾値（主判定規則で書く） | 許さない |
| 8 | 失敗の閾値と、失敗時に捨てるもの（案／設計／問い のどれか） | 許さない |
| 9 | この案を殺せる最安の実験（GPU 一日以内） | 無いなら「無い」と理由 |
| 10 | 費用（run 本数 × 時間） | 許さない |
| 11 | この案の結果でどの判断（関門・分岐）が変わるか | 変わらないなら提案しない |
| 12 | 最も近い既存研究との差分一文 | 許さない |
| 13 | F の「却下」「予測外れ」と同型でないことの宣言。読んだ行の id | 許さない |
| 14 | 初回にセットで試す設定の掃引集合。掃引する主要因、固定する交互作用、固定の理由 | 許さない |
| 15 | この比較で揃えるべき条件の一覧と、両腕の実測値。conventions#symmetry の表の様式。UNKNOWN は先に測る | 許さない |
| 16 | 差を仮説の効果と読むために排除済みの交絡の一覧。排除していない交絡があれば、その影響の向き | 許さない |

#5 #6 #10 は数値で書く。#10 は #14 の掃引集合全体で見積もる。
#11 が空なら、新規性の有無によらず提案から外す。

#15 の表に UNKNOWN が残る提案は、契約にせず先に調査契約を出す。

### 禁止語（提案と契約の本文。完全一致で検査する）

最大の新規性／世界初／画期的／有望／筋が良い／本命／未踏／空白／決定的／確実に効く／
明らかに／大幅／劇的／必ず改善／唯一の

「未踏」「空白」を使う場合は禁止を解かず、「空白である理由の仮説（技術的困難／価値が無い／偶然）」を
添えた別の語で書く。形容詞の代わりに #5 #6 #10 の三数値を併記する。

### 設定・設計・問いの三水準

| 水準 | 含むもの | 変えるときの手続き |
|---|---|---|
| 設定 | 学習率・epoch・batch・seed、特徴の取り出し層、豊かさ L0 から L3、学習範囲 W1/W2、損失の重み、送り手の掃引点 | 初回の契約に掃引として入れる。後から足さない |
| 設計 | 界面の型、塔の選択、方向、信号の種類、時間文脈の与え方 | 提案カードを書き直し、批判会話を通す |
| 問い | どの仮説を測るか、相互改善の定義、論文の段 | 利用者が決める。関門で扱う |

設定の掃引は初回にセットで試す。主要因は掃引し、交互作用は固定する。
何を固定したかと理由をカード #14 に書く。掃引集合はカードに書いた時点で固定する
（最良格子の選定は折り内 val、test は腕ごとに一度。conventions#split の規則に従う）。

### 失敗時手順（修正案を書く前に、この順で書く）

1. 失敗の定義は初回の契約にある閾値による。掃引のどの格子でも閾値に届かなければ、
   その設計の失敗である。格子を足すことは修正ではない
2. 原因候補を五区分で列挙する。測定器（eval・split・seed）／データ（ラベル・分布）／
   モデル・実装／仮説そのもの／問いの立て方
3. 区分ごとに識別実験を一つ書く（どの結果が出ればその区分だと分かるか）
4. 識別実験の結果で修正の水準を決める。測定器・データ・実装が原因なら、それを直して
   同じ設計を測り直す（設計は変えない）。仮説・問いが原因なら、設計か問いを変える
5. 設定水準の修正は選べない。例外は、初回に入れなかった設定があり、入れなかった理由が
   契約に書いてある場合のみ。その場合も後から足さず、掃引を再設計して一括で出す
6. 修正案に提案カードを付ける。設計変更一回の費用を #10 に含める

### 引用規約

- DOI か arXiv ID の無い引用は引用として扱わない
- 引用は機械で存在照合する。照合の出力を証跡に残す
- 数値つきで引く。「改善した」ではなく「指標・値・表番号・設定」
- 設定の違い（データセット・タスク粒度・入力）を必ず書く。「文献に数値がある」を「効く」と読み替えない
- 反証を先に探す。検索語・件数・見つかった否定例を記録する

### 役割分離

| 役割 | 会話 | 出力 | 禁止 |
|---|---|---|---|
| 生成 | 別会話（プロジェクトの外）。証拠地図・カードの雛形・依頼文だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |
| 批判 | 別会話。カードだけを渡す | 却下表と順位。順位は期待情報量（#11）で付ける | 生成側の推奨文を読む |
| 判定 | 利用者 | 決定。F に一行 | — |
| 起票 | 別会話 | 契約 | 手法の変更 |

生成と批判を同じ会話で行わない。批判は「やらない理由」から書く。

### 置き場と参照（2026-09-23 追加）

- 提案カードは docs/proposals/YYYY-MM-DD-slug.md に置き、tools/check_proposal.py を通す
- 生成会話は候補を三案以上出す
- 批判会話は web 検索を必須とし、検索語と件数と見つかった否定例を却下表に書く
- exp 契約は spec.yaml の intent.proposal_card にカードの経路を書く。L3 の P14 が、カードの実在と検査の通過を確かめる。
  無い exp は起動できない
- 導入前の契約（T-2026-09-19-stage1-detector-towers-r2、T-2026-09-19-stage1-phase-tower-r3）は例外。三件目を足すときは本節を改訂する

### 生成会話への依頼文（2026-10-19 追加）

- 書いてよいものは二つ。F で状態が「有効」の決定の結論（行の日付を付ける）と、M の問い・判定規則。
- 書かないものは次のとおり。実測値、実装の状態、決定の理由のうち実装や実測に触れる部分、旧カード、報告者の解釈。
- 決定ごとに、どこまで縛るかを書く。カードの候補として開いているものも書く。
- 依頼文は渡す直前に F を読み直して、一から書く。前の依頼文を直して使わない。
- 依頼文は docs/proposals/briefs/ に置き、カードから参照する。
- 生成会話は、カード #10（費用）と #15（両腕の実測値）を UNKNOWN と書く。起票者が repo の実測で埋めてから批判会話へ回す。

---

````
