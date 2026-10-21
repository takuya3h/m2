# RESULT — T-2026-10-21-ops-taskstart-resume-folds-val

実行ホスト andrew（利用者の決定 2026-10-21）、分岐 `feat/ops-taskstart-resume-folds-val`、起点 `origin/phase0` = `3cb3db07`。GPU 不使用。
命令と出力、要約値の前後、対照の出力は `audit.md`（以下 A§ で節を指す）。

## 1. 解決された参照

- `inputs.denominator` / `frozen_source`: 無し。`inputs.sigma_policy`: 省略（本契約は数値の判定を持たない）
- `inputs.data.split_files: data/splits/ego_val.txt`: schema の必須項目として置かれたもの。**参照しなかった**
- `contract.conventions_rev` `5c0eaeeb` と `runindex_commit` `63ae65da`、行数 1961 / 750 / 1506 は実測と一致（A§A）。`meta.amendments` は足していない
- `contract.inject_verbatim` の原文（起票時の版 `5c0eaeeb`。folds は本契約が小節を足す前の版）:

#### conventions#prohibitions（`5c0eaeeb` の原文）

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

#### conventions#issuer_cautions（`5c0eaeeb` の原文）

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

#### conventions#folds（`5c0eaeeb` の原文）

    <a id="folds"></a>
    ## folds

    動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
    本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。

    | 折り | test（3） | val（2） |
    |---|---|---|
    | A | 04, 05, 07 | 09, 10 |
    | B | 01, 03, 14 | 02, 08 |
    | C | 02, 08, 11 | 06, 12 |
    | D | 06, 13, 15 | 04, 05 |
    | E | 09, 10, 12 | 07, 15 |

    train はその折りの test と val を除いた 10 本である。
    **折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
    各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。

    ### 追加 6 動画

    工程の注釈がある追加動画は次の 6 本である。

        17, 18, 19, 20, 21, 22

    **22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
    旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
    出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
    `tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。

    **用途は訓練のみである。どの折りの test にも val にも現れない。**
    15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。

    ### 規律

    **選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
    test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。

    出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。

    ---

## 2. 判定

**verdict: pass。** G1 pass（A§A）、G2 pass（A§B）、G3 pass（A§E）。

## 3. 完了判定

| # | 実測 |
|---|---|
| a | 分岐 `feat/…`・起点 3cb3db07・目印は開始前から在りこの契約の所有の記録。除外の一覧 15 行。無視された未追跡のうち phase0 に同じ経路が在るもの **0 件（同じ 0・違う 0）**、二方法で一致。対照の場で同じ 1・違う 1・無い 0 と数えた（A§A） |
| b | §5.1 の 7 行すべてに陽性と陰性の試験。通した場合は中身と inode が前後で同じ、止めた場合は作業ツリー・索引・除外・分岐・目印の要約値が前後で同じ（`tests/test_task_start_classify.py`、A§B）。直す前の版で §3.2 の 2・3 行目を再現、1 行目は git で再現 |
| c | 通した後に取り込みを失敗させても、切り替えが拒まれても、状態の要約値が前後で同じ。巻き戻しから「索引から外す」を除いた写しでは、通した 2 ファイルが消え試験が差を検出（A§B） |
| d | 「0. 始める」は `scripts/task_start_classify.py` を呼ぶ（task-start と同じファイル）。無視の一覧に足してよいのは phase0 に無いと出た経路だけと書いた。`.codex/skills/task` はシンボリックリンクで要約値は両経路とも `038a5d71…`（A§C） |
| e | 未統合の stop の契約で P13 FAIL・P14 FAIL・allow_write 検出。統合済みとみなすと三つとも対象外。phase0 の上の完了済みは前後 128 件・差 0 件（A§D） |
| f | 解決しない参照で印だけの判定（`["stop"]`）に戻り、警告は二回呼んで一行（A§D） |
| g | folds に小節、変更履歴に 1 行（4e67202c）。変わった節は folds と naming だけ、アンカー 15 個すべて解決。対応と 5 本の識別子と本数は表と一致。写しの prohibitions を一文字変えると「変わった」に出る（A§E） |
| h | 2 件を型・出所（行番号つき）・対処つきで追加、消えた行 0 件（A§F） |
| i | 装置: 開始と終了とも compute apps 0 件。data への書き込み 0（forbidden-check pass、data を含む写しで fail）。接続は ls-remote・push・PR・task-report だけ。試験の失敗の集合は 6 件のまま（894 → 917 件）（A§G） |
| j | PR #247。実測 `gh pr view`: number 247、isDraft false、baseRefName phase0、headRefName feat/ops-taskstart-resume-folds-val、state OPEN |

## 4. 実測（次の契約で使う値）

- **task-start の出力の形**: `[task-start] 分類（比較先 origin/phase0 <短い hash>）` に続き、6 分類の件数を一行ずつ（`<分類>: N 件`、通す分類は「（通す）」つき）、
  「無視・起点に無い: 数えない（触れない）」、止めるときは `止めた理由 [<分類>] <経路>` を一行ずつと無視の一覧の案内、最後に `分類: 通す` か `分類: 止める`。
  読み取りだけで出すには `git fetch origin && python3 scripts/task_start_classify.py`（終了コード 0 通す / 3 止める / 4 照会の失敗）
- **通し方**: 通す経路は切り替えの前に索引へ載せる（書き直されない）。巻き戻しは索引から外してから `read-tree -m -u` で元の木へ（`git checkout` では無視されたものが消える）
- **完了済みの新しい定義**: `gates[].verdict` に空でない値があり、かつ `tasks/<id>/result.yaml` が `origin/phase0` の木に在る。参照が解決しなければ印だけで判定し、警告を一行
- **andrew の無視されたファイル**: phase0 に同じ経路が在るもの 0 件。除外の一覧 15 行（うち 3 行は 2026-10-21 起動前に利用者が足した）。README は skip-worktree の印つき
- **規約の新しい小節**: `context/conventions.md` の folds 節、「規律」の後の `### val と test の重なり`
- 分類の所要時間: andrew の実物で 0.41 秒（木 22,801 件）

## 5. 起票者の誤り

1. asserted_without_measuring — Task B-7 は §3.2 の三つの振る舞いを「直す前の task-start で」再現せよとしたが、1 行目（無視されていない未追跡）は直す前の版がその前の汚れの判定で終了コード 3 になり、切り替えに届かない。git そのもので再現した
2. asserted_without_measuring — §3.1 と Task C-4 は `.claude/skills/task/SKILL.md` と `.codex/skills/task/SKILL.md` を「二つの写し」として同じにせよとしたが、`.codex/skills/task` は `.claude/skills/task` へのシンボリックリンクで実体は一つ。写す操作は同じファイルへの複写になる

## 6. 逸脱

- 利用者は起動時に「SPEC の bengio はすべて andrew と読み替える」と指示したが、取り込んだ SPEC はすでに実行ホストを andrew と書いていた。bengio の語は §1 と §10 の事実の記述だけで、読み替えた箇所は無い
- 2 回目の `/task` は「再開」から始まった（task-start は利用者が実行）。作業ツリーの未追跡は契約自身の `SPEC.md`・`spec.yaml` だけだったため、これを最初に commit して G1 の「清浄」を満たした
- 「無視・起点に無い」は件数を出さない。B-5 は分類ごとの件数を求めるが、数えるには無視されたファイルを全数列挙する必要があり、§5.1 の「突き合わせてから比べる」と両立しない
- `tests/test_task_start_pause_owner.py` の場に分類器の写しを 1 行足した（主張は無変更）。D-3 が名指ししていない `tests/test_proposal_card_gate.py` の場にも、P14 の完了済みの扱いのため同じ差し替えを足した
- 変更履歴の commit 欄は、小節を置いた commit（4e67202c）を書き、行そのものは次の commit（2d946b07）で足した
- 巻き戻しの手段は、助言者の案（戻した後に phase0 の版で作り直す）を採らず、索引に載せて外す方式にした。作り直す方式は一時的に削除が起き、同期で他の台へ伝わりうるため

## 7. 想定外・UNKNOWN

- dlsta・bengio など他の台での分類の所要時間と git の版は UNKNOWN（andrew は git 2.43.0。`--pathspec-from-file` は 2.26 以上を要する）
- skip-worktree の印つきで変更のあるファイル（andrew の README）は `git status` に出ず、新しい分類でも数えない（§5.1 の外）。phase0 がその経路を変えると切り替えが拒まれ、終了コード 4 で巻き戻る（試験で確認）
- 各ホストの task-start とスキルは、居る分岐に本契約が統合されるまで旧い版のまま動く

## 8. 送出

- PR #247（https://github.com/takuya3h/m2/pull/247）、Draft でない
- `make task-report`（16:42）: rc 0、verdict pass、n_issuer_defects 2、report_bytes 13118、replaced_blocks 0
