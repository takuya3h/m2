#!/usr/bin/env python3
"""クラス体系の取り違え事故を防ぐ assert ヘルパ。

`tool_seg_noskewer` が名称に反し Skewer を含む 31 クラスであるように、
このバンドルは「名前と中身が一致しない」ファイルを複数含む。
Phase C で読むすべての annotation ファイルは、使う前にこの assert を通すこと。
"""
from __future__ import annotations

import json


def assert_class_system(coco_path, expected_n, expected_names=None):
    """COCO JSON のクラス数 (と任意でクラス名集合) を検証し、カテゴリ名リストを返す。"""
    with open(coco_path) as f:
        d = json.load(f)
    names = [c["name"] for c in d["categories"]]
    assert len(names) == expected_n, (
        f"class count mismatch: {coco_path} has {len(names)}, expected {expected_n}: {names}")
    if expected_names is not None:
        assert set(names) == set(expected_names), (
            f"class name mismatch: {coco_path}\n  got={sorted(names)}\n  want={sorted(expected_names)}")
    return names


# 実測済みの正解値 (T3 で確認済み)。Phase C ではこれを使って読み込み時に検証する。
KNOWN_SYSTEMS = {
    # 既存実験の凍結源 (by_split 15cls) = 14cls + Mouth Gag
    "by_split_15cls": [
        "Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Mouth Gag",
        "Needle Holders", "Raspatory", "Retractor", "Scalpel", "Scissors", "Skewer",
        "Suction Cannula", "Syringe", "Tweezers",
    ],
    # 論文値に対応する 14cls (Mouth Gag を持たない)
    "cleaned_14cls": [
        "Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Needle Holders",
        "Raspatory", "Retractor", "Scalpel", "Scissors", "Skewer", "Suction Cannula",
        "Syringe", "Tweezers",
    ],
    # もう一つの 15cls = 14cls + Kidney Dish (by_split_15cls とは別物なので混同しないこと)
    "withkidney_15cls": [
        "Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Kidney Dish",
        "Needle Holders", "Raspatory", "Retractor", "Scalpel", "Scissors", "Skewer",
        "Suction Cannula", "Syringe", "Tweezers",
    ],
    "handtool_5cls": [
        "First Person's Left Hand", "First Person's Right Hand", "Left Hand Tool",
        "Right Hand Tool", "Two Hands Tool",
    ],
    "hand_4cls": [
        "Own hands left", "Own hands right", "Other hands left", "Other hands right",
    ],
}


def assert_known_system(coco_path, system_key):
    """KNOWN_SYSTEMS のいずれかに一致することを検証する。"""
    names = KNOWN_SYSTEMS[system_key]
    return assert_class_system(coco_path, len(names), names)
