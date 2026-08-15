#!/usr/bin/env python
"""四つの区分に分ける。

区分は (設定ファイル, 入口) の組ごとに決まる。同じ鍵でも入口が違えば
読まれたり読まれなかったりするためである。

  read      設定にあり実装が読む       … 実行時に触られた
  unread    設定にあり実装が読まない   … 触られず、丸ごと渡す経路の下にもない
  impl_only 実装が読み設定に無い       … 触られたが設定ファイルが宣言していない
  unknown   判定できない               … 丸ごと渡す経路の下にあり、追跡器が無音

`unknown` は Phase B の摂動で解決する。ここでは憶測で埋めない。

出力: audit/categories.json
"""

from __future__ import annotations

import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]

# 丸ごと渡される部分木（AST の to_container 実測から）。
# scripts/train_grasp_phase_injection.py:121        -> model.temporal
# scripts/train_grasp_phase_injection_variants.py:71 -> grasp_inference
WHOLESALE = {
    "original": ["model.temporal"],
    "variants": ["model.temporal", "grasp_inference"],
}

# 実行時に (設定, 入口) の組で追跡した記録。
PAIRS = [
    ("orig_ctrl", "original", "tasks/T-2026-08-15-grasp-injection-effect/audit/run_ctrl.yaml"),
    ("orig_inj", "original", "tasks/T-2026-08-15-grasp-injection-effect/audit/run_inj.yaml"),
    ("var_ctrl", "variants", "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_ctrl.yaml"),
    ("var_inj", "variants", "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_inj.yaml"),
    ("var_raw_logits", "variants", "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_raw_logits.yaml"),
    ("var_staged", "variants", "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_staged.yaml"),
    ("var_standardized", "variants", "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_standardized.yaml"),
    ("var_oracle_upper_bound_only", "variants", "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_oracle_upper_bound_only.yaml"),
]

# CLI が実行時に注入する鍵（設定ファイルには無くて当然のもの）。
CLI_INJECTED = {"device", "smoke_train_clips", "smoke_val_clips"}


def flatten(node, prefix: str = "") -> dict[str, object]:
    from omegaconf import DictConfig, ListConfig

    out: dict[str, object] = {}
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

    result: dict[str, object] = {"pairs": {}, "wholesale": WHOLESALE}
    totals = {"read": set(), "unread": set(), "impl_only": set(), "unknown": set()}

    for tag, entry, cfg_rel in PAIRS:
        trace_path = AUDIT / "traces" / f"{tag}.json"
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        accessed = set(trace["accessed"])
        cfg = OmegaConf.load(PROJ / cfg_rel)
        leaves = set(flatten(cfg).keys())
        subtrees = WHOLESALE[entry]

        def under_wholesale(key: str) -> bool:
            return any(key.startswith(f"{s}.") for s in subtrees)

        read = sorted(k for k in leaves if k in accessed)
        unknown = sorted(
            k for k in leaves if k not in accessed and under_wholesale(k)
        )
        unread = sorted(
            k for k in leaves if k not in accessed and not under_wholesale(k)
        )
        # 実装が読み設定に無い: 触られた鍵のうち、設定の葉でも中間節点でもないもの
        containers = {
            ".".join(k.split(".")[:i])
            for k in leaves
            for i in range(1, len(k.split(".")))
        }
        impl_only = sorted(
            k for k in accessed if k not in leaves and k not in containers
        )

        result["pairs"][tag] = {
            "entrypoint": entry,
            "config": cfg_rel,
            "trace_exit": trace["exit"],
            "n_config_leaves": len(leaves),
            "n_accessed": len(accessed),
            "read": read,
            "unread": unread,
            "impl_only": impl_only,
            "impl_only_cli_injected": sorted(set(impl_only) & CLI_INJECTED),
            "unknown": unknown,
            "counts": {
                "read": len(read),
                "unread": len(unread),
                "impl_only": len(impl_only),
                "unknown": len(unknown),
            },
        }
        for name, vals in (
            ("read", read),
            ("unread", unread),
            ("impl_only", impl_only),
            ("unknown", unknown),
        ):
            totals[name] |= {f"{entry}:{v}" for v in vals}

    result["union_over_pairs"] = {k: sorted(v) for k, v in totals.items()}
    result["union_counts"] = {k: len(v) for k, v in totals.items()}
    (AUDIT / "categories.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"{'tag':30s} {'read':>5s} {'unread':>7s} {'impl':>5s} {'unk':>4s}  leaves")
    for tag, data in result["pairs"].items():
        c = data["counts"]
        print(
            f"{tag:30s} {c['read']:5d} {c['unread']:7d} {c['impl_only']:5d} "
            f"{c['unknown']:4d}  {data['n_config_leaves']}"
        )
    print()
    print("union over (config, entrypoint) pairs:", result["union_counts"])


if __name__ == "__main__":
    main()
