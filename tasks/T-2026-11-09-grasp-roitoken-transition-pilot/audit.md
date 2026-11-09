# audit — T-2026-11-09-grasp-roitoken-transition-pilot

ホスト bengio、分岐 `feat/grasp-roitoken-transition-pilot`（起点 origin/phase0 129e79b0）。時刻はホストの UTC を JST（+9 時間）に直して書く。
置き場: `$S = /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot`、`$A = experiments/analysis/grasp_roitoken_transition_pilot`。
本体の .venv、`PYTHONDONTWRITEBYTECODE=1`（`scripts/` に .pyc を書かない。前契約の逸脱の再発防止）。

## 0. 始める（2026-11-09 09:5x JST）

- 1 回目の `/task`（同じ識別子）: task-start が台帳の取り込みで止まった（`配布台帳に契約が見つかりません …（置き換え済みの行が 1 件あります）`）。
  task-start が巻き戻し、利用者の判断で中止。分岐・目印は残らなかった
- 2 回目の `/task`: 分類「通す」（無視・起点に在り中身が同じ 12 件）。`make task-start` → `[task-start] .sync-pause を作成`、
  `[task-start] 完了。`。目印の中身 `task_id=T-2026-11-09-grasp-roitoken-transition-pilot` / `branch=feat/grasp-roitoken-transition-pilot`。
  稼働中の `~/bin/m2-sync.sh` の `grep -c sync-pause` は 2（対応済み）
- `make task-validate`: OK（0 failed）。`make task-preflight`: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。
  SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（plan.env.preflight に記載なし）、P4 prereg_committed・P5 frozen_source_hash・
  P13 symmetry_table_complete・P14 proposal_card_checked（kind=analysis で対象外）、P12 refs_resolved（解決前提の参照なし）

## 1. 解決された参照

- `contract.inject_verbatim` の 7 節（prohibitions・issuer_cautions・env_p0・folds・split・crossfit・symmetry）は
  `context/conventions.md` の原文を適用した。`git log -1 -- context/conventions.md` = 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（契約の conventions_rev と一致）
- denominator・frozen_source・sigma_policy の参照は無い

## Task A — 開始状態（G1）

記録の原本は `$S/start/`。

### A-1 分岐・起点・PR 302・未追跡（`$S/start/a1_branch.txt`）

    $ git branch --show-current → feat/grasp-roitoken-transition-pilot
    $ git merge-base HEAD origin/phase0; git rev-parse origin/phase0 HEAD → 129e79b05845dc966e9ace30cd209af08d7fdf38（3 つとも同じ）
    $ git log --oneline -1 --grep "Merge pull request #302" origin/phase0 → 5f61c389 Merge pull request #302 from takuya3h/feat/grasp-cards-survey
    $ git merge-base --is-ancestor 5f61c389 HEAD → 祖先（PR 302 の REPORT・RESULT・tools/s1_pmap.py が起点に在る）
    $ git status --porcelain --untracked-files=all
    ?? experiments/analysis/grasp_roitoken_transition_pilot/tools/digests.py（本契約の道具）
    ?? tasks/T-2026-11-09-grasp-roitoken-transition-pilot/SPEC.md、spec.yaml（取り込んだ契約）

- 開始前から在る未追跡（無視されたもの）: task-start の分類で「無視・起点に在り中身が同じ」12 件（通す）。消さず動かさず、無視の一覧にも足していない

### A-2 GPU（`$S/start/a2_gpu.txt`、2026-11-09 09:59 JST）

    $ nvidia-smi --query-gpu=index,name,uuid,memory.used,memory.total,utilization.gpu,power.limit,power.default_limit --format=csv
    0, NVIDIA RTX A6000, GPU-1b153400…, 39 MiB, 49140 MiB, 0 %, 220.00 W, 300.00 W
    1, NVIDIA RTX A6000, GPU-525aae08…, 37 MiB, 49140 MiB, 0 %, 220.00 W, 300.00 W
    $ nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c . → 0
    $ nvidia-smi -i 7 --query-gpu=index --format=csv,noheader → No devices were found（rc 6）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh → count 9 ／ --match-exe /nonexistent/bin/python9 → count 0

- 全体量 39・37 MiB − 一覧の和 0 MiB = 39・37 MiB（前の契約の開始時と同じ常駐分）。**本契約以外の使用なし**

### A-3 記憶領域（`$S/start/a3_df.txt`）

    $ df -B1 /home/ubuntu/slocal2 /home/ubuntu
    /dev/sdb1  Available 1,241,149,272,064 B（使用 84%）  ← 空間特徴の見込み約 150 GB の 2 倍（300 GB）以上
    overlay    Available 1,369,835,782,144 B

### A-4 試験・仮想環境（`$S/start/a4_pytest_start.txt`・`a4_fail_names.txt`・`a4_venv_list.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped, 26 warnings in 46.69s
    失敗の名前（11）: test_check_spec::test_teacher_detection_rate、test_engines::test_mmdet_trainer_eval_recipe_in_metrics、
      test_fetch_task::test_rejects_unknown_file_name、test_research_logger の 4 件（test_log_run_idempotent、
      test_run_logging_invokes_log_run_on_finally、test_run_logging_no_double_post_on_normal_exit、
      test_run_logging_swallows_exception_in_user_block）、test_stage1_ptower_heads::test_existing_candidates_match_baseline[A,B,C,linear]
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 108 行 9c7be5c99d6b768a…、.venv-relation-detr 72 行 a74c9c787e79f014…（T-2026-11-08 の記録と一致）

### A-5 禁止の場所・重ねの BODY・重みの開始時の要約値（`$S/start/digests_start.json`、道具 `$A/tools/digests.py`）

T-2026-11-08 の digests.py の写し（根の一覧・重み・自分の tasks のフォルダを本契約に合わせた）。各根の下の全ファイルを中身で sha256 し、
(相対経路, 大きさ, sha256) の並びをもう一度 sha256。rc 0。

| 根 | ファイル | 大きさ B | sha256 の先頭 |
|---|---:|---:|---|
| third_party | 268 | 4,388,156,080 | ebfc6fe08c6f53ba |
| 重ねの BODY `/home/ubuntu/slocal2/s2fix-bengio-body` | 243 | 3,097,796 | 667933c84fdbaec3 |
| scripts（本契約が型を足すので変わる） | 419 | 4,017,750 | df01a20e3d2ac2b9 |
| configs | 104 | 153,073 | 8b6360005bf11707 |
| data/raw | 235,773 | 10,518,871,982 | 0048147de668afd9 |
| data/external | 38 | 9,692,981,482 | 37acfc82cc14610e |
| data/annotations | 111 | 950,979,054 | 3d1e52b1c3fb23de |
| data/processed | 246 | 12,196,174,327 | 45d582f115877b6c |
| data/splits | 5 | 51 | a757e013e4e6dd5f |
| experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42 | 10 | 94,413,766 | bab579d8329ef9a0 |
| experiments/phase1/grasptower_G_{all,H1,H2}_seed42 | 10・10・10 | 11,295・11,201・13,458 | 87d9a1cd・ad7a62be・752f993e |
| experiments/analysis/grasp_tower_rebuild | 3 | 38,433 | dbeb548e43eaea2c |
| experiments/analysis/grasp_pilot_arms | 69 | 199,182 | 7273d3666b324467 |
| experiments/analysis/stage2_w23_bengio | 152 | 2,777,847 | 59f158141d1cb849 |
| experiments/analysis/grasp_cards_survey | 9 | 106,545 | 765fb82ab6a4e233 |
| experiments/analysis/stage2_pilot_folda | 107 | 594,176 | 06c2a2e3a4c2aeb5 |
| tasks（本契約のフォルダを除く） | 1,889 | 114,597,743 | 1bc558ccbb772541 |
| store T-2026-11-05-grasp-tower-rebuild | 190 | 22,410,806,115 | 1a778ed32893d3b3 |
| store T-2026-10-18-stage2-pilot-folda | 30 | 1,144,270,644 | a400c01308c43a19 |
| store T-2026-11-06-grasp-pilot-arms | 138 | 7,295,870,483 | 3ed5b2b3896b592d |
| store T-2026-11-01-stage2-w23-bengio | 844 | 3,248,781,714 | 123558ce88096294 |
| store T-2026-11-08-grasp-cards-survey | 37 | 7,179,290,811 | ad02f6c4bbf79f1a |

- 重み: P_ft 79c2c4782458c981、P_head 0d76d446796f855a、P_cache c402e214d28d32c6、G_all 5ea2cbf479254d78、G_H1 5cfa055cbc72329c、G_H2 efdefccd4484fc6a
- 仮想環境（digests.py の方式。A-4 とは別の数え方）: .venv 108 行 f6c43729…・site-packages 06068852…、.venv-relation-detr 72 行 d0724876…・4f0538a3…

### A-6 contract.conventions_rev と meta.created_from

    $ git log -1 --format=%H -- context/conventions.md → 2d946b07…（契約と一致）
    $ git log -1 --format='%H %cI' -- runindex/ → b524173e7a2812ae5261ec7601fb629d1a97b60a 2026-11-08T19:39:09Z
    $ python3 -c "csv.DictReader の行数" → index 2647、experiments 1327、verdicts 1977

- 契約の値（d3e319ac・2,623/1,305/1,947）と食い違ったため spec.yaml の `meta.created_from` を実測で差し替え、`meta.amendments` に記録した。
  `make task-validate` は差し替えの後も OK

**G1: pass**（分岐が feat/ で起点が origin/phase0、PR 302 の内容が起点に在る、本契約以外の GPU 使用なし、空き 1.24 TB ≥ 300 GB、要約値を記録）

## Task B — 材料（G2）

### B-1 G の見取り・P の重みの照合（`$A/tools/b12_inputs.py`、`$S/b/b12.json`）

    $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B $A/tools/b12_inputs.py --out $S/b/b12.json

- 目録 `experiments/analysis/grasp_tower_rebuild/signals_manifest.json` の B_m（pred_noCF・pred_CF・shuffle・shuffle_CF × train/val の見取りの json と地図の npy、16 件）と
  P の fine-tune（79c2c478…、T-2026-11-08 audit 102 行の記録）・時間ヘッド（0d76d446…）・キャッシュ（c402e214…、四本目の run の config 15・17 行）: **19/19 一致**
- 対照: 見取りの json（B_pred_noCF_val.json）を写して 100 バイト目を 1 ビット反転 → a889b72b…（記録 6e639261… と不一致）

### B-2 塔単独の val（同上）

- macro Jaccard 0.7762185528074379・accuracy 0.8712871287128713、記録（`common.py` PT_RECORD）との差 0.0・0.0（許容差 1e-6）
- 対照: 別 seed の塔の記録（runindex、`stage1_ptower_r3_064_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed123`、ilya）0.6883636・0.8917492 との差 +0.0879・−0.0205（許容差を超える）

### B-3 空間特徴（`$A/tools/b3_pmaps.py`、`$S/feat/`、GPU 0 に val・GPU 1 に train）

    $ CUDA_VISIBLE_DEVICES=0 python $A/tools/b3_pmaps.py --part val --out-dir $S/feat
    $ CUDA_VISIBLE_DEVICES=1 python $A/tools/b3_pmaps.py --part train --out-dir $S/feat

- 読み方は T-2026-11-08 の s1_pmap.py と同じ（build_backbone → load_state_dict → fc = Identity → eval、EVAL_TRANSFORM = Resize(800)、deterministic(42)）。入力 3×800×1422
- val（1,515 フレーム、動画 09・10、0.105 s/フレーム）: layer4 (1515, 2048, 25, 45) fp16 6,981,120,128 B sha256 8d6ac26037f268ba…、
  layer3 (1515, 1024, **50, 89**) fp16 13,807,104,128 B b0d2146131fd529e…。対照: 空間平均とキャッシュの相対 L2 最大 4.24e-5（1e-3 超 0 件）、
  1 つずらしたフレームとは最小 0.0795（1e-3 以下 0 件）。avgpool の出力とキャッシュの相対 L2 最大 1.53e-6
- train（9,657 フレーム、動画 01・02・03・06・08・11・12・13・14・15、0.090 s/フレーム、868 s）: layer4 (9657, 2048, 25, 45) fp16 44,499,456,128 B bef6c59b71c70a4d…、
  layer3 (9657, 1024, 50, 89) fp16 88,010,035,328 B bcf3db23d1a88fe2…。対照: 空間平均とキャッシュの相対 L2 最大 4.20e-5（1e-3 超 0 件）、1 つずらすと最小 0.0530（1e-3 以下 0 件）。
  avgpool とキャッシュの相対 L2 最大 1.49e-6。合計 153 GB（`du -sh $S/feat` 143 GiB）
- 裏の命令の終了コード 1 は、最後の `tail -3 a b`（zsh で使えない書き方）の失敗。二つの取り出しの記録はどちらも rc=0
- layer3 の地図は SPEC の「50×90」ではなく 50×89（1422 → 711 → 356 → 178 → 89）

### B-4 案 3 の枠と幾何・正解の把持（`$A/tools/b4_boxes.py`、`b4_gtcheck.py`、`$S/b4/`）

- 規則: マスク = 地図の値 ≥ 128（round(p × 255)、p ≥ 0.5）。外接矩形は 270×480 の画素の縁、連結成分に分けない。幾何 6 = 正規化した中心 x・y、幅、高さ、枠の面積、有無。
  座標: 地図 × 4 → 元 1080×1920 → P の入力（y × 800/1080、x × 1422/1920）→ layer4 ÷ 32・layer3 ÷ 16
- 予測の源: train は pred_CF（B/pred_CF_train_m.npy）、val は確定（raw/all_val_m.npy）。見取りの frame_ids は工程の目録の順と一致（assert）
- 入れ替え: train は shuffle_CF、val は shuffle の見取りの mapping（二つの mapping は同じ。地図は予測の源と同じ）。
  **同じ動画への対応が train 11.5%・val 55.6%、自分自身への対応 0・2 件**（SPEC の「別の動画の同じ相対時刻」ではない。起票者の誤り）
- 有無（予測、[tool_L, tool_R, tool_B, hand_L, hand_R]）: train [8193, 8711, 577, 9028, 8471]、val [1300, 1458, 451, 1499, 1487]。器具の和集合 train 9,523・val 1,514
- 正解の把持の地図: train 9,657 フレームのうち注釈あり 9,356・なし 301、val 注釈あり 1,514・なし 1（**注釈の無いフレーム = loss_mask の一覧**、その行の地図は全部 0）。
  sha256 train 30974fa3…・val 2076ef90…。有無 train [7129, 7176, 952, 8659, 8386]、val [1231, 1274, 176, 1491, 1463]
- 照合（`b4_gtcheck.py`）: 注釈を独立に復号して作り直した地図が、seed 42 で選んだ 200 フレームで保存した地図と **200/200 一致**（隣のフレームとは 0/200）
- 対照: マスクを x 方向に 1 画素ずらすと枠が変わる — 予測 train 34,980/34,980・val 6,195/6,195、正解 train 32,293/32,302・val 5,633/5,635
  （変わらなかった枠は roll で端の画素が回り込んだもの）
- **実行者の誤り**: `b4_boxes.py` の記録 `b4_record.json` は正解の地図の統計（鍵 `gt`）を後の枠の統計で上書きした。地図と枠のファイルは正しく、統計は `b4_gtcheck.json` で測り直した

### B-4 の続き ROI のトークン（`$A/tools/b5_tokens.py`、`$S/tok/`）

- torchvision roi_align（7×7、aligned=True、sampling_ratio=2）→ 7×7 の平均。源 pred・gt（5 個）、union（1 個）、shuffle（mapping で持ってきた枠でこのフレームの特徴を切る、5 個）
- 形: layer4 (N, 5, 2048)、layer3 (N, 5, 1024)。在る枠の数 = 零でないトークンの数（例 val pred 6,195・gt 5,635・union 1,514・shuffle 6,195）
- 所要: layer4 train 105 s・val 27 s、layer3 train 217 s・val 51 s
- 対照（画像全体の枠の ROI 平均と地図の空間平均）: layer4 val 相対 L2 中央 0.082・最大 0.156、別のフレームとは最小 0.103・中央 0.309。
  layer3 val 最大 0.089、別のフレーム最小 0.081・中央 0.102。**最大と最小が重なり、この対照は弱い**（全体の枠の ROI は端の標本点の分だけ空間平均と違う）

### B-5 案 5 の窓（`$A/tools/b6_windows.py`、`$S/seq/`）

- 時刻 = 番号 × 2 秒。**G の出力の最小の間隔 2 秒 = Δ（train・val）→ 間隔の水準を落とした（Δ = 2 秒だけ）**
- 境（クリップが変わるか間隔 > 2 秒）: train 605（間隔 > Δ 592・クリップの始め 13）、val 196（193・3）。区間の長さ train 中央 10（1〜268）、val 中央 5（1〜47）
- 時点の数: k=4 train 35,177・val 4,973（全部埋まる窓 7,972・992）、k=16 train 101,211・val 10,638（3,926・243）
- 対照: 境を無視して伸ばした写しで k=4 train 38,622・val 6,054、k=16 train 154,392・val 24,120（時点の数が変わる）。k=1 は変わらない（9,657・1,515）
- 並べ替え: 在る時点が 2 個以上の窓 train 9,052・val 1,319 のすべてで順が変わった
- 正解の列: 注釈の無いフレームの時点は「無し」（GT_k4 train 34,173・val 4,969、GT_k16 98,780・10,633）
- 列のファイル: seq_{SW,SWperm,SWR,SWU,GT}_k{4,16}・seq_S1_k1 × train/val、(a) (N, k, 320)、(b) (N, k, 39)、印 (N, k)

### B-6 把持の注釈のある行（参照段の集合）

- `has_gt`: train 9,356・val 1,514 行（上の B-4）

**G2: pass**（G の信号と P の重みの sha256 が 19/19 一致、塔単独の val の差 0.0、layer4 の空間平均がキャッシュと相対 4.2e-5 以内で一致し別フレームでは外れる、
窓の列が規則どおり（境で切る・伸ばすと時点の数が変わる）、正解のマスクが注釈と 200/200 一致）

## Task C — 殺し実験（カード #9。`$A/tools/c_kill.py`、`$S/c/c_kill.json`、GPU 0）

    $ CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 python $A/tools/c_kill.py --box-dir $S/b4 --tok-dir $S/tok --seq-dir $S/seq --out $S/c/c_kill.json   → rc=0

- 線形の層の処方（実行者が決めた。測る前に道具に固定）: train の平均・標準偏差で標準化、Linear(D → 9)、クラスの重みつき交差エントロピー（dp_train と同じ規則）、
  AdamW 学習率 1e-3・重み減衰 1e-4、batch 512、100 epoch、seed 42、最後の状態。val の各フレームの argmax を動画ごとの列にして PhaseEvaluator
- 殺す条件の閾値 0.001（m を仮に 0.2 pt とした m/2）

| 項目 | 行（train/val） | 次元 | base（J / acc / 6 工程） | plus（J / acc / 6 工程） | plus − base | 殺す条件 |
|---|---|---|---|---|---|---|
| 陽性対照（＋ 正解の工程の one-hot） | 9,657 / 1,515 | 2048 → 2057 | 0.5936 / 0.8205 / 0.6925 | 0.6096 / 0.8191 / 0.6903 | +0.0160 / −0.0013 / −0.0022 | — |
| 案 3 正解の枠の ROI（layer4） | 9,356 / 1,514 | 2048 → 12293 | 0.5930 / 0.8217 / 0.6918 | 0.6219 / 0.8421 / 0.7256 | **+0.0289 / +0.0205 / +0.0338** | 当たらない |
| 案 3 G の予測の枠の ROI | 9,356 / 1,514 | 2048 → 12293 | 同上 | 0.6183 / 0.8349 / 0.7213 | **+0.0253 / +0.0132 / +0.0295** | 当たらない |
| 案 5 L = 8 秒（窓 k=4 の (b) と印） | 9,657 / 1,515 | 2087 → 2247 | 0.5958 / 0.8185 / 0.6951 | 0.5860 / 0.8099 / 0.6836 | −0.0098 / −0.0086 / −0.0114 | 差は当たる |
| 案 5 L = 32 秒（k=16） | 9,657 / 1,515 | 2087 → 2727 | 同上 | 0.5918 / 0.8139 / 0.6904 | −0.0040 / −0.0046 / −0.0047 | 差は当たる |

- **陽性対照が弱い**: 正解の工程の one-hot を足しても差は Jaccard +0.016・accuracy −0.0013。train が P の特徴だけでほぼ分かれ、足した列を重く使わないとみる。
  この線形の層は「足した情報の有用さ」に対する感度が低く、案 3 の差（12,245 次元を足した）には次元の増加の分が混ざりうる。処方は結果を見た後に変えていない
- 案 5 の遷移の事象（val、G の確定の出力。区間の始めは事象なし）: 出現 220・消失 210・持ち替え 35・両手の開始 118・終了 121、いずれか 391 フレーム

| L | 境界の ±L 秒の中 / 外 | 事象の率 中 / 外 | 比 | null の 95% 区間（区間の並びを動画ごとに 2,000 回並べ替え） | 比が null の区間の中 | 両側 p |
|---|---|---|---|---|---|---|
| 8 秒 | 115 / 1,400 | 0.2087 / 0.2621 | 0.796 | [0.501, 1.462]（中央 0.943） | はい | 0.393 |
| 32 秒 | 325 / 1,190 | 0.2215 / 0.2681 | 0.826 | [0.569, 1.396]（中央 0.942） | はい | 0.403 |

- 判定: **案 5 は殺す条件に当たった**（両方の L で、比が null の区間の中・1 を含む区間、かつ線形の層の差が両方の指標で 0.1 pt 未満）。
  **案 3 は当たらない**（正解の枠・G の予測の枠とも差が 0.1 pt を大きく超える）
- 「率の比の区間が 1 を含む」を、動画単位の並べ替えで作った null の比の 95% 区間に観測の比が入ること（null の区間は 1 を含む）と読んだ（実行者の判断）
- SPEC Task C-3 に従い、**ここで停止して掃引に進むかを利用者に諮る**（2026-11-09 JST）

## 利用者の決定（2026-11-09 JST）

- Task C の結果を示して諮り、利用者の返事「**案3だけ進める**」。案 3（型 RT）の Task D・E だけを回し、案 5 の型 TW と 68 本は作らず回さない（`tasks/inbox.d/` に 1 行）

## Task D — 恒等性と対照（G3。`$A/tools/run_d_check.sh`、`compare_default.py`、`$S/d/`、GPU 0）

- 実装: `scripts/stage2pilot/dp_model.py` に型 `roitoken`（`RoiTokens`）、`dp_train.py` に型 RT・腕 geo・union・引数 `--rt-dir --rt-layer --rt-content --rt-k` を**足す形**で書いた。
  既存の型の経路は変えていない（`scopes` の既定の型の一覧から RT を除き、従来と同じ一覧にした）。ruff: 変更した 2 ファイルは指摘なし（同じフォルダの既存の 3 ファイルに既存の指摘 4 件）
- 起点の版: `git show 129e79b0:scripts/stage2pilot/{dp_train,dp_model}.py` → `$S/check/old/stage2pilot/`（a82e25d5…・426a2b2b…）、`common.py` は本体へのシンボリックリンク。
  変更後: dp_train 750daeea…・dp_model 994570b7…（`$S/d/code_sha256.txt`）
- W&B は手元だけ（`WANDB_MODE=offline`、仮の鍵 `offline-placeholder`。資格情報は読み込まない）

### D-1 既定の挙動（`$S/d/compare_default.json`）

    $ bash $A/tools/run_d_check.sh 0
    [d1] identity GA old rc=0 / identity D1-L1 old rc=0 / train GA old rc=0 jaccard=0.769818
    [d1] identity GA new rc=0 / identity D1-L1 new rc=0 / train GA new rc=0 jaccard=0.769818
    $ python $A/tools/compare_default.py $S/d experiments/phase1/grasprt_chk_dpold_001_GA-noflag_gt_ep1_smoke_seed42 \
        --new-runs experiments/phase1/grasprt_chk_dpnew_001_GA-noflag_gt_ep1_smoke_seed42 --out $S/d/compare_default.json
    identity GA 差 0 件・D1-L1 差 0 件。試走: metrics・history・per_class・config・notes・val の確率・界面の重みの全テンソルが一致、
    陽性対照（新しい版の metrics の Jaccard を 1e-9 ずらした写し）を検出。all_equal: true

### D-2・D-3 RT の学習前の出力と陽性対照（`$S/d/identity_RT_<層>_<中身>_K<K>.json`）

- 8 設定 × 7 腕（empty・pred_CF・geo・union・shuffle・gt・gtpred_CF）の 56 件で、**学習前のロジットと塔単独のロジットの差の最大 0.0**
- 参照段の 2 腕は把持の注釈のある 1,514 行で評価するため、Jaccard の値は塔の記録（1,515 行）と同じにならない（`jaccard_equals_taskB: false`）。ロジットは一致
- 陽性対照（出力射影の重みと bias を N(0, 0.05²)）: 56 件すべてで変わる（ロジットの差 0.060〜0.642）。**T0（empty）も変わる**: 空トークンは学ぶ定数で、
  問い合わせ x(t) に依る注意の出力が零でないため（SPEC の「空の腕は入力が零で変わらない」は RT には当てはまらない）
- 界面のパラメータ数: layer4 K16 roi_geo 101,200・roi 101,088、K64 404,800・404,352、layer3 K16 84,816・84,704、K64 339,264・338,816（10 トークンの腕は枠位置と空トークンの分だけ多い）
- RT の試走（`grasprt_chk_rt_001_RT-layer4-roi_geo-K64_gtpred_CF_ep1_smoke_seed42`、腕に数えない）: rc 0、1 epoch 0.74 s、受け取り手は不変

**G3: pass**（既存の型の既定の挙動が変わらない、RT の全腕で学習前の出力が塔単独と一致、陽性対照で変わる）

## Task E — 学習（案 3 だけ。`$A/tools/run_e.sh`、`$S/e/`）

    $ for w in 0..5: bash $A/tools/run_e.sh $((w % 2)) $w 6 &     （GPU 0・1 に 3 本ずつ、計 6 本並行）
    開始 2026-11-09 10:40:12 JST、終了 10:42:15 JST。56 本すべて rc=0（DP_RUN_COMPLETE）、止まった run 0 件（aborted/ は空）

- run: `experiments/phase1/grasprt_rt_<番号>_RT-<層>-<中身>-K<K>_<腕>_ep4_seed42`（56 件）。番号は並行の起動で重なりうるが、名前は設定と腕で一意
- 処方: W1、学習率 5e-4、weight decay 0.01、平滑化 0.3、4 epoch 固定・最後の状態、seed 42。学習 1 本 1.4〜9.4 s（metrics の elapsed_seconds、読み込みを除く）
- 界面の重み: `$S/dp_ckpt/<run>.pth`。epoch ごとの val の J・acc、界面の L2 ノルム、出力射影の絶対値の最大は各 run の `logs/history.json`
- 裏の命令の終了コード 1 は、最後の `grep "rc=[1-9]"` が 0 件だったため

## Task F — 集計・検証・報告

### F-1 集計（`$A/tools/f_aggregate.py`、`$S/f/summary.json`）と REPORT（`$A/tools/make_report.py` → `$A/REPORT.md`）

- g: run 56/56、全本 4 epoch・最後の状態、存在しない run の名前 2 つで 0・0 件、受け取り手不変（全本）
- h: 差（8 設定 × 6 差 × 3 指標 = 144 個）を各 run の val の確率の argmax から PhaseEvaluator で測り直して一致（ずれの最大 0.0）。1e-6 ずらした写しを検出
- i: 通した動画 train 01・02・03・06・08・11・12・13・14・15、val 09・10。{04, 05, 07} との共通 0 件、04 を混ぜると [04]
- layer4-roi-K64 の TGeo と T0 は val の argmax が全フレームで一致（確率の差の最大 09 0.0036・10 0.0019）。入力が違うことは確率の差で確かめた
- REPORT の直書きの値を確かめた: dressing の範囲は記録から計算した 0.0732〜0.7308（最初に書いた「0.31〜0.70」は誤りで、計算する形に直した）

### F-2 無変更・試験・禁止領域（`$S/end/`）

    $ python $A/tools/digests.py --out $S/end/digests_end.json --files $S/end/digests_end_files.json   → rc=0
    24 根のうち 22 が開始時と一致。違う 2 根: scripts（stage2pilot/dp_model.py・dp_train.py の 2 件だけ。本契約の型の追加）、
    tasks（inbox.d/T-2026-11-09-grasp-roitoken-transition-pilot.md の 1 件の追加だけ。本契約の判断の受け皿）。重み 6 件・仮想環境 2 つは一致
    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped（失敗の名前は開始時と diff 0 行）
    $ make forbidden-check TASK=T-2026-11-09-grasp-roitoken-transition-pilot
    status pass、changed 490・checked 490、permitted 484、違反 0 件

- 終了の検査の時点で、別の契約の道具 6 件（`experiments/analysis/stage2_pd_w3_lowlr_andrew/tools/w3lra_*.py`、mtime 2026-11-09 10:10〜10:28 JST）が同期で届いていた。
  `git ls-tree origin/phase0` で phase0 に無い（0 件）ことを確かめ、`.git/info/exclude` に `experiments/analysis/stage2_pd_w3_lowlr_andrew/` を 1 行足した。消さず動かさず

## 追加: 案 5 の掃引（利用者の依頼 2026-11-09「案5、追加でやって」）

完了の手続き（PR #307・task-report・`task-release: RELEASED`）の後に、利用者が案 5 の掃引を追加で求めた。同じ契約・分岐・PR に積む。

### X-0 再開（2026-11-09 JST）

- 目印は task-start を経ずに置き直した（手順書「5. 実行する」の例外。所有の記録つき）:
  `printf 'task_id=%s\nbranch=%s\n' T-2026-11-09-grasp-roitoken-transition-pilot feat/grasp-roitoken-transition-pilot > .sync-pause`
- 外していた間に分岐は動いていない: `git rev-parse HEAD origin/feat/grasp-roitoken-transition-pilot` → どちらも 07323d1f。`origin/phase0` は 129e79b0 のまま。
  `~/claude-sync/sync-alerts.log` に本分岐の auto-merge・auto-push の行は無い
- 同期で別の契約の run 6 件（`experiments/phase1/w3lra_*`）が届いていた。phase0 に無い（`git ls-tree` 0 件）ことを確かめ、`.git/info/exclude` に
  `experiments/phase1/w3lra_*/` を 1 行足した。消さず動かさず

### X-1 実装（型 TW）

- `dp_model.py` に型 `transwin`（`TransWindow`: 時点ごとの MLP（D + 1 → 64 → 64）＋ 相対時刻の埋め込み、x(t) を問い合わせにした 4 head の注意、
  零初期化の 64 → 2048 の射影を x(t) に足す）、`dp_train.py` に型 TW・腕 `t1`・`perm`・引数 `--tw-dir --tw-form --tw-L --tw-k` を足す形で書いた
- K = 64: Stage 2 の D1 concat は隠れ次元を持たない（`Conv1d(S, conv_in.out_channels, 1)`）。`conv_in.out_channels = num_f_maps = 64` を読んだ値とした
- 入力: B-5 の列（`$S/seq/`）。無い時点は 0 と印 0 のまま入れる（注意で隠さない）。S_0 は k = 1 の 0 の列、S_1 は k = 1 の時刻 t の列
- 腕の名前: empty = S_0、t1 = S_1、pred_CF = S_W、perm = S_W-perm、union = S_W-U、shuffle = S_W-R、gt = 参照段 正解、gtpred_CF = 正解 ⊕ 予測（各時点で正解が先）

### X-2 恒等性と既定の挙動（`$A/tools/run_d2_check.sh`、`$S/d2/`、GPU 0）

    $ bash $A/tools/run_d2_check.sh 0     → 全行 rc=0
    $ python $A/tools/compare_default.py $S/d2 grasprt_chk2_dpold_001_… grasprt_rt_002_RT-layer4-roi_geo-K16_pred_CF_ep4_seed42 \
        --new-runs grasprt_chk2_dpnew_001_… grasprt_chk2_rt_001_RT-layer4-roi_geo-K16_pred_CF_ep4_seed42 --out $S/d2/compare_default.json
    identity GA・D1-L1 の差 0 件、GA の試走の全記録一致。案 3 の RT の 1 本を TW を足した版で回し直すと、metrics・history・config・確率・
    界面の重みの全テンソルが学習済みの run と一致（J 0.773103）。all_equal: true

- TW の identity: W1・W2・W3 × 形 a・b × L 8・32 の 12 件 × 8 腕 = 96 件で学習前のロジットと塔単独の差の最大 0.0。学ぶ範囲の集合は W ごとの定義と一致
  （受け取り手の学ぶパラメータ W1 0・W2 36・W3 72 個）。出力射影を N(0, 0.05²) にすると 96 件すべてで差 0.080〜0.213
- 界面のパラメータ数: 形 a 297,408（k = 1）〜298,368（k = 16）、形 b 279,424〜280,384
- TW の W2 の試走 `grasprt_chk2_tw_001_TW-W2-b-L32-K64_pred_CF_ep1_smoke_seed42`（腕に数えない）: rc 0

**G3（案 5）: pass**

### X-3 学習（`$A/tools/run_e5.sh`、`$S/e5/`）

    $ for w in 0..5: bash $A/tools/run_e5.sh $((w % 2)) $w 6 &     （GPU 0・1 に 3 本ずつ）
    1 巡目 2026-11-09 11:22:20〜11:24:43 JST: 64 本 rc=0、4 本 rc=1（TW-W1-a・W1-b・W2-a・W2-b の S_0）

- 止まった原因: 空の腕の学習の後に回る陰性対照（`negative_control`）が相手の腕を `pred_noCF` にしていて、TW では窓の L を要するため SystemExit で止まった。
  学習そのものは 4 epoch 済みだった。W3 の S_0 の 2 本は直した後に始まったので通った
- 直し: `negative_control` の相手を TW では `t1`（S_1、k = 1 で S_0 と同じ形）にした（`dp_train.py`。空の腕でしか呼ばれない関数で、ほかの腕・型の経路は変わらない）
- 止まった 4 本の実験フォルダと界面の重みと起動のログを保存先の `$S/aborted/{phase1,dp_ckpt}/` へ移した（SPEC Task E-2）
- 回し直し 11:25:06〜11:25:30 JST（GPU 0 で 4 本、ほかは「実験フォルダが在る」で飛ばした）: 4 本とも rc=0
- 68 本がそろった。学習 1 本 1.48〜9.19 s（metrics の elapsed_seconds）。W2・W3 の時間ヘッドの重みの変化の L2 は 4 epoch 目で 1.50〜2.02（summary5.json の history から）

### X-4 集計と検証（`$A/tools/f_aggregate5.py`、`$S/f/summary5.json`、REPORT §7）

- g: run 68/68（無い 0）、全本 4 epoch・最後の状態、存在しない run の名前 2 つで 0・0 件
- W1 の 28 本は受け取り手不変。W2・W3 の 40 本は学ぶ範囲が変わり（true）、範囲の外は不変（true）
- h: 差 216 個を確率から測り直してずれの最大 0.0、1e-6 ずらした写しを検出
- i: 通した動画は案 3 と同じ 12 本、{04, 05, 07} との共通 0 件、04 を混ぜると [04]
- **腕の間で指標がちょうど同じになる所が多い**（例: S_W と S_W-perm が W1-a-L32・W1-b-L32・W2-a-L8・W2-a-L32 で同じ、W2-b-L8 で S_W-perm・S_W-U・S_W-R が同じ）。
  確率を比べると腕ごとに違い（最大差 0.0003〜0.037）、argmax だけが全フレームで一致した。並べ替えの列は元の列と val 1,319 行で違う（入力は変わっている）。
  TW は時点を注意で束ねるので、順の情報は相対時刻の埋め込みからしか入らず、その埋め込みが 4 epoch で初期の大きさ（標準偏差 0.022）からほとんど育っていない
- 道具の `ruff --fix` が `b12_inputs.py`・`b3_pmaps.py`・`c_kill.py`・`f_aggregate.py`・`make_report.py` の import の並びと f-string を書き換えた（実行の後。動作は変わらない）

**案 5 の結果（REPORT §7）**: W1 の S_W − S_0 は 6 工程の平均 +0.0044〜+0.0076（4/4 で正）、S_W − S_1 は +0.0025〜+0.0058（4/4 で正）。
W2・W3 の差は −0.010〜+0.007 で符号が分かれる。§5.2 の予測 3 は外れ（4 設定のうち 3 設定で 0.005 未満）、予測 4 は当たり（S_0 が塔単独から +0.024・+0.024・−0.011・−0.020）

### X-5 終わりの検査（案 5 の追加の後、`$S/end2/`）

    $ python $A/tools/digests.py --out $S/end2/digests_end.json --files $S/end2/digests_end_files.json   → rc=0
    24 根のうち 22 が開始時と一致。違う 2 根は scripts（stage2pilot/dp_model.py・dp_train.py だけ）と tasks（inbox.d の本契約の 1 件の追加だけ）。重み 6 件・仮想環境 2 つ一致
    $ pytest（A-4 と同じ命令） → 11 failed, 980 passed, 5 skipped（失敗の名前は開始時と diff 0 行）
    $ make forbidden-check TASK=T-2026-11-09-grasp-roitoken-transition-pilot → status pass、changed 1,075、permitted 1,065、違反 0 件

- 根の数は 24（開始時の A-5 の表も 24 根。F-2 に「25 根」と書いたのは数え違い）

### X-6 所要と学習の短さの記録（利用者の依頼「これ契約の報告に含めて」、2026-11-09 JST）

- 利用者の問い「終わるの早くね？」への答えを報告に入れた: REPORT §8（`make_report.py` の `speed()` が summary.json・summary5.json・b3 の記録・
  界面の重みから作る）、RESULT §3・§6、result.yaml の followups・unknowns
- 値: 学習 1 本 案 3 1.40〜9.42 s・案 5 1.48〜9.19 s（÷ 40 歩で 35〜235 ms・37〜230 ms、評価を含む）、界面のパラメータ数 84,704〜405,440・279,424〜318,912、
  4 epoch 目の出力射影の絶対値の最大 0.0161〜0.0214・0.0103〜0.0208、案 5 の相対時刻の埋め込みの標準偏差 0.0187〜0.0249。前例は PR 302 の単価の表（W2・W3 1.4〜10.0 s）
- 目印は所有の記録つきで置き直した（外していた間に分岐の先頭 d7e12fc9 と origin/phase0 129e79b0 は動いていない）
