# 証跡の記録 — T-2026-08-26-oracle-ceiling-and-tool-drop

事実の記録は `RESULT.md`。本書は命令とその出力、参照の解決、対照の出力、変更範囲、台帳の応答を置く。
散文は書かない。**同じ内容を RESULT.md と二度書かない。**

ホスト `lecun` / 分岐 `feat/oracle-ceiling-and-tool-drop` / シェル `/usr/bin/zsh`。

---

## E1. 時刻と締切

    $ date -u '+%Y-%m-%dT%H:%M:%SZ'; TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S JST'; date +%s
    2026-08-25T21:15:07Z
    2026-08-26 06:15:07 JST
    1787692507

起点 T0 = 1787692507（2026-08-26 06:15:07 JST）。実行期限 = T0 + 16h = 2026-08-26 22:15:07 JST。

| Phase | 入口の経過 | 入口の時刻 (JST) |
|---|---:|---|
| A | 623 秒 (10.4 分) | 06:25:30 |
| B | 981 秒 (16.4 分) | 06:31:28 |
| C | 1006 秒 (16.8 分) | 06:31:53 |
| D | — | 入らず |
| E | 1679 秒 (28.0 分) | 06:43:06 |

## E2. 検証（L1+L2）

    $ make task-validate TASK=T-2026-08-26-oracle-ceiling-and-tool-drop; echo "EXIT_CODE=$?"
    EXIT_CODE=0
    WARN [L2-8] index.csv: 起票時 751 → 現在 1177（分母が動いています）
    WARN [L2-8] experiments.csv: 起票時 207 → 現在 213（分母が動いています）
    OK   T-2026-08-26-oracle-ceiling-and-tool-drop
    1 task(s), 0 failed

WARN の出所は `tools/validate_task.py:469`。`meta.created_from.counts` と現在の行数の照合である。
既知の教訓 `BL-harvester-scan-is-host-dependent`（`tools/harvest_runindex.py:3014`）に
「収穫器はディスクを走査するため、同じ commit でもホストによって索引の行数が変わる」と実測付きで記録がある。
WARN を提示して続行の承認を得た（`tasks/inbox.d/` に 1 行）。

**シェルの実測**: 初回は `${PIPESTATUS[0]}` で終了コードを取ろうとして空文字になった。
対話シェルは zsh であり配列添字で終了コードを取れない（`conventions#issuer_cautions`）。
以後すべて `; echo "EXIT_CODE=$?"` の形に統一した。

## E3. 参照の解決

### E3.1 `inputs.denominator.ref`

`exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` を
`runindex/experiments.csv` から実測で解決した。

    experiment_id  = phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42
    n_runs         = 17          n_seeds = 3      seeds = 42,123,456
    hosts          = efros,lecun eval_recipe_id = e98ffddee042
    split          = val
    accuracy_mean  = 0.8973014948553679
    accuracy_pstd  = 0.005917073407586465
    accuracy_sstd  = 0.006099179663503103
    accuracy_n     = 17
    macro_f1_mean  = 0.6940236889008451
    elapsed_seconds_mean = （空）   elapsed_seconds_n = （空）

`require` の充足: `n_seeds >= 3` → 3 で充足。`sigma: present` → pstd/sstd ともに実数で充足。
`split: val` → val で充足。**参照先そのものは移動していない**ため `escalate_if: denominator_moved` には当たらない。
`elapsed_seconds` が空であることは、申し送り 5 の「基準点の run に所要時間が残っていない」と整合する。

**本契約はこの分母を絶対値の比較に使っていない。** 申し送り 6 のとおり、上限の比較は
同じ入口・同じ split の予測側の腕（E5.2）に対して取った。

### E3.2 `inputs.sigma_policy`（省略 → `conventions#sigma` の既定を継承）

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

規約は「この既定は暫定である。正本（ddof=0 / ddof=1）は未決定」と明記している。
本契約は判定を行わないため、σ は**記録のみ**に用いた。

### E3.3 `inputs.frozen_source.ref` — `verify: ckpt_sha256`

    P5 frozen_source_hash PASS third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
       sha256=03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824

`conventions#frozen_source` の正本値と一致。`escalate_if: frozen_source_hash_mismatch` には当たらない。

### E3.4 `contract.inject_verbatim` — 解決先の原文

注入対象は `conventions#split` `#eval_recipe` `#frozen_source` `#sigma` `#prohibitions` `#issuer_cautions` の 6 節。
`contract.conventions_rev` は起票時 `PENDING_EXECUTOR_MEASUREMENT` だったため実測で差し替えた（E4）。
差し替え後の rev で `git diff <rev>..HEAD -- context/conventions.md` は空であり、L2-6 の WARN は出ていない。

`conventions#split` の原文（転記ではなく照合に用いた）:

- train: `01`, `02`, `03`, `06`, `08`, `11`, `12`, `13`, `14`, `15`
- val: `09`, `10`
- test: `04`, `05`, `07`

実測との照合（E5.1 の Step 4）で完全一致した。

`conventions#prohibitions` の 5 件と `conventions#issuer_cautions` の 13 件は本文のまま適用した。
注意 5「終了コードを件数と呼ばない」に従い、件数はすべて `grep -c` か `wc -l` で数えている。
注意 6「プロセスは `/proc/PID/exe` で絞る」に従い、GPU 競合の確認は `readlink -f /proc/PID/exe` で行った（E5.5）。

## E4. 起票者が埋められなかった二つの欄（Phase A Step 5）

    $ git --no-pager log -1 --format='%H %ci %s' -- context/conventions.md
    a8c07e813696d3720ceee648e8aa202224285955 2026-08-25 15:30:37 +0000 feat(context): move issuer references into version control and inject the cautions
    $ git --no-pager log -1 --format='%H %ci %s' -- runindex/
    7918b5dd9aab3d15b3c459f87aebdd9eb1653116 2026-08-16 00:12:23 +0000 exp(s4): 60-seed deterministic sweep -- the upper bound is not detectable

差し替え結果:

| 欄 | 起票時 | 実測値 |
|---|---|---|
| `meta.created_from.runindex_commit` | `PENDING_EXECUTOR_MEASUREMENT` | `7918b5dd9aab3d15b3c459f87aebdd9eb1653116` |
| `contract.conventions_rev` | `PENDING_EXECUTOR_MEASUREMENT` | `a8c07e813696d3720ceee648e8aa202224285955` |

`meta.amendments` に 2 件として記録した。

## E5. Phase A — 入力の実在確認（一つずつ）

### E5.1 データの実在

    $ ls -la data/processed/stage1_features/relation_detr_seed42/
    test_gap.npz 35092940 / train_gap.npz 79458316 / val_gap.npz 12465940
    $ ls -la data/processed/b2a_detsignal/relation_detr_seed42/
    test_toolpresence.npz 409956 / train_toolpresence.npz 927588 / val_toolpresence.npz 145956
    $ ls -la data/processed/oracle_toolpresence/
    test_oracletool.npz 409956 / train_oracletool.npz 927588 / val_oracletool.npz 145956
    $ ls -la data/processed/phase_manifest/
    phase_vocab.json 164 / test.json 465823 / train.json 1068981 / val.json 164386
    $ cat data/splits/ego_train.txt data/splits/ego_val.txt data/splits/ego_test.txt
    train: 01 02 03 06 08 11 12 13 14 15   val: 09 10   test: 04 05 07

分割は `conventions#split`（E3.4）と**完全一致**。
`phase_vocab.json` は 9 工程（anesthesia/closure/design/disinfection/dissection/dressing/hemostasis/incision/irrigation）。
clip 数: train 13 / val 3 / test 6。frame 数: train 9657 / val 1515 / test 4265。

参考: `data/splits/surgeon_folds.json` と `exo_sync_map.json` はいずれも中身が `{}` である。
本契約は標準 split（fold は 1 つ）を使うため影響しない。

### E5.2 入口の実在

    $ ls -la scripts/train_b2a.py
    -rw-rw-r-- 1 ubuntu ubuntu 19568 Aug 22 03:31 scripts/train_b2a.py

`inputs.code.entrypoints` の記載どおりであり、申し送り 1 が警戒した名の変更は起きていなかった。
実装を読んで判明した本契約に関わる引数:

- `--tool-source {pred,oracle}` — 術具存在の出所。`oracle` は GT bbox 由来の one-hot 15-d。
- `--mask-tool-dims '0,6,9'` — 指定 dim を 0 埋めして落とす（術具除去の**適用側**）。
- 評価専用の経路は**無い**（E7 の起票者の誤り 2）。

### E5.3 落とす集合を求める仕組みの探索（異質な 3 方法・先頭ドット含む）

    $ grep -rniI "entropy" src/ scripts/               → 集合計算に該当するもの 0 件
    $ find . -name "*entropy*" -not -path "./.git/*"    → 31 件（うち .venv 外は 3 件）
    $ git ls-files | grep -i entropy                    → 3 件

3 方法が一致して指したのは次の 3 件のみである。

    docs/analysis_scripts/proxy_lovo_prune_by_entropy.py
    docs/task_drafts/E9_prune_high_entropy_tools.spec.yaml
    src/egosurgery/models/feedback/entropy_gate.py

`entropy_gate.py` は H-C-v1 の per-frame entropy gate であり、術具の集合計算とは別物。
`E9_*.spec.yaml` は起票の下書きであって実装ではない。
集合計算 `H(phase | tool present)/log2(9)` の実体は
`docs/analysis_scripts/proxy_lovo_prune_by_entropy.py:22` の `entropy_rank`、
`docs/analysis_scripts/proxy_threshold_sweep.py` の `entropies`、
`docs/analysis_scripts/proxy_lovo_recommended.py` の `high_entropy_tools` の 3 本で、
いずれも `docs/analysis_scripts/` 配下＝**代理側**にある。`src/` と `scripts/` には無い。

補足（判断材料として実測）: これらが読む入力は本番のキャッシュそのものである。
`proxy_phase_presence_denoise.py` の `load_sig` は `data/processed/oracle_toolpresence/` と
`data/processed/b2a_detsignal/relation_detr_seed42/` を、`clips` は `data/processed/phase_manifest/` を読む。
代理なのは下流の分類器（LogisticRegression + phase HMM）だけである。
この事実を添えて起票者へ提示し、**「契約どおり止める」との回答を得た**（`tasks/inbox.d/`）。

### E5.4 凍結源

E3.3 のとおり sha256 が規約の正本値と一致。

### E5.5 計算資源

    $ nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu --format=csv
    0, NVIDIA RTX A6000, 49140 MiB, 35 MiB, 0 %
    1, NVIDIA RTX A6000, 49140 MiB, 20 MiB, 0 %
    $ nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c .
    0

GPU プロセス 0 件。他の利用者との競合なし。以降 `CUDA_VISIBLE_DEVICES=0` に固定した（契約の `gpu: 1`）。

    $ hostname
    lecun

## E6. プリフライト（L3）

初回:

    $ source .venv/bin/activate && make task-preflight TASK=...; echo "EXIT_CODE=$?"
    EXIT_CODE=2
    P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=... sys.prefix=...
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP UNKNOWN 判定基準が未確定。決定性設定は実行プロセス内で行われ外部から観測できない。backlog B-20 が未解決
    P4 prereg_committed       FAIL prereg.commit が未記入
    P5 frozen_source_hash     PASS sha256=03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824
    P6 decisions_answered     FAIL 未回答 4 件: 落とす術具の判断に用いる閾値を変更すること; 分母を別の実験へ移すこと; 決定化を無効にすること; 本契約の範囲を越えて別の腕を追加すること
    P7 destination_writable   PASS experiments/transfer/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    RESULT: 5 PASS / 0 WARN / 2 SKIP / 2 FAIL

**SKIP は合格ではない。** P2 と P3 は実行されていない。
とくに P3 は「決定化が効いているか」を検査器では確かめられないことを意味する。
契約はそれを Phase C の対照で測れと定めており、E8 で実測した。

P6 の 4 件を起票者へ提示し、**4 件とも「行わない」との回答**を得た。
`governance.decisions_required` を空にし、回答は `tasks/inbox.d/` と `meta.amendments` に残した。

P4 のため契約 3 ファイルと `tasks/inbox.d/` を commit した（承認済み）。

    $ git --no-pager log -1 --format='%H %ci %s'
    1f4dd9c7e886aad2db9c4650b31a32d364f1f95a 2026-08-25 21:25:02 +0000 docs(task): register the prereg for the oracle ceiling and tool drop

`prereg.commit` / `prereg.committed_at` へ記入後:

    EXIT_CODE=0
    P4 prereg_committed       PASS 1f4dd9c7e886aad2db9c4650b31a32d364f1f95a committed_at=2026-08-25T21:25:02+00:00
    P6 decisions_answered     PASS decisions_required は空
    RESULT: 7 PASS / 0 WARN / 2 SKIP / 0 FAIL

## E7. 決定化と刻印の配線（`scripts/train_b2a.py`）

契約は決定化を有効にすることを求めるが、入口に切り替えが無かった。
本番側の `src/egosurgery/utils/determinism.py` の `enable_determinism()` は既に存在し、
`scripts/train_grasp_phase_injection_variants.py --deterministic` にのみ配線されていた。
同じ作法で `train_b2a.py` へ配線した（既定は現状のまま。過去 run との比較可能性を壊さない）。

    $ git --no-pager diff --stat scripts/train_b2a.py
     scripts/train_b2a.py | 28 +++++++++++++++++++++++++---
     1 file changed, 25 insertions(+), 3 deletions(-)

変更は 4 点。(1) `enable_determinism` の import。(2) `train()` 冒頭で
`--deterministic` のとき `enable_determinism(args.seed)` を呼ぶ（最初の CUDA 演算より前）。
(3) `config.yaml` へ `determinism` / `task_id` / `oracle_upper_bound_only_do_not_report` を書き出す。
(4) `--deterministic` と `--task-id` の追加。**学習の数式には触れていない。**

上限測定専用の印は既存の作法に合わせた
（`scripts/train_grasp_phase_injection_variants.py:286` の `oracle_upper_bound_only_do_not_report`）。

lint は変更前後で同一である。`I001` は変更前から出ている既存の指摘（末尾の `import os` に由来）。

    $ ruff check scripts/train_b2a.py                       → I001 1 件 (EXIT 1)
    $ git stash -q && ruff check scripts/train_b2a.py       → I001 1 件 (EXIT 1)   ← 変更前も同じ

疎通（決定化あり・証跡なし・3 epoch）で `torch.use_deterministic_algorithms(True)` が
例外を投げないことを確かめた。投げれば「決定的実装の無い演算がある」として止める設計である。

    $ python scripts/train_b2a.py --smoke --deterministic --tool-source oracle
    [b2a] train clips=3  val clips=2  in_dim=2063  tool_source=oracle  classes=9  device=cuda
    [b2a] best @epoch 1: acc=0.3510 macroF1=0.0993        （3.78 秒・例外なし）

## E8. Phase B / C の命令と出力

### E8.1 上限の評価（Phase B・証跡あり）

    $ export CUDA_VISIBLE_DEVICES=0
    $ python scripts/train_b2a.py --tool-source oracle --seed 42 --epochs 50 --deterministic \
        --task-id T-2026-08-26-oracle-ceiling-and-tool-drop
    RUN=B_oracle_seed42 START_EPOCH=1787693488 START_JST=2026-08-26 06:31:28
    RC=0 END_EPOCH=1787693513 ELAPSED_SEC=25
    [b2a] best @epoch 48: acc=0.9558 macroF1=0.8237
    [b2a] evidence written -> experiments/transfer/b2a_det2phase_oracletool_009_b2a_det2phase_oracletool_seed42

証跡（`ls` で 11 件: checkpoints / command.sh / config.yaml / git_commit.txt / logs /
metrics.json / notes.md / per_class_ap.json / predictions / server.txt / visualizations）。

`config.yaml` の該当行:

    48: task_id: T-2026-08-26-oracle-ceiling-and-tool-drop
    49: oracle_upper_bound_only_do_not_report: true
    determinism:
      deterministic: true
      seed: 42
      cublas_workspace_config: :4096:8
      torch_use_deterministic_algorithms: true
      cudnn_deterministic: true
      cudnn_benchmark: false

`metrics.json`（**分類と分節の双方**）:

    phase_accuracy   = 0.9557755775577558
    phase_macro_f1   = 0.8236749678606377
    phase_edit_score = 52.63492063492063
    phase_jaccard    = 0.7946755567390006
    phase_seg_f1_10  = 0.5944066515495088
    phase_seg_f1_25  = 0.5944066515495088
    phase_seg_f1_50  = 0.5437641723356009
    epoch            = 48

### E8.2 比較の相手（予測側・既存記録からの引用と出所）

`runindex/experiments.csv` の
`transfer/b2a_det2phase_toolpresence/b2a_det2phase_toolpresence@val~relation_detr_seed42`。

    n_runs = 9   n_seeds = 5   seeds = 42,123,456,789,1000   eval_recipe_id = 4ac382e09c21
    hosts  = efros,lecun       task_ids = （空）              n_runs_excluded = 0
    accuracy   mean=0.9369270260359369 pstd=0.0018698274710644725 sstd=0.001983251526657872 n=9
    macro_f1   mean=0.7905424423176497 pstd=0.004257277125884496  sstd=0.004515524287654953 n=9
    edit_score mean=43.31280835965053  pstd=5.612936361613077     n=9
    jaccard    mean=0.7446490489005801 pstd=0.005595483729892315  n=9
    seg_f1_10  mean=0.5035920800735615 pstd=0.056534846532847606  n=9
    seg_f1_25  mean=0.489440355597763  pstd=0.05926953172789311   n=9
    seg_f1_50  mean=0.4613526168618761 pstd=0.06562031451883309   n=9

**出所の明記**: `runindex/index.csv` で run ごとに数えると **efros 7 件 / lecun 2 件**である。
すなわち予測側の 9 件のうち **7 件は当該ホスト（lecun）で測られたものではない。**
どの run にも `task_id` は付いていない（9 件すべて空）。

同じ入口の既存オラクル腕
`transfer/b2a_det2phase_oracletool/b2a_det2phase_oracletool@val~relation_detr_seed42`:

    n_runs = 8   n_seeds = 5   hosts = lecun 5 件 / efros 3 件   eval_recipe_id = 4ac382e09c21
    accuracy mean=0.9575907590759076 pstd=0.003126616389685883 n=8
    macro_f1 mean=0.8244215227243904 pstd=0.003360921329971693 n=8

### E8.3 効果量（判定は行っていない）

(a) 本契約の新規 oracle run − 予測側の既存記録の平均:

    accuracy    oracle=0.955776  pred_mean=0.936927  pred_pstd=0.001870  Δ=+0.018849
    macro_f1    oracle=0.823675  pred_mean=0.790542  pred_pstd=0.004257  Δ=+0.033133
    edit_score  oracle=52.634921 pred_mean=43.312808 pred_pstd=5.612936  Δ=+9.322112
    jaccard     oracle=0.794676  pred_mean=0.744649  pred_pstd=0.005595  Δ=+0.050027
    seg_f1_10   oracle=0.594407  pred_mean=0.503592  pred_pstd=0.056535  Δ=+0.090815
    seg_f1_25   oracle=0.594407  pred_mean=0.489440  pred_pstd=0.059270  Δ=+0.104966
    seg_f1_50   oracle=0.543764  pred_mean=0.461353  pred_pstd=0.065620  Δ=+0.082412

(b) 既存記録を**種ごとに対にした**もの（`runindex/index.csv` の per-run 値の種内平均）:

    seed | pred n  pred acc  pred mF1 | orc n   orc acc   orc mF1 |     Δacc     ΔmF1
      42 |      3  0.937074  0.790706 |     2  0.953795  0.819540 | +0.01672 +0.02883
     123 |      2  0.934983  0.785525 |     2  0.959736  0.825681 | +0.02475 +0.04016
     456 |      2  0.938614  0.792300 |     2  0.956106  0.824575 | +0.01749 +0.03227
     789 |      1  0.937294  0.791366 |     1  0.961716  0.830070 | +0.02442 +0.03870
    1000 |      1  0.936634  0.795748 |     1  0.959736  0.825712 | +0.02310 +0.02996

    対になった種の数 = 5
    accuracy: 改善側へ倒れた個数 = 5/5   平均Δ = +0.02130
    macro-F1: 改善側へ倒れた個数 = 5/5   平均Δ = +0.03399

ホストの内訳（対の素性）:

    pred   seed42=[efros,efros,efros] seed123=[efros,efros] seed456=[efros,efros] seed789=[lecun] seed1000=[lecun]
    oracle seed42=[lecun,efros]       seed123=[lecun,efros] seed456=[lecun,efros] seed789=[lecun] seed1000=[lecun]

**同一ホスト（lecun）だけで対になるのは seed 789 と 1000 の 2 組**で、いずれも改善側（+0.02442 / +0.02310）。
残り 3 組はホストをまたいでいる。

### E8.4 工程ごとの内訳と、評価側に現れない工程の扱い

本契約の oracle run（seed42）の `per_class_ap.json` と val の支持数:

    phase          idx  val frames  per-class F1
    anesthesia       0          98  0.9948717948717948
    closure          1         557  0.9587357330992098
    design           2         103  1.0
    disinfection     3           0  0.0
    dissection       4         506  0.9656526005888126
    dressing         5          24  0.0
    hemostasis       6          57  0.8888888888888888
    incision         7         170  0.9575757575757576
    irrigation       8           0  0.0

**評価側に 1 frame も現れない工程は `disinfection` と `irrigation` の 2 件。**
この 2 件の F1=0.0 は成績ではなく支持が無いことの表れである。

macro-F1 の定義を実装で確認した（`src/egosurgery/metrics/phase.py:258-262`）。

    # クラス存在のあるものだけで macro F1 を取る（全 GT 不在のクラスは除外）。
    present = np.array([(gts == c).any() for c in range(self.num_classes)])
    macro = per_class[present].mean()

算術で裏を取った:

    全 9 クラス平均       = 0.6406360861138293
    支持のある 7 クラス平均 = 0.8236749678606377
    metrics.json の macro_f1 = 0.8236749678606377   ← 7 クラス平均と一致

したがって **macro-F1 は支持のある 7 工程の平均**であり、支持ゼロの 2 件は除外されている。
一方 **`dressing` は val に 24 frame の支持がありながら F1=0.0** で、除外されずに macro-F1 に入っている。
すなわち macro-F1 の分母は 7 であり、そのうち 1 件は一度も当たっていない。

### E8.5 決定化の対照（Phase C・証跡なし）

    $ for tag_seed in "C1a 42" "C1b 42" "C2 123"; do
        python scripts/train_b2a.py --tool-source oracle --seed $seed --epochs 50 --deterministic --no-evidence
      done
    C1a seed=42  RC=0 ELAPSED_SEC=26
    C1b seed=42  RC=0 ELAPSED_SEC=27
    C2  seed=123 RC=0 ELAPSED_SEC=34

**陰性対照（同じ種なら一致するはず）**: 50 epoch 分の全出力を照合。

    $ diff C1a.log C1b.log; echo "diff_exit=$?"
    diff_exit=0
    差分行数: 0
    C1a  [b2a] best @epoch 48: acc=0.9558 macroF1=0.8237
    C1b  [b2a] best @epoch 48: acc=0.9558 macroF1=0.8237

**陽性対照（種を変えれば変わるはず）**:

    $ diff C1a.log C2.log; echo "diff_exit=$?"
    diff_exit=1
    差分行数: 102
    C2   [b2a] best @epoch 45: acc=0.9584 macroF1=0.8264

**証跡の有無で結果が変わらないことの確認**（`ExperimentManager` が RNG に触れていないか）:

    $ diff <(grep '^\[b2a\]\[epoch' B_oracle_seed42.log) <(grep '^\[b2a\]\[epoch' C1a.log); echo "diff_exit=$?"
    diff_exit=0

**陰性対照が空振りでないことの確認**（決定化を外すと同じ種でも揺れるはず）:

    $ python scripts/train_b2a.py --tool-source oracle --seed 42 --epochs 50 --no-evidence   （×2）
    N1 (決定化なし) RC=0 ELAPSED_SEC=19
    N2 (決定化なし) RC=0 ELAPSED_SEC=11
    $ diff N1.log N2.log; echo "diff_exit=$?"
    diff_exit=1
    差分行数: 96
    N1  [b2a] best @epoch 40: acc=0.9564 macroF1=0.8185
    N2  [b2a] best @epoch 40: acc=0.9545 macroF1=0.8176

決定化なしでは同じ種でも 96 行が食い違い、best acc が 0.9564 と 0.9545 に分かれた。
決定化ありでは 0 行である。**したがって陰性対照は「常に一致を返す壊れ方」ではない。**

### E8.6 所要時間の実測と本数の計算（Phase C Step 3）

    決定化あり n=4: [25, 26, 27, 34] 秒  mean=28.0  min=25 max=34
    決定化なし n=2: [19, 11] 秒          mean=15.0  min=11 max=19
    平均の比（あり / なし）= 1.87 倍
    範囲で見た比: 下限 25/19 = 1.32 倍 / 上限 34/11 = 3.09 倍   ← n が小さくばらつきが大きい

計算の過程:

    残り時間 = 実行期限 − 現在 = 56307 秒（938.5 分 = 15.64 時間）
    1 本の所要（安全側に最大値を採用） = 34 秒
    対 1 組 = 2 本 = 68 秒
    入る対の組数 = floor(56307 / 68) = 828 組
    参考: 3 種（42/123/456）の対 3 組に必要なのは 204 秒 = 3.4 分

**時間は制約にならなかった。** Phase D へ入らなかった理由は時間ではない（E5.3）。

## E9. 変更範囲と禁止領域

    $ source .venv/bin/activate && make forbidden-check; echo "EXIT_CODE=$?"
    EXIT_CODE=2
    {"base": "origin/phase0", "changed": 12, "checked": 12, "errors": [], "excluded": 0,
     "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"],
     "status": "fail", "violations": [ ... 7 件 ... ]}

**内訳を一件ずつ示す。** 変更 12 件のうち違反は 7 件で、**7 件すべてが本契約が作った run の内側**である。

| # | 経路 | 違反か | 由来 |
|---|---|---|---|
| 1 | `tasks/T-2026-08-26-oracle-ceiling-and-tool-drop/SPEC.md` | 否 | 契約（配布物） |
| 2 | `tasks/T-2026-08-26-oracle-ceiling-and-tool-drop/prereg.md` | 否 | 契約（配布物） |
| 3 | `tasks/T-2026-08-26-oracle-ceiling-and-tool-drop/spec.yaml` | 否 | 契約（E4 と P6 の反映） |
| 4 | `tasks/inbox.d/T-2026-08-26-oracle-ceiling-and-tool-drop.md` | 否 | 判断の受け皿 |
| 5 | `scripts/train_b2a.py` | 否 | 決定化と刻印の配線（E7） |
| 6 | `experiments/transfer/b2a_det2phase_oracletool_009_.../command.sh` | **是** | 本契約の run |
| 7 | 同上 `/config.yaml` | **是** | 本契約の run |
| 8 | 同上 `/git_commit.txt` | **是** | 本契約の run |
| 9 | 同上 `/metrics.json` | **是** | 本契約の run |
| 10 | 同上 `/notes.md` | **是** | 本契約の run |
| 11 | 同上 `/per_class_ap.json` | **是** | 本契約の run |
| 12 | 同上 `/server.txt` | **是** | 本契約の run |

**本契約の成果物以外による違反は 0 件。** SPEC §6 が予告したとおり、
run を作る契約はこの検査を構造的に通せない。検査は 12 件中 5 件を違反としていないため、
「何でも違反にする」壊れ方ではない。

`make runindex` は回していない（E10 の逸脱 5）。索引が本契約の run を `task_id` 付きで
拾うことは、収穫器の読取関数を直接呼んで陽性・陰性の両方向で確かめた。

    $ python -c "from harvest_runindex import harvest_config; ..."
    陽性: 本契約の run の config.yaml  → task_id = 'T-2026-08-26-oracle-ceiling-and-tool-drop'  warnings=[]
    陰性: b2a_det2phase_oracletool_001_..._seed789 → task_id = ''
    陰性: 存在しない経路 experiments/transfer/zzz_no_such_run/config.yaml → task_id = ''

## E10. 試験

    $ pytest tests/ -q          （変更後）  5 failed, 472 passed, 22 warnings in 24.45s
    $ git stash push -- scripts/train_b2a.py && pytest tests/ -q   （変更前）
                                              5 failed, 472 passed, 22 warnings in 23.25s
    $ diff <(grep '^FAILED' before) <(grep '^FAILED' after); echo "diff_exit=$?"
    diff_exit=0

**失敗集合は変更前後で完全に一致**（5 件）。すなわち本契約の変更に由来する失敗は 0 件である。

    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

## E11. 自動同期の抑止

    $ ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 25 21:14 .sync-pause     ← 開始時点で既に置かれていた
    $ grep -c sync-pause ~/bin/m2-sync.sh
    2                                                          ← 稼働中の版は対応済み

作業ツリーは開始時点で契約 3 ファイルのみが未追跡であり、**退避を要するものは無かった。**

## E12. 台帳への送出

E13 に記す。

## E13. 追跡と資格情報

`source scripts/load_env.sh` の前提となる `.env` / `.env.gpg` への接触は
権限フックに拒否された（`Permission to use Bash with command ls -la .env.gpg .env has been denied.`）。
したがって W&B と Notion の認証は読み込めず、`tracking.init/log/finish` と
`log_experiment_to_notion` は**設計どおり no-op で走った**（研究フローは止まっていない）。
`make task-report` も同じ理由で送れない。結果は RESULT.md の「送出」に記す。
