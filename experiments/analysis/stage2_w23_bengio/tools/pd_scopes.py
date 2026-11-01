"""PD の学ぶパラメータの名前の集合を型と W ごとに出し、SPEC §3.1 の定義と比べる（非公式 T-2026-11-01-stage2-w23-bengio、Task C-2・C-4）。

学習しない。``train_t1b.build_model`` と ``train_t1b.set_trainable``（run と同じ経路）で学ぶ集合を作り、定義と比べる:

- W1 = ``--trainable film``（P2L・EQ の W1）または ``w2``（P3 の W1。``run_pd_fix.sh``）。W1 の run の ``config.yaml`` の
  ``total_trainable`` と要素数を比べる
- W2 = 名前に ``phase`` を含むもの（界面）∪ ``pd_model.w2_parameter_names``（decoder の最終層とその層のクラスと box の頭）
- W3 = 設定の凍結（組み立て直後に requires_grad が偽のもの）以外のすべて。凍結が backbone の中だけであることも記録する
- 陽性対照: 定義の外のパラメータを一つ混ぜた集合では一致しない

    EGO_BODY=<重ねの BODY> <BODY>/.venv-relation-detr/bin/python pd_scopes.py --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import train_t1b as t1b  # noqa: E402  (import 時に cwd を third_party/Relation-DETR へ移す)
from stage2pilot.pd_model import w2_parameter_names  # noqa: E402

CFG = {"P2L": "configs/stage2pilot/pd_clsbias_lin_d9.py", "P3": "configs/stage2pilot/pd_query_d9.py",
       "EQ": "configs/stage2pilot/pd_extra_q_d9.py", "P1": "configs/stage2pilot/pd_film_d9.py"}
W1_MODE = {"P2L": "film", "P3": "w2", "EQ": "film", "P1": "film"}
W1_RUN = {"P2L": "stage2fix_pd_P2L_shuffle_ep4_seed42", "P3": "stage2fix_pd_P3_gt_ep4_seed42",
          "EQ": "stage2four_pd_EQ_gt_ep4_seed42", "P1": "stage2fix_pd_P1-W1_empty_ep4_seed42"}
DET = ROOT / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth"


def trainable(model):
    return sorted(n for n, p in model.named_parameters() if p.requires_grad)


def check(model, got, expected):
    names = [n for n, _ in model.named_parameters()]
    outside = [n for n in names if n not in set(expected)]
    extra = outside[0] if outside else "__not_a_parameter__"
    numel = dict((n, p.numel()) for n, p in model.named_parameters())
    return {"equal": got == expected, "n_names": len(got), "n_params": int(sum(numel[n] for n in got)),
            "mixed_name": extra, "equal_with_one_outside_mixed": sorted(set(got) | {extra}) == expected,
            "names": got}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--types", nargs="+", default=list(CFG))
    a = ap.parse_args()
    device = torch.device("cuda")
    out = {"task_id": "T-2026-11-01-stage2-w23-bengio", "body": str(t1b.BODY), "types": {}}
    for typ in a.types:
        row = {"cfg": CFG[typ]}
        for scope, mode in (("W1", W1_MODE[typ]), ("W2", "w2"), ("W3", "all")):
            model = t1b.build_model(device, 42, str(ROOT / CFG[typ]), ckpt_override=str(DET))
            names = [n for n, _ in model.named_parameters()]
            default_trainable = trainable(model)                    # 組み立て直後（設定の凍結だけが効いている）
            frozen = sorted(set(names) - set(default_trainable))
            t1b.set_trainable(model, mode)
            got = trainable(model)
            iface = [n for n in names if "phase" in n]
            if scope == "W3":
                expected = default_trainable
            elif mode == "w2":
                expected = sorted(set(iface) | set(w2_parameter_names(model)))
            else:
                expected = sorted(iface)
            rep = check(model, got, expected)
            rep.update(mode=mode, n_iface_names=len(iface),
                       n_iface_params=int(sum(p.numel() for n, p in model.named_parameters() if "phase" in n)))
            if scope == "W3":
                rep.update(frozen_by_config=len(frozen), frozen_all_backbone=all(n.startswith("backbone.") for n in frozen),
                           iface_included=set(iface) <= set(got))
            if scope == "W2":
                rep["w2_subset_of_w3"] = set(got) <= set(default_trainable)
            if scope == "W1":
                cfg = yaml.safe_load((ROOT / "experiments/phase1" / W1_RUN[typ] / "config.yaml").read_text())
                rec = cfg["stage2pilot"]["total_trainable"] if "stage2pilot" in cfg and "total_trainable" in cfg["stage2pilot"] \
                    else cfg.get("total_trainable")
                rep.update(w1_run=W1_RUN[typ], w1_run_total_trainable=rec, equals_w1_run=rec == rep["n_params"])
            row[scope] = rep
            del model
            torch.cuda.empty_cache()
        row["P3_W2_equals_W1"] = row["W2"]["names"] == row["W1"]["names"] if typ == "P3" else None
        out["types"][typ] = row
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({t: {s: {k: v for k, v in r[s].items() if k != "names"} for s in ("W1", "W2", "W3")}
                      | {"P3_W2_equals_W1": r["P3_W2_equals_W1"]} for t, r in out["types"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
