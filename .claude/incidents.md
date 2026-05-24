# egosurgery_multitask — Incident Log

過去セッションで発生し、コストを払って解決した失敗の記録。
新規セッションは **コード変更前に全項目を読む**（`.claude/skills/avoid-past-failures/SKILL.md`）。
「Prohibited going forward」は今後のセッションが必ず守るルール。

---

### Incident 1 — `pyproject.toml` 空 + `.venv` 欠落で CUDA/torch ロスト (2026-05-22)

- What was tried:
  別サーバー or 再クローン直後に `python` を直接呼んで学習スクリプトを起動した。
- What broke:
  `torch.cuda.is_available() == False`、`mmcv` import 失敗。GPU/driver
  （NVIDIA 535.288.01、A6000）自体は健全だった。
- Root cause:
  `pyproject.toml` が空のまま push されており、`.venv/` も .gitignore で
  リポジトリ外。新環境では torch 自体が未インストール、import path も未通電。
- Fix / mitigation:
  Method A（再現スイート）として `requirements.lock.txt`（100 pkg pin）、
  `scripts/setup_env.sh`（2-stage：torch 2.1.2+cu118 → mmcv/mmdet/mamba-ssm）、
  `docs/environment.md` / `docs/reproduce_on_new_machine.md` を整備。
- Prohibited going forward:
  - **`pyproject.toml` を空にしない**。依存はここと `requirements.lock.txt` を
    必ず同期。
  - **対話セッションで `python` を素で呼ばない**。`source .venv/bin/activate`
    か `.venv/bin/python` を明示する（pyenv global python では mmcv の C 拡張
    が ABI 不一致で落ちる）。
  - 環境壊滅疑いのときはまず `python -c "import torch; print(torch.version.cuda)"`
    と `.venv` の存在チェックを行う。GPU ドライバを疑うのは最後。

---

### Incident 2 — 検出ヘッド bias 初期化バグで mAP ≡ 0.0 (2026-05-22)

- What was tried:
  内蔵 `SimpleDetectionHead` で S0 を回した。
- What broke:
  6 実験全てで val mAP = 0.0、loss は下がるのに検出は完全失敗。
- Root cause:
  detection head の classification branch bias を 0 で初期化していた。
  RetinaNet 系 / focal loss 系は **prior bias ≈ -log((1-π)/π) (π≈0.01)** が
  必須。これがないと初期段階で全 anchor が背景 logit に支配され、
  positive サンプルが学習されない。座標変換側にも 392→1920px 逆スケール
  漏れがあり、評価器側で 0 になっていた。
- Fix / mitigation:
  bias を focal-loss 流の負バイアス初期化に変更。`StageATrainer._rescale_to_original`
  で予測を元解像度へ逆スケールしてから COCO 評価へ渡す経路に統一。pytest 23
  ケース通過を確認。
- Prohibited going forward:
  - **新規検出ヘッドの cls bias を 0 で出さない**。focal loss を使う限り
    `bias_init_with_prob(0.01)` 相当を必ず適用。
  - **モデル出力は `img_size` 正方空間 / 評価 GT は元解像度** という
    座標系ギャップを忘れない（CLAUDE.md「ハマりどころ」）。新規評価ループを
    書くたびに「逆スケール済みか？」を確認する。
  - mAP=0.0 を見たら loss curve を見る前に **prior bias と座標系** を疑う。

---

### Incident 3 — S2 (Tool+Hand 19 cls) で tool mAP が壊滅的忘却 (2026-05-23)

- What was tried:
  S0 best（Mask DINO 15 cls、tool mAP 0.327）から `load_from` で
  19 クラス（tool 15 + hand 4）の Mask DINO を 8 epoch fine-tune。
- What broke:
  hand mAP = 5.6%（目標 65%）、tool mAP が 0.327 → 0.003 に崩壊。
  判定 #2「hand>65 & Δ(S2-S0) tool ≤ 1pt」未達。
- Root cause:
  mmengine の `load_from` は形状不一致の重みを random init に置換する。
  Mask DINO の `bbox_head.cls_branches[0..6]` 全 14 層が 15→19 で
  サイズ不一致になり、tool の判別を担っていた cls head が全て再初期化。
  query embedding 側に残った tool 表現と、新規 hand 表現が 8 epoch では
  分離できず競合崩壊した。
- Fix / mitigation:
  honest に未達として `experiments/phase0/s2_001..003` に保存。
  リカバリ案として「COCO 重みから 19 cls を S0 と同等手順で学習」を提示
  （未実施）。
- Prohibited going forward:
  - **クラス数を増やして既存検出器を継続学習する設計を、何も検証せず採用しない**。
    `load_from` がどのキーを random init するかを **事前に dry-run で列挙**
    し、cls_branches が全部置換される設計は避けるか、epoch 数・LR を
    大幅に積むこと。
  - S0→S2 のように「タスクは増えるが基準点 mAP を維持」する要求がある
    遷移では、**load_from 経由ではなく COCO 重みから同等手順で再学習** を
    第一選択にする。

---

### Incident 4 — S3 Phase 認識で逆頻度 class weights が val_acc を 0.5% に崩壊 (2026-05-24)

- What was tried:
  `PhaseLoss(use_class_weights=True)` で `class_weights_from_frequencies`
  （単純な逆頻度）を有効化して S3 を学習。
- What broke:
  val_acc 0.5%（random 11% 未満）まで崩壊。3 seed 全滅。
- Root cause:
  EgoSurgery の `disinfection` / `irrigation` は train には登場するが
  val/test に **GT が存在しない**。逆頻度重みは非常に小さい train 出現
  クラスへ極大重み（数百倍）を割り当て、モデルがそれらに過適合した結果、
  val に出現する 7 クラスでの判別が崩壊した。
- Fix / mitigation:
  `use_class_weights: false` で均一重みに切替 → val_acc 49 → 59.6 ± 0.7%
  まで回復。失敗ランは `experiments/phase0/_failed_s3_weighted/` に証跡
  として保存（消さない）。
- Prohibited going forward:
  - **逆頻度系のクラス重みを「train 頻度のみ」から算出しない**。EgoSurgery
    のように val/test に欠落クラスがある場合、重み付けの根拠そのものが歪む。
    使うなら `sqrt(inverse freq)` + クリップ + val 出現クラスのみに正規化。
  - **長尾対策を入れたら最初に val_acc が random 以下に落ちていないかを
    確認**（無効化版より明確に良くなる根拠を出してから採用）。
  - 失敗 run は `experiments/.../_failed_*` ディレクトリへ残し、削除しない
    （研究 integrity 物理証拠、README §15）。

---

### Incident 5 — Tool-split のバグ + score_thr 過大で VFNet が公式 SOTA から 7pt 乖離 (2026-05-24)

- What was tried:
  `s0_004_varifocanet_seed42` の test 評価で公式 SOTA (mAP 45.8) を再現
  しようとした。
- What broke:
  val 27.8（−18pt）、test 38.8（−7pt）。判定 #4「VFNet mAP ≥ 45.8」未達。
- Root cause:
  独立調査の結果、二つの原因が重なっていた：
  1. `score_thr=0.05` を採用していた。公式評価は `score_thr ≈ 1e-8`
     （NMS 支配）。これだけで −2〜5pt。
  2. tool 用の自作 split が video 09 / 10 を欠落していた。
     公式 split との差で −1〜3pt。
- Fix / mitigation:
  公式 split を導入、`score_thr` を 1e-8 まで下げて NMS 支配構成に統一、
  full split で再評価。`docs/experiment_log.md` に未達を honest に明示。
- Prohibited going forward:
  - **公開ベンチを再現するときは split を自作しない**。論文・公式リポの
    split ファイルをそのまま読み込む。新規 split を作るときは
    `assert_paper_split()` 等の照合アサートを必ず通す（README §179 参照）。
  - **検出評価の `score_thr` は公式の値（VFNet は ≈ 1e-8）を使う**。
    可視化目的の 0.05 を評価パイプにそのまま流用しない。
  - 再現性ベンチで数 pt 乖離が出たら、まず **(a) split、(b) score_thr/NMS、
    (c) schedule (1x vs 2x/3x)、(d) multi-scale training** の 4 点を
    この順で疑う。

---

### Incident 6 — 数値ねつ造の誘惑（プロセス上のリスク） (継続)

- What was tried:
  CUDA 不可・データ未配置などの環境制約下で、デモ用にダミー数値で
  metrics を埋めたくなる場面が複数回発生。
- What broke:
  実害は出していない（CLAUDE.md ガード + ExperimentManager の証拠保存で
  抑止）。ただし「未達を未達として書く」ことに毎回明示的判断が要っている。
- Root cause:
  プロセス上の構造的リスク。LLM 側に「進捗を見せたい」バイアスが残る。
- Fix / mitigation:
  - 各実験ディレクトリに config.yaml / command.sh / git_commit.txt /
    metrics.json / per_class_ap.json / notes.md を残す体制
    （ExperimentManager が自動化）。
  - README §15・docs/experiment_log.md で「未達は未達」テンプレを徹底。
- Prohibited going forward:
  - **metrics / mAP / accuracy をダミー値で埋めない**。環境制約等で未達なら
    「未達」「環境制約により未取得」と明示する（CLAUDE.md 研究インテグリティ）。
  - 改善主張は §10.1 に従い `|Δ| > 1σ` のときのみ。seed 1 本で「改善」を
    主張しない。
  - S0〜S9 の Δ 基準点を比較する実験では **optimizer / seed / scheduler /
    augmentation / batch size を必ず揃える**。揃えていない比較は Δ として
    出さない。

---

### テンプレート（新規追加用）

```
### Incident N - Short title (YYYY-MM-DD)

- What was tried:
- What broke:
- Root cause:
- Fix / mitigation:
- Prohibited going forward:
```
