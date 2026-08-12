#!/usr/bin/env python3
"""experiments/ を走査して機械可読な横断インデックス (runindex/) を収穫する。

設計原則
--------
1. 値を捏造しない。判定できないものは null + provenance="not_determinable"。
2. 情報を捨てない。除外は削除ではなくフラグ (excluded / exclusion_reason)。
3. experiments/ 配下は読み取り専用。一切変更しない。
4. 完全に再生成可能。出力に時刻・乱数・絶対パスを含めない (冪等性)。

二段構え
--------
  Stage 1: experiments/**/metrics.json  ->  runindex/runs/<ledger_key>.json
  Stage 2: runindex/runs/*.json           ->  runindex/index.csv

使い方
------
  python tools/harvest_runindex.py            # dry-run (書き出さない)
  python tools/harvest_runindex.py --write    # runindex/ を再生成
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"
RUNINDEX = REPO_ROOT / "runindex"

# --------------------------------------------------------------------------- #
# 除外規約
#
# experiments/README.md には `_` 接頭辞が「解析対象外」を意味するという規約が
# 明文化されていない (2026-07-31 時点)。そのため下記は「ディレクトリ名の意味
# からの判断」であり、規約に基づくものではない。anomalies.md にもその旨を記す。
# --------------------------------------------------------------------------- #
# 判定は 3 層。優先順は allowlist > run 単位 > ディレクトリ単位（classify_exclusion 参照）。
#
# ⚠️ 前方一致に一括変更してはならない。`_legacy_score_thr_0` は `_` 接頭辞だが
#    11 検出器の S0 基準点の唯一の証跡であり、除外すると解析から消える
#    (backlog B-28 / BL-legacy-prefix-must-not-exclude)。
#    マーカー末尾が `_` のものだけ前方一致にしている (backlog B-29)。
EXCLUSION_RULES: list[tuple[str, str]] = [
    # 既存 4 件（減らさない）
    ("_smoke_prior", "smoke_test"),
    ("_smoke_ddq", "smoke_test"),
    ("_wrong_split_8_2_3", "known_bad_split"),
    ("_failed_s3_weighted", "failed_run"),
    # lecun の退避 8 種。いずれも完全一致では拾えていなかった (B-29)。
    # `_smoke_prior_simplehead` は `_smoke_prior` とは別ディレクトリである点に注意。
    ("_smoke_v2_part3", "smoke_test"),
    ("_smoke_prior_simplehead", "smoke_test"),
    ("_smoke_e3", "smoke_test"),
    ("_pre_redo_s0_smoke", "smoke_test"),
    ("_prior_no_eval_recipe", "superseded"),
    ("_failed_num_workers_zero", "failed_run"),
    ("_aborted_codetr_no_config", "aborted_run"),
    ("_aborted_s0_cuda_visible_misconfig", "aborted_run"),
    # 初期化恒等性の検証 (B-24)。マーカー自体が可変長のため末尾 `_` で前方一致にする。
    ("_identity_", "identity_check"),
    ("_p0_identity_", "identity_check"),
]

# 🔴 `_` 接頭辞だが除外してはいけないディレクトリ (B-28)。EXCLUSION_RULES より優先する。
EXCLUSION_ALLOWLIST: frozenset[str] = frozenset(
    {
        "_legacy_score_thr_0",
        # 現状 metrics.json を持たないため走査されないが、規約の意図を明示しておく。
        "_orphan_no_metrics",
    }
)

# 個別 run の隔離（run ディレクトリ名の完全一致）。
# harvester は INVALID.md を読まないため、無効判定はここに書く必要がある。
RUN_EXCLUSIONS: dict[str, str] = {
    # 宣言と実体が食い違う凍結源で走った 3 run (B-25 / B-27)。
    # 一次証拠: evidence/aligndetr_s0frozen_incident_20260703/
    "s4_phase_baseline_010_frozen_tecno_phase_baseline_aligndetr_seed42": "wrong_frozen_source",
    "s4_phase_baseline_011_frozen_tecno_phase_baseline_aligndetr_seed123": "wrong_frozen_source",
    "s4_phase_baseline_012_frozen_tecno_phase_baseline_aligndetr_seed456": "wrong_frozen_source",
    # step='t1b_phasefilm' / arm='injection' と記録されているが実体は trainable=all / 3ep
    # の注入なし run (B-26)。数値自体は正しく、誤っているのはラベルのみ。
    # 対照情報として参照する場合は B-26 の本文と当該 metrics.json を直接見ること。
    "t1b_phasefilm_001_t1b_phasefilm_seed123": "mislabeled_arm_all_not_film",
    "t1b_phasefilm_002_t1b_phasefilm_seed456": "mislabeled_arm_all_not_film",
}

# --------------------------------------------------------------------------- #
# 指標キーの正規化
#
# Step 1 の実測で判明した構造:
#   - "val/<metric>"   : スラッシュ形式。split = val (284 key 出現)
#   - "test_<metric>"  : アンダースコア形式。split = test (27 key 出現)
#   - "phase_<metric>" : ★ split ではない。工程認識タスクの接頭辞 (506 key 出現)
#     根拠: phase_accuracy と test_accuracy が同一 run に 27 件共存する。
#           同じ run が 2 つの split を同時に持つことはあり得ない。
# --------------------------------------------------------------------------- #
PHASE_METRIC_BASES = {
    "accuracy",
    "edit_score",
    "jaccard",
    "macro_f1",
    "seg_f1_10",
    "seg_f1_25",
    "seg_f1_50",
    "frame_acc_inline",
}

# split とみなしてよい接頭辞 (アンダースコア形式)
UNDERSCORE_SPLIT_PREFIXES = {"test"}

# metrics.json のトップレベルが `"val": {...}` のように split で入れ子になる形式
# (g2_* 群)。スラッシュ形式 `val/<metric>` と意味は同じ。
SPLIT_NAMES = {"train", "val", "test"}

# 指標本体ではないメタキー
META_KEYS = {"eval_recipe", "eval_recipe_detection", "eval_recipe_phase", "epoch"}

# 数値だが指標ではない実行メタデータ。metrics に入れると experiments.csv に
# seed_mean / delta_seed / abs_delta_over_sigma_seed といった無意味な列が生える。
# 値は attributes に保持するので情報は失われない。
NON_METRIC_NUMERIC_KEYS = {
    "seed",
    "epochs",
    "best_epoch",
    "in_dim",
    "train_seconds",
    "n_clips",
}

# per_class_ap.json のクラス体系判定用
TOOL_CLASS_SET = frozenset(
    {
        "Bipolar Forceps",
        "Electric Cautery",
        "Forceps",
        "Gauze",
        "Hook",
        "Mouth Gag",
        "Needle Holders",
        "Raspatory",
        "Retractor",
        "Scalpel",
        "Scissors",
        "Skewer",
        "Suction Cannula",
        "Syringe",
        "Tweezers",
    }
)
PHASE_CLASS_SET = frozenset(
    {
        "anesthesia",
        "closure",
        "design",
        "disinfection",
        "dissection",
        "dressing",
        "hemostasis",
        "incision",
        "irrigation",
    }
)

# --------------------------------------------------------------------------- #
# host 正規化
#
# server.txt / eval_recipe.server_name に現れる生の値を実サーバー名へ写す。
# "aolab" は philip と ilya の双方が返すコンテナ内 hostname であり、
# 実サーバーを一意に特定できないため null にする (推測しない)。
# GPU 型番はどの証拠ファイルにも記録が無いため gpu は基本 null。
# --------------------------------------------------------------------------- #
HOST_ALIASES: dict[str, dict[str, Any]] = {
    "lecun": {"host": "lecun", "gpu": None, "note": "そのまま採用"},
    "efros": {"host": "efros", "gpu": None, "note": "そのまま採用"},
    "philip": {"host": "philip", "gpu": None, "note": "そのまま採用"},
    "bengio": {"host": "bengio", "gpu": None, "note": "そのまま採用"},
    "andrew": {"host": "andrew", "gpu": None, "note": "そのまま採用"},
    "ilya": {"host": "ilya", "gpu": None, "note": "そのまま採用"},
    "aolab": {
        "host": None,
        "gpu": None,
        "note": (
            "philip と ilya はいずれもコンテナ内 hostname が aolab を返すため "
            "実サーバーを特定できない。host は null、原文は host_raw に保持する。"
        ),
    },
}

# 終端は $ ではなく \Z を使い、照合は fullmatch で行う。Python の $ は**文字列末尾の
# 改行の直前にも一致する**ため、末尾に改行を持つディレクトリ名が「改行を落とした値」で
# 捕獲されてしまう（実測: "…_seed42\n" が seed='42' として通る）。異なる 2 つの
# ディレクトリが同じ ledger_key へ潰れうるため、検証系と同じ書き方に揃える。
RUN_NAME_RE = re.compile(r"(?P<step>.+?)_(?P<seq>\d{3})_(?P<desc>.+)_seed(?P<seed>\d+)\Z")
# seq を持たない別系統の命名 (g2_* 群: base_seed42 / bboxROI_seed123 / shuffleROI_seed456)。
# ExperimentManager を経由せずに作られた run。step は description と同じものを充てる。
RUN_NAME_NOSEQ_RE = re.compile(r"(?P<desc>.+?)_seed(?P<seed>\d+)\Z")

# --------------------------------------------------------------------------- #
# ディレクトリ名の det<N> / p<N> トークン
#
# ★ これらは seed とは限らない。command.sh の実引数が一次証拠:
#
#   b2a_base_oracle_noise_p010 ->
#     python scripts/train_b2a.py --seed 42 --tool-noise-rate 0.10
#       --description-override b2a_base_oracle_noise_p010
#     => p010 は **ノイズ率 0.10** であって seed ではない。
#
#   t1a_3seed_det123_p456_aug_001_..._seed456 ->
#     python scripts/train_t1a.py --description t1a_3seed_det123_p456_aug --seed 456
#     => p456 は --seed 456 と一致する。工程学習の seed（= 反復軸）。
#        det123 は凍結検出器チェックポイントの指定（= 条件。反復軸ではない）。
#
# 実測: ノイズ系を除いた 27 run すべてで p<N> == seed（27/27）。
#       ノイズ系 72 run はすべて --tool-noise-rate を持つ。
# --------------------------------------------------------------------------- #
AUX_DET_RE = re.compile(r"(?:^|_)det(\d+)(?:_|$)")
AUX_P_RE = re.compile(r"(?:^|_)p(\d+)(?:_|$)")
# ノイズ率を指定している run は p<N> をノイズ率として読む
NOISE_ARG_RE = re.compile(r"--(?:tool-)?noise(?:-rate)?[= ]")


# --------------------------------------------------------------------------- #
# ユーティリティ
# --------------------------------------------------------------------------- #
def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _denan(obj: Any) -> Any:
    """NaN / Infinity を None に落として標準 JSON として妥当にする。"""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _denan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_denan(v) for v in obj]
    return obj


def _is_nan(v: Any) -> bool:
    return isinstance(v, float) and math.isnan(v)


def _is_number(v: Any) -> bool:
    """指標として扱える数値か。bool は数値ではなく状態フラグなので除く。"""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def ledger_key_of(rel_path: Path) -> str:
    """runs/<key>.json のファイル名。dirname は 6 種が衝突するためパス由来にする。"""
    return str(rel_path).replace("/", "__")


# --------------------------------------------------------------------------- #
# 収穫ロジック
# --------------------------------------------------------------------------- #
def classify_exclusion(rel_path: Path) -> tuple[bool, str | None]:
    """run を解析対象から外すかを判定する。

    優先順:
      1. allowlist に載るディレクトリを通るなら **除外しない**（B-28）
      2. run 名が RUN_EXCLUSIONS に一致するなら除外
      3. パス構成要素が EXCLUSION_RULES に一致するなら除外
         マーカー末尾が ``_`` のものは前方一致、それ以外は完全一致（B-29）
    """
    # 1) 除外してはいけないものを最優先で救う。
    if any(part in EXCLUSION_ALLOWLIST for part in rel_path.parts):
        return False, None

    # 2) run 単位の隔離。
    reason = RUN_EXCLUSIONS.get(rel_path.name)
    if reason is not None:
        return True, reason

    # 3) ディレクトリ単位の除外。
    for part in rel_path.parts:
        for marker, marker_reason in EXCLUSION_RULES:
            hit = part.startswith(marker) if marker.endswith("_") else part == marker
            if hit:
                return True, marker_reason
    return False, None


def parse_run_name(name: str, command: str | None = None) -> tuple[dict[str, Any], list[str]]:
    """ディレクトリ名から step / seq / desc / seed を取り出す。

    補助 seed (det<N> / p<N>) は **command.sh の実引数を一次証拠にして**判定する。
    名前の見た目だけで seed だと決めない (b2a_*_noise_p010 の p010 はノイズ率)。
    """
    warnings: list[str] = []
    out: dict[str, Any] = {
        "step": None,
        "seq": None,
        "description": None,
        "seed": None,
        "seed_detector": None,
        "seed_phase": None,
        "aux_token_provenance": "no_aux_token",
        "name_provenance": "not_determinable",
    }
    m = RUN_NAME_RE.fullmatch(name)
    if m:
        out["step"] = m.group("step")
        out["seq"] = int(m.group("seq"))
        out["description"] = m.group("desc")
        out["seed"] = int(m.group("seed"))
        out["name_provenance"] = "from_dirname_step_seq_desc_seed"
    else:
        m2 = RUN_NAME_NOSEQ_RE.fullmatch(name)
        if not m2:
            warnings.append(f"run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない: {name}")
            return out, warnings
        # seq が無い系統。seq は「条件」ではなく単なる実行カウンタなので
        # (src/egosurgery/utils/experiment_id.py)、欠けていても実験単位は作れる。
        out["step"] = m2.group("desc")
        out["seq"] = None
        out["description"] = m2.group("desc")
        out["seed"] = int(m2.group("seed"))
        out["name_provenance"] = "from_dirname_desc_seed_no_seq"
        warnings.append(
            f"run 名に seq (3 桁連番) が無い別系統の命名: {name}。"
            f"step には description を充てた。"
        )

    cmd = command or ""
    det = AUX_DET_RE.search(name)
    p = AUX_P_RE.search(name)

    # det<N>: 凍結検出器チェックポイントの seed。**条件**であって反復軸ではない。
    # experiment_id からは剥がさない（剥がすと別 backbone の run が混ざる）。
    if det:
        out["seed_detector"] = int(det.group(1))

    if p:
        if NOISE_ARG_RE.search(cmd):
            # --tool-noise-rate を持つ -> p<N> はノイズ率。seed ではない。
            out["aux_token_provenance"] = "p_token_is_noise_rate_by_command_sh"
            warnings.append(
                f"ディレクトリ名の p{p.group(1)} は seed ではない。"
                f"command.sh が --tool-noise-rate を渡しており、ノイズ率 "
                f"0.{p.group(1)[:2] if len(p.group(1)) == 3 else p.group(1)} を指す。"
                f"seed_phase には入れない。"
            )
        elif int(p.group(1)) == out["seed"]:
            # p<N> == 末尾 seed -> 工程学習の seed（反復軸）。
            out["seed_phase"] = int(p.group(1))
            out["aux_token_provenance"] = "p_token_equals_run_seed"
        else:
            # 一次証拠が無い。推測しない。
            out["aux_token_provenance"] = "p_token_not_determinable"
            warnings.append(
                f"ディレクトリ名の p{p.group(1)} が末尾 seed{out['seed']} と一致せず、"
                f"command.sh にノイズ引数も無い。seed か否かを確定できないため "
                f"seed_phase は null にした。"
            )
    if det:
        out["aux_token_provenance"] = (
            out["aux_token_provenance"] + "+det_token_is_backbone_condition"
            if p
            else "det_token_is_backbone_condition"
        )
    return out, warnings


def normalize_metric_key(key: str) -> dict[str, Any]:
    """指標キーを (canonical, split, task) へ分解する。推測はしない。"""
    # スラッシュ形式: "<split>/<metric>"
    if "/" in key:
        prefix, rest = key.split("/", 1)
        return {"canonical": rest, "split": prefix, "task": None, "form": "slash"}

    # アンダースコア形式。第 1 トークンが split か task かを厳密に判定する。
    head, _, rest = key.partition("_")
    if rest:
        if head in UNDERSCORE_SPLIT_PREFIXES and rest in PHASE_METRIC_BASES:
            return {"canonical": rest, "split": head, "task": "phase", "form": "underscore_split"}
        if head == "phase" and rest in PHASE_METRIC_BASES:
            # phase_ は split ではなくタスク名。ただし split 自体は学習スクリプトの
            # コードから確定できる: 全 7 本が best = {**val, ...} で val を採る。
            #   scripts/train_{s4_tecno,b2a,t1a,haux,taux,t1a_boundary,
            #                  t1a_regiontraj}.py
            # 対になる test_* は k.replace("phase_", "test_") で書かれる。
            return {"canonical": rest, "split": "val", "task": "phase",
                    "form": "task_prefix_val_by_script"}
        if head == "sticky":
            # sticky_test_accuracy / sticky_accuracy
            sub = normalize_metric_key(rest)
            return {
                "canonical": f"sticky_{sub['canonical']}",
                "split": sub["split"],
                "task": sub["task"],
                "form": "sticky",
            }

    # 末尾 _sticky 形式 (phase_accuracy_sticky)
    if key.endswith("_sticky"):
        sub = normalize_metric_key(key[: -len("_sticky")])
        return {
            "canonical": f"sticky_{sub['canonical']}",
            "split": sub["split"],
            "task": sub["task"],
            "form": "sticky_suffix",
        }

    return {"canonical": key, "split": None, "task": None, "form": "bare"}


def harvest_metrics(raw: Any) -> dict[str, Any]:
    """metrics.json を正規化する。"""
    result: dict[str, Any] = {
        "metrics": {},
        "metrics_by_split": {},
        "metrics_nested": {},
        "attributes": {},
        "metrics_primary_split": None,
        "split": None,
        "split_provenance": "not_determinable",
        "epoch": None,
        "eval_recipe": None,
        "warnings": [],
        "duplicate_bare_keys": [],
        "conflicting_bare_keys": [],
    }
    if not isinstance(raw, dict):
        result["warnings"].append(f"metrics.json が dict ではない: {type(raw).__name__}")
        return result
    if not raw:
        result["warnings"].append("metrics.json が空 ({})")
        return result

    result["epoch"] = raw.get("epoch") if isinstance(raw.get("epoch"), int) else None
    recipe = raw.get("eval_recipe")
    if isinstance(recipe, dict):
        result["eval_recipe"] = _denan(recipe)

    by_split: dict[str, dict[str, Any]] = defaultdict(dict)
    bare: dict[str, Any] = {}
    nested: dict[str, Any] = {}
    attributes: dict[str, Any] = {}

    for key, value in raw.items():
        if key in META_KEYS:
            continue
        if isinstance(value, dict):
            # `"val": {"phase_accuracy": ...}` 形式（g2_* 群）。
            # `val/phase_accuracy` というスラッシュ形式と意味は同じで表記だけが違う。
            if key in SPLIT_NAMES and any(_is_number(v) for v in value.values()):
                for mk, mv in value.items():
                    if _is_number(mv):
                        # 外側のキーが split を表すので内側の split 判定は使わない
                        by_split[key][normalize_metric_key(mk)["canonical"]] = mv
                    else:
                        nested[f"{key}.{mk}"] = _denan(mv)
                continue
            nested[key] = _denan(value)
            continue
        if isinstance(value, list):
            nested[key] = _denan(value)
            continue
        if not _is_number(value) or key in NON_METRIC_NUMERIC_KEYS:
            # 指標は数値である。"system": "base" のような文字列を metrics に入れると
            # index.csv の metric.* 列に文字列が混ざり、集約も比較もできなくなる。
            # 数値でも seed / epochs のような実行メタデータは指標ではない。
            attributes[key] = value
            continue
        info = normalize_metric_key(key)
        canon = info["canonical"]
        if info["split"]:
            by_split[info["split"]][canon] = value
        else:
            bare[canon] = value

    # ------------------------------------------------------------------ #
    # primary split を **先に** 決める。
    #
    # ここを後回しにすると primary の入れ物 (flat) を primary が決まる前に
    # 埋めることになり、同じ canonical 名を複数 split が書く run
    # (phase_accuracy と test_accuracy が共存する 27 run) で
    # 「metrics.json のキー順で後に来た側が勝つ」= test が primary に入る。
    # split 列は val のままなので「val と名乗る test の値」という最悪の形になる。
    # 実際にこの退行が起きていたため、決定 -> 充填の順序を固定する。
    # ------------------------------------------------------------------ #
    #
    # val と test が共存する run は「val で best を選び、その重みを test でも評価した」
    # ものであり曖昧ではない。学習スクリプトのコードが一次証拠:
    #   best = {**val, ...}                        -> primary は val
    #   test_scalars[k.replace("phase_", "test_")] -> test は --eval-test の追加評価
    # したがって run 単位の split（= primary な指標の由来）は val で確定する。
    # 両方の値は metrics_by_split に保持しているので情報は失われない。
    primary: str | None = None
    evidence = {s for s in by_split if s != "unknown"}
    if len(evidence) == 1:
        primary = next(iter(evidence))
        result["split"] = primary
        result["split_provenance"] = "from_metric_key_prefix"
    elif evidence == {"val", "test"}:
        primary = "val"
        result["split"] = primary
        result["split_provenance"] = "primary_val_by_training_script"
        result["warnings"].append(
            "val と test の指標が共存する。primary（best 選択元）は val。"
            "test 側は metrics_by_split['test'] に保持している。"
        )
    elif len(evidence) > 1:
        # 実測 0 件。将来出現したときに黙って誤った primary を作らないための分岐。
        result["warnings"].append(
            f"複数 split の指標が同一 run に共存: {sorted(evidence)}。split は null にした。"
            "metrics には <split>__<metric> として split 名を残したまま入れる。"
        )
        result["split_provenance"] = "ambiguous_multiple_splits"

    # primary が決まってから flat を充填する。上書き衝突は起こり得ない。
    # flat は **数値のみ**。ネスト値を混ぜると index.csv の metric.* 列に
    # 辞書リテラルが書かれてしまう（metrics_nested に分けて保持している）。
    flat: dict[str, Any] = {}
    if primary is not None:
        flat.update(by_split[primary])
    else:
        for s in sorted(evidence):
            for k, v in by_split[s].items():
                flat[f"{s}__{k}"] = v

    # prefix 無しキーは、prefix 付きと一致すれば重複とみなす。不一致なら両方残す。
    for canon, value in bare.items():
        matched_splits = [s for s, d in by_split.items() if canon in d]
        if not matched_splits:
            flat.setdefault(canon, value)
            by_split["unknown"][canon] = value
            continue
        agree = all(by_split[s][canon] == value for s in matched_splits)
        if agree:
            result["duplicate_bare_keys"].append(canon)
        else:
            result["conflicting_bare_keys"].append(
                {
                    "key": canon,
                    "bare_value": _denan(value),
                    "by_split": {s: _denan(by_split[s][canon]) for s in matched_splits},
                }
            )
            flat[f"{canon}__bare"] = value
            by_split["unknown"][canon] = value

    # metrics の出所を機械可読に残す。回帰テストはこの列を突き合わせて検証する。
    result["metrics_primary_split"] = primary
    # 情報は捨てない。指標として扱えないものは別フィールドで保持する。
    result["metrics_nested"] = _denan(dict(sorted(nested.items())))
    result["attributes"] = _denan(dict(sorted(attributes.items())))

    result["metrics"] = _denan(dict(sorted(flat.items())))
    result["metrics_by_split"] = _denan(
        {s: dict(sorted(d.items())) for s, d in sorted(by_split.items())}
    )
    return result


# 正本 M2研究計画 §16.7（優先度 A 検証結果, 2026/05/29 追加）の §16.7.1 に、
# 評価 split についての明示的な記録がある:
#
#   「§8 訓練スクリプトに関する補足: val_evaluator の ann_file は
#     instances_val.json、prefix='val'（mmdet_config.py:314-320）のため、
#     metrics.json / per_class_ap.json はすべて val split の数値。
#     test split は未評価（最終報告用に温存、Δ 判定は val で行う設計）。」
#
#   ローカル写し: docs/m2_plan_rewrite/sections/19_epoch_16.md L161
#                 docs/m2_plan_rewrite/m2_plan_v2_full.md L1561
#
# これを split の既定値とする。ただし後から --eval-test が実装され、
# test_* キーを持つ run が 27 件出現している（正本の記述の例外。anomalies.md 参照）。
PLAN_DEFAULT_SPLIT_PROVENANCE = "from_plan_section_16_7"

# split を確定するための一次証拠。eval_recipe の split_*_images からの逆引きは
# 採用しない (3 split 全ての枚数が常に記録されており、どれを使ったかの情報ではない)。
_SPLIT_ARG_RE = re.compile(r"--(?:eval[-_])?split[= ]+(train|val|test)\b")
_SPLIT_ANN_RE = re.compile(r"instances_(train|val|test)\.json")
_EVAL_TEST_FLAG_RE = re.compile(r"--eval[-_]test\b")


def split_from_primary_evidence(
    recipe: dict[str, Any] | None,
    command: str | None,
    config_text: str | None,
) -> tuple[str | None, str]:
    """command.sh / config.yaml / eval_split キーという一次証拠から split を読む。

    優先順:
      (c) metrics.json の eval_recipe.eval_split  … 最も明示的
      (a) command.sh の --split / instances_*.json
      (b) config.yaml の ann_file / instances_*.json
    いずれからも取れなければ None (推測しない)。
    """
    if isinstance(recipe, dict):
        v = recipe.get("eval_split")
        if isinstance(v, str) and v in {"train", "val", "test"}:
            return v, "from_eval_split_key"

    if command:
        m = _SPLIT_ARG_RE.search(command)
        if m:
            return m.group(1), "from_command_sh"
        found = set(_SPLIT_ANN_RE.findall(command))
        if len(found) == 1:
            return found.pop(), "from_command_sh"

    if config_text:
        found = set(_SPLIT_ANN_RE.findall(config_text))
        if len(found) == 1:
            return found.pop(), "from_config_yaml"

    return None, "not_determinable"


def harvest_per_class(path: Path) -> dict[str, Any]:
    """per_class_ap.json を読み、kind / metric / source を分けて確定する。

    ファイル名は per_class_ap.json だが **中身が F1 の群が 500 run ある**。
    kind だけでは事故を防げないため metric を明示的に持たせる。

    実測根拠:
      - 9 クラス (工程名)  … scripts/train_{b2a,t1a,s4_tecno,haux,taux,
        t1a_boundary,t1a_regiontraj}.py が best.get("phase_per_class_f1", {}) を
        log_per_class_ap() に渡している  -> metric = "F1"
      - 15 クラス (術具名) … per_class_coco_map / COCOeval.precision 由来 -> "AP"
    """
    out: dict[str, Any] = {
        "per_class": None,
        "per_class_kind": None,
        "per_class_metric": None,
        "per_class_source": None,
        "per_class_nan_classes": [],
        "per_class_valid_count": None,
        "warnings": [],
    }
    if not path.exists():
        out["warnings"].append("per_class_ap.json が存在しない")
        return out
    out["per_class_source"] = str(path.relative_to(REPO_ROOT))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        out["warnings"].append(f"per_class_ap.json のパースに失敗: {exc}")
        return out
    if not isinstance(data, dict):
        out["warnings"].append(f"per_class_ap.json が dict ではない: {type(data).__name__}")
        return out
    if not data:
        out["warnings"].append("per_class_ap.json が空 ({})")
        out["per_class"] = {}
        out["per_class_valid_count"] = 0
        return out

    keys = frozenset(data)
    if keys == TOOL_CLASS_SET:
        out["per_class_kind"] = "tool"
        out["per_class_metric"] = "AP"
    elif keys == PHASE_CLASS_SET:
        # ファイル名は per_class_ap.json だが中身は工程別 F1 (AP ではない)。
        out["per_class_kind"] = "phase"
        out["per_class_metric"] = "F1"
    else:
        out["per_class_kind"] = "unknown"
        out["per_class_metric"] = "unknown"
        out["warnings"].append(
            f"per_class_ap.json のクラス集合が既知の 2 体系のいずれとも一致しない "
            f"({len(keys)} クラス) -> metric を確定できないため unknown"
        )

    nan_classes = sorted(k for k, v in data.items() if _is_nan(v))
    out["per_class"] = _denan(dict(sorted(data.items())))
    out["per_class_nan_classes"] = nan_classes
    out["per_class_valid_count"] = len(data) - len(nan_classes)
    return out


def harvest_per_class_from_nested(
    nested: dict[str, Any], run_dir: Path
) -> dict[str, Any] | None:
    """per_class_ap.json を持たない群 (g2_*) の per-class を metrics.json から拾う。

    `metrics.json` の `"val": {"phase_per_class_f1": {...}}` に入っている。
    値は F1 (ファイル名 per_class_ap.json の群と同じく AP ではない)。
    出所が違うので per_class_source で区別できるようにする。
    """
    if not nested:
        return None
    # primary は val。無ければ test。
    for split in ("val", "test", "train"):
        key = f"{split}.phase_per_class_f1"
        data = nested.get(key)
        if not isinstance(data, dict) or not data:
            continue
        keys = frozenset(data)
        kind = "phase" if keys == PHASE_CLASS_SET else "unknown"
        warnings: list[str] = []
        if kind == "unknown":
            warnings.append(
                f"metrics.json の {key} のクラス集合が既知の工程 9 クラスと一致しない "
                f"({len(keys)} クラス) -> metric を確定できないため unknown"
            )
        nan_classes = sorted(k for k, v in data.items() if _is_nan(v))
        return {
            "per_class": _denan(dict(sorted(data.items()))),
            "per_class_kind": kind,
            "per_class_metric": "F1" if kind == "phase" else "unknown",
            "per_class_source": f"{run_dir.relative_to(REPO_ROOT)}/metrics.json#{key}",
            "per_class_nan_classes": nan_classes,
            "per_class_valid_count": len(data) - len(nan_classes),
            "warnings": warnings,
        }
    return None


def harvest_config(path: Path) -> dict[str, Any]:
    """config.yaml から **機械可読な** 対照宣言と条件軸を取り出す。

    実測で判明した 2 つの重要な事実:

    1. `delta:` ブロックが 441/573 run にあり、`phase_denominator` が
       対照 family を文字列で明示している。
       例: `phase_denominator: s4_phase_baseline (frozen_tecno_phase_baseline)`
       notes.md の散文より遥かに強い一次証拠。

    2. `frozen_source.cache_dir` が凍結特徴の抽出元を示す **条件軸**である。
       これは環境変数 RELDETR_FROZEN_TAG で与えられるため
       command.sh にもディレクトリ名にも現れない
       (scripts/train_s4_tecno.py の _FROZEN_SRC = os.environ.get(...))。
       これを experiment_id に入れないと、異なる backbone の run が 1 実験に混ざる。
    """
    out: dict[str, Any] = {
        "delta_declaration": None,
        "frozen_source_tag": None,
        "seed_config": None,
        "frozen_source_seed_declared": None,
        # 契約 (tasks/<task_id>/spec.yaml) と run を結ぶ鍵。無ければ空文字
        # （未設定と未測定は違うので UNKNOWN にはしない）。
        "task_id": "",
        "warnings": [],
    }
    if not path.exists():
        return out
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001
        out["warnings"].append(f"config.yaml のパースに失敗: {type(exc).__name__}")
        return out
    if not isinstance(data, dict):
        return out

    d = data.get("delta")
    if isinstance(d, dict):
        out["delta_declaration"] = _denan(d)

    tid = data.get("task_id")
    if isinstance(tid, str) and tid.strip():
        out["task_id"] = tid.strip()

    # run 自身の学習 seed。ディレクトリ名の seed<N> と突き合わせる。
    if _is_number(data.get("seed")):
        out["seed_config"] = int(data["seed"])

    fs = data.get("frozen_source")
    if isinstance(fs, dict):
        cache = fs.get("cache_dir") or fs.get("gap_cache") or fs.get("tool_signal_cache")
        if isinstance(cache, str) and cache.strip():
            out["frozen_source_tag"] = cache.rstrip("/").split("/")[-1]
        # ★ frozen_source.seed は信用できない。scripts/train_s4_tecno.py が
        #   42 をハードコードしており、cache_dir と矛盾する run が実在する。
        #   実態はキャッシュのパスから取り、こちらは矛盾検出のためだけに保持する。
        if _is_number(fs.get("seed")):
            out["frozen_source_seed_declared"] = int(fs["seed"])
    return out


# command.sh から run 自身の seed を取る。argparse 形式と Hydra 形式の両方。
_CMD_SEED_RE = re.compile(r"(?:--seed[= ]+|(?<![\w.])seed=)(\d+)")


def seed_from_command(command: str | None) -> int | None:
    if not command:
        return None
    found = {int(m) for m in _CMD_SEED_RE.findall(command)}
    return found.pop() if len(found) == 1 else None


def normalize_host(server_txt: str | None, recipe: dict[str, Any] | None) -> dict[str, Any]:
    raw_txt = server_txt.strip() if isinstance(server_txt, str) else None
    raw_recipe = None
    if isinstance(recipe, dict):
        v = recipe.get("server_name")
        raw_recipe = v.strip() if isinstance(v, str) else None

    warnings: list[str] = []
    if raw_txt and raw_recipe and raw_txt != raw_recipe:
        warnings.append(
            f"server.txt ({raw_txt!r}) と eval_recipe.server_name ({raw_recipe!r}) が不一致。"
            f"server.txt を優先した。"
        )
    raw = raw_txt or raw_recipe
    provenance = (
        "from_server_txt" if raw_txt else ("from_eval_recipe" if raw_recipe else "not_determinable")
    )
    if raw is None:
        return {
            "host": None,
            "host_raw": None,
            "gpu": None,
            "provenance": "not_determinable",
            "warnings": warnings,
        }
    alias = HOST_ALIASES.get(raw)
    if alias is None:
        warnings.append(f"host_aliases.json に無い値: {raw!r}。host は null にした。")
        return {
            "host": None,
            "host_raw": raw,
            "gpu": None,
            "provenance": "unknown_alias",
            "warnings": warnings,
        }
    if alias["host"] is None:
        warnings.append(f"host {raw!r} は実サーバーを一意に特定できない。host は null にした。")
    return {
        "host": alias["host"],
        "host_raw": raw,
        "gpu": alias["gpu"],
        "provenance": provenance,
        "warnings": warnings,
    }



# --------------------------------------------------------------------------- #
# 外部記録（W&B）との対応
#
# tracking.record_run_identity() が実験フォルダ直下へ置く wandb_run.json を読む。
# 外部記録が無効だった run にはファイル自体が存在しない（空ファイルは作られない）
# 設計なので、「ファイルが無い＝空欄」で扱える。遡っての対応づけは行わないため、
# 本変更より前の run は全て空欄になるのが正しい。
# --------------------------------------------------------------------------- #
TRACKING_FILE = "wandb_run.json"


def harvest_tracking(run_dir: Path) -> dict[str, Any]:
    """wandb_run.json から run 識別子と参照先を読む。無ければ空。"""
    raw = _read_text(run_dir / TRACKING_FILE)
    if raw is None:
        return {"wandb_run_id": None, "wandb_run_url": None, "warnings": []}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "wandb_run_id": None,
            "wandb_run_url": None,
            "warnings": [f"{TRACKING_FILE} を読めない（JSON 不正）: {exc}"],
        }
    if not isinstance(data, dict):
        return {
            "wandb_run_id": None,
            "wandb_run_url": None,
            "warnings": [f"{TRACKING_FILE} の中身が dict でない: {type(data).__name__}"],
        }
    rid = data.get("run_id")
    url = data.get("run_url")
    return {
        "wandb_run_id": str(rid) if rid else None,
        "wandb_run_url": str(url) if url else None,
        "warnings": [],
    }


RECIPE_ID_KEYS = (
    "test_cfg",
    "split_train_images",
    "split_val_images",
    "split_test_images",
    "split_train_annotations",
    "split_val_annotations",
    "split_test_annotations",
    "effective_batch_size",
    "gpu_count",
    "lr_scaling",
)


def eval_recipe_id(recipe: dict[str, Any] | None) -> str | None:
    """同一評価条件の run を束ねる安定ハッシュ。server_name は条件に含めない。"""
    if not isinstance(recipe, dict):
        return None
    subset = {k: recipe[k] for k in RECIPE_ID_KEYS if k in recipe}
    if not subset:
        return None
    return _stable_hash(_denan(subset))


def build_run_record(run_dir: Path) -> dict[str, Any]:
    rel = run_dir.relative_to(REPO_ROOT)
    rel_from_exp = run_dir.relative_to(EXPERIMENTS)
    warnings: list[str] = []
    provenance: dict[str, str] = {}

    excluded, reason = classify_exclusion(rel_from_exp)

    # command.sh は補助 seed トークンの意味を確定する一次証拠なので先に読む。
    command = _read_text(run_dir / "command.sh")

    name_info, name_warn = parse_run_name(run_dir.name, command)
    warnings.extend(name_warn)

    try:
        raw_metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raw_metrics = None
        warnings.append(f"metrics.json のパースに失敗: {exc}")

    m = harvest_metrics(raw_metrics if raw_metrics is not None else {})
    warnings.extend(m["warnings"])

    pc = harvest_per_class(run_dir / "per_class_ap.json")
    # per_class_ap.json を持たない群 (g2_*) は metrics.json の
    # <split>.phase_per_class_f1 に per-class を入れている。出所は provenance で区別する。
    if pc["per_class"] is None:
        pc = harvest_per_class_from_nested(m["metrics_nested"], run_dir) or pc
    warnings.extend(pc["warnings"])

    server_txt = _read_text(run_dir / "server.txt")
    host = normalize_host(server_txt, m["eval_recipe"])
    warnings.extend(host["warnings"])

    tracking_ids = harvest_tracking(run_dir)
    warnings.extend(tracking_ids["warnings"])

    commit_txt = _read_text(run_dir / "git_commit.txt")
    commit = commit_txt.strip().split("\n")[0] if commit_txt else None
    notes = _read_text(run_dir / "notes.md")
    config_file = run_dir / "config.yaml"
    config_path = str(rel / "config.yaml") if config_file.exists() else None
    cfg = harvest_config(config_file)
    warnings.extend(cfg["warnings"])

    # split の確定。順に一次証拠を当たり、最後に正本の既定へ落とす。
    #   1. 指標キー形式（val/ … / test_ … / phase_ … + 学習スクリプトのコード）
    #   2. command.sh / config.yaml / eval_recipe.eval_split
    #   3. 正本 M2研究計画 §16.7 の既定（下記）
    # いずれも事実であり推測ではない。
    split = m["split"]
    split_prov = m["split_provenance"]
    if split is None:
        split, split_prov = split_from_primary_evidence(
            m["eval_recipe"], command, _read_text(config_file) if config_file.exists() else None
        )
    if split is None and m["metrics"]:
        # 正本の既定。指標が 1 つでもある run にのみ適用する
        # （metrics.json が空の run は「評価されていない」ので null のまま）。
        split, split_prov = "val", PLAN_DEFAULT_SPLIT_PROVENANCE

    # seed の出所と、他の一次証拠との突き合わせ。
    # notes.md は seed を書くが虚偽の実績があるため、証拠は command.sh と config.yaml。
    seed_cmd = seed_from_command(command)
    seed_cfg = cfg["seed_config"]
    # g2_* 群は command.sh も config.yaml も持たないが metrics.json に seed を書く。
    # 数値だが指標ではないので attributes へ退避してある。証拠としては使える。
    seed_mtr = m["attributes"].get("seed")
    seed_mtr = seed_mtr if isinstance(seed_mtr, int) else None
    seed_dir = name_info["seed"]
    if seed_dir is None:
        seed_prov, seed_agree = "not_determinable", "no_seed_in_dirname"
    else:
        others = {
            k: v
            for k, v in (
                ("command_sh", seed_cmd),
                ("config_yaml", seed_cfg),
                ("metrics_json", seed_mtr),
            )
            if v is not None
        }
        if not others:
            seed_prov, seed_agree = "from_dirname", "unverified_no_other_evidence"
        elif all(v == seed_dir for v in others.values()):
            seed_prov = "from_dirname_verified_by_" + "_and_".join(sorted(others))
            seed_agree = "agree"
        else:
            seed_prov, seed_agree = "from_dirname_conflicting_evidence", "conflict"
            warnings.append(
                f"ディレクトリ名の seed{seed_dir} が他の証拠と食い違う: "
                + ", ".join(f"{k}={v}" for k, v in sorted(others.items()))
                + "。ディレクトリ名を採用したが要確認。"
            )
    provenance["seed"] = seed_prov
    provenance["seed_detector"] = (
        "from_dirname_det_token" if name_info["seed_detector"] is not None else "not_determinable"
    )
    provenance["seed_phase"] = (
        "from_dirname_p_token" if name_info["seed_phase"] is not None else "not_determinable"
    )
    provenance["step"] = "from_dirname" if name_info["step"] else "not_determinable"
    provenance["name"] = name_info["name_provenance"]
    provenance["aux_token"] = name_info["aux_token_provenance"]
    provenance["split"] = split_prov
    provenance["per_class_metric"] = (
        "from_class_set_and_writer_script"
        if pc["per_class_metric"] in {"AP", "F1"}
        else "not_determinable"
    )
    provenance["host"] = host["provenance"]
    provenance["epoch"] = "from_metrics_json" if m["epoch"] is not None else "not_determinable"
    provenance["commit"] = "from_git_commit_txt" if commit else "not_determinable"
    provenance["per_class"] = (
        "from_per_class_ap_json" if pc["per_class"] is not None else "not_determinable"
    )

    record: dict[str, Any] = {
        "ledger_key": ledger_key_of(rel_from_exp),
        "run_id": run_dir.name,
        "group": rel_from_exp.parts[0],
        "subgroup": rel_from_exp.parts[1] if len(rel_from_exp.parts) > 2 else None,
        "path": str(rel),
        "excluded": excluded,
        "exclusion_reason": reason,
        "step": name_info["step"],
        "seq": name_info["seq"],
        "description": name_info["description"],
        "seed": name_info["seed"],
        # seed の突き合わせ用（§4）。notes.md は証拠に使わない（虚偽の実績がある）。
        "seed_command": seed_cmd,
        "seed_config": seed_cfg,
        "seed_agreement": seed_agree,
        "frozen_source_seed_declared": cfg["frozen_source_seed_declared"],
        "seed_detector": name_info["seed_detector"],
        "seed_phase": name_info["seed_phase"],
        "split": split,
        # metrics の各値がどの split から来たか。null なら split 接頭辞付きの指標が
        # 1 つも無い（= metrics は bare キーのみ、または空）。
        # split 列との整合は tools/verify_runindex.py が毎回検査する。
        "metrics_primary_split": m["metrics_primary_split"],
        "metrics": m["metrics"],
        "metrics_by_split": m["metrics_by_split"],
        # 指標として扱えなかった値。捨てずにここへ退避する（絶対規則: 情報を捨てない）。
        #   metrics_nested … metrics.json のネスト値 (hyperparams / n_clips 等)
        #   attributes     … 文字列や、数値でも指標ではない実行メタデータ (seed / epochs 等)
        "metrics_nested": m["metrics_nested"],
        "attributes": m["attributes"],
        "per_class": pc["per_class"],
        "per_class_kind": pc["per_class_kind"],
        "per_class_metric": pc["per_class_metric"],
        "per_class_source": pc["per_class_source"],
        "per_class_nan_classes": pc["per_class_nan_classes"],
        "per_class_valid_count": pc["per_class_valid_count"],
        "eval_recipe": m["eval_recipe"],
        "eval_recipe_id": eval_recipe_id(m["eval_recipe"]),
        # config.yaml 由来。対照宣言と、名前にも command.sh にも現れない条件軸。
        "delta_declaration": cfg["delta_declaration"],
        "frozen_source_tag": cfg["frozen_source_tag"],
        "task_id": cfg["task_id"],
        "host": host["host"],
        "host_raw": host["host_raw"],
        "gpu": host["gpu"],
        # 外部記録との対応。遡及しないため、本変更より前の run は空欄になる。
        "wandb_run_id": tracking_ids["wandb_run_id"],
        "wandb_run_url": tracking_ids["wandb_run_url"],
        "commit": commit,
        "command": command,
        "notes": notes,
        "config_path": config_path,
        "epoch": m["epoch"],
        "notion_page_id": None,
        "provenance": dict(sorted(provenance.items())),
        "harvest_warnings": warnings,
        "duplicate_bare_keys": sorted(m["duplicate_bare_keys"]),
        "conflicting_bare_keys": m["conflicting_bare_keys"],
        # experiments/ 配下は 6 点証跡が揃っている前提。直下 transfer/ と区別する（B-12）。
        "evidence_completeness": "full",
        "metrics_source": "metrics_json",
    }
    return record


# --------------------------------------------------------------------------- #
# B-12 / BL-runs-outside-experiments-dir — 直下 transfer/ の取り込み
#
# 直下 transfer/ の 29 run は 6 点証跡を 1 つも持たず、result.json だけがある。
# metrics.json / eval_recipe / git_commit.txt / server.txt が存在しないため、
# **無いものは生成せず null のまま**取り込み、evidence_completeness で区別する。
# 詳細な棚卸しは docs/runindex_instr10_stage1_transfer_inventory_ilya_2026-08-04.md。
# --------------------------------------------------------------------------- #
TRANSFER_LEGACY = REPO_ROOT / "transfer"

# 注入側 / 対照側の result ファイル名。群ごとに命名が違うので候補で受ける。
_TL_INJECTED = (
    "injected_result.json",
    "injection_t1b_result.json",
    "t1b_result.json",
    "bidir_result.json",
    "bidir_s4_result.json",
)
_TL_CONTROL = (
    "control_result.json",
    "zeroctx_t1b_result.json",
    "phasefrozen_result.json",
    "plasticphase_result.json",
)
# ディレクトリ名の接尾辞から分かるホスト。付いていない run は判別不能（null）。
_TL_HOST_SUFFIX = ("efros", "lecun", "bengio", "philip", "andrew", "ilya")


def _tl_first(run_dir: Path, names: tuple[str, ...]) -> tuple[dict | None, str | None]:
    for n in names:
        p = run_dir / n
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")), n
            except Exception:  # noqa: BLE001
                return None, n
    return None, None


def _tl_map(d: dict | None) -> dict[str, Any]:
    """result.json の指標を index の metric 名へ写す。無いキーは入れない。"""
    if not isinstance(d, dict):
        return {}
    out: dict[str, Any] = {}
    # 検出側。t1c 群は final_det_mAP / init_det_mAP という別名を使う。
    for src, dst in (
        ("mAP", "mAP"),
        ("init_mAP", "init_mAP"),
        ("final_mAP", "final_mAP"),
        ("final_det_mAP", "mAP"),
        ("init_det_mAP", "init_mAP"),
        ("final_epoch", "final_epoch"),
    ):
        v = d.get(src)
        if isinstance(v, (int, float)) and dst not in out:
            out[dst] = v
    # 工程側（t1c 群のみ）。accuracy 列に載せる。
    v = d.get("final_phase_acc")
    if isinstance(v, (int, float)):
        out["accuracy"] = v
    return out


def build_transfer_legacy_record(run_dir: Path) -> dict[str, Any]:
    rel = run_dir.relative_to(REPO_ROOT)
    warnings: list[str] = []
    provenance: dict[str, str] = {}

    inj, inj_file = _tl_first(run_dir, _TL_INJECTED)
    ctrl, ctrl_file = _tl_first(run_dir, _TL_CONTROL)
    if inj is None and ctrl is None:
        warnings.append("result.json を 1 つも読めなかった")

    primary = inj if inj is not None else ctrl
    metrics = _tl_map(primary)
    if ctrl is not None:
        cm = _tl_map(ctrl)
        if "mAP" in cm:
            metrics["control_mAP"] = cm["mAP"]
        if "init_mAP" in cm:
            metrics["control_init_mAP"] = cm["init_mAP"]
    # Δ は result.json 内で完結する引き算なので算出してよい（σ は別問題）。
    if "mAP" in metrics and "init_mAP" in metrics:
        metrics["delta_detection"] = metrics["mAP"] - metrics["init_mAP"]
    if "control_mAP" in metrics and "control_init_mAP" in metrics:
        metrics["delta_control"] = metrics["control_mAP"] - metrics["control_init_mAP"]
        if "delta_detection" in metrics:
            metrics["injection_effect"] = metrics["delta_detection"] - metrics["delta_control"]

    # host はディレクトリ名の接尾辞からのみ分かる。無ければ判別不能。
    # 接尾辞は実験条件ではなく実行ホストの印なので、step/seed の解釈前に外す
    # （外さないと `..._seed42_efros` から step を取れず experiments.csv に載らない）。
    host = None
    name_for_parse = run_dir.name
    for suf in _TL_HOST_SUFFIX:
        if run_dir.name.endswith(f"_{suf}"):
            host = suf
            name_for_parse = run_dir.name[: -(len(suf) + 1)]
            break

    name_info, name_warn = parse_run_name(name_for_parse, None)
    warnings.extend(name_warn)

    # per_class。best_epoch=-1 の run は {} を返す仕様なので「欠損ではなく結果」。
    pc_raw = (primary or {}).get("per_class_coco_map") or (primary or {}).get(
        "final_det_per_class_coco_map"
    )
    # NaN は標準 JSON として不正なので None へ落とし、どのクラスかは別に保持する。
    pc_nan = sorted(k for k, v in (pc_raw or {}).items() if _is_nan(v))
    per_class = _denan(pc_raw) if isinstance(pc_raw, dict) and pc_raw else None
    provenance["per_class"] = (
        f"from_{inj_file or ctrl_file}#per_class_coco_map"
        if per_class is not None
        else "empty_in_result_json_best_epoch_minus_1"
    )

    provenance["name"] = (
        "from_dirname_host_suffix_stripped" if host else "from_dirname"
    )
    provenance["host"] = (
        "from_dirname_suffix" if host else "not_determinable_no_server_txt_and_no_suffix"
    )
    provenance["commit"] = "not_determinable_no_git_commit_txt"
    provenance["eval_recipe"] = "not_determinable_no_metrics_json"
    provenance["metrics"] = f"from_{inj_file}" if inj_file else "not_determinable"
    provenance["split"] = "not_determinable_no_eval_recipe"
    provenance["seed"] = "from_dirname" if name_info["seed"] is not None else "not_determinable"
    provenance["step"] = "from_dirname" if name_info["step"] else "not_determinable"

    return {
        "ledger_key": str(rel).replace("/", "__"),
        "run_id": run_dir.name,
        "group": "transfer_legacy",
        "subgroup": None,
        "path": str(rel),
        "excluded": False,
        "exclusion_reason": None,
        "step": name_info["step"],
        "seq": name_info["seq"],
        "description": name_info["description"],
        "seed": name_info["seed"],
        "seed_command": None,
        "seed_config": None,
        "seed_agreement": "unverified_no_other_evidence",
        "frozen_source_seed_declared": None,
        "seed_detector": name_info["seed_detector"],
        "seed_phase": name_info["seed_phase"],
        # 外部記録との対応。**主経路と同じ出所から取る。**
        # ここに列が無いと、索引には列があるのに個別記録には無いという食い違いが残り、
        # 読む側は「対応が無い」のか「経路が違って書かれなかった」のか区別できない。
        # 2026-08-11 の実測では 751 件中 29 件（すべて transfer_legacy）が列を持たなかった。
        # 値は harvest_tracking が決める。wandb_run.json が無い run は空欄になるのが正しく、
        # **遡って対応づけはしない。**
        **{k: v for k, v in harvest_tracking(run_dir).items() if k != "warnings"},
        "split": None,
        "metrics_primary_split": None,
        "metrics": _denan(metrics),
        "metrics_by_split": {},
        "metrics_nested": {},
        # 指標以外（trainable / inject / epochs / zero_ctx / denominator 等）は捨てない。
        "attributes": _denan(
            {
                k: v
                for k, v in (primary or {}).items()
                if not isinstance(v, (dict, list)) and k not in metrics
            }
        ),
        "per_class": per_class,
        "per_class_kind": "coco_map" if per_class is not None else None,
        "per_class_metric": "AP" if per_class is not None else None,
        "per_class_source": (
            f"{rel}/{inj_file or ctrl_file}#per_class_coco_map" if per_class is not None else None
        ),
        "per_class_nan_classes": pc_nan,
        "per_class_valid_count": (
            sum(1 for v in per_class.values() if v is not None) if per_class is not None else None
        ),
        # 🔴 無いものは生成しない。eval_recipe が無いので同一条件の束ねができない。
        "eval_recipe": None,
        "eval_recipe_id": None,
        "delta_declaration": None,
        "frozen_source_tag": None,
        # config.yaml を持たない群（B-12）。task_id は取れないので空文字。
        "task_id": "",
        "host": host,
        "host_raw": host,
        "gpu": None,
        "commit": None,
        "command": None,
        "notes": _read_text(run_dir / "README.txt"),
        "config_path": None,
        "epoch": _denan((primary or {}).get("best_epoch")),
        "notion_page_id": None,
        "provenance": dict(sorted(provenance.items())),
        "harvest_warnings": warnings,
        "duplicate_bare_keys": [],
        "conflicting_bare_keys": {},
        "evidence_completeness": "result_json_only",
        "metrics_source": "result_json",
    }


def build_transfer_legacy_records() -> list[dict[str, Any]]:
    if not TRANSFER_LEGACY.is_dir():
        return []
    dirs = sorted(
        d for d in TRANSFER_LEGACY.iterdir() if d.is_dir() and any(d.glob("*result*.json"))
    )
    return [build_transfer_legacy_record(d) for d in dirs]


# --------------------------------------------------------------------------- #
# §3.1 experiment_id — seed を束ねる単位
#
# runs/*.json には seed をまたいで run を束ねるフィールドが 1 つも無かった。
# そのため 573 run は「573 個の孤立した run」であって「N 個の実験」ではなく、
# seed 集約も Δ も paired-σ も機械的に計算できない状態だった。
#
# 実験 ID = group + step + description(反復軸トークンを除去) + split
#   - seed / seed_phase は含めない（それが反復軸だから）
#   - seed_detector (det<N>) と名前中の seed<N> は **含める**
#     （凍結検出器チェックポイントの指定 = 条件であって反復軸ではない）
#   - split を含める（val と test を同一実験に混ぜない）
#   - 同一 ID 内で eval_recipe_id が食い違う場合は #<hash> を付けて分離する
#     （評価条件が違う run を束ねてはならない）
# --------------------------------------------------------------------------- #
def normalize_description(desc: str | None, seed_phase: int | None) -> str | None:
    """description から反復軸のトークンだけを取り除く。

    p<N> は seed_phase として確定できたときにだけ剥がす
    （b2a_*_noise_p010 のような「ノイズ率」は条件なので残す）。
    """
    if desc is None:
        return None
    out = desc
    if seed_phase is not None:
        out = re.sub(rf"(?:^|_)p{seed_phase}(?=_|$)", "_", out)
    out = re.sub(r"_+", "_", out).strip("_")
    return out or desc


def assign_experiment_ids(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """各 record に experiment_id を振る。戻り値は eval_recipe 分離の記録。"""
    base_of: dict[str, str] = {}
    for r in records:
        if r["step"] is None:
            r["experiment_id"] = None
            r["experiment_id_provenance"] = "not_determinable"
            continue
        # step にも同じ正規化を掛ける。多くの family では step == description であり、
        # description からだけ p<N> を剥がすと step 側に残った seed が実験を分裂させる
        # (t1a_3seed_det123_p{42,123,456}_aug が 3 つの単一 seed 実験になっていた)。
        ns = normalize_description(r["step"], r["seed_phase"])
        nd = normalize_description(r["description"], r["seed_phase"])
        base = f"{r['group']}/{ns}/{nd}@{r['split']}"
        # 凍結特徴の抽出元は環境変数 RELDETR_FROZEN_TAG で与えられるため
        # run 名にも command.sh にも現れない。config.yaml だけが持つ条件軸なので
        # ここで分離しないと異なる backbone の run が 1 実験に混ざる。
        if r.get("frozen_source_tag"):
            base += f"~{r['frozen_source_tag']}"
        base_of[r["ledger_key"]] = base

    # eval_recipe_id が食い違う base を分離する
    recipes: dict[str, set[str]] = defaultdict(set)
    for r in records:
        b = base_of.get(r["ledger_key"])
        if b is not None:
            recipes[b].add(str(r["eval_recipe_id"]))

    split_records: list[dict[str, Any]] = []
    for r in records:
        b = base_of.get(r["ledger_key"])
        if b is None:
            continue
        if len(recipes[b]) > 1:
            rid = str(r["eval_recipe_id"])
            r["experiment_id"] = f"{b}#{rid[:8]}"
            r["experiment_id_provenance"] = "from_run_name_split_by_eval_recipe"
            r["harvest_warnings"].append(
                f"同一 (group, step, description, split) 内で eval_recipe_id が "
                f"{len(recipes[b])} 通りに食い違う。評価条件が違う run を束ねないため "
                f"experiment_id を #{rid[:8]} で分離した。"
            )
            split_records.append({"base": b, "recipes": sorted(recipes[b])})
        else:
            r["experiment_id"] = b
            r["experiment_id_provenance"] = "from_run_name"
    return split_records


# --------------------------------------------------------------------------- #
# §3.2 arm / control_of — Δ を計算可能にする対照ペア
#
# 一次証拠の探索結果 (573 run 全走査):
#   - command.sh に --control / --baseline / --inject / --arm 引数は **0 件**
#   - notes.md に "## Δ" 節を持つ run が **439 件**あり、そこに対照が明記されている
#       例: 「Δ_phase = (B2a − S4 base 0.8986±0.0034)。同一土台(...)」
#           「Δ = (T1a-Boundary − T1a base[同env efros])」
#   - 参照先は "S4 base" (430 件) と "T1a base" (9 件) の 2 つだけ
#
# "S4 base" の同定は **数値照合で確定**した:
#   phase1/s4_phase_baseline を host=lecun・seed ごと最小 seq の 3 run に絞ると
#     mean   = 0.898570  -> notes の 0.8986 と一致
#     pstdev = 0.002766  -> notes の ±0.0028 と一致
#     stdev  = 0.003387  -> notes の ±0.0034 と一致 (= pstdev * sqrt(3/2))
#   同じ 3 run が母集団σと標本σの 2 通りで引用されている (anomalies 参照)。
#
# "T1a base[同env efros]" は step t1a_base_env (efros, seed 42/123/456) に対応する。
# こちらは数値の裏付けが無く、名前と host の一致による同定である。
# --------------------------------------------------------------------------- #
DELTA_SECTION_RE = re.compile(r"^##+\s*Δ.*?$(.*?)(?=^##|\Z)", re.M | re.S)
# Δ 節 / delta ブロックに書かれた基準値 (mean±sigma)
CONTROL_VALUE_RE = re.compile(r"([01]\.\d{3,4})\s*±\s*([0-9.]+)")
# 分母宣言の先頭トークン (= step) と、括弧内が識別子なら description
DENOM_RE = re.compile(r"^\s*(?P<step>[A-Za-z0-9_.-]+)(?:\s+base)?\s*(?:\((?P<paren>[^)]*)\))?")
IDENTIFIER_RE = re.compile(r"[a-z0-9_]+\Z")


def _parse_denominator(text: str) -> dict[str, Any]:
    """config.yaml の `delta.phase_denominator` を (step, description) に分解する。

    実データに現れる 4 通り:
      "s4_phase_baseline (frozen_tecno_phase_baseline)"  -> step + description
      "t1a_regiontoken base (同env efros paired)"        -> step のみ (括弧は散文)
      "t1a_regiontoken base (同一環境 efros で再学習・paired)" -> 同上
      "S0-frozen (=init mAP, within-run)"                -> run ではなく同一 run 内の初期値
    """
    s = (text or "").strip()
    if "within-run" in s or "within_run" in s:
        return {"kind": "within_run", "step": None, "description": None}
    m = DENOM_RE.match(s)
    if not m:
        return {"kind": "unparseable", "step": None, "description": None}
    paren = (m.group("paren") or "").strip()
    desc = paren if IDENTIFIER_RE.fullmatch(paren) else None
    return {"kind": "run_reference", "step": m.group("step"), "description": desc}


def assign_arms(records: list[dict[str, Any]]) -> dict[str, Any]:
    """対照ペア (arm / control_of) を一次証拠から決める。確定できなければ null。

    証拠の優先順:
      1. config.yaml の `delta.phase_denominator` … **機械可読な明示宣言**。441 run が保有
      2. notes.md の `## Δ` 節 … 散文。1 が無い run の補完に使う

    ★ 1 を先に見るのは重要である。notes.md の「T1a base[同env efros]」を
      名前の近さから step t1a_base_env と読むと **誤る**。
      config.yaml は分母を `t1a_regiontoken base (同env efros paired)` と
      明示しており、正しい対照は t1a_regiontoken である。
      散文からの同定は config の宣言に従属させる。
    """
    exps: dict[str, dict[str, Any]] = {}
    for r in records:
        eid = r.get("experiment_id")
        if not eid:
            continue
        exps.setdefault(
            eid,
            {
                "step": r["step"],
                "description": normalize_description(r["description"], r["seed_phase"]),
                "frozen_source_tag": r.get("frozen_source_tag"),
                "runs": [],
            },
        )["runs"].append(r)

    def _quoted_subset(runs: list[dict[str, Any]], host: str | None) -> list[float]:
        """host を絞り、seed ごとに最小 seq を 1 本ずつ採った accuracy の列。"""
        per_seed: dict[int, tuple[int, float]] = {}
        for r in runs:
            if host is not None and r["host"] != host:
                continue
            v = r["metrics"].get("accuracy")
            if isinstance(v, (int, float)) and r["seed"] is not None:
                if r["seed"] not in per_seed or r["seq"] < per_seed[r["seed"]][0]:
                    per_seed[r["seed"]] = (r["seq"], v)
        return [acc for _, acc in per_seed.values()]

    def _quoted_subset_mean(runs: list[dict[str, Any]], host: str | None) -> float | None:
        vals = _quoted_subset(runs, host)
        return statistics.mean(vals) if len(vals) > 1 else None

    resolved: dict[str, str] = {}
    unresolved: list[str] = []
    checks: list[dict[str, Any]] = []
    cache: dict[tuple[str, str | None, float | None, str | None], str | None] = {}

    def resolve(
        step: str, desc: str | None, quoted: float | None, frozen_tag: str | None
    ) -> str | None:
        key = (step, desc, quoted, frozen_tag)
        if key in cache:
            return cache[key]
        cands = [
            eid
            for eid, e in exps.items()
            if e["step"] == step and (desc is None or e["description"] == desc)
        ]
        # 凍結特徴のソースが同じ実験に絞る。
        # notes.md が対照の条件を「同一土台（凍結backbone/GAP/recipe/seed・neck無し）」と
        # 明記しているため、凍結 backbone を揃えるのは研究者自身が宣言した規則である。
        # （frozen_source_tag で実験を分けた以上、これをしないと分母が確定しない）
        if len(cands) > 1 and frozen_tag:
            same = [eid for eid in cands if exps[eid]["frozen_source_tag"] == frozen_tag]
            if len(same) == 1:
                cache[key] = same[0]
                return same[0]
            if same:
                cands = same
        result: str | None = None
        if len(cands) == 1:
            result = cands[0]
        elif len(cands) > 1 and quoted is not None:
            # 複数候補は引用された基準値で切り分ける（名前だけでは決めない）
            hit = []
            for eid in cands:
                for host in (None, "lecun", "efros"):
                    got = _quoted_subset_mean(exps[eid]["runs"], host)
                    if got is not None and abs(round(got, 4) - quoted) < 5e-5:
                        hit.append((eid, host, got))
                        break
            if len(hit) == 1:
                result = hit[0][0]
                vals = _quoted_subset(exps[result]["runs"], hit[0][1])
                checks.append(
                    {
                        "denominator": f"{step} ({desc})" if desc else step,
                        "experiment_id": result,
                        "quoted_mean": quoted,
                        "reproduced_mean": round(hit[0][2], 4),
                        "reproduced_from": f"host={hit[0][1]}, seed ごと最小 seq",
                        "population_sigma": round(statistics.pstdev(vals), 4) if len(vals) > 1 else None,
                        "sample_sigma": round(statistics.stdev(vals), 4) if len(vals) > 1 else None,
                        "n_candidates": len(cands),
                        "matched": True,
                    }
                )
            else:
                unresolved.append(
                    f"分母 {step!r} が {len(cands)} 実験に該当し、"
                    f"引用値 {quoted} で切り分けても {len(hit)} 件に絞られた。対照を確定できない。"
                )
        elif len(cands) > 1:
            unresolved.append(
                f"分母 {step!r} が {len(cands)} 実験に該当し、"
                f"引用値も無いため切り分けられない。対照を確定できない。"
            )
        else:
            unresolved.append(f"分母 {step!r} に該当する実験が experiments/ に無い。")
        cache[key] = result
        return result

    stats: Counter[str] = Counter()
    for r in records:
        r["arm"] = "unknown"
        r["control_of"] = None
        r["pairing_provenance"] = "not_determinable"
        r["control_note_value"] = None

        eid = r.get("experiment_id")
        decl = r.get("delta_declaration")

        denom_text = None
        prov = None
        if isinstance(decl, dict):
            for k in ("phase_denominator", "denominator", "detection_denominator"):
                v = decl.get(k)
                if isinstance(v, str) and v.strip():
                    denom_text, prov = v, "from_config_yaml"
                    break
        if denom_text is None:
            sec = DELTA_SECTION_RE.search(r.get("notes") or "")
            if sec:
                mm = re.search(r"[−-]\s*([A-Za-z0-9_.-]+\s*base)", sec.group(1))
                if mm:
                    denom_text, prov = mm.group(1), "from_notes"

        # 引用された基準値（config の denominator_value_* / note、なければ notes 本文）
        quoted = None
        blob = ""
        if isinstance(decl, dict):
            blob = " ".join(str(v) for v in decl.values())
        if not blob:
            sec = DELTA_SECTION_RE.search(r.get("notes") or "")
            blob = sec.group(1) if sec else ""
        vm = CONTROL_VALUE_RE.search(blob)
        if vm:
            quoted = float(vm.group(1))
            r["control_note_value"] = quoted

        if denom_text is None:
            stats["no_denominator_declared"] += 1
            continue

        parsed = _parse_denominator(denom_text)
        if parsed["kind"] == "within_run":
            # 同一 run 内の初期値との比較。対照 run は存在しない。
            r["arm"] = "injection"
            r["pairing_provenance"] = "within_run_baseline"
            stats["within_run_baseline"] += 1
            continue
        if parsed["kind"] != "run_reference" or not parsed["step"]:
            stats["denominator_unparseable"] += 1
            continue

        target = resolve(
            parsed["step"], parsed["description"], quoted, r.get("frozen_source_tag")
        )
        if target is None:
            stats["denominator_unresolvable"] += 1
            continue
        resolved[denom_text] = target
        if target == eid:
            r["arm"] = "baseline"
            r["pairing_provenance"] = prov
            stats["baseline_self"] += 1
            continue
        r["arm"] = "injection"
        r["control_of"] = target
        r["pairing_provenance"] = prov
        stats[f"injection_{prov}"] += 1

    # 対照として参照された実験自身に baseline を立てる
    targets = set(resolved.values())
    for r in records:
        if r.get("experiment_id") in targets and r["arm"] == "unknown":
            r["arm"] = "baseline"
            r["pairing_provenance"] = "referenced_as_denominator"
            stats["baseline"] += 1

    return {
        "resolved": resolved,
        "unresolved": sorted(set(unresolved)),
        "value_checks": checks,
        "stats": dict(stats),
    }


# --------------------------------------------------------------------------- #
# §3.3 experiments.csv — 1 行 = 1 実験 (= 論文 Table の 1 行)
# --------------------------------------------------------------------------- #
EXPERIMENT_SCALAR_COLUMNS = [
    "experiment_id",
    "group",
    "step",
    "description",
    "split",
    "eval_recipe_id",
    "n_runs",
    "n_seeds",
    "seeds",
    "runs_per_seed_max",
    "hosts",
    # index.csv の task_id（単数）を実験単位で distinct・カンマ結合したもの。
    "task_ids",
    "n_runs_excluded",
    "per_class_kind",
    "per_class_metric",
    "arm",
    "control_of",
    "pairing_provenance",
    "control_note_value",
    "delta_method",
    "delta_sigma_source",
    # 🔴 σ の系統。delta_sigma_source（paired / unpaired_pooled）とは軸が違う。
    #   paired_delta … 対照実験の宣言があり delta_pstd_* を使う（既存 720 run の主経路）
    #   within_run_seed_spread … run 内で対照が引かれた指標の seed 間 σ（B-12 / B-18）
    "sigma_source",
    "delta_dedup_rule",
    # §10.1 判定（主指標について）。σ の規約が repo 内で割れているため両方出す。
    "verdict_metric",
    "verdict_10_1",
    "verdict_10_1_sstd",
    "verdict_10_1_agree",
    "verdict_10_1_reason",
    # σ が何を測っているか（§2 の within/between 比から機械的に決める）
    "sigma_interpretation",
    "sigma_within_over_between",
    "n_command_variants",
]


def _agg(values: list[float]) -> dict[str, float | None]:
    """seed 集約。σ は **母集団σと標本σの両方**を出す。

    n=3 では両者の比が sqrt(3/2)=1.2247 あり、|Δ| > 1σ 判定の結論が反転しうる。
    どちらか一方だけを出すと、下流でどちらの規約か判別できなくなる
    (実際に notes.md が同じ基準点を ±0.0028 と ±0.0034 の 2 通りで引用していた)。
    """
    return {
        "mean": statistics.mean(values),
        "pstd": statistics.pstdev(values),  # 母集団σ (ddof=0)
        "sstd": statistics.stdev(values) if len(values) > 1 else None,  # 標本σ (ddof=1)
        "min": min(values),
        "max": max(values),
        "n": len(values),
    }


# --------------------------------------------------------------------------- #
# seed ごとに複数 run がある場合の代表値の取り方
#
# 対照実験 (s4_phase_baseline) は 1 つの seed に最大 7 run を持つ。畳まないと
# seed ごとの対応が付かず paired-σ が計算できない (136 実験中 131 が計算不能)。
#
# 既定は **mean**。理由:
#   - 順序に依存しない（seq / 時刻の記録が信用できない run がある）
#   - 特定の 1 本を選ばないので「どれを選ぶか」の恣意性が入らない
#   - 再実行のばらつきを捨てずに平均へ織り込む
#
# ★ "best"（比較する指標が最良の run を選ぶ）は **実装しない**。
#   比較対象の指標そのもので代表を選ぶと Δ が系統的に偏る（選択バイアス）。
#   対照側で best を選べば Δ は小さく、注入側で選べば大きく出る。
#   研究公正性の観点から提供しない。
# --------------------------------------------------------------------------- #
DEDUP_RULES = ("mean", "latest", "first")
DEFAULT_DEDUP_RULE = "mean"


def _reduce_by_seed(
    pairs: list[tuple[int | None, float]], rule: str
) -> float | None:
    """(seq, value) の列を seed 代表値 1 つに畳む。"""
    if not pairs:
        return None
    if len(pairs) == 1:
        return pairs[0][1]
    if rule == "mean":
        return statistics.mean(v for _, v in pairs)
    ordered = sorted(pairs, key=lambda x: (x[0] is None, x[0]))
    return ordered[-1][1] if rule == "latest" else ordered[0][1]


def _pool_sigma(a: float | None, b: float | None) -> float | None:
    """独立 2 群の差の σ: sqrt(σ_inj^2 + σ_ctl^2)。

    seed ごとの対応が取れない (unpaired) ときの合成。seed で対応が付く分の
    変動が相殺されないため **paired-σ より大きくなる**（= 有意になりにくい）。
    したがって unpaired で σ 条件を満たせば paired でも満たすが、逆は言えない。

    ★ ここでいう σ は「seed 間のばらつき」ではない。学習が決定的でないため
      同一条件反復のばらつきが混ざっている（anomalies §25 / §26）。
      どちらが支配的かは sigma_interpretation 列で判別する。
    """
    if a is None or b is None:
        return None
    return math.sqrt(a * a + b * b)


def _command_signature(command: str | None, seed: int | None = None) -> str:
    """command.sh の最終行から seed 由来・環境由来の差を除いた引数列。

    同一 experiment_id 内に **異なるハイパーパラメータの run** が混ざっていないかを
    見るための指紋。b2a_ro_oracle_noise000 は名前が 1 つなのに
    --tool-noise-rate が 0.05/0.10/0.20/0.30 の 4 通り存在する (anomalies §7.3)。

    seed が変われば必ず変わるもの（seed 値そのもの、seed を含む作業ディレクトリ、
    DDP の master_port）は条件差ではないので落とす。落とし損ねると
    「3 seed = 3 条件」に見えて偽陽性を大量に出す。
    """
    if not command:
        return ""
    line = [ln for ln in command.strip().split("\n") if ln.strip() and not ln.startswith("#")]
    if not line:
        return ""
    toks = line[-1].split()
    out, skip = [], False
    for t in toks:
        if skip:
            skip = False
            continue
        # argparse 形式: --seed 42
        if t in {"--seed", "--description", "--description-override"}:
            skip = True
            continue
        # Hydra 形式: seed=42 / experiment.description=foo
        if re.fullmatch(r"(?:\S+\.)?(?:seed|description)=\S*", t):
            continue
        # seed を名前に含む作業ディレクトリ (/tmp/dac_work_seed42)
        if re.search(r"seed\d+", t):
            continue
        # DDP の待ち受けポートは環境差
        if t.startswith("--master_port"):
            continue
        # 位置引数として渡された seed 値そのもの
        if seed is not None and t == str(seed):
            continue
        # 絶対パスは環境差なので除く（同一条件を別サーバーで回すと差が出る）
        out.append(re.sub(r"(/[^\s]*/)(?=[^/\s]+\.py\b)", "", t))
    return " ".join(out)


def _verdict_10_1(
    delta: float | None, sigma: float | None, same_sign: bool | None
) -> tuple[str, str]:
    """§10.1 の改善判定。**2 条件**を両方満たしたときだけ significant。

        |mean(Δ)| > σ  かつ  全 seed 同符号

    根拠 (リポジトリ内の実装 7 箇所が同じ 2 条件で書いている):
      scripts/paired_sigma_3seed.py:7 / analyze_t1a_factorial_ablation.py:13 /
      report_t1a_boundary.py:5 / report_daux_paired.py:114 /
      run_haux_oracle_gate.sh:14 / run_taux_problemA.sh:76 /
      src/egosurgery/utils/transfer_delta_report.py

    同符号は seed ごとの Δ が無いと判定できないので、unpaired では
    **undecidable** にする（σ 条件だけで significant と言ってはいけない）。
    """
    if delta is None or sigma is None:
        return "undecidable", "Δ または σ が無い"
    if same_sign is None:
        return "undecidable", "unpaired のため同符号条件を判定できない"
    if sigma == 0:
        return "undecidable", "σ = 0（ばらつきを測れていない）"
    if abs(delta) <= sigma:
        return "not_significant", "|Δ| <= σ"
    if not same_sign:
        return "not_significant", "全 seed 同符号ではない"
    return "significant", "|Δ| > σ かつ全 seed 同符号"


def _primary_metric(row: dict[str, Any], available: set[str]) -> str | None:
    """その実験の主指標。工程系は accuracy、検出系は mAP。"""
    for m in ("accuracy", "mAP", "tool_mAP"):
        if m in available and row.get(f"{m}_mean") is not None:
            return m
    return None


def build_experiments(
    records: list[dict[str, Any]], dedup_rule: str = DEFAULT_DEDUP_RULE
) -> tuple[list[str], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if r.get("experiment_id"):
            groups[r["experiment_id"]].append(r)

    metric_names: set[str] = set()
    for rs in groups.values():
        for r in rs:
            metric_names.update(k for k, v in r["metrics"].items() if isinstance(v, (int, float)))
    metric_names = set(sorted(metric_names))

    # 集約値をいったん全部作ってから Δ を計算する (対照の集約が要るため)
    agg_by_exp: dict[str, dict[str, dict[str, float]]] = {}
    seedvals_by_exp: dict[str, dict[str, dict[int, list[float]]]] = {}
    for eid, rs in groups.items():
        per_metric: dict[str, dict[str, float]] = {}
        per_seed: dict[str, dict[int, list[float]]] = {}
        for name in metric_names:
            vals = [r["metrics"][name] for r in rs if isinstance(r["metrics"].get(name), (int, float))]
            if not vals:
                continue
            per_metric[name] = _agg(vals)
            # (seq, value) で持つ。seq は latest / first の代表選択に要る。
            s: dict[int, list[tuple[int | None, float]]] = defaultdict(list)
            for r in rs:
                v = r["metrics"].get(name)
                if isinstance(v, (int, float)) and r["seed"] is not None:
                    s[r["seed"]].append((r.get("seq"), v))
            per_seed[name] = dict(s)
        agg_by_exp[eid] = per_metric
        seedvals_by_exp[eid] = per_seed

    # §2 の within/between 比を (experiment_id, metric) で引けるようにする。
    # σ が seed 効果を測っているかの判定に使う。
    _wh, _wr = build_within_vs_between(records)
    wb: dict[tuple[str, str], float] = {
        (r["experiment_id"], r["metric"]): r["ratio_within_over_between"]
        for r in _wr
        if r["ratio_within_over_between"] is not None
    }

    used_metrics = sorted({m for a in agg_by_exp.values() for m in a})
    header = list(EXPERIMENT_SCALAR_COLUMNS)
    for m in used_metrics:
        header += [f"{m}_mean", f"{m}_pstd", f"{m}_sstd", f"{m}_min", f"{m}_max", f"{m}_n"]
    for m in used_metrics:
        header += [
            f"delta_{m}",
            f"delta_pstd_{m}",
            f"delta_sstd_{m}",
            f"abs_delta_over_sigma_{m}",
            # §10.1 の第 2 条件（全 seed 同符号）。paired のときだけ判定できる。
            f"delta_same_sign_{m}",
            f"delta_n_seeds_{m}",
        ]

    rows = []
    for eid in sorted(groups):
        rs = groups[eid]
        first = rs[0]
        seeds = sorted({r["seed"] for r in rs if r["seed"] is not None})
        seed_counts = Counter(r["seed"] for r in rs if r["seed"] is not None)
        hosts = sorted({r["host"] for r in rs if r["host"]})
        task_ids = sorted({r["task_id"] for r in rs if r.get("task_id")})
        arms = sorted({r["arm"] for r in rs})
        controls = sorted({r["control_of"] for r in rs if r["control_of"]})
        note_vals = sorted({r["control_note_value"] for r in rs if r["control_note_value"]})
        cmd_sigs = {_command_signature(r.get("command"), r.get("seed")) for r in rs}

        row: dict[str, Any] = {
            "experiment_id": eid,
            "group": first["group"],
            "step": first["step"],
            "description": normalize_description(first["description"], first["seed_phase"]),
            "split": first["split"],
            "eval_recipe_id": first["eval_recipe_id"],
            "n_runs": len(rs),
            "n_seeds": len(seeds),
            "seeds": ",".join(str(s) for s in seeds),
            "runs_per_seed_max": max(seed_counts.values()) if seed_counts else 0,
            "hosts": ",".join(hosts),
            "task_ids": ",".join(task_ids),
            "n_runs_excluded": sum(1 for r in rs if r["excluded"]),
            "per_class_kind": ",".join(sorted({str(r["per_class_kind"]) for r in rs})),
            "per_class_metric": ",".join(sorted({str(r["per_class_metric"]) for r in rs})),
            "arm": ",".join(arms),
            "control_of": controls[0] if len(controls) == 1 else "",
            "pairing_provenance": ",".join(sorted({r["pairing_provenance"] for r in rs})),
            "control_note_value": note_vals[0] if len(note_vals) == 1 else "",
            "n_command_variants": len(cmd_sigs),
            "delta_method": "",
            "delta_sigma_source": "",
            "sigma_source": "",
            "delta_dedup_rule": "",
            "verdict_metric": "",
            "verdict_10_1": "",
            "verdict_10_1_sstd": "",
            "verdict_10_1_agree": "",
            "verdict_10_1_reason": "",
            "sigma_interpretation": "unknown",
            "sigma_within_over_between": "",
        }
        for m, a in agg_by_exp[eid].items():
            row[f"{m}_mean"] = a["mean"]
            row[f"{m}_pstd"] = a["pstd"]
            row[f"{m}_sstd"] = a["sstd"]
            row[f"{m}_min"] = a["min"]
            row[f"{m}_max"] = a["max"]
            row[f"{m}_n"] = a["n"]

        ctrl = controls[0] if len(controls) == 1 else None
        if ctrl and ctrl in agg_by_exp:
            cs = seedvals_by_exp[ctrl]
            os_ = seedvals_by_exp[eid]
            # paired: 双方とも seed ごとにちょうど 1 run で、seed 集合が一致するとき
            methods: set[str] = set()
            sources: set[str] = set()
            for m in agg_by_exp[eid]:
                if m not in agg_by_exp[ctrl]:
                    continue
                a, b = os_.get(m, {}), cs.get(m, {})
                # paired は **共通 seed（積集合）**で取る。片側にしか無い seed は
                # 対応が付かないので paired 比較から外すだけであり、
                # seed 集合の完全一致を要求する必要はない（それは過度に厳しい）。
                # 除外した seed は paired_feasibility.csv に記録する。
                #
                # seed ごとに複数 run がある場合は DEFAULT_DEDUP_RULE で 1 本に畳む。
                # 畳まないと 136 実験中 131 が paired 不能のままになる。
                common = set(a) & set(b)
                if len(common) >= 2:
                    ra = {s: _reduce_by_seed(a[s], dedup_rule) for s in common}
                    rb = {s: _reduce_by_seed(b[s], dedup_rule) for s in common}
                    diffs = [ra[s] - rb[s] for s in sorted(common)]
                    delta = statistics.mean(diffs)
                    pstd = statistics.pstdev(diffs)
                    sstd = statistics.stdev(diffs) if len(diffs) > 1 else None
                    # §10.1 は |mean(Δ)| > σ に加えて **全 seed 同符号**も要求する。
                    # unpaired では seed ごとの Δ が無く判定できないため paired 限定。
                    row[f"delta_same_sign_{m}"] = all(d > 0 for d in diffs) or all(
                        d < 0 for d in diffs
                    )
                    row[f"delta_n_seeds_{m}"] = len(diffs)
                    methods.add("paired")
                    sources.add("paired")
                else:
                    delta = agg_by_exp[eid][m]["mean"] - agg_by_exp[ctrl][m]["mean"]
                    # seed の対応が取れないので、独立 2 群として σ を合成する。
                    # paired-σ より大きく出る保守的な推定であることを
                    # delta_sigma_source 列で明示する。
                    pstd = _pool_sigma(agg_by_exp[eid][m]["pstd"], agg_by_exp[ctrl][m]["pstd"])
                    sstd = _pool_sigma(agg_by_exp[eid][m]["sstd"], agg_by_exp[ctrl][m]["sstd"])
                    methods.add("unpaired")
                    sources.add("unpaired_pooled")
                row[f"delta_{m}"] = delta
                row[f"delta_pstd_{m}"] = pstd
                row[f"delta_sstd_{m}"] = sstd
                # σ=0 は「有意」ではなく「ばらつきを測れていない」なので比を出さない
                if pstd:
                    row[f"abs_delta_over_sigma_{m}"] = abs(delta) / pstd
            # paired と unpaired を混同してはならないので両方出たら併記する。
            row["delta_method"] = ",".join(sorted(methods))
            row["delta_sigma_source"] = ",".join(sorted(sources))
            if any(k.startswith("delta_pstd_") and row.get(k) is not None for k in row):
                row["sigma_source"] = "paired_delta"
            row["delta_dedup_rule"] = dedup_rule if "paired" in methods else ""

            # §10.1 判定（主指標について）。σ の規約が割れているので両方出す。
            pm = _primary_metric(row, set(agg_by_exp[eid]))
            if pm:
                row["verdict_metric"] = pm
                v_p, reason = _verdict_10_1(
                    row.get(f"delta_{pm}"),
                    row.get(f"delta_pstd_{pm}"),
                    row.get(f"delta_same_sign_{pm}"),
                )
                v_s, _ = _verdict_10_1(
                    row.get(f"delta_{pm}"),
                    row.get(f"delta_sstd_{pm}"),
                    row.get(f"delta_same_sign_{pm}"),
                )
                row["verdict_10_1"] = v_p
                row["verdict_10_1_sstd"] = v_s
                row["verdict_10_1_agree"] = v_p == v_s
                row["verdict_10_1_reason"] = reason

                # σ が seed 効果を測っているのか、同一条件反復のばらつきも
                # 混ざっているのかを判定する。注入側と対照側の**両方**を見る
                # （Δ の σ は両者の合成であり、片方でも逆転していれば mixed）。
                ratios = [
                    wb[(e, pm)]
                    for e in (eid, ctrl)
                    if (e, pm) in wb
                ]
                if not ratios:
                    row["sigma_interpretation"] = "unknown"
                else:
                    worst = max(ratios)
                    row["sigma_within_over_between"] = worst
                    row["sigma_interpretation"] = (
                        "mixed_with_nondeterminism" if worst >= 1 else "seed_effect"
                    )

        # B-12 / B-18: 対照実験の宣言が無く paired σ を出せない実験でも、
        # run 内で対照が引かれた指標があれば seed 間 σ で §10.1 を判定する。
        # 出所を必ず列に残す（どちらの σ か分からない行を作らない）。
        if not row["sigma_source"]:
            for m in WITHIN_RUN_VERDICT_METRICS:
                if isinstance(row.get(f"{m}_pstd"), (int, float)):
                    row["sigma_source"] = "within_run_seed_spread"
                    break
        rows.append(row)
    return header, rows


VERDICT_COLUMNS = [
    "experiment_id",
    "metric",
    # 🔴 σ の出所。B-18（σ 規約の併存）の再発を防ぐため必ず埋める。
    #   paired_delta           … 対照実験が宣言された実験の delta_pstd_*（実験間の paired Δ の σ）
    #   within_run_seed_spread … run 内で対照が引かれた指標の seed 間 σ（{metric}_pstd）
    "sigma_source",
    "arm",
    "control_of",
    "delta_method",
    "delta_dedup_rule",
    "n_seeds",
    "delta",
    "pstd",
    "sstd",
    "ratio_pstd",
    "ratio_sstd",
    "same_sign",
    "verdict_pstd",
    "verdict_sstd",
    "agree",
    "reason",
]


# run 内で既に対照が引かれており、seed 間 σ で §10.1 を判定してよい指標。
# ここに delta_detection / delta_control を入れてはならない（対照が引かれていない）。
WITHIN_RUN_VERDICT_METRICS = ("injection_effect",)


def _within_run_verdicts(r: dict[str, Any]) -> list[dict[str, Any]]:
    """対照実験の宣言が無い実験を、run 内で引かれた指標の seed 間 σ で判定する。

    同符号は `{m}_min` / `{m}_max` から見る（seed ごとの値と等価）。
    0 は同符号とみなさない — §10.1 は「改善が全 seed で観測される」ことを求めており、
    差が 0 の seed は改善を示していないため。
    """
    out = []
    for m in WITHIN_RUN_VERDICT_METRICS:
        d = r.get(f"{m}_mean")
        if not isinstance(d, (int, float)):
            continue
        ps = r.get(f"{m}_pstd")
        ss = r.get(f"{m}_sstd")
        lo, hi = r.get(f"{m}_min"), r.get(f"{m}_max")
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            same_sign = (lo > 0 and hi > 0) or (lo < 0 and hi < 0)
        else:
            same_sign = None
        vp, reason = _verdict_10_1(d, ps, same_sign)
        vs, _ = _verdict_10_1(d, ss, same_sign)
        out.append(
            {
                "experiment_id": r["experiment_id"],
                "metric": m,
                "sigma_source": "within_run_seed_spread",
                "arm": r.get("arm"),
                "control_of": r.get("control_of"),
                "delta_method": "within_run",
                "delta_dedup_rule": "",
                "n_seeds": r.get(f"{m}_n"),
                "delta": d,
                "pstd": ps,
                "sstd": ss,
                "ratio_pstd": abs(d) / ps if ps else None,
                "ratio_sstd": abs(d) / ss if ss else None,
                "same_sign": same_sign,
                "verdict_pstd": vp,
                "verdict_sstd": vs,
                "agree": vp == vs,
                "reason": reason,
            }
        )
    return out


def build_verdicts(exp_rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """1 行 = 1 実験 × 1 指標 の §10.1 判定表（long 形式）。

    experiments.csv の `verdict_10_1` は主指標 1 つだけなので、
    全指標の判定はここで縦持ちにする。
    母集団σ (ddof=0) と標本σ (ddof=1) の両方で判定し `agree` で突き合わせる。
    """
    rows = []
    for r in exp_rows:
        # B-12 / B-18: transfer_legacy は対照実験が宣言されておらず delta_pstd_* が
        # 計算されない。ただし injection_effect は result.json 内で既に
        # Δ_inj − Δ_ctrl が引かれた値なので、その seed 間 σ で §10.1 を判定できる。
        # 対照が引かれていない delta_detection / delta_control は判定対象にしない
        # （mAP と同種の生の値であり、§10.1 の Δ ではない）。
        if r.get("group") == "transfer_legacy":
            rows.extend(_within_run_verdicts(r))
            continue
        metrics = sorted(
            k[len("delta_") :]
            for k in r
            if k.startswith("delta_")
            and not k.startswith(("delta_pstd_", "delta_sstd_", "delta_same_sign_", "delta_n_seeds_"))
            and k not in {"delta_method", "delta_sigma_source", "delta_dedup_rule"}
            and isinstance(r.get(k), (int, float))
        )
        for m in metrics:
            d = r.get(f"delta_{m}")
            ps = r.get(f"delta_pstd_{m}")
            ss = r.get(f"delta_sstd_{m}")
            sign = r.get(f"delta_same_sign_{m}")
            vp, reason = _verdict_10_1(d, ps, sign)
            vs, _ = _verdict_10_1(d, ss, sign)
            rows.append(
                {
                    "experiment_id": r["experiment_id"],
                    "metric": m,
                    "sigma_source": "paired_delta",
                    "arm": r.get("arm"),
                    "control_of": r.get("control_of"),
                    "delta_method": r.get("delta_method"),
                    "delta_dedup_rule": r.get("delta_dedup_rule"),
                    "n_seeds": r.get(f"delta_n_seeds_{m}"),
                    "delta": d,
                    "pstd": ps,
                    "sstd": ss,
                    "ratio_pstd": abs(d) / ps if d is not None and ps else None,
                    "ratio_sstd": abs(d) / ss if d is not None and ss else None,
                    "same_sign": sign,
                    "verdict_pstd": vp,
                    "verdict_sstd": vs,
                    "agree": vp == vs,
                    "reason": reason,
                }
            )
    return VERDICT_COLUMNS, rows


DEDUP_SENSITIVITY_COLUMNS = [
    "experiment_id",
    "metric",
    "dedup_rule",
    "delta",
    "pstd",
    "ratio_pstd",
    "same_sign",
    "verdict_pstd",
]


def build_dedup_sensitivity(
    records: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """代表値の取り方 (mean / latest / first) で Δ と判定がどれだけ動くか。

    既定は mean。恣意的な選択が結論を変えていないことを確認するために、
    他の規則でも計算して並べる。**"best" は選択バイアスを生むので出さない。**
    """
    rows = []
    for rule in DEDUP_RULES:
        _h, exp_rows = build_experiments(records, dedup_rule=rule)
        for r in exp_rows:
            if r.get("delta_method") != "paired":
                continue
            pm = r.get("verdict_metric")
            if not pm:
                continue
            d = r.get(f"delta_{pm}")
            ps = r.get(f"delta_pstd_{pm}")
            sign = r.get(f"delta_same_sign_{pm}")
            v, _ = _verdict_10_1(d, ps, sign)
            rows.append(
                {
                    "experiment_id": r["experiment_id"],
                    "metric": pm,
                    "dedup_rule": rule,
                    "delta": d,
                    "pstd": ps,
                    "ratio_pstd": abs(d) / ps if d is not None and ps else None,
                    "same_sign": sign,
                    "verdict_pstd": v,
                }
            )
    rows.sort(key=lambda x: (x["experiment_id"], x["metric"], x["dedup_rule"]))
    return DEDUP_SENSITIVITY_COLUMNS, rows


# --------------------------------------------------------------------------- #
# index.csv (Stage 2: runs/*.json から導出する)
# --------------------------------------------------------------------------- #
SCALAR_COLUMNS = [
    "ledger_key",
    "run_id",
    "experiment_id",
    "arm",
    "control_of",
    "pairing_provenance",
    "group",
    "subgroup",
    "path",
    "excluded",
    "exclusion_reason",
    "step",
    "seq",
    "description",
    "seed",
    "seed_command",
    "seed_config",
    "seed_agreement",
    "seed_detector",
    "seed_phase",
    "split",
    "metrics_primary_split",
    "frozen_source_tag",
    "per_class_kind",
    "per_class_metric",
    "per_class_source",
    "per_class_valid_count",
    "eval_recipe_id",
    "host",
    "host_raw",
    "gpu",
    "commit",
    "epoch",
    "notion_page_id",
    # 契約 (tasks/<task_id>/spec.yaml) と run を結ぶ鍵。config.yaml に無ければ空文字。
    "task_id",
    "has_test",
    "n_harvest_warnings",
    # 証跡の完全性。720 run は 'full'、直下 transfer/ の 29 run は 'result_json_only'
    # （metrics.json / eval_recipe / git_commit / server.txt を持たない）。B-12。
    "evidence_completeness",
    "metrics_source",
    # 証跡 (wandb_run.json) と外部記録 (W&B) を結ぶ鍵。外部記録が無効な run では空。
    # 遡っての対応づけは行わないため、本列の導入時点の run は全て空である。
    "wandb_run_id",
    "wandb_run_url",
]


def build_index(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """index.csv の列を組み立てる。

    `metric.<name>` は **primary（= split 列が指す側。実質 val）** の値。
    既存列の意味は変えない（後方互換）。

    test 側の値は `metric_test.<name>` として **別列**に展開する。
    これが無いと「split 列が val 一色 -> test 評価は存在しない」と誤読される。
    実測では 27 run が test 評価を持ち、val とは大きく乖離する。
    """
    metric_keys: set[str] = set()
    test_keys: set[str] = set()
    for r in records:
        metric_keys.update(r["metrics"].keys())
        test_keys.update((r["metrics_by_split"] or {}).get("test", {}).keys())

    metric_cols = [f"metric.{k}" for k in sorted(metric_keys)]
    test_cols = [f"metric_test.{k}" for k in sorted(test_keys)]
    header = SCALAR_COLUMNS + metric_cols + test_cols

    rows = []
    for r in sorted(records, key=lambda x: x["ledger_key"]):
        row = {c: r.get(c) for c in SCALAR_COLUMNS}
        row["n_harvest_warnings"] = len(r["harvest_warnings"])
        row["has_test"] = bool((r["metrics_by_split"] or {}).get("test"))
        for k, v in r["metrics"].items():
            row[f"metric.{k}"] = v
        for k, v in (r["metrics_by_split"] or {}).get("test", {}).items():
            row[f"metric_test.{k}"] = v
        rows.append(row)
    return header, rows


def build_val_test_pairs(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """test 評価を持つ run の val/test 対応表（anomalies/val_test_pairs.csv）。

    index.csv を横に見るだけでは val と test の乖離が読み取りにくいため、
    該当 run だけを縦持ちで別出しする。
    """
    names: set[str] = set()
    targets = [r for r in records if (r["metrics_by_split"] or {}).get("test")]
    for r in targets:
        by = r["metrics_by_split"]
        names.update(by.get("val", {}).keys() & by.get("test", {}).keys())

    header = ["ledger_key", "path", "group", "step", "seed", "excluded"]
    for n in sorted(names):
        header += [f"val.{n}", f"test.{n}", f"delta.{n}"]

    rows = []
    for r in sorted(targets, key=lambda x: x["ledger_key"]):
        by = r["metrics_by_split"]
        row = {
            "ledger_key": r["ledger_key"],
            "path": r["path"],
            "group": r["group"],
            "step": r["step"],
            "seed": r["seed"],
            "excluded": r["excluded"],
        }
        for n in sorted(names):
            v = by.get("val", {}).get(n)
            t = by.get("test", {}).get(n)
            row[f"val.{n}"] = v
            row[f"test.{n}"] = t
            if isinstance(v, (int, float)) and isinstance(t, (int, float)):
                row[f"delta.{n}"] = round(t - v, 6)
        rows.append(row)
    return header, rows


# --------------------------------------------------------------------------- #
# §1 決定性制御の棚卸し
#
# 同一 commit・同一 config・同一コマンド・同一 host の再実行が再現しない
# （anomalies §25）。原因は学習スクリプトが GPU の決定性を制御していないこと。
# 同じ欠陥が他のスクリプトにもあるかを機械的に棚卸しする。
#
# ★ ここで見ているのは **静的なコードの記述だけ**である。
#   実際に決定的かどうかを実行して確かめてはいない（再実行はしない方針）。
# --------------------------------------------------------------------------- #
SCRIPTS_DIR = REPO_ROOT / "scripts"
SRC_DIR = REPO_ROOT / "src"

DETERMINISM_CHECKS: dict[str, str] = {
    "random_seed": r"\brandom\.seed\s*\(",
    "numpy_seed": r"\bnp\.random\.seed\s*\(|\bnumpy\.random\.seed\s*\(|default_rng\s*\(",
    "torch_manual_seed": r"\btorch\.manual_seed\s*\(",
    "cuda_manual_seed": r"\btorch\.cuda\.manual_seed(?:_all)?\s*\(",
    "use_deterministic_algorithms": r"\btorch\.use_deterministic_algorithms\s*\(",
    "cudnn_deterministic": r"cudnn\.deterministic\s*=",
    "cudnn_benchmark": r"cudnn\.benchmark\s*=",
    "pythonhashseed": r"PYTHONHASHSEED",
    "dataloader_worker_init_fn": r"worker_init_fn\s*=",
    "dataloader_generator": r"\bgenerator\s*=\s*(?:g\b|torch\.Generator|gen\b)",
    "cublas_workspace_config": r"CUBLAS_WORKSPACE_CONFIG",
}

# 「これが揃わないと GPU 上で決定的になり得ない」項目
DETERMINISM_REQUIRED = (
    "torch_manual_seed",
    "cuda_manual_seed",
    "use_deterministic_algorithms",
    "cudnn_deterministic",
)

# 決定性制御をまとめて張るヘルパ。呼び出し元にはこの内容が効くので、
# ファイル単位の正規表現だけで判定すると **委譲先を見落として過小評価する**。
# 実際 src/egosurgery/ の Hydra 経路は seed_everything() 経由で
# cuda_manual_seed / cudnn_deterministic / PYTHONHASHSEED を設定している。
SEED_HELPERS: dict[str, str] = {
    "seed_everything": "src/egosurgery/utils/seed.py",
}

DETERMINISM_COLUMNS = [
    "script",
    # ok = 中身がある / empty = 0 バイトの scaffold / missing = repo に無い
    "file_state",
    # 直接記述か、ヘルパ経由か
    "seed_setup_via",
    "uses_cuda",
    "n_runs",
    "n_steps",
    "steps",
    *DETERMINISM_CHECKS.keys(),
    "num_workers",
    "shuffle",
    # DataLoader を使わないなら worker_init_fn / generator の欠落は該当しない。
    # 自前スクリプトはメモリ上のリストを random.shuffle で並べ替えている。
    "uses_dataloader",
    "shuffle_via_random_shuffle",
    # 実行時に os.environ["PYTHONHASHSEED"] を設定しても、CPython の
    # ハッシュ乱択はインタプリタ起動時に確定済みなので現行プロセスには効かない。
    "pythonhashseed_effective",
    # mmengine の randomness に deterministic=False を渡すなど、
    # フレームワーク側の決定化を **明示的に無効化**しているか
    "explicitly_disables_determinism",
    "missing_required",
    "can_be_deterministic",
]

_ENTRYPOINT_RE = re.compile(r"(?:python3?|bash)\s+(\S+\.(?:py|sh))")
_NUM_WORKERS_RE = re.compile(r"num_workers\s*=\s*([^,)\s]+)")
_SHUFFLE_RE = re.compile(r"shuffle\s*=\s*([^,)\s]+)")


def _entrypoint_of(command: str | None) -> str | None:
    """command.sh の entrypoint を **リポジトリ相対**に正規化する。

    command.sh には絶対パス (/home/ubuntu/slocal2/m2/scripts/train_b2a.py) と
    相対パス (scripts/train_b2a.py) が混在する。正規化しないと同じスクリプトが
    2 行に分かれて run 数が割れる。
    """
    if not command:
        return None
    m = _ENTRYPOINT_RE.search(command)
    if not m:
        return None
    path = m.group(1)
    # 絶対パスは既知のプロジェクトルート以降を残す
    for marker in ("/m2/", "/egosurgery_multitask/"):
        if marker in path:
            path = path.split(marker, 1)[1]
            break
    return path.lstrip("./")


def build_determinism_audit(
    records: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """学習スクリプトごとの決定性制御の有無と、影響を受ける run / step を出す。"""
    # entrypoint -> run
    by_script: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        ep = _entrypoint_of(r.get("command"))
        if ep:
            by_script[ep].append(r)

    # 監査対象: entrypoint に現れた全スクリプト + scripts/train_*.py
    #         + Hydra entrypoint が委譲する実装 (src/egosurgery/train.py は
    #           自身では CUDA を触らず engines/trainer.py に委譲する)
    targets: set[str] = set(by_script)
    if SCRIPTS_DIR.is_dir():
        targets |= {f"scripts/{p.name}" for p in sorted(SCRIPTS_DIR.glob("train_*.py"))}
    eng = SRC_DIR / "egosurgery" / "engines"
    if eng.is_dir():
        targets |= {
            str(p.relative_to(REPO_ROOT)) for p in sorted(eng.glob("*.py")) if p.name != "__init__.py"
        }

    rows = []
    for name in sorted(targets):
        cand = REPO_ROOT / name
        text = _read_text(cand) if cand.exists() else None
        runs = by_script.get(name, [])
        steps = sorted({r["step"] for r in runs if r["step"]})

        row: dict[str, Any] = {
            "script": name,
            "file_state": "ok" if text else ("empty" if cand.exists() else "missing"),
            "n_runs": len(runs),
            "n_steps": len(steps),
            "steps": ",".join(steps[:12]) + (" …" if len(steps) > 12 else ""),
        }
        if not text:
            for k in DETERMINISM_CHECKS:
                row[k] = None
            row["seed_setup_via"] = None
            row["uses_cuda"] = None
            row["num_workers"] = None
            row["shuffle"] = None
            row["uses_dataloader"] = None
            row["shuffle_via_random_shuffle"] = None
            row["pythonhashseed_effective"] = None
            row["explicitly_disables_determinism"] = None
            row["missing_required"] = ""
            row["can_be_deterministic"] = None
            rows.append(row)
            continue

        row["uses_cuda"] = bool(re.search(r'device\s*\(\s*["\']cuda|\.cuda\(\)|to\(\s*["\']cuda', text))
        for k, pat in DETERMINISM_CHECKS.items():
            row[k] = bool(re.search(pat, text))

        # 委譲を 1 段だけ追う。ヘルパを呼んでいればその設定内容を合成する。
        via = []
        for fn, helper_path in SEED_HELPERS.items():
            if not re.search(rf"\b{re.escape(fn)}\s*\(", text):
                continue
            helper = _read_text(REPO_ROOT / helper_path)
            if not helper:
                continue
            via.append(fn)
            for k, pat in DETERMINISM_CHECKS.items():
                if re.search(pat, helper):
                    row[k] = True
        # Hydra entrypoint は自分では乱数を触らず trainer に委譲する。
        # 呼び出し元の行だけを見ると「設定ゼロ」に見えるので明示する。
        if re.search(r"_select_trainer|StageATrainer|PhaseTrainer|MMDetTrainer", text):
            via.append("delegates_to_engines")
        row["seed_setup_via"] = (
            "+".join(via) if via else ("direct" if row["torch_manual_seed"] else "none")
        )
        row["num_workers"] = ",".join(sorted(set(_NUM_WORKERS_RE.findall(text)))) or ""
        row["shuffle"] = ",".join(sorted(set(_SHUFFLE_RE.findall(text)))) or ""
        row["uses_dataloader"] = bool(re.search(r"\bDataLoader\s*\(", text))
        row["shuffle_via_random_shuffle"] = bool(re.search(r"random\.shuffle\s*\(", text))
        # os.environ への代入は起動後なので効かない。シェル側の export だけが有効。
        row["pythonhashseed_effective"] = bool(
            re.search(r"export\s+PYTHONHASHSEED|PYTHONHASHSEED=\S+\s+(?:python|accelerate)", text)
        )
        row["explicitly_disables_determinism"] = bool(
            re.search(r"deterministic\s*=\s*False", text)
        )
        missing = [k for k in DETERMINISM_REQUIRED if not row[k]]
        row["missing_required"] = ",".join(missing)
        # uses_cuda の正規表現検出は取りこぼしうる（委譲先で .to(device) する等）。
        # 「CUDA を使わないから GPU 制御は不要」と判定すると偽の OK を出すので、
        # 必須項目が 1 つでも欠けていれば決定的になり得ないとする（保守側）。
        row["can_be_deterministic"] = not missing
        rows.append(row)
    return DETERMINISM_COLUMNS, rows


# --------------------------------------------------------------------------- #
# §2 within-seed と between-seed のばらつきの比較
#
# 「3-seed の σ」が seed 効果を測っているという前提が成り立つのは
# within < between のときだけである。逆転していれば σ は
# 「同一条件の再実行のばらつき」を主に測っている。
# --------------------------------------------------------------------------- #
WITHIN_BETWEEN_COLUMNS = [
    "experiment_id",
    "group",
    "step",
    "metric",
    "n_runs",
    "n_seeds",
    "n_seeds_with_repeats",
    "within_seed_sd",
    "between_seed_sd",
    "ratio_within_over_between",
    "within_exceeds_between",
    "within_seed_range_max",
    "between_seed_range",
    # ★ 交絡の指標。>1 なら同一 experiment_id に異なる条件の run が混ざっており、
    #   within-seed のばらつきは「非決定性」ではなく「条件差」を測っている。
    "n_command_variants",
    "within_is_confounded_by_condition",
]


def build_within_vs_between(
    records: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """同一 seed の反復がある実験について within / between のσを比べる。

    within_seed_sd  … seed ごとの母集団σを、反復がある seed について平均したもの
    between_seed_sd … seed 平均どうしの母集団σ
    比が 1 を超える = σ が seed 効果ではなく非決定性を主に測っている。
    """
    by_exp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if r.get("experiment_id"):
            by_exp[r["experiment_id"]].append(r)

    rows = []
    for eid in sorted(by_exp):
        rs = by_exp[eid]
        seeds = Counter(r["seed"] for r in rs if r["seed"] is not None)
        if not seeds or max(seeds.values()) < 2:
            continue  # 反復が無ければ within は定義できない
        metric_names = sorted(
            {k for r in rs for k, v in r["metrics"].items() if _is_number(v)}
        )
        n_variants = len({_command_signature(r.get("command"), r.get("seed")) for r in rs})
        for m in metric_names:
            per_seed: dict[int, list[float]] = defaultdict(list)
            for r in rs:
                v = r["metrics"].get(m)
                if _is_number(v) and r["seed"] is not None:
                    per_seed[r["seed"]].append(v)
            reps = {s: v for s, v in per_seed.items() if len(v) > 1}
            means = [statistics.mean(v) for v in per_seed.values() if v]
            if not reps or len(means) < 2:
                continue
            within = statistics.mean(statistics.pstdev(v) for v in reps.values())
            between = statistics.pstdev(means)
            rows.append(
                {
                    "experiment_id": eid,
                    "group": rs[0]["group"],
                    "step": rs[0]["step"],
                    "metric": m,
                    "n_runs": len(rs),
                    "n_seeds": len(per_seed),
                    "n_seeds_with_repeats": len(reps),
                    "within_seed_sd": within,
                    "between_seed_sd": between,
                    "ratio_within_over_between": (within / between) if between else None,
                    "within_exceeds_between": bool(between and within > between),
                    "within_seed_range_max": max(max(v) - min(v) for v in reps.values()),
                    "between_seed_range": max(means) - min(means),
                    "n_command_variants": n_variants,
                    "within_is_confounded_by_condition": n_variants > 1,
                }
            )
    return WITHIN_BETWEEN_COLUMNS, rows


PAIRED_FEASIBILITY_COLUMNS = [
    "experiment_id",
    "control_of",
    "paired_declared",
    "pairable_now",
    "blocking_reason",
    "pairable_after_dedup",
    "dedup_rule",
    "n_runs_injection",
    "n_seeds_injection",
    "seeds_injection",
    "runs_per_seed_max_injection",
    "n_runs_control",
    "n_seeds_control",
    "seeds_control",
    "runs_per_seed_max_control",
    "seed_set_match",
    "n_seeds_common",
    "n_seeds_paired_now",
    "seeds_only_in_injection",
    "seeds_only_in_control",
    "n_runs_injection_pairable",
]

# notes.md / config.yaml が paired-σ 判定を宣言しているか
PAIRED_DECLARED_RE = re.compile(r"paired[-\s]?(?:σ|sigma)|対seed差")


def build_paired_feasibility(
    records: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """paired-σ が計算できるか / できないなら何が阻んでいるかを全件出力する。

    notes.md は「3-seed 揃ったら paired-σ(対seed差) で §10.1 判定」と宣言するが、
    実際に seed 対応が取れる実験はごく少数である。宣言と実行可能性の差を
    実験ごとに機械可読な形で残す（§10.1 の結論に影響しうるため）。

    `pairable_after_dedup` は「seed ごとに代表 1 本を選ぶ規約」を入れた場合に
    paired 可能になるかを示す。代表の選び方は
    src/egosurgery/utils/transfer_delta_report.py が seq 最大（最新の再実行）を
    採っているので、それに倣った場合を計算する。**この規約は s4 系には
    明文化されていない**ため、あくまで「入れれば可能になる」の試算である。
    """
    by_exp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        if r.get("experiment_id"):
            by_exp[r["experiment_id"]].append(r)

    rows = []
    for eid in sorted(by_exp):
        rs = by_exp[eid]
        controls = sorted({r["control_of"] for r in rs if r.get("control_of")})
        if len(controls) != 1:
            continue
        ctrl = controls[0]
        crs = by_exp.get(ctrl)
        declared = any(
            PAIRED_DECLARED_RE.search(
                (r.get("notes") or "") + json.dumps(r.get("delta_declaration") or {}, ensure_ascii=False)
            )
            for r in rs
        )
        base = {
            "experiment_id": eid,
            "control_of": ctrl,
            "paired_declared": declared,
            "n_runs_injection": len(rs),
        }
        if not crs:
            rows.append(
                {
                    **base,
                    "pairable_now": False,
                    "blocking_reason": "control_experiment_not_in_index",
                    "pairable_after_dedup": False,
                    "dedup_rule": "",
                    "n_runs_injection_pairable": 0,
                }
            )
            continue

        ia = Counter(r["seed"] for r in rs if r["seed"] is not None)
        ib = Counter(r["seed"] for r in crs if r["seed"] is not None)
        imax = max(ia.values()) if ia else 0
        cmax = max(ib.values()) if ib else 0
        match = set(ia) == set(ib)
        # paired は共通 seed（積集合）で取る。両側とも 1 本ずつある seed の数。
        common = set(ia) & set(ib)
        usable = {s for s in common if ia[s] == 1 and ib[s] == 1}

        if not ia or not ib:
            reason = "seed_missing"
        elif not common:
            reason = "no_common_seed"
        elif len(usable) >= 2:
            reason = ""
        elif cmax > 1 and imax > 1:
            reason = "both_multi_run_per_seed"
        elif cmax > 1:
            reason = "control_multi_run_per_seed"
        elif imax > 1:
            reason = "injection_multi_run_per_seed"
        else:
            reason = "too_few_common_seeds"

        # seed ごとに 1 本へ畳んだ場合、共通 seed が 2 つ以上あれば paired になる
        after = len(common) >= 2
        rows.append(
            {
                **base,
                "pairable_now": reason == "",
                "blocking_reason": reason,
                "pairable_after_dedup": after,
                "dedup_rule": "one_run_per_seed_by_max_seq" if after and reason else "",
                "n_seeds_injection": len(ia),
                "seeds_injection": ",".join(str(s) for s in sorted(ia)),
                "runs_per_seed_max_injection": imax,
                "n_runs_control": len(crs),
                "n_seeds_control": len(ib),
                "seeds_control": ",".join(str(s) for s in sorted(ib)),
                "runs_per_seed_max_control": cmax,
                "seed_set_match": match,
                "n_seeds_common": len(common),
                "n_seeds_paired_now": len(usable),
                "seeds_only_in_injection": ",".join(str(s) for s in sorted(set(ia) - set(ib))),
                "seeds_only_in_control": ",".join(str(s) for s in sorted(set(ib) - set(ia))),
                # 畳めば対応が付く注入側 run の本数（対照に同じ seed があるもの）
                "n_runs_injection_pairable": sum(n for s, n in ia.items() if s in ib),
            }
        )
    return PAIRED_FEASIBILITY_COLUMNS, rows


PER_CLASS_COLUMNS = [
    "ledger_key",
    "group",
    "step",
    "seed",
    "split",
    "host",
    "excluded",
    "per_class_kind",
    "per_class_metric",
    "class_name",
    "value",
    "is_nan",
]


def build_per_class_long(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """per_class を long 形式（1 行 = 1 run × 1 クラス）に展開する。

    per-class の値は runs/*.json にしか無く、index.csv には件数しか出ていない。
    横断分析のたびに 573 ファイルを開くのは実務上使えないため、1 ファイルで配布する。

    ★ tool (AP, 15 クラス) と phase (F1, 9 クラス) は **絶対に混ぜて集計しない**。
      同一ファイルに入れるが per_class_kind / per_class_metric で必ず分離できる。

    NaN は空欄にして標準 CSV として妥当にし、「元が NaN だった」という情報は
    is_nan 列に保持する（GT 不在クラスの意味を失わないため）。
    """
    rows = []
    for r in sorted(records, key=lambda x: x["ledger_key"]):
        pc = r.get("per_class")
        if not pc:
            continue
        nan_set = set(r.get("per_class_nan_classes") or [])
        for cls in sorted(pc):
            rows.append(
                {
                    "ledger_key": r["ledger_key"],
                    "group": r["group"],
                    "step": r["step"],
                    "seed": r["seed"],
                    "split": r["split"],
                    "host": r["host"],
                    "excluded": r["excluded"],
                    "per_class_kind": r["per_class_kind"],
                    "per_class_metric": r["per_class_metric"],
                    "class_name": cls,
                    # _denan 済みなので NaN は None。CSV では空欄になる。
                    "value": pc[cls],
                    "is_nan": cls in nan_set,
                }
            )
    return PER_CLASS_COLUMNS, rows


# --------------------------------------------------------------------------- #
# 出力
# --------------------------------------------------------------------------- #
RUNINDEX_README = """# runindex/ — experiments/ から収穫した横断インデックス

**これは派生物です。手で編集しないでください。**

```bash
make runindex      # runindex/ 全体をゼロから再生成する
```

生成元は `tools/harvest_runindex.py`。入力は `experiments/**` のみで、
出力は入力が同じなら常に同じになります (冪等)。

## ファイル

| ファイル | 内容 |
|---|---|
| `index.csv` | 1 行 = 1 **run** の横断インデックス。`runs/*.json` から導出 |
| `per_class.csv` | 1 行 = 1 run × 1 クラス。per-class を long 形式で 1 ファイル化 |
| `experiments.csv` | 1 行 = 1 **実験**（seed 集約 + 対照 Δ + §10.1 判定）。論文 Table の 1 行に対応 |
| `verdicts.csv` | 1 行 = 1 実験 × 1 指標 の §10.1 判定（母集団σ / 標本σ の両方） |
| `runs/<ledger_key>.json` | 正規化済みの run 記録 |
| `host_aliases.json` | host 正規化の対応表 |
| `metric_aliases.json` | 指標名の表記ゆれ統合表 |
| `anomalies.md` | 規約から外れたもの・判断を保留したものの一覧 (人間が読む) |
| `anomalies/val_test_pairs.csv` | test 評価を持つ run の val/test 対応表 (縦持ち) |
| `anomalies/paired_feasibility.csv` | paired-σ の宣言と実行可能性の差 (1 行 = 1 実験) |
| `anomalies/dedup_sensitivity.csv` | seed 代表値の取り方 (mean/latest/first) で判定が動くかの感度分析 |
| `anomalies/determinism_audit.csv` | 学習スクリプトの決定性制御の棚卸し (1 行 = 1 スクリプト) |
| `anomalies/within_vs_between_seed.csv` | 同一条件反復と seed 間のばらつきの比較 (1 行 = 1 実験 × 1 指標) |
| `anomalies/backlog.md` | 本タスクの範囲外として起票した未着手事項 |

## index.csv の列

| 列 | 意味 |
|---|---|
| `metric.<name>` | **primary (= `split` 列が指す側。実質 val) の値** |
| `metric_test.<name>` | **test 側の値**。別列なので既存列の意味は変わらない |
| `has_test` | test 評価を持つか。`true` の run だけ `metric_test.*` が埋まる |
| `metrics_primary_split` | `metric.*` が実際にどの split 由来か。`split` 列と一致する |
| `experiment_id` | seed 集約の単位。`experiments.csv` と結合するキー |
| `arm` / `control_of` | 注入か対照か / 対照とする実験 |
| `frozen_source_tag` | 凍結特徴の抽出元。**run 名にも `command.sh` にも現れない条件軸** |

`metric.*` だけを見ると test 評価の存在に気づけません。
val と test は大きく乖離するため、下流解析では `has_test` で分岐してください。
乖離の実測は `anomalies.md` §13.1 と `anomalies/val_test_pairs.csv` にあります。

## per_class.csv（目的①: per-class の横断分析）

`ledger_key` で `index.csv` と結合できます。単独でも分析できるよう
`group` / `step` / `seed` / `split` / `host` / `excluded` を再掲しています。

> **⚠️ `tool` と `phase` を混ぜて集計しないでください。**
> `per_class_kind=tool` は術具 15 クラスの **AP**、
> `per_class_kind=phase` は工程 9 クラスの **F1** です。指標の種類が違います。
> 元ファイルはどちらも `per_class_ap.json` という名前なので、名前では判別できません。
> 必ず `per_class_kind` / `per_class_metric` で分離してください。

`value` が空欄の行は元が `NaN`（`is_nan=true`）。術具側の `NaN` は
**val split に GT が 1 件も無いクラス**であり 0 ではありません。

## experiments.csv（目的②: 機構・条件の横断比較と回帰）

1 行 = 1 実験 = seed をまたいで束ねた 1 条件。

| 列 | 意味 |
|---|---|
| `n_runs` / `n_seeds` / `seeds` | 集約した run 数・seed 数・seed 一覧 |
| `runs_per_seed_max` | 同一 seed の run 数の最大。**> 1 は再実行か条件混在の徴候** |
| `n_command_variants` | `command.sh` 引数の種類数。**> 1 なら条件が混在している** |
| `hosts` | 使われた host。**複数なら交絡の可能性がある** |
| `<metric>_mean` / `_min` / `_max` / `_n` | seed 集約 |
| `<metric>_pstd` / `<metric>_sstd` | **母集団σ (ddof=0) / 標本σ (ddof=1)** |
| `arm` / `control_of` | 注入 / 対照。`control_of` は対照実験の `experiment_id` |
| `delta_<metric>` | Δ = 注入 − 対照。`control_of` が確定した実験のみ |
| `delta_pstd_<metric>` / `delta_sstd_<metric>` | Δ の σ（母集団 / 標本） |
| `abs_delta_over_sigma_<metric>` | **\\|Δ\\| / `delta_pstd_<metric>`**（母集団σ基準） |
| `delta_method` | `paired` か `unpaired` か。**混同してはいけません** |
| `delta_sigma_source` | `paired` / `unpaired_pooled` |
| `control_note_value` | `notes.md` に引用されている基準値（実測との突き合わせ用） |

### σ の読み方（必読）

`delta_method` によって σ の意味が変わります。

| `delta_sigma_source` | σ の定義 |
|---|---|
| `paired` | seed ごとの差の σ。seed で対応が付く分の変動が相殺される |
| `unpaired_pooled` | √(σ_注入² + σ_対照²)。**paired-σ より大きく出る保守的な推定** |

したがって **`unpaired_pooled` で σ 条件を満たせば `paired` でも満たします**（逆は言えません）。

> ### ⚠️ σ は「seed 間のばらつき」ではありません
>
> **σ は「同一条件の反復のばらつき」と「seed を変えたときのばらつき」を
> 合成したもの**です。学習が決定的でないため、同じ設定で回し直すだけで
> 結果が変わります（`anomalies.md` §25 / §26）。
>
> `sigma_interpretation` 列で判別してください。
>
> | 値 | 意味 |
> |---|---|
> | `seed_effect` | 同一条件反復のばらつき < seed 間のばらつき。σ は概ね seed 効果 |
> | `mixed_with_nondeterminism` | **逆転している。σ は主に非決定性を測っている** |
> | `unknown` | 反復が無く判定できない |
>
> 実測では `control_of` を持つ 136 実験のうち **123 が `mixed_with_nondeterminism`** です。

現状 **136 実験中 134 が `unpaired_pooled`** です。対照実験に同一 seed の
再実行が畳まれずに残っているためで、詳細と全件は
`anomalies.md` §22 と `anomalies/paired_feasibility.csv` にあります。

母集団σと標本σは n=3 で √(3/2)=1.2247 倍違いますが、**実データでは
1σ / 2σ 基準の判定は 1 件も変わりません**（§21.1）。判定に標本σを使いたい場合は
`delta_sstd_<metric>` で割り直してください。

## 注意

- `runs/*.json` のファイル名は `run_id` (ディレクトリ名) ではなく
  `ledger_key` (experiments/ からの相対パス由来) です。
  ディレクトリ名は 6 種が 3 箇所ずつ衝突するためです。
- `split` は次の順で確定します。**推測値は入れません。**
  1. 指標キーの形式 (`val/…` / `test_…` / `phase_…` + 学習スクリプトのコード)
  2. `command.sh` / `config.yaml` / `eval_recipe.eval_split`
  3. 正本 M2研究計画 §16.7 の既定 (`metrics.json` は全て val)
  由来は `provenance.split` に入ります。指標が 1 つも無い run は `null` です。
- 元データの `NaN` は標準 JSON として不正なため `null` に変換しています。
  どのクラスが `NaN` だったかは `per_class_nan_classes` に保持しています。
- `per_class_ap.json` は名前に反して **中身が F1 の群が 500 run** あります。
  必ず `per_class_metric` 列 (`AP` / `F1` / `unknown`) で判別してください。

## 生成ホストによる差異

harvester はディスクを走査するため、**どのホストで `make runindex` を
実行するかで結果が変わる**（backlog B-29 / BL-exclusion-rules-exact-match）。

本 runindex は **ilya（ディスク 720 = git 追跡 720、退避 0）**で生成している。
lecun / efros / Andrew には git 管理外の退避 run（`.gitignore:143-162` で除外、
合計 ~5.6GB）がディスク上に存在し、そこで生成すると
`superseded` / `aborted_run` の除外が追加で現れる。

**再生成は ilya で行うこと。** 他ホストで回すと index が食い違う。
"""

BACKLOG = """# backlog — 本タスクの範囲外として起票した未着手事項

**これは派生物です。手で編集しないでください**（`tools/harvest_runindex.py` が生成）。

指示書 #02 §0「明示的にやらないこと」に該当するため、着手せず記録だけしたもの。
いずれも価値はあるが**監査・整備であって分析可能性を上げない**ため、
分析基盤（`index.csv` / `per_class.csv` / `experiments.csv`）の完成を優先した。

| id | # | 事項 | 分かっていること | 着手の前提 |
|---|---|---|---|---|
| BL-git-commit-existence-audit | B-1 | 573 run の `git_commit.txt` 実在性の全件検査 | `t1b_phasefilm_{001,002}` は記録された commit `a697d90` に `scripts/postprocess_t1b.py` が存在せず、**記録された commit では再現できない**ことが確認済み。他 571 run は未検査 | 全件 `git cat-file` する走査を書く。`experiments/` は読み取りのみ |
| BL-b2b-rescore-entrypoint-unknown | B-2 | `b2b_rescore_alpha{0.5,1.0,2.0}` の entrypoint 特定 | `verify_no_dummy_metrics.py` の死角スキャンが新規に検出。`command.sh` に python 呼び出しが無く、どのコードが mAP を書いたか不明 | 3 run の `command.sh` / `notes.md` / ログを個別に読む |
| BL-notion-ledger-reconciliation | B-3 | Notion 実験Run台帳との run_id 単位の突合 | 母数が 616 か 739 か未確定（§14）。データソース重複・フィルタ付きビュー・DB 重複はいずれも排除済み。`Status='failed'` が 0 件であることは母数に依らず確定 | Notion のクエリ利用上限の解除、または `.env` の `NOTION_API_KEY` 使用の承認 |
| BL-dummy-trainer-removal | B-4 | dummy Trainer の除去 | `src/egosurgery/engines/trainer.py` が乱数で per-class AP を生成し `mAP` として書く。混入は現時点 0 件と検証済みだが**コードは残っている**（§11） | 学習コードの変更にあたるため、本タスクでは触れない |
| BL-experiments-readme-outdated | B-5 | `experiments/README.md` の更新 | 規定は 17 種の step 識別子だが実データには 156 種ある（§12）。観測された family は b1 / b2a / b2b / t1a / t1b / taux / haux / hires | README は規約側の文書であり、実データに合わせて書き換えるかは方針判断 |
| BL-nonstandard-group-adapter | B-6 | 非標準群の adapter | `analysis` / `detector_improve` / `audit` / `ablations` / `final` / `g2_main_*` は `metrics.json` を持たず収穫できない（§9）。取りこぼした run は 0 件（そもそも run 構造ではない） | 群ごとにファイル形式が違うため個別の読み取りが要る |
| BL-ledger-key-rename | B-7 | `ledger_key` フィールド名の改名 | `ledger/` → `runindex/` の改名後も、フィールド名 `ledger_key` は 573 個の JSON と `index.csv` 第 1 列に残っている | スキーマ変更になるため利用側の合意が要る |
| BL-b2a-oracle-noise-name-mismatch | B-8 | `b2a_ro_oracle_noise000` の名前と実態の食い違い | 名前は noise 0.00 を示すが `--tool-noise-rate` は 0.05/0.10/0.20/0.30 の 4 通り（§7.3）。原因は `scripts/run_b2a_ro_oracle_noise_sweep.sh` のタグ生成が `bc` に依存しており、`bc` 不在時に全水準が `000` に潰れること。実測 accuracy も 0.9549 / 0.9435 / 0.9023 / 0.8106 と水準に応じて単調減衰しており、4 水準であることを独立に裏付ける | ディレクトリ名の改名は `experiments/` の変更にあたるため不可。正本側での扱いを決める必要がある |
| BL-sigma-convention-unification | B-9 | σ の規約統一（**判断: 保留**） | `S4 base` が母集団σ `±0.0028` と標本σ `±0.0034` の 2 通りで引用されている（§18.2）。**利用者の判断で「両方出し続ける」ことになった**（2026-08-01）。`experiments.csv` は `verdict_10_1`（母集団σ）と `verdict_10_1_sstd`（標本σ）を並べ、食い違いを `verdict_10_1_agree=False` で検出する。実測では主指標で 1 件、全指標で 4 件のみ食い違う | **論文に数値を出す段階で必ず決める。**それまでは両方を保持する |
| BL-paired-sigma-representative-run | B-10 | **paired-σ を可能にする「seed ごとの代表 run」規約** | 実測（§22）: `control_of` が確定した 136 実験の**全て**が paired-σ 判定を宣言しているが、実際に計算できるのは **2 実験**。阻害原因は `control_multi_run_per_seed` 119 / `seed_set_differs` 9 / 両方 4 / `both_multi_run_per_seed` 2。**seed ごとに代表 1 本を選ぶ規約を 1 つ足せば 125 実験で計算可能になる**（残り 11 は seed 集合が違うため不可）。注入側 439 run のうち 427 run は対照に同一 seed が存在する | 代表の選び方を決める（`transfer_delta_report.py` は seq 最大＝最新の再実行を採る実装がある）。決まれば harvester 側は機械的に適用できる |
| BL-asymmetric-seed-extension | B-16 | seed 789 / 1000 の非対称な拡張 | 全 615 run 中 12 run だけが seed 789/1000 を持ち、その 12 件すべてが `scripts/run_l3_seed5_extension.sh`（「3-seed→5-seed 化、paired-σ 強化」）の産物。同スクリプトは**注入側 6 variant のみを拡張し対照 (S4 baseline) を呼んでいない**ため片側だけ 5-seed になった。paired は共通 seed で取るので計算自体は成立する | 対照側も 5-seed 化するか、789/1000 を解析から外すかの判断 |
| BL-t1a-regiontraj-denominator | B-17 | `t1a_regiontraj` 系 3 実験の分母 | `config.yaml` は分母を `t1a_regiontoken base (同env efros paired)` と宣言しているが、`t1a_base_env`（efros・seeds 42/123/456・1 run/seed、config は `server_name` 以外一致）へ付け替えると追加計算なしで完全な paired になるという指摘がある | 分母の付け替えは研究上の判断。`config.yaml` の宣言に反するため harvester では変更しない |
| BL-two-sigma-conventions | B-18 | σ 規約の 2 系統併存 | `pstdev` 系 48 箇所（§10.1 判定・レポート層）と `stdev`/`ddof=1` 系 16 箇所（`scripts/analysis/*` の解析・監査層）が併存（§21.2）。**Δ の規約を監査する `delta_convention_audit.py` 自身が判定側と違うσを使っている**。**2026-08-04 に 3 系統目が加わった（ilya）。** `transfer_legacy` の 29 run は対照実験が宣言されておらず（`arm='unknown'` / `control_of=''`）`delta_pstd_*` が計算されないため、**run 内で対照が引かれた `injection_effect`（= Δ_inj − Δ_ctrl）の seed 間 σ（`injection_effect_pstd`）で §10.1 を判定している**。`sigma_source` 列（`paired_delta` / `within_run_seed_spread`）で出所を区別しており（`verdicts.csv` 1038 行の内訳: `paired_delta` 1027 / `within_run_seed_spread` 11）、σ を持つのに出所が空の行は 0 件だが、**σ の定義が 2 種類ある状態そのものは解消されていない**。判定に載せるのは `injection_effect` のみで、対照が引かれていない `delta_detection` / `delta_control` は `WITHIN_RUN_VERDICT_METRICS` から意図的に外している（`mAP` と同種の生の値であり §10.1 の Δ ではない）。なお `eval_recipe_id` が null の 199 run のうち、同じ構造（`arm='unknown'` で `delta_pstd` なし）の実験は**既存 720 run 側にも 34 件ある**（`g2_*` 30 / `hand2det_dev` 6 等）ため、この 3 系統目は transfer_legacy 固有ではなく、既存側にも同じ扱いを広げるかは未決。詳細は `docs/runindex_transfer_legacy_sigma_investigation_ilya_2026-08-04.md`。**2026-08-04 時点で σ に関する列は 4 系統ある。** ①`{metric}_pstd` / `{metric}_sstd` … seed 間の σ（母集団 / 標本）、②`delta_pstd_{metric}` / `delta_sstd_{metric}` … 実験間 paired Δ の σ、③`sigma_source` … σ の系統（`paired_delta` / `within_run_seed_spread`）、④`delta_sigma_source` … paired σ の計算方法（`paired` / `unpaired_pooled`）。③と④は軸が直交する（どの σ を使ったか vs paired σ をどう計算したか）ため別列にしているが、**列が増えたこと自体が「どの σ を見ればよいか」を分かりにくくしている**。統合はできないが、README で「§10.1 の判定に使うのはどれか」を明示する必要がある | 正本 §10.1 でσを定義したうえで、どちらかに寄せる |
| ~~BL-empty-delta-scaffold~~ | ~~B-19~~ | ~~空の Δ scaffold~~ | **解決済み**。`scripts/compute_delta.py` / `scripts/export_paper_tables.py` / `tools/generate_delta_report.py` は 3 つとも 0 バイトで scaffold コミット `af1fc58` 以来未実装だったため削除し、`make delta` / `make tables` を `runindex/` への案内に置き換えた（利用者の判断による） | — |
| BL-nondeterministic-training | B-20 | 🔴 **学習の非決定性が制御されていない（棚卸し完了）** | 同一 commit・同一 config・同一コマンド・同一 host の再実行が再現しない（`s4_phase_baseline_015` vs `_017` で macro_f1 が 0.7406 vs 0.6572）。**欠陥は 1 スクリプト固有ではなく体系的**で、CUDA を使う 13 本のうち `cuda_manual_seed` / `use_deterministic_algorithms` / `cudnn_deterministic` / `worker_init_fn` / `PYTHONHASHSEED` を設定している本は **0 本**（§26.1）。影響 run は 500。`control_of` を持つ 136 実験のうち **123 の σ が `mixed_with_nondeterminism`**（§26.4） | 学習コードの変更 + 再実行にあたるため本タスクでは触れない。**これを直さない限り paired-σ は seed 効果を測れない**。GPU 時間の判断が要る |
| BL-same-sign-condition-definition | B-21 | 「全 seed 同符号」条件の定義（**判断: 保留**） | dedup 後は「seed 平均どうしの符号が揃うか」を見ている（§27）。**利用者の判断で定義変更は保留**（2026-08-01）。理由は「σ の 123/136 が `mixed_with_nondeterminism` である以上、どの定義を採っても σ が汚染されているため、条件の定義より **B-20 の非決定性の解消が先**」。実測（accuracy / 134 実験）: 現状の seed 平均基準 125、全 run 組合せの厳格基準 124、符号一致率 100% は 124 | **B-20 の解消後に定義を決める。**それまで `delta_same_sign_<metric>`（seed 平均ベース）と `delta_n_seeds_<metric>` を出し続ける |
| BL-empty-engines-scaffold | B-22 | `engines/` の空 scaffold | `hooks.py` / `stage_b_trainer.py` / `stage_c_trainer.py` / `stage_d_trainer.py` / `validator.py` が 0 バイト（§26.2）。B-19 で削除した Δ scaffold と同じパターン | 使う予定が無ければ削除、あるなら実装 |
| BL-missing-entrypoint-script | B-23 | `train_net_egosurgery.py` が repo に無い | 3 run がこれを entrypoint にしているが実体が無い（`third_party/` は同期対象外）。`tools/train.py` も同様に 1 run（§26.2） | これらの run の決定性は確認できない。detectron2/detrex 側の配置を記録するか、run を除外対象にするか |
| BL-phase3seed-tsv-missing | B-11 | `logs/phase3seed_results.tsv` の欠落 | `scripts/paired_sigma_3seed.py` はこの TSV の `arm` 列（frozen / augstrong）を読んで paired-σ を出す設計だが、ファイルが repo に存在しない（`.gitignore` 対象）。arm 情報自体は `config.yaml` の `frozen_source.*` に残っており `frozen_source_tag` として収穫済み | TSV の復元、または `paired_sigma_3seed.py` を `runindex` 由来に切り替える |
| BL-runs-outside-experiments-dir | B-12 | 573 run の外側にある inj/ctrl ペア | `transfer/*_efros/` と `experiments/transfer/{hc,oracle_phase}_seed*/` に `injected_result.json` / `control_result.json` の対が 18 組あるが、`metrics.json` を持たないため収穫対象外。真の注入/対照ペアはここにある。**2026-08-04 に (a) 走査範囲の拡大で対処した（ilya）。** 直下 `transfer/` の **29 run** を `group='transfer_legacy'` として取り込み、`evidence_completeness='result_json_only'` / `metrics_source='result_json'` でフラグ化している。**6 点証跡が 0 件のため `eval_recipe_id` / `commit` は全 29 件 null、`host` は 16/29 のみ判別可能（efros 12 / lecun 2 / bengio 2、残り 13 は null）。** `per_class` は injected 側が空（`best_epoch=-1`）の 8 run で null。**σ を計算できないため `verdicts.csv` には載せていない**（`eval_recipe_id` が null で同一条件の束ねが定義できず、`delta_pstd_*` は全件 null）。`experiments.csv` には 12 実験として載る。null の理由は各 run の `provenance` に記録した（`not_determinable_no_git_commit_txt` 等）。**`hc_*` 3 run と `oracle_phase_*` 3 run は phase→det 方向の実測であり、研究計画が「実質空白」と記録していた領域そのものだった。** 実測（注入純効果 = Δ_inj − Δ_ctrl）: `oracle_phase`（`inject=ca`）seed42 **+0.005132** / seed123 **+0.003437** / seed456 **+0.003529**、`hc`（`inject=hc`）seed42 **+0.000000** / seed123 **+0.000873** / seed456 **+0.000334**。**σ が無いため §10.1 の判定は行っていない。** なお指示書が「`hc_*` 10 / `oracle_phase_*` 9」としていたのは `/tmp` 原本のファイル単位の数で、ディレクトリ単位では各 3。棚卸しの全文は `docs/runindex_instr10_stage1_transfer_inventory_ilya_2026-08-04.md` | 非標準群の adapter（B-6）と同じ作業 |
| BL-experiment-id-split | B-13 | 同一条件が別 `experiment_id` に分裂する組 | `description` / `split` / `frozen_source_tag` が同じで `step` だけ違う組がある（§17.2）。多くは `eval_recipe_id` による意図的分離 | 起動経路が同一かの判断が要るため harvester では決めない |
| BL-notes-frozen-source-false | B-14 | `notes.md` の凍結源記載が虚偽 | `s4_phase_baseline` の 55 件すべてが「凍結源: Relation-DETR seed42」と書くが、実際の `frozen_source.cache_dir` が違う run が 38 件（うち 24 件は seed 123/456）。`scripts/train_s4_tecno.py` の固定 f-string に由来。`config.yaml` の `frozen_source.seed` も 42 ハードコード | 学習コードの変更にあたるため本タスクでは触れない。過去の `notes.md` は `experiments/` 配下なので修正不可 |
| BL-g2-no-control-declaration | B-15 | g2_* 群に対照宣言が無い | 42 run が `config.yaml` を持たないため `control_of` を確定できない（§20）。`metrics.json` の `system` フィールド（base / bboxROI / shuffleROI）が arm を表す可能性はあるが、対照関係の明示ではない | 実験設計の意図を確認したうえで、`system` を arm として採用してよいか決める |
| BL-identity-runs-not-excluded | B-24 | `_identity_*` 24 run を Δ 分析から隔離する | `experiments/hand2det_dev/_identity_*`（18）と `experiments/transfer/_p0_identity_*`（6）は**初期化恒等性の検証**であり、`epoch=-1` / `mAP == init_mAP`（0.7302938994613697）/ `delta_detection=0.0` が**設計どおりの結果**。efros で 2026-08-02 に回収（commit `3952ac9`）。現状は除外フラグが付かないため解析対象に入り、**Δ=0 が実測値として Δ テーブルに混ざる** | `excluded=true` / `exclusion_reason='identity_check'` を harvester の除外ロジックに追加する。判定条件の候補は `epoch == -1 and mAP == init_mAP and delta_detection == 0.0`（`metrics.json` に 3 つとも入っている）。命名（`_identity_`）に依存させるかは要判断 |
| BL-frozen-source-self-contradiction | B-25 | 🔴 **凍結源の記述が 1 run の内部で矛盾している（+ 依拠キャッシュの破棄）** | `experiments/phase1/s4_phase_baseline_{010,011,012}_frozen_tecno_phase_baseline_aligndetr_seed{42,123,456}`（philip の成果。`891953c` に含まれ phase0 未マージ、PR #10 で回収予定）で、同一 run の 7 点証跡の**内部が直接矛盾**している。**ディレクトリ名** = `aligndetr` / **`command.sh`** = `train_s4_tecno_aligndetr.py` / **`config.yaml`** = `cache_dir .../aligndetr_seed42` に対し、**`notes.md` 見出し** = 「frozen Relation-DETR」/ **`metrics.json`** = `eval_recipe.test_cfg.backbone = relation_detr_resnet50_frozen_seed42`。3 対 2 で aligndetr 側が優勢に見えるが、**優勢だった側も実体と異なっていた**。philip の実測（B-27）により、実体は AlignDETR ではあるが **S0-frozen ではなく 2026-05-31 の通常学習 ckpt** と確定した。したがって `notes.md`（relation_detr）も `config.yaml`（align_detr の S0-frozen）も、**どちらも実体を正しく記述していない**。2026-07-03 15:55 の S0-frozen 学習が NCCL ALLREDUCE タイムアウト（`SeqNum=1`）で失敗し、`entry5.sh` が代替 ckpt で走らせたため（17:10〜17:20:02 に特徴を再抽出 → 17:20:54 / 17:21:02 / 17:21:09 に run 010 / 011 / 012 起動）。当初 ilya は「`.npz` のバイトサイズ（train 79458316 / val 12465940 / test 35092940）が Relation-DETR 版と完全一致するため中身では判別できず、`/tmp/queue_runner/train_s4_tecno_aligndetr.py` も消失しており断定不能」と報告したが、philip が `/tmp` の揮発物を保全したことで確定した。依拠した特徴キャッシュ `aligndetr_seed42` は 2026-07-05 に `.discarded_20260705` へリネームされている（破棄理由が記録されない構造問題そのものは B-27 で別途起票）。**本 run は philip が `INVALID.md` で無効と記録済み（`684eb42`）。一次証拠: `evidence/aligndetr_s0frozen_incident_20260703/`（19 ファイル。`entry5.sh` / `train_s4_tecno_aligndetr.py` / NCCL 失敗ログを含む）。**一方で **数値記録は健全**（2026-08-02 ilya 実測）: checkpoint の指標と `metrics.json` が 3 seed とも小数点以下全桁まで一致（seed42 `epoch=49` / `acc=0.8567656765676568` / `macro_f1=0.6351559658149464`、seed123 `epoch=36` / `acc=0.8422442244224423` / `macro_f1=0.5828472115684166`、seed456 `epoch=44` / `acc=0.8402640264026403` / `macro_f1=0.5929150228940421`）、`per_class_ap.json` も checkpoint の `phase_per_class_f1` と完全一致。**→ 不一致は指標側ではなくメタ情報（実験条件の記述）側にある。** 付随して判明: (1) この 3 run は philip の成果（`server.txt=philip` / `config.yaml` の `server_name: philip`）であり、ilya の「`891953c` 側の未回収成果」という報告は誤りで PR #10 が本筋。(2) `git_commit.txt` の `1a52c6f` は ilya が 2026-07-01 06:06 に clone した直後の HEAD であり**実行コードを指していない**（B-1 と同型）。(3) 凍結源は 3 run とも seed42 固定で、run 名の `_seed123` / `_seed456` は TeCNO 側の seed のみを指す（Δ の σ を seed 間分散として解釈する際に影響する） | **B-14 と根本原因が同一**（`train_s4_tecno*.py` の固定 f-string）。ただし B-14 が数えた `s4_phase_baseline` 55 件は runindex 収録分であり、phase0 未マージの本 3 run は**含まれていない**。また B-14 が `notes.md` / `config.yaml` の齟齬を指すのに対し、本件は **`metrics.json` の `eval_recipe` にまで誤りが波及**している点と、**依拠キャッシュが破棄済み**である点が新規。**runindex では `excluded=true` / `exclusion_reason='wrong_frozen_source'` とすべき**（philip の `INVALID.md` と整合させる）。着手は PR #10 のマージ後。`experiments/` 配下は実験時の記録として書き換えない。破棄の経緯は B-27 で判明済みのため、この 3 run を Δ の基準点に**使わないことは確定**。同型の既出: B-8（`b2a_ro_oracle_noise000` の名前と実態の食い違い）/ B-14 / B-24（arm 取り違え）。**run 名・メタ記述から実験条件を推定してはならない。** |
| BL-postprocess-t1b-arm | B-26 | 🔴 **`postprocess_t1b.py` のグロブが arm を取り違えている** | `scripts/postprocess_t1b.py:35` が `TRANSFER.glob("t1b_seed*")` を読み、**`trainable=all` / 3ep の run を `t1b_phasefilm_*` という名前で登録**している。実際の film arm（`trainable=film` / 6ep / `film_params=266880`）は `experiments/` に一件も登録されていない。実測による裏付け（2026-08-02, Bengio + 解析側）: 登録済み `t1b_phasefilm_001_seed123` は `epoch=-1` / `mAP=0.729178` で、`logs/t1b_seed123.log`（all/3ep, best=-1, mAP=0.7292）と一致し、`logs/t1b_film_seed123.log`（film/6ep, best=ep5, mAP=0.7314）とは不一致。`config.yaml` も `trainable: all` / `epochs: 3` と記載。**`experiments.csv` 上で `arm='injection'` と記録されているが、実体は注入なしの all arm である。** 未登録の film 6 run（seed 42/123/456 × inj/ctrl）は `logs/t1b_film_*` にログのみ残り、構造化結果 `t1b_result.json` は `/tmp` 出力（当時の `run_t1b.sh` が `T1B_WORK_DIR=/tmp/${TAG}` 固定）のため Bengio 側では消失済み。影響: runindex 上の `t1b_phasefilm` 2 run は step 名・arm ともに誤り。ただし README / Notion に記録された T1b-FiLM の純効果（s42/123/456）は film の実測値であり、**STEP B の分析結論には影響しない。登録経路だけが取り違えていた。**なお s456 の純効果はログ（`:.4f` 丸め）からは +0.0003 と読めるが既存記載は +0.0002 で、原本 JSON 由来の後者が正しい可能性が高い。**2026-08-04 追記（ilya 実測）**: この 2 run は `trainable=all` / 3ep の実測記録であり、**誤っているのは step 名と arm のラベルであって数値ではない**（seed123: `epoch=-1` / `mAP=0.7291778095772903`、seed456: `epoch=-1` / `mAP=0.721658691470358`。いずれも `init_mAP` と同値で `delta_detection=0.0`）。「all arm では 3ep で init を超えなかった」という**対照情報として参照する場合は、runindex ではなく本エントリと `experiments/transfer/t1b_phasefilm_{001,002}/metrics.json` を直接見ること**。`excluded=true` / `exclusion_reason='mislabeled_arm_all_not_film'` としているのは、`step='t1b_phasefilm'` / `arm='injection'` というラベルのまま Δ 分析に載せると FiLM の効果と誤読されるため。**また、根本原因はグロブではなく `run_t1b.sh` の TAG 命名と `DESC` の定数化にある（B-32 参照）。本エントリの見出し「グロブが arm を取り違えている」は不正確で、グロブだけを直しても再発する。** | `postprocess_t1b.py` のグロブと step 名の対応を修正する。既存 2 run は `step='t1b_all'` 等の正しい名前へ付け替えるか、`excluded` + `exclusion_reason='mislabeled_arm'` とするか要判断（`experiments/` 配下は変更不可のため runindex 側での扱いを決める）。**data そのものは書き換えない**（実験時の記録として保存する）。film 6 run の登録は、原本 `t1b_result.json` が lecun の `/tmp/t1b_film_*` に残っているかを先に確認してから（残っていれば 16 桁精度・per-class AP・`lr`/`film_lr` が無損失で回収でき、ログからの復元が不要になる）。同型の既出: B-8（`b2a_ro_oracle_noise000` の名前と実態の食い違い）/ B-14（`notes.md` の記載と実体の乖離）。**run 名から実験条件を推定してはならない。** また B-1 が指摘する「`t1b_phasefilm_{001,002}` は記録 commit `a697d90` では再現できない」も同じ登録経路に由来する（`postprocess_t1b.py` の初出は `ba3df41` で `a697d90` には存在しない。実測で確認済み） |
| BL-discarded-cache-no-reason | B-27 | 🔴 **破棄されたキャッシュに理由が記録されない** | `data/processed/**/*.discarded_*` が 3 件あるが破棄理由がどこにも無い（`data/processed/` が `.gitignore` 対象のため `git log -S` も効かない）。2026-08-02 に `aligndetr_seed42.discarded_20260705` の理由を再構成できたのは、`/tmp` の揮発性ファイル（`queue_runner/entry5.sh` / `aligndetr_s0frozen_logs/`）が偶然 40 日間生き残っていたためで、**再起動していれば永久に判明しなかった**。再構成の結果: 2026-07-03 15:55 の AlignDETR-S0-frozen 学習が NCCL ALLREDUCE タイムアウト（`SeqNum=1`）で失敗し、17:08 の `entry5.sh` が 2026-05-31 の通常学習 ckpt で代替した。その特徴で走った TeCNO 3 run（`s4_phase_baseline_{010,011,012}_..._aligndetr_seed{42,123,456}`）は宣言している S0-frozen 条件で走っておらず **無効**と判定（2026-08-02）。`excluded=true` / `exclusion_reason='wrong_frozen_source'` とすべき。残る 2 件（07-06 の `t1a_regiontoken` / `b2a_detsignal`）は理由**判別不能**だが、後継との npz 内容が md5 で不一致（同サイズ・同形状）であることは実測済み | 破棄時に `DISCARDED.md` を同梱する運用（`data/annotations/_deprecated/` と同じ方式）。2026-08-02 に 3 件へ遡って作成し、`.gitignore:15` が追跡を阻むため追跡コピーを `evidence/discarded_caches/` に置いた。実行痕跡は `evidence/aligndetr_s0frozen_incident_20260703/` に保全。B-8 / B-14 / B-24 / B-25 / B-26 と同じく宣言と実体の食い違いだが、本件は**実験条件そのものが意図と異なっていた**ケースであり、記録の誤りではなく実験の無効を意味する点が異なる |
| BL-legacy-prefix-must-not-exclude | B-28 | 🔴 **`_legacy_score_thr_0/` は `_` 接頭辞だが除外してはいけない** | `experiments/baselines/_legacy_score_thr_0/` の 33 run は退避規約と同じ `_` 接頭辞を持つが、**除外すると 11 検出器の S0 基準点の証跡が失われる**。実測（2026-08-02 / ilya / 統合ブランチ `chore/integrate-20260802`）: `experiments/baselines/s0_007_codetr_bbox_seed42/` は `metrics.json` を**持たない**（22 ファイル＝Syncthing 由来の `checkpoints` / `logs` / `predictions` のみ）のに対し、`experiments/baselines/_legacy_score_thr_0/s0_007_codetr_bbox_seed42/` は **7 点証跡フルセットを持つ**。legacy にしか証跡が無い `description` は 11 件（`aligndetr_bbox` / `codetr_bbox` / `dacdetr_bbox` / `dimaskdino_bbox` / `focusdetr_bbox` / `mrdetralign_bbox` / `mrdetrdino_bbox` / `relationdetr_bbox` / `stabledino_bbox` / `relationdetr_s0frozen_cocohead` / `relationdetr_s0frozen_neck_cocohead`）で、**直下に同じ `description` を持つ run は 0 件**。二重計上は起きていない: legacy の `experiment_id` は `eval_recipe` が異なるため非 legacy と重複せず、`experiment_id` の衝突は 0 件。`run_id` 重複 12 件はすべて `_smoke_prior` / `_wrong_split_8_2_3`（両方 `excluded=True`）と g2 の `base_*` / `bboxROI_*`（別グループ）で、legacy 由来は 0 件。導入は Andrew の `421e400`。なお `_` 接頭辞なのに `excluded=False` の run は全体で **57 件**あり、内訳は `_legacy_score_thr_0` 33（**除外してはいけない**）/ `_identity_*` 18 + `_p0_identity_*` 6（**B-24 が隔離対象として挙げているもの**）。**同じ `_` 接頭辞に正反対の要求が同居している。** | 🔴 **`EXCLUSION_RULES` を前方一致へ変更する際の直接の危険。** 現行は 4 マーカー（`_smoke_prior` / `_smoke_ddq` / `_wrong_split_8_2_3` / `_failed_s3_weighted`）の**完全一致**（`tools/harvest_runindex.py:50` および `classify_exclusion()` の `part == marker`）。`_` の一括除外や前方一致の対象に `_legacy` を含めてはならない。対処の候補: **(a)** `EXCLUSION_RULES` を明示リスト（除外すべきものだけを列挙）に保つ。前方一致にする場合も `_legacy_score_thr_0` を明示的に除外対象外とする。**(b)** ディレクトリ名を `legacy_score_thr_0`（`_` なし）へ改名する。ただし既存の `run_id` / `experiment_id` が変わるため影響範囲の確認が必要。**(c)** 退避と保管を接頭辞で区別する規約を作る（例: 退避は `_x_`、保管は `_keep_`）。関連: **B-24**（`_identity_*` 24 run は逆に隔離すべき）と**正反対の方向**の問題であり、`EXCLUSION_RULES` に触れる変更は両方を同時に満たす必要がある。`EXCLUSION_RULES` の問題そのものは **B-29** で起票済み。前方一致化の際は本エントリ（B-28）を必ず参照すること。 |
| BL-exclusion-rules-exact-match | B-29 | 🔴 **`EXCLUSION_RULES` が完全一致のみのため退避 run が解析対象に混入する** | `tools/harvest_runindex.py:50` の `EXCLUSION_RULES` は 4 マーカーのみ（`_smoke_prior` / `_smoke_ddq` / `_wrong_split_8_2_3` / `_failed_s3_weighted`）で、`classify_exclusion()` はパス構成要素の**完全一致**（`part == marker`）で判定する。そのため規約上の退避ディレクトリでも、この 4 つに文字列一致しない限り `excluded=False` のまま解析対象に入る。実測（2026-08-02 / ilya / 統合ブランチ `chore/integrate-20260802` の 720 run）: **`_` 接頭辞なのに `excluded=False` の run は 57 件**（`_legacy_score_thr_0` 33（Andrew の `421e400` 由来）/ `_identity_*` 18 / `_p0_identity_*` 6）。一方 `excluded=True` は 19 件のみ（`smoke_test` 7 / `known_bad_split` 6 / `failed_run` 6）。また harvester は git ではなく**ディスクを走査する**ため、「git で退避した＝解析から除外される」は成り立たない。二層は独立している（lecun 実測: ディスク 721 / git 追跡 687 / 差 34。ただしその 34 は git 上の退避であって runindex の除外とは別の話）。 | 🔴 **対処の際の必須参照**: **B-28**（`_legacy_score_thr_0` の 33 run は `_` 接頭辞だが**除外してはいけない**。11 検出器の S0 基準点の唯一の証跡であり、前方一致や `_` 一括除外を入れると消える）/ **B-24**（`_identity_*` 24 run は `excluded=true` / `exclusion_reason='identity_check'` とすべき。efros 起票）。対処の候補: **(a)** 除外すべきものを明示リストで列挙し続ける（現行方式の維持＋追加）→ 退避 dir を増やすたびに追記が必要で、漏れが再発する。**(b)** 前方一致にしたうえで `_legacy_score_thr_0` を明示的に対象外にする → B-28 の危険は回避できるが、例外が増えると同じ問題に戻る。**(c)** 退避と保管を接頭辞で区別する規約を作る（例: 退避 `_x_` / 保管 `_keep_`）→ 最も堅牢だが、既存ディレクトリの改名と `run_id` / `experiment_id` の変更を伴う。関連: **B-28**（逆方向の問題であり、**B-29 を直すと B-28 が壊れる**関係にある）。 |
| BL-sync-alert-message-inaccurate | B-30 | **`m2-sync.sh` のアラート文言「phase0更新失敗（未コミット変更と衝突）」が不正確** | 実際の失敗原因は「未追跡ファイルの上書き拒否」であり、追跡ファイルの変更ではない。2026-08-04 に未整備 5 ノード（`Hinton` / `adam` / `DL-Station` / `he` / `ian`）を調査したところ、5 台とも **追跡ファイルの変更 0 件**で、`git status` に出ていたのはすべて未追跡ファイル（Syncthing 由来の `logs/eval_meta_val.json` と `logs/val_metrics_by_epoch.json`）だった。件数は `Hinton` / `adam` / `DL-Station` / `he` が各 58 件、`ian` が 4 件。git は未追跡ファイルの上書きを**バイト単位で同一でも拒否する**ため `git merge --ff-only origin/phase0` が失敗し続けていた（アラート 28〜32 件 / 台）。`ian` だけ成功していたのは未追跡 4 件が phase0 に存在しなかったため。文言が誤っていたため、調査するまで「未コミットの成果が眠っている」と誤読された（実際は 5 台とも未追跡 `metrics.json` 0 件で、固有の実験成果はゼロ）。 | git のエラー出力を判別して文言を分ける。`untracked working tree files would be overwritten by merge` → 「未追跡ファイルと衝突（Syncthing 由来の可能性）」、`Your local changes to the following files would be overwritten` → 「未コミット変更と衝突」。なお `m2-sync.sh` は `~/bin/keeper.sh` から呼ばれる**外部管理スクリプト**であり、リポジトリの `scripts/sync/m2-sync.sh` を変更しても各ホストには自動配布されない。配布方法の確認が先に必要。 |
| BL-hostname-container-id-in-alerts | B-31 | **`SERVERNAME` 未設定のホストで、アラートログにコンテナ ID が記録され追跡不能になる** | `m2-sync.sh` は `SRV="${SERVERNAME:-$(hostname)}"` でホスト名を解決する。`DL-Station` は `hostname` がコンテナ ID `084f3b0911a2` を返すため、`SERVERNAME` 未設定の状態でアラート 29 件がこの ID で記録され、2026-08-03 時点ではどのマシンか判別できなかった（2026-08-04 に特定）。同じ問題は `philip` / `ilya` にもある（両者とも `hostname` が `aolab` を返す）が、こちらは `SERVERNAME` が設定済みのため顕在化していない。2026-08-04 時点で `SERVERNAME` 未設定だったのは `Hinton` / `adam` / `DL-Station` / `he` / `ian` / `efros` / `Andrew` の 7 台。うち `Hinton` / `adam` / `he` / `ian` / `efros` / `Andrew` は `hostname` が論理名と一致するためフォールバックしても正しい値になり、実害は `DL-Station` のみだった。 | 全ノードで `SERVERNAME` を設定する（2026-08-04 に未整備 5 ノードで実施）。加えて防御として、`hostname` が 12 桁の 16 進数（コンテナ ID の形式）に一致する場合はアラート行に警告を添えるか、そもそもアラートを出さずに設定不備として別扱いにする。判定は `[[ "$SRV" =~ ^[0-9a-f]{12}$ ]]` で足りる。 |
| BL-run-t1b-tag-ignores-arm | B-32 | 🔴 **`run_t1b.sh` の TAG が `--trainable` を反映しないため、arm が出力先に現れない** | `scripts/run_t1b.sh:20-21` の TAG は `--zero-ctx` の有無しか見ておらず、`--trainable film` でも `--trainable all` でも**出力先は同じ `t1b_seed{N}`** になる（`T1B_WORK_DIR="$BODY/experiments/transfer/${TAG}"`、:28）。加えて `scripts/postprocess_t1b.py` の `DESC = "t1b_phasefilm"`（:29）と `step="t1b_phasefilm"`（:69, :71）が**定数**のため、グロブが何を拾っても必ず `t1b_phasefilm` の名前で登録される。**B-26 が「グロブの取り違え」としたのは不正確で、根本原因は TAG と `DESC` の設計にある。グロブだけを直しても再発する。** 履歴で確認した意図（2026-08-04 / ilya）: `postprocess_t1b.py` の初出 `ba3df41` の docstring は「`train_t1b.py` は seed 毎に注入 run（`/tmp/t1b_seed{N}`）と §4.6 対照 run（`/tmp/t1b_zeroctx_seed{N}`）の `t1b_result.json` を出す」と述べており、`DENOM` も「①学習FiLM phase→det」と書いている。**グロブは「`train_t1b.py` の出力ディレクトリを拾う」意味しかなく、arm を選別する意図は元から無い。** `0ea33ca` は `/tmp` → `experiments/transfer/` の移行のみでパターンは不変。副次的に判明: `run_t1b.sh:29` で `--epochs 6` が固定されているのに登録済み 2 run は `epochs=3` であり、**`run_t1b.sh` 経由ではない起動があった**ことを示すが経路は**判別不能**（`command.sh` は `postprocess_t1b.py` が組成したもので実際の起動コマンドではない）。これは B-1 と同型。 | **(i)** TAG に `--trainable` を反映させる（例: `t1b_film_seed{N}` / `t1b_all_seed{N}`）、または **(ii)** `postprocess_t1b.py` の `DESC` を実データの `trainable` から決める。**(i) が根本的**だが `run_t1b.sh` は**学習の起動スクリプト**であり、指示書 #10 の「学習・評価コードには触れない」範囲を超える。現在 `experiments/transfer/t1b_seed*` は **0 件**で即座の影響はなく、修正は将来の再実行に対する予防である。着手時は `scripts/run_t1b.sh` / `scripts/postprocess_t1b.py` の 2 箇所を同時に直すこと（片方だけでは再発する）。関連: **B-26**（同じ事象を index 側から見たもの。既存 2 run は `mislabeled_arm_all_not_film` で除外済み）/ **B-1**（記録 commit で再現できない run）。 |
| BL-backlog-pipe-breaks-columns | B-33 | 🔴 **BACKLOG の Markdown 表に半角パイプを含む本文を書くと列数が壊れる** | 2026-08-04 の B-18 追記で `paired_delta` と `within_run_seed_spread` を**半角パイプ文字で区切って**書いたところ、それがセル区切りと解釈され、当該行だけ列数が 6 になり表全体で `{8, 7}` の 2 種類になった（区切り文字数ベース）。**`py_compile` は通る** — BACKLOG は Python から見れば単なる文字列であり、構文チェックは表構造の破損を一切検出しない。AST 検証（`ast.literal_eval` で `BACKLOG` の値を取り出し、先頭が `BL-` の行を `str.split` して列数を数える）でのみ検出できた。**バッククォートで囲んでもエスケープされない**点に注意（コード片として書いても表は壊れる）。同種の事故は **2026-08-02 にも発生**しており（B-29 起票時に行末の閉じ区切りを落とし、列数が 3 になった）、**2 回とも AST 検証だけが捕まえている**。 | **(i)** 本文で区切りが必要なときは `/` や全角に置換する運用を `runindex/README.md` に明記する、または **(ii)** BACKLOG を Markdown 表ではなく構造化データ（`list[dict]` 等）で持ち、`backlog.md` はそこから生成する。**(ii) が根本的**だが既存 34 エントリの移行が要る。当面は **`make runindex` に AST 検証を組み込み、列数が 1 種類でなければ `exit 1` とするのが安価**（現状は人間が検証コマンドを手で流しており、流し忘れると壊れたまま commit される）。関連: B-18（この事故が起きた対象エントリ）。 |
| BL-ledger-key-namespace-collision | B-34 | 🔴 **`ledger_key` の名前空間が `transfer` と `transfer_legacy` で重なる** | `ledger_key` はパス区切りを `__` に置換して作る。直下 `transfer/hc_seed42` は `str(rel)` から、`experiments/transfer/hc_seed42` は `str(rel_from_exp)` から作られるため、**どちらも `transfer__hc_seed42` になる**。2026-08-04 時点で `index.csv` の `ledger_key` 重複は **0 件（実測）** で実害は出ていないが、これは両者の run 名がたまたま重ならないためであり、規約で保証されているわけではない。将来 `experiments/transfer/` に直下 `transfer/` と同名の run が作られると、`runindex/runs/<ledger_key>.json` が**静かに上書きされる**（例外も警告も出ない）。`index.csv` 側は 1 行しか出ないため、run が 1 件消えたことに気づけない。 | `transfer_legacy` の `ledger_key` を `transfer_legacy__` 接頭辞にする（`build_transfer_legacy_record` の `str(rel).replace("/", "__")` を変更）。既存の `runs/*.json` のファイル名が 29 件変わるため、**再生成時に 29 件の rename が発生する（削除ではないことを commit メッセージに明記すること）**。`index.csv` の `ledger_key` を参照している外部の記録（`docs/` 配下の報告書等）があれば追随が必要。あわせて、`ledger_key` の重複を検出したら警告する検査を harvester に入れておくと同種の事故を防げる。関連: B-12（この取り込みを行ったエントリ）/ B-7（`ledger_key` のフィールド名改名）。 |
| BL-third-party-drift-detection | B-35 | `third_party/` の drift 検出（配布はしない方針で確定） | `third_party/` は `.gitignore:132-133` と `.stignore:35` の両方で除外され、git にも Syncthing にも乗らない。2026-08-05 に 4 案を比較し、**(d) 配らない + drift 検出**を採ることに決定した。却下した案と理由: **(a) Syncthing で `.git` だけ除外して配る** → `.git` 除外自体は既存ルール（`.stignore:9` の単独パターン）で効く見込みだが、`.stglobalignore` の 1 回のタイプミスが 30 分で 11 台に波及し、実 git を持つ philip / efros / lecun の 3 台のオブジェクト DB が同時に汚染される。checkpoint も一緒に配ることになり容量も膨らむ。**(c) submodule 化** → 🔴 9 fork すべてが upstream 直接 clone（Visual-AI/Mr.DETR / xiuqhou/Relation-DETR / Sense-X/Co-DETR 等）で team fork ではない。submodule は upstream の commit しか指せず、upstream 改変 4 本と未追跡の独自実装 100+ file が一切乗らない。さらに同一 commit `b485955` でホスト間の dirty が異なり（efros 35 / lecun 25 / philip 8）、どれを正とするかは研究上の判断。snapshot は復元可能であることを 2026-08-05 に実測で確認した（初めての検証）: `git clone --depth 50 <upstream>` → `checkout <記録commit>` → `git apply --check upstream_mods.patch`（exit 0）→ `git apply` → `tar xzf`。README が「実行を想定していない」と書いていた手順が実際に通った。 | `m2-sync.sh` に「ディスク上の `third_party` と `third_party_snapshot/<host>/` の provenance がずれていないか」の検出を追加する。`third_party` を使う 4 台（lecun / efros / philip / Andrew）限定。ずれたら `sync-alerts.log` にアラートを出し、**snapshot の更新自体は自動 commit にしない**（何を「正」とするかは研究上の判断のため）。🔴 実装前に決める必要がある設計判断: 検出の粒度を commit ハッシュのみにするか、patch + 未追跡ファイルの内容ハッシュまで見るか。前者は軽量だが「同じ commit でも dirty 内容が違う」実態（efros 35 / lecun 25 / philip 8）を見逃す。未計測: `third_party` 配下の checkpoint 総量（案 (a) の容量評価に必要だったが全台の `du` が無いため出せなかった）。関連: `.git` 除外が入れ子に効くことは ilya では実地検証できなかった（ilya に `third_party` の `.git` が無いため）。philip / efros / lecun での再検証が必要だが、(a) を却下したため優先度は低い。 |
| BL-harvester-scan-is-host-dependent | B-36 | 🔴 **収穫器はディスクを走査するため、同じ commit でもホストによって索引の行数が変わる** | `EXPERIMENTS = REPO_ROOT / "experiments"` を走査対象としており、git の追跡状態を見ていない。`.gitignore` で退避されたディレクトリはホストごとに有無が違うため、**同一 commit から再生成しても `index.csv` の行数が一致しない**。2026-08-07 に lecun で実測（commit `c905f19` 時点、`T-2026-08-09-run-wiring-verification`）: commit 済みの `index.csv` は 749 行だったが `make runindex` で **784 行**になった（+35）。内訳は**新規 run 1 件と、lecun のディスクにのみ存在する退避済み 34 件**である。退避 34 件の除外理由の内訳は `smoke_test` 19 件 / `superseded` 6 件 / `failed_run` 5 件 / `aborted_run` 4 件で、**34 件すべてに `excluded=True` が付いた**（B-28 と B-29 の修正が効いており、除外規約そのものは正しく働いている）。したがって**解析対象（`excluded=False`）の増分は 701 から 702 への +1 のみ**であり、Δ 分析への影響は無い。削除された run は 0 件。併せて `experiments.csv` は 206 から 215、`per_class.csv` は 6210 から 6588 に増え、`verdicts.csv` は 1038 のまま不変だった。既存 run の JSON も 12 件変化したが、**変化は `harvest_warnings` の文言のみ**（同一 `(group, step, description, split)` 内の `eval_recipe_id` の食い違いが「2 通り」から「3 通り」へ）で、指標・`experiment_id` の分離子はいずれも不変。副作用として `make task-validate` の L2-8 が「起票時 749 → 現在 784（分母が動いています）」を WARN で出すようになり、`meta.created_from.counts` を根拠にする検査はホスト差で恒常的に警告する。再現手順は、退避ディレクトリを持つホストで `make runindex` を実行し commit 済みの `index.csv` と行数を比べる。 | **索引の同一性は現状保証されていない。** 取りうる方針は次の 3 つ。**(i)** 走査対象を git 追跡下の run に限る（退避 run が索引から消えるため、退避の記録が失われる）。**(ii)** 退避ディレクトリの一覧を規約化して全ホストで同一に保つ（運用負荷が高く、既に 34 件の差がある）。**(iii)** 索引はホスト依存の生成物と割り切り、正本を 1 ホストに定める（どのホストを正本とするかが未定）。**どれを採るかが決まるまで、行数の差だけを見て「除外漏れ」と判断してはならない。** 判断には `excluded` 列で切り分けた解析対象の増分を使う。関連: B-12（`experiments/` の外にある run）/ B-28 / B-29。 |
| BL-autosync-log-only-on-abort | B-37 | 🔴 **自動同期の記録は中断時にのみ書かれるため、記録が無いことは不発火を意味しない** | `src/egosurgery/utils/git_autosync.py` の `_write_alert` が呼ばれるのは中断の経路だけである。具体的には `git add` の失敗 / 秘匿パスの denylist 一致 / 秘匿内容の正規表現一致 / staged 単一ファイルが 5 MB 超 / commit の失敗 / push の失敗（`committed_no_push`）の 6 つ。**`_skipped()` は書かない**（kill-switch の `EGOSURGERY_AUTOSYNC` 無効値 / repo 外 / `exp/*` 以外のブランチ / deploy key 未構成 / stage 差分が空）。**成功時（`action=pushed`）も書かない。** つまり `~/claude-sync/sync-alerts.log` に `git_autosync` の行が無いことは、「発火しなかった」ではなく「**中断が一度も起きなかった**」を意味する。2026-08-07 に lecun で実測（`T-2026-08-09-run-wiring-verification`）: `finalize()` から初めて発火し commit `25ea5ef` を作って push まで到達したにもかかわらず、`sync-alerts.log` の `git_autosync` 行は **0 件のまま**だった。**この性質を知らずに書かれた検査条件が実際に誤りを生んでいる。** 同 SPEC は「記録に該当行が無い場合、発火していない」と判定させており、指示どおりなら**発火したのに不発火と報告するところだった**。発火を確認する正しい方法は、`_build_commit_message` が subject 末尾に付ける `[auto-sync]` を commit 履歴で探すこと、および遠隔との差を見ることである。すなわち `git log --oneline --grep='auto-sync'` と `git rev-list --count origin/<branch>..HEAD` を使う。 | **(i)** 成功時と見送り時にも記録を書く（`sync-alerts.log` は Syncthing で全台に配られるため、全ホストの全 run 分が積み上がる肥大を許容できるかの判断が要る。現状 826 行）。または **(ii)** 記録の意味を `runindex/README.md` と `tasks/README.md` に明記し、発火の判定には commit 履歴を使う手順を手順書側へ書く。**(ii) は本 task で着手済み**（`tasks/README.md` に「自動同期の確認方法」を追加）。(i) を採る場合は、記録の粒度を run 単位ではなくホスト単位の集計にする等、肥大を抑える設計が要る。関連: B-30（アラート文言の不正確さ）/ B-31（アラートログのホスト名）。 |
| BL-ignore-does-not-protect-index | B-38 | 🔴 **版管理の無視設定は索引を保護しない。収穫器はファイルシステムを直接走査し、無視設定を参照しない** | `harvest_runindex.py` の走査は `EXPERIMENTS.rglob("metrics.json")` の親を run とするもので、`git check-ignore` への照会も `.gitignore` の解釈も一切持たない（2026-08-09 に 3 通りの探し方で確認: check-ignore / gitignore の語での検索、`subprocess` 呼び出しの検索、走査起点の検索。いずれも該当なし）。**影響**: 無視設定を足しても索引からは消えない。「退避したから解析から外れた」は成り立たず、過去に追加した無視設定は作業ツリーにのみ効く。逆に、索引から外したい run を無視設定で外そうとすると静かに失敗する。**実測**: 先行調査では別ホストで 37 件が該当したとされる。**自ホスト bengio では 0 件**（2026-08-09 実測）。内訳は、収穫器が走査する run 722 件を `git check-ignore --stdin` にかけて該当 0 件、`git ls-files --error-unmatch` で未追跡 0 件。`experiments/` 配下の無視エントリ自体は 936 件あるが、いずれも追跡済み run 配下の checkpoint / logs / predictions / wandb 等であり `metrics.json` を含まないため走査対象にならない。**別ホストの 37 件を自ホストの値として持ち込んではならない。** **B-36 と根本原因は同一である。** B-36 は「同じ commit でもホストによって索引の行数が変わる」側面を扱い、本エントリは「無視設定が索引を保護しない」側面を扱う。片方だけ直しても他方は残らないため、対処は同時に検討する | **3 案を挙げる。ここでは選ばない。** **(i) 走査時に無視設定を参照する** — 走査結果を `git check-ignore` で濾す。無視設定と索引の意味が一致する反面、退避 run が索引から消えるため退避の記録自体が失われる。B-36 の案 (i) と同じ副作用を持つ。 **(ii) 除外規約へ移す** — 無視設定ではなく `EXCLUSION_RULES` と `excluded` 列で表現する。索引には残したまま解析からのみ外せるが、B-28 と B-29 が示すとおり現行の完全一致判定は取りこぼす。B-28 の `_legacy_score_thr_0` 33 run を巻き込む危険があるため、規約の設計をやり直す必要がある。 **(iii) 正本ホストの条件で担保する** — 索引はホスト依存の生成物と割り切り、無視設定を持たないホストを正本と定めてそこでのみ生成する。実装は不要だがどのホストを正本とするかが未定であり、B-36 の案 (iii) と同じ判断を要する。 **判断の前に測るべきこと**: 各ホストで走査対象 run のうち無視設定に該当する件数。自ホストが 0 件である以上、この事象はホスト横断で測らないと影響範囲が分からない。関連: B-36（同一の根本原因）/ B-28 / B-29（除外規約側の制約）/ B-12 |
| BL-shared-config-host-value-unchecked | B-39 | 🔴 **共有配布物にホスト固有値が混ざっていないことを機械的に検査する仕組みが無い** | 共有される雛形 `.env.example` に `SERVERNAME=bengio` が残っており、写した全ホストが揃って同じ論理名を名乗る導線になっていた（2026-08-15 の契約で除去）。実測では、ホストの正しい論理名 `lecun` を先に置いた状態でこの雛形を読み込むと `bengio` へ**上書き**され、bash と zsh の双方で再現した。空欄を埋めるだけの無害な挙動ではない。共有の暗号設定からは同じ値が `c61a673` で除かれていたが、**雛形は直っていなかった**。規約自体は `docs/secrets_and_tracking.md` に明文化したが、**検査は人手のままである**。同種の候補として `configs/default.yaml` を調べたところ、値は `${oc.env:SERVERNAME,null}` の間接参照であり写しても誤らないが、コメントに具体名 `bengio` を例示として含む。 | 共有配布物の一覧（`.env.example` / `configs/**` / `scripts/sync/**`）を先に定める。そのうえで、ホスト論理名の集合に一致する具体値が**代入行**に現れたら `exit 1` とする検査を `make` へ組み込む。コメント中の例示を許すか禁じるかを先に決めないと、`configs/default.yaml` の扱いが定まらない。関連: B-33（この表へ追記する際の列破壊）。 |
| BL-research-logger-tests-fail | B-40 | 🔴 **Notion 記録の試験 4 件が phase0 で失敗し続けている** | `tests/test_research_logger.py` の 4 件（`test_log_run_idempotent` `test_run_logging_invokes_log_run_on_finally` `test_run_logging_no_double_post_on_normal_exit` `test_run_logging_swallows_exception_in_user_block`）が `origin/phase0` の時点から失敗する。`log_run` が `None` を返し、`log_experiment_to_notion` が呼ばれない。**環境非依存である**ことを 2026-08-11 に lecun で実測した。MagicMock を使う純粋な論理の照合であり、資格情報も外部接続も要らない。実装と試験のどちらが正しいかは未調査である。**この 4 件は長らく文書に載っていなかった。** `docs/reproduce_on_new_machine.md` は「既知の失敗は 1 件」と書いており、新規ホストの構築者が健全な環境を壊れていると誤判定する状態だった（同文書は T-2026-08-16 で実測値へ直した）。 | `research_logger.log_run` の戻り値の規約を先に決める。試験が要求する page id を返すのか、`None` でよいのか。決めてから実装か試験のどちらかを直す。Notion 記録は無認証で no-op になる設計なので、**no-op のときの戻り値**も併せて決めないと同じ食い違いが再発する。関連: B-39（文書と実態の食い違いを機械で検査する仕組みが無い）。 |
"""

METRIC_ALIASES = {
    "_comment": (
        "指標キーの表記ゆれ統合表。Step 1 の実測 (573 run) に基づく。"
        "canonical は split 接頭辞を剥がした後の名前。"
    ),
    "slash_split_prefixes": {
        "_comment": "スラッシュ形式は split を表す。例: val/mAP -> split=val, canonical=mAP",
        "observed": ["val"],
    },
    "underscore_split_prefixes": {
        "_comment": (
            "アンダースコア形式で split を表す接頭辞。"
            "test_accuracy -> split=test, canonical=accuracy"
        ),
        "observed": sorted(UNDERSCORE_SPLIT_PREFIXES),
    },
    "task_prefixes_not_split": {
        "_comment": (
            "★ split ではなくタスク名。phase_accuracy の phase を split と誤認しないこと。"
            "根拠: phase_accuracy と test_accuracy が同一 run に 27 件共存する。"
        ),
        "observed": ["phase"],
    },
    "phase_metric_bases": sorted(PHASE_METRIC_BASES),
    "sticky_variants": {
        "_comment": "sticky_<metric> / sticky_test_<metric> / <metric>_sticky は sticky_<canonical> に統合",
        "forms": ["sticky_<metric>", "sticky_test_<metric>", "<metric>_sticky"],
    },
    "bare_key_policy": {
        "_comment": (
            "prefix 無しキー (例: mAP) は、prefix 付き (val/mAP) と値が一致すれば重複として"
            "捨てる。一致しなければ <canonical>__bare として両方保持し anomalies.md に記録する。"
        )
    },
}


def write_runindex(records: list[dict[str, Any]], anomalies: str) -> None:
    runs_dir = RUNINDEX / "runs"
    if RUNINDEX.exists():
        shutil.rmtree(RUNINDEX)
    runs_dir.mkdir(parents=True)

    for r in records:
        out = runs_dir / f"{r['ledger_key']}.json"
        out.write_text(
            json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    # Stage 2: runs/*.json を読み直して index を作る (二段構え)
    reloaded = [
        json.loads(p.read_text(encoding="utf-8")) for p in sorted(runs_dir.glob("*.json"))
    ]
    header, rows = build_index(reloaded)
    with (RUNINDEX / "index.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    # per-class を long 形式で 1 ファイルに配布する（目的①）
    pch, pcr = build_per_class_long(reloaded)
    with (RUNINDEX / "per_class.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=pch, lineterminator="\n")
        writer.writeheader()
        writer.writerows(pcr)

    # 1 行 = 1 実験（seed 集約 + 対照 Δ）（目的②）
    eh, er = build_experiments(reloaded)
    with (RUNINDEX / "experiments.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=eh, lineterminator="\n")
        writer.writeheader()
        writer.writerows(er)

    # 1 行 = 1 実験 × 1 指標 の §10.1 判定表
    vh, vr = build_verdicts(er)
    with (RUNINDEX / "verdicts.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=vh, lineterminator="\n")
        writer.writeheader()
        writer.writerows(vr)

    # test 評価を持つ run の val/test 対応表（縦持ち）
    anomalies_dir = RUNINDEX / "anomalies"
    anomalies_dir.mkdir(exist_ok=True)
    ph, pr = build_val_test_pairs(reloaded)
    with (anomalies_dir / "val_test_pairs.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ph, lineterminator="\n")
        writer.writeheader()
        writer.writerows(pr)

    # paired-σ の実行可能性（宣言と実態の差）
    fh_, fr = build_paired_feasibility(reloaded)
    with (anomalies_dir / "paired_feasibility.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fh_, lineterminator="\n")
        writer.writeheader()
        writer.writerows(fr)

    # 学習スクリプトの決定性制御の棚卸し（§1）
    ah, ar = build_determinism_audit(reloaded)
    with (anomalies_dir / "determinism_audit.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ah, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ar)

    # within-seed と between-seed のばらつきの比較（§2）
    wh, wr = build_within_vs_between(reloaded)
    with (anomalies_dir / "within_vs_between_seed.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=wh, lineterminator="\n")
        writer.writeheader()
        writer.writerows(wr)

    # 代表値の取り方で結論が動かないことの確認
    dh, dr = build_dedup_sensitivity(reloaded)
    with (anomalies_dir / "dedup_sensitivity.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=dh, lineterminator="\n")
        writer.writeheader()
        writer.writerows(dr)

    (anomalies_dir / "backlog.md").write_text(BACKLOG, encoding="utf-8")

    (RUNINDEX / "README.md").write_text(RUNINDEX_README, encoding="utf-8")
    (RUNINDEX / "host_aliases.json").write_text(
        json.dumps(HOST_ALIASES, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (RUNINDEX / "metric_aliases.json").write_text(
        json.dumps(METRIC_ALIASES, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (RUNINDEX / "anomalies.md").write_text(anomalies, encoding="utf-8")


# --------------------------------------------------------------------------- #
# anomalies.md
# --------------------------------------------------------------------------- #
def build_anomalies(
    records: list[dict[str, Any]],
    nonstandard: list[tuple[str, int]],
    recipe_splits: list[dict[str, Any]] | None = None,
    pairing: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    add = lines.append

    add("# anomalies — 規約から外れたもの・判断を保留したもの")
    add("")
    add("`tools/harvest_runindex.py` が自動生成する。手で編集しない。")
    add("")

    add("## 1. 除外した run")
    add("")
    add("`experiments/README.md` に `_` 接頭辞が「解析対象外」を意味するという規約は")
    add("**明文化されていない**。以下はディレクトリ名の意味からの判断であり、")
    add("規約に基づくものではない。**除外規約の明文化を推奨する。**")
    add("")
    excl = [r for r in records if r["excluded"]]
    by_reason: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in excl:
        by_reason[r["exclusion_reason"]].append(r)
    add(f"除外 {len(excl)} run / 全 {len(records)} run（削除ではなくフラグ）")
    add("")
    add("| exclusion_reason | runs | 対象 |")
    add("|---|---:|---|")
    for reason in sorted(by_reason):
        rs = by_reason[reason]
        paths = sorted({str(Path(r["path"]).parent) for r in rs})
        add(f"| `{reason}` | {len(rs)} | {', '.join(f'`{p}`' for p in paths)} |")
    add("")
    add("### 1.1 `phase0/_failed_s3_weighted/` の 6 run — 運用上の欠陥")
    add("")
    add("**repo 上で失敗が確認できる唯一の run 群だが、Notion 実験Run台帳では")
    add("`Status='failed'` が 616 行中 0 件。失敗が台帳に反映されない運用上の欠陥がある。**")
    add("")
    add("- 6 run とも `metrics.json` が空 `{}` で、学習が完走していない")
    add("- うち 3 つ（`_004_partial` / `_005_partial` / `_006_partial`）は命名規約にも従わない")
    add("- 成功 run だけが台帳に載る運用では、失敗率・試行回数・打ち切り理由を")
    add("  後から復元できない。Δ の解釈（何回試して何回失敗したか）が検証不能になる")
    add("- 対処案: `ExperimentManager` に失敗時の Status 書き込みを配線する、")
    add("  または収穫時に `metrics.json` 空を failed として台帳へ補完投稿する")
    add("")

    add("## 2. split を確定できなかった run")
    add("")
    add("指標キーの接頭辞から split を確定できない run。**推測していない**。")
    add("")
    nosplit = [r for r in records if r["split"] is None]
    add(f"確定不能 {len(nosplit)} run / 全 {len(records)} run")
    add("")
    prov = Counter(r["provenance"]["split"] for r in nosplit)
    add("| split_provenance | runs |")
    add("|---|---:|")
    for k, v in prov.most_common():
        add(f"| `{k}` | {v} |")
    add("")
    add("残るのは **`metrics.json` が空 `{}` の run** である。指標が 1 つも無いため")
    add("「どの split で評価したか」が原理的に存在しない。正本 §16.7 の既定（§13）も")
    add("指標を持つ run にのみ適用しており、これらには適用していない。")
    add("")
    if nosplit:
        add("| path | excluded | exclusion_reason |")
        add("|---|---|---|")
        for r in sorted(nosplit, key=lambda x: x["path"]):
            add(f"| `{r['path']}` | {r['excluded']} | `{r['exclusion_reason']}` |")
        add("")

    add("## 3. host を確定できなかった run")
    add("")
    nohost = [r for r in records if r["host"] is None]
    add(f"確定不能 {len(nohost)} run")
    add("")
    add("| host_raw | runs | 理由 |")
    add("|---|---:|---|")
    hc = Counter(r["host_raw"] for r in nohost)
    for k, v in sorted(hc.items(), key=lambda x: (-x[1], str(x[0]))):
        if k is None:
            why = "server.txt 欠損かつ eval_recipe.server_name 無し"
        elif k == "aolab":
            why = "philip / ilya の双方が返すコンテナ内 hostname のため一意に特定不能"
        else:
            why = "host_aliases.json に無い値"
        add(f"| `{k}` | {v} | {why} |")
    add("")

    add("## 4. per_class_ap.json のクラス体系が 2 種類ある")
    add("")
    add("ファイル名は `per_class_ap.json` だが、中身は 2 つの異なる体系が混在する。")
    add("**横断比較の際に混ぜてはならない。**")
    add("")
    add("**ファイル名が `per_class_ap.json` でありながら中身が F1 の群があるため、")
    add("`per_class_kind` だけでなく `per_class_metric` を必ず参照すること。**")
    add("`per_class_source` に読み取り元の相対パスを保持している。")
    add("")
    km = Counter((r["per_class_kind"], r["per_class_metric"]) for r in records)
    add("| per_class_kind | per_class_metric | runs | 内容 | 根拠 |")
    add("|---|---|---:|---|---|")
    desc = {
        ("tool", "AP"): (
            "15 クラスの術具 AP",
            "`per_class_coco_map` / `COCOeval.precision` 由来",
        ),
        ("phase", "F1"): (
            "9 クラスの工程別 **F1**（AP ではない）",
            "`scripts/train_{b2a,t1a,s4_tecno,haux,taux,t1a_boundary,t1a_regiontraj}.py` が "
            "`best.get(\"phase_per_class_f1\", {})` を `log_per_class_ap()` に渡している",
        ),
        ("unknown", "unknown"): ("既知の 2 体系のいずれとも一致しない", "確定不能"),
        (None, None): ("`per_class_ap.json` が無い・空・パース失敗", "—"),
    }
    for k, v in sorted(km.items(), key=lambda x: (-x[1], str(x[0]))):
        d, why = desc.get(k, ("", ""))
        add(f"| `{k[0]}` | `{k[1]}` | {v} | {d} | {why} |")
    add("")
    unk = [r for r in records if r["per_class_metric"] == "unknown"]
    add(f"### metric を確定できなかった run: {len(unk)}")
    add("")
    if unk:
        for r in sorted(unk, key=lambda x: x["path"]):
            n = len(r["per_class"] or {})
            add(f"- `{r['path']}`（{n} クラス）")
    else:
        add("なし。")
    add("")

    add("## 5. NaN を含む run")
    add("")
    add("`NaN` は標準 JSON として不正なため出力では `null` に変換した。")
    add("どのクラスが `NaN` だったかは `per_class_nan_classes` に保持している。")
    add("")
    add("### NaN の意味（コードとデータから確定済み）")
    add("")
    add("**「そのクラスがその評価 split の GT に存在せず、AP が定義できない」**")
    add("")
    add("根拠 3 点:")
    add("")
    add("1. `scripts/post_process_sensex_codino.py:97` が全クラスを `float('nan')` で初期化し、")
    add("   mmdet のログ表に現れたクラスだけを上書きする。mmdet は COCO の precision が")
    add("   `-1`（GT 無し）のとき `nan` を出力する。")
    add("2. `data/annotations/egosurgery_tool/instances_val.json` を全数集計すると")
    add("   **`Retractor` の GT が val split に 0 件**（train 2079 / val 0 / test 325）。")
    add("3. NaN になるクラスの組が run 群と完全に対応する（下表）。split が壊れている")
    add("   `_wrong_split_8_2_3` の run だけ NaN のクラスが違うことは、")
    add("   「NaN = その split に GT が無い」以外では説明できない。")
    add("")
    nan_pat: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for r in records:
        if r["per_class_nan_classes"]:
            nan_pat[tuple(r["per_class_nan_classes"])].append(r["path"])
    add("| NaN のクラス | runs | 該当群 |")
    add("|---|---:|---|")
    for k, v in sorted(nan_pat.items(), key=lambda x: -len(x[1])):
        groups = sorted({str(Path(p).parent) for p in v})
        add(f"| {', '.join(f'`{c}`' for c in k)} | {len(v)} | {', '.join(f'`{g}`' for g in groups)} |")
    add("")
    add("### 平均の取り方への含意")
    add("")
    add("`NaN` を 0 として平均すると mAP を過小評価する。`per_class_valid_count` を")
    add("分母に使うこと（15 固定にしない）。")
    add("")

    add("## 6. 命名規約から外れた run")
    add("")
    odd = [r for r in records if r["step"] is None]
    add(f"`<step>_<seq3>_<desc>_seed<N>` に一致しない run: {len(odd)}")
    add("")
    for r in sorted(odd, key=lambda x: x["path"]):
        add(f"- `{r['path']}`")
    add("")

    add("## 7. ディレクトリ名の `det<N>` / `p<N>` トークン — 大半は seed ではない")
    add("")
    add("### 7.1 🔴 修正済みの誤読: `p010` は seed ではなくノイズ率")
    add("")
    add("以前の実装は `(det|p)(\\d+)` にマッチした数値を無条件に補助 seed として扱い、")
    add("**81 run に `seed_phase` を付けていた。うち 72 件は誤り**である。")
    add("")
    add("一次証拠 (`command.sh` の実引数):")
    add("")
    add("```")
    add("b2a_base_oracle_noise_p010_001_b2a_base_oracle_noise_p010_seed42/command.sh")
    add("  python scripts/train_b2a.py --seed 42 --epochs 50 --tool-source oracle \\")
    add("    --tool-noise-rate 0.10 --description-override b2a_base_oracle_noise_p010")
    add("```")
    add("")
    add("`p010` は `--tool-noise-rate 0.10`、すなわち**ノイズ率 0.10** であって seed ではない。")
    add("これを seed とみなすと、ノイズ水準という**条件**が反復軸に誤分類され、")
    add("`experiment_id` から剥がされて noise 0.10 / 0.20 / 0.30 が 1 実験に混ざる。")
    add("")
    add("現在の判定は `command.sh` を一次証拠にする:")
    add("")
    add("| 条件 | 判定 | provenance |")
    add("|---|---|---|")
    add("| `--tool-noise-rate` を持つ | ノイズ率。seed ではない | `p_token_is_noise_rate_by_command_sh` |")
    add("| `p<N>` == 末尾 `seed<N>` | 工程学習の seed (反復軸) | `p_token_equals_run_seed` |")
    add("| どちらでもない | **確定不能。null にする** | `p_token_not_determinable` |")
    add("| `det<N>` | 凍結検出器の指定 = **条件**。反復軸ではない | `det_token_is_backbone_condition` |")
    add("")
    add("ノイズ系を除いた 27 run すべてで `p<N> == seed` であることを実測で確認した。")
    add("")
    aux_prov = Counter(
        r.get("aux_token_provenance") for r in records if r.get("aux_token_provenance")
    )
    add("### 7.2 現在の内訳")
    add("")
    add("| aux_token_provenance | run 数 |")
    add("|---|---:|")
    for k, n in sorted(aux_prov.items(), key=lambda x: -x[1]):
        if k == "no_aux_token":
            continue
        add(f"| `{k}` | {n} |")
    add("")
    aux = [r for r in records if r["seed_detector"] is not None or r["seed_phase"] is not None]
    add(f"`seed_detector` または `seed_phase` が実際に付いた run: **{len(aux)}**")
    add("")
    if aux:
        add("| path | seed (末尾) | seed_detector | seed_phase |")
        add("|---|---:|---:|---:|")
        for r in sorted(aux, key=lambda x: x["path"])[:40]:
            add(
                f"| `{r['path']}` | {r['seed']} | "
                f"{r['seed_detector'] if r['seed_detector'] is not None else '—'} | "
                f"{r['seed_phase'] if r['seed_phase'] is not None else '—'} |"
            )
        if len(aux) > 40:
            add(f"| … 他 {len(aux) - 40} 件 | | | |")
    add("")
    add("### 7.3 🔴 未解決: `noise000` という名前が実態と食い違う")
    add("")
    add("`b2a_ro_oracle_noise000` は名前が「ノイズ 0.00」を意味するように読めるが、")
    add("12 run の `command.sh` が渡している `--tool-noise-rate` は実際には")
    add("**0.05 / 0.10 / 0.20 / 0.30 の 4 通り**である。")
    add("")
    add("- 名前を信じて「ゼロノイズの対照」として使うと、**4 水準の混合**と比較することになる。")
    add("- `description` が 1 つしか無いため、`experiment_id` はこの 12 run を 1 実験に束ねる。")
    add("  `n_command_variants` 列が 4 になるので機械的には検出できるが、")
    add("  **この実験の集約値 (mean / pstd) は 4 条件の混合であり、意味を持たない**。")
    add("- 規約と実データのどちらを正とするかは harvester が決めることではないため、")
    add("  ここに記録するに留める。ディレクトリ名の改名は `experiments/` の変更にあたる。")
    add("")

    add("## 8. prefix 無しキーと prefix 付きキーの値が食い違った run")
    add("")
    conf = [r for r in records if r["conflicting_bare_keys"]]
    add(f"該当 {len(conf)} run（食い違いがあれば両方を保持している）")
    add("")
    for r in sorted(conf, key=lambda x: x["path"]):
        add(f"- `{r['path']}`: `{json.dumps(r['conflicting_bare_keys'], ensure_ascii=False)}`")
    add("")

    add("## 9. 標準規約 (1 run 1 dir) に従わない群")
    add("")
    add("`metrics.json` を持たないため run として収穫していない。")
    add("**取りこぼした run 数は 0**（これらの配下に `metrics.json` は 1 つも無い）。")
    add("個別 adapter は次段階に回す。")
    add("")
    add("| group | ファイル数 | 中身の種別 | 術具 per-class 指標 |")
    add("|---|---:|---|---|")
    kindmap = {
        "analysis": (
            "EDA レポート / 図 (png) / CSV / JSON",
            "**あり**: `detector_sanity/reldetr_seed42_val_perclass.json` "
            "(COCO 形式 `AP`/`AP50`/`AP75`/`AP_s`/`AP_m` 等 13 キー)、"
            "`signature_subset_detector_compare/results.json` (`per_class` キー)",
        ),
        "detector_improve": (
            "`label_names.txt` / `val_perclass.json`",
            "**あり**: `augstrong_seed42/val_perclass.json` (COCO 形式 13 キー)",
        ),
        "audit": (
            "`audit_report.json` × 3",
            "なし (`inject` / `trainable` / `n_trainable_params` 等の学習設定監査)",
        ),
        "g2_main_2026-07-29": (
            "`csv/` `json/` `prereg/` `HANDOVER_lecun.md`",
            "なし (`f_roi_stats_{val,test}.json` は ROI 統計)",
        ),
        "ablations": ("`.gitkeep` のみ", "未着手 scaffold"),
        "final": ("`.gitkeep` のみ", "未着手 scaffold"),
    }
    for name, n in nonstandard:
        kind, pc = kindmap.get(name, ("(未調査)", "(未調査)"))
        add(f"| `{name}` | {n} | {kind} | {pc} |")
    add("")
    add("### 次段階への申し送り")
    add("")
    add("**現在 `per_class_metric=AP` の run は 62 しか無い。**")
    add("上表の `val_perclass.json` 系は術具 per-class 指標を含むため、")
    add("adapter を書けば貴重な追加ソースになる。")
    add("")
    add("また `analysis/step_c_coupling_analysis/*.json`（12 ファイル）は")
    add("`model` / `seed` / **`split`** / `ckpt` / `phase` / `mAP` を持ち、")
    add("**`split` を明示している**。split が確定できない run の補強材料になりうる。")
    add("")

    add("## 10. 警告が出た run の内訳")
    add("")
    wc: Counter[str] = Counter()
    for r in records:
        for w in r["harvest_warnings"]:
            # 可変部分を落として集計する
            key = re.sub(r"\{[^}]*\}", "{...}", w)
            key = re.sub(r"'[^']*'", "'...'", key)
            key = re.sub(r"seed\d+", "seed<N>", key)
            key = re.sub(r": .*$", "", key) if key.startswith("run 名が") else key
            wc[key] += 1
    add("| 警告 | 件数 |")
    add("|---|---:|")
    for k, v in wc.most_common():
        add(f"| {k} | {v} |")
    add("")

    add("## 11. 🔴 要対処: 乱数で per-class AP を生成するコードが残っている")
    add("")
    add("`src/egosurgery/engines/trainer.py:273-278`")
    add("")
    add("```python")
    add("rng = np.random.default_rng(int(self.cfg.seed))")
    add("per_class_ap = {")
    add("    cls: round(float(rng.uniform(0.05, 0.85)), 4) for cls in TOOL_CLASSES")
    add("}")
    add("self.manager.log_per_class_ap(per_class_ap)")
    add("```")
    add("")
    add("この dummy Trainer は **乱数を `mAP` として `metrics.json` に書く**。")
    add("`CLAUDE.md` の「metrics / mAP 等の数値を絶対に捏造しない」に照らして危険。")
    add("`cfg.experiment.step` が s0/s1/s2 以外のとき dummy Trainer が選ばれる。")
    add("")
    add("### 現時点の混入は 0 件（検証済み）")
    add("")
    add("`tools/verify_no_dummy_metrics.py` が 2 系統で検査する:")
    add("")
    add("1. **語彙照合** — dummy 側の `TOOL_CLASSES` は `Needle_Holders` / `Retractors` /")
    add("   `Clip_Applier` / `Suction` / `Electrocautery` / `Needle` / `Thread` という")
    add("   **別の語彙**を使う。実データ 2 体系のどちらとも一致しない。")
    add("2. **値の再現照合** — 既知 seed で `np.random.default_rng(seed).uniform(0.05, 0.85)`")
    add("   を再現し、`per_class_ap.json` と完全一致するものを探す。")
    add("")
    add("結果: **混入 0 件**。experiments/ の per-class 指標は全て実評価器由来。")
    add("")
    add("**このタスクではコードを変更していない。**")
    add("dummy Trainer の削除またはガード追加は別タスクで検討すること。")
    add("再検証: `python tools/verify_no_dummy_metrics.py`（`make runindex` に組込済）")
    add("")
    add("### 11.1 🔴 検査の死角 — mAP を持つが術具 per-class を持たない run")
    add("")
    add("上の 2 系統（語彙照合・値再現）は **`per_class_ap.json` に依存する**。")
    add("mAP 系の指標を持つのに術具 per-class（15 クラス）を持たない run は、")
    add("どちらの検査でも判定できない。**個別確認が要る対象**として列挙する。")
    add("")
    blind = [
        r
        for r in records
        if r["per_class_metric"] != "AP"
        and any("mAP" in k for k in (r["metrics"] or {}))
    ]
    add(f"該当 {len(blind)} run")
    add("")
    if blind:
        add("| path | mAP 系のキー | entrypoint | commit |")
        add("|---|---|---|---|")
        for r in sorted(blind, key=lambda x: x["path"]):
            mk = ", ".join(f"`{k}`" for k in sorted(k for k in r["metrics"] if "mAP" in k))
            cmd = r["command"] or ""
            m = re.search(r"(?:python3?|bash)\s+(\S+\.(?:py|sh))", cmd)
            entry = f"`{m.group(1)}`" if m else "—"
            commit = (r["commit"] or "")[:10] or "—"
            add(f"| `{r['path']}` | {mk} | {entry} | `{commit}` |")
        add("")
    add("`tools/verify_no_dummy_metrics.py --strict` はこの死角が 1 件でもあれば")
    add("異常終了する。`make runindex` は非 strict で実行し、警告として表示する。")
    add("")
    add("#### 11.1.1 `t1b_phasefilm_{001,002}` の個別確認結果")
    add("")
    add("3 つの独立した検証（コード経路 / 値の性質 / 証跡の整合）を、いずれも")
    add("「実評価器由来である」という主張を**反証する**目的で実施した。")
    add("**3/3 が反証に失敗し、`real_evaluator`（確信度 high）で一致した。**")
    add("")
    add("反証を退けた根拠:")
    add("")
    add("1. **到達不能性** — `command.sh` は `python scripts/postprocess_t1b.py`。")
    add("   dummy Trainer は `src/egosurgery/train.py::_select_trainer` 経由でしか")
    add("   選ばれず、それは `python -m egosurgery.train` でしか実行されない。")
    add("2. **値域の外** — seed 0..100000 を全探索した結果、")
    add("   `np.random.default_rng(s).uniform(0.05,0.85,15).mean()` の最大値は")
    add("   **0.6907**（seed 98115）。**0.70 を超える seed は 1 つも存在しない**。")
    add("   観測値 0.7292 / 0.7217 は生成器の到達可能範囲の外にある。")
    add("   直接照合でも seed123 -> 0.45405 / seed456 -> 0.43498 で不一致。")
    add("3. **精度の不整合** — dummy は各クラス AP を 4 桁、mAP を 6 桁に丸める")
    add("   (`trainer.py:276,299`)。観測値は `0.7291778095772903` と float64 の全桁。")
    add("4. **キー形状の不一致** — dummy が返すのは `val/loss` `val/accuracy`")
    add("   `val/mAP` `mAP` のみ。観測されたのは `control_init_mAP` `delta_control`")
    add("   `injection_effect` 等で、契約が異なる。")
    add("5. **`epoch = -1`** — dummy は `for epoch in range(1, epochs+1)` なので")
    add("   0 以下を出せない。-1 は「warm-start init が best」を表す番兵値。")
    add("6. **ビットレベル再現** — `transfer/t1b_camt_all_seed456_efros/`")
    add("   `injected_result.json` の `init_per_class_coco_map` を `np.nanmean` すると")
    add("   **0.7216586914703580 と完全一致**。実 COCO per-class AP から再構成できる。")
    add("   その per-class は EgoSurgery-Tool の 15 クラスで `Retractor = NaN`（GT 0 件）。")
    add("")
    add("**ただし証跡としては不完全である（3 レンズが独立に指摘）:**")
    add("")
    add("- 🔴 **一次成果物が消失** — `postprocess_t1b.py` が読む")
    add("  `experiments/transfer/t1b_seed{123,456}/t1b_result.json` が存在せず、")
    add("  commit もされていない。再現には元データが要る。")
    add("- 🔴 **provenance の欠陥** — `git_commit.txt` は `a697d90` を記録するが、")
    add("  **その commit に `scripts/postprocess_t1b.py` は存在しない**")
    add("  (`git ls-tree -r a697d90 | grep t1b` が 0 件)。記録された commit では")
    add("  この run を再現できない。")
    add("- 🔴 **数値が退化している** — `mAP == init_mAP` かつ")
    add("  `delta_detection = delta_control = injection_effect = 0.0`、`epoch = -1`。")
    add("  これは T1b の訓練効果ではなく **warm-start(S0-frozen) 時点の評価**を")
    add("  そのまま記録したもの。改善の証拠として引用してはならない。")
    add("- `eval_recipe` が両 `metrics.json` に不在。学習/評価ログも残っていない")
    add("  （兄弟の camt / clsbias 系にはログがある）。")
    add("")
    add("**結論**: 捏造値ではない（dummy Trainer 由来ではない）が、")
    add("**再現不能かつ Δ=0 の退化した記録**であり、解析に使う前に上記 3 点の解消が要る。")
    add("")

    add("## 12. experiments/README.md と実態の乖離")
    add("")
    add("README は step 識別子を **s0〜s9 / a1〜a7（17 種）** と規定しているが、")
    steps = Counter(r["step"] for r in records if r["step"])
    add(f"実測は **{len(steps)} 種**。README に無い以下の系統が存在する。")
    add("")
    fam = {"b1": [], "b2a": [], "t1a": [], "t1b": [], "taux": [], "haux": [], "hires": []}
    for s, n in steps.items():
        for f in fam:
            if s == f or s.startswith(f + "_"):
                fam[f].append((s, n))
                break
    add("| 系統 | step 識別子の種類 | run 合計 | 例 |")
    add("|---|---:|---:|---|")
    for f, items in fam.items():
        if not items:
            continue
        total = sum(n for _, n in items)
        ex = ", ".join(f"`{s}`" for s, _ in sorted(items, key=lambda x: -x[1])[:2])
        add(f"| `{f}` | {len(items)} | {total} | {ex} |")
    add("")
    add("また README は 6 カテゴリ（`baselines` / `phase0` / `phase1` / `ablations` /")
    add("`transfer` / `final`）を規定するが、実際に run があるのは 4 つで、")
    add("`ablations` と `final` は空。逆に README に無い `_smoke_prior` に run がある。")
    add("")
    add("**このタスクでは README を変更していない。** 規約の更新は別タスク。")
    add("")

    add("## 13. 正本 §16.7 の既定と、その例外である test 評価 run")
    add("")
    add("M2研究計画 §16.7（優先度 A 検証結果, 2026/05/29 追加）§16.7.1 に記録がある:")
    add("")
    add("> **§8 訓練スクリプトに関する補足**: val_evaluator の ann_file は")
    add("> `instances_val.json`、`prefix='val'`（mmdet_config.py:314-320）のため、")
    add("> `metrics.json` / `per_class_ap.json` はすべて **val split の数値**。")
    add("> test split は未評価（最終報告用に温存、Δ 判定は val で行う設計）。")
    add("")
    add("ローカル写し: `docs/m2_plan_rewrite/sections/19_epoch_16.md` L161 /")
    add("`docs/m2_plan_rewrite/m2_plan_v2_full.md` L1561")
    add("")
    add("これを split の既定値とし、`provenance.split = from_plan_section_16_7` を記録する。")
    add("ただし **指標が 1 つもない run には適用しない**（評価されていないため null のまま）。")
    add("")
    plan_default = [r for r in records if r["provenance"].get("split") == "from_plan_section_16_7"]
    add(f"既定を適用した run: {len(plan_default)}")
    add("")
    if plan_default:
        add("| path | 指標キー |")
        add("|---|---|")
        for r in sorted(plan_default, key=lambda x: x["path"]):
            ks = ", ".join(f"`{k}`" for k in sorted((r["metrics"] or {}).keys())[:6])
            add(f"| `{r['path']}` | {ks} |")
        add("")

    add("### 13.1 🔴 正本の記述の例外 — test 評価を持つ run")
    add("")
    add("正本は「test split は未評価」と述べているが、その後 `--eval-test` が実装され、")
    add("**test 側の数値を持つ run が実在する**。正本の記述はこの時点より前のもの。")
    add("")
    tested = [r for r in records if (r["metrics_by_split"] or {}).get("test")]
    add(f"該当 {len(tested)} run。全件の val/test 対応表は `anomalies/val_test_pairs.csv`。")
    add("")
    add("**index.csv の `metric.<name>` 列は primary(val) の値である。**")
    add("test 側は `metric_test.<name>` 列に別出ししてある（`has_test` 列で絞り込める）。")
    add("この分離が無いと「split 列が val 一色 → test 評価は存在しない」と誤読される。")
    add("")
    # val/test の乖離を実測で示す
    diffs: dict[str, list[float]] = defaultdict(list)
    vals: dict[str, list[float]] = defaultdict(list)
    tests: dict[str, list[float]] = defaultdict(list)
    for r in tested:
        by = r["metrics_by_split"]
        for n in by.get("val", {}).keys() & by.get("test", {}).keys():
            v, t = by["val"][n], by["test"][n]
            if isinstance(v, (int, float)) and isinstance(t, (int, float)):
                vals[n].append(v)
                tests[n].append(t)
                diffs[n].append(t - v)
    if diffs:
        add("#### val / test の乖離（実測・全 %d run）" % len(tested))
        add("")
        add("| 指標 | val 平均 | test 平均 | 差 (test - val) | n |")
        add("|---|---:|---:|---:|---:|")
        for n in sorted(diffs, key=lambda x: sum(diffs[x]) / len(diffs[x])):
            nv = sum(vals[n]) / len(vals[n])
            nt = sum(tests[n]) / len(tests[n])
            add(f"| `{n}` | {nv:.4f} | {nt:.4f} | {nt - nv:+.4f} | {len(diffs[n])} |")
        add("")
    add("| path | seed | excluded |")
    add("|---|---:|---|")
    for r in sorted(tested, key=lambda x: x["path"]):
        add(f"| `{r['path']}` | {r['seed']} | {r['excluded']} |")
    add("")

    add("## 14. Notion 実験Run台帳との照合 — 母数は未確定（結論保留）")
    add("")
    add("台帳の行数について 2 つの実測値がある。**母数が確定するまで差分の結論は出さない。**")
    add("")
    add("| 出所 | 実測 | 計測方法 |")
    add("|---|---:|---|")
    add("| ユーザー側 | 616 | `COUNT(*)` |")
    add("| Claude Code (MCP) | **739** | `SELECT COUNT(*)` via query_data_sources |")
    add("")
    add("### 排除できた原因")
    add("")
    add("| 仮説 | 検証結果 |")
    add("|---|---|")
    add("| 複数データソース | ❌ **データソースは 1 つ**（`collection://7bcf9406-…`） |")
    add("| フィルタ付きビューを見ていた | ❌ **ビューは 1 つ**（\"Default view\"）で Status 昇順ソートのみ・**フィルタなし** |")
    add("| 同名 DB の重複 | ❌ ワークスペース検索で `実験Run台帳` は **1 件のみ** |")
    add("")
    add("### 残る候補（未検証）")
    add("")
    add("- **計測時点の差**（台帳が増加した）: 作成日分布を取るクエリが")
    add("  Notion のクエリ利用上限に達し実行できなかった")
    add("- **アーカイブ行の扱い**: MCP の SQL モードは `is_archived` を受け付けず、")
    add("  アーカイブ行を含むか否かが仕様上未定義")
    add("")
    add("### 確定した事実")
    add("")
    add("| 項目 | 実測 |")
    add("|---|---:|")
    add("| 総行数（MCP 計測） | 739 |")
    add("| ユニークな Name | 738 |")
    add("| `Name LIKE '%_seed%'`（run 形式） | 712 |")
    add("| 散文タイトルの行 | 27 |")
    add("| **Status = `failed`** | **0** |")
    add("| Status = completed / planned / running / null | 733 / 4 / 1 / 1 |")
    add("")
    add("**`failed` が 0 件であることは母数と無関係に確定している。**")
    add("repo 側には `metrics.json` が空の失敗 run が 6 件あるため、§1.1 の")
    add("運用欠陥（失敗が台帳に反映されない）はこの時点で成立する。")
    add("")
    add("run_id 単位の 3 分類（記録漏れ / 成果物消失 / 数値の食い違い）は、")
    add("クエリ上限のため **未実施**。推測で埋めていない。")
    add("")

    add("## 15. run_id の衝突")
    add("")
    dup: Counter[str] = Counter(r["run_id"] for r in records)
    dups = {k: v for k, v in dup.items() if v > 1}
    add(f"`run_id`（ディレクトリ名）は **{len(dups)} 種が複数箇所で衝突**する。")
    add("スキーマは `runs/<run_id>.json` を指定しているが、そのままではファイルが")
    add("上書きされるため、パス由来の `ledger_key` をファイル名に使い、")
    add("`run_id` はフィールドとして保持した。")
    add("")
    if dups:
        add("| run_id | 箇所数 |")
        add("|---|---:|")
        for k, v in sorted(dups.items(), key=lambda x: (-x[1], x[0])):
            add(f"| `{k}` | {v} |")
        add("")

    # ---------------------------------------------------------------- #
    add("## 16. 🔴 修正済み: primary 指標に test の値が入っていた")
    add("")
    add("### 16.1 症状")
    add("")
    add("`has_test = true` の **27 run** で、`metrics.<name>`（primary）に")
    add("val ではなく **test の値**が入っていた。`split` 列は `val` のままだったため、")
    add("**「val と名乗る test の値」**という最も危険な不整合になっていた。")
    add("`index.csv` の `metric.*` と `metric_test.*` が全 27 run で完全一致し、")
    add("Δ が全て 0.00 に見えていた。")
    add("")
    add("### 16.2 原因")
    add("")
    add("`harvest_metrics()` が「どの split が primary か」を決める **前に**")
    add("primary の入れ物を埋めていた。同じ canonical 名を複数 split が書くと")
    add("`metrics.json` のキー順で **後に来た側が勝つ**。")
    add("`phase_accuracy` → `test_accuracy` の順に並ぶため test が残っていた。")
    add("")
    add("```python")
    add("# 誤: split 判定より前に flat を埋めていた")
    add("if info['split']:")
    add("    by_split[info['split']][canon] = value")
    add("    flat[canon] = value          # <- 後勝ちで test が primary になる")
    add("...")
    add("evidence = {s for s in by_split if s != 'unknown'}   # <- 判定はこの後")
    add("```")
    add("")
    add("追補 G で `split` の既定を val と宣言した時点で、宣言（`split` 列）と")
    add("実体（`metrics`）が別の場所で決まる構造が顕在化した。")
    add("")
    add("### 16.3 対処")
    add("")
    add("1. primary split を **先に**決め、その後で `flat` を充填する順序に変更した。")
    add("2. `metrics_primary_split` 列を追加し、`metrics` の出所を機械可読にした。")
    add("3. `tools/verify_runindex.py` を追加し `make runindex` に組み込んだ。")
    add("   C1〜C3 が同型の退行を検出する（`split` 列と出所の不一致、Δ が全て 0）。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 17. 実験単位 (`experiment_id`) の導入と、その限界")
    add("")
    add("`runs/*.json` には seed をまたいで run を束ねるフィールドが 1 つも無く、")
    add("573 run は「573 個の孤立した run」であって「N 個の実験」ではなかった。")
    add("seed 集約も Δ も paired-σ も機械的に計算できない状態だったため、")
    add("**run 名から機械的に導ける実験単位**を定義した。")
    add("")
    add("```")
    add("experiment_id = <group>/<step>/<description(反復軸トークン除去)>@<split>~<frozen_source_tag>")
    add("                （同一 ID 内で eval_recipe_id が食い違う場合は #<hash8> を付与）")
    add("```")
    add("")
    add("### 17.0 🔴 名前にも command.sh にも現れない条件軸がある")
    add("")
    add("`s4_phase_baseline` の 55 run は当初「同一条件の 18 反復」に見えたが、そうではない。")
    add("真の条件軸は `config.yaml` の `frozen_source.cache_dir`（凍結特徴の抽出元）で **7 通り**あり、")
    add("これは環境変数 `RELDETR_FROZEN_TAG` で与えられるため")
    add("**run 名にも `command.sh` にも `eval_recipe` にも現れない**。")
    add("")
    add("```python")
    add("# scripts/train_s4_tecno.py")
    add('_FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")')
    add("```")
    add("")
    add("`eval_recipe_id` は phase1/s4 の 61 run すべてで同一（`test_cfg.backbone` が")
    add("リテラル固定のため条件差が原理的に現れない）。つまり `eval_recipe_id` による分離だけでは")
    add("この交絡を防げない。`frozen_source_tag` を `experiment_id` に含めることで分離している。")
    add("")
    add("`b2a` / `t1a` 系では同じ情報が `frozen_source.gap_cache` /")
    add("`frozen_source.tool_signal_cache` というキー名で入っているため、3 つのキーを順に見ている。")
    add("")
    add("#### 🔴 証跡ファイルの記述が実態と食い違う（凍結源）")
    add("")
    n_s4 = sum(1 for r in records if r["step"] == "s4_phase_baseline")
    n_claim = sum(
        1
        for r in records
        if r["step"] == "s4_phase_baseline" and "凍結源" in (r.get("notes") or "")
    )
    n_contra = sum(
        1
        for r in records
        if r["step"] == "s4_phase_baseline"
        and "凍結源" in (r.get("notes") or "")
        and r.get("frozen_source_tag")
        and r["frozen_source_tag"] != "relation_detr_seed42"
    )
    add(f"`s4_phase_baseline` の `notes.md` は **{n_claim} 件すべてで**")
    add("「凍結源: Relation-DETR seed42」と断言するが、`config.yaml` の実際の")
    add(f"`frozen_source.cache_dir` がそれと異なる run が **{n_contra} 件**ある")
    add(f"（step `s4_phase_baseline` の run 総数は {n_s4}）。`config.yaml` の `frozen_source.seed` も")
    add("`42` がハードコードされており同様に信用できない。")
    add("いずれも `scripts/train_s4_tecno.py` の固定文字列に由来する。")
    add("")
    add("**したがって `frozen_source_tag` はキャッシュのパスからのみ導き、")
    add("`frozen_source.seed` と `notes.md` の記述は採用していない。**")
    add("")
    exps = {r["experiment_id"] for r in records if r.get("experiment_id")}
    add(f"- 実験数: **{len(exps)}** / run 数 {len(records)}")
    add(f"- `experiment_id` を付けられなかった run: {sum(1 for r in records if not r.get('experiment_id'))}")
    add("  （run 名が命名規約に一致しない run）")
    if recipe_splits:
        add(f"- `eval_recipe_id` の食い違いで分離した base: {len(recipe_splits)}")
        for s in recipe_splits[:6]:
            add(f"  - `{s['base']}` -> {s['recipes']}")
    else:
        add("- `eval_recipe_id` の食い違いによる分離: 0 件")
    add("")
    add("### 17.1 🔴 限界: 名前が条件を一意に表さない実験がある")
    add("")
    add("`experiment_id` は run 名から導く以上、**名前が条件を表していない場合は")
    add("異なる条件の run を 1 実験に束ねてしまう**。検出のため次の 2 列を出している。")
    add("")
    add("| 列 | 意味 | 異常の徴候 |")
    add("|---|---|---|")
    add("| `n_command_variants` | seed/description を除いた `command.sh` 引数の種類数 | **> 1 なら条件が混在** |")
    add("| `runs_per_seed_max` | 同一 seed の run 数の最大 | > 1 なら再実行か条件違いが混在 |")
    add("")
    add("実データで判明している最悪の例は §7.3 の `b2a_ro_oracle_noise000`")
    add("（1 つの名前に 4 通りのノイズ率）。**この実験の集約値は使ってはならない。**")
    add("")
    add("### 17.2 🔴 逆向きの限界: 同一条件が別 experiment_id に分裂しうる")
    add("")
    add("`step` は `ExperimentManager` に渡された文字列でしかなく")
    add("（`src/egosurgery/utils/experiment_id.py`）、同じ条件でも起動経路が違えば別の値になる。")
    add("`description` / `split` / `frozen_source_tag` が一致しているのに `step` だけが違う組を")
    add("機械的に検出した結果が次である。**同一条件が分裂している候補**として扱うこと。")
    add("")
    by_cond: dict[tuple[str, str | None, str | None, str | None], set[str]] = defaultdict(set)
    for r in records:
        if not r.get("experiment_id"):
            continue
        key = (
            r["group"],
            normalize_description(r["description"], r["seed_phase"]),
            r["split"],
            r.get("frozen_source_tag"),
        )
        by_cond[key].add(r["experiment_id"])
    splits = {k: v for k, v in by_cond.items() if len(v) > 1}
    if splits:
        add(f"該当 **{len(splits)} 組**")
        add("")
        add("| group / description / split / frozen_source | 分裂した experiment_id |")
        add("|---|---|")
        for k, v in sorted(splits.items(), key=lambda x: str(x[0])):
            head = f"`{k[0]}` / `{k[1]}` / `{k[2]}` / `{k[3]}`"
            add(f"| {head} | " + "<br>".join(f"`{e}`" for e in sorted(v)) + " |")
        add("")
        add("これらを 1 実験として束ねるべきかは、起動経路が同一かどうかの判断を伴うため")
        add("harvester では決めない。`experiments.csv` では別行のままにしてある。")
    else:
        add("該当なし（0 組）。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 18. 対照ペア (`arm` / `control_of`) — 確定できた範囲")
    add("")
    add("### 18.1 一次証拠の探索結果")
    add("")
    add("| 証拠源 | 結果 |")
    add("|---|---|")
    add("| `command.sh` の `--control` / `--baseline` / `--inject` / `--arm` | **0 件**。引数による対照指定は存在しない |")
    add("| **`config.yaml` の `delta:` ブロック** | **441 run** が保有。`phase_denominator` が分母を名指しする |")
    add("| `notes.md` の `## Δ` 節 | 439 run が保有。同じ内容を散文で書いたもの |")
    add("")
    add("`config.yaml` の記述例（機械可読）:")
    add("")
    add("```yaml")
    add("delta:")
    add("  phase_denominator: s4_phase_baseline (frozen_tecno_phase_baseline)")
    add("  denominator_value_lecun: 0.8986±0.0034")
    add("  note: Δ_phase = (T1a − S4 base). 別サーバー実行時は lecun 分母を流用し …")
    add("```")
    add("")
    if pairing:
        add("### 18.2 対照名の同定と、その裏付け")
        add("")
        add("`config.yaml` の `delta.phase_denominator` は分母を **文字列で名指し**する。")
        add("実データに現れる 4 通り:")
        add("")
        add("| 宣言 | run 数 | 解釈 |")
        add("|---|---:|---|")
        add("| `s4_phase_baseline (frozen_tecno_phase_baseline)` | 430 | step + description |")
        add("| `t1a_regiontoken base (同env efros paired)` | 6 | step のみ（括弧は散文） |")
        add("| `t1a_regiontoken base (同一環境 efros で再学習・paired)` | 3 | 同上 |")
        add("| `S0-frozen (=init mAP, within-run)` | 2 | **同一 run 内の初期値**。対照 run は存在しない |")
        add("")
        add("#### 🔴 散文からの同定は誤る — config の宣言に従属させた")
        add("")
        add("`notes.md` は分母を `T1a base[同env efros]` と書く。名前の近さだけで読むと")
        add("`step=t1a_base_env` に見えるが、**同じ run の `config.yaml` は")
        add("`t1a_regiontoken base` と宣言している**。両者は別の実験である。")
        add("そのため証拠の優先順を `config.yaml` → `notes.md` に固定した。")
        add("")
        if pairing.get("value_checks"):
            add("#### 引用された基準値との照合")
            add("")
            for c in pairing["value_checks"]:
                mark = "✅ 一致" if c["matched"] else "❌ 不一致"
                add(f"**`{c['denominator']}`** -> `{c['experiment_id']}`")
                add("")
                add(f"- 候補数: {c['n_candidates']} 実験（引用値で切り分けた）")
                add(f"- 引用値: `{c['quoted_mean']}`")
                add(f"- 再現値: `{c['reproduced_mean']}` ({c['reproduced_from']}) … {mark}")
                add(f"- 母集団σ = `{c['population_sigma']}` / 標本σ = `{c['sample_sigma']}`")
                add("")
        add("#### 🔴 同じ基準点が 2 通りのσで引用されている")
        add("")
        add("`S4 base` は `±0.0034` (397 run) と `±0.0028` (33 run) の 2 通りで引用されている。")
        add("実測すると **同一の 3 run** に対する母集団σ (0.002766) と標本σ (0.003387) であり、")
        add("比は √(3/2) = 1.2247 である。")
        add("§10.1 の改善判定は `|Δ| > 1σ` を条件とするため、")
        add("**どちらのσを採るかで有意・非有意の判定が変わりうる**。σの規約は正本で統一が要る。")
        add("")
        add("#### 分母が複数実験に該当するときの切り分け")
        add("")
        add("`frozen_source_tag` で実験を分けた結果、`s4_phase_baseline` は 7 実験になった。")
        add("分母の宣言は 1 つなので、そのままでは確定しない。切り分けは 2 段構えで行う。")
        add("")
        add("1. **凍結特徴ソースの一致** — `notes.md` が対照の条件を")
        add("   「同一土台（凍結backbone/GAP/recipe/seed・neck無し）」と明記している。")
        add("   凍結 backbone を揃えるのは研究者自身が宣言した規則なので、")
        add("   注入 run と同じ `frozen_source_tag` を持つ実験を分母とする。")
        add("2. **引用値による照合** — 1 で決まらないときのみ、")
        add("   `denominator_value_lecun` 等の引用値を再現する部分集合を探す。")
        add("")
        add("### 18.3 確定できた件数")
        add("")
        st = pairing.get("stats") or {}
        add("| 分類 | run 数 |")
        add("|---|---:|")
        for k, v in sorted(st.items(), key=lambda x: -x[1]):
            add(f"| `{k}` | {v} |")
        add("")
        if pairing.get("unresolved"):
            for u in pairing["unresolved"]:
                add(f"- 未解決: {u}")
        else:
            add("**分母を宣言している run はすべて実験に解決できた（未解決 0 件）。**")
        add("")
        add("`no_denominator_declared` の run は `config.yaml` にも `notes.md` にも")
        add("分母の記載が無い。推測で埋めず `control_of` は null のままにしてある。")
        add("")
        add("#### 🔴 paired-σ がほぼ計算できない")
        add("")
        add("`notes.md` は 439 run で「3-seed 揃ったら **paired-σ(対seed差)** で §10.1 判定」と")
        add("書いているが、実際に `paired` で計算できた実験は **わずか 1 件**である。")
        add("")
        add("理由は基準点実験の構成にある:")
        add("`phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42` は")
        add("**17 run / 3 seed（1 つの seed に最大 7 run）**であり、")
        add("seed ごとに 1 本ずつ対応させることができない。")
        add("どの run を代表とするかを決める規約はどの証跡ファイルにも無い。")
        add("")
        add("したがって残り 155 実験は `unpaired`（平均の差のみ）とし、")
        add("**`delta_pstd_*` は空欄**にしてある。対応が取れない以上 paired-σ は定義できず、")
        add("それらしい数値を入れることは捏造にあたる。")
        add("**§10.1 の `|Δ| > 1σ` 判定は、現状の証跡では実行できない。**")
        add("")
    add("### 18.4 `arm=control` を使っていない理由")
    add("")
    add("スキーマは `injection` / `control` / `baseline` / `unknown` を許すが、")
    add("**自らを「対照」と宣言している run は 1 件も無い**。")
    add("実在するのは「Δ の基準点として参照されている実験」であり、これを `baseline` とした。")
    add("`control` を使うと、存在しない設計意図を捏造することになる。")
    add("")
    add("### 18.5 Δ の計算方式")
    add("")
    add("- `paired`: 注入側・対照側とも **seed ごとにちょうど 1 run** で seed 集合が一致するとき。")
    add("  seed ごとの差を取り、その平均を `delta_<metric>`、母集団σを `delta_pstd_<metric>` とする。")
    add("- `unpaired`: 上記を満たさないとき。平均の差だけを出し、")
    add("  **`delta_pstd_<metric>` は空欄**にする（対応が取れない以上 paired-σ は定義できない）。")
    add("- どちらで計算したかは `delta_method` 列に必ず記録する。混同してはならない。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 19. `per_class.csv` を使うときの必須の注意")
    add("")
    add("per-class の値は 573 個の JSON に分散していて横断分析に使えなかったため、")
    add("`runindex/per_class.csv` に long 形式（1 行 = 1 run × 1 クラス）で 1 ファイル化した。")
    add("")
    n_tool = sum(1 for r in records if r["per_class_kind"] == "tool")
    n_phase = sum(1 for r in records if r["per_class_kind"] == "phase")
    add(f"- `per_class_kind=tool` : {n_tool} run × 15 クラス（術具 **AP**）")
    add(f"- `per_class_kind=phase`: {n_phase} run × 9 クラス（工程 **F1**）")
    add("")
    add("**この 2 つを混ぜて集計してはならない。** 指標の種類が違う（AP と F1）。")
    add("ファイル名は両方とも `per_class_ap.json` なので、名前では判別できない。")
    add("必ず `per_class_kind` / `per_class_metric` で分離すること。")
    add("")
    add("`value` が空欄の行は元が `NaN` だったもので、`is_nan=True` が立っている。")
    add("術具側の `NaN` は **val split に GT が 1 件も無いクラス**を意味する（0 ではない）。")
    add("平均を取るときは `nanmean` 相当（空欄を除外）にすること。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 20. metrics.json / 命名規約に 2 系統ある")
    add("")
    add("`g2_followup_2026-07-29` / `g2_main_2026-07-29_lecun` 群 (42 run) は")
    add("他の群と **スキーマも命名も違う**。")
    add("")
    add("| 観点 | 主系統 | g2_* 系統 |")
    add("|---|---|---|")
    add("| ディレクトリ名 | `<step>_<seq3>_<desc>_seed<N>` | `<desc>_seed<N>`（seq が無い） |")
    add("| split の表現 | `val/<metric>` / `phase_<metric>` | `\"val\": {\"phase_<metric>\": …}` の入れ子 |")
    add("| per-class | `per_class_ap.json` | `val.phase_per_class_f1`（metrics.json 内） |")
    add("| 付随ファイル | `command.sh` / `config.yaml` / `notes.md` / `git_commit.txt` | `env.json` のみ |")
    add("")
    add("両方を収穫できるようにした。出所は次の列で区別できる。")
    add("")
    add("- `provenance.name` … `from_dirname_step_seq_desc_seed` / `from_dirname_desc_seed_no_seq`")
    add("- `per_class_source` … `…/per_class_ap.json` か `…/metrics.json#val.phase_per_class_f1`")
    add("")
    add("**この群には `config.yaml` が無いため対照宣言も凍結源も取れない。**")
    add("`control_of` は null、`frozen_source_tag` も null である。")
    add("`metrics.json` の `system` フィールド（`base` / `bboxROI` / `shuffleROI`）が")
    add("arm を表している可能性があるが、対照関係を明示した記録ではないため採用していない。")
    add("値は `attributes` に保持してある。")
    add("")
    add("### 20.1 🔴 指標でないものが `metric.*` 列に入っていた（修正済み）")
    add("")
    add("`metrics.json` のネスト値と文字列値がそのまま `metrics` に入っていたため、")
    add("`index.csv` に `metric.val = {'phase_accuracy': …}` のような")
    add("**辞書リテラル**や `metric.system = base` のような文字列が書かれていた。")
    add("旧 573 run でも `b2b_rescore_*` の `denominator` / `method` が文字列で入っていた。")
    add("")
    add("「指標とは数値である」という不変条件を実装に入れ、")
    add("数値以外は `attributes` / `metrics_nested` に分離した（情報は捨てていない）。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 21. σ の定義 — 母集団σと標本σを両方出す")
    add("")
    add("`<metric>_pstd` が母集団σか標本σか判別できず、`|Δ| > 1σ` 判定が")
    add("規約次第で反転しうる状態だった（§18.2）。両方を明示的に出すことにした。")
    add("")
    add("| 列 | 定義 | Python |")
    add("|---|---|---|")
    add("| `<metric>_pstd` | **母集団σ** (ddof=0) | `statistics.pstdev` |")
    add("| `<metric>_sstd` | **標本σ** (ddof=1) | `statistics.stdev` |")
    add("| `<metric>_n` | 集約した値の個数 | |")
    add("| `delta_pstd_<metric>` | Δ の母集団σ | paired: 差の pstdev / unpaired: √(σ_inj²+σ_ctl²) |")
    add("| `delta_sstd_<metric>` | Δ の標本σ | 同上を標本σで |")
    add("| `abs_delta_over_sigma_<metric>` | **\\|Δ\\| / `delta_pstd_<metric>`** | 母集団σ基準 |")
    add("")
    add("### 21.1 規約の違いが実際の判定に与える影響（実測）")
    add("")
    add("`accuracy` について両方の規約で判定件数を出した。")
    add("")
    exp_rows = None
    try:
        _h, exp_rows = build_experiments(records)
    except Exception:  # noqa: BLE001
        exp_rows = None
    if exp_rows:
        pairs = [
            (r.get("delta_accuracy"), r.get("delta_pstd_accuracy"), r.get("delta_sstd_accuracy"))
            for r in exp_rows
            if isinstance(r.get("delta_accuracy"), (int, float))
            and r.get("delta_pstd_accuracy")
            and r.get("delta_sstd_accuracy")
        ]
        add("| 閾値 | 母集団σ基準 | 標本σ基準 | 判定が反転 |")
        add("|---|---:|---:|---:|")
        for k in (1, 2, 3):
            p = sum(1 for d, ps, ss in pairs if abs(d) / ps >= k)
            s = sum(1 for d, ps, ss in pairs if abs(d) / ss >= k)
            fl = sum(1 for d, ps, ss in pairs if abs(d) / ps >= k and abs(d) / ss < k)
            add(f"| {k}σ | {p} | {s} | **{fl}** |")
        add("")
        if pairs:
            ratios = sorted(ss / ps for _, ps, ss in pairs)
            med = ratios[len(ratios) // 2]
            add(f"対象 {len(pairs)} 実験。標本σ/母集団σ の実測中央値 = **{med:.4f}**。")
        add("")
    add("**§10.1 が使う 1σ 基準では、現在の実データで判定は 1 件も反転しない。**")
    add("理由は σ の合成にある。注入側は n=3（比 √(3/2)=1.2247）だが")
    add("対照側は n が大きく（比が 1 に近い）、合成 σ では差が薄まる。")
    add("")
    add("ただし `notes.md` に手書きされた `0.8986±0.0028` と `±0.0034` は")
    add("**単一の集計値そのもの**なので 22% の差がそのまま出る。")
    add("手書きの値を引用するときは規約の確認が要る。")
    add("")
    add("### 21.2 🔴 リポジトリ内に σ の規約が **2 系統併存**している")
    add("")
    add("`scripts/` と `src/` を実測した結果:")
    add("")
    add("| 規約 | 出現箇所 | 主な使用層 |")
    add("|---|---:|---|")
    add("| 母集団σ (`pstdev` / `pvariance`) | **48** | §10.1 判定・レポート生成 |")
    add("| 標本σ (`statistics.stdev` / `ddof=1`) | **16** | 解析・監査 (`scripts/analysis/*`) |")
    add("")
    add("**§10.1 の判定を実装している箇所は母集団σで一致している:**")
    add("")
    add("| ファイル:行 | 記述 |")
    add("|---|---|")
    add("| `scripts/paired_sigma_3seed.py:7,80` | \\|mean(Δ)\\| > pstdev(Δ) かつ 全 detector_seed 同符号 |")
    add("| `scripts/analyze_t1a_factorial_ablation.py:13,81` | §10.1: \\|meanΔ\\|>pstdev かつ全 seed 同符号 |")
    add("| `scripts/report_t1a_boundary.py:5,59` | \\|mean\\|>pstdev かつ 3-seed 同符号 |")
    add("| `scripts/report_daux_paired.py:69,114` | \\|mean\\|>pstdev かつ 3-seed 同符号 |")
    add("| `src/egosurgery/utils/transfer_delta_report.py` | pstdev（haux/taux 系レポートの単一情報源） |")
    add("| `scripts/run_haux_oracle_gate.sh:14` / `run_taux_problemA.sh:76` | 同上 |")
    add("")
    add("**一方、解析・監査層は標本σを使っている:**")
    add("`scripts/analysis/delta_allrun_recompute.py:157` / `delta_convention_audit.py:132` /")
    add("`g1_power_analysis.py:68` / `g2_report.py:166,179,452`（`np.std(..., ddof=1)`）/")
    add("`scripts/analyze_phase_coupling.py:93,154,162`。")
    add("")
    add("**「Δ の規約を監査する」スクリプト自身が、判定側と違うσを使っている。**")
    add("")
    add("### 21.2.1 🔴 **明文の規約は ddof=1、実装は ddof=0** — 両者が逆を向いている")
    add("")
    add("正本の研究計画（`docs/m2_plan_rewrite/`）は §10.1 の 1σ を")
    add("「同一 eval recipe での 3-seed std」としか書かず種類を明示していないが、")
    add("**スコープを限った明示宣言は複数あり、そのすべてが ddof=1（標本σ）を指す**:")
    add("")
    add("| 出典 | 記述 |")
    add("|---|---|")
    add("| `scripts/analyze_phase_coupling.py:21` | 「改善主張は §10.1 に従い \\|Δ\\| > 1σ のときのみ。**1σ は base 3-seed の標本(n-1)標準偏差**」 |")
    add("| `src/egosurgery/metrics/delta.py:111,131` | 「標準偏差は**不偏標準偏差（ddof=1）**」/ `arr.std(ddof=1)` |")
    add("| `docs/experiment_log.md:1742` | 「n=3, **ddof=1**」 |")
    add("")
    add("**実験ログの数値も ddof=1 で書かれている**（実測で照合）:")
    add("")
    add("```")
    add("docs/experiment_log.md:440   S4' = acc 0.9142 ± 0.0017")
    add("  実測 (s4_phase_baseline_004/005/006 _neck):")
    add("    mean = 0.9142")
    add("    pstdev (ddof=0) = 0.001426   -> 0.0014  ✗ 一致しない")
    add("    stdev  (ddof=1) = 0.001746   -> 0.0017  ✅ 一致")
    add("```")
    add("")
    add("一方 §10.1 の**判定を実装している** 7 箇所は `pstdev`（ddof=0）である。")
    add("つまり **文書が定めた規約と、判定コードが使っている規約が食い違っている。**")
    add("これは「どちらか未定」ではなく「二つが並存し矛盾している」状態である。")
    add("")
    add("`abs_delta_over_sigma_<metric>` と `verdict_10_1` は **母集団σ**（ddof=0）を分母に、")
    add("`verdict_10_1_sstd` は **標本σ**（ddof=1）を分母にしている。")
    add("**どちらを正本とするかは harvester が決めることではない**ため両方出し、")
    add("結論が食い違う実験を `verdict_10_1_agree = False` で列挙している（backlog B-9 / B-18）。")
    add("")
    add("なお件数の数え方に注意: 上の「48 / 16」は docstring・コメント・print 文を含む")
    add("全 grep ヒットである。実コード行だけに絞ると概ね 21 / 15 になる。")
    add("")
    add("なお `notes.md` / `config.yaml` の `0.8986±0.0034` は書き出し時に計算された値ではなく、")
    add("`scripts/train_*.py` にハードコードされた文字列リテラルである。")
    add("値が更新されない構造なので、引用するときは実測と突き合わせること")
    add("（`experiments.csv` の `control_note_value` 列に保持してある）。")
    add("")
    add("また `scripts/compute_delta.py` と `scripts/export_paper_tables.py` は")
    add("**0 バイトの空ファイル**（未実装 scaffold）である。`Makefile` の `delta` /")
    add("`tables` ターゲットはこれらを呼ぶので、現状では何もしない。")
    add("")
    add("### 21.3 🔴 §10.1 は σ 条件だけではない — **同符号条件**がある")
    add("")
    add("上記 7 箇所すべてが判定を **2 条件**で書いている:")
    add("")
    add("> `|mean(Δ)| > pstdev(Δ)` **かつ** `全 seed 同符号`")
    add("")
    add("第 2 条件は seed ごとの Δ が要るので **paired のときしか判定できない**。")
    add("`delta_same_sign_<metric>` 列に出しているが、埋まるのは paired の実験だけである。")
    add("")
    add("**したがって `unpaired_pooled` の 131 実験は、σ 条件は評価できても")
    add("§10.1 の判定を完成させることができない。**")
    add("`abs_delta_over_sigma_*` が大きくても「§10.1 で有意」と結論してはいけない。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 22. paired-σ の宣言と実行可能性の乖離")
    add("")
    add("全件は `anomalies/paired_feasibility.csv`（1 行 = 1 実験）。")
    add("")
    fh_, fr = build_paired_feasibility(records)
    if fr:
        declared = sum(1 for r in fr if r.get("paired_declared"))
        now = sum(1 for r in fr if r.get("pairable_now"))
        after = sum(1 for r in fr if r.get("pairable_after_dedup"))
        add(f"- `control_of` が確定した実験: **{len(fr)}**")
        add(f"- そのうち `notes.md` / `config.yaml` が **paired-σ 判定を宣言**: **{declared}**")
        add(f"- 実際に paired-σ を計算できる: **{now}**")
        add(f"- **seed ごとに代表 1 本を選ぶ規約を入れれば計算できる: {after}**")
        add("")
        add("### 22.1 何が paired を阻んでいるか")
        add("")
        add("| 原因 | 実験数 |")
        add("|---|---:|")
        for k, v in Counter(r.get("blocking_reason") or "(阻害なし)" for r in fr).most_common():
            add(f"| `{k}` | {v} |")
        add("")
        add("**支配的原因は対照実験の再実行が畳まれていないこと**であり、")
        add("注入側の seed 記録誤りではない（§23 のとおり seed の食い違いは 0 件）。")
        add("")
        tot = sum(r.get("n_runs_injection", 0) for r in fr)
        pab = sum(r.get("n_runs_injection_pairable", 0) for r in fr)
        add(f"注入側 run {tot} 本のうち、対照に同じ seed が存在するのは **{pab} 本**。")
        add(f"残り {tot - pab} 本は対照側に対応する seed が無く、畳んでも paired にできない。")
        add("")
        add("### 22.2 🔴 「paired と宣言されているが unpaired でしか計算できない実験」")
        add("")
        mism = [r for r in fr if r.get("paired_declared") and not r.get("pairable_now")]
        add(f"**{len(mism)} 実験**が該当する。§10.1 の判定を paired-σ で行ったと")
        add("読める記述が `notes.md` にあるが、実際にはできていない。")
        add("")
        add("| 阻害原因 | 実験数 | 代表例 |")
        add("|---|---:|---|")
        byr: dict[str, list[str]] = defaultdict(list)
        for r in mism:
            byr[r.get("blocking_reason") or ""].append(r["experiment_id"])
        for k, v in sorted(byr.items(), key=lambda x: -len(x[1])):
            add(f"| `{k}` | {len(v)} | `{sorted(v)[0]}` |")
        add("")
        add("現在の `experiments.csv` はこれらを `delta_method=unpaired` /")
        add("`delta_sigma_source=unpaired_pooled` と明示している。")
        add("unpaired の σ は paired-σ より大きく出る保守的な推定なので、")
        add("**σ 条件については unpaired で満たせば paired でも満たす**（逆は言えない）。")
        add("ただし §21.3 のとおり **同符号条件は unpaired では判定できない**ため、")
        add("これらの実験について §10.1 の判定を完成させることはできない。")
        add("")
        add("### 22.3 paired が成立した実験の §10.1 判定")
        add("")
        pr = [r for r in fr if r.get("pairable_now")]
        add(f"現時点で paired-σ を計算できるのは **{len(pr)} 実験**。")
        add("`accuracy` について 2 条件を両方適用した結果は次のとおり。")
        add("")
        if exp_rows:
            paired_rows = [
                r
                for r in exp_rows
                if r.get("delta_method") == "paired"
                and isinstance(r.get("delta_accuracy"), (int, float))
            ]
            if paired_rows:
                add("| experiment_id | Δacc | \\|Δ\\|/σ | 同符号 | §10.1 |")
                add("|---|---:|---:|---|---|")
                for r in sorted(paired_rows, key=lambda x: -abs(x["delta_accuracy"])):
                    ratio = r.get("abs_delta_over_sigma_accuracy")
                    same = r.get("delta_same_sign_accuracy")
                    ok = bool(ratio and ratio > 1 and same)
                    add(
                        f"| `{r['experiment_id']}` | {r['delta_accuracy']:+.5f} | "
                        f"{ratio:.2f} | {'✓' if same else '✗'} | "
                        f"{'**有意**' if ok else '非有意'} |"
                    )
                add("")
        add("これが現在の証跡で**実際に完成できる §10.1 判定のすべて**である。")
        add("")

    # ---------------------------------------------------------------- #
    add("## 23. seed の出所 — run の学習 seed に誤りは無い")
    add("")
    add("§17.0 の「`notes.md` の凍結源 seed 記載が虚偽」を受けて、")
    add("**run 自身の学習 seed** が汚染されていないかを全件突き合わせた。")
    add("証拠は `command.sh` の `--seed` / `seed=`、`config.yaml` の `seed`、")
    add("そして `metrics.json` の `seed`（g2_* 群は前 2 つを持たないため）。")
    add("`notes.md` は虚偽の実績があるため証拠に使っていない。")
    add("")
    agree = Counter(r.get("seed_agreement") for r in records)
    add("| seed_agreement | run 数 | 意味 |")
    add("|---|---:|---|")
    add(f"| `agree` | {agree.get('agree', 0)} | ディレクトリ名と他証拠が一致 |")
    add(
        f"| `unverified_no_other_evidence` | {agree.get('unverified_no_other_evidence', 0)} | "
        "`command.sh` も `config.yaml` も無い（g2_* 群） |"
    )
    add(f"| `no_seed_in_dirname` | {agree.get('no_seed_in_dirname', 0)} | 命名規約外 |")
    add(f"| **`conflict`** | **{agree.get('conflict', 0)}** | **食い違い** |")
    add("")
    add("**食い違いは 0 件。** したがって Δ の seed 対応が誤っている可能性は排除できる。")
    add("§17.0 の誤記は**凍結検出器の seed** の話であって、run の学習 seed ではない。")
    add("")
    add("### 23.1 `frozen_source.seed` は信用できない（実測）")
    add("")
    fsd = [r for r in records if r.get("frozen_source_seed_declared") is not None]
    contra = [
        r
        for r in fsd
        if r.get("frozen_source_tag")
        and f"seed{r['frozen_source_seed_declared']}" not in r["frozen_source_tag"]
    ]
    add(f"- `config.yaml` に `frozen_source.seed` を持つ run: **{len(fsd)}**")
    add(f"- そのうち実際の cache パスと**矛盾**する run: **{len(contra)}**")
    add("")
    add("矛盾例: 宣言は `seed: 42` だが cache は `relation_detr_augstrong_seed123`。")
    add("`frozen_source_tag` は cache パスからのみ導いており、この宣言は採用していない。")
    add("値は矛盾検出のためだけに `frozen_source_seed_declared` に保持している。")
    add("")
    add("### 23.2 分母が `s4_phase_baseline` である実験の一覧")
    add("")
    s4c = sorted(
        {
            r["control_of"]
            for r in records
            if r.get("control_of") and "s4_phase_baseline" in r["control_of"]
        }
    )
    s4exp: dict[str, set[str]] = defaultdict(set)
    for r in records:
        if r.get("control_of") in s4c and r.get("experiment_id"):
            s4exp[r["control_of"]].add(r["experiment_id"])
    n_exp = sum(len(v) for v in s4exp.values())
    n_run = sum(1 for r in records if r.get("control_of") in s4c)
    add(f"`s4_phase_baseline` を `control_of` に持つ実験は **{n_exp}**、run は **{n_run}**。")
    add("")
    for c in s4c:
        add(f"- 分母 `{c}` … {len(s4exp[c])} 実験")
    add("")
    add("§17.0 の凍結源誤記は**この分母実験そのもの**で起きている。ただし:")
    add("")
    add("1. `frozen_source_tag` は `config.yaml` の cache パスから導いており、")
    add("   誤っている `notes.md` / `frozen_source.seed` は使っていない。")
    add("2. `experiment_id` は `frozen_source_tag` を含むので、")
    add("   異なる凍結源の run は**別の分母実験**に分かれている。")
    add("")
    add("したがって Δ の分母は cache パス基準で正しく分離されている。")
    add("**残るリスクは cache パス自体が実行時の実態と違う場合**だが、")
    add("これを検証できる証跡（実行時の環境変数の記録）は repo に存在しない。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 24. seed 代表値の畳み込み (dedup) と §10.1 判定")
    add("")
    add("### 24.1 代表値の取り方")
    add("")
    add("対照実験は 1 つの seed に最大 7 run を持つため、畳まないと seed 対応が付かず")
    add("paired-σ を計算できなかった（§22）。`experiments.csv` の Δ は")
    add(f"**`{DEFAULT_DEDUP_RULE}`** を既定として seed ごとに 1 値へ畳んでいる")
    add("（`delta_dedup_rule` 列に記録）。")
    add("")
    add("| 規則 | 内容 | 採否 |")
    add("|---|---|---|")
    add("| `mean` | seed 内の全 run の平均 | **既定** |")
    add("| `latest` | seq が最大の run | 感度分析のみ |")
    add("| `first` | seq が最小の run | 感度分析のみ |")
    add("| `best` | 比較する指標が最良の run | **実装しない** |")
    add("")
    add("`mean` を既定にした理由:")
    add("")
    add("1. 順序に依存しない（`git_commit.txt` や seq の記録が信用できない run がある）")
    add("2. 特定の 1 本を選ばないので「どれを選ぶか」の恣意性が入らない")
    add("3. 再実行のばらつきを捨てずに平均へ織り込む")
    add("")
    add("**`best` を実装しない理由**: 比較する指標そのもので代表を選ぶと Δ が")
    add("系統的に偏る（選択バイアス）。対照側で best を選べば Δ は大きく、")
    add("注入側で選べば小さく出る。研究公正性の観点から提供しない。")
    add("")
    add("### 24.2 代表値の取り方は結論を変えない（感度分析）")
    add("")
    dh_, dr_ = build_dedup_sensitivity(records)
    if dr_:
        piv: dict[str, dict[str, str]] = defaultdict(dict)
        dlt: dict[str, dict[str, float]] = defaultdict(dict)
        for r in dr_:
            piv[r["experiment_id"]][r["dedup_rule"]] = r["verdict_pstd"]
            if isinstance(r.get("delta"), (int, float)):
                dlt[r["experiment_id"]][r["dedup_rule"]] = r["delta"]
        same = sum(1 for v in piv.values() if len(set(v.values())) == 1)
        add(f"3 規則すべてで §10.1 判定が一致する実験: **{same} / {len(piv)}**")
        add("")
        diffs = [
            abs(d["mean"] - d[k])
            for d in dlt.values()
            for k in ("latest", "first")
            if "mean" in d and k in d
        ]
        if diffs:
            add(f"ただし Δ の値自体は動く（`mean` との差の最大 = **{max(diffs):.6f}**）。")
            add("判定が変わらないのは σ も同時にスケールするためである。")
            add("**Δ の絶対値を引用するときは `delta_dedup_rule` を併記すること。**")
        add("")
        add("全件は `anomalies/dedup_sensitivity.csv`。")
        add("")
    add("### 24.3 §10.1 判定の結果")
    add("")
    add("判定条件は 2 つ（§21.3）。**両方**満たしたときだけ `significant`。")
    add("")
    add("> `|mean(Δ)| > σ` **かつ** `全 seed 同符号`")
    add("")
    if exp_rows:
        vp = Counter(r.get("verdict_10_1") for r in exp_rows if r.get("verdict_10_1"))
        vs = Counter(r.get("verdict_10_1_sstd") for r in exp_rows if r.get("verdict_10_1_sstd"))
        add("| 判定 | 母集団σ (ddof=0) | 標本σ (ddof=1) |")
        add("|---|---:|---:|")
        for k in ("significant", "not_significant", "undecidable"):
            add(f"| `{k}` | {vp.get(k, 0)} | {vs.get(k, 0)} |")
        add("")
        flip = [r for r in exp_rows if r.get("verdict_10_1") and not r.get("verdict_10_1_agree")]
        add(f"**σ の規約で結論が変わる実験: {len(flip)} 件**")
        add("")
        for r in flip:
            m = r["verdict_metric"]
            add(f"- `{r['experiment_id']}`（指標 `{m}`）")
            add(
                f"  - Δ = {r.get(f'delta_{m}'):+.6f} / "
                f"母集団σ = {r.get(f'delta_pstd_{m}'):.6f} -> **{r['verdict_10_1']}** / "
                f"標本σ = {r.get(f'delta_sstd_{m}'):.6f} -> **{r['verdict_10_1_sstd']}**"
            )
        add("")
        und = [r for r in exp_rows if r.get("verdict_10_1") == "undecidable"]
        if und:
            add(f"`undecidable` は {len(und)} 件。いずれも paired にできない実験である。")
            for r in und:
                add(f"- `{r['experiment_id']}` … {r.get('verdict_10_1_reason')}")
            add("")
        ns = [r for r in exp_rows if r.get("verdict_10_1") == "not_significant"]
        if ns:
            same_sign_fail = sum(
                1
                for r in ns
                if r.get("verdict_10_1_reason") == "全 seed 同符号ではない"
            )
            add(
                f"`not_significant` {len(ns)} 件のうち **{same_sign_fail} 件は同符号条件で落ちている**"
                "（σ 条件は満たしている）。"
            )
            add("σ だけを見て有意と判断すると誤る典型である。")
            add("")
    add("全指標の判定は `runindex/verdicts.csv`（1 行 = 1 実験 × 1 指標）。")
    add("")

    # ---------------------------------------------------------------- #
    add("## 25. 🔴🔴 最重要: paired-σ は seed 効果ではなく**非決定性**を測っている")
    add("")
    add("§24 で paired-σ が計算できるようになったが、**その σ が何を測っているか**には")
    add("重大な但し書きがある。Δ を解釈する前に必ず読むこと。")
    add("")
    add("### 25.1 同一条件が再現しない（実測）")
    add("")
    add("`s4_phase_baseline_015` と `_017` は次がすべて一致する:")
    add("")
    add("| 項目 | 値 |")
    add("|---|---|")
    add("| `git_commit.txt` | `bd0609749afdfa2a`（両者同一） |")
    add("| `config.yaml` の sha256 | `9cf8c2dde6920f01`（バイト一致） |")
    add("| `command.sh` | `python scripts/train_s4_tecno.py --seed 42`（同一） |")
    add("| `server.txt` | `efros`（同一） |")
    add("")
    add("それでも結果は違う:")
    add("")
    add("```")
    add("phase_accuracy   0.9042904290429042  vs  0.8970297029702970   (Δ = 0.00726)")
    add("phase_macro_f1   0.7405981456025096  vs  0.6571673826301749   (Δ = 0.08343)")
    add("epoch (best)     49                  vs  31")
    add("```")
    add("")
    add("### 25.2 seed は分散を制御できていない")
    add("")
    add("対照実験（17 run / seed42×7・123×5・456×5）で、")
    add("**同一 seed 内のばらつきが seed 間のばらつきを全指標で上回る**:")
    add("")
    add("| 指標 | within-seed σ | between-seed σ | 比 |")
    add("|---|---:|---:|---:|")
    add("| accuracy | 0.004647 | 0.003385 | **1.37** |")
    add("| macro_f1 | 0.020214 | 0.008879 | **2.28** |")
    add("| jaccard | 0.019112 | 0.007814 | **2.45** |")
    add("| edit_score | 1.981335 | 1.478973 | **1.34** |")
    add("| seg_f1_50 | 0.031471 | 0.019595 | **1.61** |")
    add("")
    add("### 25.3 原因 — GPU の決定性が一切制御されていない")
    add("")
    add("```python")
    add("# scripts/train_s4_tecno.py:192-195")
    add('device = torch.device("cuda" if torch.cuda.is_available() else "cpu")')
    add("random.seed(args.seed)")
    add("np.random.seed(args.seed)")
    add("torch.manual_seed(args.seed)      # ← CPU 側のみ")
    add("```")
    add("")
    add("`torch.cuda.manual_seed_all` / `torch.use_deterministic_algorithms` /")
    add("`cudnn.deterministic` / DataLoader の `worker_init_fn` / `generator` /")
    add("`PYTHONHASHSEED` は **1 つも設定されていない**。")
    add("さらに 50 epoch の best-of-N 選択（`:263`）が非決定性を増幅する")
    add("（best epoch が 31〜50 に散る）。")
    add("")
    add("リポジトリ自身の診断ツール `scripts/analysis/diag_same_seed_variance.py` も")
    add("同じ結論を出す: `N1 VERDICT: CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM`。")
    add("")
    add("### 25.4 Δ の解釈への含意")
    add("")
    add("1. **paired-σ は「seed を変えたときの変動」ではなく「同じ設定で回し直したときの")
    add("   変動」を主に測っている。** §10.1 の「3-seed の σ」という想定は成立していない。")
    add("2. `significant` と出た実験も、**測っているのは注入効果 + 非決定性**である。")
    add("   Δ が within-seed σ（accuracy で 0.0046）より小さい主張は特に慎重に扱うこと。")
    add("3. seed ごとに **1 本を選ぶ**代表規約（`latest` / `first` / mtime 最大）は、")
    add("   within-seed 分布から 1 標本を引くことに等しい。")
    add("   **`mean` を既定にしたのはこの理由による**（within-seed ノイズを平均で潰す）。")
    add("   同じ発想はリポジトリ内に先例がある —")
    add("   `scripts/paired_sigma_3seed.py:5`「phase_seed を平均 → phase 学習の非決定性を除去」。")
    add("")
    add("### 25.5 代表選択の規約がリポジトリ内で 4 つに割れている")
    add("")
    add("| 方式 | 出典 |")
    add("|---|---|")
    add("| seq 最大 | `src/egosurgery/utils/transfer_delta_report.py:55,86-87` |")
    add("| mtime 最大 | `scripts/report_daux_paired.py:12-13,43-47` |")
    add("| 辞書順末尾 | `scripts/report_t1a_boundary.py:46-49` / `compare_causal_decode.py:76` |")
    add("| 代表を選ばず平均 | `scripts/paired_sigma_3seed.py:5,59-60` |")
    add("| **規約を決めないと明記** | `scripts/analysis/delta_allrun_recompute.py:4-10` |")
    add("")
    add("なお mtime 方式は使えない。`metrics.json` の mtime は git チェックアウト時刻")
    add("（全件 2026-07-31 14:49）であり実験の新旧を表していない。")
    add("")
    add("**根本対処は「非決定性を制御して再実行する」ことであり、")
    add("代表値の選び方を工夫することではない。**（backlog B-20）")
    add("")

    # ---------------------------------------------------------------- #
    add("## 26. 非決定性の棚卸しと影響範囲")
    add("")
    add("§25 の欠陥が `train_s4_tecno.py` 固有かを全スクリプトで確認した。")
    add("全件は `anomalies/determinism_audit.csv`。")
    add("")
    add("### 26.1 🔴 決定的になり得る学習スクリプトは **1 本も無い**")
    add("")
    dh_, dr_ = build_determinism_audit(records)
    cuda = [r for r in dr_ if r.get("uses_cuda")]
    add(f"監査 {len(dr_)} スクリプト / うち CUDA を使う **{len(cuda)}** 本 / ")
    add(f"`can_be_deterministic = True` は **{sum(1 for r in dr_ if r.get('can_be_deterministic'))}** 本。")
    add("")
    add("| 制御項目 | 設定している本数 |")
    add("|---|---:|")
    for k in DETERMINISM_CHECKS:
        add(f"| `{k}` | {sum(1 for r in cuda if r.get(k))} / {len(cuda)} |")
    add("")
    add("**`torch.use_deterministic_algorithms` はどのスクリプトも呼んでいない。**")
    add("これが無い限り GPU 上で bit 単位の再現は保証されないため、")
    add("`can_be_deterministic` は全件 `False` になる。")
    add("")
    add("### 26.1.1 制御の張り方が 2 系統に分かれている")
    add("")
    add("`seed_setup_via` 列で区別できる。")
    add("")
    via = Counter(r.get("seed_setup_via") for r in dr_ if r.get("seed_setup_via"))
    add("| seed_setup_via | 本数 | 意味 |")
    add("|---|---:|---|")
    add(f"| `direct` | {via.get('direct', 0)} | ファイル内で直接 seed を張る（`scripts/train_*.py` 系）|")
    add(
        f"| `seed_everything` | {via.get('seed_everything', 0)} | "
        "`src/egosurgery/utils/seed.py` のヘルパ経由 |"
    )
    add(
        f"| `seed_everything+delegates_to_engines` | {via.get('seed_everything+delegates_to_engines', 0)} | "
        "ヘルパを呼びつつ更に委譲もする |"
    )
    add(
        f"| `delegates_to_engines` | {via.get('delegates_to_engines', 0)} | "
        "自分では触らず trainer に委譲（`src/egosurgery/train.py`）|"
    )
    add(f"| `none` | {via.get('none', 0)} | seed を張らない |")
    add("")
    add("**`seed_everything()` は 6 項目を設定している**")
    add("（`random` / `PYTHONHASHSEED` / `numpy` / `torch.manual_seed` /")
    add("`torch.cuda.manual_seed_all` / `cudnn.deterministic=True` / `cudnn.benchmark=False`）。")
    add("したがって Hydra 経路（`src/egosurgery/`）は `scripts/train_*.py` 系より制御が厚い。")
    add("")
    add("> ⚠️ **この表はファイル単位の静的解析である。** 委譲は 1 段だけ追っている")
    add("> （`seed_everything` の呼び出しと `_select_trainer` 系の委譲）。")
    add("> `src/egosurgery/train.py` の行は `delegates_to_engines` であり、")
    add("> 実際の制御状況は委譲先 `engines/*_trainer.py` の行を見ること。")
    add("")
    add("一方 `scripts/train_*.py` 系（**`direct`**、run 数で見て大半）は")
    add("CPU 側 3 種のみで **GPU 側の制御が 1 つも無い**。")
    add("")
    n_cuda_runs = sum(r.get("n_runs", 0) for r in cuda)
    add(f"影響を受ける run: **{n_cuda_runs}**（CUDA 学習スクリプトが entrypoint の run）")
    add("")
    add("| スクリプト | run 数 | 欠落している必須項目 |")
    add("|---|---:|---|")
    for r in sorted(cuda, key=lambda x: -x.get("n_runs", 0)):
        if r.get("n_runs"):
            add(f"| `{r['script']}` | {r['n_runs']} | `{r['missing_required']}` |")
    add("")
    add("### 26.2 監査できなかったもの")
    add("")
    miss = [r for r in dr_ if r.get("file_state") != "ok"]
    if miss:
        add("| スクリプト | 状態 | run 数 |")
        add("|---|---|---:|")
        for r in sorted(miss, key=lambda x: (x["file_state"], x["script"])):
            add(f"| `{r['script']}` | `{r['file_state']}` | {r['n_runs']} |")
        add("")
        add("`empty` は 0 バイトの scaffold、`missing` は**この worktree に**実体が無いもの。")
        add("")
        add("`missing` は「存在しない」ではなく「`third_party/` が同期対象外」である")
        add("（`.stglobalignore` が `third_party` を除外。入れ子 `.git` を含むため）。")
        add("本体側 `/home/ubuntu/slocal2/m2/third_party/` には Co-DETR / DAC-DETR /")
        add("DI-MaskDINO / MaskDINO / Mr.DETR / Relation-DETR / Stable-DINO / detrex がある。")
        add("**したがってこれらの run の決定性は runindex 単独では確認できない。**")
        add("")
        add("### 26.2.1 第三者 entrypoint について分かっていること")
        add("")
        add("本体側の実体を読んだ範囲では、制御の状況は自前スクリプトと異なる:")
        add("")
        add("| entrypoint | 状況 |")
        add("|---|---|")
        add("| Relation-DETR | `main.py:123-127` に **完全な決定性ブロック**（`use_deterministic_algorithms` / `worker_init_fn` / `generator`）がある。ただし `--use-deterministic-algorithms` フラグでゲートされており、該当 run の `command.sh` は渡していない。さらに `--mixed-precision fp16` で走っている |")
        add("| detrex | detectron2 の `default_setup` が seed 系と `worker_init_fn` を張るが、`cudnn.deterministic` と `use_deterministic_algorithms` は設定しない |")
        add("")
        add("**フラグ 1 つで決定的にできる経路が存在するのに使われていない**、というのが")
        add("Relation-DETR 経路の状況である。")
        add("")
        add("### 26.2.2 監査表を読むときの注意")
        add("")
        add("| 列 | 注意 |")
        add("|---|---|")
        add("| `dataloader_worker_init_fn` / `dataloader_generator` | **DataLoader を使わないスクリプトには該当しない。** 自前スクリプト 8 本は `DataLoader` を一切使わず、メモリ上の clip リストを `random.shuffle` で並べ替えている。`uses_dataloader` 列で判別すること |")
        add("| `pythonhashseed` | `os.environ[\"PYTHONHASHSEED\"]` への**実行時代入は効かない**。CPython のハッシュ乱択はインタプリタ起動時に確定するため、既に走っているプロセスには影響しない。実効性は `pythonhashseed_effective` 列（シェル側の export を検出）で見ること。**実測では 0 / 20** |")
        add("| `explicitly_disables_determinism` | `src/egosurgery/engines/mmdet_trainer.py` は `mmcfg.randomness = dict(..., deterministic=False, ...)` を明示指定し、**mmengine 側の決定化を止めている**。制御が「無い」のではなく「切っている」 |")
        add("")

    add("### 26.3 影響範囲の定量 — within-seed と between-seed の比較")
    add("")
    add("全件は `anomalies/within_vs_between_seed.csv`（1 行 = 1 実験 × 1 指標）。")
    add("")
    wh_, wr_ = build_within_vs_between(records)
    if wr_:
        exceed = [r for r in wr_ if r["within_exceeds_between"]]
        conf = [r for r in exceed if r["within_is_confounded_by_condition"]]
        clean = [r for r in exceed if not r["within_is_confounded_by_condition"]]
        add(f"- 反復がある (実験 × 指標) の組: **{len(wr_)}**")
        add(f"- そのうち **within > between**: **{len(exceed)}**")
        add(f"  - 条件混在の交絡あり: {len(conf)}")
        add(f"  - 交絡なし（純粋に非決定性）: **{len(clean)}**")
        add("")
        add("**⚠️ 単純に「47 件で within が上回る」と読んではいけない。**")
        add("`b2a_ro_oracle_noise000` のように 1 つの名前に 4 水準の条件が混ざっている実験")
        add("（§7.3）では、within-seed のばらつきは非決定性ではなく**条件差**である。")
        add("`within_is_confounded_by_condition` 列で切り分けること。")
        add("")
        add("| step | 組数 | 比の中央値 | 比の最大 |")
        add("|---|---:|---:|---:|")
        bystep: dict[str, list[float]] = defaultdict(list)
        for r in clean:
            bystep[str(r["step"])].append(r["ratio_within_over_between"])
        for s, v in sorted(bystep.items(), key=lambda x: -statistics.median(x[1])):
            add(f"| `{s}` | {len(v)} | {statistics.median(v):.3f} | {max(v):.3f} |")
        add("")
        add("### 26.4 🔴 汚染された 1 つの分母が 117 実験に伝播している")
        add("")
        add("Δ の σ は注入側と対照側の**合成**なので、対照が汚染されていれば")
        add("それを分母に使う全実験の σ が汚染される。")
        add("")
        add("対照実験 `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`")
        add("の within/between 比は **accuracy 1.373 / macro_f1 2.277**（交絡なし）。")
        add("この実験を `control_of` に持つ実験がその比を継承する。")
        add("")
    if exp_rows:
        si = Counter(
            r.get("sigma_interpretation") for r in exp_rows if r.get("control_of")
        )
        add("| `sigma_interpretation` | 実験数 |")
        add("|---|---:|")
        for k in ("mixed_with_nondeterminism", "seed_effect", "unknown"):
            add(f"| `{k}` | {si.get(k, 0)} |")
        add("")
        add(f"**`control_of` を持つ {sum(si.values())} 実験のうち "
            f"{si.get('mixed_with_nondeterminism', 0)} の σ は seed 効果を測っていない。**")
        add("")
        sig_mixed = sum(
            1
            for r in exp_rows
            if r.get("verdict_10_1") == "significant"
            and r.get("sigma_interpretation") == "mixed_with_nondeterminism"
        )
        add(f"うち `verdict_10_1 = significant` は **{sig_mixed}** 件。")
        add("これらは「§10.1 の条件は満たすが、σ が想定どおりのものではない」状態である。")
        add("**判定を無効とするか、非決定性を制御して再実行するかは研究上の判断**であり、")
        add("harvester は判定を消さずに `sigma_interpretation` で印を付けるに留める。")
        add("")

    # ---------------------------------------------------------------- #
    add("## 27. 論点: 「全 seed 同符号」条件は dedup 後も同じ意味か")
    add("")
    add("**これは判断を仰ぐための論点整理であり、harvester は定義を変えていない。**")
    add("")
    add("### 27.1 何が変わったか")
    add("")
    add("§24 で seed ごとに複数 run がある場合 `mean` で畳むようにした。その結果:")
    add("")
    add("| | 畳み込み前 | 畳み込み後（現在） |")
    add("|---|---|---|")
    add("| 「全 seed 同符号」の対象 | 個々の run の Δ | **seed 平均どうしの Δ** |")
    add("| 符号を見る個数 | run 数（対照側は最大 7）| seed 数（通常 3） |")
    add("")
    add("### 27.2 🔴 そもそも正本に「同符号」の規定は無い")
    add("")
    add("`docs/m2_plan_rewrite/` を全文検索しても **「同符号」は 0 件**である。")
    add("この条件は 2026-06-20 の運用判断として実験ログに導入された:")
    add("")
    add("> `docs/experiment_log.md:527`")
    add("> 「`scripts/analyze_phase_coupling.py` を **paired-σ 判定に改修**")
    add("> （matched 差の有意性を base 群σでなく **対seed差σ + 全seed同符号**で判定）」")
    add("")
    add("### 27.3 論点")
    add("")
    add("1. **既存実装は「個々の run の Δ」の符号を見ている。**")
    add("   `scripts/report_t1a_boundary.py:57-61` / `report_daux_paired.py:66-73` /")
    add("   `analyze_t1a_factorial_ablation.py:124-125` はいずれも")
    add("   `d = [vals[s] - base[s] for s in SEEDS]`（seed ごとに 1 run）である。")
    add("   **平均してから符号を見る実装はリポジトリ内に無い**")
    add("   （`paired_sigma_3seed.py` は平均するが、平均する軸は phase_seed で")
    add("   符号を見る軸 detector_seed とは別軸）。")
    add("   したがって現在の runindex の方式（符号軸と同じ軸を mean で畳んでから")
    add("   符号を見る）には**先例が無い**。")
    add("2. **平均は符号のばらつきを隠す。** 同一 seed 内で Δ の符号が")
    add("   割れていても、平均の符号は片方に決まる。§25 のとおり同一条件反復の")
    add("   ばらつきが大きいため、これは実際に起こりうる。")
    add("3. **n=3 の同符号条件は偶然一致しやすい。** 効果が無くても")
    add("   3 つの符号が揃う確率は 2 × (1/2)^3 = **25%**。")
    add("   σ 条件と併せた偶然通過率も σ 条件単独からわずかしか下がらず、")
    add("   n=3 では検出力の裏付けとして弱い。")
    add("4. 代替案としては「全 run の Δ の符号が揃う」（より厳しい）、")
    add("   「符号一致率を出す」（連続量にする）などがありうる。")
    add("")
    add("現状は `delta_same_sign_<metric>`（seed 平均ベース）を出しており、")
    add("`delta_n_seeds_<metric>` で何個の符号を見たかが分かる。")
    add("")
    add("### 27.4 判断: **保留**（2026-08-01）")
    add("")
    add("利用者の判断により定義変更は保留となった。理由:")
    add("")
    add("> σ の 123/136 が `mixed_with_nondeterminism` である以上、")
    add("> どの定義を採っても σ そのものが汚染されている。")
    add("> **条件の定義より B-20（非決定性の解消）が先。**")
    add("")
    add("参考として 3 案の実測値（`accuracy` / 134 実験）:")
    add("")
    add("| 案 | 定義 | 同符号となる実験数 |")
    add("|---|---|---:|")
    add("| 現状 | seed 平均どうしの Δ の符号が揃う | **125** |")
    add("| 厳格 | 全 run 組合せの差の符号が揃う | 124 |")
    add("| 連続量 | 符号一致率（中央値 1.000 / 最小 0.529） | 一致率 100% が 124 |")
    add("")
    add("3 案の差は 1 件しかない。**定義の選択より σ の汚染の方が影響が大きい**")
    add("という判断は実測に整合している。")
    add("")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
def find_nonstandard_groups() -> list[tuple[str, int]]:
    out = []
    for d in sorted(EXPERIMENTS.iterdir()):
        if not d.is_dir():
            continue
        if any(d.rglob("metrics.json")):
            continue
        out.append((d.name, sum(1 for f in d.rglob("*") if f.is_file())))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="runindex/ を実際に書き出す")
    args = ap.parse_args()

    run_dirs = sorted({p.parent for p in EXPERIMENTS.rglob("metrics.json")})
    records = [build_run_record(d) for d in run_dirs]
    # B-12: 直下 transfer/ は metrics.json を持たないため別経路で取り込む。
    records += build_transfer_legacy_records()
    records.sort(key=lambda r: r["ledger_key"])

    # §3: 実験単位と対照ペアを振る（run 単位の収穫が全部終わってから）
    recipe_splits = assign_experiment_ids(records)
    pairing = assign_arms(records)

    nonstandard = find_nonstandard_groups()
    anomalies = build_anomalies(records, nonstandard, recipe_splits, pairing)

    # ---- レポート ----
    ok = [r for r in records if not r["harvest_warnings"]]
    warned = [r for r in records if r["harvest_warnings"]]
    excluded = [r for r in records if r["excluded"]]
    nosplit = [r for r in records if r["split"] is None]
    nohost = [r for r in records if r["host"] is None]

    print("=" * 72)
    print(f"走査した run 数        : {len(records)}")
    print(f"  警告なしで収穫       : {len(ok)}")
    print(f"  警告ありで収穫       : {len(warned)}")
    print("  収穫失敗             : 0  (metrics.json のパース失敗は 0 件)")
    print(f"除外フラグ付き         : {len(excluded)}  (削除ではなくフラグ)")
    print(f"  解析対象             : {len(records) - len(excluded)}")
    print(f"split 確定不能         : {len(nosplit)}")
    print(f"host 確定不能          : {len(nohost)}")
    print(f"非標準構造の群         : {len(nonstandard)}  (取りこぼし run 数 = 0)")
    print("=" * 72)

    print("\n[除外の内訳]")
    for reason, n in Counter(r["exclusion_reason"] for r in excluded).most_common():
        print(f"  {reason:24s} {n}")

    print("\n[per_class_kind の内訳]")
    for k, n in Counter(r["per_class_kind"] for r in records).most_common():
        print(f"  {str(k):24s} {n}")

    print("\n[split の内訳]")
    for k, n in Counter(r["split"] for r in records).most_common():
        print(f"  {str(k):24s} {n}")

    print("\n[host の内訳]")
    for k, n in Counter(r["host"] for r in records).most_common():
        print(f"  {str(k):24s} {n}")

    print("\n[非標準構造の群]")
    for name, n in nonstandard:
        print(f"  {name:24s} {n} ファイル")

    exps = {r["experiment_id"] for r in records if r.get("experiment_id")}
    print("\n[実験単位 (§3)]")
    print(f"  experiment 数           : {len(exps)}")
    print(f"  experiment_id 未確定 run: {sum(1 for r in records if not r.get('experiment_id'))}")
    print(f"  eval_recipe で分離した base: {len(recipe_splits)}")
    print("\n[対照ペア (§3.2)]")
    for k, v in sorted((pairing.get("stats") or {}).items(), key=lambda x: -x[1]):
        print(f"  {k:32s} {v}")
    for name, eid in sorted((pairing.get("resolved") or {}).items()):
        print(f"  解決: {name!r} -> {eid}")
    for u in pairing.get("unresolved") or []:
        print(f"  未解決: {u}")

    if args.write:
        write_runindex(records, anomalies)
        n_runs = len(list((RUNINDEX / "runs").glob("*.json")))
        with (RUNINDEX / "index.csv").open(encoding="utf-8") as fh:
            n_rows = sum(1 for _ in csv.DictReader(fh))
        print(f"\n[書き出し完了] runs/*.json = {n_runs}, index.csv = {n_rows} 行")
    else:
        print("\n" + "=" * 72)
        print("DRY-RUN: 何も書き出していない。書き出すには --write を付ける。")
        print("=" * 72)
        print("\n---------------- anomalies.md (全文) ----------------\n")
        print(anomalies)

    return 0


if __name__ == "__main__":
    sys.exit(main())
