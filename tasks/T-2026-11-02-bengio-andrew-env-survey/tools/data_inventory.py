"""塔と Stage 2 が読むデータと checkpoint の項目表（T-2026-11-02-bengio-andrew-env-survey、Task D）。

読むだけ。結果は標準出力（JSON）。andrew では ``ssh andrew 'python3 -B -I - <args>' < この台本`` で回し、何も書かない。
画像の要約値は ``experiments/analysis/dlsta_tower_feasibility/inputs_inventory.py`` と同じ取り方
（data/raw/ego の 01〜15 の jpg、``other`` を除く。動画ごとに「相対経路 sha256\\n」を並べた sha256）。
加えて ``image_input_lock.json`` の 17,233 行の各画像（selected と counterpart）の sha256 を取る。

    python3 -B data_inventory.py --root ~/slocal2/m2 --lists lists.json          # bengio
    ssh andrew 'python3 -B -I - --root ~/slocal2/m2' < 一覧を埋めた写し             # andrew

経路の一覧（JSON）は ``--lists <file>`` で渡す。andrew では標準入力が台本で塞がるため、
呼び出し側が台本の先頭に ``_EMBEDDED = <一覧>`` を足した写しを標準入力で渡す（``build_embedded.py``）。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

V15 = [f"{i:02d}" for i in range(1, 16)]
HOME = os.path.expanduser("~")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_blob(path):
    data = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _digest(p):
    return p, sha256_file(p)


def stat_entry(path, blob=False):
    p = Path(path)
    if not p.exists():
        return {"path": str(path), "exists": False, "is_link": p.is_symlink()}
    e = {"path": str(path), "exists": True, "is_link": p.is_symlink(), "real": str(p.resolve()),
         "bytes": p.stat().st_size, "sha256": sha256_file(p)}
    if blob:
        e["git_blob"] = git_blob(p)
    return e


def coco_counts(path, ego):
    d = json.loads(Path(path).read_text())
    if not (isinstance(d, dict) and "images" in d):
        return {}
    return {"images": len(d["images"]), "annotations": len(d["annotations"]),
            "missing_images": sum(not (ego / im["file_name"]).exists() for im in d["images"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--lists", default=None)
    a = ap.parse_args()
    root = Path(os.path.expanduser(a.root))
    lists = globals().get("_EMBEDDED") or json.loads(Path(a.lists).read_text())
    ego = root / "data/raw/ego"
    out = {"root": str(root), "host": os.uname().nodename}

    # 1. 画像: data/raw/ego の 01〜15（前例と同じ集合）と、固定記録の全経路
    b1 = sorted(str(p.relative_to(root)) for p in ego.rglob("*.jpg") if p.name[:2] in V15 and "other" not in p.parts[-3])
    lock = sorted(set(lists["lock_paths"]))
    allp = sorted(set(b1) | set(lock))
    present = [p for p in allp if (root / p).is_file()]
    with Pool(a.workers) as pool:
        dig = dict(pool.map(_digest, [str(root / p) for p in present], chunksize=64))
    img = {p: dig[str(root / p)] for p in present}
    per_video, total = defaultdict(hashlib.sha256), hashlib.sha256()
    for p in b1:
        line = f"{p} {img[p]}\n".encode()
        per_video[Path(p).name[:2]].update(line)
        total.update(line)
    out["b1"] = {"count": len(b1), "bytes": sum((root / p).stat().st_size for p in b1), "sha256": total.hexdigest(),
                 "per_video": {v: {"count": sum(1 for p in b1 if Path(p).name[:2] == v),
                                   "sha256": per_video[v].hexdigest()} for v in V15}}
    out["lock"] = {"paths": len(lock), "present": sum(1 for p in lock if p in img),
                   "missing": [p for p in lock if p not in img],
                   "bytes": sum((root / p).stat().st_size for p in lock if p in img)}
    out["image_sha256"] = img

    # 2. 工程の注釈（CSV）と行
    rows = {}
    csvs = sorted((root / "data/annotations/egosurgery_phase").glob("*.csv"))
    for f in csvs:
        with f.open() as h:
            for r in csv.DictReader(h):
                rows[r["Frame"]] = (f.stem, r["Phase"])
    p15 = {k for k in rows if k[:2] in V15}
    out["phase_csv"] = {"files": [stat_entry(f, blob=True) for f in csvs], "rows_v15": len(p15),
                        "phase_only_v15": len(p15 - {Path(p).stem for p in b1})}

    # 3. 個別のファイル（manifest、術具注釈、折り、分割、重み、塔、Stage 2 の材料、把持の注釈）
    out["files"] = {}
    for group, paths in lists["files"].items():
        ents = []
        for p in paths:
            full = Path(os.path.expanduser(p)) if p.startswith(("/", "~")) else root / p
            e = stat_entry(full, blob=group in lists.get("blob_groups", []))
            if e["exists"] and full.suffix == ".json" and group in ("tool_ann", "tool_folds"):
                e.update(coco_counts(full, ego))
            if e["exists"] and group == "manifest":
                try:
                    d = json.loads(full.read_text())
                    if isinstance(d, dict) and "clips" in d:
                        fr = [x for c in d["clips"] for x in c["frames"]]
                        e["frames"] = len(fr)
                        e["missing_image_path"] = sum(not (root / x["image_path"]).exists() for x in fr)
                except Exception as ex:  # noqa: BLE001
                    e["parse_error"] = str(ex)
            ents.append(e)
        out["files"][group] = ents

    # 4. ディレクトリ単位（件数とバイト数だけ）
    out["dirs"] = {}
    for p in lists.get("dirs", []):
        d = root / p
        if d.is_dir():
            fs = [x for x in d.rglob("*") if x.is_file()]
            out["dirs"][p] = {"exists": True, "files": len(fs), "bytes": sum(x.stat().st_size for x in fs),
                              "is_link": d.is_symlink()}
        else:
            out["dirs"][p] = {"exists": False, "is_link": d.is_symlink()}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
