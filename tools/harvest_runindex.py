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
EXCLUSION_RULES: list[tuple[str, str]] = [
    ("_smoke_prior", "smoke_test"),
    ("_smoke_ddq", "smoke_test"),
    ("_wrong_split_8_2_3", "known_bad_split"),
    ("_failed_s3_weighted", "failed_run"),
]

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

# 指標本体ではないメタキー
META_KEYS = {"eval_recipe", "eval_recipe_detection", "eval_recipe_phase", "epoch"}

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

RUN_NAME_RE = re.compile(r"^(?P<step>.+?)_(?P<seq>\d{3})_(?P<desc>.+)_seed(?P<seed>\d+)$")

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
    for part in rel_path.parts:
        for marker, reason in EXCLUSION_RULES:
            if part == marker:
                return True, reason
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
    }
    m = RUN_NAME_RE.match(name)
    if not m:
        warnings.append(f"run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない: {name}")
        return out, warnings
    out["step"] = m.group("step")
    out["seq"] = int(m.group("seq"))
    out["description"] = m.group("desc")
    out["seed"] = int(m.group("seed"))

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

    for key, value in raw.items():
        if key in META_KEYS:
            continue
        if isinstance(value, (dict, list)):
            # eval_recipe 以外のネスト値は指標として扱わず原文のみ保持
            nested[key] = _denan(value)
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
    flat: dict[str, Any] = dict(nested)
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

    fs = data.get("frozen_source")
    if isinstance(fs, dict):
        cache = fs.get("cache_dir") or fs.get("gap_cache") or fs.get("tool_signal_cache")
        if isinstance(cache, str) and cache.strip():
            out["frozen_source_tag"] = cache.rstrip("/").split("/")[-1]
    return out


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
    warnings.extend(pc["warnings"])

    server_txt = _read_text(run_dir / "server.txt")
    host = normalize_host(server_txt, m["eval_recipe"])
    warnings.extend(host["warnings"])

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

    provenance["seed"] = "from_dirname" if name_info["seed"] is not None else "not_determinable"
    provenance["seed_detector"] = (
        "from_dirname_det_token" if name_info["seed_detector"] is not None else "not_determinable"
    )
    provenance["seed_phase"] = (
        "from_dirname_p_token" if name_info["seed_phase"] is not None else "not_determinable"
    )
    provenance["step"] = "from_dirname" if name_info["step"] else "not_determinable"
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
        "seed_detector": name_info["seed_detector"],
        "seed_phase": name_info["seed_phase"],
        "split": split,
        # metrics の各値がどの split から来たか。null なら split 接頭辞付きの指標が
        # 1 つも無い（= metrics は bare キーのみ、または空）。
        # split 列との整合は tools/verify_runindex.py が毎回検査する。
        "metrics_primary_split": m["metrics_primary_split"],
        "metrics": m["metrics"],
        "metrics_by_split": m["metrics_by_split"],
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
        "host": host["host"],
        "host_raw": host["host_raw"],
        "gpu": host["gpu"],
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
    }
    return record


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
IDENTIFIER_RE = re.compile(r"^[a-z0-9_]+$")


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
    desc = paren if IDENTIFIER_RE.match(paren) else None
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
    "n_runs_excluded",
    "per_class_kind",
    "per_class_metric",
    "arm",
    "control_of",
    "pairing_provenance",
    "control_note_value",
    "delta_method",
    "n_command_variants",
]


def _agg(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.mean(values),
        "pstd": statistics.pstdev(values),
        "min": min(values),
        "max": max(values),
    }


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


def build_experiments(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
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
            s: dict[int, list[float]] = defaultdict(list)
            for r in rs:
                v = r["metrics"].get(name)
                if isinstance(v, (int, float)) and r["seed"] is not None:
                    s[r["seed"]].append(v)
            per_seed[name] = dict(s)
        agg_by_exp[eid] = per_metric
        seedvals_by_exp[eid] = per_seed

    used_metrics = sorted({m for a in agg_by_exp.values() for m in a})
    header = list(EXPERIMENT_SCALAR_COLUMNS)
    for m in used_metrics:
        header += [f"{m}_mean", f"{m}_pstd", f"{m}_min", f"{m}_max"]
    for m in used_metrics:
        header += [f"delta_{m}", f"delta_pstd_{m}"]

    rows = []
    for eid in sorted(groups):
        rs = groups[eid]
        first = rs[0]
        seeds = sorted({r["seed"] for r in rs if r["seed"] is not None})
        seed_counts = Counter(r["seed"] for r in rs if r["seed"] is not None)
        hosts = sorted({r["host"] for r in rs if r["host"]})
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
            "n_runs_excluded": sum(1 for r in rs if r["excluded"]),
            "per_class_kind": ",".join(sorted({str(r["per_class_kind"]) for r in rs})),
            "per_class_metric": ",".join(sorted({str(r["per_class_metric"]) for r in rs})),
            "arm": ",".join(arms),
            "control_of": controls[0] if len(controls) == 1 else "",
            "pairing_provenance": ",".join(sorted({r["pairing_provenance"] for r in rs})),
            "control_note_value": note_vals[0] if len(note_vals) == 1 else "",
            "n_command_variants": len(cmd_sigs),
            "delta_method": "",
        }
        for m, a in agg_by_exp[eid].items():
            row[f"{m}_mean"] = a["mean"]
            row[f"{m}_pstd"] = a["pstd"]
            row[f"{m}_min"] = a["min"]
            row[f"{m}_max"] = a["max"]

        ctrl = controls[0] if len(controls) == 1 else None
        if ctrl and ctrl in agg_by_exp:
            cs = seedvals_by_exp[ctrl]
            os_ = seedvals_by_exp[eid]
            # paired: 双方とも seed ごとにちょうど 1 run で、seed 集合が一致するとき
            methods: set[str] = set()
            for m in agg_by_exp[eid]:
                if m not in agg_by_exp[ctrl]:
                    continue
                a, b = os_.get(m, {}), cs.get(m, {})
                common = set(a) & set(b)
                pairable = (
                    common
                    and set(a) == set(b)
                    and all(len(a[s]) == 1 and len(b[s]) == 1 for s in common)
                )
                if pairable:
                    diffs = [a[s][0] - b[s][0] for s in sorted(common)]
                    row[f"delta_{m}"] = statistics.mean(diffs)
                    row[f"delta_pstd_{m}"] = statistics.pstdev(diffs)
                    methods.add("paired")
                else:
                    row[f"delta_{m}"] = agg_by_exp[eid][m]["mean"] - agg_by_exp[ctrl][m]["mean"]
                    # 対応が取れない以上 paired-σ は定義できない。捏造せず空欄。
                    methods.add("unpaired")
            # paired と unpaired を混同してはならないので両方出たら併記する。
            row["delta_method"] = ",".join(sorted(methods))
        rows.append(row)
    return header, rows


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
    "has_test",
    "n_harvest_warnings",
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
| `experiments.csv` | 1 行 = 1 **実験**（seed 集約 + 対照 Δ）。論文 Table の 1 行に対応 |
| `runs/<ledger_key>.json` | 正規化済みの run 記録 |
| `host_aliases.json` | host 正規化の対応表 |
| `metric_aliases.json` | 指標名の表記ゆれ統合表 |
| `anomalies.md` | 規約から外れたもの・判断を保留したものの一覧 (人間が読む) |
| `anomalies/val_test_pairs.csv` | test 評価を持つ run の val/test 対応表 (縦持ち) |
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
| `<metric>_mean` / `_pstd` / `_min` / `_max` | seed 集約 |
| `arm` / `control_of` | 注入 / 対照。`control_of` は対照実験の `experiment_id` |
| `delta_<metric>` / `delta_pstd_<metric>` | `control_of` が確定した実験のみ |
| `delta_method` | `paired` か `unpaired` か。**混同してはいけません** |
| `control_note_value` | `notes.md` に引用されている基準値（実測との突き合わせ用） |

`delta_pstd_*` は `delta_method=paired` のときだけ入ります。
対応が取れない場合に paired-σ は定義できないため、空欄にしてあります。

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
"""

BACKLOG = """# backlog — 本タスクの範囲外として起票した未着手事項

**これは派生物です。手で編集しないでください**（`tools/harvest_runindex.py` が生成）。

指示書 #02 §0「明示的にやらないこと」に該当するため、着手せず記録だけしたもの。
いずれも価値はあるが**監査・整備であって分析可能性を上げない**ため、
分析基盤（`index.csv` / `per_class.csv` / `experiments.csv`）の完成を優先した。

| # | 事項 | 分かっていること | 着手の前提 |
|---|---|---|---|
| B-1 | 573 run の `git_commit.txt` 実在性の全件検査 | `t1b_phasefilm_{001,002}` は記録された commit `a697d90` に `scripts/postprocess_t1b.py` が存在せず、**記録された commit では再現できない**ことが確認済み。他 571 run は未検査 | 全件 `git cat-file` する走査を書く。`experiments/` は読み取りのみ |
| B-2 | `b2b_rescore_alpha{0.5,1.0,2.0}` の entrypoint 特定 | `verify_no_dummy_metrics.py` の死角スキャンが新規に検出。`command.sh` に python 呼び出しが無く、どのコードが mAP を書いたか不明 | 3 run の `command.sh` / `notes.md` / ログを個別に読む |
| B-3 | Notion 実験Run台帳との run_id 単位の突合 | 母数が 616 か 739 か未確定（§14）。データソース重複・フィルタ付きビュー・DB 重複はいずれも排除済み。`Status='failed'` が 0 件であることは母数に依らず確定 | Notion のクエリ利用上限の解除、または `.env` の `NOTION_API_KEY` 使用の承認 |
| B-4 | dummy Trainer の除去 | `src/egosurgery/engines/trainer.py` が乱数で per-class AP を生成し `mAP` として書く。混入は現時点 0 件と検証済みだが**コードは残っている**（§11） | 学習コードの変更にあたるため、本タスクでは触れない |
| B-5 | `experiments/README.md` の更新 | 規定は 17 種の step 識別子だが実データには 156 種ある（§12）。観測された family は b1 / b2a / b2b / t1a / t1b / taux / haux / hires | README は規約側の文書であり、実データに合わせて書き換えるかは方針判断 |
| B-6 | 非標準群の adapter | `analysis` / `detector_improve` / `audit` / `ablations` / `final` / `g2_main_*` は `metrics.json` を持たず収穫できない（§9）。取りこぼした run は 0 件（そもそも run 構造ではない） | 群ごとにファイル形式が違うため個別の読み取りが要る |
| B-7 | `ledger_key` フィールド名の改名 | `ledger/` → `runindex/` の改名後も、フィールド名 `ledger_key` は 573 個の JSON と `index.csv` 第 1 列に残っている | スキーマ変更になるため利用側の合意が要る |
| B-8 | `b2a_ro_oracle_noise000` の名前と実態の食い違い | 名前は noise 0.00 を示すが `--tool-noise-rate` は 0.05/0.10/0.20/0.30 の 4 通り（§7.3）。原因は `scripts/run_b2a_ro_oracle_noise_sweep.sh` のタグ生成が `bc` に依存しており、`bc` 不在時に全水準が `000` に潰れること。実測 accuracy も 0.9549 / 0.9435 / 0.9023 / 0.8106 と水準に応じて単調減衰しており、4 水準であることを独立に裏付ける | ディレクトリ名の改名は `experiments/` の変更にあたるため不可。正本側での扱いを決める必要がある |
| B-9 | σ の規約統一 | `S4 base` が母集団σ `±0.0028` と標本σ `±0.0034` の 2 通りで引用されている（§18.2）。`|Δ| > 1σ` 判定の結論が変わりうる | 正本 §10.1 でどちらを採るかを定める |
| B-10 | paired-σ が計算できない | 基準点実験が 17 run / 3 seed（1 seed に最大 7 run）のため、seed ごとの対応が取れず paired-σ が定義できない（§18.3）。`notes.md` は 439 run で paired-σ 判定を宣言しているが実行不能 | seed ごとの代表 run を決める規約が要る（どの再実行を採るか） |
| B-11 | `logs/phase3seed_results.tsv` の欠落 | `scripts/paired_sigma_3seed.py` はこの TSV の `arm` 列（frozen / augstrong）を読んで paired-σ を出す設計だが、ファイルが repo に存在しない（`.gitignore` 対象）。arm 情報自体は `config.yaml` の `frozen_source.*` に残っており `frozen_source_tag` として収穫済み | TSV の復元、または `paired_sigma_3seed.py` を `runindex` 由来に切り替える |
| B-12 | 573 run の外側にある inj/ctrl ペア | `transfer/*_efros/` と `experiments/transfer/{hc,oracle_phase}_seed*/` に `injected_result.json` / `control_result.json` の対が 18 組あるが、`metrics.json` を持たないため収穫対象外。真の注入/対照ペアはここにある | 非標準群の adapter（B-6）と同じ作業 |
| B-13 | 同一条件が別 `experiment_id` に分裂する 3 組 | `description` / `split` / `frozen_source_tag` が同じで `step` だけ違う組が 3 組ある（§17.2）。うち 2 組は `eval_recipe_id` による意図的分離 | 起動経路が同一かの判断が要るため harvester では決めない |
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

    # test 評価を持つ run の val/test 対応表（縦持ち）
    anomalies_dir = RUNINDEX / "anomalies"
    anomalies_dir.mkdir(exist_ok=True)
    ph, pr = build_val_test_pairs(reloaded)
    with (anomalies_dir / "val_test_pairs.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ph, lineterminator="\n")
        writer.writeheader()
        writer.writerows(pr)

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
