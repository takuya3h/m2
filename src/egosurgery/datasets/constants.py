"""EgoSurgery のクラス定義（単一情報源）。

術具 15 クラス・手 4 クラス・手術工程 9 クラスの ID と名称をここに集約する。
データセット / Copy-Paste / サンプラ / 前処理スクリプトはすべて本モジュールを
参照し、クラス定義の二重管理を避ける。

注意: ID・名称は EgoSurgery 公式データの仕様に合わせて調整すること。
本定義は実装指示書（phase2_part1）に基づく値であり、実データの
アノテーション仕様を確認のうえ必要に応じて更新する。
"""

from __future__ import annotations

# --- 術具 15 クラス（COCO category id 0..14） ----------------------------- #
# EgoSurgery-Tool 公式 COCO アノテーション
# (annotations/coco_format/bbox/by_split/tool/*.json) の categories に一致。
TOOL_CLASSES: list[dict] = [
    {"id": 0, "name": "Bipolar Forceps"},
    {"id": 1, "name": "Electric Cautery"},
    {"id": 2, "name": "Forceps"},
    {"id": 3, "name": "Gauze"},
    {"id": 4, "name": "Hook"},
    {"id": 5, "name": "Mouth Gag"},
    {"id": 6, "name": "Needle Holders"},
    {"id": 7, "name": "Raspatory"},
    {"id": 8, "name": "Retractor"},
    {"id": 9, "name": "Scalpel"},
    {"id": 10, "name": "Scissors"},
    {"id": 11, "name": "Skewer"},
    {"id": 12, "name": "Suction Cannula"},
    {"id": 13, "name": "Syringe"},
    {"id": 14, "name": "Tweezers"},
]

# --- 手 4 クラス（S2 以降で使用） ---------------------------------------- #
# EgoSurgery-Tool の hand アノテーションは別ファイルで category id 1..4 を持つ。
# tool（id 0..14）との衝突を避けるため、本プロジェクト内部では id 15..18 を割当。
HAND_CLASSES: list[dict] = [
    {"id": 15, "name": "Own hands left"},
    {"id": 16, "name": "Own hands right"},
    {"id": 17, "name": "Other hands left"},
    {"id": 18, "name": "Other hands right"},
]

# --- 手術工程 9 クラス（phase id 0..8、S3 以降で使用） -------------------- #
PHASE_CLASSES: list[dict] = [
    {"id": 0, "name": "Preparation"},
    {"id": 1, "name": "Draping"},
    {"id": 2, "name": "Incision"},
    {"id": 3, "name": "Dissection"},
    {"id": 4, "name": "Hemostasis"},
    {"id": 5, "name": "Irrigation"},
    {"id": 6, "name": "Closure"},
    {"id": 7, "name": "Dressing"},
    {"id": 8, "name": "Completion"},
]

NUM_TOOL_CLASSES = len(TOOL_CLASSES)   # 15
NUM_HAND_CLASSES = len(HAND_CLASSES)   # 4
NUM_PHASE_CLASSES = len(PHASE_CLASSES)  # 9

# 形状が似て混同しやすいクラス（confusion matrix / Compensation factor 対象）。
CONFUSABLE_CLASSES = ["Forceps", "Tweezers", "Needle Holders", "Bipolar Forceps"]

# 稀少クラス（Copy-Paste / RFS の優先対象）。研究計画 §7 の長尾分析に基づく。
RARE_CLASSES = ["Skewer", "Syringe", "Forceps"]


def _build_maps(classes: list[dict]) -> tuple[dict, dict]:
    """クラス定義リストから name->id / id->name の双方向マップを作る。"""
    name_to_id = {c["name"]: c["id"] for c in classes}
    id_to_name = {c["id"]: c["name"] for c in classes}
    return name_to_id, id_to_name


TOOL_NAME_TO_ID, TOOL_ID_TO_NAME = _build_maps(TOOL_CLASSES)
HAND_NAME_TO_ID, HAND_ID_TO_NAME = _build_maps(HAND_CLASSES)
PHASE_NAME_TO_ID, PHASE_ID_TO_NAME = _build_maps(PHASE_CLASSES)

# 術具 + 手をまとめた 19 クラスのマップ（include_hand=True で使用）。
ALL_NAME_TO_ID = {**TOOL_NAME_TO_ID, **HAND_NAME_TO_ID}
ALL_ID_TO_NAME = {**TOOL_ID_TO_NAME, **HAND_ID_TO_NAME}

# tool のみのカテゴリ ID 集合（include_hand=False のフィルタに使用）。
TOOL_CATEGORY_IDS = frozenset(TOOL_ID_TO_NAME)
HAND_CATEGORY_IDS = frozenset(HAND_ID_TO_NAME)


def coco_categories(include_hand: bool = False) -> list[dict]:
    """COCO JSON の ``categories`` フィールド用のリストを返す。

    Args:
        include_hand: ``True`` なら手 4 クラスも含めた 19 クラスを返す。

    Returns:
        ``[{"id": int, "name": str, "supercategory": str}, ...]``。
    """
    cats = [dict(c, supercategory="tool") for c in TOOL_CLASSES]
    if include_hand:
        cats += [dict(c, supercategory="hand") for c in HAND_CLASSES]
    return cats
