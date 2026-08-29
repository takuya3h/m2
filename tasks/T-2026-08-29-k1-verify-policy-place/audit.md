# audit — T-2026-08-29-k1-verify-policy-place

実行ホスト `lecun`（`hostname` の出力）。GPU は使用していない。
`experiments/` `data/` `runindex/` へは読み取りのみ。

以下、節ごとに命令とその出力を全文で置く。RESULT.md からは行番号で指す。

---

## 1. 実行環境の実測（記録との食い違いを含む）

    $ hostname
    lecun

    $ git rev-parse --show-toplevel
    /home/ubuntu/slocal/m2

    $ git branch --show-current
    feat/k1-verify-policy-place

🔴 **SPEC §1 が記録として挙げる経路 `/home/ubuntu/slocal2/m2` は lecun に存在しない。**

    $ ls -d /home/ubuntu/slocal2/m2
    ls: cannot access '/home/ubuntu/slocal2/m2': No such file or directory

    $ ls -d /home/ubuntu/slocal*
    /home/ubuntu/slocal

同期の常駐処理自身がこの差を吸収している（`scripts/sync/m2-sync.sh:10`、
`scripts/sync/keeper.sh:28`）。

    M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

したがって記録の `slocal2` は**別ホストの配置**であり、lecun では `slocal` が正しい。
SPEC §7「lecun の repo の位置が記録と違う → 実測を優先」に従い実測を採った。

GPU（`nvidia-smi`。本契約では使用していない。次の契約のための実測）:

    index, name, memory.total [MiB], memory.used [MiB], memory.free [MiB], utilization.gpu [%]
    0, NVIDIA RTX A6000, 49140 MiB, 35 MiB, 48507 MiB, 0 %
    1, NVIDIA RTX A6000, 49140 MiB, 20 MiB, 48521 MiB, 0 %

**RTX A6000 ×2、いずれも空き 48.5GB / 利用率 0%。両枚とも空いている。**

---

## 2. Step A-1 事前記入値の照合

    $ git --no-pager log -1 --format="%H %h %ad %s" -- context/conventions.md
    a8c07e813696d3720ceee648e8aa202224285955 a8c07e81 Tue Aug 25 15:30:37 2026 +0000 feat(context): move issuer references into version control and inject the cautions

    $ git --no-pager log -1 --format="%h %ad %s" -- runindex/
    7918b5dd Sun Aug 16 00:12:23 2026 +0000 exp(s4): 60-seed deterministic sweep -- the upper bound is not detectable

    $ for f in runindex/index.csv runindex/experiments.csv runindex/verdicts.csv; do
        echo "$f: $(($(wc -l < "$f") - 1))"; done
    runindex/index.csv: 1177
    runindex/experiments.csv: 213
    runindex/verdicts.csv: 1038

| 項目 | 事前記入値 | 実測 | 判定 |
|---|---|---|---|
| `conventions_rev` | `a8c07e81` | `a8c07e81` | 一致 |
| `runindex_commit` | `7918b5dd` | `7918b5dd` | 一致 |
| `counts.index` | 1177 | 1177 | 一致 |
| `counts.experiments` | 213 | 213 | 一致 |
| `counts.verdicts` | 1038 | 1038 | 一致 |

**置換不要。** 統合は進んでいたが索引は動いていない（索引の最終変更は 08-16）。

---

## 3. Step A-2 六 run の所在

### 3.1 発見までの経緯

SPEC §1 の「記録上の証跡経路 `experiments/transfer/` 配下」には**存在しない。**

    $ ls -d experiments/transfer/t1a_frozen_src*
    (eval):1: no matches found: experiments/transfer/t1a_frozen_src*

（zsh は一致しないグロブでコマンド自体を実行しない。`issuer_cautions` のシェル前提どおり。
以後 `find` を使った。）

    $ find experiments -maxdepth 3 -type d -name '*frozen_src*' | sort
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_aligndetr_001_t1a_frozen_src_aligndetr_seed42
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_aligndetr_002_t1a_frozen_src_aligndetr_seed456
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_aligndetr_003_t1a_frozen_src_aligndetr_seed123
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_relationdetr_001_t1a_frozen_src_relationdetr_seed123
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_relationdetr_001_t1a_frozen_src_relationdetr_seed42
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_relationdetr_002_t1a_frozen_src_relationdetr_seed456

**六 run すべて実在する。ただし置き場は `experiments/_orphan_no_metrics/transfer/` である。**
relationdetr 側は連番 `001` が二つある（`seed123` と `seed42`）。

### 3.2 中身（読み取り可否）

    $ find experiments/_orphan_no_metrics/transfer -type f | wc -l
    6

    $ find experiments/_orphan_no_metrics/transfer -type f
    .../t1a_frozen_src_aligndetr_001_..._seed42/checkpoints/best_tecno.pth
    .../t1a_frozen_src_aligndetr_002_..._seed456/checkpoints/best_tecno.pth
    .../t1a_frozen_src_aligndetr_003_..._seed123/checkpoints/best_tecno.pth
    .../t1a_frozen_src_relationdetr_001_..._seed123/checkpoints/best_tecno.pth
    .../t1a_frozen_src_relationdetr_001_..._seed42/checkpoints/best_tecno.pth
    .../t1a_frozen_src_relationdetr_002_..._seed456/checkpoints/best_tecno.pth

🔴 **六 run が持つファイルは checkpoint 一つずつ、合計 6 ファイルだけである。**
`metrics.json` `config.yaml` `command.sh` `git_commit.txt` `notes.md` は**一件も無い。**
`predictions/` と `visualizations/` は**空ディレクトリ**である。

**したがって metrics からの再計算は原理的にできない。**

### 3.3 隔離の理由（版管理された記録）

`.gitignore:157-162`:

    # 孤児 run 退避 (#05-lecun): metrics.json/config.yaml/command.sh/git_commit.txt/
    # notes.md がすべて無く checkpoints のみ・失敗ログも無い 9 run を退避。
    # (transfer/t1a_frozen_src ×6, phase1/s4_phase_baseline_*_aligndetr_010-012 ×3)
    # 削除せずローカル保持: checkpoints は再評価用、logs 欠落自体が「失敗 run が台帳に
    # 載らない」運用欠陥の手がかり。回収可能な指標を持つ nmsfree/hand2det_dev は対象外。
    experiments/_orphan_no_metrics/

**metrics の欠落は本契約で生じたものではなく、隔離の時点で既に確認されていた。**
`experiments/_orphan_no_metrics/` は版管理から除外されている（`git check-ignore` が
`.gitignore:162` を返す）。これが前契約で「リポジトリから遡れない」となった機構である。

収穫器も同じ位置づけを明示している（`tools/harvest_runindex.py`、`EXCLUSION_ALLOWLIST`）:

    "_orphan_no_metrics",  # 現状 metrics.json を持たないため走査されないが、規約の意図を明示しておく。

索引側にも一件も無い。

    $ grep -c "t1a_frozen_src" runindex/index.csv runindex/experiments.csv \
        runindex/verdicts.csv runindex/per_class.csv
    runindex/index.csv:0
    runindex/verdicts.csv:0
    runindex/experiments.csv:0
    runindex/per_class.csv:0

    $ find runindex/runs -name '*t1a_frozen_src*' | wc -l
    0

### 3.4 六 run の同一性（隔離前の記録との照合）

版管理された `experiments/analysis/t1a_diag_2026-07-29/csv/t2_ckpt_inventory.csv` に、
隔離前の経路 `experiments/transfer/...` での md5 が残っている。現物と突き合わせた。

| run | 記録の md5 | 現物の md5 | 大きさ | 判定 |
|---|---|---|---|---|
| aligndetr_001_seed42 | `95fc689143841d80f021bbb89160e95f` | `95fc689143841d80f021bbb89160e95f` | 2,599,650 | 一致 |
| aligndetr_002_seed456 | `65e8423c1bcf840aaf05935bc8cc2cd5` | `65e8423c1bcf840aaf05935bc8cc2cd5` | 2,599,650 | 一致 |
| aligndetr_003_seed123 | `595b9010a63f0aed47894e9c0080cb22` | `595b9010a63f0aed47894e9c0080cb22` | 2,599,650 | 一致 |
| relationdetr_001_seed123 | `1710ec8d4fdbaf3f318cba48b6e04b0a` | `1710ec8d4fdbaf3f318cba48b6e04b0a` | 2,599,650 | 一致 |
| relationdetr_001_seed42 | `16cee16661c31dd91207424f51112900` | `16cee16661c31dd91207424f51112900` | 2,599,650 | 一致 |
| relationdetr_002_seed456 | `72e75d8a498b29a58bc894bc5f75428c` | `72e75d8a498b29a58bc894bc5f75428c` | 2,599,650 | 一致 |

**6/6 一致。** 六つの md5 は互いに異なるため、複製ではなく別個の六 run である。
**現物は隔離前に記録された当の六 run である**（隔離は移動であって差し替えではない）。

### 3.5 日付（学習時刻としては使えない）

    $ find experiments/_orphan_no_metrics/transfer -name 'best_tecno.pth' -printf '%T@ %p\n' | sort -n
    1783705669  relationdetr_001_seed123
    1783705670  relationdetr_001_seed42
    1783705695  aligndetr_001_seed42
    1783705699  relationdetr_002_seed456
    1783705716  aligndetr_003_seed123
    1783705718  aligndetr_002_seed456

日時では 2026-07-10 17:47:49 〜 17:48:38。**六件が 49 秒の中に収まっている。**

生成器 `scripts/run_when_gpu_free.sh` の Phase 3 は relationdetr(42→123→456) →
aligndetr(42→123→456) を `--epochs 50` で**逐次**回す実装である。50 epoch × 6 run が
49 秒で終わることはなく、順序も逐次の順と食い違う。

🔴 **したがって、この mtime は学習の完了時刻ではなく複製の時刻である。**
**六 run がいつ・どのホストで学習されたかは、現物からは判別できない（UNKNOWN）。**

### 3.6 学習ログの所在

生成器はログを `/tmp` へ出していた（`scripts/run_when_gpu_free.sh`）:

    LOG_DIR="${GPU_WAITER_LOG_DIR:-/tmp/gpu_waiter_logs}"
    ... > "$LOG_DIR/tecno_t1a_relation_seed${seed}.log" 2>&1

    $ ls -la /tmp/gpu_waiter_logs
    ls: cannot access '/tmp/gpu_waiter_logs': No such file or directory

**消失している。** metrics を回収できる経路はここにも無い。

---

## 4. Step A-3 追跡外 run の棚卸し（読み取りのみ）

判定は収穫器と同じ定義に合わせた。`tools/harvest_runindex.py` の走査は
`EXPERIMENTS.rglob("metrics.json")` の親を run とする（同ファイル 4790 行）。

索引側の `path` 列には `experiments/` 接頭辞を持たない旧様式が 29 件あるため、
**両者を正規化してから差集合を取った**（正規化しないと 29 件が偽の欠落として出る）。

    走査 run（metrics.json の親）: 1209
    索引 path（正規化後の一意）  : 1177
    追跡外（metrics 有り・索引に無い）: 61
    索引にあるが走査に出ない        : 29

**(i) metrics.json を持ち索引に無い run — 61 件**（すべて `experiments/transfer/` 配下）

| 群 | 件数 | 日付 |
|---|---|---|
| `b2a_det2phase_oracletool_009_..._seed42` | 1 | 2026-08-25 |
| `b2a_lovo_v01..v15_{oracletool,toolpresence}_001_..._seed42` | 30 | 2026-08-26 |
| `b2a_seglovo_v01..v15_{notool,withtool}_001_..._seed42` | 30 | 2026-08-26 〜 08-28 |

全 61 件の経路と日付は
`/tmp/claude-1000/.../scratchpad/a3_inventory.txt` に出力した（本節の表がその要約）。
いずれも索引の最終更新（08-16, `7918b5dd`）より後に生成された run である。
**取りこぼしではなく、索引を再生成していないだけである。**

**(ii) metrics.json を持たず checkpoints だけを持ち索引に無い — 19 件**

    experiments/_orphan_no_metrics/phase1/s4_phase_baseline_010_..._aligndetr_seed42
    experiments/_orphan_no_metrics/phase1/s4_phase_baseline_011_..._aligndetr_seed123
    experiments/_orphan_no_metrics/phase1/s4_phase_baseline_012_..._aligndetr_seed456
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_aligndetr_001_..._seed42
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_aligndetr_002_..._seed456
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_aligndetr_003_..._seed123
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_relationdetr_001_..._seed123
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_relationdetr_001_..._seed42
    experiments/_orphan_no_metrics/transfer/t1a_frozen_src_relationdetr_002_..._seed456
    experiments/baselines/s0_007_codetr_bbox_seed42
    experiments/baselines/s0_008_codetr_bbox_seed123
    experiments/baselines/s0_009_codetr_bbox_seed456
    experiments/detector_improve/augstrong_hires_seed42
    experiments/detector_improve/augstrong_seed123
    experiments/detector_improve/augstrong_seed42
    experiments/detector_improve/augstrong_seed456
    experiments/transfer/_smoke_artifacts_ctrl
    experiments/transfer/_smoke_artifacts_inj
    experiments/transfer/_smoke_fullval

（先頭 9 件が本契約の対象である隔離 9 run。うち 6 件が K1 の六 run。）

**(iii) 索引にあるが走査に出ない 29 件は欠落ではない。**
`transfer/hc_seed42` 等の旧様式経路で、`*result*.json` から収穫された別系統である
（`tools/harvest_runindex.py:1310` の `TRANSFER_LEGACY`）。実在する 6 件を抜き取って
確かめたところ、ディレクトリは在るが `metrics.json` を持たない。走査定義の違いによる。

**索引への書き込みは行っていない**（§7 参照）。

---

## 5. Task 1 記録値の照合

### 5.1 再計算できる量とできない量

六 run に metrics が無い以上、**§4 が求める四つの再計算のうち三つは実行できない。**

| 求められた再計算 | 可否 | 理由 |
|---|---|---|
| 両側の 3-seed 平均 acc とばらつき | **不可** | run の metrics が無い |
| 両側の hemostasis F1 の 3-seed 平均とばらつき | **不可** | 同上 |
| seed 対応の paired 差（三つ）とその平均・ばらつき | **記録値からのみ可** | 記録側に seed 別の差 3 件が書かれている |
| aligndetr の特徴の由来 | **部分的に可** | config が無いため直接の連結は取れない（§6） |

そこで、**記録側に seed 別で残る唯一の量（paired 差 3 件）と、平均どうしの引き算**に
対して検算器を作った。これは**記録の内部整合**の検査であって、run への遡及ではない。

### 5.2 許容差の扱い（訂正を含む）

SPEC §1 は「許容差は各値の表示桁の丸め幅」と定める。最初に書いた検算器はこれを
**出力側にだけ**適用し、入力（`-0.0561` 等の 4 桁表示）を実数として扱っていた。
その結果 `mean(paired)` が「不一致」と出た（再計算 −0.069067 / 記録 −0.06909、差 2.3e-5）。

`issuer_cautions` 注意 7「丸めた表示を実数として扱わない」に反していたため、
**入力の丸め幅を出力へ伝播させる**方式に改めた。伝播は解析式ではなく、
各入力を ±(丸め幅/2) だけ動かした端点の総当たり（2^n 通り）で区間を出している
（`pstdev` は非線形のため解析式が使えない）。検算器は
`/tmp/claude-1000/.../scratchpad/recheck.py`。

### 5.3 検算器の出力（全文）

    == 陽性対照 1: paired 差 3 件から平均・ばらつきを再計算 ==
    mean(paired 3 件)                   再計算=-0.069067 伝播区間=[-0.069117,-0.069017] 記録=-0.069090(±5e-06)  一致
    pstdev(paired 3 件) ddof=0          再計算=+0.009480 伝播区間=[+0.009434,+0.009526] 記録=+0.009490(±5e-06)  一致
    stdev (paired 3 件) ddof=1          再計算=+0.011610 伝播区間=[+0.011555,+0.011666] 記録=+0.009490(±5e-06)  不一致
       -> 記録の sigma 系統は ddof=0 (pstd)。conventions#sigma の既定 series: pstd と一致

    == 陽性対照 2: 平均どうしの引き算 ==
    acc_rel_mean - denom               再計算=+0.049000 伝播区間=[+0.048900,+0.049100] 記録=+0.049000(±5e-05)  一致
    acc_ali_mean - denom               再計算=-0.020100 伝播区間=[-0.020200,-0.020000] 記録=-0.020100(±5e-05)  一致
    acc_ali - acc_rel (=paired 平均)     再計算=-0.069100 伝播区間=[-0.069200,-0.069000] 記録=-0.069090(±5e-06)  一致

    == 陰性対照: seed を一つ除くと一致しなくなるか ==
      seed#1 除外 -> mean=-0.075550 区間=[-0.075600,-0.075500] 不一致（期待どおり）
      seed#2 除外 -> mean=-0.067300 区間=[-0.067350,-0.067250] 不一致（期待どおり）
      seed#3 除外 -> mean=-0.064350 区間=[-0.064400,-0.064300] 不一致（期待どおり）

    == 陰性対照 2: 検算器が常に一致を返さないことの確認（偽値を入れる） ==
      paired#3 を -0.0300 に差し替え -> mean=-0.052900 区間=[-0.052950,-0.052850] 不一致（期待どおり）

    == 判定 ==
    陽性対照（ddof=0 側）すべて一致: True   ddof=1 は不一致: True
    陰性対照 すべて不一致: True

**対照は両方向で取れている**（注意 3）。陽性が通り、陰性が四通りとも落ちる。
`ddof=1` が落ちることは、検算器が系統の違いに感応していることの追加の証拠でもある。

### 5.4 分母 0.8986 の実体

SPEC §4 は「lecun 上に対応する run か記録があるなら実測で確かめる」と定める。**在った。**

    s4_phase_baseline_001_frozen_tecno_phase_baseline_seed42   acc=0.9023102310231023
    s4_phase_baseline_002_frozen_tecno_phase_baseline_seed456  acc=0.8957095709570957
    s4_phase_baseline_003_frozen_tecno_phase_baseline_seed123  acc=0.8976897689768977

    3-seed 平均 = 0.8985698569856986  -> 4 桁表示 0.8986
    pstd (ddof=0) = 0.002766   sstd (ddof=1) = 0.003387

**分母 0.8986 は索引にある 3 run の 3-seed 平均として再現する。**

ただし**一意ではない。** 陰性対照として同じ description の 55 行から作れる 3 件組
26,235 通りを全数で調べた。

    frozen_tecno_phase_baseline 55 行から作れる 3 件組 26235 通りのうち 0.8986 になる組: 277

🔴 **4 桁表示での一致は 277/26235 = 1.06% で起きる。数値の一致だけでは特定できない。**
001/002/003 を採る根拠は、連番の最初の 3-seed 組（seed42/456/123）であり
基準点として自然だという点にあり、**数値の一致はそれを排除しないという以上の意味を持たない。**

seed を一つ除く陰性対照も取った（4 桁表示で 0.8986 から外れる）:

      001 除外 -> 0.8967    002 除外 -> 0.9000    003 除外 -> 0.8990

### 5.5 記録値そのものの所在（リポジトリ全域の走査）

記録の三値がリポジトリ内の他所に残っていないかを、語境界つきの正規表現で調べた。
単独の数値では部分一致が大量に出る（`0.8986` で 1188 ファイル）ため、
**対で同時に現れるファイル**に絞った。

    $ grep -rIElZ --exclude-dir=.git '(^|[^0-9])0\.9476([^0-9]|$)' . \
        | xargs -0 -r grep -IEl '(^|[^0-9])0\.8785([^0-9]|$)'
    ./experiments/baselines/s0_004_varifocanet_bbox_seed42/20260526_001620/20260526_001620.log
    ./tasks/T-2026-08-29-k1-verify-policy-place/SPEC.md
    ./reports/hts_audit/csv/c07_which_tool_recovery.csv

    $ grep -rIElZ --exclude-dir=.git '(^|[^0-9])0\.8010([^0-9]|$)' . \
        | xargs -0 -r grep -IEl '(^|[^0-9])0\.1788([^0-9]|$)'
    ./experiments/baselines/s0_010_ddq_bbox_seed42/20260528_081312/20260528_081312.log
    ./experiments/baselines/s0_003_maskdino_bbox_seed456/20260525_213034/20260525_213034.log
    ./experiments/baselines/s0_001_maskdino_bbox_seed42/20260525_155843/20260525_155843.log
    ./experiments/baselines/s0_009_codetr_bbox_seed456/20260527_034107/20260527_034107.log
    ./tasks/T-2026-08-29-k1-verify-policy-place/SPEC.md

    $ grep -rIElZ --exclude-dir=.git '(^|[^0-9])0\.0561([^0-9]|$)' . \
        | xargs -0 -r grep -IElZ '(^|[^0-9])0\.0726([^0-9]|$)' \
        | xargs -0 -r grep -IEl '(^|[^0-9])0\.0785([^0-9]|$)'
    ./data/external/weights/sensex_codino_seed42/20260529_114906.log
    ./data/external/weights/sensex_codino_seed42/20260531_044608.log
    ./data/external/weights/sensex_codino_seed42/20260528_225228.log
    ./experiments/baselines/s0_010_ddq_bbox_seed42/20260528_081312/20260528_081312.log
    ./experiments/baselines/s0_003_maskdino_bbox_seed456/20260525_213034/20260525_213034.log
    ./experiments/baselines/s0_012_ddq_bbox_seed456/20260528_160312/20260528_160312.log
    ./experiments/baselines/s0_009_codetr_bbox_seed456/20260527_034107/20260527_034107.log
    ./experiments/baselines/s0_008_codetr_bbox_seed123/20260526_160703/20260526_160703.log
    ./experiments/baselines/s0_007_codetr_bbox_seed42/20260526_043302/20260526_043302.log
    ./experiments/baselines/_wrong_split_8_2_3/s0_003_maskdino_bbox_seed456/20260522_224421/20260522_224421.log
    ./experiments/baselines/_wrong_split_8_2_3/s0_001_maskdino_bbox_seed42/20260522_162725/20260522_162725.log
    ./experiments/baselines/_wrong_split_8_2_3/s0_002_maskdino_bbox_seed123/20260522_162804/20260522_162804.log
    ./experiments/baselines/s0_011_ddq_bbox_seed123/20260528_120816/20260528_120816.log
    ./tasks/T-2026-08-29-k1-verify-policy-place/SPEC.md

**SPEC.md 以外はすべて偶然の一致である。** 中身を目視した（注意 2 の「一致したときは
何に一致したのかを見る」）:

    s0_004_..._log:2269  ... loss: 0.9476  loss_cls: 0.5856 ...
    s0_004_..._log:1336  ... loss: 1.4258  loss_cls: 0.8785 ...
    c07_which_tool_recovery.csv:1714  train,06_1_0751,Left Hand Tool,Tweezers,0.9476,0.873,1080,1920
    s0_010_..._log:3330  ... d0.dn_loss_cls: 0.0561  d0.dn_loss_bbox: 0.2958 ...
    s0_010_..._log:2972  ... d0.dn_loss_cls: 0.0726  d0.dn_loss_bbox: 0.3214 ...
    s0_010_..._log:2872  ... d0.dn_loss_cls: 0.0785  d0.dn_loss_bbox: 0.3378 ...

学習 loss（`d0.dn_loss_cls` 等）と bbox の座標・確信度の列であり、K1 の集計値ではない。
paired 三値が同じログに揃うのは、`dn_loss_cls` が epoch を追って単調に下がる過程で
三つの値を順に通過するためであり、seed 別の差ではない。

**リポジトリ内に K1 の三値を保持する run 由来の記録は無い**（前契約の結論と一致）。

---

## 6. 特徴の由来（判定 b）

### 6.1 直接の連結は取れない

SPEC §4 は「config が指す特徴ファイルが作り直し版（07-06 以降の生成物）であること」を
求める。**六 run に `config.yaml` は無い**（§3.2）。**したがって config を起点にした
連結は測れない。この部分は UNKNOWN である。**

### 6.2 経路と日付による間接の裏付け

生成器 `scripts/run_when_gpu_free.sh` の Phase 3 は環境変数で凍結源を渡す。

    RELDETR_FROZEN_TAG=aligndetr_s0frozen_seed42 CUDA_VISIBLE_DEVICES=0 "$vpy" scripts/train_t1a.py \
      --seed "$seed" --epochs 50 --description t1a_frozen_src_aligndetr

受け側 `scripts/train_t1a.py:57-61` はこれをそのまま経路に使う。

    FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
    GAP_DIR    = PROJ / "data" / "processed" / "stage1_features" / FROZEN_SRC
    REGION_DIR = PROJ / "data" / "processed" / "t1a_regiontoken" / REGION_SRC

現物の日付:

    2026-07-10 17:39  148,679,688  data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42/train_regiontoken.npz
    2026-07-10 17:41   23,325,456  data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42/val_regiontoken.npz
    2026-07-10 17:47   65,664,456  data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42/test_regiontoken.npz

    2026-07-06 03:26   23,325,456  .../aligndetr_s0frozen_seed42.discarded_20260706/val_regiontoken.npz
    2026-07-06 03:32  148,679,688  .../aligndetr_s0frozen_seed42.discarded_20260706/train_regiontoken.npz

**採用されている `aligndetr_s0frozen_seed42` は 07-10 版で、07-06 版は破棄されている。**
いずれも 07-06 の作り直し（v2）以降の生成物であり、07-03 の失敗版ではない。

### 6.3 検出性能 68.60 の一次証拠（版管理された記録）

`evidence/aligndetr_s0frozen_incident_20260703/aligndetr_s0frozen_v2_train_log.txt:1670`:

    [07/06 03:25:53] d2.evaluation.testing INFO: copypaste: 68.5960,81.1582,73.8712,0.4680,23.9375,69.5419

同 `README.md:21`:

    | 07-06 03:24 | S0-frozen を再学習（v2）**成功**。bbox AP 68.596 | `aligndetr_s0frozen_v2_train_log.txt` |

**SPEC §0 の「作り直し版の検出性能 68.60」は bbox AP 68.5960 として版管理された
一次ログに実在する。** これは K1 の三値のうち `0.686` に対応する。

### 6.4 残る不定

`evidence/discarded_caches/t1a_regiontoken/aligndetr_s0frozen_seed42.discarded_20260706.md`
（版管理された追跡コピー）は、07-10 の再抽出について次を記録している。

> **v3 の ckpt は存在しない。** `/tmp` に残る S0-frozen 学習成果は v2（07-06 03:24）のみ。
> 07-10 の再抽出はログを残していないため、実際に渡された引数を確認できない。

したがって「07-10 版の特徴が v2 ckpt から出た」ことは**消去法による推定であり、
直接の記録は無い。** 同文書は 07-06 版と 07-10 版で npz の md5 が異なることも記録しており、
その理由は未解明のままである。

---

## 7. 変更範囲と検査

### 7.1 変更の全量

    $ git --no-pager diff --name-only origin/phase0...HEAD ; git status --porcelain
     M context/auto/followups.md          （生成物。make taskindex）
     M context/auto/results_recent.md     （生成物。make taskindex）
     M context/auto/tasks_summary.csv     （生成物。make taskindex）
     M docs/stage0/A7_k1_provenance.md    （追記 +146 行）
     M docs/stage0/stage0_summary.md      （追記 +27 行）
     M tasks/inbox.md                     （生成物。make inbox）
    ?? tasks/T-2026-08-29-k1-verify-policy-place/
    ?? tasks/inbox.d/T-2026-08-29-k1-verify-policy-place.md

    $ git --no-pager diff --stat
     docs/stage0/A7_k1_provenance.md | 146 ++++++++++++++++++
     docs/stage0/stage0_summary.md   |  27 ++++++
     2 files changed, 173 insertions(+)

**173 insertions / 0 deletions。** 既存本文の書き換えは一行も無い（SPEC §6 禁止 5 を満たす）。

    $ git status --porcelain | grep -E 'experiments/|data/|runindex/' | wc -l
    0

### 7.2 検査の結果（終了コードを個別に測った）

zsh は配列添字で終了コードを取れない（`issuer_cautions` のシェル前提）。
`${PIPESTATUS[0]}` は空を返すため、各命令を単独で走らせて `$?` を取った。

    make taskindex-check  -> exit=0
    make inbox-check      -> exit=0
    make docs-check       -> exit=0
    make agent-check      -> exit=0
    make forbidden-check  -> exit=0

### 7.3 検査が今回の変更を走査していること（対象件数）

    $ python tools/check_forbidden.py
    {"base": "origin/phase0", "changed": 12, "checked": 8, "excluded": 4,
     "excluded_paths": ["context/auto/followups.md", "context/auto/results_recent.md",
                        "context/auto/tasks_summary.csv", "tasks/inbox.md"],
     "status": "pass", "violations": []}

**変更 12 件のうち生成物 4 件を除いた 8 件を実際に走査している。**
その 8 件に `docs/stage0/A7_k1_provenance.md` と `docs/stage0/stage0_summary.md` が含まれる
（12 = 変更 6 + 契約ディレクトリの 5 ファイル + 受け皿 1）。

    $ make docs-check
    [docs-check] 対象 42 文書 / Makefile のターゲット 33 件
    [docs-check] 食い違いなし

    $ make agent-check
    {"errors": [], "pager_violations": [], "status": "pass", "targets": 109, "violations": []}

### 7.4 検査が空振りでないことの確認（陽性対照）

**`forbidden-check` を、禁止領域に実際に変更のある起点へ当てた。**

    $ C=$(git --no-pager log --format=%H -1 origin/phase0 -- experiments/)
    $ make forbidden-check BASE=$C~1
    exit=2
    {"base": "36f71ff5...~1", "changed": 71, "checked": 63, "excluded": 8,
     "status": "fail", "violations": [
       {"path": "experiments/analysis/official_split_reassessment/REPORT.md",   "reason": "禁止領域 experiments/ の内側"},
       {"path": "experiments/analysis/official_split_reassessment/controls.py", "reason": "禁止領域 experiments/ の内側"},
       {"path": "experiments/analysis/official_split_reassessment/controls.txt","reason": "禁止領域 experiments/ の内側"},
       {"path": "experiments/analysis/official_split_reassessment/inventory.py","reason": "禁止領域 experiments/ の内側"},
       {"path": "experiments/analysis/official_split_reassessment/inventory.txt","reason": "禁止領域 experiments/ の内側"},
       {"path": "experiments/analysis/official_split_reassessment/juxtapose.py","reason": "禁止領域 experiments/ の内側"},
       {"path": "experiments/analysis/official_split_reassessment/juxtapose.txt","reason": "禁止領域 experiments/ の内側"}]}

**違反 7 件を出して落ちた。上の 0 件は「検出できていない」ではない。**

### 7.5 索引への書き込みが零件であること（判定 e）

    $ git status --porcelain | grep -E '^.. runindex/' | wc -l
    0

同じ絞り込みを、実際に変更のある `docs/` へ当てると 2 件出る。

    $ git status --porcelain | grep -E '^.. docs/' | wc -l
    2

**絞り込みは働いている。**

### 7.6 同期の抑止

`task_start.sh` が `.sync-pause` を置いた。稼働中の常駐処理が対応済みであることを確かめた。

    $ grep -c sync-pause ~/bin/m2-sync.sh
    2

（0 なら未対応。2 のため抑止は効く。）**報告まで終えたら解除する。**
