# 証跡の記録 — T-2026-08-26-det2phase-segmentation-lovo

事実の記録は `RESULT.md`。本書は命令とその出力、対照の出力、変更範囲、台帳の応答を置く。
ホスト `lecun` / 分岐 `feat/det2phase-segmentation-lovo` / 起点 `phase0` / シェル `/usr/bin/zsh`。

---

## E1. 時刻と締切

    $ TZ=Asia/Tokyo date '+%F %T JST'; date +%s
    2026-08-26 13:25:39 JST
    1787718339

T0 = 1787718339。**開始から十二時間**が上限 → 締切 = 1787761539（2026-08-27 01:25:39 JST）。

| Phase | 入口の経過 | 締切まで |
|---|---:|---:|
| A | 6502 秒 (108 分) | 611 分 |
| B | 6553 秒 (109 分) | 610 分 |
| C | 6716 秒 (112 分) | 608 分 |
| D | 7872 秒 (131 分) | 588 分 |
| E | 約 140 分 | 約 580 分 |

## E2. 検証（L1+L2）

    $ make task-validate TASK=T-2026-08-26-det2phase-segmentation-lovo; echo "EXIT_CODE=$?"
    EXIT_CODE=0
    OK   T-2026-08-26-det2phase-segmentation-lovo
    1 task(s), 0 failed

**WARN は 0 件である。** 先行する二つの契約では L2-8（母集団の移動）が出ていたが、
本契約は `created_from.counts` が `{index: 1177, experiments: 213, verdicts: 1038}` と現在に一致しており、出ない。
（本契約は `make runindex` を回していないため索引は動いていない。）

参照の解決。`inputs.denominator.ref` は
`phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`。
先行契約で `n_runs=17 / n_seeds=3 / split=val / accuracy_mean=0.8973014948553679 /
pstd=0.005917073407586465 / sstd=0.006099179663503103` を実測しており、
`require`（n_seeds>=3・sigma present・split=val）を満たす。
**本契約はこの分母を使っていない。** 対は同じ入口・同じ種で新たに作ったためである。
`inputs.sigma_policy` は省略されており `conventions#sigma` の既定
（`series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired`）を継承する。
**ただし本契約の判定は先行契約が確定させた則に従うため、この既定は記録のみに用いた。**
`contract.conventions_rev` は `a8c07e813696d3720ceee648e8aa202224285955` で、
`git diff <rev>..HEAD -- context/conventions.md` は空。L2-6 の WARN は出ていない。

## E3. プリフライト（L3）

初回:

    EXIT_CODE=2
    P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=... sys.prefix=...
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP UNKNOWN 判定基準が未確定。決定性設定は実行プロセス内で行われ外部から観測できない。backlog B-20 が未解決
    P4 prereg_committed       FAIL prereg.commit が未記入
    P5 frozen_source_hash     PASS sha256=03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    P6 decisions_answered     FAIL 未回答 4 件: 採用する則を一つへ絞ること; 主終点を分類の指標へ移すこと; 分母を別の実験へ移すこと; 学習の数式や最適化に触れること
    P7 destination_writable   PASS   P8 contract_valid PASS   P9 spec_lint PASS 規則 8 件を検査し該当なし
    RESULT: 5 PASS / 0 WARN / 2 SKIP / 2 FAIL

**SKIP は合格ではない。** P3 が SKIP のため、決定化は事前登録 §5 の対照で測った（E7）。

P6 の 4 件を起票者へ提示。1 件目は **R2 が本契約のデータに当てられない**ことを受け、
SPEC 第 3 節の逃げ道（当てはめられない場合は理由を記録して効果量と符号の個数だけを出す）を使う決定。
**則を一つへ絞る決定ではない。** 残り 3 件は「行わない」。

    $ git --no-pager log -1 --format='%H %ci'
    081ec004bf35e7167d15ab66425b12ef2293d5e6 2026-08-26 06:13:44 +0000

再実行: `RESULT: 7 PASS / 0 WARN / 2 SKIP / 0 FAIL`（EXIT_CODE=0）。

## E4. Phase A — 前提の統合

### E4.1 先行する二つの契約の成果

    $ grep -n "lovo-holdout\|def load_clips_lovo\|def check_no_leak\|def video_of" scripts/train_b2a.py
    143: def video_of / 148: def check_no_leak / 157: def load_clips_lovo / 458: "--lovo-holdout"
    $ git log --oneline -1 -- scripts/train_b2a.py
    ee93885e exp(b2a): the oracle gain shrinks under leave-one-video-out
    $ git status --porcelain=v1 scripts/train_b2a.py | grep -c .
    0                                    ← commit 済みのものがそのまま在る

    $ git ls-files | grep -i "lovo_decision_rule" | grep -c .
    → rules.py / CRITERIA.md / REPORT.md / results.json / r2_results.json / folds/ / r2/ が版管理下

**二つとも統合されている。**

### E4.2 術具を渡さない腕の実在

    $ python scripts/train_b2a.py --help | grep -E "^  --"
    --tool-source {pred,oracle} / --mask-tool-dim / --mask-tool-dims / --drop-gap /
    --tool-noise-rate / --tool-noise-dims / --lovo-holdout / --deterministic / --task-id ...

`--mask-tool-dims 0,...,14` が術具 15 次元だけを 0 埋めする（実装 99-104 行）。GAP は別に連結される（135 行）。
**配線は不要であった。**

**陰性対照（実在しない腕を同じ 2 方法で探す）**

    CLI:  --no-such-arm-xyz  → 0 件
    実装: no_such_arm_xyz    → 0 件

## E5. 腕の分離（事前登録 §5 が「特に重要」とする対照）

実際に読み込んだ特徴 (1515, 2063) = GAP 2048 ⊕ tool 15 で照合した。

**陽性対照 — 術具に対応する部分は二つの腕で違うはず**

    違う要素 = 22616 / 22725 = 99.52%   完全一致か = False
    渡す腕の術具部分   : 範囲=[0.000000,0.973633] 非零要素=22616
    渡さない腕の術具部分: 範囲=[0.000000,0.000000] 非零要素=0

**陰性対照 — 術具以外の部分は一致するはず**

    GAP 2048 次元の完全一致 = True
    違う要素 = 0 / 3102720          ← 術具以外は一切落としていない

**検査そのものが空振りでないことの確認**

    dim 0 だけ落とした腕 vs 渡す腕: 術具部分の違う要素 = 1513   （15 次元全部の 22616 より小さい）
    同じ腕を二度読んだときの完全一致 = True

## E6. 漏れの検査（証跡を残さない）

    陰性対照（正しく分けた）  : train=["02_1","03_2","15_1"] eval=["01_1"] → 検出 = []
    陽性対照（意図的に漏らした）: train=["02_1","01_2"]        eval=["01_1"] → 検出 = ['01']

30 本すべての `config.yaml` の `lovo` 節を照合した。

    検査した run = 30 本 / 漏れのあった run = 0
    task_id が刻まれていない run = 0
    上限測定専用の印が立っている run = 0     ← 本契約に上限の腕は無いので 0 が正しい

## E7. 決定化の対照

**陰性対照（同じ種なら一致）— 契約をまたいだ再現性で取った。**
先行契約 `T-2026-08-26-oracle-ceiling-lovo` の v01 pred（同一設定・数時間前）と本契約の v01 withtool を照合した。

    $ diff <(grep '^\[b2a\]\[epoch' lovo/v01_pred.log) <(grep '^\[b2a\]\[epoch' seg/v01_withtool.log)
    diff_exit=0   差分行数=0
    先行契約 v01_pred     : best @epoch 49: acc=0.9671 macroF1=0.9535
    本契約   v01_withtool : best @epoch 49: acc=0.9671 macroF1=0.9535

**陽性対照（種を変えれば変わる）**

    $ python scripts/train_b2a.py --lovo-holdout 01 --tool-source pred --seed 123 --epochs 50 --deterministic --no-evidence
    RC=0 ELAPSED_SEC=41
    seed42 vs seed123: diff_exit=1  差分行数=100
    seed123: best @epoch 50: acc=0.9693 macroF1=0.9615

## E8. 実行の順序と所要時間

**対の両側は分け方ごとに隣接して交互（notool → withtool）に走らせた。**
各対の入口で残り時間を確かめ、両側が入らないなら始めない条件を実装した（発動せず）。

```
seq  |  video  |  arm  |  start_epoch  |  elapsed_sec  |  rc  |  remaining_min_at_pair_entry  |  note
0  |  01  |  notool  |  UNKNOWN(測っていない)  |  2  |  2  |  UNKNOWN  |  単語分割に頼った書き方で argparse が拒否。証跡なし。開始時刻を記録していなかった
1  |  01  |  withtool  |  1787724892  |  37  |  0  |  610  |  config.yaml の mtime による実測
2  |  01  |  notool  |  1787724959  |  49  |  0  |  609  |  config.yaml の mtime による実測。走り直し
3  |  02  |  notool  |  1787725055  |  35  |  0  |  608  |  
4  |  02  |  withtool  |  1787725090  |  45  |  0  |  608  |  
5  |  03  |  notool  |  1787725135  |  35  |  0  |  606  |  
6  |  03  |  withtool  |  1787725170  |  50  |  0  |  606  |  
7  |  04  |  notool  |  1787725220  |  38  |  0  |  605  |  
8  |  04  |  withtool  |  1787725258  |  35  |  0  |  605  |  
9  |  05  |  notool  |  1787725293  |  33  |  0  |  604  |  
10  |  05  |  withtool  |  1787725326  |  36  |  0  |  604  |  
11  |  06  |  notool  |  1787725362  |  35  |  0  |  602  |  
12  |  06  |  withtool  |  1787725397  |  35  |  0  |  602  |  
13  |  07  |  notool  |  1787725432  |  32  |  0  |  601  |  
14  |  07  |  withtool  |  1787725464  |  41  |  0  |  601  |  
15  |  08  |  notool  |  1787725505  |  42  |  0  |  600  |  
16  |  08  |  withtool  |  1787725547  |  42  |  0  |  600  |  
17  |  09  |  notool  |  1787725589  |  44  |  0  |  599  |  
18  |  09  |  withtool  |  1787725633  |  41  |  0  |  599  |  
19  |  10  |  notool  |  1787725674  |  46  |  0  |  597  |  
20  |  10  |  withtool  |  1787725720  |  34  |  0  |  597  |  
21  |  11  |  notool  |  1787725754  |  36  |  0  |  596  |  
22  |  11  |  withtool  |  1787725790  |  34  |  0  |  596  |  
23  |  12  |  notool  |  1787725824  |  35  |  0  |  595  |  
24  |  12  |  withtool  |  1787725859  |  36  |  0  |  595  |  
25  |  13  |  notool  |  1787725895  |  38  |  0  |  594  |  
26  |  13  |  withtool  |  1787725933  |  48  |  0  |  594  |  
27  |  14  |  notool  |  1787725981  |  39  |  0  |  592  |  
28  |  14  |  withtool  |  1787726020  |  39  |  0  |  592  |  
29  |  15  |  notool  |  1787726059  |  42  |  0  |  591  |  
30  |  15  |  withtool  |  1787726101  |  45  |  0  |  591  |  
DONE
```

**seq 0 は `zsh` が引数を単語分割しなかったための失敗である。**

    EXTRA="--mask-tool-dims $ALLD"   →  python ... $EXTRA
    train_b2a.py: error: unrecognized arguments: --mask-tool-dims 0,1,2,...,14
    RC=2 / 所要 2 秒 / 証跡ディレクトリは作られていない

`conventions#issuer_cautions` の「シェルの前提: 単語分割が起きない」に該当する。
**失敗は大声で落ちたため、誤った腕の証跡は 1 件も残っていない。**
分割に依存しない書き方（引数を直接並べる）で走り直した。

**実行者の誤りの訂正。** 手で書いた fold 01 の 3 行のうち、当初 `start_epoch` に
測っていない値（`1787723920` 等）を書いていた。**これは捏造である。**
証跡の `config.yaml` の mtime（`ExperimentManager` が run 開始時に書く）で実測に置き換え、
記録の無いものは `UNKNOWN(測っていない)` と記した。

    v01 withtool: config.yaml mtime = 1787724892 (2026-08-26 15:14:52 JST)
    v01 notool  : config.yaml mtime = 1787724959 (2026-08-26 15:15:59 JST)

所要時間（実測・秒、成功した 30 本）: 最小 32 / 最大 50 / 平均 39.5。
**先行契約が同じ入口の一つ抜き検証で測った 34〜49 秒（平均 38.0）とほぼ同じである。**

本数の計算（Phase B 終了時点）:

    残り = 36504 秒 = 608.4 分 = 10.14 時間
    1 本の所要（安全側に実測の最大 49 秒）/ 対 1 組 = 98 秒
    入る対の組数 = floor(36504 / 98) = 372 組
    残り 14 組に要する時間 = 1372 秒 = 22.9 分     ← 全 15 組が入る

終了コードの内訳（**終了コードを件数と呼ばず、数える命令で数えた**）:

    $ awk -F'\t' 'NR>1 && $6!="" {print $6}' order.txt | sort | uniq -c
         30 0
          1 2

## E9. 分け方ごとの内訳

     video  notool edit  withtool edit      Δedit    Δseg@50       Δacc
        01     60.97561       88.88889  +27.91328   +0.24106   +0.02300
        02     63.63636      100.00000  +36.36364   +0.22222   +0.01735
        03     40.74074       45.00000   +4.25926   +0.17280   +0.04224
        04     13.63636       24.80620  +11.16984   +0.17671   +0.02634
        05     57.84314       64.28571   +6.44258   +0.07506   +0.02449
        06     38.63636       39.41441   +0.77805   +0.00940   +0.02756
        07     28.33333       25.79365   -2.53968   +0.02797   +0.02221
        08     33.40426       31.69811   -1.70614   -0.13208   +0.06571
        09     13.33333       28.57143  +15.23810   +0.26797   +0.04440
        10     61.66667       72.04301  +10.37634   +0.09989   +0.02207
        11     88.88889       85.00000   -3.88889   +0.06486   +0.01724
        12     36.84211       65.00000  +28.15789   +0.33333   +0.14450
        13     75.00000       84.61538   +9.61538   +0.08920   +0.01703
        14     27.71382       35.62500   +7.91118   +0.12215   +0.00773
        15     85.71429       85.71429   +0.00000   +0.07692   +0.02381

## E10. 効果量と符号の個数（**判定とは別・則に依存しない**）

    edit（主終点）              Δ=  +10.00606  中央値=  +7.91118  pstd=11.82350  符号 +11/-3/0 1 (n=15)
    seg-F1@10                Δ=   +0.12814  中央値=  +0.13251  pstd= 0.10088  符号 +12/-2/0 1 (n=15)
    seg-F1@25                Δ=   +0.11599  中央値=  +0.06486  pstd= 0.09372  符号 +14/-0/0 1 (n=15)
    seg-F1@50                Δ=   +0.12316  中央値=  +0.09989  pstd= 0.11281  符号 +14/-1/0 0 (n=15)
    accuracy（根拠に用いない）    Δ=   +0.03505  中央値=  +0.02381  pstd= 0.03226  符号 +15/-0/0 0 (n=15)
    macro-F1（根拠に用いない）    Δ=   +0.06518  中央値=  +0.04902  pstd= 0.04651  符号 +15/-0/0 0 (n=15)
    jaccard                  Δ=   +0.08817  中央値=  +0.06163  pstd= 0.05406  符号 +15/-0/0 0 (n=15)

## E11. 確定した則の適用

**則の実装は先行契約の成果物をそのまま使った**（`experiments/analysis/lovo_decision_rule/rules.py`）。
新たに書き起こしていない。

    指標                        R0 統計量  R0      R1 統計量  R1      R3 p       R3     R2
    edit（主終点）                 3.278  検出      2.200  検出    0.00293  検出    未適用
    seg-F1@10                  4.920  検出      3.302  検出    0.00085  検出    未適用
    seg-F1@25                  4.793  検出      3.217  検出    0.00012  検出    未適用
    seg-F1@50                  4.229  検出      2.838  検出    0.00159  検出    未適用
    accuracy（根拠に用いない）        4.208  検出      2.824  検出    0.00006  検出    未適用
    macro-F1（根拠に用いない）        5.428  検出      3.644  検出    0.00006  検出    未適用
    jaccard                    6.316  検出      4.240  検出    0.00006  検出    未適用

**R0 は旧則、R3 は候補外**（`CRITERIA.md` 第 6 節・S3 を満たさない）。比較のため値だけ併記した。

### R2 を当てられない理由（**片方だけを採用したのではない**）

`r2_aggregate.py` の設計は次のとおりである（転記ではなく原文の要旨）。

> d_i = mu + b + e_i と書ける。b は 14 動画の学習側が共有されることから来る成分で、
> すべての fold に同じ値が乗る。**1 回の一つ抜き検証しか無いと b は mu と見分けがつかない。
> 学習側が実際に違う状態を複数作って初めて b の散らばりが測れる。**

したがって R2 は**反復 LOVO を必要とする。** 代理側の記録 `r2/presence.json` を実測すると

    構造 = ['script','m','reps','seed','subsets','replicates']
    反復の数 = 24
    1 反復の腕 = ['raw','gap-free oracle','HMM L=2']、各腕 12 fold
    → 24 反復 × 12 fold × 2 腕 = 576 run

さらに反復は 15 動画から 12 動画を選び直すため、**動画の母集団を絞る配線が別途要る**
（現在の `--lovo-holdout` は「抜いた 1 本以外すべて」を学習側にする）。
契約の宣言は `expected_runs: 30` である。

**SPEC 第 3 節の「当てはめられない場合は、その理由を記録して効果量と符号の個数だけを出す」に従った。**
効果量と符号の個数は E10 に、則に依存しない形で残してある。

## E12. 判定が特定の分け方に支配されていないか

**R1 の閾は 2.0 である。主終点 edit の統計量は 2.200 で、閾に近い。**
一つの分け方を除いて R1 を取り直した。

    edit（主終点）: 全 15 組 Δ=+10.00606 R1=2.200 検出
      動画 01 (Δ=+27.91328) を除く: 平均Δ= +8.72697  R1=1.988  検出せず   ← 判定が変わる
      動画 12 (Δ=+28.15789) を除く: 平均Δ= +8.70950  R1=1.990  検出せず   ← 判定が変わる
      動画 09 (Δ=+15.23810) を除く: 平均Δ= +9.63234  R1=2.021  検出
      動画 04 を除く R1=2.068 / 動画 10 を除く R1=2.079 / 動画 13 を除く R1=2.090
      動画 02 を除く R1=2.107 / 動画 14 を除く R1=2.118 / 動画 05 を除く R1=2.144
      動画 03 を除く R1=2.189 / 動画 06 を除く R1=2.272 / 動画 15 を除く R1=2.293
      動画 08 を除く R1=2.342 / 動画 07 を除く R1=2.368 / 動画 11 を除く R1=2.413
      → 判定が変わる分け方 = ['01','12']  (2/15)

    seg-F1@50: 全 15 組 Δ=+0.12316 R1=2.838 検出
      どの 1 組を除いても検出のまま。最小は動画 02 を除いたときの R1=2.608
      → 判定が変わる分け方 = なし  (0/15)

**主終点 edit の判定は脆い。seg-F1@50 の判定は脆くない。**

## E13. 代理モデルとの並び

代理側の値は先行契約の成果物 `folds/gap_vs_presence.json` と `r2_results.json` から取り、
同じ `rules.py` を当てた。

                                                       Δ  符号        R0        R1        R2
    --- edit（主終点）
    代理 C01  pres − gap（契約 §1.2 が引く結論）     +32.20040  +15/-0/0   6.440 検出  4.323 検出  検出
    代理 C04  gap+pres − gap（本契約の腕と一致）       +4.76391  +12/-3/0   2.920 検出  1.960 検出せず 検出
    本契約   withtool − notool（本番の時系列）       +10.00606  +11/-3/1   3.278 検出  2.200 検出  未適用
    --- seg-F1@50
    代理 C01  pres − gap（契約 §1.2 が引く結論）      +0.33820  +15/-0/0   6.091 検出  4.089 検出  検出
    代理 C04  gap+pres − gap（本契約の腕と一致）       +0.04644  +12/-3/0   2.123 検出  1.425 検出せず 検出
    本契約   withtool − notool（本番の時系列）        +0.12316  +14/-1/0   4.229 検出  2.838 検出  未適用

**C01 と C04 は別の比較である。**
C01 は GAP を丸ごと落として術具だけにする比較、C04 は GAP に術具を足す比較である。
`conclusions.py` の記載は C01 が `pres − gap`「予測 presence を渡す（対 GAP のみ）」、
C04 が `gap+pres − gap`「GAP に presence を足す」。
**契約 §2.1 は「術具の次元だけを落とし、他の入力には触れないこと」と指示しており、
本契約の腕は C04 と一致する。契約 §1.2 が「十五の分け方すべてで同じ向き」と述べたのは C01 である。**

## E14. 既存の分割が書き換えられていないこと

    $ git --no-pager diff HEAD -- data/splits/ | grep -c .          → 0
    陽性対照: ego_test.txt へ 1 行足すと                            → 9
    戻したあと                                                      → 0   / cmp による内容の照合 = 一致

## E15. 変更範囲と禁止領域

    $ source .venv/bin/activate && make forbidden-check; echo "EXIT_CODE=$?"
    EXIT_CODE=2
    base=origin/phase0 changed=214 checked=214 status=fail errors=[]

| 区分 | 件数 | 中身 |
|---|---:|---|
| 違反・**本契約が作った run の内側** | **210** | `experiments/transfer/b2a_seglovo_v{01..15}_{notool,withtool}_001_*_seed42/` の 30 ディレクトリ × 7 ファイル |
| 違反・**本契約の成果物でない** | **0** | 無し |
| 違反でない | 4 | `tasks/T-2026-08-26-det2phase-segmentation-lovo/{SPEC.md,prereg.md,spec.yaml}` と `tasks/inbox.d/T-2026-08-26-det2phase-segmentation-lovo.md` |

**検査は 214 件のうち 4 件を違反としていないため、「何でも違反にする」壊れ方ではない。**
SPEC 第 4 節 Task 6 Step 2 が予告したとおり、成果物の置き場所そのものが禁止領域として扱われる。

**コードの変更は 0 件である。**

    $ git status --porcelain=v1 scripts/ src/ | grep -c .
    0

術具を渡さない腕は既存の `--mask-tool-dims` で足りたため、**本契約は配線を一切していない。**

## E16. 試験

    $ pytest tests/ -q
    5 failed, 472 passed, 22 warnings in 23.81s
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

**本契約はコードを変更していないため、変更前と変更後は同じ作業ツリーである。**
したがって before と after を別々に測る意味が無く、1 度だけ測って両方に記した。
5 件はいずれも既存の失敗で、先行する二つの契約でも同じ 5 件だった。

## E17. 自動同期の抑止

    $ touch .sync-pause; ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 26 04:26 .sync-pause
    $ grep -c sync-pause ~/bin/m2-sync.sh
    2                                        ← 稼働中の版は対応済み

開始時点の作業ツリーは本契約の契約 3 ファイルのみが未追跡で、**退避を要するものは無かった。**
先行契約の実行中に現れた他ホストの未追跡ファイルは、本契約の開始時点では既に版管理へ入っていた。

## E18. 分岐の起点と PR の base

    $ git merge-base HEAD phase0 → HEAD と一致（ahead=0 behind=0）
    $ gh repo view --json defaultBranchRef -q .defaultBranchRef.name → master

**起点は `phase0`。既定の分岐 `master` ではない。** したがって PR の base は `phase0` とする。

## E19. 台帳への送出

`make task-report` は **exit 0 で送出に成功した。** 台帳の応答:

    {"task_id": "T-2026-08-26-det2phase-segmentation-lovo", "verdict": "partial",
     "n_issuer_defects": 4,
     "report_sha256": "d927f50f77b8bb2d7a2ffd4a91665da20091ea162c5b1395b4288613b69af38d",
     "report_bytes": 12881, "replaced_blocks": 0}

`source scripts/load_env.sh` はパイプに繋がず同じ命令の中で実行した。
秘匿の検査は無効にしていない。外部への送信は `make task-report` の 1 経路のみで行った。
