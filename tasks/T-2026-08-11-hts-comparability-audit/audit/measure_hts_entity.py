"""領域注釈（EgoSurgery-HTS）の実体を測る。読み取りのみ。

Phase B Step 2-5 に対応する。出力は AUD/hts_entity.txt へリダイレクトして保存する。
"""

import collections
import csv
import json
import pathlib
import sys

sys.path.insert(0, "src")

HTS = pathlib.Path("data/annotations/egosurgery_hts")
TOOL = pathlib.Path("data/annotations/egosurgery_tool")
PHASE = pathlib.Path("data/annotations/egosurgery_phase")
SPLITS = ("train", "val", "test")


def stem(file_name: str) -> str:
    return pathlib.PurePath(file_name).stem


def load_coco(path: pathlib.Path):
    with path.open() as f:
        return json.load(f)


def annotated_stems(doc) -> set:
    """annotation を 1 件以上持つ image の stem 集合。列挙だけでは不十分。"""
    with_ann = {a["image_id"] for a in doc["annotations"]}
    return {stem(im["file_name"]) for im in doc["images"] if im["id"] in with_ann}


def all_stems(doc) -> set:
    return {stem(im["file_name"]) for im in doc["images"]}


def cross_split_overlap(sets: dict) -> dict:
    keys = list(sets)
    out = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            out[f"{a}∩{b}"] = len(sets[a] & sets[b])
    return out


print("=" * 72)
print("1. 領域注釈 3 種の規模（実測）")
print("=" * 72)

scale = {}
for kind in ("hand_seg", "tool_seg", "hand_tool_seg"):
    print(f"\n--- {kind} ---")
    for split in SPLITS + ("extra",):
        p = HTS / kind / f"{split}.json"
        if not p.exists():
            print(f"  {split}: ファイル無し")
            continue
        d = load_coco(p)
        a_stems = annotated_stems(d)
        scale[(kind, split)] = a_stems
        print(
            f"  {split:5s} images={len(d['images']):6d} anns={len(d['annotations']):7d} "
            f"ann>=1 の image={len(a_stems):6d} cats={len(d['categories']):3d} "
            f"列挙のみで注釈0件={len(all_stems(d)) - len(a_stems):5d}"
        )
        if split == "train":
            print(f"    categories: {[c['name'] for c in d['categories']]}")

print("\n" + "=" * 72)
print("2. 術具 bbox split との集合差（両方向）")
print("=" * 72)

tool_stems = {}
tool_doc = {}
for split in SPLITS:
    d = load_coco(TOOL / f"instances_{split}.json")
    tool_doc[split] = d
    tool_stems[split] = all_stems(d)
    print(f"  tool {split:5s}: {len(tool_stems[split])} frames")
tool_all = set().union(*tool_stems.values())
print(f"  tool 合計: {len(tool_all)}")

for kind in ("hand_seg", "tool_seg", "hand_tool_seg"):
    print(f"\n--- {kind} vs 術具 bbox ---")
    for split in SPLITS:
        hs = scale.get((kind, split), set())
        ts = tool_stems[split]
        cov = len(hs & ts)
        print(
            f"  {split:5s} 被覆={cov:6d}/{len(ts):6d} ({cov / len(ts) * 100:6.2f}%) "
            f"| 術具にあり注釈なし={len(ts - hs):5d} | 注釈にあり術具外={len(hs - ts):5d}"
        )
    hs_all = set().union(*[scale.get((kind, s), set()) for s in SPLITS])
    extra = scale.get((kind, "extra"), set())
    print(f"  3 split 合計 被覆={len(hs_all & tool_all)}/{len(tool_all)}")
    print(f"  extra（術具 split 外の拡張フレーム）= {len(extra)}  うち術具集合と交差={len(extra & tool_all)}")

print("\n" + "=" * 72)
print("3. 分割を跨ぐフレームの重複（陽性対照つき）")
print("=" * 72)

for kind in ("hand_seg", "tool_seg", "hand_tool_seg"):
    sets = {s: scale.get((kind, s), set()) for s in SPLITS}
    print(f"  {kind:14s} {cross_split_overlap(sets)}")

print("\n  --- 動画（セグメント）単位 ---")
for kind in ("hand_tool_seg",):
    sets = {s: {x.rsplit("_", 1)[0] for x in scale.get((kind, s), set())} for s in SPLITS}
    print(f"  {kind:14s} {cross_split_overlap(sets)}")
    for s in SPLITS:
        print(f"    {s}: {sorted(sets[s])}")

probe = next(iter(scale[("hand_tool_seg", "val")]))
injected = dict(
    train=scale[("hand_tool_seg", "train")] | {probe},
    val=scale[("hand_tool_seg", "val")],
    test=scale[("hand_tool_seg", "test")],
)
ctl = cross_split_overlap(injected)
print(f"\n  陽性対照: val の識別子 {probe!r} を train へ 1 件注入 → {ctl}")
assert ctl["train∩val"] == 1, "陽性対照が成立していない"
print("  陽性対照 成立（1 件だけ検出）")

print("\n" + "=" * 72)
print("4. 注釈が無いフレーム（loss_mask）の実数と内訳 — Q5")
print("=" * 72)

from egosurgery.datasets.loss_mask import DEFAULT_ROOT, load_loss_mask  # noqa: E402

print(f"  DEFAULT_ROOT: {DEFAULT_ROOT}  {'存在' if DEFAULT_ROOT.exists() else '無し'}")

masks = {}
total = 0
for s in SPLITS:
    try:
        m = load_loss_mask(s)
    except Exception as e:  # noqa: BLE001
        print(f"  {s}: {type(e).__name__} {e}")
        continue
    masks[s] = set(m)
    total += len(m)
    vids = collections.Counter(x.rsplit("_", 1)[0] for x in m)
    print(f"  {s:5s} 件数={len(m):4d} セグメント別={dict(sorted(vids.items()))}")
print(f"  合計={total}  （SPEC の主張 460 と{'一致' if total == 460 else '不一致'}）")

print("\n  --- loss_mask は「術具 split にあり hand_tool_seg 注釈が無い」集合と一致するか ---")
for s in SPLITS:
    derived = tool_stems[s] - scale[("hand_tool_seg", s)]
    m = masks.get(s, set())
    print(
        f"  {s:5s} 導出={len(derived):4d} loss_mask={len(m):4d} "
        f"一致={'はい' if derived == m else 'いいえ'} 差={len(derived ^ m)}"
    )

print("\n  --- 除外フレームの術具クラス内訳（Q5 の核心） ---")
cat_name = {c["id"]: c["name"] for c in tool_doc["train"]["categories"]}
all_missing = set().union(*masks.values()) if masks else set()

frames_by_class = collections.Counter()
missing_by_class = collections.Counter()
class_sets_missing = collections.Counter()
n_tools_missing = collections.Counter()
missing_no_tool = 0

for s in SPLITS:
    d = tool_doc[s]
    id2stem = {im["id"]: stem(im["file_name"]) for im in d["images"]}
    per_frame = collections.defaultdict(set)
    for a in d["annotations"]:
        per_frame[id2stem[a["image_id"]]].add(cat_name[a["category_id"]])
    for st in tool_stems[s]:
        cls = per_frame.get(st, set())
        for c in cls:
            frames_by_class[c] += 1
        if st in masks.get(s, set()):
            if not cls:
                missing_no_tool += 1
            for c in cls:
                missing_by_class[c] += 1
            class_sets_missing[frozenset(cls)] += 1
            n_tools_missing[len(cls)] += 1

print(f"  {'クラス':22s} {'除外':>6s} {'全体':>7s} {'除外率':>8s}")
for c in sorted(frames_by_class, key=lambda x: -(missing_by_class[x] / max(frames_by_class[x], 1))):
    r = missing_by_class[c] / frames_by_class[c] * 100 if frames_by_class[c] else 0.0
    print(f"  {c:22s} {missing_by_class[c]:6d} {frames_by_class[c]:7d} {r:7.2f}%")
print(f"  除外フレームのうち術具の箱が 1 つも無いもの: {missing_no_tool}")
print(f"  除外フレームの術具個数分布: {dict(sorted(n_tools_missing.items()))}")
print("\n  除外フレームのクラス集合（上位 12）:")
for k, v in class_sets_missing.most_common(12):
    print(f"    {v:4d}  {sorted(k) if k else '（術具なし）'}")

print("\n  --- 除外フレームの工程内訳 ---")
stem2phase = {}
for csv_path in sorted(PHASE.glob("*.csv")):
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            stem2phase[row["Frame"]] = row["Phase"]
print(f"  工程ラベルを持つフレーム総数: {len(stem2phase)}")

base_phase = collections.Counter(stem2phase[x] for x in tool_all if x in stem2phase)
miss_phase = collections.Counter(stem2phase[x] for x in all_missing if x in stem2phase)
no_label = sum(1 for x in all_missing if x not in stem2phase)
print(f"  除外 {len(all_missing)} のうち工程ラベル無し: {no_label}")
print(f"  {'工程':16s} {'除外':>6s} {'術具split全体':>12s} {'除外率':>8s}")
for p in sorted(base_phase, key=lambda x: -(miss_phase[x] / max(base_phase[x], 1))):
    r = miss_phase[p] / base_phase[p] * 100 if base_phase[p] else 0.0
    print(f"  {p:16s} {miss_phase[p]:6d} {base_phase[p]:12d} {r:7.2f}%")
