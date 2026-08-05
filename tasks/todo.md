# TODO — 研究ピボット「分析ファースト」のセットアップ

出典: `prompts/research_pivot_summary_and_roadmap.md`（正本は Notion）。
作成: 2026-06-15 / サーバー: lecun（RTX A6000 ×2）。

## 現状の重要な制約（実地調査で判明）

- このサーバー（lecun）は新設環境。検出ベンチは別サーバー（bengio/philip）で実施。
- `experiments/baselines/` には **軽量証拠（metrics.json 等）のみ**コミット。
  **チェックポイント・生予測・フレームワーク repo（Relation-DETR/detrex/Co-DETR）・
  フレームワーク venv は lecun に存在しない**（広域探索で確認済）。
- 現存 venv は再構築した `.venv`（mmdet 系）のみ。
- → STEP 0-1（両 recipe 再 eval）・STEP A（凍結源 = Relation-DETR 検出 backbone）は
  **成果物が無いため lecun 上ではそのまま実行不可**。

## recipe 差の分析（実測前の見立て）

- Relation-DETR test_cfg: `score_thr=0.0, max_per_img=300, NMS-free(nms_*=None)`
- locked-down: `score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6`
- NMS-free DETR では nms_* は no-op、max_per_img は両者 300 → **実差は score_thr 0.0 vs 1e-8
  のみ**で COCO AP 上ほぼ同一（Δ_recipe ≈ 0 と予想）。doc §8 注2 と整合。
  ただし doc は「実測してから決定」を要求 → 1 モデルの再 eval が必要（成果物前提）。

## STEP 0 — 土台固め（最優先ブロッカー）
- [x] 0-1 `.venv-relation-detr` 構築・検証（MS-Deform-Attn CUDA op 実コンパイル確認）
- [x] 0-1 **完走 ckpt 検証**: philip から `checkpoints/incoming/seed{42,123,456}/best_ap.pth` を配置、
      3 seed すべて記録値再現（0.7303/0.729/0.722 ±0.0005）。早期 run は破棄候補。
- [x] 0-1 **Δ_recipe 実測完了**: score_thr 軸=0（min score 4.58e-3≫1e-8）/ NMS 軸=**+0.045 mAP**
      （locked-down NMS@0.6 で 4.5pt 低下、class-agnostic NMS が異クラス重なり箱を誤除去）。
- [x] 0-1 **公式 recipe 決定 = score_thr=0.0系（NMS-free, max_per_img=300）**。三角形の検出ヘッドに
      NMS を適用しない（Δ_detection 汚染防止）。証跡: `experiments/analysis/step0_recipe/notes.md`
- [x] 0-1【イ】公式 recipe を `eval_recipe.py` に集約: `NMS_FREE_TEST_CFG`（DETR/三角形の公式）
      + `PHASE_EVAL_PROTOCOL`（工程 recipe ロック: online_causal / Jaccard strict）追加。
- [x] 0-1【イ】`DeltaCalculator._recipes_match` を **phase 側にも適用**: 固定検出キー列→「実効キー全比較
      （記述用 `DESCRIPTIVE_TEST_CFG_KEYS` 除く）」に一般化。test_delta.py に phase 保護テスト6件追加・全16緑。
- [x] 0-2 凍結源 backbone = **Relation-DETR seed42 完走 ckpt** で確定（mAP 0.7303 再現済）→ 残: 特徴抽出経路の実装

## STEP A — 単一タスク基準点（scaffold 済・エンジン実装これから）
- [x] `configs/stage/s0_frozen.yaml` 新設（scaffold: 凍結源/freeze_backbone/NMS-free recipe/2段 cache を明文化）
- [x] `configs/stage/s4_phase_baseline.yaml` 新設（scaffold: 凍結=Relation-DETR/TeCNO/online causal/PHASE_EVAL_PROTOCOL）
- [x] `eval_recipe.py` に phase 用 recipe（`PHASE_EVAL_PROTOCOL`: online_causal・Jaccard strict）を追加・テスト済
- [x] **凍結 backbone ローダ + Stage1 特徴抽出器**: `scripts/extract_stage1_features.py` 新設。
      モデルを config+ckpt で構築→backbone 凍結→`preprocess`→`backbone`→C5 を valid GAP で 2048-d 抽出。
      検出 val 8枚で smoke 検証済（C5=(1,2048,24,42)→2048-d, 全相異, frozen 確認, npz 書込/読込 OK）。ruff clean。
- [x] **frame manifest 構築**: `scripts/build_phase_manifest.py`。CSV↔画像交差→clip 時系列順、9クラス vocab。
      train 9657 / val 1515（検出 split と一致）。`data/processed/phase_manifest/{split}.json`。
- [x] **Stage1 本走（train/val 完了・検証済）**: manifest モードで `train_gap.npz`(76M) / `val_gap.npz`(12M) 生成。
      件数=manifest一致・時系列順一致・全相異・NaN なし。read_image 経路が coco 経路と byte 一致をクロス検証済。
- [x] **test 画像問題 解消 + test Stage1 完了**: ユーザーが test 画像実体(4265枚)を再転送 → manifest 再生成(test 4265有効)
      → `test_gap.npz` 抽出・検証済（順序一致・全相異・NaN なし）。**3 split キャッシュ完備**。堅牢化(0バイト除外/read skip)済。
- [x] **TeCNO 時系列ヘッド**: `src/egosurgery/models/heads/tecno_head.py`(causal MS-TCN, online)。
      `tests/test_tecno.py` 3件緑（**因果性テスト=未来フレーム不参照を構造検証**, 可変長, shape）。ruff clean。
- [x] **S4 トレーナー**: `scripts/train_s4_tecno.py`(cache+manifest→clip列→TeCNO学習→val PhaseMetrics)。
      GPU smoke 疎通（loss 4.09→3.08 単調減少）。**smoke 値0.348は疎通用で実測でない**。NpzFile 再読込バグ修正(lessons.md)。
- [x] **S4 トレーナーに証跡配線**: ExperimentManager(category=phase1) + eval_recipe(PHASE_EVAL_PROTOCOL 併記)
      + best_tecno.pth 保存。smoke は証跡なし（Δ汚染防止）。
- [x] **S4 full 実走（Δ_phase 分母 確定）**: 50epoch × seed42/123/456 完走。
      **accuracy 0.8986±0.0034 / macro-F1 0.7086±0.0192**（証跡 `experiments/phase1/s4_phase_baseline_00{1,2,3}_*`）。
- [x] **S0-frozen 完走（Δ_detection 分母 確定）**: 3-seed 完走（freeze 実ロード確認 backbone_trainable=0）。
      **mAP 0.7051 ± 0.0052**（NMS-free recipe 一致）。証跡 `experiments/baselines/s0_frozen_00{1,2,3}_*`。
      → **🎯 三角形の両分母が揃った**: Δ_detection 分母 0.7051±0.0052 / Δ_phase 分母 0.8986±0.0034。
- [x] **Jaccard 指標を phase.py に追加**（§4.2）: per-class IoU=TP/(TP+FP+FN) の macro 平均。`PhaseEvaluator.compute()` に
      `phase_jaccard` / `phase_per_class_jaccard` 追加、test_metrics.py に手計算テスト（全 8 緑）。既存 S4 分母に適用 →
      **S4 Jaccard = 0.6447 ± 0.0146**（best_tecno.pth 再評価, acc が記録値と一致＝忠実性確認）。
- [ ] **【次パス】拡充**: SKiT/SPRMamba/causal-SR-Mamba 併走（全 online）/ S6 結合手法で Δ 実測。

## 2026-06-16 — S0-frozen COCO-init head 実行チェックリスト

- [x] 方針確定: COCO-init head + seed42 frozen backbone のマージ済み初期化を採用。
- [x] Relation-DETR の S0-frozen model/train config を追加（backbone `freeze_indices=(0,1,2,3)`）。
- [x] 3 seed 起動スクリプトを追加（seed 並列: GPU0/GPU1 に 2 本、残り 1 本）。
- [x] syntax / freeze 設定 / 重み存在を実行前検証。
- [x] background 起動 + watchdog 監視開始（setsid -f、seed42/123 wave1 稼働中）。
- [x] 初期ログで GPU 使用・iter・出力先を確認（seed42/123 epoch0 iter100 到達）。

## STEP B — 既存結合を「複数」実装し Δ を測る（研究本体・いま着手）

出典: Notion §2.5(b) §7.3 ／ roadmap §5.4 ／ EDA(`experiments/analysis/dataset_eda/REPORT.md`)。
**比較の三角形（不変条件）**: Δ_detection=(結合−S0-frozen) / Δ_phase=(結合−S4)。
結合モデルは {凍結bb(Relation-DETR seed42)・初期化・解像度・検出ヘッド・検出損失/sched・
TeCNO・工程損失/sched・データ(Tool subset 10/2/3)・fps0.5・eval recipe・seed42/123/456} を
全て分母と共有し、変えるのは「もう一方のタスク+結合機構だけ（1軸）」。

### 確定事項（2026-06-18・ユーザー確認済 / 全5論点ロック）
- **結合の土台 = 2系統併設**:
  - ①予測レベル結合（neck無）: 既存 **S0-frozen 0.7051±0.0052 / S4 0.8986±0.0034(Jaccard0.6447±0.0146)** をそのまま分母に使用。
    → 片方向 pipeline(B2a/B2b)・MT4MTL-KD-style 予測蒸留＋双方向・Cross-Task Consistency（予測レベルの Tier 手法）。
  - ②特徴レベル結合（共有trainable neck有）: 凍結bb直後に neck を1枚→neck版基準点 **S0-frozen′ 0.7095±0.0091 / S4′ 0.9142±0.0017** を分母化（確定）。
    → B1 素朴MTL・region-token→工程(TAPIS/GraSP)・SANGRIA 弱ラベル SG×工程（特徴レベルの Tier 手法）。
  - ※ 凍結bbでは hard sharing の勾配交差が無いため、特徴結合は neck が無いと Δ≈0 で構造的に成立しない（設計上の核心）。
- **最初の手法 = 素朴 MTL（B1, ②系統）** → 前提に neck導入 + neck版基準点 再取得が必要。
- **(1) 4分母運用を許容**: S0-frozen / S4 / S0-frozen′ / S4′ の4基準点。STEP C で各手法を**対応する分母**と比較する規律で交絡を担保（系統跨ぎのΔ禁止）。
- **(2) B1 先頭を維持**（roadmap 準拠）。最初の Δ は neck版基準点の3-seed再学習後に出る（後ろ倒しを承知の上で確定）。
- **(3) 共有neck = (a) C5 のみに置く**。検出枝は他階層 raw＋C5-via-neck、工程枝は C5-via-neck→GAP。C5 が結合を運ぶ唯一の接点。
- **(4) 結合学習の batch 単位 = clip**（内部で per-frame 検出を回す）。TeCNO の時系列入力と検出の per-frame を両立。
- **(5) ExperimentManager category = `transfer`**。

### B0 — 前提作業（比較群の前に1回／B1が②系統のため neck まで含む）
- [x] **統合データパス（B0-1 完了 2026-06-18）**: `scripts/build_joint_manifest.py`（phase manifest から派生→tool bbox 後付け）
      + `src/egosurgery/datasets/joint_clip_dataset.py`（`JointClipDataset`, 1item=1clip, bbox+phase+任意GAP）。
      生成: `data/processed/joint_manifest/{train,val,test}.json`（frames 9657/1515/4265・boxes 32272/4707/12673・
      missing_in_tool=0 で phase frame⊆tool frame 実証・0-tool 39/0/84）。`tests/test_joint_dataset.py` 14緑・ruff clean。
      **split 検証**: `PAPER_SPLIT_VIDEOS` は名称に反し実体 10/2/3(15動画)＝Tool subset。既存 S4 分母は STEP B で有効。
      ※ tool COCO category_id=0..14 が constants.TOOL_CLASSES と完全一致（remap不要）を検証済。
      ※ 結合作業集合での 0-tool は 0.8%（123/15437）。EDA の 11% は phase 全 17233 基準（tool subset 外含む）。
- [x] **共有 trainable neck（B0-2 完了 2026-06-18）**: `src/egosurgery/models/necks/c5_linear_neck.py`（`C5LinearNeck`）。
      確定形=**1×1 線形・2048→2048・残差・zero-init**。spatial/vector 両適用で同一重み共有→**masked-GAP 可換性を数値検証**
      （工程枝=GAPキャッシュ流用 / 検出枝=C5 spatial を同一 neck で両立）。`tests/test_c5_neck.py` 5緑・ruff clean。
- [x] **neck版 単一タスク基準点 S0-frozen′/S4′ を3-seed再取得 完了（2026-06-20）**（②系統の分母・両方確定）
      - [x] **S4′（②工程分母）= acc 0.9142±0.0017 / Jaccard 0.6644±0.0036**（証跡 `s4_phase_baseline_00{4,5,6}_..._neck_seed*`）。
            neck 単体で S4 比 +1.6/+2.0pt（>1σ）→ 容量増を分母に織り込み（B1 の Δ_phase は (B1−S4′) で測る）。
      - [x] **S0-frozen′（②検出分母）= mAP 0.7095±0.0091（3-seed 確定 2026-06-20）**: seed42 0.7159 / 123 0.6992 / 456 0.7136。
            ①S0-frozen(neck無) 0.7051±0.0052 比 +0.0044（<1σ）→ neck 挿入は検出 mAP を悪化させない。
            実装: `models/detectors/relation_detr_c5neck.py`（`RelationDETRC5Neck`）+ `..._s0_frozen_neck.py` + train config
            + `scripts/run_s0_frozen_neck.sh`。証跡 `experiments/baselines/s0_frozen_00{4,5,6}_..._neck_*`。
            ※ nvidia-smi compute-apps は稀に当該 PID を偽陰性で落とす → 生死判定はログ mtime/iter 進行で行う（lessons 記録済）。
- [x] 統合トレーナー = `scripts/train_b1_mtl.py`（S6 骨格の役割。単GPU round-robin・両eval・category=transfer）。後処理 `scripts/postprocess_b1.py`
- [ ] 二重eval: 1モデルから Δ_detection(NMS-free) と Δ_phase(PHASE_EVAL_PROTOCOL) を同時出力
- [ ] online性保全: phase→det が消費する phase信号も online-causal（未来frame不参照）

### STEP B 比較群（統合版 Tier 0/1/2・現行 Notion §2.5(c)/§8.1, 2026-06-19 改訂）
<!-- 旧「B1–B6・6手法4層」は改訂で廃止。Tier 0(必須)→1(主力⭐)→2(任意) の順に同一土台で Δ を測る。 -->
- [~] **B1 素朴MTL（L4, ②系統・最初）実装完了・本番走行中（2026-06-20）**: 共有neck上で `L=wd·Ld+wp·Lp`（固定）+ Kendall&Gal。
      単GPU round-robin（検出=標準ローダ全frame, R=89でphase clip注入）。smoke PASS（両枝→共有neck勾配確認）・ruff clean。
      本番 fixed seed42/123 を 2GPU並列で起動（~12h/run）。残: fixed seed456 + K&G 3-seed → postprocess_b1 → 両Δ paired-σ。詳細 experiment_log 2026-06-20。
- [ ] **Tier 0 片方向 検出→工程（B2a, 必須）**: 各frame tool-presence(15d)/object-token を GAP(2048d) に連結→TeCNO入力。**Δ_phase のみ**。
- [ ] **Tier 0 片方向 工程→検出（B2b, 必須・EDA推奨）**: online phase posterior(9d) で検出ヘッド条件付け(FiLM/query context)。**Δ_detection のみ**。
- [ ] **Tier 1 region-token→工程（TAPIS/GraSP 型, 主力⭐）**: 検出 object/region-token を Phase head の主入力に（object-centric）。**Δ_phase**（②系統）。
- [ ] **Tier 1 弱ラベル SG×工程（SANGRIA 型, 主力⭐）**: 弱ラベル scene-graph × 工程の同時学習。H-H（ラベル効率結合）の先行・低ラベル性能曲線。
- [ ] **Tier 1 予測相互作用（MT4MTL-KD-style 蒸留 ＋ §4.6 双方向・自前, 主力）**: PAD-Net/MTI-Net の**現代版置換**＝多教師蒸留＋検出↔工程の予測相互注入。**両Δ**（結合効果①②の主検証）。
- [ ] **Tier 2 階層/整合（任意・余力）**: HCT/MSSU・OSFENet/LG-CVS/STRG ／ Cross-Task Consistency（H-C の踏み台）。両Δ。
- ※ **スキップ／格下げ（現行 §8.1 統合版・2026-06-19 改訂）**: Cross-stitch・MTAN=スキップ（同一画素グリッド前提で uninformative）／
  **PAD-Net・MTI-Net 原実装=実施しない**（MT4MTL-KD-style で代替。素朴蒸留が異粒度で効かない負の対照として分析用 最大1本のみ）／
  SSG-Com=H1（手-術具関係）側の比較へ。勾配系(PCGrad/CAGrad/FAMO/DB-MTL)は併用アドオンで比較群外。

### EDA を STEP C へ事前登録（検証の的・対照群）
- Δ_detection の的（B2b）: 希少∧工程特異術具 = Skewer/Bipolar Forceps/Scalpel/Syringe/Raspatory。
- Δ_phase の的（B2a）: signature tool = anesthesia↤Syringe / design↤Skewer / incision↤Scalpel / closure↤Needle Holders。
- 負の対照群（Δ≈0であるべき）: 偏在術具 Gauze/Mouth Gag/Suction Cannula/Tweezers ← 動いたら交絡を疑う。
- 注意: 11% frameは術具0／val Retractor 0件（per-class Δ から除外）／closure42%・dissection34% 偏在で per-phase 分解必須。

## STEP C/D（後続）
- [~] C: Δ の per-class / per-phase / 境界 / negative transfer / 自信の相補性 分解（B2a⊥B2b の方向分離を含む）
      - [x] **②系統 真の結合（検出→工程 凍結 neck 転移）per-phase 分解 — n=3 確定（2026-06-20）**:
            `scripts/analyze_phase_coupling.py`（paired-σ 判定・再走可能, 出力 `experiments/phase1/_analysis_phase_coupling_n3.txt`）。
            **結合効果 ΔL2 は全指標 中立**（paired 判定: accuracy +0.37±0.61・seed123 負, edit/seg-F1 も σ≫平均）。
            → **検出→工程 凍結 neck 一方向転移は Δ_phase 純効果なし**。容量利得は工程タスク固有で検出から転移しない。
            **per-phase 機構**: 容量と転移は逆符号で相殺（head: incision 容量+5.0/転移−4.2 等）。希少 hemostasis は逆向き大スイング(容量−6.5/転移+6.4,純≈0)だが seed 変動大→示唆止まり。
            **【撤回】n=2 の segmental 改善(解離)は非再現**（小標本アーティファクト）。詳細 `docs/experiment_log.md` 2026-06-20。
            → 結合で工程を伸ばすには勾配双方向の結合(B1素朴MTL / MT4MTL-KD-style 蒸留＋双方向)が要る、の STEP B 設計仮説と整合。
- [ ] D: 観察から結合原理を選ぶ/作り直し（§13 H-C/H-H/H-A プール）、比較群へ新手法として戻して検証

## 決定が必要な分岐（ユーザー確認）
1. 成果物ギャップの解消方針: (a) bengio/philip から ckpt+repo 転送 / (b) lecun で再学習 /
   (c) 当面スキャフォールディング（コード・config）のみ先行
2. 公式 eval recipe: 実測 Δ_recipe を待つ（score_thr=0.0系 が作業最小の最有力）

---

## 2026-07-28 — 検出側 run 成果物の永続化（/tmp 廃止 + predictions 保存）

作業前の状態: host `efros` / branch `exp/efros-wip-20260703` / commit `cb075fc`。

### 方針（厳守事項の遵守）
- 学習・評価ロジック（loss / optimizer / eval recipe / AP 算出）には触れない。
  変更は **保存先** と **保存物の追加** のみ。
- `eval_detection()` は既定の戻り値 arity を変えず、`collect_predictions=True` の
  ときだけ 3-tuple を返す（既存呼び出しは無改変で動く）。
- `T1B_WORK_DIR` は override として残す（過去 run / 既存スクリプトを壊さない）。
- ckpt 読み出し側は `checkpoints/best_t1b.pth` → 旧 flat `best_t1b.pth` の順で探す
  （旧レイアウトの残存 run も引き続き評価可能）。

### チェックリスト
- [x] A-1 `/tmp` 洗い出し（成果物 vs 意図的一時ファイルの分類）
- [x] 共通ヘルパ `scripts/run_artifacts.py` 新規（stdlib のみ / 両 venv で動く）
- [x] A-2/A-3 `train_t1b.py`: 既定出力先を `experiments/transfer/<run_name>/` に変更 + 証跡一式
- [x] B `train_t1b.py`: predictions 保存（既定 on / init・best 必須 / `--save-predictions-all`）
- [x] B-4 `eval_phase2det_test.py` / `eval_t1b_test.py`: predictions 保存 + ckpt 解決
- [x] C `logs/val_metrics_by_epoch.json`（epoch 別 mAP + per-class + best_epoch + init）
- [x] C-2 init の per-class と predictions SHA256 を記録（inj/ctrl 恒等一致の検証記録）
      → スモークで **SHA-256 完全一致**を実測（`83fe1d82…c791b2`）。ランチャーが本走ごとに自動検証。
- [x] `.gitignore`: `logs/val_metrics_by_epoch.json` と `logs/eval_meta_*.json` のみ追跡可能に
- [x] A-2 全ランチャーおよび成果物を `/tmp` に出す他トレーナの出力先変更
- [x] D `notion_logger`: Artifacts をホスト名付き絶対パス + checkpoints/predictions/logs
- [x] 検証1 スモーク実行 → **AP 再現 bit-exact（差 0.000e+00）**を smoke(20枚) と val 全 1515 枚の両方で確認
- [x] 検証2 `grep -rn "/tmp"` → 保存先としての `/tmp` は 0 件。残るのは意図的一時（wheel/alert）・
      旧 run 読み取りの後方互換（`train_status.py`）・経緯説明コメントのみ
- [~] 検証3 `pytest tests/ -q` → efros に `.venv` が無いため `.venv-relation-detr` + 一時 pytest で実行。
      **133 passed / 4 skipped / 20 failed**。20 件は全て mmdet・hydra 未導入または DINOv2 取得失敗によるもので、
      **変更前の HEAD でも同一に失敗すること**を stash で確認済み（本改修に起因する失敗は 0）。
- [x] README / docs 更新

### 未確認事項（正直な記録）
- フル依存環境（`.venv`: mmcv/mmdet/hydra 込み）でのテスト全パスは efros 上では未検証。
  `.venv` を持つホスト（lecun 等）で `PYTHONPATH=src pytest tests/ -q` を一度回すことを推奨。
- 消失済みの過去 run は本改修では復元されない（再発防止であって遡及修復ではない）。

---

## 2026-07-28（続き）— planned直近4件の前提2件（p0/l0）実行結果

方針: run台帳 planned直近4件 p0→l0→{l1a,l2}。ユーザ選択=前提2件先行。host=efros / venv=.venv-relation-detr。

### p0_artifact_persistence_and_grad_check — ほぼ完了（3-seed恒等を実測中）
- [x] (1) /tmp: 主旨達成（残13件は旧挙動コメント/意図的用途。成果物喪失系0）※字義0化は掃除機能を壊すため非推奨→判定基準の扱い要相談
- [x] (2) predictions既定on: 達成済
- [x] (3) 勾配フロー: 既存 audit_t1b_l0(film/ca/hc) all_pass=True（zero-init層grad0・out_projのみ非ゼロ）
- [~] (4) 3-seed恒等: `scripts/verify_p0_init_identity.sh` 実行中（seed42 init mAP=0.7303 恒等健全）。42/123/456完了待ち
- [ ] 証跡束ね→台帳 completed 更新

### l0_hts_acceptance — 検査完了・verdict=NOT ACCEPTED（完全版 未達）
- [x] `scripts/audit_l0_hts_acceptance.py` 新規作成・実行 → `experiments/audit/l0_hts_acceptance/acceptance_report.json`
- [x] C1✗(seg 4頂点=真マスク無) / C2✗(値5=Mouth Gag, Two Hands Tool不在) / C3✗(手46,320≠57,173, 欠落03_1/03_3/12_2/15_2) / C4✓ / C5✓
- [x] 結論: HTS完全版は未組立（egosurgery_hts空・現行派生は旧世代）。門番として前提未達を正しく検出
- [ ] 完全版の組立（raw 02_hand 4動画復活→57,173 / 把持関係 raw 04_handtool 5cls / RLE真マスク）= 別タスク・ユーザ判断待ち

### l1a / l2（重GPU・24run）— 未着手（前提未達 + 新規実装要）
- [ ] 前提: l0完全版組立 + 手mask→det注入機構の設計・実装（train_t1b/haux いずれにも無い第三方向）

---

## 2026-08-05 — TASK 契約システム ブートストラップ

task_id: `T-2026-08-03-task-contract-bootstrap`

### 計画

- [x] 1. `tasks/` 骨格、自己契約の `SPEC.md`、規約 README を作成する
- [x] 2. 一次情報を確認し、`context/conventions.md` と README を実値で作成する
- [x] 3. Draft 2020-12 JSON Schema を追加し、dev 依存へ `jsonschema>=4` を追加する
- [x] 4. validator L1 と単体テストを実装し、静的検証を通す
- [x] 5. runindex の実列を確認して validator L2 を実装し、参照解決テストを通す
- [x] 6. `make task-validate` ターゲットを追加して動作確認する
- [x] 7. exp / impl / analysis のテンプレートを追加し、L1 の hard finding がないことを確認する
- [x] 8. `.claude/skills/task/SKILL.md` を追加する
- [x] 9. root の対象6ファイルを移動せず棚卸しし、参照・由来・提案を記録する
- [x] 10. 自己適用 `spec.yaml` / `RESULT.md` を作成し、近接テスト・全テスト・禁止領域無変更を検証する
- [x] 11. コード変更内容と現在の実装状態を `README.md` に記録する
- [ ] 12. 指定単位で commit し、承認後に push と PR 作成を行う

### 成功基準

- `make task-validate TASK=T-2026-08-03-task-contract-bootstrap` が exit 0
- `tests/test_validate_task.py` が全件 passし、テスト数の実測を `RESULT.md` に記録
- `python -m pytest tests/ -q` の結果を実測で報告
- `context/conventions.md` のアンカーが7個で、禁止されたプレースホルダがない
- テンプレート3種と `/task` skill が存在する
- `runindex/`、既存 `experiments/`、`transfer/`、`data/splits/`、`tools/harvest_runindex.py` に変更がない
