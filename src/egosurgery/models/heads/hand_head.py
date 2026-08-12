"""手 (hand) 検出ヘッド: own/other × L/R = 4 クラスの bbox 分類。

S2 で術具検出 (15 cls) に追加する hand 4 クラス検出のための小型ヘッド。
構造は tool head とパラメータを共有せず、独立した bbox + class branch
として実装する（§14 catastrophic forgetting 教訓: tool head を再利用
すると tool 性能が崩壊するため）。

実装上は MMDetTrainer の 19-class fine-tune（tool 15 + hand 4）と
共存する補助ヘッドとしての位置付け。MMDetTrainer 経路では mmdet 標準の
bbox_head が 19 クラスを直接出力するため、本ヘッドは

- 単体テスト時の forward 確認
- 将来 hand 専用の独立 head に切り替える際の足がかり

として用意する（v2 prompts_n/phase2_part4_s2_s3_v2.md §1.5）。

使い方:
    head = HandHead(input_dim=256, num_classes=4)
    logits = head(roi_feat)   # (N, 256) -> (N, 4) のクラス logits
"""

from __future__ import annotations

from torch import nn

# v2 仕様: own_L, own_R, other_L, other_R の 4 クラス。
HAND_CLASS_NAMES: tuple[str, ...] = (
    "Own_Left", "Own_Right", "Other_Left", "Other_Right",
)


class HandHead(nn.Module):
    """own/other × L/R の 4 クラス分類ヘッド（小型 MLP）。

    入力は RoI 特徴 (N, input_dim) を想定。出力は 4 クラス logits (N, 4)。
    bbox 回帰は MMDetTrainer 側の標準 bbox_head が担うため、本ヘッドは
    分類のみを行う。
    """

    def __init__(
        self,
        input_dim: int = 256,
        hidden_dim: int = 128,
        num_classes: int = 4,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.input_dim = int(input_dim)
        self.hidden_dim = int(hidden_dim)
        self.num_classes = int(num_classes)
        self.dropout_p = float(dropout)

        self.classifier = nn.Sequential(
            nn.Linear(self.input_dim, self.hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(self.dropout_p),
            nn.Linear(self.hidden_dim, self.num_classes),
        )

    def forward(self, x):
        """RoI 特徴から 4 クラス logits を返す。

        Args:
            x: ``(N, input_dim)`` の RoI 特徴。

        Returns:
            ``(N, num_classes)`` のクラス logits。
        """
        return self.classifier(x)
