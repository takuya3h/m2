# T1a（region-token→工程）別サーバー実行 run sheet — server B の Claude Code 向け

**目的**: lecun の B1/B2a と**並行**して T1a を別サーバー(server B)で走らせ、火曜 MTG までに
Δ_phase を出す。T1a のコードは lecun 側で実装・疎通検証済み（本 run sheet が指すスクリプト群）。

**T1a とは**: Tier-1 主力⭐「TAPIS/GraSP 型 region-token→工程」（②系統・Δ_phase）。凍結
Relation-DETR seed42 のデコーダ object-query 埋め込み（region token, クラス別 256-d, score 加重 →
15×256=3840-d）を GAP(2048) に連結 → 素 causal TeCNO（in_dim=5888）。分母は S4 base（素 TeCNO on
GAP）。**変える軸は region-token を見せるか否かの 1 点**。

---

## STEP 0: 環境再構築（`docs/reproduce_on_new_machine.md` 手順 0–2）
1. 前提（nvcc 11.8 / driver / uv / GPU）を確認。
2. 本体 venv: `bash scripts/setup_env.sh`（pytest 99 collected、既知 fail 1 件 `test_mmdet_trainer_eval_recipe_in_metrics` は赤のまま正常）。
3. 検出器 venv: `CUDA_HOME=/usr/local/cuda-11.8 bash scripts/setup_env_relation_detr.sh`。

## STEP 1: 凍結資産・データ配置（手順 4・**最重要**）
比較の三角形は**同一凍結源**が絶対条件。lecun から転送する（再学習禁止）:
- 凍結 ckpt: `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`（195MB）
- 画像: `rsync -aL`（symlink を辿り実体コピー）で `data/raw/ego/`（1.2GB, 15437 frames）
- manifest: `data/processed/phase_manifest/`（1.7MB）
- annotations は git clone で入る（不足あれば転送）。GAP cache は T1a では不要。
- 配置後、手順 4 の整合スニペット（image_path 解決 + ckpt 存在）を必ず実行。

## STEP 2: region-token 抽出（検出器 venv）
```bash
source .venv-relation-detr/bin/activate
export CUDA_HOME=/usr/local/cuda-11.8
CUDA_VISIBLE_DEVICES=0 python scripts/extract_t1a_regiontoken.py --subset val --limit 8   # スモーク
#   → "saved 8 x 3840 ... nonzero frac=1.000" が出れば hook 配線 OK
for sub in train val test; do
  CUDA_VISIBLE_DEVICES=0 python scripts/extract_t1a_regiontoken.py --subset "$sub" --limit 0
done
deactivate
```
出力: `data/processed/t1a_regiontoken/relation_detr_seed42/{train,val,test}_regiontoken.npz`。
（任意の健全性確認: region を (N,15,256) に整形し per-class norm 最大が、その frame に実在する器具クラスと一致するか。）

## STEP 3: 3-seed 学習（本体 venv・GPU 長時間は background+Monitor）
```bash
.venv/bin/python scripts/train_t1a.py --smoke        # 疎通（train+val 全件 region が必要）
bash scripts/run_t1a.sh 42 0
bash scripts/run_t1a.sh 123 0
bash scripts/run_t1a.sh 456 0
```
証跡: `experiments/transfer/t1a_regiontoken_*/metrics.json`（phase_accuracy / macro_f1 等）。

## STEP 4: Δ_phase 算出（分母 = lecun S4 base・§8.0 明文化）
**分母 S4 base（素 TeCNO on GAP・neck 無）の lecun 実測 per-seed 値**（これを流用し、サーバー差を §8.0 明記）:

| seed | S4 base acc | S4 base macro_f1 |
|---|---|---|
| 42 | 0.9023 | （metrics.json 参照） |
| 123 | 0.8977 | |
| 456 | 0.8957 | |
| 平均 | 0.8986±0.0034 | 0.7086±0.0192 |

paired-σ（対 seed 差）判定: 各 seed で ΔL2 = T1a_seed − S4base_seed、
**|mean Δ| > paired-σ(=対 seed 差の標本 std) かつ全 seed 同符号**なら有意（§10.1）。
参考: 同型の **B2a(信号スカラ)は Δ_phase(acc)=+0.0383 有意**。T1a(256-d 埋め込み)がこれを上回るかで
「presence か object 特徴か」を分離できる。

## 研究インテグリティ（厳守）
- **metrics/mAP を捏造しない**。未収束・環境制約は実測値と理由をそのまま報告。
- サーバー差（GPU/cuDNN 数値）は §8.0 として notes.md・experiment_log に明文化（同一 ckpt・同一前処理ゆえ差は TeCNO 学習数値のみ）。
- 走行中の学習を kill しない。長時間 GPU は background + Monitor。

---

## lecun 側で必要な準備（**ユーザー承認後**に実施）
T1a コードは現在 lecun の作業ツリーにあり**未コミット**。server B が `git pull` で取得するには:
1. `git add` → commit（新規: `requirements.relation_detr.lock.txt` / `scripts/setup_env_relation_detr.sh` /
   `scripts/extract_t1a_regiontoken.py` / `scripts/train_t1a.py` / `scripts/run_t1a.sh` /
   `docs/t1a_server_b_runsheet.md`、更新: `docs/reproduce_on_new_machine.md` / `docs/experiment_log.md`）→ push。
2. ckpt・画像・manifest を rsync（STEP 1）。
→ いずれも commit/push/転送は規約上ユーザー承認が必要。
