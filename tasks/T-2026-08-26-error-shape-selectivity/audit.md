# audit — T-2026-08-26-error-shape-selectivity

証跡の記録。命令とその出力、対照の出力、変更範囲の一覧、台帳の応答。
事実の記録は `RESULT.md`。**同じ内容を二度書かない。**

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/error-shape-selectivity`

---

## Task 1 — 開始の記録

### Step 1 時刻

    $ TZ=Asia/Tokyo date '+JST %Y-%m-%d %H:%M:%S'; date -u '+UTC %Y-%m-%dT%H:%M:%SZ'; date +%s
    JST 2026-08-26 06:50:26
    UTC 2026-08-25T21:50:26Z
    epoch=1787694626

**上限は Phase A の開始から 14 時間 = 840 分。** 各 Phase の入口で経過を測る。

### Step 2 作業ツリー

前の契約（T-2026-08-25-issuer-refs-to-repo）の終了時に退避済み。

    $ git stash list
    stash@{0}: On feat/issuer-refs-to-repo: T-2026-08-26-error-shape-selectivity: 契約開始前から在った汚れの退避（.stglobalignore の変更 + 未追跡 4 件）

    $ git --no-pager stash show --name-status stash@{0}
    M	.stglobalignore
    $ git --no-pager show --name-only --format='' stash@{0}^3
    .sync-pause.released
    docs/sessions/digest/2026-08-22-d0076c74-6667-46a0-95fb-96d9c1d68f8c.md
    docs/sessions/digest/2026-08-23-da7743d1-f487-4089-98e2-79391f7eb001.md
    docs/sessions/digest/2026-08-24-32ddc4ea-b89f-4cf5-b828-6ef1483afe84.md

**追跡済み 1 件 + 未追跡 4 件。`mv` は使っていない。**
**本契約の中では戻さない。** 元の分岐へ戻ってから戻す。

    $ git --no-pager status --porcelain
    ?? tasks/T-2026-08-26-error-shape-selectivity/
    件数: 1

### Step 3 抑止

    $ [ -e .sync-pause ] && echo 在る
    在る
    $ grep -c sync-pause ~/bin/m2-sync.sh
    2

`task-start` の出力にも `[task-start] .sync-pause は実行前から存在するため触れません` と出た。

---

## 取り込みと検証

### 取り込みは一度失敗している

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-08-26-error-shape-selectivity
    取り込みを中止しました: 要約値が一致しません: T-2026-08-26-error-shape-selectivity
      台帳の記載: 52b41bdab1442c5d36acaa569f9e7446ff39caed4a08ea9545b4a3594c649286
      取得した本文: 55609ac99288da9ef1f5ac7bd8c286e1ce1faee4be72b9fef90d2025b25afd60
    台帳が本文を改変した可能性があります。取り込みません
    [task-start] 取り込みに失敗しました。巻き戻します
    [task-start] 実行前の状態へ戻しました
    make: *** [Makefile:205: task-start] Error 4
    --- 実際の終了コード: 2 ---

**二度実行して同一の値。** 巻き戻しは完全だった（分岐 0 件・契約ディレクトリ無し・作業ツリー 0 件）。
起票者が台帳の要約値を直したのち、再実行して取り込めた。

**終了コードは `|` 越しでは取れない。** `exit=$?` はパイプの右端の値になる。
`out=$(...); ec=$?` で取り直した。

### 実測して置換した値

    $ git --no-pager log -1 --format='%h %ad %s' --date=short -- context/conventions.md
    a8c07e81 2026-08-25 feat(context): move issuer references into version control and inject the cautions
    $ git --no-pager log -1 --format='%h %ad %s' --date=short -- runindex/
    7918b5dd 2026-08-16 exp(s4): 60-seed deterministic sweep -- the upper bound is not detectable

`spec.yaml` の `PENDING_EXECUTOR_MEASUREMENT` 2 件を上記で置換した。
**`created_from.counts` は起票時点の記録であるため触っていない**（一度 現在値へ書き換えたが、
L2-8 の警告そのものを消してしまうため戻した）。

### L1 + L2

    $ make task-validate TASK=T-2026-08-26-error-shape-selectivity
    WARN [L2-8] index.csv: 起票時 751 → 現在 1177（分母が動いています）
    WARN [L2-8] experiments.csv: 起票時 207 → 現在 213（分母が動いています）
    OK   T-2026-08-26-error-shape-selectivity

    1 task(s), 0 failed
    validate exit=0

**WARN 2 件を利用者へ提示し、続行の可否を確認した。回答は「続行する」。**

### L3（回答前）

    P6 decisions_answered     FAIL 未回答 3 件: 選択性を研究の主たる知見として位置づけること; 掃引の範囲を本契約の外へ広げること; 既存の報告の記述を訂正すること
    RESULT: 4 PASS / 0 WARN / 4 SKIP / 1 FAIL
    preflight exit=2

**列挙して利用者へ提示し停止した。自分で決めていない。**
回答は**「三件とも契約の外」**。`tools/preflight_task.py:242-251` は
`decisions_required` が空であることだけを見るため、回答を記録したうえで空にした。

### L3（回答後）

    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS experiments/analysis/error_shape_selectivity/ は未作成だが作成可能（experiments/analysis へ書き込みと削除ができた）
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし

    RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
    preflight exit=0

**SKIP は「合格」ではない。** P2 P3 P4 P5 は実行されていない。

### 解決した参照

`contract.inject_verbatim`（原文は `context/conventions.md` の該当アンカー）

    conventions#sigma                ->  903 B / sha256 b537ada68a02bb41
    conventions#prohibitions         ->  277 B / sha256 bc032d4d93e7194e
    conventions#issuer_cautions      -> 1012 B / sha256 512f7bf5e84a4489

`issuer_cautions` は前の契約（T-2026-08-25-issuer-refs-to-repo）で追加した節であり、
**本契約が最初の利用者**である。注入の仕組みが端から端まで働いた。

`inputs.denominator.ref` = `exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`

    experiment_id  = phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
    split          = val          （require: split=val を満たす）
    n_seeds        = 3            （require: >=3 を満たす）
    seeds          = 42,123,456
    n_runs         = 17
    accuracy_mean  = 0.8973014948553679
    accuracy_sstd  = 0.006099179663503103
    accuracy_min   = 0.8864686468646865
    accuracy_max   = 0.9082508250825082
    edit_score_mean= 39.91661295170067
    edit_score_sstd= 2.621371700613755
    sigma_source   = （空）
    delta_sigma_source = （空）

**`require: {sigma: present}` について。** `accuracy_sstd` は在るが `sigma_source` の列は空である。
L2 は通っている。**本契約はこの分母を基準点として引くだけで、掃引の値には使っていない。**
掃引はプロキシ（LOVO）の上で行うため、分母は文脈としてのみ記録する。

---

## Task 2（Phase A）— 既存の介入実験の再現

    === Phase A 入口 ===
    JST 2026-08-26 06:53:02
    経過: 2 分 / 上限 840 分

### Step 1 所在の確認（在ると仮定しない）

    $ ls -la docs/analysis_scripts/proxy_lovo_noise_structure.py
    -rw-rw-r-- 1 ubuntu ubuntu 3100 Aug 23 20:30 docs/analysis_scripts/proxy_lovo_noise_structure.py

**異質な方法で二度確かめた。先頭がドットのものを含めている。**

    $ find . -path ./.git -prune -o -name '*noise*' -print | head -20
    ./experiments/selection_noise_2026-07-29
    ./scripts/run_t1a_combined_oracle_noise.sh
    ...（20 件）

    $ grep -rl "noise_structure\|isolated_flip\|burst" --include='*.py' --include='*.md' --exclude-dir=.git --exclude-dir=.venv .
    README.md
    docs/analysis_scripts/README.md
    docs/analysis_scripts/proxy_noise_structure.py
    docs/analysis_scripts/proxy_lovo_noise_structure.py
    docs/experiment_log.md
    docs/research_review_and_next_plan_2026-08-22.md
    docs/analysis_scripts/proxy_lovo_noise_testonly.py
    docs/sessions/digest/2026-08-21-538fcc76-67d1-404f-a34b-288e15cb5242.md

**一致は零件ではなかった。** 名前で探す方法と中身で探す方法の双方が同じ実装を指した。

記録されている値は `docs/research_review_and_next_plan_2026-08-22.md:1042-1130`（§3.10）にある。

### Step 2 再現

    $ python docs/analysis_scripts/proxy_lovo_noise_structure.py 3
    --- acc
        clean                mean=  0.8680
        iid p=0.05           mean=  0.8378  Δ= -0.0302 |m|/SE= 5.51 neg=13/15
        burst L=32 p=0.05    mean=  0.7534  Δ= -0.1145 |m|/SE= 6.46 neg=15/15
        iid p=0.10           mean=  0.8193  Δ= -0.0487 |m|/SE= 5.63 neg=14/15
        burst L=32 p=0.10    mean=  0.6283  Δ= -0.2396 |m|/SE=15.18 neg=15/15
    --- mF1
        clean                mean=  0.8087
        iid p=0.05           mean=  0.7619  Δ= -0.0468 |m|/SE= 3.69 neg=13/15
        burst L=32 p=0.05    mean=  0.6628  Δ= -0.1459 |m|/SE= 8.96 neg=15/15
        iid p=0.10           mean=  0.7299  Δ= -0.0788 |m|/SE= 5.15 neg=13/15
        burst L=32 p=0.10    mean=  0.5370  Δ= -0.2717 |m|/SE=16.28 neg=15/15
    --- edit
        clean                mean= 56.6133
        iid p=0.05           mean= 38.1620  Δ=-18.4513 |m|/SE= 3.24 neg=14/15
        burst L=32 p=0.05    mean= 38.8393  Δ=-17.7740 |m|/SE= 3.18 neg=13/15
        iid p=0.10           mean= 34.0231  Δ=-22.5902 |m|/SE= 3.85 neg=14/15
        burst L=32 p=0.10    mean= 31.9555  Δ=-24.6578 |m|/SE= 4.14 neg=14/15
    --- segF50
        clean                mean=  0.5788
        iid p=0.05           mean=  0.3932  Δ= -0.1857 |m|/SE= 4.43 neg=15/15
        burst L=32 p=0.05    mean=  0.3654  Δ= -0.2134 |m|/SE= 4.47 neg=15/15
        iid p=0.10           mean=  0.3374  Δ= -0.2414 |m|/SE= 5.04 neg=14/15
        burst L=32 p=0.10    mean=  0.2485  Δ= -0.3303 |m|/SE= 5.89 neg=15/15

記録（`docs/research_review_and_next_plan_2026-08-22.md:1077-1082`）と突き合わせる。

| 条件 | 記録 acc | 実測 acc | 記録 Δacc | 実測 Δacc | 記録 edit | 実測 edit | 記録 Δedit | 実測 Δedit |
|---|---|---|---|---|---|---|---|---|
| ノイズ無し | 0.8680 | 0.8680 | — | — | 56.61 | 56.6133 | — | — |
| iid p=0.05 | 0.8378 | 0.8378 | −0.0302（5.51・13/15） | −0.0302（5.51・13/15） | 38.16 | 38.1620 | −18.45（3.24・14/15） | −18.4513（3.24・14/15） |
| burst L=32 p=0.05 | 0.7534 | 0.7534 | −0.1145（6.46・15/15） | −0.1145（6.46・15/15） | 38.84 | 38.8393 | −17.77（3.18・13/15） | −17.7740（3.18・13/15） |
| iid p=0.10 | 0.8193 | 0.8193 | −0.0487（5.63） | −0.0487（5.63） | 34.02 | 34.0231 | −22.59（3.85） | −22.5902（3.85） |
| burst L=32 p=0.10 | 0.6283 | 0.6283 | −0.2396（15.18） | −0.2396（15.18） | 31.96 | 31.9555 | −24.66（4.14） | −24.6578（4.14） |

**全ての値・効果量・符号の個数が一致した。**

### Step 2 の空振り確認（入力を変えれば一致しなくなるか）

種の本数を 3 → 1 に変えて走らせた。

    $ python docs/analysis_scripts/proxy_lovo_noise_structure.py 1
    --- acc
        clean                mean=  0.8680          ← ノイズ無しは種に依らない。変わらないのが正しい
        iid p=0.05           mean=  0.8309  Δ= -0.0371 |m|/SE= 4.61 neg=15/15
        burst L=32 p=0.05    mean=  0.7491  Δ= -0.1189 |m|/SE= 4.74 neg=15/15
        iid p=0.10           mean=  0.8139  Δ= -0.0541 |m|/SE= 4.72 neg=14/15
        burst L=32 p=0.10    mean=  0.6201  Δ= -0.2478 |m|/SE=14.30 neg=15/15

**汚した条件はすべて変わり、汚していない条件だけが変わらなかった。** 入力を読んでいる。

**判定 G1 — 通過。**

---

## Task 3（Phase B）— 対照の設置

    === Phase B 入口 ===
    JST 2026-08-26 06:58:xx
    経過: 8 分 / 上限 840 分

### 軸二の両端が同じ仕組みで扱えるか（SPEC 2.1・申し送り 2）

原典の `add_noise` は `mode="iid"` と `mode="burst"` を持つ。
**burst の L=1 が iid と同じかを実測した。**（`controls/verify_axis2.out`）

    p      seed  iid==burst(L=1)  異なる位置数
    0.01   7     True            0
    ...（p 5 水準 × 種 3 本 = 15 条件すべて True・異なる位置数 0）
    全条件で一致: True
    陰性対照 iid vs burst(L=2): 一致 = False  異なる位置数 = 6885

**ビット単位で同一である。** 乱数の消費順序まで一致する
（`rng.random(T)` と、L=1 の burst が回す `rng.random()` を T 回は同じ列を同じ順に消費する）。

→ **二つの形は一つの軸の両端である。L だけを動かせばよい。**
→ 申し送り 3（持続の長さを変える手続きが在るか）も**在る**。軸二の掃引ができる。

### 誤りの量を集合の差で求めていること（完了判定 c）

`controls/verify_err_rate.out`

         p    L  seed |       A 集合の対称差   B (X!=Y).sum       C 件数の差 | A==B  A!=C
      0.02    1     7 |           1177           1177          483 | True  True
      ...（18 条件）
       0.2   32    17 |           9933           9933         3851 | True  True

    A == B が全条件で成立: True  ← 掃引の数え方は集合の対称差と同値
    A != C が全条件で成立: True  ← 件数の差では別の値になる（誤った数え方と区別できている）

**部分一致（件数の差）で数えると約 2.5 分の 1 の値になる。** 区別できている。

### 陰性対照（誤りの経路を通した零）

原典の `build` は `add_noise(...) if p>0 else X` と分岐するため、
**p=0 では誤りを与える手続きを一度も呼ばない。それでは add_noise の欠陥を検出できない。**
`add_noise` を直接 p=0 で呼んだ。（`controls/verify_zero_noise.out`）

      mode    L  seed |       異なる位置数       実測誤り率
       iid    1     7 |            0    0.000000
      ...（12 条件すべて 0）
    誤りの経路を通しても全条件で零: True
    陽性方向 p=0.001: 異なる位置数 = 93  実測誤り率 = 0.001033

**片方向ではない。** 同じ検査が p=0.001 では非零を返す。

### 陽性対照（誤りを極端に多く与える）

    ===== 評価側のみ（ctrl_testonly_A.csv）=====
      クリーン: acc=0.8680  edit=56.6133  動画=15
      陽性対照 p=0.40 L=1: 実測誤り率=0.40047
        Δacc  = -0.5631  （0.8680 → 0.3049）
        Δedit = -51.6400  （56.6133 → 4.9733）

    ===== 学習側も汚す（ctrl_traintest.csv）=====
      陽性対照 p=0.40 L=1: 実測誤り率=0.40047
        Δacc  = -0.2359  （0.8680 → 0.6321）
        Δedit = -33.2522  （56.6133 → 23.3611）

**分類も分節も大きく壊れた。誤りは信号に届いている。**

### 乱数の再現（両方向）

    === 同じ種で二度走らせて一致するか（陽性方向）===
    🟢 A と B は完全一致
    行数: A=61 B=61
    sha256: A=82f6cd1981b92bea  B=82f6cd1981b92bea

    === 種を変えると変わるか（陰性方向）===
    🟢 A と C は異なる（異なる行数 120）
    sha256: C=9be8a9945ab5c1f0

**判定 G2 — 通過。**

### 過程の計数で否定対照が 1 を返した（申し送り 6 の罠）

    $ pgrep -af "proxy_lovo_noise_structure" | head -3
    226538 python docs/analysis_scripts/proxy_lovo_noise_structure.py 3
    226618 /usr/bin/zsh -c ... eval 'pgrep -af "proxy_lovo_noise_structure" ...'
    --- 生存: 2 件 ---

**自分の命令行を拾っている。** `/proc/PID/exe` で絞ったが、**最初は絞りを陽性側にしか
当てておらず、否定対照が 1 を返した。**

    実体の件数: 1     ← 陽性
    実体の件数: 1     ← 陰性（誤り）

同じ絞りを両方向へ当て直した。

    陽性（実在する処理）: 1
    陰性（存在しない語）: 0

---

## 想定外 — 掃引の実装が同期処理に削除された

**Phase C の一度目は、出力が一つも作られずに「完了」した。**

    $ cat logs/sweep_testonly.log
    python: can't open file '/home/ubuntu/slocal2/m2/experiments/analysis/error_shape_selectivity/sweep_error_shape_selectivity.py': [Errno 2] No such file or directory

**実装が消えていた。** 同じファイルで Phase B の対照 4 本は動いていた（21:59〜22:00）。

    $ grep "Deleted file" ~/.syncthing.log | tail -5
    2026-08-25 21:59:55 INF Deleted file (folder.id=m2 folder.type=sendreceive file.name=experiments/analysis/lovo_decision_rule/dump_folds.py log.pkg=model)
    2026-08-25 21:59:55 INF Deleted file (folder.id=m2 folder.type=sendreceive file.name=experiments/analysis/lovo_decision_rule/rules.py log.pkg=model)
    2026-08-25 21:59:55 INF Deleted file (folder.id=m2 folder.type=sendreceive file.name=experiments/analysis/error_shape_selectivity/sweep_error_shape_selectivity.py log.pkg=model)
    2026-08-25 21:59:55 INF Deleted file (folder.id=m2 folder.type=sendreceive file.name=experiments/analysis/error_shape_selectivity/verify_err_rate.py log.pkg=model)

**同期処理が消した。** 本契約の 2 件だけでなく、**別の契約の 2 件も同時刻に消えている**
（`lovo_decision_rule/` は本契約が作ったものではない）。

原因は除外規則である。

    $ sed -n '52p' .stignore
    !experiments/**/*.py

`!` は「除外しない」＝**同期対象にする**の意である。`experiments/` 配下の `.py` は
他ホストと同期され、**他ホストの状態で削除されうる。**

    $ ls experiments/analysis/error_shape_selectivity/
    aggregate.py  ctrl_testonly_A.csv  ctrl_testonly_B.csv  ctrl_testonly_C.csv  ctrl_traintest.csv  logs

**`.csv` は除外の対象で同期されないため生き残った。** 消えたのは `.py` だけである。
（`aggregate.py` はこの時点ではまだ作られていなかったため難を逃れた。）

🔴 **`.sync-pause` はこれを止めない。** 目印を見ているのは `scripts/sync/m2-sync.sh:40` であり、
**git 操作（統合・push・起票）だけを抑止する。** syncthing の実ファイル同期は別の仕組みで、
本契約の実行中も動き続けていた。

**対処**: 実装を同期の外（scratchpad）へ置いて実行し、出力の `.csv` だけを repo 配下へ書いた。
消えた検査器 2 件は書き直し、出力を `controls/` へ残した。
**成果物は `git add` で即座に確保した。**

---

## Task 4（Phase C）— 掃引

    === Phase C 入口 ===
    JST 07:0x:xx  経過: 13 分 / 上限 840 分
    掃引の締切（この時刻を過ぎたら新しい点を始めない）: JST 18:50:26

締切は「開始 + 14 時間」から報告用に 2 時間を残した時刻である。
実装に `--deadline-epoch` を渡し、**過ぎたら新しい点を始めず空欄で残す**ようにした。

    $ tail -2 logs/sweep_traintest.log
    [traintest] p=0.4 L=64 seed=27 err=0.28911 runlen=62.04 9s
    [done]

    $ grep -c '^\[traintest\]' logs/sweep_traintest.log
    126
    $ grep -c '^\[skip\]' logs/sweep_traintest.log
    0
    $ 行数（見出しを除く）: rows_testonly=1905  rows_traintest=1905

**126 = 6 水準 × 7 水準 × 種 3 本。飛ばした点は 0。**
**1905 = 15 動画 × (42 点 × 3 種 + クリーン 1)。格子に空欄は無い。**

    === Phase C 完了 ===
    経過: 29 分 / 上限 840 分

**締切による水準の削減は起きなかった。** 見積り（README: 約 15 分／5 条件・種 3 本）に対し、
評価側のみの腕は分類器を fold ごとに 1 度だけ学習すれば足りるため大幅に速い。

### 誤りの量が意図した水準になっているか（完了判定 b）

`tables/breakdown_testonly.txt` および `tables/breakdown_traintest.txt` の第 4 節。

         p | L=1   L=2   L=4   L=8   L=16  L=32  L=64
      0.01 |  1.02  1.02  0.99  0.98  0.98  0.93  0.92
      0.02 |  1.02  1.01  1.01  0.98  0.96  0.96  0.90
      0.05 |  1.01  1.00  0.99  0.98  0.96  0.93  0.90
       0.1 |  1.00  0.96  0.95  0.94  0.92  0.90  0.87
       0.2 |  1.00  0.91  0.88  0.86  0.85  0.84  0.81
       0.4 |  1.00  0.83  0.77  0.74  0.73  0.72  0.71
      （値は 実測誤り率 / 名目 p。1.00 なら意図どおり）

**両腕で同一の値である**（同じ種・同じ手続きで誤りを作るため）。
**設定を変えれば実測値も変わる**ことは、この表の全 42 点が示している
（名目 p を 0.01 → 0.40 と 40 倍にすると実測も 0.0102 → 0.4005 と 39 倍になる）。

平均の連長も意図どおり動いた（L=1 → 1.01〜1.67、L=64 → 59.14〜61.86）。

---

## Task 5（Phase D）— 選択性の曲線化

    === Phase D 入口 ===
    JST 07:19:52  経過: 29 分 / 上限 840 分

集計は `aggregate.py`、崩れる領域の材料は `breakdown.py`、腕の比較は `compare_arms.py`。
出力は `tables/` にそのまま置いた。**本文へ手で書き写した数値は無い。**

### 掃引が原典を再現していることの独立な確認

原典の 4 条件は本掃引の格子の 4 点に対応する。**別々の実装で同じ値が出た。**

| 条件 | 原典 Δacc | 掃引 Δacc | 原典 Δedit | 掃引 Δedit |
|---|---|---|---|---|
| iid p=0.05 = (p=0.05, L=1) | −0.0302 | **−0.0302** | −18.4513 | **−18.4513** |
| burst L=32 p=0.05 = (p=0.05, L=32) | −0.1145 | **−0.1145** | −17.7740 | **−17.7740** |
| iid p=0.10 = (p=0.10, L=1) | −0.0487 | **−0.0487** | −22.5902 | **−22.5902** |
| burst L=32 p=0.10 = (p=0.10, L=32) | −0.2396 | **−0.2396** | −24.6578 | **−24.6578** |

### 効果量と符号の個数

`summary_testonly.csv` / `summary_traintest.csv` の
`eff_acc` `neg_acc` `eff_edit` `neg_edit` `eff_mF1` `neg_mF1` `eff_segF50` `neg_segF50` 列。
**42 点 × 2 腕 × 4 指標のすべてに入っている。判定とは別に記録した。**
表の形は `tables/compare_arms.txt` の第 5 節。

### 種ごとの散らばり

`sel_per_seed` 列に**種ごとに独立に求めた選択性**を、`sel_sstd` `sel_min` `sel_max` に
その散らばりを入れた。表は `tables/compare_arms.txt` の第 2 節。

**判定 G4 — 通過。** 表ができ、崩れる領域が三つとも特定された。

---

## Task 6（Phase E）— 報告

    === Phase E 入口 ===
    JST 07:22:37  経過: 32 分 / 上限 840 分

### 判定を行っていないことの確認

    $ grep -c '有意' REPORT.md
    0
    $ grep -c '非有意' REPORT.md
    0

### logs を版管理へ入れなかった理由

    $ git check-ignore -v experiments/analysis/error_shape_selectivity/logs/sweep_traintest.log
    .gitignore:28:experiments/**/logs/**	experiments/analysis/error_shape_selectivity/logs/sweep_traintest.log
    $ git ls-files 'experiments/analysis/**/logs/*' | grep -c ''
    0

**規約であり、前例も 0 件である。** 集計・崩れる領域・腕の比較・Phase A の再現の
各出力は `tables/` へ置いた（除外されないことを `git check-ignore` で確かめた）。
