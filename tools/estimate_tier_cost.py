#!/usr/bin/env python3
"""Tier ごとの総量（run 本数 × 所要時間）を Stage 0 の実測から積む。

関門 G0 の三条件目「所要時間から Tier 1 が締切に収まるか判明」のための計算器である。
契約 `T-2026-09-17-tier1-cost-estimate`。

**所要時間は実測から引く。実測の無い run 型は代理であることを型に持たせる。**
`RunType.measured` が False の行は代理であり、`--unknown` で一覧に出る。
代理は利用者の承認済み（spec.yaml の `meta.amendments`）で、いずれも t1b の実測
（1 run 約 4 時間 / 6 epoch）に由来し、逆伝播の範囲が t1b より広いため **下界** である。

**並列の模型は実測に裏づけがある。** 「2 本並行で 1 epoch 36〜40 分、単独時は 37 分/epoch」
（`tasks/T-2026-08-29-lecun-detector-env-pd/RESULT.md:88`）は、装置を分けた 2 本が
単独と同じ速さで進むことを示す。したがって壁時計時間は GPU 時間を台数で割る。
ただし **1 本の run は装置をまたげない** ため、最長の 1 run を下限に置く。

run の列挙は M（マスター v1）の Tier 表の各項目に対応づけてある。対応の無い項目が
零件であることは `--check-coverage` が数える。**対応表から項目を消すと 1 件を返す。**

使い方:

    python tools/estimate_tier_cost.py                      # 既定（K=3, 装置 2, 24h/日）
    python tools/estimate_tier_cost.py --k 2 --devices 4 --hours-per-day 12
    python tools/estimate_tier_cost.py --section base       # 節を一つだけ出す
    python tools/estimate_tier_cost.py --control            # 対照（所要時間 ×2 / 装置 ×2）
    python tools/estimate_tier_cost.py --check-sources      # 出所の無い行を数える
    python tools/estimate_tier_cost.py --check-coverage     # 対応の無い M 項目を数える
    python tools/estimate_tier_cost.py --check-doc docs/stage0/B1_tier1_cost_estimate.md
    python tools/estimate_tier_cost.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# 文書に埋め込む生成物の境界。`--check-doc` はこの内側だけを突き合わせる。
BLOCK_BEGIN = "<!-- estimate:begin {key} -->"
BLOCK_END = "<!-- estimate:end {key} -->"
_BLOCK_RE = r"<!-- estimate:begin (?P<key>[a-z0-9_]+) -->\n(?P<body>.*?)\n<!-- estimate:end (?P=key) -->"


# --------------------------------------------------------------------------
# run 型と所要時間。**出所の無い行を置かない。**
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class RunType:
    key: str
    label: str
    hours: float
    source: str
    measured: bool
    note: str = ""


_H = 1.0
_S = 1.0 / 3600.0

RUN_TYPES: dict[str, RunType] = {
    rt.key: rt
    for rt in [
        RunType(
            key="phase_iface",
            label="工程側の界面 run（受け取り = 工程塔、50 epoch）",
            hours=30.0 * _S,
            source="docs/stage0/B_contract_b_results.md §3（11.9〜30.0 s、n=11。A6000 1 枚）",
            measured=True,
            note="実測の範囲の上端を採る。B4 の強い塔での同型 run 14.5〜32.2 s とも重なる",
        ),
        RunType(
            key="phase_tower_train",
            label="工程塔の学習（train 10 動画、3 epoch、1 seed）",
            hours=105.0 * _S,
            source="docs/stage0/B_pd_b2_b4_results.md §2.1（ImageNet-R50、105 秒）",
            measured=True,
            note="暫定塔の実測。Stage 1 の塔は epoch を増やす前提のため下界",
        ),
        RunType(
            key="phase_eval",
            label="工程側の評価のみ run",
            hours=30.0 * _S,
            source="docs/stage0/B_contract_b_results.md §3（学習込みの run 時間を上界に使う）",
            measured=False,
            note="評価だけを分離した計測が無い。学習込みの値を代理に置く（上界）",
        ),
        RunType(
            key="det_iface_w1",
            label="検出側の W1 界面 run（凍結検出器＋注入層のみ、6 epoch）",
            hours=4.0 * _H,
            source="tasks/T-2026-08-29-lecun-detector-env-pd/RESULT.md:88（1 run 約 4 時間）",
            measured=True,
            note="2 本並行で 1 epoch 36〜40 分、単独時 2.2 it/s = 37 分/epoch",
        ),
        RunType(
            key="det_iface_w2",
            label="検出側の W2 界面 run（末端ブロックまで学習）",
            hours=4.82 * _H,
            source="T-2026-09-17-frozen-feature-cache-timing（W2/W1 の 1 step 比 1.205 を同一バッチ n=20 で実測）"
            " × tasks/T-2026-08-29-lecun-detector-env-pd/RESULT.md:88（W1 の 1 run 約 4 時間）",
            measured=False,
            note="W2 の run は依然として repo 全体に一件も無い。**値は実測の比から導いた**"
            "（4.00 h × 1.205 = 4.82 h）が、W2 の run そのものを計時していないため代理のままとする",
        ),
        RunType(
            key="det_tower_train",
            label="検出塔の学習（COCO / ImageNet 初期化、12 epoch）",
            hours=8.35 * _H,
            source="T-2026-09-18-stage1-detector-towers（efros・A6000 2 枚・14 run の実測平均）",
            measured=True,
            note="14 run の Training time の平均（7.816〜9.225 h、中央 8.031 h）。"
            "**2 本同時に走らせた下での 1 run の壁時計**であり、14 x 8.35 / 2 枚 = 58.5 h が"
            "実際の経過 58.7 h（9/17 22:26 -> 9/20 09:09 UTC）と一致する。折りにより "
            "train の枚数が 9,657〜11,182 と違うため run ごとに幅がある",
        ),
        RunType(
            key="det_eval",
            label="検出側の評価のみ run",
            hours=40.0 / 60.0 * _H,
            source="tasks/T-2026-08-29-lecun-detector-env-pd/RESULT.md:88（1 epoch 36〜40 分を代理）",
            measured=False,
            note="評価だけを分離した計測が無い。学習 1 epoch 分を代理に置く（上界）",
        ),
        RunType(
            key="det_tower_w3",
            label="検出側の W3 界面 run（受け取り塔全体を学習）",
            hours=8.35 * _H,
            source="T-2026-09-18-stage1-detector-towers の検出塔学習の実測を代理に置く",
            measured=False,
            note="W3 の run は依然として一件も無い。塔全体を更新するためフル学習と同じ範囲に置く。"
            "**値は実測由来になったが W3 そのものは計時していないため代理のままとする**",
        ),
        RunType(
            key="probe",
            label="クリップ ID 識別プローブ",
            hours=30.0 * _S,
            source="docs/stage0/B_contract_b_results.md §3（工程側の界面 run を代理）",
            measured=False,
            note="プローブ単体の計時が無い。キャッシュ特徴上の線形当てはめのため同規模に置く",
        ),
    ]
}


# --------------------------------------------------------------------------
# M（マスター v1）の項目。**ここが対応表の分母である。**
# 出所は契約 SPEC の §2.2（Tier 表）・§2.3・M §4.3（対照）・M §4.4（参照入力段）。
# --------------------------------------------------------------------------
M_ITEMS: dict[str, str] = {
    # Tier 1（M §5.3 の表）
    "t1.denominator_and_identity": "Tier1: 分母と一致確認",
    "t1.ref_input_4stage": "Tier1: 参照入力 4 段",
    "t1.direction_4arm": "Tier1: 方向 4 腕",
    "t1.dp_w1": "Tier1: D→P の W1",
    "t1.dp_l1l2": "Tier1: D→P の L1/L2",
    "t1.dp_p21": "Tier1: D→P の P*-21",
    "t1.pd_w1": "Tier1: P→D の W1",
    "t1.pd_w2": "Tier1: P→D の W2",
    "t1.pd_dedicated_search": "Tier1: P→D の専用探索",
    "t1.pd_l3": "Tier1: P→D の L3",
    "t1.pd_both_detectors": "Tier1: P→D の両検出塔",
    "t1.controls": "Tier1: 対照",
    "t1.foldA_3seed": "Tier1: 折り A の 3 seed",
    # 対照（M §4.3。Tier 1 に含む）
    "c1.empty_iface": "対照: 空入力界面（分母）",
    "c2.no_iface_identity": "対照: 界面なしとの一致確認",
    "c3.random_input": "対照: 乱数入力",
    "c4.same_volume_unrelated": "対照: 同量非関連特徴（L3 で必須）",
    "c5.shuffle_time_video": "対照: 時間・動画間 shuffle",
    "c6.reverse_selection": "対照: 逆選別",
    "c7.clipid_probe": "対照: クリップ ID 識別プローブ",
    "c8.w1_vs_w2": "対照: 受け取り側 W1 vs W2",
    # 参照入力段（M §4.4）
    "s.empty": "参照入力段: 空",
    "s.pred": "参照入力段: 予測",
    "s.oracle": "参照入力段: 正解",
    "s.oracle_plus_pred": "参照入力段: 正解 ⊕ 予測",
    # Stage 1（M §5.2）
    "s1.towers_4types": "Stage1: 塔 4 種（D*-COCO / D*-ImageNet / P*-21 / P*-15）",
    "s1.folds5_foldA3seed": "Stage1: 5 折りで確定、折り A は 3 seed",
    "s1.tournament_K": "Stage1: トーナメント（候補数 K）",
    # Tier 2（M §5.3）
    "t2.sender_sweep_4pt": "Tier2: 送り手掃引 4 点",
    "t2.axis2_selection": "Tier2: 軸 2 選別",
    "t2.dp_w2": "Tier2: D→P の W2",
    "t2.dp_l0": "Tier2: D→P の L0",
    "t2.s1_on_p15": "Tier2: P*-15 上の S1",
    # Tier 3（M §5.3）
    "t3.w3": "Tier3: W3",
    "t3.sweep_extra_points": "Tier3: 掃引の追加点",
    "t3.s2_preliminary": "Tier3: S2 の予備",
    "t3.cholec80_l0": "Tier3: Cholec80 L0",
}


# --------------------------------------------------------------------------
# run の列挙。configs = 構成の数、reps は Tier ごとの反復（別に与える）。
# **二通りに読める項目は configs を (低, 高) の幅で持つ。一方に決めて隠さない。**
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class RunRow:
    key: str
    tier: str  # "stage1" | "tier1" | "tier2" | "tier3"
    label: str
    run_type: str
    configs_low: float
    configs_high: float
    covers: tuple[str, ...]
    reps_override: tuple[float, float] | None = None
    note: str = ""


# 反復（M §5.3 の「反復」欄）。
# Tier 1 の低い読み: 5 折り × 5 seed = 25。
# Tier 1 の高い読み: 折り A だけ受け取り塔が 3 seed のため 3×5 + 4×5 = 35。
#   （M §5.1「折り A のみ受け取り塔を 3 seed」を Tier 1 の反復へ掛ける読み）
REPS: dict[str, tuple[float, float]] = {
    "stage1": (1.0, 1.0),  # Stage 1 は行ごとに reps_override を持つ
    "tier1": (25.0, 35.0),
    "tier2": (10.0, 10.0),
    "tier3": (3.0, 3.0),
}

# 探索回数。M に回数の記載が無い。既定を 4 とし UNKNOWN として報告する。
DEFAULT_SEARCH_TRIALS = 4


def build_rows(k: int, search_trials: int, two_stage_selection: bool) -> list[RunRow]:
    """候補数 K と探索回数から run の列挙を組み立てる。"""
    # Stage 1 の反復。
    #   読み 1（既定）: 全候補を全折りで走らせる → 折り A 3 seed + 他 4 折り 1 seed = 7
    #   読み 2（二段選定）: 折り A で K 候補を 3 seed 走らせ、勝者だけ残り 4 折り → 3K + 4
    if two_stage_selection:
        s1_configs = 1.0
        s1_reps = (3.0 * k + 4.0, 3.0 * k + 4.0)
    else:
        s1_configs = float(k)
        s1_reps = (7.0, 7.0)

    rows: list[RunRow] = [
        # ---------------- Stage 1 ----------------
        RunRow(
            "s1_det_coco", "stage1", "Stage1: D*-COCO の塔", "det_tower_train",
            s1_configs, s1_configs,
            ("s1.towers_4types", "s1.folds5_foldA3seed", "s1.tournament_K"),
            reps_override=s1_reps,
        ),
        RunRow(
            "s1_det_imagenet", "stage1", "Stage1: D*-ImageNet の塔", "det_tower_train",
            s1_configs, s1_configs,
            ("s1.towers_4types", "s1.tournament_K"),
            reps_override=s1_reps,
        ),
        RunRow(
            "s1_phase_21", "stage1", "Stage1: P*-21 の塔", "phase_tower_train",
            s1_configs, s1_configs,
            ("s1.towers_4types", "s1.tournament_K"),
            reps_override=s1_reps,
        ),
        RunRow(
            "s1_phase_15", "stage1", "Stage1: P*-15 の塔", "phase_tower_train",
            s1_configs, s1_configs,
            ("s1.towers_4types", "s1.tournament_K"),
            reps_override=s1_reps,
        ),
        # ---------------- Tier 1 ----------------
        RunRow(
            "t1_none_det", "tier1", "方向なし: 検出塔 2 種の素評価", "det_eval",
            2, 2, ("t1.direction_4arm", "c2.no_iface_identity", "t1.pd_both_detectors"),
            note="界面なしとの一致確認の相手",
        ),
        RunRow(
            "t1_none_phase", "tier1", "方向なし: 工程塔の素評価", "phase_eval",
            1, 1, ("t1.direction_4arm", "c2.no_iface_identity"),
        ),
        RunRow(
            "t1_dp_w1", "tier1", "D→P・W1: 参照入力 4 段 × 送り手 L1/L2", "phase_iface",
            4 * 2, 4 * 2,
            ("t1.direction_4arm", "t1.ref_input_4stage", "t1.dp_w1", "t1.dp_l1l2",
             "t1.dp_p21", "t1.foldA_3seed", "t1.denominator_and_identity",
             "c1.empty_iface", "s.empty", "s.pred", "s.oracle", "s.oracle_plus_pred"),
            note="受け取りは P*-21。空段が分母",
        ),
        RunRow(
            "t1_pd_w1", "tier1", "P→D・W1: 参照入力 4 段 × 両検出塔", "det_iface_w1",
            4 * 2, 4 * 2,
            ("t1.direction_4arm", "t1.ref_input_4stage", "t1.pd_w1", "t1.pd_l3",
             "t1.pd_both_detectors", "t1.foldA_3seed", "t1.denominator_and_identity",
             "c1.empty_iface"),
            note="送り手は L3。空段が分母",
        ),
        RunRow(
            "t1_pd_w2", "tier1", "P→D・W2: 参照入力 4 段 × 両検出塔", "det_iface_w2",
            4 * 2, 4 * 2,
            ("t1.pd_w2", "c8.w1_vs_w2", "t1.foldA_3seed"),
            note="W1 との対比が対照 8 になる",
        ),
        RunRow(
            "t1_pd_search", "tier1", "P→D の専用探索", "det_iface_w1",
            search_trials, search_trials, ("t1.pd_dedicated_search",),
            note="探索回数は M に記載が無い（UNKNOWN）。--search-trials で動かせる",
        ),
        RunRow(
            "t1_bidir", "tier1", "双方向: 参照入力 4 段 × 両検出塔", "det_iface_w1",
            4 * 2, 4 * 2, ("t1.direction_4arm",),
            note="両側の界面を同時に学習する。費用は検出側が支配する",
        ),
        RunRow(
            "t1_ctrl_random_dp", "tier1", "対照: 乱数入力（D→P）", "phase_iface",
            1, 1, ("c3.random_input", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_random_pd", "tier1", "対照: 乱数入力（P→D）", "det_iface_w1",
            1, 1, ("c3.random_input", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_unrelated", "tier1", "対照: 同量非関連特徴（P→D の L3）", "det_iface_w1",
            1, 1, ("c4.same_volume_unrelated", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_shuffle_dp", "tier1", "対照: 時間・動画間 shuffle（D→P、2 種）", "phase_iface",
            2, 2, ("c5.shuffle_time_video", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_shuffle_pd", "tier1", "対照: 時間・動画間 shuffle（P→D、2 種）", "det_iface_w1",
            2, 2, ("c5.shuffle_time_video", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_reverse_dp", "tier1", "対照: 逆選別（D→P）", "phase_iface",
            1, 1, ("c6.reverse_selection", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_reverse_pd", "tier1", "対照: 逆選別（P→D）", "det_iface_w1",
            1, 1, ("c6.reverse_selection", "t1.controls"),
        ),
        RunRow(
            "t1_ctrl_probe", "tier1", "対照: クリップ ID 識別プローブ", "probe",
            1, 1, ("c7.clipid_probe", "t1.controls"),
        ),
        # ---------------- Tier 2 ----------------
        RunRow(
            "t2_sweep_pd", "tier2", "送り手掃引 4 点（P→D）", "det_iface_w1",
            4, 4, ("t2.sender_sweep_4pt",),
        ),
        RunRow(
            "t2_sweep_dp", "tier2", "送り手掃引 4 点（D→P）", "phase_iface",
            4, 4, ("t2.sender_sweep_4pt",),
        ),
        RunRow(
            "t2_axis2", "tier2", "軸 2 選別", "det_iface_w1",
            2, 2, ("t2.axis2_selection",),
        ),
        RunRow(
            "t2_dp_w2", "tier2", "D→P の W2（参照入力 4 段）", "phase_iface",
            4, 4, ("t2.dp_w2",),
        ),
        RunRow(
            "t2_dp_l0", "tier2", "D→P の L0（参照入力 4 段）", "phase_iface",
            4, 4, ("t2.dp_l0",),
        ),
        RunRow(
            "t2_s1_p15", "tier2", "P*-15 上の S1（参照入力 4 段）", "phase_iface",
            4, 4, ("t2.s1_on_p15",),
        ),
        # ---------------- Tier 3 ----------------
        RunRow(
            "t3_w3_pd", "tier3", "W3（P→D、参照入力 4 段）", "det_tower_w3",
            4, 4, ("t3.w3",),
        ),
        RunRow(
            "t3_w3_dp", "tier3", "W3（D→P、参照入力 4 段）", "phase_iface",
            4, 4, ("t3.w3",),
        ),
        RunRow(
            "t3_sweep_extra", "tier3", "掃引の追加点", "det_iface_w1",
            2, 2, ("t3.sweep_extra_points",),
        ),
        RunRow(
            "t3_s2_prelim", "tier3", "S2 の予備", "phase_iface",
            2, 2, ("t3.s2_preliminary",),
        ),
        RunRow(
            "t3_cholec80_l0", "tier3", "Cholec80 L0（参照入力 4 段）", "phase_iface",
            4, 4, ("t3.cholec80_l0",),
        ),
    ]
    return rows


# --------------------------------------------------------------------------
# 縮退順（M §5.3）。**段の数は M の項目数と一致させる。**
# 「掃引 4 点 → 3 点、検出塔候補の二段選定、seed 5 → 3、
#   探索的腕（W3、L3 の D→P 側）→ D→P の W2」= 読点区切りで 4 段。
# 4 段目は「探索的腕を削り、次に D→P の W2 を削る」と二段に読むこともできる。
# 両方の読みを出すため `--degrade-split-last` を置く。
# **P→D の W1・W2・専用探索は最後まで削らない**（M）。
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DegradeStep:
    key: str
    label: str
    note: str = ""


DEGRADE_STEPS: list[DegradeStep] = [
    DegradeStep("sweep_4to3", "掃引 4 点 → 3 点", "Tier 2 の送り手掃引と Tier 3 の追加点"),
    DegradeStep("two_stage_selection", "検出塔候補の二段選定", "Stage 1 の反復が 7K → 3K+4"),
    DegradeStep("seed_5to3", "seed 5 → 3", "Tier 1 の反復が 5 折り × 5 → 5 折り × 3"),
    DegradeStep(
        "drop_exploratory_and_dp_w2",
        "探索的腕（W3、L3 の D→P 側）→ D→P の W2",
        "Tier 3 の W3 と Tier 2 の D→P W2・L0 を落とす",
    ),
]

DEGRADE_STEPS_SPLIT: list[DegradeStep] = DEGRADE_STEPS[:3] + [
    DegradeStep("drop_exploratory", "探索的腕（W3、L3 の D→P 側）", "Tier 3 の W3 を落とす"),
    DegradeStep("drop_dp_w2", "D→P の W2", "Tier 2 の D→P W2・L0 を落とす"),
]

# 縮退で落とす行・値の対応。**P→D 側は現れない。**
_DEGRADE_DROP_ROWS: dict[str, tuple[str, ...]] = {
    "drop_exploratory_and_dp_w2": ("t3_w3_pd", "t3_w3_dp", "t2_dp_w2", "t2_dp_l0"),
    "drop_exploratory": ("t3_w3_pd", "t3_w3_dp"),
    "drop_dp_w2": ("t2_dp_w2", "t2_dp_l0"),
}


@dataclass
class Assumptions:
    k: int = 3
    devices: int = 2
    hours_per_day: float = 24.0
    search_trials: int = DEFAULT_SEARCH_TRIALS
    duration_scale: float = 1.0
    sweep_points: int = 4
    tier1_seeds: int = 5
    two_stage_selection: bool = False
    dropped_rows: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RowCost:
    row: RunRow
    runs_low: float
    runs_high: float
    gpu_hours_low: float
    gpu_hours_high: float


def _reps_for(row: RunRow, a: Assumptions) -> tuple[float, float]:
    if row.reps_override is not None:
        return row.reps_override
    if row.tier == "tier1":
        # 5 折り × seed 数。高い読みは折り A の受け取り塔 3 seed を掛ける。
        low = 5.0 * a.tier1_seeds
        high = 3.0 * a.tier1_seeds + 4.0 * a.tier1_seeds
        return (low, high)
    return REPS[row.tier]


def _configs_for(row: RunRow, a: Assumptions) -> tuple[float, float]:
    low, high = row.configs_low, row.configs_high
    if row.key in ("t2_sweep_pd", "t2_sweep_dp"):
        return (float(a.sweep_points), float(a.sweep_points))
    return (low, high)


def compute(a: Assumptions) -> dict:
    rows = build_rows(a.k, a.search_trials, a.two_stage_selection)
    rows = [r for r in rows if r.key not in a.dropped_rows]

    costs: list[RowCost] = []
    for row in rows:
        reps_low, reps_high = _reps_for(row, a)
        cfg_low, cfg_high = _configs_for(row, a)
        hours = RUN_TYPES[row.run_type].hours * a.duration_scale
        runs_low = cfg_low * reps_low
        runs_high = cfg_high * reps_high
        costs.append(
            RowCost(row, runs_low, runs_high, runs_low * hours, runs_high * hours)
        )

    by_tier: dict[str, dict[str, float]] = {}
    for c in costs:
        t = by_tier.setdefault(
            c.row.tier,
            {"runs_low": 0.0, "runs_high": 0.0, "gpu_low": 0.0, "gpu_high": 0.0},
        )
        t["runs_low"] += c.runs_low
        t["runs_high"] += c.runs_high
        t["gpu_low"] += c.gpu_hours_low
        t["gpu_high"] += c.gpu_hours_high

    longest = max(
        (RUN_TYPES[c.row.run_type].hours * a.duration_scale for c in costs), default=0.0
    )
    for t in by_tier.values():
        # **1 本の run は装置をまたげない。** 最長の 1 run を壁時計の下限に置く。
        t["wall_low"] = max(t["gpu_low"] / a.devices, longest)
        t["wall_high"] = max(t["gpu_high"] / a.devices, longest)

    return {"assumptions": a, "costs": costs, "by_tier": by_tier, "longest_run_hours": longest}


def cumulative_totals(result: dict, tiers: tuple[str, ...]) -> dict[str, float]:
    out = {"runs_low": 0.0, "runs_high": 0.0, "gpu_low": 0.0, "gpu_high": 0.0}
    for t in tiers:
        if t not in result["by_tier"]:
            continue
        for key in out:
            out[key] += result["by_tier"][t][key]
    dev = result["assumptions"].devices
    longest = result["longest_run_hours"]
    out["wall_low"] = max(out["gpu_low"] / dev, longest)
    out["wall_high"] = max(out["gpu_high"] / dev, longest)
    return out


# --------------------------------------------------------------------------
# 縮退
# --------------------------------------------------------------------------
def apply_degrade(base: Assumptions, steps: list[DegradeStep], upto: int) -> Assumptions:
    """縮退順を先頭から upto 段まで当てた前提を返す。"""
    a = Assumptions(**{**base.__dict__})
    dropped = list(base.dropped_rows)
    for step in steps[:upto]:
        if step.key == "sweep_4to3":
            a.sweep_points = 3
        elif step.key == "two_stage_selection":
            a.two_stage_selection = True
        elif step.key == "seed_5to3":
            a.tier1_seeds = 3
        elif step.key in _DEGRADE_DROP_ROWS:
            dropped.extend(_DEGRADE_DROP_ROWS[step.key])
    a.dropped_rows = tuple(dict.fromkeys(dropped))
    return a


# --------------------------------------------------------------------------
# 設計変更一回分（提案関門 B.7）
# Stage 1 の塔一種を作り直し、Tier 1 の P→D 側を測り直す。
# --------------------------------------------------------------------------
_REDESIGN_S1_ROW = "s1_det_coco"
_REDESIGN_T1_ROWS = (
    "t1_pd_w1",
    "t1_pd_w2",
    "t1_pd_search",
    "t1_bidir",
    "t1_ctrl_random_pd",
    "t1_ctrl_unrelated",
    "t1_ctrl_shuffle_pd",
    "t1_ctrl_reverse_pd",
    "t1_none_det",
)


def redesign_cost(a: Assumptions) -> dict:
    res = compute(a)
    keep = {_REDESIGN_S1_ROW, *_REDESIGN_T1_ROWS}
    rows = [c for c in res["costs"] if c.row.key in keep]
    total = {
        "runs_low": sum(c.runs_low for c in rows),
        "runs_high": sum(c.runs_high for c in rows),
        "gpu_low": sum(c.gpu_hours_low for c in rows),
        "gpu_high": sum(c.gpu_hours_high for c in rows),
    }
    total["wall_low"] = max(total["gpu_low"] / a.devices, res["longest_run_hours"])
    total["wall_high"] = max(total["gpu_high"] / a.devices, res["longest_run_hours"])
    return {"rows": rows, "total": total}


# --------------------------------------------------------------------------
# 締切（M §5.4。公式未確認。契約の決定により外部参照は行わない）
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Deadline:
    key: str
    label: str
    date: str
    source: str


TODAY = "2026-09-16"
DEADLINES: list[Deadline] = [
    Deadline("ipcai_intention", "IPCAI 2027 intention", "2026-10-25",
             "M §5.4「2026-10 下旬」。公式未確認。下旬の代表として 10-25 を採る"),
    Deadline("ipcai_abstract", "IPCAI 2027 long abstract", "2027-01-15",
             "M §5.4「2027-01 中旬」。公式未確認。中旬の代表として 01-15 を採る"),
    Deadline("miccai", "MICCAI 2027", "2027-02-15",
             "M §5.4「2027-02 頃」。公式未確認。月央の代表として 02-15 を採る"),
]


def days_until(date: str) -> int:
    from datetime import date as _date

    y0, m0, d0 = (int(x) for x in TODAY.split("-"))
    y1, m1, d1 = (int(x) for x in date.split("-"))
    return (_date(y1, m1, d1) - _date(y0, m0, d0)).days


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------
def _f(x: float, nd: int = 1) -> str:
    return f"{x:,.{nd}f}"


def _i(x: float) -> str:
    return f"{x:,.0f}"


def section_durations() -> str:
    out = ["| run 型 | 1 本の所要時間 | 実測/代理 | 出所 |", "|---|---:|---|---|"]
    for rt in RUN_TYPES.values():
        h = rt.hours
        dur = f"{h * 3600:.0f} s" if h < 1.0 / 60 * 3 else f"{h:.2f} h"
        kind = "実測" if rt.measured else "**代理（下界/上界）**"
        out.append(f"| {rt.label} | {dur} | {kind} | `{rt.source}` |")
    return "\n".join(out)


def section_enumeration(a: Assumptions) -> str:
    res = compute(a)
    out = [
        f"K = {a.k}、探索回数 = {a.search_trials}、Tier 1 の seed = {a.tier1_seeds}、掃引 = {a.sweep_points} 点。",
        "",
        "| 段階 | run 行 | run 型 | 構成 | 反復 | run 本数（低〜高） | GPU 時間（低〜高） | M の項目 |",
        "|---|---|---|---:|---|---:|---:|---|",
    ]
    for c in res["costs"]:
        reps_low, reps_high = _reps_for(c.row, a)
        cfg_low, cfg_high = _configs_for(c.row, a)
        cfg = _i(cfg_low) if cfg_low == cfg_high else f"{_i(cfg_low)}〜{_i(cfg_high)}"
        reps = _i(reps_low) if reps_low == reps_high else f"{_i(reps_low)}〜{_i(reps_high)}"
        runs = (
            _i(c.runs_low)
            if c.runs_low == c.runs_high
            else f"{_i(c.runs_low)}〜{_i(c.runs_high)}"
        )
        gpu = (
            _f(c.gpu_hours_low)
            if c.gpu_hours_low == c.gpu_hours_high
            else f"{_f(c.gpu_hours_low)}〜{_f(c.gpu_hours_high)}"
        )
        covers = "、".join(c.row.covers)
        out.append(
            f"| {c.row.tier} | {c.row.label} | `{c.row.run_type}` | {cfg} | {reps} | {runs} | {gpu} | {covers} |"
        )
    return "\n".join(out)


def section_base(a: Assumptions) -> str:
    out = [
        f"装置 {a.devices} 枚、1 日あたり {_f(a.hours_per_day)} 時間。",
        "",
        "| K | 段階 | run 本数（低〜高） | GPU 時間（低〜高） | 壁時計（低〜高） | 壁時計の日数（低〜高） |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for k in (2, 3, 4):
        aa = Assumptions(**{**a.__dict__, "k": k})
        res = compute(aa)
        for tiers, label in (
            (("stage1",), "Stage 1"),
            (("tier1",), "Tier 1"),
            (("stage1", "tier1"), "**Stage 1 + Tier 1**"),
            (("tier2",), "Tier 2"),
            (("tier3",), "Tier 3"),
            (("stage1", "tier1", "tier2", "tier3"), "全体"),
        ):
            t = cumulative_totals(res, tiers)
            out.append(
                f"| {k} | {label} | {_i(t['runs_low'])}〜{_i(t['runs_high'])} | "
                f"{_f(t['gpu_low'])}〜{_f(t['gpu_high'])} | "
                f"{_f(t['wall_low'])}〜{_f(t['wall_high'])} | "
                f"{_f(t['wall_low'] / a.hours_per_day)}〜{_f(t['wall_high'] / a.hours_per_day)} |"
            )
    return "\n".join(out)


def section_degrade(a: Assumptions, split_last: bool) -> str:
    steps = DEGRADE_STEPS_SPLIT if split_last else DEGRADE_STEPS
    out = [
        f"K = {a.k}、装置 {a.devices} 枚、1 日あたり {_f(a.hours_per_day)} 時間。"
        "対象は Stage 1 + Tier 1 + Tier 2 + Tier 3 の全体。",
        "",
        "| 段 | 当てた縮退 | run 本数（低〜高） | GPU 時間（低〜高） | 壁時計（低〜高） | 壁時計の日数（低〜高） |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    all_tiers = ("stage1", "tier1", "tier2", "tier3")
    for i in range(len(steps) + 1):
        aa = apply_degrade(a, steps, i)
        t = cumulative_totals(compute(aa), all_tiers)
        label = "縮退なし" if i == 0 else steps[i - 1].label
        out.append(
            f"| {i} | {label} | {_i(t['runs_low'])}〜{_i(t['runs_high'])} | "
            f"{_f(t['gpu_low'])}〜{_f(t['gpu_high'])} | "
            f"{_f(t['wall_low'])}〜{_f(t['wall_high'])} | "
            f"{_f(t['wall_low'] / a.hours_per_day)}〜{_f(t['wall_high'] / a.hours_per_day)} |"
        )
    return "\n".join(out)


def section_redesign(a: Assumptions) -> str:
    r = redesign_cost(a)
    out = [
        f"K = {a.k}、装置 {a.devices} 枚。Stage 1 の塔一種（D*-COCO）を作り直し、"
        "Tier 1 の P→D 側を測り直す。",
        "",
        "| 含めた run 行 | run 型 | run 本数（低〜高） | GPU 時間（低〜高） |",
        "|---|---|---:|---:|",
    ]
    for c in r["rows"]:
        out.append(
            f"| {c.row.label} | `{c.row.run_type}` | "
            f"{_i(c.runs_low)}〜{_i(c.runs_high)} | {_f(c.gpu_hours_low)}〜{_f(c.gpu_hours_high)} |"
        )
    t = r["total"]
    out.append(
        f"| **設計変更 1 回分（合計）** | — | **{_i(t['runs_low'])}〜{_i(t['runs_high'])}** | "
        f"**{_f(t['gpu_low'])}〜{_f(t['gpu_high'])}** |"
    )
    out.append("")
    out.append(
        f"壁時計 **{_f(t['wall_low'])}〜{_f(t['wall_high'])} 時間** "
        f"= **{_f(t['wall_low'] / a.hours_per_day)}〜{_f(t['wall_high'] / a.hours_per_day)} 日**"
        f"（1 日あたり {_f(a.hours_per_day)} 時間）。"
    )
    return "\n".join(out)


def section_deadline(a: Assumptions, split_last: bool) -> str:
    steps = DEGRADE_STEPS_SPLIT if split_last else DEGRADE_STEPS
    all_tiers = ("stage1", "tier1")
    out = [
        f"K = {a.k}、装置 {a.devices} 枚、1 日あたり {_f(a.hours_per_day)} 時間。"
        f"基準日 {TODAY}。対象は **Stage 1 + Tier 1**（Tier 2・3 は投稿の必須ではない）。",
        "",
        "| 段 | 当てた縮退 | 要する日数（低〜高） | "
        + " | ".join(f"{d.label}<br>（{d.date}、残 {days_until(d.date)} 日）" for d in DEADLINES)
        + " |",
        "|---:|---|---:|" + "---|" * len(DEADLINES),
    ]
    for i in range(len(steps) + 1):
        aa = apply_degrade(a, steps, i)
        t = cumulative_totals(compute(aa), all_tiers)
        need_low = t["wall_low"] / a.hours_per_day
        need_high = t["wall_high"] / a.hours_per_day
        label = "縮退なし" if i == 0 else steps[i - 1].label
        cells = []
        for d in DEADLINES:
            avail = days_until(d.date)
            if need_high <= avail:
                cells.append("収まる")
            elif need_low <= avail:
                cells.append("**読みにより分かれる**")
            else:
                cells.append("**収まらない**")
        out.append(
            f"| {i} | {label} | {_f(need_low)}〜{_f(need_high)} | " + " | ".join(cells) + " |"
        )
    out.append("")
    out.append("締切の出所:")
    for d in DEADLINES:
        out.append(f"- **{d.label}** = `{d.date}` — {d.source}")
    return "\n".join(out)


def section_unknown() -> str:
    out = ["| # | UNKNOWN | 影響 | 代理として置いた値 |", "|---:|---|---|---|"]
    n = 0
    for rt in RUN_TYPES.values():
        if rt.measured:
            continue
        n += 1
        out.append(f"| {n} | {rt.label} の所要時間 | `{rt.key}` を使う全行 | {rt.note} |")
    n += 1
    out.append(
        f"| {n} | P→D の専用探索の回数 | `t1_pd_search` の構成数 | "
        f"M に記載が無い。既定 {DEFAULT_SEARCH_TRIALS} 回。`--search-trials` で動かせる |"
    )
    n += 1
    out.append(
        f"| {n} | Tier 1 の反復に折り A の 3 seed が掛かるか | Tier 1 の全行 | "
        "二通りに読める。低い読み 25 本／高い読み 35 本を幅として出している |"
    )
    n += 1
    out.append(
        f"| {n} | Stage 1 で全候補を全折りに掛けるか | Stage 1 の全行 | "
        "二通りに読める。既定は全候補×全折り（7K）。二段選定の読みは縮退段 2 として出している |"
    )
    n += 1
    out.append(
        f"| {n} | 縮退順の 4 項目目が 1 段か 2 段か | 縮退表の段数 | "
        "読点区切りでは 4 段。`--degrade-split-last` で 5 段の読みも出せる |"
    )
    return "\n".join(out)


# 感度の例。**前提を変えると判定が変わり得ることを一例で示す**（完了判定 g）。
# 1 日あたりの使用時間だけを半分にし、他の前提は呼び出し側のまま使う。
SENSITIVITY_HOURS_PER_DAY = 12.0


def section_deadline_sensitivity(a: Assumptions, split_last: bool) -> str:
    aa = Assumptions(**{**a.__dict__, "hours_per_day": SENSITIVITY_HOURS_PER_DAY})
    return section_deadline(aa, split_last)


SECTIONS = {
    "durations": lambda a, s: section_durations(),
    "enumeration": lambda a, s: section_enumeration(a),
    "base": lambda a, s: section_base(a),
    "degrade": lambda a, s: section_degrade(a, s),
    "redesign": lambda a, s: section_redesign(a),
    "deadline": lambda a, s: section_deadline(a, s),
    "deadline_sensitivity": lambda a, s: section_deadline_sensitivity(a, s),
    "unknown": lambda a, s: section_unknown(),
}


# --------------------------------------------------------------------------
# 検査
# --------------------------------------------------------------------------
def check_sources() -> tuple[int, list[str]]:
    """出所の無い run 型を数える。**一件消せば 1 を返す。**"""
    bad = [rt.key for rt in RUN_TYPES.values() if not rt.source.strip()]
    return len(bad), bad


def check_coverage(a: Assumptions) -> tuple[int, list[str]]:
    """M の項目のうち run 行に対応づいていないものを数える。"""
    covered: set[str] = set()
    for row in build_rows(a.k, a.search_trials, a.two_stage_selection):
        covered.update(row.covers)
    missing = [k for k in M_ITEMS if k not in covered]
    return len(missing), missing


def check_doc(path: Path, a: Assumptions, split_last: bool) -> tuple[int, list[str]]:
    """文書に埋め込まれた生成物と、いま計算した値の差を数える。"""
    text = path.read_text(encoding="utf-8")
    found = {m.group("key"): m.group("body") for m in re.finditer(_BLOCK_RE, text, re.S)}
    diffs: list[str] = []
    for key, fn in SECTIONS.items():
        want = fn(a, split_last)
        got = found.get(key)
        if got is None:
            diffs.append(f"{key}: 文書に節が無い")
            continue
        if got.strip() != want.strip():
            want_lines = want.strip().split("\n")
            got_lines = got.strip().split("\n")
            for i in range(max(len(want_lines), len(got_lines))):
                w = want_lines[i] if i < len(want_lines) else "(無し)"
                g = got_lines[i] if i < len(got_lines) else "(無し)"
                if w != g:
                    diffs.append(f"{key} 行 {i + 1}:\n  文書 = {g}\n  再計算 = {w}")
    return len(diffs), diffs


def run_control(a: Assumptions) -> str:
    """対照。所要時間を 2 倍 → 総量 2 倍。装置を 2 倍 → 壁時計は半分以下。"""
    tiers = ("stage1", "tier1", "tier2", "tier3")
    base = cumulative_totals(compute(a), tiers)
    twice_dur = cumulative_totals(
        compute(Assumptions(**{**a.__dict__, "duration_scale": a.duration_scale * 2})), tiers
    )
    twice_dev = cumulative_totals(
        compute(Assumptions(**{**a.__dict__, "devices": a.devices * 2})), tiers
    )

    ratio_gpu_low = twice_dur["gpu_low"] / base["gpu_low"]
    ratio_gpu_high = twice_dur["gpu_high"] / base["gpu_high"]
    ratio_wall_low = twice_dev["wall_low"] / base["wall_low"]
    ratio_wall_high = twice_dev["wall_high"] / base["wall_high"]

    ok_dur = abs(ratio_gpu_low - 2.0) < 1e-9 and abs(ratio_gpu_high - 2.0) < 1e-9
    ok_dev = ratio_wall_low <= 0.5 + 1e-9 and ratio_wall_high <= 0.5 + 1e-9

    lines = [
        f"前提: K={a.k} 装置={a.devices} 1日={_f(a.hours_per_day)}h",
        "",
        "[対照 1] 所要時間表をすべて 2 倍にする → 総量が 2 倍になるはず",
        f"  基準   GPU 時間 = {_f(base['gpu_low'])} 〜 {_f(base['gpu_high'])}",
        f"  2 倍後 GPU 時間 = {_f(twice_dur['gpu_low'])} 〜 {_f(twice_dur['gpu_high'])}",
        f"  比 = {ratio_gpu_low:.6f} / {ratio_gpu_high:.6f}  → {'PASS' if ok_dur else 'FAIL'}",
        "",
        "[対照 2] 装置を 2 倍にする → 壁時計時間が半分以下になるはず",
        f"  基準   壁時計 = {_f(base['wall_low'])} 〜 {_f(base['wall_high'])} h（装置 {a.devices}）",
        f"  2 倍後 壁時計 = {_f(twice_dev['wall_low'])} 〜 {_f(twice_dev['wall_high'])} h（装置 {a.devices * 2}）",
        f"  比 = {ratio_wall_low:.6f} / {ratio_wall_high:.6f}  → {'PASS' if ok_dev else 'FAIL'}",
        "",
        f"RESULT: {'PASS' if ok_dur and ok_dev else 'FAIL'}"
        "（片方だけでは線形性の壊れ方と区別できないため両方を出している）",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--k", type=int, default=3, help="塔の候補数 K")
    p.add_argument("--devices", type=int, default=2, help="同時に使える GPU の枚数")
    p.add_argument("--hours-per-day", type=float, default=24.0, help="1 日あたり装置を使える時間")
    p.add_argument("--search-trials", type=int, default=DEFAULT_SEARCH_TRIALS,
                   help="P→D の専用探索の回数（M に記載が無い）")
    p.add_argument("--duration-scale", type=float, default=1.0, help="所要時間表の一律倍率")
    p.add_argument("--degrade-split-last", action="store_true",
                   help="縮退順の 4 項目目を 2 段に読む")
    p.add_argument("--section", choices=sorted(SECTIONS), help="節を一つだけ出す")
    p.add_argument("--control", action="store_true", help="対照を走らせる")
    p.add_argument("--check-sources", action="store_true", help="出所の無い行を数える")
    p.add_argument("--check-coverage", action="store_true", help="対応の無い M 項目を数える")
    p.add_argument("--check-doc", type=Path, help="文書の埋め込みと再計算の差を数える")
    p.add_argument("--json", action="store_true", help="機械可読で出す")
    args = p.parse_args(argv)

    a = Assumptions(
        k=args.k,
        devices=args.devices,
        hours_per_day=args.hours_per_day,
        search_trials=args.search_trials,
        duration_scale=args.duration_scale,
    )

    if args.check_sources:
        n, bad = check_sources()
        print(f"出所の無い run 型: {n} 件" + (f" → {bad}" if bad else ""))
        return 0 if n == 0 else 1

    if args.check_coverage:
        n, missing = check_coverage(a)
        print(f"対応の無い M 項目: {n} 件")
        for k in missing:
            print(f"  - {k}  {M_ITEMS[k]}")
        return 0 if n == 0 else 1

    if args.check_doc:
        n, diffs = check_doc(args.check_doc, a, args.degrade_split_last)
        print(f"文書と再計算の差: {n} 件")
        for d in diffs:
            print(f"  - {d}")
        return 0 if n == 0 else 1

    if args.control:
        print(run_control(a))
        return 0

    if args.json:
        tiers = ("stage1", "tier1", "tier2", "tier3")
        res = compute(a)
        payload = {
            "assumptions": a.__dict__,
            "by_tier": res["by_tier"],
            "longest_run_hours": res["longest_run_hours"],
            "stage1_plus_tier1": cumulative_totals(res, ("stage1", "tier1")),
            "all": cumulative_totals(res, tiers),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    keys = [args.section] if args.section else list(SECTIONS)
    for key in keys:
        if not args.section:
            print(BLOCK_BEGIN.format(key=key))
        print(SECTIONS[key](a, args.degrade_split_last))
        if not args.section:
            print(BLOCK_END.format(key=key))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
