# フェーズ II — Part 2/5: Backbone + 検出ヘッド + 損失関数

> **v2 追補（2026/05/24）を統合済み**
> - Mask DINO ヘッドの test_cfg を locked-down 値に対応させる口を用意（§15.3 G1）
>
> **v2.1 追補（2026/05/25 §13.2・§9 #6 反映）**
> - 【追加】Co-DETR 検出ヘッドを実装対象に追加（§13.2 S0「Mask DINO・VarifocalNet・Co-DETR を準備」、§9 #6 判断ポイント「Mask DINO vs Co-DETR を APr で比較」のため必須）
> - Co-DETR は長尾対照（long-tail 耐性の比較対象）として位置づける
>
> **v2.2 追補（2026/05/25 §8.0 DDP 運用条件・§13.2 (b)(iv) 反映）**
> - 【追加】各モデル（backbone・検出ヘッド）が BatchNorm を含むか LayerNorm 主体かを明示。DDP 2 GPU 実行時の `SyncBatchNorm` 選択的適用（§13.2 (b)(iv)）の判断材料とする

前提: Part 1（データパイプライン v2）が完了し、EgoSurgery データパイプライン（datasets/, transforms, Copy-Paste, RFS）が動作する状態。

Part 2 では **DINOv2 backbone** と **検出ヘッド (Mask DINO / VarifocalNet / Co-DETR)** と **長尾対策の損失関数** を実装する。

> **既存 S0 実験との関係（重要）**: 現在 Part 3 で VarifocalNet / Mask DINO の S0 学習（VFNet ≥ 45.8 を目指す）が進行中の場合、**それをやり直す必要はない**。S0 の完了判定は「VarifocalNet が公式 SOTA 45.8 を上回る」ことのみであり、Co-DETR はこの判定とは独立した**追加実験枠**である。Co-DETR は既存の `s0_001`〜`s0_006` の後に `s0_007`〜`s0_009`（3 seeds）として差し込めばよく、§9 #6 の「Mask DINO vs Co-DETR の APr 比較」はこの追加実験が揃った時点で実施する。既存 S0 実験は破棄しないこと。

> **監査で判明した現状（2026/05/25 ddp_migration_audit）**
> - `src/egosurgery/models/heads/mask_dino_head.py` と `vfnet_head.py` は
>   **既に実装済み**（単一 GPU で S0 学習が回っていた実績がある）。本プロンプトでは
>   これらを作り直さず、SyncBatchNorm 方針（§4.5）の確認に留める。
> - **`src/egosurgery/models/heads/codetr_head.py` はファイルとして存在するが
>   中身が未実装**（空ファイルまたはスケルトン）。本プロンプトの主作業は
>   **この既存ファイルへの Co-DETR 実装の書き込み**である。`create_file` は
>   ファイル既存で失敗するため、`codetr_head.py` への実装は `str_replace` または
>   `bash` での上書き（`cat > path << 'EOF'`）で行うこと。まず `view` で
>   現在の中身を確認し、空かスケルトンかを判定してから書き込む。
> - `DINOv2Backbone`・`ViTAdapter`・`SeesawLoss`・`LogitAdjustment`・`build.py` は
>   既存の可能性が高い。各ファイルを `view` で確認し、Co-DETR 分岐の追加など
>   **差分のみ**を当てる。既存の動作する実装は作り直さない。

---

## 0. 外部手法の取り込み方式

| 手法 | 方式 | 詳細 |
|------|------|------|
| DINOv2 ViT-L/14-with-registers | C（pip: torch.hub） | `torch.hub.load('facebookresearch/dinov2', 'dinov2_vitl14_reg')` |
| ViT-Adapter | B（抽出して src/ に統合） | DINOv2 の multi-scale 出力を生成 |
| Mask DINO | D（fork + `third_party/`） | `pip install -e third_party/MaskDINO` |
| VarifocalNet | C（pip: mmdet） | `mmdet.models.VFNet` |
| Co-DETR | C（pip: mmdet） | `mmdet` の `CoDETR` 実装（projects/CO-DETR）。長尾対照 |
| Seesaw Loss | B（抽出して src/ に統合） | mmdet 実装から必要部分を抽出 |

方式 B で抽出する際は、ファイル冒頭に以下を必ず記載:
```python
# =============================================================================
# Adapted from: {公式リポジトリ URL}
# Original authors: {著者名}
# License: {ライセンス}
# Modifications: {変更内容の要約}
# =============================================================================
```

---

## 1. DINOv2 Backbone

### `src/egosurgery/models/backbones/dinov2_registry.py`

```python
class DINOv2Backbone(nn.Module):
    """
    DINOv2 ViT-L/14-with-registers backbone（§4.2）。
    - register token 4 個で high-norm artifact patch を除去
    - 形状類似ペア（Forceps/Tweezers/Needle Holders）の識別を改善
    - 出力: 4 段階の特徴マップ + cls_token

    Fine-tuning 戦略:
    - 全層凍結 → LoRA（rank=8, alpha=16）で Q/V のみ適応
    - DoRA（magnitude + direction 分解）で強化
    - heavy full fine-tuning は回避（F1 サーベイ: tail-class 悪化リスク）
    """
    def __init__(self, model_name="dinov2_vitl14_reg", frozen=True, lora_rank=8, lora_alpha=16):
        super().__init__()
        self.model = torch.hub.load('facebookresearch/dinov2', model_name)
        if frozen:
            for param in self.model.parameters():
                param.requires_grad = False
        # LoRA は peft で適用（DoRA 対応）

    def forward(self, x):
        """
        Returns:
            features: List[Tensor] - 4段階の特徴マップ（stride 4/8/16/32）
            cls_token: Tensor - [B, D] のクラストークン
        """
        pass
```

### `src/egosurgery/models/backbones/vit_adapter.py`

```python
class ViTAdapter(nn.Module):
    """
    ViT-Adapter: DINOv2 ViT の single-scale 出力を multi-scale FPN 出力に変換。
    stride 4/8/16/32 の 4 段階特徴を生成し、Mask DINO / VarifocalNet に供給する。
    """
    pass
```

---

## 2. 検出ヘッド

### `src/egosurgery/models/heads/mask_dino_head.py`

```python
class MaskDINOHead(nn.Module):
    """
    Mask DINO 検出ヘッド（§4.2）。
    - Detectron2 ベースの Mask DINO を EgoSurgery-Tool 用にラップ
    - bbox-only モード（Phase-0）と bbox+mask モード（Phase-1）を config で切替
    - class-balanced denoising sampling（提案手法）を追加可能

    【v2 追補】test_cfg を locked-down 値に対応させる:
    - build_d2_config(cfg) で TEST.DETECTIONS_PER_IMAGE = 300（= max_per_img）を設定可能にする
    - score threshold を外部から注入可能な引数を持たせる
    - 実際の値の適用は Part 3 の MMDetTrainer._build_mmdet_cfg で行う
    """
    def __init__(self, cfg):
        super().__init__()
        self.d2_config = self.build_d2_config(cfg)

    def build_d2_config(self, cfg, test_detections_per_img=300, test_score_thr=1e-8):
        """
        Detectron2 config を構築する。
        test_detections_per_img と test_score_thr を外部から指定可能にする（§15.3 G1）。
        """
        pass

    def forward(self, features):
        pass
```

### `src/egosurgery/models/heads/vfnet_head.py`

```python
class VFNetHead(nn.Module):
    """
    VarifocalNet 検出ヘッド（§4.2, B2 サーベイ）。
    - mmdet の VFNet 実装をラップ
    - EgoSurgery-Tool 実質 SOTA（mAP 45.8）の再現が S0 の最低達成ライン
    - S0 で Mask DINO との比較基準として必ず並走させる
    """
    pass
```

### `src/egosurgery/models/heads/codetr_head.py`

> **実装方法の注記（監査結果）**: このファイルは**既に存在する**が中身が未実装
> （空またはスケルトン）。`create_file` はファイル既存で失敗するため、まず `view` で
> 現在の中身を確認し、`str_replace`（スケルトンがある場合）または
> `bash` の `cat > src/egosurgery/models/heads/codetr_head.py << 'EOF' ... EOF`
> （空ファイルの場合）で以下の実装を書き込むこと。

```python
# =============================================================================
# Adapted from: https://github.com/open-mmlab/mmdetection (projects/CO-DETR)
# Original authors: Zong et al. (ICCV 2023, "DETRs with Collaborative Hybrid Assignments Training")
# License: Apache 2.0
# Modifications: EgoSurgery-Tool 用にクラス数・入力次元を調整、
#                DINOv2 ViT-L/14 + ViT-Adapter backbone への接続
# =============================================================================

class CoDETRHead(nn.Module):
    """
    Co-DETR 検出ヘッド（§4.2, §13.2 S0, §9 #6）。

    位置づけ:
    - 長尾対照（long-tail 耐性の比較対象）。
    - Co-DETR は collaborative hybrid assignment（one-to-many 補助ヘッド併用）により、
      DETR 系の Hungarian one-to-one matching が稀少クラスの query を早期 quench
      する構造的バイアスを緩和する設計（§4.2）。
    - §9 #6 の判断ポイント: S0 完了時に Mask DINO vs Co-DETR を APr（稀少クラス AP）
      で比較し、3pt 以上の差が出れば S1 以降を Co-DETR ベースに切り替える。

    実装方針:
    - mmdet の projects/CO-DETR の CoDETR をラップする（方式 C）。
    - backbone は Mask DINO / VFNet と同一の DINOv2 ViT-L/14-with-registers + ViT-Adapter
      を使い、検出ヘッドのみを差し替える（Δ 基準点の公平性のため backbone を揃える）。
    - test_cfg は Part 3 の MMDetTrainer._build_mmdet_cfg が locked-down 値で
      強制上書きする（§15.3 G1）。CoDETRHead 側はその値を受け取れる口を持つ。
    """
    pass
```

---

## 補足: Co-DETR の S0 への組み込み（§13.2・§9 #6）

Co-DETR は S0 の**完了判定（VFNet ≥ 45.8）には関与しない**。S0 完了判定は VarifocalNet が
公式 SOTA を上回ることのみで定義される。Co-DETR は次の目的のための追加実験である。

- §13.2 S0 の「Mask DINO・VarifocalNet・**Co-DETR** を準備し並走」の充足。
- §9 #6 の判断ポイント「Mask DINO vs Co-DETR を APr で比較し 3pt 以上差があれば
  S1 以降を Co-DETR ベースに切替」の実行。

したがって、既存の S0 実験（`s0_001`〜`s0_006` = Mask DINO ×3 + VFNet ×3）が
進行中・完了済みであっても**やり直す必要はない**。Co-DETR は `s0_007`〜`s0_009`
（3 seeds）として後から追加すればよい。Part 3 の `run_s0.sh` にこの 3 実験を
追記する（Part 3 v2.1 参照）。

---

## 3. 損失関数

### `src/egosurgery/models/losses/seesaw.py`

```python
# =============================================================================
# Adapted from: https://github.com/open-mmlab/mmdetection
# Original authors: OpenMMLab
# License: Apache 2.0
# Modifications: EgoSurgery-Tool 用にクラス数・パラメータを調整
# =============================================================================

class SeesawLoss(nn.Module):
    """
    Seesaw Loss（§3.3, F1 サーベイ）。
    p=0.8, q=2.0 で稀少クラスの勾配を相対的に強化。
    """
    def __init__(self, num_classes=15, p=0.8, q=2.0):
        pass
```

### `src/egosurgery/models/losses/logit_adjustment.py`

```python
class LogitAdjustment(nn.Module):
    """
    Post-hoc Logit Adjustment（§3.3, F1 サーベイ）。
    全分類ヘッドに適用、実装 1 行・コスト無し。
    クラス頻度の対数を logit にバイアスとして加算。
    """
    def __init__(self, class_frequencies, tau=1.0):
        pass
```

---

## 4. モデルビルダー

### `src/egosurgery/models/build.py`

```python
def build_model(cfg):
    """
    config に基づいてモデル全体を組み立てる。

    S0 の場合:
    - backbone: DINOv2 ViT-L/14-with-registers + ViT-Adapter
    - head: MaskDINOHead / VFNetHead / CoDETRHead（config の model.head.name で切替）
    - loss: SeesawLoss + LogitAdjustment

    Returns:
        model: nn.Module
    """
    pass
```

---

## 4.5 DDP / SyncBatchNorm に関するモデル側の注記（§13.2 (b)(iv)）

S0 を bengio の DDP 2 GPU で実行する（§14）にあたり、Part 3 の `MMDetTrainer._build_model()`
が `SyncBatchNorm` を**選択的に**適用する。`SyncBatchNorm` は BatchNorm を持つモデルに
のみ意味があり、LayerNorm 主体のモデルには不要（変換しても無害だが意図を明確にする）。
本 Part で実装する各コンポーネントの正規化層の種別を以下に明示する。

- **DINOv2 ViT-L/14-with-registers backbone**: LayerNorm 主体。BatchNorm を持たない。
  → `SyncBatchNorm` 変換の対象外。
- **ViT-Adapter**: 実装によっては spatial prior module 等に BatchNorm を含みうる。
  → BatchNorm を含む場合は `SyncBatchNorm` 変換の対象。実装時にどちらかを明記すること。
- **Mask DINO ヘッド**: Transformer decoder 主体で LayerNorm 中心。pixel decoder の
  一部に GroupNorm / BatchNorm を含む実装がある。→ BatchNorm を含む場合のみ対象。
- **VFNet ヘッド**: 畳み込みベースで GroupNorm を使う構成が一般的。BatchNorm を使う
  構成の場合は対象。
- **Co-DETR ヘッド**: DETR 系で LayerNorm 主体。補助 ATSS ヘッドが畳み込み +
  BatchNorm を含む場合は対象。

実装方針として、各モデルの `build_*` 関数または README に「BatchNorm を含むか否か」を
1 行コメントで明記すること。`MMDetTrainer._build_model()` は
`any(isinstance(m, nn.BatchNorm*) for m in model.modules())` で実際に判定して
`SyncBatchNorm` 変換の要否を決めるため、モデル側で特別な対応コードは不要だが、
**学習を凍結している層（frozen backbone）の BatchNorm は統計更新されない**点に注意する。
DINOv2 backbone を frozen で使う S0 では、backbone 内に BatchNorm があっても
統計が動かないため SyncBatchNorm 化の影響はない。

---

## 5. Hydra config（モデル関連）

### `configs/model/mask_dino.yaml`

```yaml
model:
  name: mask_dino
  backbone:
    name: dinov2_vitl14_reg
    frozen: true
    lora:
      enabled: true
      rank: 8
      alpha: 16
      target_modules: ["q_proj", "v_proj"]
      use_dora: true
  head:
    name: mask_dino
    num_classes: 15
    bbox_only: true  # Phase-0: mask 不要
    denoising:
      enabled: true
      class_balanced: true  # 提案手法: class-balanced denoising sampling
  loss:
    seesaw:
      enabled: true
      p: 0.8
      q: 2.0
    logit_adjustment:
      enabled: true
      tau: 1.0
```

### `configs/model/vfnet.yaml`

```yaml
model:
  name: vfnet
  backbone:
    name: dinov2_vitl14_reg
    frozen: true
    lora:
      enabled: true
      rank: 8
      alpha: 16
  head:
    name: vfnet
    num_classes: 15
  loss:
    seesaw:
      enabled: true
      p: 0.8
      q: 2.0
    logit_adjustment:
      enabled: true
      tau: 1.0
```

### `configs/model/codetr.yaml`

```yaml
model:
  name: codetr
  backbone:
    name: dinov2_vitl14_reg   # Mask DINO / VFNet と同一 backbone（Δ 公平性）
    frozen: true
    lora:
      enabled: true
      rank: 8
      alpha: 16
      target_modules: ["q_proj", "v_proj"]
      use_dora: true
  head:
    name: codetr
    num_classes: 15
    bbox_only: true  # Phase-0: mask 不要
    # Co-DETR の collaborative hybrid assignment（one-to-many 補助ヘッド）
    aux_heads:
      enabled: true   # 長尾 query quench 緩和の核
  loss:
    seesaw:
      enabled: true
      p: 0.8
      q: 2.0
    logit_adjustment:
      enabled: true
      tau: 1.0
```

---

## 6. テスト

`tests/test_models.py` に以下を実装:

1. `test_dinov2_backbone_forward`: ダミー画像 (B=2, 3, 518, 518) で forward し、features が 4 段階 + cls_token が返ること
2. `test_dinov2_with_lora`: LoRA 適用後も forward が通り、学習可能パラメータ数が全体の ~1% であること
3. `test_vit_adapter_output_shapes`: ViT-Adapter が stride 4/8/16/32 の 4 段階特徴を返すこと
4. `test_build_model_s0`: S0 config で `build_model(cfg)` が backbone + detection_head を含むモデルを返すこと
5. `test_seesaw_loss_gradient`: Seesaw Loss が正しい shape の勾配を返すこと
6. `test_logit_adjustment`: Logit Adjustment が頻度に応じて logit を調整すること
7. `test_build_model_codetr`: `configs/model/codetr.yaml` で `build_model(cfg)` が CoDETRHead を含むモデルを返すこと

Mask DINO / VarifocalNet / Co-DETR のテストは Detectron2 / mmdet 未インストール環境では `pytest.mark.skipif` でスキップ。
DINOv2 のテストもネットワーク未接続環境ではスキップ。

---

## 7. 完了判定

1. `from egosurgery.models.backbones.dinov2_registry import DINOv2Backbone` がエラーなく通る
2. `from egosurgery.models.build import build_model` がエラーなく通る
3. `pytest tests/test_models.py -v` が全テストパス（スキップは許容）
4. DINOv2 backbone が (2, 3, 518, 518) の入力で正しい shape の特徴マップを返す
5. Seesaw Loss / Logit Adjustment が正しく動作する
6. **Mask DINO ヘッドの `build_d2_config` が test_detections_per_img / test_score_thr を受け取れる**（§15.3 G1）
7. `from egosurgery.models.heads.codetr_head import CoDETRHead` がエラーなく通り、`configs/model/codetr.yaml` で `build_model` がモデルを返す（§13.2 S0・§9 #6）

---

## 8. この Part で触らないファイル

- `src/egosurgery/engines/` 配下 → Part 3
- `src/egosurgery/metrics/` 配下 → Part 3
- `scripts/run_s0.sh` → Part 3
- `src/egosurgery/models/heads/phase_head.py` → Part 4
- `src/egosurgery/models/temporal/` 配下 → Part 5
- `src/egosurgery/models/feedback/` 配下 → フェーズ III
- `src/egosurgery/models/relation/` 配下 → フェーズ IV
- `src/egosurgery/models/exo/` 配下 → フェーズ IV
