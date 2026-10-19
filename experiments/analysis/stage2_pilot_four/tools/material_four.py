"""Task B-1: 本契約が使う信号と受け取り手の入力の在否と要約値を、前回と直しの契約の記録と照合する
（非公式 T-2026-10-19-stage2-pilot-four-new-types）。読むだけ。書き込みは --out と --flip-dir（陽性対照の複製）だけ。

記録の出所（どれも andrew で書かれ、版管理下にあるか STORE に写したもの）:
  - 直しの契約の material/material_check.json（前回の信号の sha256 を前回の記録・DP の run の config と照合した結果）
  - 直しの契約の shuffle/shuffle_record.json（入れ替えた信号の out_sha256）
  - 直しの契約の bengio/input_digest_andrew.json（PD の 8 本の sha256）
  - 直しの契約の repro/ptower_val.json（工程塔の特徴と時間ヘッドの sha256）

    python material_four.py --out <json> [--flip-dir <dir>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

WT = Path(__file__).resolve().parents[4]
FIXA = WT / "experiments/analysis/stage2_pilot_fix"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
OLD = STORE / "T-2026-10-18-stage2-pilot-folda"
FIX = STORE / "T-2026-10-19-stage2-pilot-fix-epoch4-shuffle"
EFROS = OLD / "efros_ptower"
PT_CACHE = EFROS / "data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz"
PT_HEAD = EFROS / "experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth"

# 本契約が読むもの（用途）
USED = {
    OLD / "signals/final/P0_train.npz": "PD 予測-noCF（train）",
    OLD / "signals/final/P0_val.npz": "PD 予測-noCF・予測-CF・空（val）",
    OLD / "signals/final/P-GT_train.npz": "PD 正解（train）",
    OLD / "signals/final/P-GT_val.npz": "PD 正解（val）",
    OLD / "signals/cf/P0_train.npz": "PD 予測-CF（train）",
    OLD / "arms/PD/gtpred_CF_train.npz": "PD 正解予測-CF（train）",
    OLD / "arms/PD/gtpred_noCF_val.npz": "PD 正解予測-CF（val）",
    FIX / "signals/shuffle/P0_train.npz": "PD 入れ替え（train）",
    FIX / "signals/shuffle/P0_val.npz": "PD 入れ替え（val）",
    OLD / "signals/final/D0_train.npz": "DP 予測-noCF の予測の半分（train）",
    OLD / "signals/final/D0_val.npz": "DP 予測の半分（val）、K3 の val",
    OLD / "signals/final/D-GT_train.npz": "DP 正解の半分（train）",
    OLD / "signals/final/D-GT_val.npz": "DP 正解の半分（val）",
    OLD / "signals/cf/D0_train.npz": "DP 予測-CF の予測の半分（train）、K3 の train",
    FIX / "signals/shuffle/D0_train.npz": "DP 入れ替えの予測の半分（train）",
    FIX / "signals/shuffle/D0_val.npz": "DP 入れ替えの予測の半分（val）",
    PT_CACHE: "工程塔の特徴（受け取り手の入力）",
    PT_HEAD: "工程塔の時間ヘッド（受け取り手）",
}


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def recorded() -> dict[str, dict[str, str]]:
    """経路 → {記録の名前: sha256}。"""
    rec: dict[str, dict[str, str]] = {}
    mc = json.loads((FIXA / "material/material_check.json").read_text())
    for r in mc["signals"]:
        if r.get("match") is True:
            rec.setdefault(r["path"], {})["fix_material_check"] = r["sha256"]
    sr = json.loads((FIXA / "shuffle/shuffle_record.json").read_text())
    for part in sr["parts"].values():
        for s in part["signals"].values():
            rec.setdefault(s["out"], {})["fix_shuffle_record"] = s["out_sha256"]
            rec.setdefault(s["source"], {})["fix_shuffle_record_source"] = s["source_sha256"]
    ia = json.loads((FIXA / "bengio/input_digest_andrew.json").read_text())
    for p, h in ia["signals"].items():
        rec.setdefault(p, {})["fix_input_digest_andrew"] = h
    pv = json.loads((FIXA / "repro/ptower_val.json").read_text())
    rec.setdefault(str(PT_HEAD), {})["fix_ptower_val_head"] = pv["head_sha256"]
    rec.setdefault(str(PT_CACHE), {})["fix_ptower_val_cache"] = pv["cache_sha256"]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--flip-dir", default=None)
    a = ap.parse_args()
    rec = recorded()
    rows = []
    for path, use in USED.items():
        exists = path.is_file()
        h = sha256(path) if exists else None
        r = rec.get(str(path), {})
        rows.append({"path": str(path), "use": use, "exists": exists, "bytes": path.stat().st_size if exists else None,
                     "sha256": h, "recorded": r, "n_records": len(r),
                     "match": bool(r) and exists and all(v == h for v in r.values())})
    out = {"task_id": "T-2026-10-19-stage2-pilot-four-new-types", "rows": rows,
           "all_exist": all(x["exists"] for x in rows), "all_have_record": all(x["n_records"] > 0 for x in rows),
           "all_match": all(x["match"] for x in rows)}
    if a.flip_dir:
        # 陽性対照: 一つを 1 バイト変えた複製は記録と一致しなくなる
        src = OLD / "signals/final/D0_val.npz"
        dst = Path(a.flip_dir) / "D0_val_flipped.npz"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        with dst.open("r+b") as f:
            f.seek(1000)
            b = f.read(1)
            f.seek(1000)
            f.write(bytes([b[0] ^ 0x01]))
        fh = sha256(dst)
        out["flip_control"] = {"copy": str(dst), "sha256": fh,
                               "matches_record": all(v == fh for v in rec[str(src)].values())}
        dst.unlink()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, ensure_ascii=False))
    for x in rows:
        print(x["match"], x["n_records"], x["sha256"][:12] if x["sha256"] else None, x["path"].replace(str(STORE) + "/", ""))


if __name__ == "__main__":
    main()
