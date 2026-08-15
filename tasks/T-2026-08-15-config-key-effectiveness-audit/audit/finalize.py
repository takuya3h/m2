#!/usr/bin/env python
"""四つの区分を確定する。

判定の順位は次のとおり。**実挙動が最も強い。**

  1. 実行時に触れた                        -> read
       指標が動くかで下位区分に分ける。**指標が動かない = 読まれていない、ではない。**
       フォルダ名や証跡の中身だけを決める鍵は、読まれていても指標を動かさない。
  2. 触れていないが摂動で指標が変わった    -> read（丸ごと渡す経路の下）
  3. 触れておらず摂動でも変わらなかった    -> unread（揺れ 0.0 が基準）
  4. 触れておらず摂動もしていない          -> unread_untested（憶測で埋めない）

出力: audit/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]

PAIRS = {
    "original": {
        "config": "tasks/T-2026-08-15-grasp-injection-effect/audit/run_inj.yaml",
        "smoke": "traces/orig_inj.json",
        "nonsmoke": "trace_nonsmoke_original.json",
        "wholesale": ["model.temporal"],
    },
    "variants": {
        "config": "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_inj.yaml",
        "smoke": "traces/var_inj.json",
        "nonsmoke": "trace_nonsmoke_variants.json",
        "wholesale": ["model.temporal", "grasp_inference"],
    },
}
CLI_INJECTED = {"device", "smoke_train_clips", "smoke_val_clips"}


def flatten(node, prefix=""):
    from omegaconf import DictConfig, ListConfig

    out = {}
    if isinstance(node, (DictConfig, dict)):
        if len(node) == 0:
            out[prefix] = {}
            return out
        for key in node.keys():
            child = node[key]
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(child, (DictConfig, dict)) and len(child) > 0:
                out.update(flatten(child, path))
            elif isinstance(child, (DictConfig, dict)):
                out[path] = {}
            else:
                out[path] = list(child) if isinstance(child, ListConfig) else child
        return out
    out[prefix] = node
    return out


def main() -> None:
    from omegaconf import OmegaConf

    eff = json.loads((AUDIT / "effectiveness.json").read_text(encoding="utf-8"))
    summary = {"noise_floor": eff["noise_floor"], "entrypoints": {}}

    for entry, meta in PAIRS.items():
        acc = set(json.loads((AUDIT / meta["smoke"]).read_text())["accessed"])
        acc |= set(json.loads((AUDIT / meta["nonsmoke"]).read_text())["accessed"])
        leaves = set(flatten(OmegaConf.load(PROJ / meta["config"])).keys())
        results = eff["results"][entry]

        changed, unchanged = set(), set()
        for key, data in results.items():
            if data.get("skipped") or not data.get("run_ok"):
                continue
            (changed if (data.get("n_changed") or 0) > 0 else unchanged).add(key)

        read, read_metric_invariant, read_unmeasured = [], [], []
        unread, unread_untested, unknown = [], [], []
        for key in sorted(leaves):
            if key in acc:
                # 実行時に触れた = 読まれている。指標が動くかは別の軸であり、
                # 摂動していない鍵について「効かない」とは言えない。
                if key in changed:
                    read.append(key)
                elif key in unchanged:
                    read_metric_invariant.append(key)
                else:
                    read_unmeasured.append(key)
            elif key in changed:
                read.append(key)  # 丸ごと渡す経路の下。摂動で到達を実証。
            elif key in unchanged:
                unread.append(key)
            elif any(key.startswith(f"{w}.") for w in meta["wholesale"]):
                unknown.append(key)
            else:
                unread_untested.append(key)

        containers = {
            ".".join(k.split(".")[:i])
            for k in leaves
            for i in range(1, len(k.split(".")))
        }
        impl_only = sorted(k for k in acc if k not in leaves and k not in containers)

        summary["entrypoints"][entry] = {
            "config": meta["config"],
            "n_leaves": len(leaves),
            "counts": {
                "read": len(read) + len(read_metric_invariant) + len(read_unmeasured),
                "read_metric_affecting": len(read),
                "read_metric_invariant": len(read_metric_invariant),
                "read_metric_effect_unmeasured": len(read_unmeasured),
                "unread": len(unread),
                "unread_untested": len(unread_untested),
                "unknown": len(unknown),
                "impl_only": len(impl_only),
            },
            "read_metric_affecting": read,
            "read_metric_invariant": read_metric_invariant,
            "read_metric_effect_unmeasured": read_unmeasured,
            "unread": unread,
            "unread_untested": unread_untested,
            "unknown": unknown,
            "impl_only": impl_only,
            "impl_only_cli_injected": sorted(set(impl_only) & CLI_INJECTED),
            "control_keys_that_changed": sorted(
                k for k in changed if results[k]["prior_class"] == "read"
            ),
        }

    (AUDIT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for entry, data in summary["entrypoints"].items():
        c = data["counts"]
        print(f"=== {entry} ({data['n_leaves']} leaf keys) ===")
        print(
            f"  read={c['read']} (指標に効く {c['read_metric_affecting']} / "
            f"摂動しても不変 {c['read_metric_invariant']} / "
            f"指標影響は未測定 {c['read_metric_effect_unmeasured']})"
        )
        print(
            f"  unread={c['unread']}  unread_untested={c['unread_untested']}  "
            f"unknown={c['unknown']}  impl_only={c['impl_only']}"
        )
        print(f"  read かつ摂動しても指標不変: {data['read_metric_invariant']}")
        print(f"  unread（実挙動で確認）: {data['unread']}")
        if data["unread_untested"]:
            print(f"  unread_untested       : {data['unread_untested']}")
        if data["unknown"]:
            print(f"  unknown               : {data['unknown']}")
        print(f"  対照で変化した読まれる項目: {data['control_keys_that_changed']}")
        print()
    print(f"noise floor: {summary['noise_floor']}")


if __name__ == "__main__":
    main()
