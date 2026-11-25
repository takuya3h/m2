"""検出塔のクラス別の誤りの分解（非公式 T-2026-11-22-dtower-class-error-breakdown）の共通部分。

本体の .venv で動かす（numpy と pycocotools だけ）。GPU・学習・推論を使わない。

- 材料と記録のファイルは read_bytes / read_json を通して開き、経路・sha256・大きさ・目的を
  reads.jsonl に一行ずつ足す（完了判定 i・j の「読んだファイルの一覧」）
- test の予測と注釈（eval_test.*、instances_test.json、per_class_ap_test.json、test_access.json）は
  開く前に止める。工程のマニフェストの test.json も、利用者の判断が出るまでは開かない（allow_manifest_test）
- AP の類は保存済みの予測の全件で、記録の値を作ったのと同じ COCOeval（area all、maxDets 100、
  クラス別 AP は precision[:, :, k, 0, -1] の p > -1 の平均）で計算する。id 0 の注釈もそのまま使う
- 分解（SPEC §4.2〜§4.4）は score 0.05 以上の予測だけで行う。IoU は pycocotools の bbox の IoU
"""
from __future__ import annotations

import contextlib
import gzip
import hashlib
import io
import json
import math
import re
from pathlib import Path

import numpy as np
from pycocotools import mask as mask_utils
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval as CocoEvalAlias  # alias: semgrep hook

TASK_ID = "T-2026-11-22-dtower-class-error-breakdown"
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "experiments/analysis/dtower_class_error_breakdown"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
RERUN_RUNS = STORE / "T-2026-11-07-dtower-rerun/runs"
FIX = STORE / "T-2026-10-19-stage2-pilot-fix-epoch4-shuffle"
ANN = ROOT / "data/annotations/egosurgery_tool_folds"
FROZEN = ROOT / "experiments/analysis/dtower_rerun/frozen_towers.json"
T2_DIR = ROOT / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42"
T2_PREDS = FIX / "identity/plain_val_preds.json.gz"
T2_PD_PLAIN = ROOT / "experiments/analysis/stage2_pilot_fix/identity/pd_plain.json"
# SPEC §1.1（tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/RESULT.md §2 の G2）の表示の値
T2_RECORD = {"AP": 0.7273450, "target_AP": 0.7950748, "control_AP": 0.6726632}
MANIFEST = ROOT / "data/processed/phase_manifest"
FOLD_TABLE = ROOT / "docs/stage0/A1_fold_table.md"
CONVENTIONS = ROOT / "context/conventions.md"
READS = OUT / "reads.jsonl"

SCORE_MIN = 0.05  # docs/stage0/A6_error_decomposition.md
IOU_MATCH = 0.5
IOU_NEAR = 0.1
TARGETS = [("T1", f) for f in "ABCDE"] + [("T2", "A")]
FOCUS = ["Forceps", "Gauze", "Hook", "Scissors"]
COMPARE = ["Tweezers", "Syringe"]

TEST_FILE = re.compile(r"^(eval_test\..*|instances_test\.json|per_class_ap_test\.json|test_access\.json)$")
allow_manifest_test = False
log_reads = True


def guard(path) -> None:
    """test の予測と注釈を開く前に止める。"""
    p = Path(path)
    if TEST_FILE.match(p.name):
        raise RuntimeError(f"test のファイルは開かない: {p}")
    if p.name == "test.json" and p.parent.resolve() == MANIFEST.resolve() and not allow_manifest_test:
        raise RuntimeError(f"工程のマニフェストの test.json は利用者の判断が出るまで開かない: {p}")


def read_bytes(path, purpose: str, kind: str = "material") -> bytes:
    guard(path)
    data = Path(path).read_bytes()
    if log_reads:
        entry = {"path": str(Path(path).resolve()), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                 "purpose": purpose, "kind": kind}
        with open(READS, "a") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return data


def read_json(path, purpose: str, kind: str = "material"):
    data = read_bytes(path, purpose, kind)
    if str(path).endswith(".gz"):
        data = gzip.decompress(data)
    return json.loads(data)


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, allow_nan=True) + "\n")


def folds() -> dict[str, dict[str, list[str]]]:
    """正本 docs/stage0/A1_fold_table.md（scripts/stage1_ptower.py の folds と同じ読み方）。"""
    text = read_bytes(FOLD_TABLE, "Fold の正本の表", "record").decode()
    out = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == 4 and len(cells[0]) == 1 and cells[0] in "ABCDE":
            out[cells[0]] = {k: re.findall(r"\b\d{2}\b", c) for k, c in zip(("test", "val", "train"), cells[1:])}
    assert sorted(out) == list("ABCDE"), out
    return out


def groups() -> dict[str, list[str]]:
    """conventions#det_groups の表（scripts/stage2pilot/det_metrics.py の read_groups と同じ読み方）。"""
    text = read_bytes(CONVENTIONS, "conventions#det_groups", "record").decode()
    m = re.search(r'<a id="det_groups"></a>\n(.*?)(?=<a id="|\Z)', text, re.S)
    keys = {"標的群": "signature", "陰性対照群": "negative"}
    out = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] in keys:
            out[keys[cells[0]]] = [c.strip() for c in cells[1].split("、")]
    assert set(out) == set(keys.values()), out
    return out


def video_of(file_name) -> str:
    return Path(str(file_name)).stem.split("_")[0]


def coco_from(dataset: dict) -> COCO:
    with contextlib.redirect_stdout(io.StringIO()):
        c = COCO()
        c.dataset = dataset
        c.createIndex()
    return c


def ann_path(fold: str, part: str) -> Path:
    assert part in ("train", "val"), part
    return ANN / fold / f"instances_{part}.json"


def load_ann(fold: str, part: str) -> dict:
    return read_json(ann_path(fold, part), f"Fold {fold} の {part} の注釈")


def t1_run(fold: str, seed: int = 42) -> str:
    return f"dtowerrerun_p12_dcoco_fold{fold}_seed{seed}"


def pred_path(tower: str, fold: str) -> Path:
    if tower == "T1":
        return RERUN_RUNS / t1_run(fold) / "eval_val.detections.json.gz"
    assert (tower, fold) == ("T2", "A"), (tower, fold)
    return T2_PREDS


def arrays(dets: list) -> dict:
    """予測の並びを保ったまま numpy の配列にする（json の float は float64 へそのまま入る）。"""
    return {"image_id": np.array([int(d["image_id"]) for d in dets], dtype=np.int64),
            "category_id": np.array([int(d["category_id"]) for d in dets], dtype=np.int64),
            "bbox": np.array([[float(v) for v in d["bbox"]] for d in dets], dtype=np.float64).reshape(-1, 4),
            "score": np.array([float(d["score"]) for d in dets], dtype=np.float64)}


def load_preds(tower: str, fold: str) -> dict:
    raw = read_json(pred_path(tower, fold), f"{tower} Fold {fold} の保存済みの val の予測")
    dets = raw["detections"] if tower == "T1" else raw
    P = arrays(dets)
    assert np.isfinite(P["score"]).all() and np.isfinite(P["bbox"]).all()
    P["images_in_file"] = raw.get("images") if tower == "T1" else None
    return P


def subset(P: dict, keep) -> dict:
    keep = np.asarray(keep)
    return {k: (v[keep] if isinstance(v, np.ndarray) else v) for k, v in P.items()}


def results(P: dict) -> list:
    return [{"image_id": int(i), "category_id": int(c), "bbox": [float(v) for v in b], "score": float(s)}
            for i, c, b, s in zip(P["image_id"], P["category_id"], P["bbox"], P["score"])]


def iou(dboxes: np.ndarray, gboxes: np.ndarray) -> np.ndarray:
    """COCO の bbox の IoU（xywh）。行が予測、列が GT。"""
    if len(dboxes) == 0 or len(gboxes) == 0:
        return np.zeros((len(dboxes), len(gboxes)))
    return np.asarray(mask_utils.iou(np.asarray(dboxes, dtype=np.float64), np.asarray(gboxes, dtype=np.float64),
                                     [0] * len(gboxes)), dtype=np.float64).reshape(len(dboxes), len(gboxes))


def by_image(ids: np.ndarray) -> dict[int, np.ndarray]:
    """画像の id ごとの行の番号（元の並びの順）。"""
    order = np.argsort(ids, kind="stable")
    uniq, start = np.unique(ids[order], return_index=True)
    bounds = list(start[1:]) + [len(order)]
    return {int(u): order[s:e] for u, s, e in zip(uniq, start, bounds)}


def gt_arrays(ann: dict) -> dict:
    a = ann["annotations"]
    return {"id": np.array([x["id"] for x in a], dtype=np.int64),
            "image_id": np.array([x["image_id"] for x in a], dtype=np.int64),
            "category_id": np.array([x["category_id"] for x in a], dtype=np.int64),
            "bbox": np.array([x["bbox"] for x in a], dtype=np.float64).reshape(-1, 4)}


def evaluate(gt: COCO, P: dict, img_ids=None) -> dict:
    """記録と同じ COCOeval。クラス別の AP・AP50・AP75 と四つの平均を返す（注釈の無いクラスは nan）。"""
    ids = sorted(gt.getImgIds()) if img_ids is None else sorted(int(i) for i in img_ids)
    res = results(P)
    with contextlib.redirect_stdout(io.StringIO()):
        dt = gt.loadRes(res) if res else COCO()
        ev = CocoEvalAlias(gt, dt, "bbox")
        ev.params.imgIds = ids
        ev.evaluate()
        ev.accumulate()
        ev.summarize()
    prec = ev.eval["precision"]
    t50 = int(np.flatnonzero(np.isclose(ev.params.iouThrs, 0.5))[0])
    t75 = int(np.flatnonzero(np.isclose(ev.params.iouThrs, 0.75))[0])
    names = {c["id"]: c["name"] for c in gt.dataset["categories"]}
    per_class = {}
    for k, cid in enumerate(ev.params.catIds):
        out = {}
        for key, p in (("AP", prec[:, :, k, 0, -1]), ("AP50", prec[t50, :, k, 0, -1]), ("AP75", prec[t75, :, k, 0, -1])):
            p = p[p > -1]
            out[key] = float(p.mean()) if p.size else float("nan")
        per_class[names[cid]] = out
    return {"images": len(ids), "detections": len(res), "stats": [float(v) for v in ev.stats],
            "AP": float(ev.stats[0]), "AP50": float(ev.stats[1]), "AP75": float(ev.stats[2]),
            "per_class": per_class, "means": means({c: v["AP"] for c, v in per_class.items()}),
            "means50": means({c: v["AP50"] for c, v in per_class.items()}),
            "means75": means({c: v["AP75"] for c, v in per_class.items()})}


_GROUPS = None


def class_groups(names) -> dict[str, list[str]]:
    global _GROUPS
    if _GROUPS is None:
        _GROUPS = groups()
    g = dict(_GROUPS)
    used = set(g["signature"]) | set(g["negative"])
    g["other"] = [c for c in names if c not in used]
    g["all"] = list(names)
    return g


def means(values: dict[str, float]) -> dict:
    """全クラス・signature class・negative control・その他の平均。nan のクラスは除き、除いたクラスを書く。"""
    out = {}
    for g, classes in class_groups(list(values)).items():
        used = [values[c] for c in classes if c in values and not math.isnan(values[c])]
        out[g] = float(np.mean(used)) if used else float("nan")
        out[f"{g}_missing"] = [c for c in classes if c in values and math.isnan(values[c])]
    return out
