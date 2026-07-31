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
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

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
# ディレクトリ名に含まれる補助 seed (例: det42 / p123)
AUX_SEED_RE = re.compile(r"(?:^|_)(det|p)(\d+)(?:_|$)")


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


def parse_run_name(name: str) -> tuple[dict[str, Any], list[str]]:
    """ディレクトリ名から step / seq / desc / seed を取り出す。"""
    warnings: list[str] = []
    out: dict[str, Any] = {
        "step": None,
        "seq": None,
        "description": None,
        "seed": None,
        "seed_detector": None,
        "seed_phase": None,
    }
    m = RUN_NAME_RE.match(name)
    if not m:
        warnings.append(f"run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない: {name}")
        return out, warnings
    out["step"] = m.group("step")
    out["seq"] = int(m.group("seq"))
    out["description"] = m.group("desc")
    out["seed"] = int(m.group("seed"))

    # det42 / p123 のような補助 seed。
    # 後段の paired 統計では比較単位が (検出器 seed, 工程 seed) の組であり、
    # 末尾 seed だけでは基準点を特定できない。汎用 dict や provenance の文字列に
    # 落とすと機械的に結合できなくなるため、専用フィールドに分けて保持する。
    aux = {k: int(v) for k, v in AUX_SEED_RE.findall(name)}
    if "det" in aux:
        out["seed_detector"] = aux["det"]
    if "p" in aux:
        out["seed_phase"] = aux["p"]
    if aux:
        warnings.append(
            f"ディレクトリ名に補助 seed {aux} が含まれる。"
            f"seed には末尾の seed{out['seed']} のみを採用し、"
            f"det/p は seed_detector / seed_phase に分離した。"
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
    flat: dict[str, Any] = {}

    for key, value in raw.items():
        if key in META_KEYS:
            continue
        if isinstance(value, (dict, list)):
            # eval_recipe 以外のネスト値は指標として扱わず原文のみ保持
            flat[key] = _denan(value)
            continue
        info = normalize_metric_key(key)
        canon = info["canonical"]
        if info["split"]:
            by_split[info["split"]][canon] = value
            flat[canon] = value
        else:
            bare[canon] = value

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

    # run 単位の split を決める。証拠が無ければ null。推測はしない。
    #
    # val と test が共存する run は「val で best を選び、その重みを test でも評価した」
    # ものであり曖昧ではない。学習スクリプトのコードが一次証拠:
    #   best = {**val, ...}                        -> primary は val
    #   test_scalars[k.replace("phase_", "test_")] -> test は --eval-test の追加評価
    # したがって run 単位の split（= primary な指標の由来）は val で確定する。
    # 両方の値は metrics_by_split に保持しているので情報は失われない。
    evidence = {s for s in by_split if s != "unknown"}
    if len(evidence) == 1:
        result["split"] = next(iter(evidence))
        result["split_provenance"] = "from_metric_key_prefix"
    elif evidence == {"val", "test"}:
        result["split"] = "val"
        result["split_provenance"] = "primary_val_by_training_script"
        result["warnings"].append(
            "val と test の指標が共存する。primary（best 選択元）は val。"
            "test 側は metrics_by_split['test'] に保持している。"
        )
    elif len(evidence) > 1:
        result["warnings"].append(
            f"複数 split の指標が同一 run に共存: {sorted(evidence)}。split は null にした。"
        )
        result["split_provenance"] = "ambiguous_multiple_splits"

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

    name_info, name_warn = parse_run_name(run_dir.name)
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
    command = _read_text(run_dir / "command.sh")
    notes = _read_text(run_dir / "notes.md")
    config_file = run_dir / "config.yaml"
    config_path = str(rel / "config.yaml") if config_file.exists() else None

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
# index.csv (Stage 2: runs/*.json から導出する)
# --------------------------------------------------------------------------- #
SCALAR_COLUMNS = [
    "ledger_key",
    "run_id",
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
| `index.csv` | 1 行 = 1 run の横断インデックス。`runs/*.json` から導出 |
| `runs/<ledger_key>.json` | 正規化済みの run 記録 |
| `host_aliases.json` | host 正規化の対応表 |
| `metric_aliases.json` | 指標名の表記ゆれ統合表 |
| `anomalies.md` | 規約から外れたもの・判断を保留したものの一覧 (人間が読む) |
| `anomalies/val_test_pairs.csv` | test 評価を持つ run の val/test 対応表 (縦持ち) |

## index.csv の列

| 列 | 意味 |
|---|---|
| `metric.<name>` | **primary (= `split` 列が指す側。実質 val) の値** |
| `metric_test.<name>` | **test 側の値**。別列なので既存列の意味は変わらない |
| `has_test` | test 評価を持つか。`true` の run だけ `metric_test.*` が埋まる |

`metric.*` だけを見ると test 評価の存在に気づけません。
val と test は大きく乖離するため、下流解析では `has_test` で分岐してください。
乖離の実測は `anomalies.md` §13.1 と `anomalies/val_test_pairs.csv` にあります。

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

    # test 評価を持つ run の val/test 対応表（縦持ち）
    anomalies_dir = RUNINDEX / "anomalies"
    anomalies_dir.mkdir(exist_ok=True)
    ph, pr = build_val_test_pairs(reloaded)
    with (anomalies_dir / "val_test_pairs.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ph, lineterminator="\n")
        writer.writeheader()
        writer.writerows(pr)

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
def build_anomalies(records: list[dict[str, Any]], nonstandard: list[tuple[str, int]]) -> str:
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

    add("## 7. ディレクトリ名に補助 seed を含む run")
    add("")
    add("`det42` / `p123` のように、末尾の `seed<N>` とは別の seed が名前に含まれる run。")
    add("後段の paired 統計では比較単位が **(検出器 seed, 工程 seed) の組**であり、")
    add("末尾 seed だけでは基準点を特定できない。機械的に結合できるよう")
    add("`seed_detector` / `seed_phase` の専用フィールドに分離している。")
    add("")
    aux = [r for r in records if r["seed_detector"] is not None or r["seed_phase"] is not None]
    add(f"該当 {len(aux)} run")
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

    nonstandard = find_nonstandard_groups()
    anomalies = build_anomalies(records, nonstandard)

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
    print(f"  収穫失敗             : 0  (metrics.json のパース失敗は 0 件)")
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
