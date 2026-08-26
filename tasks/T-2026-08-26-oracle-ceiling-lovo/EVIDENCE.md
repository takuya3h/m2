# 証跡の記録 — T-2026-08-26-oracle-ceiling-lovo

事実の記録は `RESULT.md`。本書は命令とその出力、対照の出力、変更範囲、台帳の応答を置く。
ホスト `lecun` / 分岐 `feat/oracle-ceiling-lovo` / 起点 `phase0` / シェル `/usr/bin/zsh`。

---

## E1. 時刻と締切

先行契約 `T-2026-08-26-oracle-ceiling-and-tool-drop` の Phase A 開始 = 1787692507（2026-08-26 06:15:07 JST）。
その十六時間後 = **1787750107（2026-08-26 22:15:07 JST）が本契約の締切**である。

    $ PRIOR_T0=1787692507; PRIOR_DEADLINE=$((PRIOR_T0+16*3600)); NOW=$(date +%s)
    本契約 T0 = 1787697051 (2026-08-26 07:30:51 JST)
    残り      = 53056 秒 = 884 分 = 14.74 時間

| Phase | 入口の経過 | 締切まで |
|---|---:|---:|
| A | 約 5 分 | 883 分 |
| B | 12882 秒 (215 分) | 670 分 |
| C | 12980 秒 (216 分) | 668 分 |
| D | 14467 秒 (241 分) | 643 分 |

## E2. 検証（L1+L2）

    $ make task-validate TASK=T-2026-08-26-oracle-ceiling-lovo; echo "EXIT_CODE=$?"
    EXIT_CODE=0
    WARN [L2-8] index.csv: 起票時 751 → 現在 1177（分母が動いています）
    WARN [L2-8] experiments.csv: 起票時 207 → 現在 213（分母が動いています）
    OK   T-2026-08-26-oracle-ceiling-lovo

SPEC §7 の指示に従い、**参照先の分母そのものが移動したか**を確かめた。

    experiment_id = phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
    n_runs = 17   n_seeds = 3   seeds = 42,123,456   split = val   hosts = efros,lecun
    eval_recipe_id = e98ffddee042
    accuracy_mean = 0.8973014948553679  pstd = 0.005917073407586465  sstd = 0.006099179663503103  n = 17

**先行契約が実測した値と完全に同一である。参照先は移動していない。**
`require` は `n_seeds >= 3`（3 で充足）/ `sigma: present`（pstd・sstd とも実数）/ `split: val`（val）をすべて満たす。
なお**本契約はこの分母を使っていない。** 対は同じ入口・同じ種で新たに作ったためである。

`inputs.sigma_policy` は省略されており、`conventions#sigma` の既定 `series: pstd` /
`sigma_source: paired_delta` / `delta_sigma_source: paired` を継承する。本契約は判定しないため記録のみに用いた。

`inputs.frozen_source.ref` は P5 が sha256 を照合して PASS（E3）。
`contract.conventions_rev` は起票時から `a8c07e813696d3720ceee648e8aa202224285955` が入っており、
`git diff <rev>..HEAD -- context/conventions.md` は空で L2-6 の WARN は出ていない。

## E3. プリフライト（L3）

初回:

    EXIT_CODE=2
    P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=... sys.prefix=...
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP UNKNOWN 判定基準が未確定。決定性設定は実行プロセス内で行われ外部から観測できない。backlog B-20 が未解決
    P4 prereg_committed       FAIL prereg.commit が未記入
    P5 frozen_source_hash     PASS sha256=03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    P6 decisions_answered     FAIL 未回答 4 件: 分け方の数を計画から変えること; 分母を別の実験へ移すこと; 決定化を無効にすること; 学習の数式や最適化に触れること
    P7 destination_writable   PASS experiments/transfer/ へ書き込みと削除ができた
    P8 contract_valid         PASS   P9 spec_lint PASS 規則 8 件を検査し該当なし
    RESULT: 5 PASS / 0 WARN / 2 SKIP / 2 FAIL

**SKIP は合格ではない。** P3 が SKIP であることは、検査器では決定化を確かめられないことを意味する。
事前登録 §4 の対照で測った（E8）。

P6 の 4 件を起票者へ提示。1 件目は実測（動画 15 本）に従い **15 組・30 run** とする決定、残り 3 件は「行わない」。
P4 のため契約を commit した。

    $ git --no-pager log -1 --format='%H %ci'
    9563ce5169bf305a245d6fef007369c2ed5c7ebf 2026-08-26 02:02:23 +0000

再実行: `RESULT: 7 PASS / 0 WARN / 2 SKIP / 0 FAIL`（EXIT_CODE=0）。

## E4. Phase A — 一つ抜き検証の経路の確認

**在ると仮定せず、異質な 3 方法で探した。先頭がドットのものを含める。**

    $ grep -rniIl "lovo\|leave.one.video\|leave_one_out\|holdout\|hold_out" src/ scripts/     → 1 件
    $ find . -iname "*lovo*" -o -iname "*leave*one*"  （.git と .venv を除く）                → 20 件
    $ git ls-files | grep -i "lovo\|leave"                                                    → 20 件

**陰性対照（実在しない語 `zqx_absent_mechanism` で同じ 3 方法）**

    grep: 0 件 / find: 0 件 / git ls-files: 0 件      ← 探し方は働いている

内訳。`src/` と `scripts/` の唯一の一致 `scripts/audit_hts_acceptance.py` は散文であって実装ではない。

    618: notes.append("動画17-22 に評価ギャップ工程なし -> G-4 は train 内 LOVO-CV (A案) で確定")
    1316: g4 = "拡張test split案を推奨" if ... else "train内LOVO-CV(A案)で確定"

実装は `docs/analysis_scripts/proxy_lovo_*.py` の **16 本のみ**で、いずれも代理側である。
`experiments/analysis/lovo_decision_rule/replicate_lovo.py` は**同時に走っている別契約の未追跡の生成物**であり、
本契約は依存していない（E10）。

**結論: 本番側に一つ抜き検証の経路は無い。** SPEC Task 2 Step 3 が明示的に許可する
「分け方を外から与える経路」「学習側と評価側の動画の集合を指定する経路」に限って配線した（E5）。

## E5. 配線した内容（`scripts/train_b2a.py`）

    $ git --no-pager diff --stat scripts/train_b2a.py
     scripts/train_b2a.py | 73 ++++++++++++++++++++++++++++++++++++++++++++--------
     1 file changed, 62 insertions(+), 11 deletions(-)

足したもの。

1. `video_of(clip_id)` — `"06_2" -> "06"`。manifest の命名に従う。
2. `check_no_leak(train_clips, eval_clips)` — 評価側の動画が学習側にも在ればその集合を返す。
3. `load_clips_lovo(holdout, **kw)` — 3 つの split の clip を集め、動画 ID で分ける。
   **既存の `load_clips` を改変せずに呼んでいる。既存の分割ファイルは読むだけである。**
4. `--lovo-holdout <video>` — 分け方を外から与える経路。
5. `config.yaml` へ `lovo` 節（`holdout_video` / `train_videos` / `eval_videos` /
   `n_train_clips` / `n_eval_clips` / `leak_check`）を書き出す。
6. `eval_recipe` の `test_cfg` へ `cv_scheme: leave_one_video_out` と `lovo_holdout` を足す。
   **評価の作法が標準 split と違うため、recipe を分けないと索引で同じ実験に混ざる。**

**触っていないもの**: 学習の数式、損失、最適化、既存の分割ファイル、凍結源。

lint は変更前後で同一。`I001` は変更前から出ている既存の指摘（末尾の `import os` に由来）で 1 件のまま。

## E6. 漏れの検査の対照（証跡を残さない）

**CLI に漏れを起こす経路は足していない。** `check_no_leak` を最小の `clip_id` の組で直接呼んだ。

    陰性対照（正しく分けた）
      train = ["01_1","02_1","06_2"]  eval = ["09_1"]   → 検出 = []          ← 空集合であるべき
    陽性対照（意図的に漏らした）
      train = ["01_1","09_2"]         eval = ["09_1"]   → 検出 = ['09']      ← 検出されるべき
    video_of: [('01_1','01'), ('06_2','06'), ('15_1','15'), ('09_1','09')]

**片方向だけでは「常に空集合を返す壊れ方」と区別できない。両方向で働いている。**

## E7. 腕の分離（入力の信号が実際に違うこと）

    split  frame_ids 一致  shape        pred 範囲          oracle の値集合  二値化して違う要素
    train  True           (9657,15)    [0.0000,0.9849]    [0.0,1.0]        749 / 144855 = 0.52%
    val    True           (1515,15)    [0.0000,0.9736]    [0.0,1.0]        657 / 22725  = 2.89%
    test   True           (4265,15)    [0.0000,0.9819]    [0.0,1.0]        5347 / 63975 = 8.36%
    合計                                                                    6753 / 231555 = 2.92%
    完全一致か = False（3 split すべて）

**陰性対照**: 同じ腕（oracle）を二度読むと `np.array_equal` = True。

**この内訳自体が本契約の問いに効く。** 凍結検出器は train で学習されているため train の不一致が最小（0.52%）なのは当然だが、
**val 2.89% に対し test 8.36% と 2.9 倍の開きがある。**
SPEC §1.3 の「検証側の分割は術具と工程の対応が異常にきれい」を、検出器の側から裏づける実測である。

## E8. 決定化の対照（LOVO の経路で・証跡なし）

    D1a seed=42  RC=0 ELAPSED_SEC=42
    D1b seed=42  RC=0 ELAPSED_SEC=39
    D2  seed=123 RC=0 ELAPSED_SEC=42

    陰性対照（同じ種なら一致）D1a vs D1b : diff_exit=0  差分行数=0
    陽性対照（種を変えれば変わる）D1a vs D2 : diff_exit=1  差分行数=102
    D1a  best @epoch 49: acc=0.9704 macroF1=0.9574
    D1b  best @epoch 49: acc=0.9704 macroF1=0.9574
    D2   best @epoch 48: acc=0.9693 macroF1=0.9604

    証跡ありの本体 v01_oracle と D1a の epoch 行の照合 : diff_exit=0
      → ExperimentManager は RNG に触れていない

## E9. Phase B / C — 実行の順序と所要時間

**対の両側は分け方ごとに隣接して交互（pred → oracle）に走らせた。**
各対の入口で残り時間を確かめ、両側が入らないなら始めない条件を実装した（発動せず）。

    seq  video  arm     start_epoch   elapsed_sec  rc  remaining_min_at_pair_entry
    1    01     pred    1787709993    37           0   668
    2    01     oracle  1787710030    42           0   668
    3    02     pred    1787710036    46           0   667
    4    02     oracle  1787710082    40           0   667
    5    03     pred    1787710122    37           0   666
    6    03     oracle  1787710159    49           0   666
    7    04     pred    1787710208    39           0   664
    8    04     oracle  1787710247    39           0   664
    9    05     pred    1787710286    36           0   663
    10   05     oracle  1787710322    36           0   663
    11   06     pred    1787710358    43           0   662
    12   06     oracle  1787710401    36           0   662
    13   07     pred    1787710437    35           0   661
    14   07     oracle  1787710472    35           0   661
    15   08     pred    1787710507    36           0   660
    16   08     oracle  1787710543    38           0   660
    17   09     pred    1787710581    36           0   658
    18   09     oracle  1787710617    37           0   658
    19   10     pred    1787710654    35           0   657
    20   10     oracle  1787710689    38           0   657
    21   11     pred    1787710727    39           0   656
    22   11     oracle  1787710766    34           0   656
    23   12     pred    1787710800    34           0   655
    24   12     oracle  1787710834    35           0   655
    25   13     pred    1787710869    35           0   653
    26   13     oracle  1787710904    39           0   653
    27   14     pred    1787710943    35           0   652
    28   14     oracle  1787710978    39           0   652
    29   15     pred    1787711017    35           0   651
    30   15     oracle  1787711052    40           0   651
    DONE

**30 本すべて rc=0。片側だけの腕は 0 本。**

所要時間（実測・秒）: 最小 34 / 最大 49 / 平均 38.0（n=30）。
**先行契約が同じ入口の標準 split で測った 25〜34 秒より長い。**
学習側の clip が 13 から 21 へ増えるためで、SPEC §5 が「同じとは限らない」と述べたとおりである。

本数の計算（Phase B 終了時点）:

    残り = 40091 秒 = 668.2 分 = 11.14 時間
    1 本の所要（安全側に実測の最大 42 秒）/ 対 1 組 = 84 秒
    入る対の組数 = floor(40091 / 84) = 477 組
    残り 14 組に要する時間 = 1176 秒 = 19.6 分     ← 全 15 組が入る

## E10. すべての分け方での漏れの検査

証跡の `config.yaml` の `lovo` 節を 30 本すべてについて照合した。

    そろった分け方 = 15 / 15   欠け = なし
    検査した run = 30 本 / 漏れのあった run = 0
    上限測定専用の印が無い oracle run = 0
    task_id が刻まれていない run = 0

`lovo` 節の例（v01・oracle）:

    lovo:
      holdout_video: '01'
      train_videos: ['02','03','04','05','06','07','08','09','10','11','12','13','14','15']
      eval_videos: ['01']
      n_train_clips: 21
      n_eval_clips: 1
      leak_check: pass

実行中の標準出力にも 1 行ずつ残っている。

    [b2a][LOVO] holdout=01 train_videos=[...14 本...] eval_videos=['01'] leak=0

## E11. 分け方ごとの内訳

     video  n_ev_clip   pred acc    orc acc      Δacc   pred mF1    orc mF1      ΔmF1
        01          1   0.967141   0.970427  +0.00329   0.953543   0.957443  +0.00390
        02          1   0.993492   0.995662  +0.00217   0.974778   0.985912  +0.01113
        03          1   0.897153   0.896235  -0.00092   0.705580   0.702950  -0.00263
        04          2   0.859293   0.864560  +0.00527   0.570627   0.589541  +0.01891
        05          2   0.884082   0.887347  +0.00327   0.815268   0.825104  +0.00984
        06          2   0.961566   0.968093  +0.00653   0.803411   0.808809  +0.00540
        07          2   0.909410   0.940970  +0.03156   0.836581   0.818192  -0.01839
        08          2   0.962857   0.962857  +0.00000   0.928732   0.928080  -0.00065
        09          1   0.990347   0.998069  +0.00772   0.992766   0.998562  +0.00580
        10          2   0.923771   0.944835  +0.02106   0.807065   0.812817  +0.00575
        11          1   0.973475   0.978780  +0.00531   0.909908   0.922112  +0.01220
        12          1   0.917898   0.945813  +0.02791   0.799419   0.937866  +0.13845
        13          1   0.936740   0.954988  +0.01825   0.783462   0.794919  +0.01146
        14          2   0.798895   0.791713  -0.00718   0.713393   0.729888  +0.01649
        15          1   0.995238   0.995238  +0.00000   0.992874   0.992874  +0.00000

全指標の集計（判定は行っていない）:

    phase_accuracy     平均Δ=+0.008282  中央値Δ=+0.005267  pstd=0.010832  min=-0.007182 max=+0.031560  改善側=11/15  同値=2
    phase_macro_f1     平均Δ=+0.014511  中央値Δ=+0.005795  pstd=0.034250  min=-0.018389 max=+0.138447  改善側=11/15  同値=1
    phase_jaccard      平均Δ=+0.020975  中央値Δ=+0.016402  pstd=0.028819  min=-0.002543 max=+0.120275  改善側=13/15  同値=1
    phase_edit_score   平均Δ=+3.905476  中央値Δ=+2.090965  pstd=10.998652 min=-7.727273 max=+38.095238 改善側=8/15   同値=3
    phase_seg_f1_10    平均Δ=+0.032564  中央値Δ=+0.024893  pstd=0.099191  min=-0.122269 max=+0.355556  改善側=9/15   同値=3
    phase_seg_f1_25    平均Δ=+0.057288  中央値Δ=+0.034535  pstd=0.086770  min=-0.034305 max=+0.355556  改善側=12/15  同値=2
    phase_seg_f1_50    平均Δ=+0.045762  中央値Δ=+0.041176  pstd=0.099224  min=-0.072072 max=+0.355556  改善側=9/15   同値=2

**特定の動画が支配していないかの検査**（一つの分け方を除いたときの平均Δ）:

    accuracy  全 15 組 = +0.008282
      動画 07（Δ=+0.031560）を除くと +0.006619（変化 -0.001663、20%）
      動画 12（Δ=+0.027915）を除くと +0.006879（変化 -0.001402、17%）
      動画 10（Δ=+0.021063）を除くと +0.007369（変化 -0.000913、11%）
    macro-F1  全 15 組 = +0.014511
      動画 12（Δ=+0.138447）を除くと +0.005658（変化 -0.008853、61%）   ← 支配している
      動画 04（Δ=+0.018914）を除くと +0.014196（変化 -0.000315、 2%）
      動画 07（Δ=-0.018389）を除くと +0.016861（変化 +0.002350、16%）

**主終点の accuracy はどの 1 組を除いても正のままで、最大の変化も 20% にとどまる。**
**macro-F1 は動画 12 が支配している。** 1 組を除くと平均が 61% 縮む。

## E12. 工程の支持（評価側に現れない工程の扱い）

     video  eval frames  現れる工程数  現れない工程
        01          913            6  disinfection,dressing,irrigation
        02          461            7  disinfection,dressing
        03         1089            7  disinfection,dressing
        04         1329            6  design,disinfection,dressing
        05         1225            7  disinfection,irrigation
        06         1379            7  dressing,irrigation
        07         1711            7  disinfection,dressing
        08         1400            6  disinfection,dressing,irrigation
        09          518            4  closure,disinfection,dressing,hemostasis,irrigation
        10          997            7  disinfection,irrigation
        11          754            7  design,disinfection
        12          609            6  design,disinfection,dressing
        13          822            6  disinfection,dressing,irrigation
        14         1810            5  closure,design,disinfection,dressing
        15          420            4  closure,disinfection,dressing,hemostasis,irrigation

macro-F1 は**評価側に支持のある工程だけ**で平均される（`src/egosurgery/metrics/phase.py:258-262`、先行契約で実装を確認）。
**したがって分母は分け方ごとに 4 から 7 まで違う。** 分け方をまたいだ macro-F1 の平均は同じ土俵の平均ではない。
主終点を accuracy に固定した事前登録の判断は、この点で整合している。
`disinfection` はどの分け方でも評価側に現れない。

## E13. 既存の分割が書き換えられていないこと

    $ git --no-pager diff HEAD -- data/splits/ | grep -c .     → 0
    $ git status --porcelain=v1 -uall data/splits/ | grep -c . → 0

**陽性対照**（検査が変更を検出できるか）:

    ego_val.txt へ 1 行足したとき   diff 行数 = 8      ← 検出される
    戻したあと                      diff 行数 = 0
    cmp による内容の照合            一致
    sha256: c28816de... (train) / f1bc456a... (val) / 7edeab62... (test)

## E14. 変更範囲と禁止領域

    $ source .venv/bin/activate && make forbidden-check; echo "EXIT_CODE=$?"
    EXIT_CODE=2
    base=origin/phase0 changed=231 checked=231 status=fail errors=[]

**内訳を一件ずつ分ける。**

| 区分 | 件数 | 中身 |
|---|---:|---|
| 違反・**本契約が作った run の内側** | **210** | `experiments/transfer/b2a_lovo_v{01..15}_{toolpresence,oracletool}_001_*_seed42/` の 30 ディレクトリ × 7 ファイル |
| 違反・**本契約の成果物でない** | **16** | 同時に走る別契約の未追跡ファイル。`experiments/analysis/error_shape_selectivity/` 7 件、`experiments/analysis/lovo_decision_rule/` 9 件 |
| 違反でない | 5 | `scripts/train_b2a.py` / `tasks/T-2026-08-26-oracle-ceiling-lovo/{SPEC.md,prereg.md,spec.yaml}` / `tasks/inbox.d/T-2026-08-26-oracle-ceiling-lovo.md` |

**検査は 231 件のうち 5 件を違反としていないため、「何でも違反にする」壊れ方ではない。**
SPEC §7 が予告したとおり、run を作る契約はこの検査を構造的に通せない。

別契約の 16 件には**触れていない。commit にも含めていない。**
SPEC Task 1 Step 2 は「汚れていれば退避」と述べるが、**退避すると他契約の実行中の作業を壊す。**
実行中であることは mtime で確かめた（当時 75 秒前に更新されていた）。

**プロセスによる確認は使えなかった。**

    $ pgrep -f "lovo_decision_rule" | grep -c .        → 2
    $ pgrep -f "zzz_no_such_token_xyz" | grep -c .     → 2      ← 陰性対照も 2 を返す
    /proc の cmdline 走査でも、陰性対照 "qqq_absent_marker" が 1 件を返した

いずれも**自分の命令行にその語が含まれるため**で、`conventions#issuer_cautions` 注意 6 の実測と同型である。
**したがって判断は mtime に拠った。**

`make runindex` は回していない（禁止 5・E15 の逸脱）。
索引が本契約の run を `task_id` 付きで拾うことは、先行契約で収穫器の読取関数を陽性・陰性の両方向で確かめてある。
本契約の 30 本すべてに `task_id` が刻まれていることは E10 のとおり。

## E15. 試験

    $ pytest tests/ -q   （変更後）  5 failed, 472 passed, 22 warnings in 23.96s
    $ git stash push -- scripts/train_b2a.py && pytest tests/ -q   （変更前）
                                     5 failed, 472 passed, 22 warnings in 23.39s
    $ diff <(grep '^FAILED' before|sort) <(grep '^FAILED' after|sort); echo "diff_exit=$?"
    diff_exit=0

**失敗集合は変更前後で完全に一致（5 件）。本契約の変更に由来する失敗は 0 件。**
5 件はいずれも既存の失敗（`test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics` と
`test_research_logger.py` の 4 件）で、先行契約でも同じ 5 件だった。

## E16. 自動同期の抑止

    $ touch .sync-pause; ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 25 22:30 .sync-pause
    $ grep -c sync-pause ~/bin/m2-sync.sh
    2                                        ← 稼働中の版は対応済み

作業ツリーは開始時点で本契約の契約 3 ファイルのみが未追跡であり、**退避を要するものは無かった。**
別契約の未追跡ファイルはその後に現れたものである（E14）。

## E17. 分岐の起点と PR の base

**SPEC Task 5 Step 8 が明記を求めている箇所である。**

    $ git merge-base HEAD phase0  → 99630357（= HEAD）  ahead=0 behind=0
    $ git merge-base HEAD master  → b887400f            ahead=269 behind=1
    $ gh repo view --json defaultBranchRef -q .defaultBranchRef.name  → master

**起点は `phase0` である。既定の分岐 `master` ではない。** したがって PR の base は `phase0` とする。

先行契約の PR #152 は `gh pr create --base master` で起票したが、実際の base は `phase0` で MERGED になっていた
（`gh pr view 152` の `baseRefName: phase0` / `mergedAt: 2026-08-25T22:15:24Z`）。
**先行契約の報告で「master 宛」と書いたのは誤りである。**

## E18. 台帳への送出

`make task-report` は **exit 0 で送出に成功した。** 台帳の応答:

    {"task_id": "T-2026-08-26-oracle-ceiling-lovo", "verdict": "pass",
     "n_issuer_defects": 3,
     "report_sha256": "38630f280780957954f8b2a3e33068656dfda7d56cd527338b37c4a9d88a0fab",
     "report_bytes": 12830, "replaced_blocks": 0}

`source scripts/load_env.sh` はパイプに繋がず同じ命令の中で実行した。
**先行契約でパイプが副シェルを起こして export が消えた事故を繰り返さないためである。**
秘匿の検査は無効にしていない。外部への送信は `make task-report` の 1 経路のみで行った。
