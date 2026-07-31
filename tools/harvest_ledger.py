#!/usr/bin/env python3
"""experiments/ を走査して機械可読な横断インデックス (ledger/) を収穫する。

設計原則
--------
1. 値を捏造しない。判定できないものは null + provenance="not_determinable"。
2. 情報を捨てない。除外は削除ではなくフラグ (excluded / exclusion_reason)。
3. experiments/ 配下は読み取り専用。一切変更しない。
4. 完全に再生成可能。出力に時刻・乱数・絶対パスを含めない (冪等性)。

二段構え
--------
  Stage 1: experiments/**/metrics.json  ->  ledger/runs/<ledger_key>.json
  Stage 2: ledger/runs/*.json           ->  ledger/index.csv

使い方
------
  python tools/harvest_ledger.py            # dry-run (書き出さない)
  python tools/harvest_ledger.py --write    # ledger/ を再生成
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
LEDGER = REPO_ROOT / "ledger"

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
        "aux_seeds": {},
    }
    m = RUN_NAME_RE.match(name)
    if not m:
        warnings.append(f"run 名が命名規約 <step>_<seq3>_<desc>_seed<N> に一致しない: {name}")
        return out, warnings
    out["step"] = m.group("step")
    out["seq"] = int(m.group("seq"))
    out["description"] = m.group("desc")
    out["seed"] = int(m.group("seed"))

    # det42 / p123 のような補助 seed。末尾 seed とは別物なので分けて保持する。
    aux = {k: int(v) for k, v in AUX_SEED_RE.findall(name)}
    if aux:
        out["aux_seeds"] = aux
        warnings.append(
            f"ディレクトリ名に補助 seed {aux} が含まれる。"
            f"seed には末尾の seed{out['seed']} のみを採用した。"
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
            # phase_ は split ではなくタスク名
            return {"canonical": rest, "split": None, "task": "phase", "form": "task_prefix"}
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

    # run 単位の split を決める。証拠が無ければ null。推測しない。
    evidence = {s for s in by_split if s not in ("unknown",)}
    if len(evidence) == 1:
        result["split"] = next(iter(evidence))
        result["split_provenance"] = "from_metric_key_prefix"
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


def infer_split_from_recipe(recipe: dict[str, Any] | None) -> tuple[str | None, str]:
    """eval_recipe.eval_split があればそれを使う。無ければ推測しない。

    参考値であり、権威ある `split` とは別カラムに入れる。
    """
    if not isinstance(recipe, dict):
        return None, "not_determinable"
    v = recipe.get("eval_split")
    if isinstance(v, str) and v:
        return v, "from_eval_recipe_eval_split"
    return None, "not_determinable"


def harvest_per_class(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "per_class": None,
        "per_class_kind": None,
        "per_class_nan_classes": [],
        "per_class_valid_count": None,
        "warnings": [],
    }
    if not path.exists():
        out["warnings"].append("per_class_ap.json が存在しない")
        return out
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
        out["per_class_kind"] = "tool_ap"
    elif keys == PHASE_CLASS_SET:
        # ファイル名は per_class_ap.json だが中身は工程別指標 (AP ではない)。
        out["per_class_kind"] = "phase_metric"
    else:
        out["per_class_kind"] = "unknown"
        out["warnings"].append(
            f"per_class_ap.json のクラス集合が既知の 2 体系のいずれとも一致しない "
            f"({len(keys)} クラス)"
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

    inferred_split, inferred_prov = infer_split_from_recipe(m["eval_recipe"])

    commit_txt = _read_text(run_dir / "git_commit.txt")
    commit = commit_txt.strip().split("\n")[0] if commit_txt else None
    command = _read_text(run_dir / "command.sh")
    notes = _read_text(run_dir / "notes.md")
    config_path = str(rel / "config.yaml") if (run_dir / "config.yaml").exists() else None

    provenance["seed"] = "from_dirname" if name_info["seed"] is not None else "not_determinable"
    provenance["step"] = "from_dirname" if name_info["step"] else "not_determinable"
    provenance["split"] = m["split_provenance"]
    provenance["inferred_split"] = inferred_prov
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
        "aux_seeds": name_info["aux_seeds"],
        "split": m["split"],
        "inferred_split": inferred_split,
        "metrics": m["metrics"],
        "metrics_by_split": m["metrics_by_split"],
        "per_class": pc["per_class"],
        "per_class_kind": pc["per_class_kind"],
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
    "split",
    "inferred_split",
    "per_class_kind",
    "per_class_valid_count",
    "eval_recipe_id",
    "host",
    "host_raw",
    "gpu",
    "commit",
    "epoch",
    "notion_page_id",
    "n_harvest_warnings",
]


def build_index(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    metric_keys: set[str] = set()
    for r in records:
        metric_keys.update(r["metrics"].keys())
    metric_cols = [f"metric.{k}" for k in sorted(metric_keys)]
    header = SCALAR_COLUMNS + metric_cols

    rows = []
    for r in sorted(records, key=lambda x: x["ledger_key"]):
        row = {c: r.get(c) for c in SCALAR_COLUMNS}
        row["n_harvest_warnings"] = len(r["harvest_warnings"])
        for k, v in r["metrics"].items():
            row[f"metric.{k}"] = v
        rows.append(row)
    return header, rows


# --------------------------------------------------------------------------- #
# 出力
# --------------------------------------------------------------------------- #
LEDGER_README = """# ledger/ — experiments/ から収穫した横断インデックス

**これは派生物です。手で編集しないでください。**

```bash
make ledger      # ledger/ 全体をゼロから再生成する
```

生成元は `tools/harvest_ledger.py`。入力は `experiments/**` のみで、
出力は入力が同じなら常に同じになります (冪等)。

## ファイル

| ファイル | 内容 |
|---|---|
| `index.csv` | 1 行 = 1 run の横断インデックス。`runs/*.json` から導出 |
| `runs/<ledger_key>.json` | 正規化済みの run 記録 |
| `host_aliases.json` | host 正規化の対応表 |
| `metric_aliases.json` | 指標名の表記ゆれ統合表 |
| `anomalies.md` | 規約から外れたもの・判断を保留したものの一覧 (人間が読む) |

## 注意

- `runs/*.json` のファイル名は `run_id` (ディレクトリ名) ではなく
  `ledger_key` (experiments/ からの相対パス由来) です。
  ディレクトリ名は 6 種が 3 箇所ずつ衝突するためです。
- `split` は指標キーの接頭辞から確定できた場合のみ入ります。
  確定できない場合は `null` です。**推測値は入れません。**
- 元データの `NaN` は標準 JSON として不正なため `null` に変換しています。
  どのクラスが `NaN` だったかは `per_class_nan_classes` に保持しています。
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


def write_ledger(records: list[dict[str, Any]], anomalies: str) -> None:
    runs_dir = LEDGER / "runs"
    if LEDGER.exists():
        shutil.rmtree(LEDGER)
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
    with (LEDGER / "index.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    (LEDGER / "README.md").write_text(LEDGER_README, encoding="utf-8")
    (LEDGER / "host_aliases.json").write_text(
        json.dumps(HOST_ALIASES, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (LEDGER / "metric_aliases.json").write_text(
        json.dumps(METRIC_ALIASES, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (LEDGER / "anomalies.md").write_text(anomalies, encoding="utf-8")


# --------------------------------------------------------------------------- #
# anomalies.md
# --------------------------------------------------------------------------- #
def build_anomalies(records: list[dict[str, Any]], nonstandard: list[tuple[str, int]]) -> str:
    lines: list[str] = []
    add = lines.append

    add("# anomalies — 規約から外れたもの・判断を保留したもの")
    add("")
    add("`tools/harvest_ledger.py` が自動生成する。手で編集しない。")
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
    add("大半は `phase_*` 系の指標しか持たない run である。`phase_` はタスク名であり")
    add("split ではないため、これらの run の評価 split は証拠ファイルからは決まらない。")
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
    kinds = Counter(r["per_class_kind"] for r in records)
    add("| per_class_kind | runs | 内容 |")
    add("|---|---:|---|")
    desc = {
        "tool_ap": "15 クラスの術具 AP（本来の per-class AP）",
        "phase_metric": "9 クラスの工程別指標（AP ではない。F1 の可能性が高い）",
        "unknown": "既知の 2 体系のいずれとも一致しない",
        None: "per_class_ap.json が無い・空・パース失敗",
    }
    for k, v in sorted(kinds.items(), key=lambda x: (-x[1], str(x[0]))):
        add(f"| `{k}` | {v} | {desc.get(k, '')} |")
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
    add("`seed` フィールドには**末尾の `seed<N>` のみ**を採用し、補助 seed は")
    add("`aux_seeds` に分けて保持している。")
    add("")
    aux = [r for r in records if r["aux_seeds"]]
    add(f"該当 {len(aux)} run")
    add("")
    if aux:
        add("| path | seed (採用) | aux_seeds |")
        add("|---|---:|---|")
        for r in sorted(aux, key=lambda x: x["path"])[:40]:
            add(f"| `{r['path']}` | {r['seed']} | `{json.dumps(r['aux_seeds'], sort_keys=True)}` |")
        if len(aux) > 40:
            add(f"| … 他 {len(aux) - 40} 件 | | |")
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
    add("| group | ファイル数 | 備考 |")
    add("|---|---:|---|")
    for name, n in nonstandard:
        note = "未着手 scaffold (.gitkeep のみ)" if n <= 1 else "非 run の成果物。次段階で adapter が必要"
        add(f"| `{name}` | {n} | {note} |")
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
    ap.add_argument("--write", action="store_true", help="ledger/ を実際に書き出す")
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
        write_ledger(records, anomalies)
        n_runs = len(list((LEDGER / "runs").glob("*.json")))
        with (LEDGER / "index.csv").open(encoding="utf-8") as fh:
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
