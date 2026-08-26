# audit — T-2026-08-26-official-split-reassessment

証跡の記録。事実の記録は `RESULT.md`、解析の結論は
`experiments/analysis/official_split_reassessment/REPORT.md`。

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/official-split-reassessment`

---

## Task 1 — 開始の記録

    $ TZ=Asia/Tokyo date '+JST %Y-%m-%d %H:%M:%S'; date -u '+UTC %Y-%m-%dT%H:%M:%SZ'; date +%s
    JST 2026-08-26 15:27:11
    UTC 2026-08-26T06:27:11Z
    epoch=1787725631

**上限は開始から 10 時間 = 600 分。**

    $ git --no-pager status --porcelain
    ?? tasks/T-2026-08-26-official-split-reassessment/

**汚れていない。退避は不要だった。** 前の契約の退避は残っている（本契約では戻さない）。

    $ git --no-pager stash list
    stash@{0}: On feat/error-shape-selectivity: pre-oracle-ceiling-lovo          ← **本実行者のものではない**
    stash@{1}: On feat/issuer-refs-to-repo: T-2026-08-26-error-shape-selectivity: 契約開始前から在った汚れの退避（.stglobalignore の変更 + 未追跡 4 件）

**退避の添字がずれた。** 前契約で作った退避は `stash@{0}` から **`stash@{1}`** へ移った。
他ホストの契約が退避を積んだためである。**添字で指さず、名前で指すこと。**

    $ [ -e .sync-pause ] && echo 在る
    在る
    $ grep -c sync-pause ~/bin/m2-sync.sh
    2

### 分岐の起点（PR の base に要る）

    分岐: feat/official-split-reassessment
    先頭: 93f133ea Merge pull request #157 from takuya3h/feat/lovo-decision-rule
    origin/phase0: 93f133ea Merge pull request #157 from takuya3h/feat/lovo-decision-rule
    既定の分岐: origin/master

**起点は `phase0`。既定の分岐は `master`。base は `phase0` にする。**

---

## 検証

    $ make task-validate TASK=T-2026-08-26-official-split-reassessment
    OK   T-2026-08-26-official-split-reassessment

    1 task(s), 0 failed
    validate exit=0

**WARN 無し。**

### L3（回答前）

    P6 decisions_answered     FAIL 未回答 3 件: 報告と論文に載せる評価枠組みを一つに決めること; 撤回した判断を取り消すこと、または維持を確定させること; 既存の報告の記述を訂正すること
    RESULT: 4 PASS / 0 WARN / 4 SKIP / 1 FAIL
    preflight exit=2

**列挙して利用者へ提示し停止した。自分で決めていない。** 回答は**「三件とも契約の外」**。
SPEC 第 4 節が同じ 3 件を「本契約が行わないこと」として禁じており、本文と整合する。

### L3（回答後）

    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS experiments/analysis/official_split_reassessment/ は未作成だが作成可能（experiments/analysis へ書き込みと削除ができた）
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし

    RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
    preflight exit=0

**SKIP は「合格」ではない。** P2 P3 P4 P5 は実行されていない。
**P3 `deterministic_flags` が SKIP であることは、本契約の主題（決定性の記録が無い）と地続きである。**

### 解決した参照

    conventions#split                  ->   311 B / sha256 1a92c51ab4d579f0
    conventions#sigma                  ->   903 B / sha256 b537ada68a02bb41
    conventions#prohibitions           ->   277 B / sha256 bc032d4d93e7194e
    conventions#issuer_cautions        -> 1012 B / sha256 512f7bf5e84a4489

    conventions_rev  spec の記載: a8c07e813696d3720ceee648e8aa202224285955
                     実測      : a8c07e813696d3720ceee648e8aa202224285955   ← 一致

`conventions#split` の原文（**分割の定義。読むだけ。変えていない**）

    ## split

    論文準拠 split の動画 ID は次のとおり。

    - train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
    - val: `09`, `10`
    - test: `04`, `05`, `07`

    転記元: `data/splits/ego_train.txt`, `data/splits/ego_val.txt`, `data/splits/ego_test.txt`。
    実装側の対応値は `src/egosurgery/utils/eval_recipe.py` の `PAPER_SPLIT_VIDEOS`。

`inputs.denominator.ref` の解決

    experiment_id        = phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
    split                = val          （require: split=val を満たす）
    n_runs               = 17
    n_seeds              = 3            （require: >=3 を満たす）
    seeds                = 42,123,456
    accuracy_mean        = 0.8973014948553679
    accuracy_sstd        = 0.006099179663503103
    sigma_source         = （空）
    delta_sigma_source   = （空）

**分母そのものの `sigma_source` が空である。** SPEC 第 5 節の引き継ぎ
「分母として指定されている実験自体が、決定性を制御していない」と整合する。

---

## Phase A — 棚卸し

入口の実装の実在（**在ると仮定しない**）

    $ ls -la tools/build_context.py
    -rw-rw-r-- 1 ubuntu ubuntu 17457 Aug 22 06:54 tools/build_context.py

三つの異質な方法（出力は `experiments/analysis/official_split_reassessment/inventory.txt`）

    === 方法 1: experiments.csv の split 列 ===
      val: 200  test: 0  空: 13  合計: 213

    === 方法 2: index.csv（run 単位・別の表）===
      split: [('val', 1142), ('', 35)]
      metrics_primary_split: [('val', 612), ('', 565)]
      全 run: 1177

    === 方法 3: experiment_id の文字列（@val / @test）===
      '@val' を含む: 200
      '@test' を含む: 0

    === 陰性対照: 存在しない語で同じ探索 ===
      '@zzznosuchsplit' を含む: 0
      split=='zzznosuchsplit': 0

    陰性対照（棚卸し側）:
      zzznosuchtoken          : experiments.csv 0 件 / index.csv 0 件
      qqq_not_a_method        : experiments.csv 0 件 / index.csv 0 件

**三つとも一致し、陰性対照は零を返した。探し方は働いている。**

棚卸しの結果（`inventory.txt:5-21`）

    結論                                experiments.csv    うち split=val    うち split=test   index.csv
    1 術具の情報を工程認識へ渡す                                 8               8                0          35
    2 全体平均の特徴を足す害(GAP)                              0               0                0           0
    3 正しい術具存在の追加の利得                                 2               1                0          11
    4 入力側の雑音除去                                      0               0                0           0
    5 弁別しない術具を落とす                                  11              11                0          33
    6 工程の情報を術具検出へ渡す                                 2               0                0           6

**綴りは複数の書き方で探した**（例: GAP は `\bgap\b|_gap|gap_|globalavg|global_avg|pooling` の 6 通り）。
**一致零件を綴りの誤りと取り違えないため。**

### 想定外 — 出力が途中で切れた

一度目は `python inventory.py | tee inventory.txt | head -60` と書いた。
**`head` が 60 行で閉じ、SIGPIPE で処理が死んだ。** 結論 4〜6 が書かれなかった。

    $ grep -n '^--- ' inventory.txt
    23:--- 1 …
    96:--- 2 …
    99:--- 3 …
    --- 総行数: 107 ---

`head` を外して取り直した（総行数 214、結論 6 件すべて）。
**背景で走らせた処理ではないが、出力の切り詰めで記録が欠ける型は同じである。**

---

## Phase B — 効果量と揺らぎの出所

全行は `inventory.txt:23-214`。**推定で埋めた欄は無い。記録が無い欄は `(記録なし)` と出る。**

公式の分割で判定を持つ 136 行の揺らぎの出所（`controls.txt:16-17`）

    公式の分割で判定を持つ行 136 件の揺らぎの出所: {'paired_delta': 136}

決定性（`controls.txt:47-52`）

    experiments.csv に決定性を表す列: **0 件**
    index.csv       に決定性を表す列: **0 件**

（`determin` `cudnn` `benchmark` `nondet` のいずれも名に含む列が無い。
 `seed` 系の列は在るが、これは種の値であって決定性の制御ではない。）

---

## Phase C — 判定の切り分けと対照

全文は `controls.txt`。

    【当てられない判定】分け方の間の相関を扱う判定（先行契約が確定させたもの 2 件）
      公式の分割には**分け方が存在しない**（分割は一通り: train 10 / val 2 / test 3 動画）。
      したがって当てられない。**当てていない。**
        fold/cv/leave を名に含む列: **0 件**

    【分離しているか】
      陽性の判定 = significant   |Δ|/σ(accuracy) = 11.423  同符号 = True
      陰性の判定 = not_significant   |Δ|/σ(accuracy) = 0.207  同符号 = False
      比: 陽性の |Δ|/σ は陰性の 55.1 倍

🔴 **SPEC が指定した対照は公式の分割に存在しなかった。**
指定の陽性（全体平均の特徴を足す害）も指定の陰性（工程→術具検出）も **0 件**である。
代替を実測から選び、選んだ理由を `controls.txt:20-28` に記録した。

**陰性対照は経路を通っている。** 同じ学習・同じ評価・同じ対の差の手続きを経たうえで
`Δ分類 = +0.00049` になっている。構造上どうやっても零になるものではない
（同じ行の `Δ分節 = −4.62615`、`|Δ|/σ = 4.155` と、指標によっては零から離れる）。

---

## Phase D — 二つの枠組みの並置

全文は `juxtapose.txt`。

    公式の分割（検証側 val）で測られた行: **11 件**。評価側 test: **0 件**。
    分類の正しさ Δ: 最小 -0.01799 / 中央 +0.02403 / 最大 +0.05462  正の数 10/11
    工程平均     Δ: 最小 -0.03741 / 中央 +0.05898 / 最大 +0.11108  正の数 8/11

    【起票者の申し送り 3 との突き合わせ】
      申し送り: 『公式の分割では分類の正しさは動かず、工程ごとの成績を平均した指標が改善していた』
      実測    : 分類の正しさは **動いている**。11 件中 10 件が正、|Δ|/σ は 0.21〜28.32。
                工程平均も **動いている**（8/11 件が正）。
      → 『分類は動かず工程平均だけ改善』という形にはなっていない。**申し送りは実測と食い違う。**

**どちらの枠組みが正しいとは書いていない。撤回の可否も判断していない。**
