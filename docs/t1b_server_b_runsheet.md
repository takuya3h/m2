# T1b（MT4MTL-KD-style Phase→Det / §4.6）別サーバー実行 run sheet — server B 向け

**目的**: lecun（B1/B2a/T1a）と並行し、server B で T1b を走らせ Δ_detection を出す。実装・smoke は
lecun で検証済み（本 run sheet が指すスクリプト群）。

**T1b とは**: MT4MTL-KD-style の §4.6 双方向のうち **Phase→Det 半分**（①予測相互作用 L3）。凍結 S4
工程モデルの per-frame 事後分布（phase context, 9-d）を条件に Relation-DETR の C5 を **FiLM 注入**
し、**学習済み検出器 s0_01{6,7,8}（=S0-frozen）から warm-start** して fine-tune する。FiLM は
zero-init=恒等なので warm-start 直後は S0-frozen と一致。

## Δ の定義（清潔・外部値不要）
T1b トレーナーは **学習前（FiLM 恒等＝warm-start 検出器）の init mAP** を同一 eval で記録する。これが
その seed の **S0-frozen 分母そのもの**。よって:
- **Δ_detection(seed) = best_mAP − init_mAP**（同一 recipe・同一 seed）。
- **§4.6 注入効果の分離**: `--zero-ctx` 対照（phase context=0 で同スケジュール fine-tune）を別途走らせ、
  **注入の純効果 = Δ_injected − Δ_control**。これで「fine-tune 自体の効果」と「phase 注入の効果」を分ける。
- 3-seed 揃ったら **Δ_injected − Δ_control を paired-σ(対seed差) §10.1 判定**（|Δ|>paired-σ かつ同符号で有意）。

## STEP 0: 環境（`docs/reproduce_on_new_machine.md` 手順 0–1.5）
本体 `.venv` ＋ 検出器 `.venv-relation-detr`（`setup_env_relation_detr.sh`、nvcc 11.8）。

## STEP 1: 転送物（lecun→server B=bengio・**3チャネル**）

> [!IMPORTANT]
> `third_party/Relation-DETR` は**親リポで gitignore＋独自 .git のネスト clone**。よって T1b の
> 検出器改変は**親リポの git pull に含まれない**。**3 チャネル**で渡すこと:

**(A) 親リポ（scripts/ + docs/ + lock）= git pull**（lecun で commit/push 後）または rsync。
T1b に必要: `scripts/{extract_phase_context,train_t1b}.py` `scripts/run_t1b.sh`
`scripts/setup_env_relation_detr.sh` `requirements.relation_detr.lock.txt` `docs/t1b_server_b_runsheet.md`
`docs/reproduce_on_new_machine.md`。

**(B) third_party/Relation-DETR 改変 = rsync**（親 git に無い・必須）:
```bash
rsync -a third_party/Relation-DETR/models/detectors/relation_detr_phasefilm.py \
         third_party/Relation-DETR/models/detectors/relation_detr_c5neck.py \
         <bengio>:<repo>/third_party/Relation-DETR/models/detectors/
rsync -a third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py \
         third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py \
         <bengio>:<repo>/third_party/Relation-DETR/configs/relation_detr/
rsync -a third_party/Relation-DETR/optimizer/param_dict.py \
         <bengio>:<repo>/third_party/Relation-DETR/optimizer/param_dict.py
```
（bengio 側は upstream Relation-DETR を clone 済みの上に上書き。base `relation_detr.py` 等は upstream のまま。）

**(C) データ・重み = rsync**:
| 資産 | パス | 用途 |
|---|---|---|
| **学習済み検出器 ×3** | `third_party/Relation-DETR/checkpoints/incoming/seed{42,123,456}/best_ap.pth`（各195MB） | warm-start init・教師・分母（s0_016/017/018） |
| **phase context cache** | `data/processed/phase_context/relation_detr_seed42/{train,val,test}_phasectx.npz` | FiLM 条件入力（または bengio で再生成: STEP 2、要 S4 ckpt） |
| 検出 annotations | `data/annotations/egosurgery_tool/instances_{train,val}.json` | 検出学習 |
| 画像 | `data/raw/ego/`（rsync -aL, 1.2GB） | 検出学習 |
| S4 ckpt（cache 再生成時のみ） | `experiments/phase1/s4_phase_baseline_001*/checkpoints/best_tecno.pth` | phase context 再生成用 |

## STEP 2: phase context（cache を転送しない場合のみ再生成）
```bash
.venv/bin/python scripts/extract_phase_context.py --subset train   # val/test も
```

## STEP 3: 学習（.venv-relation-detr・GPU 長時間 background+Monitor）
```bash
source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda-11.8
python scripts/train_t1b.py --smoke          # warm-start init mAP が ~0.7+ を確認（FiLM恒等）
# 注入本体（3-seed）と §4.6 対照（zero-ctx）
bash scripts/run_t1b.sh 42 0                  #   注入
bash scripts/run_t1b.sh 42 1 --zero-ctx       #   対照
bash scripts/run_t1b.sh 123 0 ; bash scripts/run_t1b.sh 123 1 --zero-ctx
bash scripts/run_t1b.sh 456 0 ; bash scripts/run_t1b.sh 456 1 --zero-ctx
```
- 既定 `--trainable all`（検出器＋FiLM の warm-start fine-tune, 6 epoch）。per-step は検出学習相当
  （~2h/epoch 単独・co-run でより遅い）→ **warm-start の利得は epoch 削減**（収束済みから 2-3ep で足りる
  見込み。`--epochs 3` で短縮可）。最速・最純粋なら `--trainable film`（FiLM のみ学習・検出器凍結）。
- 出力 `/tmp/t1b_*/t1b_result.json`（init_mAP, mAP, per_class）。

## STEP 4: Δ_detection 集計
各 run の `init_mAP`/`mAP` から Δ=best−init を seed 別に出し、注入 vs 対照の差を paired-σ 判定。
**早期打ち切り（§4.6）**: Δ_injected ≤ 0 が続くなら gradient 制御（`--trainable film` / lr 見直し）。

## 研究インテグリティ
metrics 捏造禁止（未収束・未達は実測と理由を正直に）。FiLM zero-init 恒等＝warm-start で S0-frozen 厳密保存
（init mAP がそれを保証）。サーバー差は同一 ckpt・同一前処理ゆえ学習数値のみ（§8.0 明記）。

## lecun 側準備（ユーザー承認後）
commit/push（新規: `relation_detr_phasefilm.py` / config / `train_t1b.py` / `run_t1b.sh` /
`extract_phase_context.py` / 本 run sheet、改修: `param_dict.py` finetune_t1b）＋ ckpt×3・画像・cache の rsync。
