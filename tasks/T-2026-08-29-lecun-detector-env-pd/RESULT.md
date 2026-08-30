# RESULT — T-2026-08-29-lecun-detector-env-pd

命令とその出力の全文・環境構築の全手順・run 一覧・時系列の証跡は `audit.md` にある。

## 判定

**status: pass。** 関門 G1 は pass、G2 は pass（四段と B2 が揃った）。

🔴 **関門 G0 の残る片方向（P→D）が成立した。** 前契約で資産欠落により測れなかった
B2・P→D・B4 の三項目をすべて実施した。

**run 17 件の内訳**: P→D 4 + 強い工程塔 1 + B4 の D→P 12 = 17（うち塔は特徴生成であり
索引には 16 run が載る。塔は `stage1_features/` への出力で run 証跡を持たない）。

## 1. 解決された参照

| spec の記載 | 解決 |
|---|---|
| `meta.created_from` | `09fdefb3` / 1250 / 277 / 1486 — **全一致。置換不要** |
| `contract.conventions_rev` | `a8c07e81` — 一致 |
| `inputs.denominator.ref` | experiments.csv に **1 件一意**。`n_runs=17` / `split=val` / `accuracy_mean=0.8973014948553679` |
| `inputs.frozen_source.ref` | index.csv に **1 件一意**。ckpt sha256 `03936318f9d45ac9...` が `conventions#frozen_source` の正本と一致 |
| `contract.inject_verbatim` | `conventions` の 7 アンカーの原文を参照（要約していない） |
| `inputs.sigma_policy`（省略） | `conventions#sigma` の既定（`series: pstd`）を継承 |

## 2. 完了判定（SPEC §6）

| # | 判定 | 実測の結果 | 空振りでないことの確認（実測） |
|---|---|---|---|
| a | 検出器の動作 | **前方計算が既知値を完全再現**。val AP = **0.7302938994613697** / AP50 = 0.8545901117284289 | `configs/stage/s4_phase_baseline.yaml:9` の「再 eval mAP **0.7303**」と一致。**独立な二系統目**として、P→D 四段の warm-start init mAP が四段とも同じ 0.7302938994613697 を示した（eval スクリプトと t1b 内部評価の一致）。索引の `s0_016` の 0.729749 は旧 recipe の値で別物（audit §3.1） |
| b | P→D 四段 | **四段そろった**（本書 §3）。不能の段なし | 四段の best mAP は**四つとも異なる**（0.733576 / 0.737538 / 0.741071 / 0.742487）。init mAP は四段とも同値で zero-init FiLM の恒等性を示す。`trainable=film` / `total_trainable=266880`（注入層のみ＝W1） |
| c | prereg の時系列 | prereg `762ee4f5` = **17:08:04**、最早の run が **17:30:58**。**全 16 run が後** | 16 run 分の対照表は audit §6.3・§7.3。**環境構築（clone・venv・重み取得）と前方計算の確認は学習ではない**（勾配更新をしない。前方計算は `@torch.no_grad()` の eval スクリプト） |
| d | B2 と B4 | B2: train **0.8425732477176417** / val **0.7302938994613697** → 差 **+0.1122793483**。B4: 塔単体 val accuracy **0.6924** / macro_f1 **0.4360**、D→P 四段（本書 §5） | B2 は同一 ckpt・同一 recipe（config の差分は ann_file の **1 行のみ**。`diff` を audit §5 に全量）。B4 の塔は学習出力の `videos` が `['01','02','03','06','08','11','12','13','14','15']` = **train 10 動画のみ**（val 2・test 3 を含まない） |
| e | 索引と環境の非追跡 | 索引 **1250 → 1266**（+16）。**削除 0 / 既存行の変更 0**。追加集合は本契約の run と**完全一致**（混入 0）、全件に `task_id` | 集合差の全量は audit §8。集約表も変更 0 件、判定列（`same_sign` / `verdict_pstd` / `verdict_sstd` / `agree` / `reason` / `n_seeds`）で変わったものは**なし**。`git status` で `third_party/Relation-DETR` 実装と `.venv-relation-detr` の該当は **0 件**（`.gitignore:133` と `:63`） |
| f | 変更範囲と不変 | 変更は §2 の対象＋逸脱で明記した `scripts/` に限られる（本書 §6） | 凍結源 ckpt の sha256 が作業前後で**一致**。分割 3 ファイルの sha256 を記録（`ego_train` `c28816de...` / `ego_val` `f1bc456a...` / `ego_test` `7edeab62...`）。合流時に `--exclude 'checkpoints/'` を使い、checkpoints は 12 ファイルのまま不変 |

## 3. P→D 四段（主指標 mAP、val）

| 段 | best mAP | init mAP | 空段との差 | best epoch | 実現 |
|---|---|---|---|---|---|
| 空 | 0.733576 | 0.730294 | +0.000000 | 2 | `--zero-ctx`（同一界面・入力 0） |
| 予測 | 0.737538 | 0.730294 | **+0.003963** | 2 | `--phase-source real`（S4 予測事後 9d） |
| 正解 | 0.741071 | 0.730294 | **+0.007496** | 2 | `--phase-source oracle`（GT one-hot 9d） |
| 正解 ⊕ 予測 | 0.742487 | 0.730294 | **+0.008912** | 2 | `--phase-source both`（18d・専用 model config） |

**解釈は書かない**（SPEC §9）。

## 4. B2 — 送り手の train/val mAP 差

| 分割 | AP | AP50 |
|---|---|---|
| train | 0.8425732477176417 | 0.9819822059638547 |
| val | 0.7302938994613697 | 0.8545901117284289 |
| **差（train − val）** | **+0.1122793483** | **+0.1273920942** |

## 5. B4 — 強い工程塔と D→P 四段

**塔単体（一 seed・3 epoch・105 秒）**: val accuracy **0.6924092409240924** / macro_f1 **0.4360**。
train_acc は ep0 0.8387 → ep2 0.9831。

| 段 | 平均 acc | pstd | 空段との差 | 平均 macro_f1 |
|---|---|---|---|---|
| 空 | 0.736854 | 0.005290 | +0.000000 | 0.453332 |
| 予測 | 0.744774 | 0.004356 | **+0.007921** | 0.468409 |
| 正解 | 0.750495 | 0.004312 | **+0.013641** | 0.469508 |
| 正解 ⊕ 予測 | 0.757976 | 0.003293 | **+0.021122** | 0.488676 |

受け手は新しい塔、送り手は凍結検出器（config に `gap_tag` と `signal_tag` を分けて記録）。

## 6. 環境の用意（何をどの経路で）

| 対象 | 経路 |
|---|---|
| `third_party/Relation-DETR` 実装 | 版管理下の `third_party_snapshot/lecun/` から復元。upstream `https://github.com/xiuqhou/Relation-DETR.git` の commit `b485955c72452788240600da6d0f0b8cc49f33c7` を clone → `upstream_mods.patch`（`--check` exit 0）→ `project_files.tar.gz`（記録 23 件・**欠落 0**） |
| `.venv-relation-detr` | `scripts/setup_env_relation_detr.sh` + `requirements.relation_detr.lock.txt`（72 pkg）。`SKIP_CUDA_CHECK=1` が必要 |
| ImageNet-R50 | torchvision 標準重み（認証なし）。sha256 の先頭がファイル名 `0676ba61` と一致 |
| philip 参照 | **使えなかった**（`Permission denied (publickey,password)`） |

手順は `docs/setup/lecun_detector.md` に記録した。**実装本体と venv は版管理へ入れていない。**

## 7. 実測（次の契約で使う値）

| 項目 | 実測値 |
|---|---|
| 収穫後の索引件数 | `index.csv` **1266** / `experiments.csv` 285 / `verdicts.csv` 1506 / `per_class.csv` 9195 |
| `runindex_commit` | 本契約の commit（§9 に記載） |
| prereg commit | `762ee4f57069990120cbc668730c17f376f3dfa7` / `2026-08-29T17:08:04+00:00` |
| 検出器 run の所要時間 | 2 本並行で 1 epoch 36〜40 分、6 epoch で **1 run 約 4 時間**。単独時は 2.2 it/s（37 分/epoch） |
| B4 の run 所要時間 | 12 run 合計 **約 4 分**（各 14.5〜32.2 s）。塔の学習は 105 秒 |
| GPU 利用実績 | A6000 **2 枚**。P→D は 1 段ずつ 2 枚へ振り分け、B4 は空き枠で並行実行 |
| 検出器環境 | `third_party/Relation-DETR` 実装 + `.venv-relation-detr`（いずれも版管理外・恒久的に再利用可） |

## 8. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | SPEC §1 が「lecun から philip へ SSH が使える（利用者の申告）」としたが、実測は `Permission denied (publickey,password)`。指示どおり philip 参照を前提にすると版・依存の突き合わせができない（本契約では snapshot から復元して回避した） |
| `asserted_without_measuring` | SPEC §3 A-2 は「ミラーされている `configs/detector_relation_detr/README.md` が正本の config 経路を指す」とするが、ミラーは augstrong 系 2 件のみで、凍結源が使う `train_config_egosurgery_seed42.py` を**含まない**。指示どおりミラーだけを頼ると復元できない（実体は `third_party_snapshot/lecun/` に在った） |
| `check_does_not_check` | `outputs.stamp.task_id_in: config.yaml` を要求する一方、P→D で使う `scripts/train_t1b.py` に `task_id` の配線が**無かった**。指示どおり実行すると完了判定 e（全 run が task_id 付き）を満たせない |
| `asserted_without_measuring` | SPEC §5 は B4 の塔を「ImageNet-R50 を微調整し、その特徴で TeCNO を学習する」と実施可能な前提で書くが、**画像から工程を学ぶ経路が既存に無い**。指示どおり進めると Phase C の着手時点で止まる（新規スクリプトを書いて回避した） |

## 9. 逸脱・想定外・UNKNOWN・判断待ち

**逸脱**

1. `judgement` — 未追跡の `.sync-pause.released` を削除せずスクラッチパッドへ退避してから phase0 へ切り替えた。
2. `judgement` — `decisions_required` の 1 件（実装の用意経路）を提示し、**snapshot から復元**の回答を得た。外部通信（clone / PyPI / torchvision 重み）も三点とも許可を得た。いずれも認証を伴わない。
3. `judgement` — prereg の停止条件「一 run 六時間超」に一度該当し停止・提示したが、利用者の判断で続行した。**なお定常状態の再実測では 1 run 約 4 時間で停止条件の内側**。最初の見積もり（103 分/epoch）は smoke 6 step 由来の過大評価だった。`meta.amendments` に記録。
4. `spec_defect` — `scripts/train_t1b.py` へ `--phase-source both`（18d 連結）・`--task-id`・`T1B_MODEL_CFG` の override を追加した。`scripts/` は §2 の変更対象外である。18d 用 model config は third_party 内に作った（差分 1 行）。
5. `spec_defect` — `scripts/train_phase_tower_r50.py` を**新設**した（B4 の塔。既存に経路が無い）。`scripts/train_b2a.py` へ `RELDETR_SIGNAL_TAG` を追加した（受け手と送り手のタグ分離）。いずれも §2 の変更対象外。
6. `judgement` — B4 の特徴を `data/processed/stage1_features/imagenet_r50_phasetower_seed42/` へ**新規に書いた**。§2 は「生データ・分割・既存キャッシュ」への書き込みを禁じており新規キャッシュは対象外と解したが、`data/` 配下ではある。
7. `environment` — ホストの nvcc が **12.9**（文書の前提 11.8 は不在）のため `SKIP_CUDA_CHECK=1` を渡した。JIT ビルドは成功したが保証された構成ではない。
8. `judgement` — 時短のため B4（検出器非依存）を P→D と**並行実行**した。GPU メモリに各 18〜26 GiB の空きがあった。
9. `judgement` — `ruff` が `train_b2a.py` に I001 を 1 件出すが HEAD でも出る既存指摘のため直していない。新設した `train_phase_tower_r50.py` は `All checks passed`。

**UNKNOWN**

1. 🔴 **t1b の実効バッチ（2）と S0 検出器学習の正本レシピ（4 = per-GPU 2 × 2 GPU DDP）の不一致。**
   `train_t1b` を DDP で起動する記述はリポジトリ全域に **0 件**（`run_t1b.sh` 不在、docstring 自身が
   単一プロセス起動を記載）で、既存 t1b 23 run も同条件。利用者の判断でバッチ 2 のまま完走させた。
   四段の内部比較は同一条件で成立するが、**S0 との比較可能性は未確認**。
2. nvcc 12.9 と torch cu118 の組み合わせの妥当性。実測では通ったが検証された構成ではない。
3. philip への SSH が使えなかった原因（SSH 設定の読み取りは実行基盤の保護規則で拒否された）。
4. 強い工程塔は一 seed・3 epoch の暫定版。seed 間のばらつきは測っていない。

**判断待ち**

1. t1b を S0 parity（実効バッチ 4）に揃えるか。揃えるなら `train_t1b.py` の DDP 化が要り、既存 23 run とは比較不能になる。
2. `docs/setup/lecun_detector.md` の nvcc 前提（11.8 → 12.9）を他ホストへも展開するか。
3. 新設した `scripts/train_phase_tower_r50.py` と `RELDETR_SIGNAL_TAG` を正式な実装として残すか。
4. B4 の塔を seed 三本へ増やすか（Stage 1 の前提）。

## 10. 送出

| 検査 | 終了コード |
|---|---|
| `make task-validate` / `taskindex-check` / `inbox-check` / `context-check` / `docs-check` / `agent-check` | すべて **0** |
| `make forbidden-check` | 🔴 **2**（既知の制約） |

`forbidden-check` の違反 146 件の内訳: `runindex/` **22**（収穫）、本契約の run 配下 **136**、
**その他 4**。その他 4 件は `experiments/analysis/hts_candidate_acceptance/*.py` で、
中身が別契約 `T-2026-08-30-hts-candidate-acceptance` と名乗り、生成時刻（08-30 02:34〜02:40）が
本契約の最後の run（08-29 23:00:28）より後である。**同期による配布であり本契約の作業ではない。
commit していない**（契約 §7 の但し書きに該当。audit §8.3）。

| 項目 | 実測 |
|---|---|
| PR | 未起票（下記） |
| 台帳への報告 | 未送信（下記） |
