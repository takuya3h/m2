# audit — T-2026-09-16-proposal-gate

命令と出力の全文。`RESULT.md` はここを行番号で指す。
時刻は JST。対話シェルは zsh。履歴を読む操作は `git --no-pager` を使った。

## 0. 取り込みと事前検査

### 0.1 契約の取り込み（task-start）

    $ cd /home/ubuntu/slocal/m2 && source .venv/bin/activate && source scripts/load_env.sh \
        && make task-start TASK=T-2026-09-16-proposal-gate
    [load_env] .env をロード（WANDB_API_KEY=set / NOTION_API_KEY=set）
    [task-start] git fetch origin
    [task-start] 分岐を作成: feat/proposal-gate（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら rm -f .sync-pause）
    [task-start] 契約を取り込みます: T-2026-09-16-proposal-gate
    OK   T-2026-09-16-proposal-gate
    1 task(s), 0 failed
    取り込みました: tasks/T-2026-09-16-proposal-gate

### 0.2 自動同期の抑止が効くことの確認

    $ grep -c sync-pause ~/bin/m2-sync.sh
    2
    $ ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Sep 16 14:25 .sync-pause

稼働中の版は抑止に対応している（0 なら未対応）。目印は task-start が置いた。

### 0.3 L1 + L2（取り込み直後）

    $ make task-validate TASK=T-2026-09-16-proposal-gate
    OK   T-2026-09-16-proposal-gate
    1 task(s), 0 failed

WARN は出ていない。`contract.conventions_rev` が差し替え前
（`REPLACE-BY-EXECUTOR-with-measured-rev`）のため、L2-6 の照合は
`git diff <rev>..HEAD` が解決に失敗して沈黙する。差し替え後に測り直す（6.2）。

### 0.4 L3 プリフライト

    $ make task-preflight TASK=T-2026-09-16-proposal-gate
    P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal/m2/.venv sys.prefix=/home/ubuntu/slocal/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS docs/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
    P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
    P12 refs_resolved          SKIP 解決前提の参照は無い

    RESULT: 6 PASS / 0 WARN / 6 SKIP / 0 FAIL

SKIP 6 件（P2 P3 P4 P5 P11 P12）。SKIP は合格ではなく「実行されなかった」。
本契約は GPU を使わず kind=impl で解決前提の参照も持たないため、いずれも対象外。

## 1. Task A — 開始状態の記録

### 1.1 A-1 作業ツリー

    $ git status --short
    ?? .sync-pause.released
    ?? docs/sessions/digest/2026-08-29-23fa444b-1ed7-4ec8-9280-bf8158c61e16.md

開始前から在る未追跡が 2 件あった。**消さず、移動で退避した。**

    $ git stash push -u -m "pre-T-2026-09-16-proposal-gate: released pause marker + session digest"
    Saved working directory and index state On feat/notion-retire-scripts-and-speccheck: ...
    $ git stash list | head -1
    stash@{0}: On feat/notion-retire-scripts-and-speccheck: pre-T-2026-09-16-proposal-gate: ...

退避先: `stash@{0}`（`git stash pop` で戻る）。件数: 2。
内訳: `.sync-pause.released`（0 バイト、前契約の解除済み目印）、
`docs/sessions/digest/2026-08-29-23fa444b-....md`（277 行、前セッションの機械抽出記録）。

退避後の作業ツリー:

    $ git status --short
    ?? tasks/T-2026-09-16-proposal-gate/

残る未追跡は task-start が置いた本契約そのものだけ。清浄と判定した。

### 1.2 A-2 conventions.md のアンカー

抽出規則は実装から取った（`tools/validate_task.py:34`）。

    _ANCHOR_RE = re.compile(r'<a id="([a-z0-9_]+)"></a>')

    $ grep -oP '<a id="\K[a-z0-9_]+(?="></a>)' context/conventions.md | nl
         1	split
         2	eval_recipe
         3	frozen_source
         4	sigma
         5	prohibitions
         6	env_p0
         7	naming
         8	issuer_cautions
    $ grep -cP '<a id="[a-z0-9_]+"></a>' context/conventions.md
    8

**変更前のアンカー数: 8。** Task B の後に 9 になることを確かめる（A-2 の対）。

### 1.3 A-3 spec-check の規則数（実装を読んで数えた）

数え方: `tools/check_spec.py` の `RULES` タプルの要素数。
検査器はこの長さを `rules_checked` として出力する（`tools/check_spec.py:498`）ため、
タプルの要素数が規則数の定義である。

    $ sed -n '447,456p' tools/check_spec.py
    RULES = (
        rule_truncation_in_measurement,
        rule_unquoted_glob,
        rule_separated_source,
        rule_forbidden_vs_output,
        rule_host_mismatch,
        rule_integration_prohibited_without_pause,
        rule_gate_requires_report_before_end,
        rule_reverify_contradiction,
    )

**変更前の規則数: 8。** P9 の出力「規則 8 件を検査し該当なし」と一致する（独立な二経路）。

注: アンカー数も 8 で同値だが無関係である。両者を取り違えない。

### 1.4 A-4 変更前の試験の失敗件数

比較を成立させるため、変更後もこの同じ命令で測る。

    $ source .venv/bin/activate && pytest tests/ -q -p no:cacheprovider
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics - Ass...
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name - AssertionEr...
    FAILED tests/test_research_logger.py::test_log_run_idempotent - AssertionErro...
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    6 failed, 509 passed, 22 warnings in 30.85s
    exit=1

**変更前: 6 failed / 509 passed。** 6 件は本契約の着手前から落ちている。
完了判定 f は「変更前に失敗していた試験の件数が増えていない」であり、
6 件を直すことは求めていない（本契約の範囲外）。

### 1.5 A-5 conventions_rev と runindex_commit の実測

測り方は実装から取った。L2-6 は次を実行する（`tools/validate_task.py:443`）。

    git diff --name-only {revision}..HEAD -- context/conventions.md

すなわち `conventions_rev` は git の版（commit）であり、
`context/conventions.md` を最後に変えた commit を書くのが実装の前提である。

    $ git --no-pager log -1 --format='%h %ad %s' --date=iso -- context/conventions.md
    a8c07e81 2026-08-25 15:30:37 +0000 feat(context): move issuer references into version control and inject the cautions
    $ git --no-pager log -1 --format='%h %ad %s' --date=iso -- runindex/
    96eb3a1c 2026-08-30 10:26:08 +0000 exp(pd-b2-b4): build the detector env on lecun and close the remaining direction of G0

測り方の検証（空振りでないことの確認）: 直前の三契約が記録している値と照合した。

    tasks/T-2026-08-31-notion-repo-followup-and-retire  runindex_commit 96eb3a1c / conventions_rev a8c07e81
    tasks/T-2026-09-01-notion-retire-scripts-and-speccheck  runindex_commit 96eb3a1c / conventions_rev a8c07e81
    tasks/T-2026-08-29-lecun-detector-env-pd  runindex_commit 09fdefb3 / conventions_rev a8c07e81

同じ測り方で同じ値が出た。別々の実行者が別の日に書いた値と一致するため、
測り方はこの repo の慣行と同じである。

差し替えた値:

    meta.created_from.runindex_commit: REPLACE-BY-EXECUTOR-with-measured-runindex-commit → 96eb3a1c
    contract.conventions_rev:          REPLACE-BY-EXECUTOR-with-measured-rev            → a8c07e81

`meta.created_from.counts` は差し替えの対象に含まれていない（Task A-5 が挙げるのは
二つだけ）ため触っていない。本契約は `inputs.denominator` を持たないため
L2-8（母集団の移動）は原理的に沈黙する（`tools/validate_task.py:459`）。

## 2. Task B — conventions.md に proposal_gate 節を置く

### 2.1 置いた場所と方法

付録 A を手で書き写さず、SPEC.md から機械で取り出した。**転記の誤りを入れないため。**
付録 A は SPEC.md の 139〜219 行で、全行が 4 字下げか空行であることを先に確かめた。

    $ sed -n '224,309p' ... と同じ要領で
    $ sed -n '139,219p' tasks/T-2026-09-16-proposal-gate/SPEC.md | sed 's/^    //' > appendix_a.txt
    $ grep -vn '^    ' <対象> | grep -v '^[0-9]*:$'
    （出力なし = 下げ幅の例外が無い）

一行目のアンカー表記を、既存節と同じ HTML の形へ置き換えた。形は
`tools/validate_task.py:34` の `_ANCHOR_RE` に合わせた。

    $ sed 's|^(aタグ) id="proposal_gate"$|<a id="proposal_gate"></a>|' appendix_a.txt
    $ grep -c '<a id="proposal_gate"></a>' appendix_a_fixed.txt
    1
    $ grep -c 'aタグ' appendix_a_fixed.txt
    0

`issuer_cautions` の後（ファイル末尾）へ追記した。

    $ cat appendix_a_fixed.txt >> context/conventions.md

### 2.2 アンカー数が一つ増えたこと（B-3）

    $ grep -cP '<a id="[a-z0-9_]+"></a>' context/conventions.md
    9
    $ grep -oP '<a id="\K[a-z0-9_]+(?="></a>)' context/conventions.md | tr '\n' ' '
    split eval_recipe frozen_source sigma prohibitions env_p0 naming issuer_cautions proposal_gate

**8 → 9。** 増えたのは `proposal_gate` だけである。

### 2.3 既存節の本文を変えていないことの確認

行数は 178 → 259。追記だけなら先頭 178 行は元のままのはずである。

    $ diff <(head -178 context/conventions.md) conventions_before.md
    （差分なし）

commit の統計でも確かめた。**81 行の挿入、0 行の削除。**

    context/conventions.md | 81 ++++++++

### 2.4 変更履歴への一行追加（B-2）

commit を推測で書かないため、本体を先に commit してから足した。

    $ git --no-pager log -1 --format='%h %s'
    6c95e4f1 feat(proposal-gate): add the proposal gate convention, the procedure doc and a static checker

挿入位置は既存の最終行の直後。**位置が一意であることを表明で確かめてから入れた**
（`assert len(idx) == 1`）。

    | 2026-09-16 | 6c95e4f | proposal_gate 節を追加。提案カード 14 項目・禁止語・設定/設計/問いの三水準・失敗時手順・引用規約・役割分離を定義。静的検査は tools/check_proposal.py、手順は docs/proposal-gate.md |

    $ git --no-pager diff --stat context/conventions.md
     context/conventions.md | 1 +
     1 file changed, 1 insertion(+)

**1 行の挿入のみ。** 既存行には触れていない。

なお表には `a8c07e81`（2026-08-25、`issuer_cautions` 節の追加）の行が欠けている。
既存の漏れだが、禁止事項 2「既存節の本文を変えない」を守るため足していない。

## 3. Task C — docs/proposal-gate.md を置く

付録 B（SPEC.md 224〜309 行）も機械で取り出した。全行が 4 字下げか空行であること、
三連バッククォートと山括弧を含まないことを先に確かめた。

    $ sed -n '224,309p' SPEC.md | grep -n '^.' | grep -v '^[0-9]*:    '
    （出力なし = 下げ幅の例外が無い）
    $ sed -n '224,309p' SPEC.md | grep -n '```\|<\|>'
    （出力なし = 禁止した記号が無い）

    $ sed -n '224,309p' SPEC.md | sed 's/^    //' | sed '/./,$!d' > docs/proposal-gate.md
    $ wc -l < docs/proposal-gate.md
    85
    $ grep -n '^#' docs/proposal-gate.md
    1:# 提案関門（proposal gate）
    6:## B.1 なぜ要るか
    20:## B.2 AI 提案者の癖（抑える対象）
    31:## B.3 問いから契約までの流れ
    47:## B.4 順位の付け方
    52:## B.5 較正の記録
    57:## B.6 静的検査
    65:## B.7 修正の大きさは意志ではなく原因で決める
    73:## B.8 失敗時手順の例（2026-06-02 の交絡発見に当てはめる）
    82:## B.9 Notion 側の対応

見出し B.1〜B.9 が揃っている。

## 4. Task D — 提案文書の検査器

### 4.1 置いた場所と、規約から読めていることの確認

置いた場所は **`tools/check_proposal.py`**（262 行）。`tools/check_spec.py` には足していない。
あちらの規則は `issuer_defects` の実例を裏付けに持つ設計で、裏付けの無い規則を足すと
検出率の分母が動くためである（禁止事項 1）。

**一覧は規約から読む。検査器は写しを持たない。** 読めているかを先に確かめた。

    $ python -c "... import check_proposal as cp; s = cp.section_text() ..."
    節の行数: 80
    禁止語 15 語: ['最大の新規性', '世界初', '画期的', '有望', '筋が良い', '本命', '未踏', '空白',
                   '決定的', '確実に効く', '明らかに', '大幅', '劇的', '必ず改善', '唯一の']
    カード 14 件: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
      1 問い。yes/no で答えが出る一文
      ...
      14 初回にセットで試す設定の掃引集合。掃引する主要因、固定する交互作用、固定の理由
    数値必須: [5, 6, 10]

数値必須の抽出は句点で区切った文単位で当てている。同じ段落の
「#10 は #14 の掃引集合全体で見積もる。」を巻き込まないためで、実測どおり
`#14` は入っていない。

### 4.2 禁止語の対照（完了判定 b、SPEC Task D-5 の境界）

    $ python tools/check_proposal.py <ctl>/fw_none.md --only forbidden
    検出 0 件（禁止語 0 / 見出し欠落 0 / 数字欠落 0）
    exit=0

    $ python tools/check_proposal.py <ctl>/fw_one.md --only forbidden
    forbidden_word   fw_one.md:1  禁止語「画期的」
    検出 1 件（禁止語 1 / 見出し欠落 0 / 数字欠落 0）
    exit=1

    $ python tools/check_proposal.py <ctl>/fw_two.md --only forbidden
    forbidden_word   fw_two.md:1  禁止語「画期的」
    forbidden_word   fw_two.md:1  禁止語「決定的」
    検出 2 件（禁止語 2 / 見出し欠落 0 / 数字欠落 0）
    exit=1

    $ python tools/check_proposal.py <ctl>/fw_mitou_bare.md --only forbidden
    forbidden_word   fw_mitou_bare.md:1  禁止語「未踏」
    検出 1 件
    exit=1

    $ python tools/check_proposal.py <ctl>/fw_mitou_hypothesis.md --only forbidden
    検出 0 件
    exit=0

**0 / 1 / 2 件と、境界の 1 / 0 件。** 五通りすべて期待どおり。
免除は「未踏」「空白」だけで、他の禁止語には及ばないことを試験で固定した
（`test_exemption_does_not_cover_other_words`: 未踏＋決定的で決定的だけが残る）。

### 4.3 カード充足の対照（完了判定 c）

    $ python tools/check_proposal.py <ctl>/card_14.md --only card
    検出 0 件（禁止語 0 / 見出し欠落 0 / 数字欠落 0）
    exit=0

    $ python tools/check_proposal.py <ctl>/card_13.md --only card
    missing_heading  card_13.md  カード #7（成功の閾値（主判定規則で書く））の見出しが無い
    検出 1 件（禁止語 0 / 見出し欠落 1 / 数字欠落 0）
    exit=1

    $ python tools/check_proposal.py <ctl>/card_no_digit_5.md --only card
    missing_number   card_no_digit_5.md:19  カード #5（期待効果量（点））の本文に数字が無い
    検出 1 件（禁止語 0 / 見出し欠落 0 / 数字欠落 1）
    exit=1

**14 件で 0 / 13 件で 1 / 数字欠落で 1。** 三通りすべて期待どおり。
`#5 #6 #10` のそれぞれで同じ結果になることを `parametrize` で 3 通り固定した。

### 4.4 試験

    $ pytest tests/test_check_proposal.py -q
    26 passed in 0.06s

26 件の内訳: 規約の読み取り 5、禁止語 4、境界 3、カード 6、入口と終了コード 6、
規約を読めない場合 1、番号書式 1。

### 4.5 検査器の自己適用（限界の実測）

    $ python tools/check_proposal.py docs/proposal-gate.md --only forbidden
    forbidden_word   docs/proposal-gate.md:13  禁止語「最大の新規性」
    検出 1 件
    exit=1

13 行目は B.1 の表で**過去の欠陥を引用した箇所**であり、文書自身の主張ではない。
**検査器は引用の中の禁止語を区別しない。** 対象は提案文書であり、手順書へ当てる用途は
想定していないが、限界として記録する。「未踏」「空白」は B.6 に
「空白である理由の仮説」があるため免除され、検出されていない。

## 5. Task E — 検証

### 5.1 完了判定 a — アンカーの解決（両方向）

    $ python -c "... vt.validate_l2(probe) ..."
    --- [conventions#proposal_gate] ---
      L2 findings: なし
      判定: 解決できた
    --- [conventions#proposal_gate_zz] ---
      L2 findings: ['[L2-5] contract.inject_verbatim: アンカー proposal_gate_zz が存在しません']
      判定: 解決できない
    --- [conventions#issuer_cautions] ---
      L2 findings: なし
      判定: 解決できた

**存在しない名では実際に落ちる。** 判定は空振りではない。

### 5.2 完了判定 e — L2-6 の WARN と、起票者の説明との食い違い

    $ grep -n "inject_verbatim\|conventions_rev" tasks/T-2026-08-10-conventions-survey/spec.yaml
    29:  inject_verbatim: [conventions#prohibitions, conventions#naming]
    30:  conventions_rev: "1201f4f"
    $ make task-validate TASK=T-2026-08-10-conventions-survey
    WARN [L2-6] conventions.md が 1201f4f 以降に変更されています。差分を確認してください
    OK   T-2026-08-10-conventions-survey
    1 task(s), 0 failed

WARN が出て、FAIL は 0 件。**ここまでは契約の期待どおり。**

否定対照を置いた。起票者の説明が正しければ、`naming` を注入しない契約では
WARN は出ないはずである。

    $ grep -n "inject_verbatim\|conventions_rev" tasks/T-2026-08-11-issuer-defect-detector/spec.yaml
    29:  inject_verbatim: [conventions#prohibitions]
    30:  conventions_rev: "d422b08"
    $ make task-validate TASK=T-2026-08-11-issuer-defect-detector
    WARN [L2-6] conventions.md が d422b08 以降に変更されています。差分を確認してください
    OK   T-2026-08-11-issuer-defect-detector
    1 task(s), 0 failed

🔴 **同じ WARN が出た。** 実装（`tools/validate_task.py:439`）は
`git diff --name-only {rev}..HEAD -- context/conventions.md` の有無だけを見ており、
`inject_verbatim` を読まない。しかもこの時点では変更履歴にまだ行を足しておらず、
`proposal_gate` 節を足しただけである。**起票者の誤り 2 として記録した。**

本契約自身にも WARN が出る。SPEC 6 節の想定どおりで、実測の側を採って続行した。

    $ make task-validate TASK=T-2026-09-16-proposal-gate
    WARN [L2-6] conventions.md が a8c07e81 以降に変更されています。差分を確認してください
    OK   T-2026-09-16-proposal-gate
    1 task(s), 0 failed

### 5.3 完了判定 d — 規則数が不変

    $ git diff --stat tools/check_spec.py
    （空 = 無変更）
    $ python -c "from check_spec import RULES; print(len(RULES))"
    8
    $ make spec-check TASK=T-2026-09-16-proposal-gate
    "rules_checked": 8,
    "hits": 0,
    "status": "pass",
    "targets": 1

**変更前 8 / 変更後 8。** 差分が空であることと、検査器の自己申告と、
タプルの要素数の三つが揃った。

### 5.4 完了判定 f — 試験と、その空振りでないことの確認

    $ pytest tests/ -q -p no:cacheprovider
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    6 failed, 535 passed, 22 warnings in 25.21s

**前 6 failed / 509 passed → 後 6 failed / 535 passed。** 失敗の増減は 0 で、
落ちている 6 件は着手前と同一である（本契約の範囲外）。通過が 26 件増えた。

陽性対照を一つ壊した。

    $ sed -i 's|text = "本案は画期的な結合である。\n"|text = "本案は堅実な結合である。\n"|' tests/test_check_proposal.py
    $ pytest tests/test_check_proposal.py -q
        text = "本案は堅実な結合である。\n"
        findings = check_forbidden(text, list(FORBIDDEN_IN_CONVENTIONS))
    >   assert len(findings) == 1
    E   assert 0 == 1
    E    +  where 0 = len([])
    FAILED tests/test_check_proposal.py::test_forbidden_one_word_gives_one
    1 failed, 25 passed in 0.09s

**禁止語を消すと落ちる。** 復元して差分が無いことを確かめ、26 passed に戻した。

### 5.5 forbidden-check — 契約の指示と禁止が矛盾していた

    $ make forbidden-check TASK=T-2026-09-16-proposal-gate
    {"status": "fail", ..., "violations": [{"path": "context/conventions.md",
     "reason": "禁止されたファイル context/conventions.md"}]}
    make: *** [Makefile:159: forbidden-check] Error 1

`context/conventions.md` は `tools/check_forbidden.py:54` の `FORBIDDEN_FILES` にある。
一方で契約の Task B は同ファイルへの追記を命じている。**契約の内部で矛盾している。**

許可の上限を実装で確かめた。`NEVER_ALLOWABLE_PREFIXES` は `data/` だけで、
`context/` は含まれない。様式上も `allow_write` は正規のキーである。

    $ python -c "... spec.schema.json の contract ..."
    contract の許可キー: ['allow_write', 'conventions_rev', 'inject_verbatim', 'prohibitions', 'verbatim_forbidden']
    additionalProperties: False

したがって**起票者が書き忘れたものと判断し、宣言を補った**（逸脱 1）。

    contract:
      allow_write: ["context/conventions.md"]

    $ make forbidden-check TASK=T-2026-09-16-proposal-gate
    "declared_allowances": ["context/conventions.md"],
    "permitted": [{"path": "context/conventions.md", "reason": "契約の allow_write ... により許可"}],
    "rejected_allowances": [],
    "status": "pass",
    "violations": []

変更対象は 7 件で、いずれも契約の範囲内である。

    context/conventions.md
    docs/proposal-gate.md
    tasks/T-2026-09-16-proposal-gate/{SPEC.md,audit.md,spec.yaml}
    tests/test_check_proposal.py
    tools/check_proposal.py

### 5.6 docs-check は新規文書について空振りだった

    $ make docs-check
    [docs-check] 対象 42 文書 / Makefile のターゲット 34 件
    [docs-check] 食い違いなし

**対象数が変更前と同じ 42 である。** 実装を読むと、対象は
`docs/docs_audit.md` に列挙された文書だけで（`tools/check_docs.py:170`
`parse_audit_targets`）、ファイルの走査ではない。

    $ grep -c "proposal-gate" docs/docs_audit.md
    0

したがって通過は `docs/proposal-gate.md` について空振りである。代わりに文書内の
経路を手で確かめた。

    実在   context/conventions.md
    実在   tools/check_spec.py
    $ grep -n "docs/evidence" docs/proposal-gate.md
    36:      → CLI が DOI を全件照合し docs/evidence/ に地図を置く
    $ ls -d docs/evidence
    （不在。並行契約 T-2026-09-16-evidence-map-ab が作る予定）

`docs_audit.md` への登録は契約が求めておらず、いま登録すると不在の経路で落ちるため
行っていない。申し送りに残した。

### 5.7 agent-check

    $ make agent-check
    {"errors": [], "pager_violations": [], "status": "pass", "targets": 116, "violations": []}

### 5.8 様式検査

    $ make task-validate TASK=T-2026-09-16-proposal-gate
    WARN [L2-6] conventions.md が a8c07e81 以降に変更されています。差分を確認してください
    OK   T-2026-09-16-proposal-gate
    1 task(s), 0 failed

`result.yaml`（版 3）が様式を通った。

### 5.9 投影を再生成していないこと

SPEC の禁止事項 3 により `context/auto/*` と `tasks/inbox.md` は再生成していない。
並行契約 `T-2026-09-16-evidence-map-ab` と同時に走るためで、統合後に利用者が
一台で一度だけ `make taskindex && make inbox` を回す。申し送りに残した。
