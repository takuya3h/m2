"""直した C3 の検査器の対照（非公式 T-2026-11-01-grasp-pilot-g、Task B-2）。判定の関数を import して呼ぶ（main() を呼ばないので出力を書かない）。
写しは版管理の外（$S/b/controls/）に作る。data/ は読むだけ。

    .venv-relation-detr/bin/python experiments/analysis/grasp_pilot_g/c3/c3_controls.py <S>/b/controls <out.json>
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HAND = ROOT / "data/annotations/egosurgery_hts/hand_seg"
TOOLHAND = ROOT / "data/annotations/egosurgery_hts/hand_tool_seg"
SPLITS = ("train", "val", "test", "extra")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def configure(m, hand=HAND, raw=None, splits=SPLITS):
    m.HAND4, m.HAND_PREFIX, m.HAND_SPLITS = hand, "", splits
    m.TOOLHAND, m.TOOLHAND_PREFIX = TOOLHAND, ""
    if raw is not None:
        m.RAW_HAND_PV = raw
    return m


def c3(m):
    r = m.check_c3_hand_total()
    return {k: r[k] for k in ("pass", "coverage_pass", "count_pass", "hand_instances_set", "segments_raw_annotated_n",
                              "missing_videos")}


def main():
    work, out = Path(sys.argv[1]), Path(sys.argv[2])
    work.mkdir(parents=True, exist_ok=True)
    new = ROOT / "scripts/audit_l0_hts_acceptance.py"
    res = {}
    res["as_is"] = c3(configure(load(new, "a0")))

    # 1. 03_3 を被覆の対象に戻した写し: raw 02_hand の写しの 03_3 に手を 1 件足す（03_3 のフレーム名の画像を 1 枚足す）
    raw = work / "raw02_with_03_3"
    if raw.exists():
        shutil.rmtree(raw)
    shutil.copytree(ROOT / "data/raw/OpenSurgery_Dataset/02_hand/json_per_video", raw)
    p = raw / "03_3/03_3.json"
    d = json.loads(p.read_text())
    iid = max([im["id"] for im in d["images"]] + [0]) + 1
    d["images"].append({"id": iid, "file_name": "03_3_0001.jpg", "width": 1920, "height": 1080})
    d["annotations"].append({"id": 10 ** 9, "image_id": iid, "category_id": 1, "bbox": [0.0, 0.0, 10.0, 10.0],
                             "area": 100.0, "iscrowd": 0})
    p.write_text(json.dumps(d))
    res["ctrl_03_3_restored"] = c3(configure(load(new, "a1"), raw=raw))

    # 2. 手のインスタンスを 1 件除いた写し（val の最初の注釈）
    hand1 = work / "hand_minus1"
    hand1.mkdir(exist_ok=True)
    for sp in SPLITS:
        d = json.loads((HAND / f"{sp}.json").read_text())
        if sp == "val":
            res["ctrl_minus1_removed_ann_id"] = d["annotations"][0]["id"]
            d["annotations"] = d["annotations"][1:]
        (hand1 / f"{sp}.json").write_text(json.dumps(d))
    res["ctrl_minus1"] = c3(configure(load(new, "a2"), hand=hand1))

    # 3. 入力のファイルを一つ隠した写し（extra.json を置かない）
    hidden = work / "hand_hidden_extra"
    hidden.mkdir(exist_ok=True)
    for sp in ("train", "val", "test"):
        shutil.copy(HAND / f"{sp}.json", hidden / f"{sp}.json")
    try:
        r = c3(configure(load(new, "a3"), hand=hidden))
        res["ctrl_hidden_input"] = {"raised": False, "result": r}
    except FileNotFoundError as e:
        res["ctrl_hidden_input"] = {"raised": True, "error": str(e).replace(str(work), "<work>")}

    # 参考: 直す前の検査器（$S/b に控えた原本）。経路は本物を与える（控えの置き場では ROOT がずれるため）
    orig = load(Path(sys.argv[3]), "orig") if len(sys.argv) > 3 else None
    if orig is not None:
        orig.RAW_HAND_PV = ROOT / "data/raw/OpenSurgery_Dataset/02_hand/json_per_video"
        orig.TOOLHAND = TOOLHAND
        orig._splits.__defaults__ = ("",)
        # 欠陥 1: val.json を隠した写しを、旧版は止めずに件数の減った値で返す
        noval = work / "hand_hidden_val"
        noval.mkdir(exist_ok=True)
        for sp in ("train", "test"):
            shutil.copy(HAND / f"{sp}.json", noval / f"{sp}.json")
        orig.HAND4 = noval
        r = orig.check_c3_hand_total()
        res["orig_hidden_val"] = {"raised": False, "hand_instances_current": r["hand_instances_current"], "pass": r["pass"]}
        try:
            c3(configure(load(new, "a5"), hand=noval, splits=("train", "val", "test")))
            res["new_hidden_val"] = {"raised": False}
        except FileNotFoundError as e:
            res["new_hidden_val"] = {"raised": True, "error": str(e).replace(str(work), "<work>")}
        # 欠陥 2: 候補（train・val・test。旧版は extra を読まない）に旧版の C3 を当てる
        orig.HAND4 = HAND
        r = orig.check_c3_hand_total()
        res["orig_c3_on_candidate"] = {k: r[k] for k in ("pass", "hand_instances_current", "missing_videos",
                                                          "segments_raw", "segments_present")}
    # C1 が全件を見たこと
    m = configure(load(new, "a4"))
    c1 = m.check_c1_polygon_points()
    n_train = len(json.loads((TOOLHAND / "train.json").read_text())["annotations"])
    res["c1_full_scan"] = {"toolhand_train_annotations": n_train, "profiled": sum(c1["toolhand_seg_types"].values())}
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
