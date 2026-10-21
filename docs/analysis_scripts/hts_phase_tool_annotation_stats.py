"""egosurgery_hts の 3 種の注釈（hand_seg・tool_seg・hand_tool_seg）と、工程 CSV・術具 bbox の関係の EDA（読み取り専用）。

出力: docs/hts_phase_tool_annotation_stats.md（引数で出力先を変えられる）
実行（リポジトリのルートで）: .venv/bin/python docs/analysis_scripts/hts_phase_tool_annotation_stats.py [出力先]
"""
import collections
import csv
import glob
import itertools
import json
import os
import re
import sys

import numpy as np
from pycocotools import mask as M

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/docs/hts_phase_tool_annotation_stats.md"
MAIN = "phase_tool_annotation_stats.md"  # 先行の EDA（同じ docs/ にある）
ANN = f"{ROOT}/data/annotations"
HTS = f"{ANN}/egosurgery_hts"
JM = f"{ROOT}/data/processed/joint_manifest"
RAW_HAND = f"{ROOT}/data/raw/OpenSurgery_Dataset/02_hand/json_per_video"
FRAMES = f"{ROOT}/data/raw/OpenSurgery_Dataset/01_frames/initial_videos"
MASTER = f"{ROOT}/data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw"
SPLITS = ["train", "val", "test"]
FILES = SPLITS + ["extra"]
TYPES = ["hand_seg", "tool_seg", "hand_tool_seg"]
TOOLS = json.load(open(f"{JM}/tool_categories.json"))
T = [TOOLS[str(i)] for i in range(15)]
TARGET = {"Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory"}
NEGCTL = {"Gauze", "Mouth Gag", "Suction Cannula", "Tweezers"}
CAN = ["disinfection", "design", "anesthesia", "incision", "dissection", "hemostasis", "irrigation", "closure",
       "dressing"]
ci = {p: i for i, p in enumerate(CAN)}
nP = len(CAN)
AB = {"disinfection": "DI", "design": "DE", "anesthesia": "AN", "incision": "IN", "dissection": "DS",
      "hemostasis": "HE", "irrigation": "IR", "closure": "CL", "dressing": "DR"}
HN = ["自分の左手", "自分の右手", "他者の左手", "他者の右手"]  # hand_seg の category_id 1〜4
SIDE = {3: "左", 4: "右", 5: "両手"}  # hand_tool_seg の Left / Right / Two Hands Tool
SIDES = ["左", "右", "両手"]


def bn(s):
    return os.path.splitext(os.path.basename(s))[0]


def grp(n):
    return "標的" if n in TARGET else ("陰性対照" if n in NEGCTL else ("—" if n in T else "（Tool15 外）"))


# ---------- 読み込み ----------
frames = []  # 術具注釈のあるフレーム（動画 01〜15）= 本書の主な母集団
for s in SPLITS:
    d = json.load(open(f"{JM}/{s}.json"))
    for c in d["clips"]:
        for f in c["frames"]:
            frames.append(dict(split=s, video=c["video"], clip=c["clip_id"], fid=f["frame"], phase=f["phase"],
                               labels=list(f["tool_labels"]), boxes=list(f["boxes"])))
N = len(frames)
fids = [f["fid"] for f in frames]
fset = set(fids)

csv_all = []
for p in sorted(glob.glob(f"{ANN}/egosurgery_phase/*.csv")):
    clip = os.path.basename(p)[:-4]
    for r in csv.DictReader(open(p)):
        csv_all.append(dict(video=clip.split("_")[0], clip=clip, cnum=int(clip.split("_")[1]),
                            idx=int(r["Frame"].rsplit("_", 1)[1]), fid=r["Frame"], phase=r["Phase"]))
csv_rows = sorted([r for r in csv_all if int(r["video"]) <= 15], key=lambda r: (r["video"], r["cnum"], r["idx"]))
csv_phase = {r["fid"]: r["phase"] for r in csv_rows}
assert all(csv_phase[f["fid"]] == f["phase"] for f in frames)
_pos = collections.Counter()
csv_pos = {}
for r in csv_rows:
    csv_pos[r["fid"]] = _pos[r["clip"]]
    _pos[r["clip"]] += 1
prog = {}
for v, g in itertools.groupby(csv_rows, key=lambda r: r["video"]):
    g = list(g)
    for i, r in enumerate(g):
        prog[r["fid"]] = i / (len(g) - 1)

H_ = {k: {} for k in TYPES}  # 種類 -> ファイル -> dict(cats, ann: fid -> [ann], imgs)
for k in TYPES:
    for fn in FILES:
        d = json.load(open(f"{HTS}/{k}/{fn}.json"))
        m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
        per = collections.defaultdict(list)
        for a in d["annotations"]:
            per[m[a["image_id"]]].append(a)
        H_[k][fn] = dict(cats={c["id"]: c["name"] for c in d["categories"]}, ann=per, imgs=set(m.values()),
                         n_img=len(d["images"]), n_ann=len(d["annotations"]))
CATS = {k: H_[k]["train"]["cats"] for k in TYPES}
assert all(H_[k][fn]["cats"] == CATS[k] for k in TYPES for fn in FILES)
assert [CATS["hand_seg"][i] for i in range(1, 5)] == ["First Person's Left Hand", "First Person's Right Hand",
                                                     "Other Person's Left Hand", "Other Person's Right Hand"]
assert [CATS["hand_tool_seg"][i] for i in range(1, 6)] == ["First Person's Left Hand", "First Person's Right Hand",
                                                          "Left Hand Tool", "Right Hand Tool", "Two Hands Tool"]
TSN = CATS["tool_seg"]  # id -> 31 クラス名
TS_NAMES = [TSN[i] for i in sorted(TSN)]
assert set(T) <= set(TS_NAMES)
for k in TYPES:
    for s in SPLITS:
        assert H_[k][s]["imgs"] <= {f["fid"] for f in frames if f["split"] == s}
A = {k: {f: a for s in SPLITS for f, a in H_[k][s]["ann"].items()} for k in TYPES}  # 母集団の注釈
X = {k: H_[k]["extra"] for k in TYPES}
LM = {s: set(open(f"{HTS}/hand_tool_seg/loss_mask/{s}.txt").read().split()) for s in SPLITS}

ph = np.array([ci[f["phase"]] for f in frames])
vid = np.array([f["video"] for f in frames])
has = {k: np.array([bool(A[k].get(x)) for x in fids]) for k in TYPES}
lm = np.array([x in LM[f["split"]] for x, f in zip(fids, frames)])
ph_n = np.array([(ph == j).sum() for j in range(nP)])
SMALL = {j for j in range(nP) if ph_n[j] < 200}
videos = sorted(set(vid))


# ---------- 書式 ----------
def pct(x, d=1):
    if x == 0:
        return "0"
    s = f"{100 * x:.{d}f}"
    return f"<{10 ** -d:.{d}f}" if float(s) == 0 else s


def rate(a, b):
    return pct(a / b) if b else "—"


def phn(j):
    return CAN[j] + ("†" if j in SMALL else "")


NUMLIKE = re.compile(r"^[\d,.<%/·—\-*]*$")


def table(head, rows, align=None):
    align = align or ["l"] + ["r" if all(NUMLIKE.match(str(r[k])) for r in rows) else "l"
                              for k in range(1, len(head))]
    sep = ["---:" if a == "r" else ("---" if a == "l" else ":---:") for a in align]
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join(sep) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def H(pv):
    pv = np.asarray(pv, float)
    pv = pv[pv > 0] / pv.sum()
    return float(-(pv * np.log2(pv)).sum())


def aid(sid):
    return "s" + sid.replace(".", "-")


def ref(sid, doc=""):
    return f"[{'付録 ' if sid.isalpha() else '§'}{sid}]({doc}#{aid(sid)})"


class Doc:
    def __init__(self):
        self.md, self.toc = [], []

    def w(self, s=""):
        self.md.append(s)

    def h(self, level, sid, title):
        self.toc.append((level, sid, title))
        label = title if sid.isalpha() else (f"{sid}. {title}" if "." not in sid and level == 2 else f"{sid} {title}")
        self.w(f"{'#' * level} <a id=\"{aid(sid)}\"></a>{label}\n")

    def details(self, summary, body):
        self.w(f"<details><summary>{summary}</summary>\n")
        self.w(body)
        self.w("\n</details>\n")


def mc(c, k=None):
    """Counter の上位。同数は名前の順にして、集合の反復順に左右されないようにする。"""
    return sorted(c.items(), key=lambda x: (-x[1], str(x[0])))[:k]


def box_iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    u = a[2] * a[3] + b[2] * b[3] - inter
    return inter / u if u > 0 else 0.0


def greedy(ious, thr=0.5):
    """IoU の大きい順に 1 対 1 で対応づけ、閾値以上の対の IoU を返す。"""
    out, used_a, used_b = [], set(), set()
    for v, a, b in sorted(((ious[a][b], a, b) for a in range(len(ious)) for b in range(len(ious[0]))), reverse=True):
        if v < thr:
            break
        if a in used_a or b in used_b:
            continue
        used_a.add(a)
        used_b.add(b)
        out.append(v)
    return out


# ---------- 構造の検査 ----------
# hand_seg の手 box と raw02（先行 EDA §4 の手の出所）
raw = collections.defaultdict(list)
for p in sorted(glob.glob(f"{RAW_HAND}/*/*.json")):
    d = json.load(open(p))
    m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
    for a in d["annotations"]:
        raw[m[a["image_id"]]].append((a["category_id"], tuple(round(v, 1) for v in a["bbox"])))
hs_raw_same = sum(sorted(raw.get(x, [])) == sorted((a["category_id"], tuple(round(v, 1) for v in a["bbox"]))
                                                    for a in A["hand_seg"].get(x, [])) for x in fids)
# hand_tool_seg の自分の手マスクと hand_seg の自分の手マスク
ht_fp_same = sum(sorted((a["category_id"], a["segmentation"]["counts"]) for a in A["hand_tool_seg"][x]
                        if a["category_id"] <= 2)
                 == sorted((a["category_id"], a["segmentation"]["counts"]) for a in A["hand_seg"].get(x, [])
                           if a["category_id"] <= 2) for x in A["hand_tool_seg"])
# 注釈 0 件の画像
zero_img = {k: {fn: H_[k][fn]["n_img"] - len(H_[k][fn]["ann"]) for fn in FILES} for k in TYPES}
# tool_seg の bbox 欄とマスクの外接矩形
ts_all = [a for x in fids for a in A["tool_seg"].get(x, [])]
tb = M.toBbox([a["segmentation"] for a in ts_all])
bbox_eq = float(np.mean([np.allclose(tb[i], a["bbox"], atol=1.0) for i, a in enumerate(ts_all)]))
area_eq = float(np.mean(M.area([a["segmentation"] for a in ts_all]) == np.array([a["area"] for a in ts_all])))

# ---------- 把持術具のクラスを決める ----------
held = {}  # fid -> [dict(side, cls, src, ann, ts)]
fp = {}  # fid -> {1: rle, 2: rle}
n_fp_multi = 0
link_best_ts = []  # 完全一致しない把持術具マスクの、tool_seg マスクとの IoU の最大値
for x, anns in A["hand_tool_seg"].items():
    tsl = A["tool_seg"].get(x, [])
    by_counts = {a["segmentation"]["counts"]: a for a in tsl}
    fp[x] = {}
    held[x] = []
    for a in anns:
        c = a["category_id"]
        if c <= 2:
            n_fp_multi += c in fp[x]
            fp[x][c] = a
            continue
        t = by_counts.get(a["segmentation"]["counts"])
        rec = dict(side=SIDE[c], ann=a, ts=t)
        if t is not None:
            rec.update(cls=TSN[t["category_id"]], src="tool_seg")
        else:
            if tsl:
                link_best_ts.append(float(np.max(M.iou([a["segmentation"]], [s_["segmentation"] for s_ in tsl],
                                                       [0] * len(tsl)))))
            rec.update(cls=None, src="none")
        held[x].append(rec)
fi = {x: i for i, x in enumerate(fids)}
master = collections.defaultdict(list)  # HTS の元の注釈（38 クラス、矩形）。手以外
for p in sorted(glob.glob(f"{MASTER}/*/annotations.json")):
    d = json.load(open(p))
    cats = {c["id"]: c["name"] for c in d["categories"]}
    m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
    for a in d["annotations"]:
        if "Hand" not in cats[a["category_id"]]:
            master[m[a["image_id"]]].append((cats[a["category_id"]], a["bbox"]))
for x, recs in held.items():
    f = frames[fi[x]]
    for rec in recs:
        if rec["src"] != "none":
            continue
        ious = [box_iou(rec["ann"]["bbox"], b) for b in f["boxes"]]
        if ious and max(ious) >= 0.5:
            rec.update(cls=T[f["labels"][int(np.argmax(ious))]], src="bbox")
            continue
        cand = [(box_iou(rec["ann"]["bbox"], b), n) for n, b in master.get(x, [])]
        if cand and max(cand)[0] >= 0.5:
            rec.update(cls=max(cand)[1], src="master")
n_held = sum(len(v) for v in held.values())
src_cnt = collections.Counter(r["src"] for v in held.values() for r in v)

# 把持術具は同じ側の自分の手とどう結びつくか（マスクの IoU 最大 / box の IoU 最大 / 画素の重なり）
der = collections.Counter()
for x, recs in held.items():
    tsl = A["tool_seg"].get(x, [])
    for rec in recs:
        hand = fp[x].get({"左": 1, "右": 2}.get(rec["side"]))
        if rec["src"] != "tool_seg" or hand is None:
            continue
        j = next(k_ for k_, s_ in enumerate(tsl) if s_ is rec["ts"])
        tr = [s_["segmentation"] for s_ in tsl]
        miou = M.iou([hand["segmentation"]], tr, [0] * len(tr))[0]
        biou = [box_iou(hand["bbox"], s_["bbox"]) for s_ in tsl]
        der["n"] += 1
        der["mask"] += bool(miou.max() > 0 and int(np.argmax(miou)) == j)
        der["box"] += bool(max(biou) > 0 and int(np.argmax(biou)) == j)
        der["zero"] += bool(M.area(M.merge([hand["segmentation"], tr[j]], intersect=True)) == 0)
hs_bbox_eq = float(np.mean(np.all(np.abs(M.toBbox([a["segmentation"] for x in fids for a in A["hand_seg"].get(x, [])])
                                         - np.array([a["bbox"] for x in fids for a in A["hand_seg"].get(x, [])])) <= 1, 1)))

# 未注釈フレームの正体
no_fp = {x for x in fids if not any(a["category_id"] <= 2 for a in A["hand_seg"].get(x, []))}
assert no_fp == set().union(*LM.values()), "loss_mask と「自分の手が写らないフレーム」が一致しない"
mg_only = {x for x, s_ in zip(fids, [frozenset(T[t] for t in f["labels"]) for f in frames]) if s_ <= {"Mouth Gag"}}
ts_none = {x for x in fids if not A["tool_seg"].get(x)}
assert ts_none <= mg_only, "tool_seg の未注釈に Mouth Gag 以外の術具 bbox があるフレームが含まれる"

# ---------- tool_seg と術具 bbox の対応 ----------
cls_stat = {n: dict(nb=0, ns=0, fb=0, fs=0, fboth=0, ious=[]) for n in TS_NAMES}
ph_match = np.zeros((nP, 2), int)  # 工程ごとの [対応のついた bbox 数, bbox 数]（tool_seg のあるフレーム）
for i, f in enumerate(frames):
    bx = collections.defaultdict(list)
    for lab, b in zip(f["labels"], f["boxes"]):
        bx[T[lab]].append(b)
    sg = collections.defaultdict(list)
    for a in A["tool_seg"].get(f["fid"], []):
        sg[TSN[a["category_id"]]].append(a["bbox"])
    for n in set(bx) | set(sg):
        st = cls_stat[n]
        st["nb"] += len(bx[n])
        st["ns"] += len(sg[n])
        st["fb"] += bool(bx[n])
        st["fs"] += bool(sg[n])
        st["fboth"] += bool(bx[n]) and bool(sg[n])
        if bx[n] and sg[n]:
            mt = greedy([[box_iou(b, s_) for s_ in sg[n]] for b in bx[n]])
            st["ious"] += mt
            if has["tool_seg"][i]:
                ph_match[ph[i], 0] += len(mt)
    if has["tool_seg"][i]:
        ph_match[ph[i], 1] += sum(len(v) for v in bx.values())

# ---------- マスクの面積と、手と術具の重なり ----------
WH = 1920 * 1080
hand_cov = {}  # fid -> (全手, 自分, 他者) の画素の割合
unions = {}
for x in fids:
    hs = A["hand_seg"].get(x, [])
    if not hs:
        continue
    u = {}
    for key, ids in [("all", (1, 2, 3, 4)), ("own", (1, 2)), ("oth", (3, 4))]:
        r = [a["segmentation"] for a in hs if a["category_id"] in ids]
        u[key] = M.merge(r) if r else None
    unions[x] = u
    hand_cov[x] = tuple(float(M.area(u[k_])) / WH if u[k_] else 0.0 for k_ in ["all", "own", "oth"])
held_ts = {id(r["ts"]) for v in held.values() for r in v if r["ts"] is not None}
tool_touch = []  # (母集団の行番号, クラス, 自分の手に接する, 他者の手に接する, 把持)
for i, x in enumerate(fids):
    for a in A["tool_seg"].get(x, []):
        u = unions.get(x, {})
        to = bool(u.get("own")) and M.area(M.merge([a["segmentation"], u["own"]], intersect=True)) > 0
        tt = bool(u.get("oth")) and M.area(M.merge([a["segmentation"], u["oth"]], intersect=True)) > 0
        tool_touch.append((i, TSN[a["category_id"]], bool(to), bool(tt), id(a) in held_ts))

# ---------- フレームごとの集合 ----------
vis_bbox = [frozenset(T[t] for t in f["labels"]) for f in frames]
vis_seg = [frozenset(TSN[a["category_id"]] for a in A["tool_seg"].get(x, [])) for x in fids]
held_set = [frozenset((r["side"], r["cls"] or "不明") for r in held.get(x, [])) for x in fids]
held_cls = [frozenset(r["cls"] or "不明" for r in held.get(x, [])) for x in fids]
held_sides = [tuple(any(r["side"] == s for r in held.get(x, [])) for s in SIDES) for x in fids]
fp_state = [tuple(c in fp.get(x, {}) for c in (1, 2)) for x in fids]
hand_state = [tuple(any(a["category_id"] == c for a in A["hand_seg"].get(x, [])) for c in (1, 2, 3, 4)) for x in fids]

# =====================================================================
D = Doc()
w, h = D.w, D.h
n_csv15 = len({r["clip"] for r in csv_rows})
uni = set().union(*[H_[k][fn]["imgs"] for k in TYPES for fn in FILES])
n_disk = sum(len(os.listdir(p)) for p in glob.glob(f"{FRAMES}/*")) if os.path.isdir(FRAMES) else None
csv_fids_all = {r["fid"] for r in csv_all}
csv15 = {r["fid"] for r in csv_rows}
phase_only = csv15 - fset  # 工程 CSV にあって術具 bbox の無いフレーム
assert not phase_only & uni and csv15 & uni <= fset
tool_nohts = fset - uni  # 術具 bbox はあるが HTS の注釈が一つも無いフレーム
all3 = has["hand_seg"] & has["tool_seg"] & has["hand_tool_seg"]

h(2, "0", "母集団・入力・注釈どうしの構造")
h(3, "0.1", "入力と結合")
w(table(["データ", "ファイル", "中身"], [
    ["hand_seg", "`data/annotations/egosurgery_hts/hand_seg/{train,val,test,extra}.json`", "手 4 クラスのインスタンスマスク（RLE）"],
    ["tool_seg", "`data/annotations/egosurgery_hts/tool_seg/{train,val,test,extra}.json`", "術具 31 クラスのインスタンスマスク（RLE）"],
    ["hand_tool_seg", "`data/annotations/egosurgery_hts/hand_tool_seg/{train,val,test,extra}.json` と `loss_mask/`",
     "自分の左手・右手と、左手・右手・両手で持っている術具のマスク（5 クラス、RLE）"],
    ["工程", "`data/annotations/egosurgery_phase/*.csv`（動画 01〜15 の " + f"{n_csv15} 本）", "フレームごとの工程"],
    ["術具 bbox", "`data/processed/joint_manifest/{train,val,test}.json`", "術具 15 クラス（Tool15）の box。先行 EDA と同じ"],
    ["HTS の元の注釈", "`data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/*/annotations.json`",
     "38 クラスの矩形。把持術具のクラスを決める最後の段だけに使う（§0.3）"],
], ["l", "l", "l"]))
w("")
w("- 結合はすべてフレーム ID（ファイル名から拡張子を除いたもの、例 `01_1_0124`）で行う。HTS の train / val / test の各ファイルの画像は、"
  "術具 bbox の同じ split の画像に含まれる（検査済み）")
w(f"- 先行 EDA（術具・工程・手、動画 01〜15）は [`{MAIN}`]({MAIN})。本書の工程・術具 bbox の母集団はそれと同じ\n")

h(3, "0.2", "母集団の層")
x_phase = {k: len(X[k]["imgs"] & csv_fids_all) for k in TYPES}
rr = [
    ["元のフレーム画像（`01_frames/initial_videos/`、動画 01〜15）", f"{n_disk:,}" if n_disk else "—", "参考"],
    ["HTS の注釈があるフレーム（3 種 × 4 ファイルの和集合）", f"{len(uni):,}", "クリップ 03_3 を含まない"],
    ["工程 CSV の行（動画 01〜15）", f"{len(csv_rows):,}", ""],
    ["　うち術具 bbox が無い（工程だけ）", f"{len(phase_only):,}", "**HTS の注釈も 1 件も無い**"],
    ["　**うち術具 bbox がある（主な母集団）**", f"**{N:,}**", "工程・術具 bbox・HTS を突き合わせられるのはここだけ"],
    ["　　うち 3 種とも未注釈", f"{len(tool_nohts):,}", ""],
]
for k in TYPES:
    rr.append([f"　　うち {k} の注釈がある", f"{has[k].sum():,}（{pct(has[k].mean())}%）", ""])
rr.append(["　　うち 3 種すべての注釈がある", f"{all3.sum():,}（{pct(all3.mean())}%）", ""])
for k in TYPES:
    rr.append([f"HTS の extra（{k}）", f"{len(X[k]['imgs']):,}", f"術具 bbox の split に属さない。工程 CSV にあるもの {x_phase[k]}"])
w(table(["集合", "フレーム", "備考"], rr, ["l", "r", "l"]))
w("")
w(f"- **HTS の注釈のうち工程ラベルを持つのは、術具 bbox のあるフレームの分だけ**（{len(csv15 & uni):,} フレーム）。"
  "工程 CSV だけのフレームと extra のフレームには、それぞれ HTS と工程ラベルが無い")
pv = collections.Counter(r["phase"] for r in csv_rows if r["fid"] in phase_only)
w(f"- 工程だけのフレーム {len(phase_only):,} の工程の内訳: " + "、".join(f"{p} {pv[p]}" for p in CAN if pv[p])
  + f"。disinfection は工程 CSV の {sum(1 for r in csv_rows if r['phase'] == 'disinfection')} 行のうち {pv['disinfection']} 行に HTS が無い")
w("- extra のフレームは工程ラベルを持たないので、本書の工程の分析には入らない。canonical の README は extra を学習に混ぜると"
  "術具 bbox の split へのリーク源になりうると注意している（`data/annotations/egosurgery_hts/hand_tool_seg/README.md` §8）")
vids_hts = sorted({x.split("_")[0] for x in uni})
w(f"- HTS の動画は {vids_hts[0]}〜{vids_hts[-1]} の {len(vids_hts)} 本で、動画 17〜21 は含まない\n")

h(3, "0.3", "注釈どうしの構造（実測）")
n_link = src_cnt["tool_seg"] + src_cnt["bbox"] + src_cnt["master"]
same14 = all(cls_stat[n]["nb"] == cls_stat[n]["ns"] and cls_stat[n]["fb"] == cls_stat[n]["fs"] == cls_stat[n]["fboth"]
             for n in T if n != "Mouth Gag")
nm14 = sum(len(cls_stat[n]["ious"]) for n in T if n != "Mouth Gag")
nb14 = sum(cls_stat[n]["nb"] for n in T if n != "Mouth Gag")
lnk_mg = sum(1 for v in held.values() for r in v if r["src"] == "bbox" and r["cls"] == "Mouth Gag")
w(table(["関係", "結果"], [
    ["hand_seg の手 box と raw02（先行 EDA §4 の手）", f"フレームごとのクラスと box が {hs_raw_same:,}/{N:,} フレームで一致"],
    ["hand_tool_seg の自分の手マスクと hand_seg の自分の手マスク", f"{ht_fp_same:,}/{len(A['hand_tool_seg']):,} フレームでマスク（RLE）まで同一"],
    ["hand_tool_seg に他者の手", "クラスが無い（自分の手と、自分の手が持つ術具だけ）"],
    ["tool_seg の Tool15 部分と術具 bbox", ("Mouth Gag 以外の 14 クラスで、クラスごとのインスタンス数・写るフレームが術具 bbox と**完全に同じ**"
                                           if same14 else "Mouth Gag 以外でもクラスごとの件数が違う")
     + f"。同じクラスどうし box IoU ≥ 0.5 で対応がつくのは {nm14:,}/{nb14:,}（{pct(nm14 / nb14)}%）。Mouth Gag は tool_seg に 0 件（{ref('2')}）"],
    ["tool_seg が未注釈のフレーム", f"{len(ts_none)} フレーム。すべて術具 bbox の術具が Mouth Gag だけか 0 個のフレーム（{ref('2.2')}）"],
    ["hand_tool_seg が未注釈のフレーム（loss_mask）", f"{len(no_fp)} フレーム。**hand_seg で自分の手が写らないフレームと完全に一致**（{ref('3.2')}）"],
    ["把持術具のマスク（左手・右手・両手で持つ術具）", f"{n_held:,} 個"],
    ["　tool_seg のマスクと RLE まで同一", f"{src_cnt['tool_seg']:,}（{pct(src_cnt['tool_seg'] / n_held)}%）→ tool_seg のクラスを使う"],
    ["　同一ではないが術具 bbox と box IoU ≥ 0.5", f"{src_cnt['bbox']:,}（{pct(src_cnt['bbox'] / n_held)}%）→ 術具 bbox のクラスを使う。"
     f"うち Mouth Gag {lnk_mg:,}"],
    ["　どちらでもないが HTS の元の注釈（38 クラス）と box IoU ≥ 0.5", f"{src_cnt['master']:,}（{pct(src_cnt['master'] / n_held)}%）→ 元の注釈のクラスを使う。"
     + "、".join(f"{n} {k:,}" for n, k in mc(collections.Counter(r["cls"] for v in held.values() for r in v if r["src"] == "master"), 3))],
    ["　どれとも対応がつかない", f"{src_cnt['none']:,}（{pct(src_cnt['none'] / n_held)}%）→ 「不明」"],
    ["　同一ではない把持術具マスクの、同じフレームの tool_seg マスクとの IoU の最大値",
     f"中央値 {np.median(link_best_ts):.3f}（{len(link_best_ts):,} 個。tool_seg に同じ術具が無い）" if link_best_ts else "—"],
    [f"左手・右手の把持術具（tool_seg と同一の {der['n']:,} 個）は、同じ側の自分の手と", ""],
    ["　box の IoU が最大の tool_seg インスタンス", f"{der['box']:,}（{pct(der['box'] / der['n'])}%）"],
    ["　マスクの IoU が最大の tool_seg インスタンス", f"{der['mask']:,}（{pct(der['mask'] / der['n'])}%）"],
    ["　マスクが 1 画素も重ならない", f"{der['zero']:,}（{pct(der['zero'] / der['n'])}%）"],
    ["`bbox` 欄 = マスクの外接矩形（1 px 以内）", f"hand_seg {pct(hs_bbox_eq)}%、tool_seg {pct(bbox_eq)}%。tool_seg の `area` 欄 = マスクの画素数: {pct(area_eq)}%"],
    ["画像として載るが注釈が 0 件のフレーム", "、".join(f"{k} {sum(zero_img[k].values())}" for k in TYPES)
     + "（載っている画像 = 注釈のある画像）"],
], ["l", "l"]))
w("")
w("- **由来**: HTS のマスクは術具・手の box を SAM のプロンプトにして作られている（EgoSurgery-HTS 論文 arXiv:2503.18755。"
  "`docs/experiment_log.md` 2026-07-29）。把持術具は論文では「手のセグメンテーションとの IoU が最大の術具」とされる")
w(f"- **実データでは、把持術具は同じ側の手と box の IoU が最大の術具とほぼ一致し（{pct(der['box'] / der['n'])}%）、"
  f"マスクの IoU が最大の術具とは {pct(der['mask'] / der['n'])}% しか一致しない。把持術具の {pct(der['zero'] / der['n'])}% は手のマスクと画素で重ならない。**"
  "hand_tool_seg の「把持」は手と術具の box の重なりから決まった量として読む。手と術具のマスクは物体ごとに描かれ、"
  "接していても境界で重ならないことがあるので、マスクが重ならないことは「触れていない」ことを意味しない")
w(f"- 以降、把持術具のクラスは上の 4 段（tool_seg と同一 → 術具 bbox と対応 → 元の注釈と対応 → 不明）で決める。対応がついたのは {pct(n_link / n_held)}%。"
  "tool_seg に 0 件の Mouth Gag と Suture, Suture Needle も、この段で把持術具として現れる\n")

h(3, "0.4", "用語と記号")
w(table(["記号", "意味"], [
    ["注釈がある", "その種類の注釈が 1 件以上あるフレーム。HTS の JSON は注釈のある画像だけを載せる（§0.3）ので、無いフレームは「未注釈」で、"
     "「写っていない」とは区別できない"],
    ["把持術具", "hand_tool_seg の Left Hand Tool（左）・Right Hand Tool（右）・Two Hands Tool（両手）。いずれも自分（カメラを着けた術者）の手"],
    ["Tool15", "術具 bbox の 15 クラス。tool_seg の 31 クラスは Tool15 の 15 クラスをすべて含み、ほかに 16 クラスを持つ（Tool15 外）"],
    ["在率", "そのフレーム集合のうち、そのクラスが 1 つ以上あるフレームの割合"],
    ["†", f"術具 bbox のあるフレームが 200 未満の工程（{', '.join(CAN[j] + f' {ph_n[j]}' for j in sorted(SMALL))}）。割合は不安定"],
    ["群", "`context/conventions.md#det_groups` の標的群・陰性対照群（Tool15 のみ）"],
    ["参照順・略号", " → ".join(f"{p}（{AB[p]}）" for p in CAN) + "。工程の列はこの順"],
], ["l", "l"]))
w("")

# ---------- §1 規模 ----------
h(2, "1", "3 種の注釈の規模")
h(3, "1.1", "ファイルごとの件数")
rr = []
for k in TYPES:
    for fn in FILES:
        rr.append([k if fn == "train" else "", fn, f"{len(H_[k][fn]['ann']):,}", f"{H_[k][fn]['n_ann']:,}"]
                  + ([f"{len(LM[fn])}"] if k == "hand_tool_seg" and fn in LM else ["—"]))
w(table(["種類", "ファイル", "注釈のあるフレーム", "インスタンス", "loss_mask のフレーム"], rr, ["l", "l", "r", "r", "r"]))
w("")
lm_eq = all(LM[s] == ({f["fid"] for f in frames if f["split"] == s} - set(H_["hand_tool_seg"][s]["ann"])) for s in SPLITS)
w("- loss_mask のフレームは、術具 bbox のあるフレームのうち hand_tool_seg の注釈が無いフレームと"
  + ("**全 split で一致**する" if lm_eq else "**一致しない**") + "\n")

h(3, "1.2", "hand_seg：クラスごとの件数とマスクの大きさ")
rr = []
for c in range(1, 5):
    ar = np.array([a["area"] / WH for x in fids for a in A["hand_seg"].get(x, []) if a["category_id"] == c])
    nf = sum(any(a["category_id"] == c for a in A["hand_seg"].get(x, [])) for x in fids)
    rr.append([HN[c - 1], f"{len(ar):,}", f"{nf:,}", pct(nf / N), f"{100 * np.median(ar):.2f}",
               f"{100 * np.percentile(ar, 25):.2f}–{100 * np.percentile(ar, 75):.2f}",
               f"{sum(a['category_id'] == c for v in X['hand_seg']['ann'].values() for a in v):,}"])
w(table(["クラス", "インスタンス", "写るフレーム", "在率 %", "マスク面積の中央値 %", "四分位範囲 %", "extra のインスタンス"], rr))
w("")
w(f"- 母集団 {N:,} フレームでの値。面積は画像（1920×1080）に対する % 。手の在否の工程別の表は先行 EDA [§4.2]({MAIN}#s4-2)\n")

h(3, "1.3", "tool_seg：31 クラスの件数とマスクの大きさ")
ts_inst = collections.Counter(TSN[a["category_id"]] for x in fids for a in A["tool_seg"].get(x, []))
ts_fr = collections.Counter(n for s_ in vis_seg for n in s_)
ts_area = collections.defaultdict(list)
for a in ts_all:
    ts_area[TSN[a["category_id"]]].append(a["area"] / WH)
ts_x = collections.Counter(TSN[a["category_id"]] for v in X["tool_seg"]["ann"].values() for a in v)
ts_vid = {n: len({vid[i] for i in range(N) if n in vis_seg[i]}) for n in TS_NAMES}
TSO = sorted(TS_NAMES, key=lambda n: (n not in T, -ts_inst[n], n))
rr = [[n, grp(n), f"{ts_inst[n]:,}", f"{ts_fr[n]:,}", f"{ts_vid[n]}/15",
       f"{100 * np.median(ts_area[n]):.2f}" if ts_area[n] else "—", f"{ts_x[n]:,}",
       f"{cls_stat[n]['nb']:,}" if n in T else "—"] for n in TSO]
w(table(["クラス", "群", "インスタンス", "写るフレーム", "出現動画", "マスク面積の中央値 %", "extra のインスタンス", "術具 bbox の box"], rr))
w("")
zero_ts = [n for n in TS_NAMES if ts_inst[n] == 0 and ts_x[n] == 0]
w(f"- 上は Tool15 の 15 クラス（box の多い順でなく tool_seg のインスタンスの多い順）、下は Tool15 外の {len(TS_NAMES) - 15} クラス")
w(f"- **注釈が 1 件も無いクラス**: {'、'.join(zero_ts)}。Mouth Gag は術具 bbox では {cls_stat['Mouth Gag']['nb']:,} box ある"
  "（陰性対照群の 1 つが tool_seg には無い）\n")

h(3, "1.4", "hand_tool_seg：把持術具の数")
cnt_side = collections.Counter(r["side"] for v in held.values() for r in v)
per_frame = collections.Counter(len(held.get(x, [])) for x in A["hand_tool_seg"])
rr = [[k, f"{per_frame[k]:,}", pct(per_frame[k] / len(A['hand_tool_seg']))] for k in sorted(per_frame)]
w(table(["1 フレームの把持術具の数", "フレーム", "%"], rr))
w("")
side_multi = collections.Counter(s for v in held.values() for s, n in collections.Counter(r["side"] for r in v).items() if n > 1)
w(f"- 把持術具 {n_held:,} 個の内訳: " + "、".join(f"{s} {cnt_side[s]:,}" for s in SIDES)
  + "。同じ側で 2 つ以上を持つフレーム: " + ("、".join(f"{s} {n}" for s, n in side_multi.items()) or "なし")
  + f"。同じ側の自分の手が 2 つあるフレーム: {n_fp_multi}")
w(f"- 分母は hand_tool_seg の注釈がある {len(A['hand_tool_seg']):,} フレーム\n")

# ---------- §2 tool_seg と術具 bbox ----------
h(2, "2", "tool_seg と術具 bbox の対応")
w(f"母集団: 術具 bbox のある {N:,} フレーム。tool_seg の各インスタンスの外接矩形と術具 bbox の box を、同じクラスどうし IoU の大きい順に 1 対 1 で"
  "対応づける（IoU ≥ 0.5）\n")
h(3, "2.1", "クラスごとの対応")
rr = []
for n in sorted(T, key=lambda n: -cls_stat[n]["nb"]):
    st = cls_stat[n]
    rr.append([n, grp(n), f"{st['nb']:,}", f"{st['ns']:,}", f"{st['fb']:,}", f"{st['fs']:,}", f"{len(st['ious']):,}",
               rate(len(st["ious"]), st["nb"]), f"{np.median(st['ious']):.3f}" if st["ious"] else "—"])
rr.append(["**計（Mouth Gag を除く）**", "", f"{nb14:,}", f"{sum(cls_stat[n]['ns'] for n in T if n != 'Mouth Gag'):,}", "", "",
           f"{nm14:,}", rate(nm14, nb14), f"{np.median([v for n in T for v in cls_stat[n]['ious']]):.3f}"])
w(table(["クラス", "群", "術具 bbox の box", "tool_seg のインスタンス", "bbox のあるフレーム", "tool_seg のあるフレーム",
         "対応のついた組", "box のうち対応あり %", "対応の IoU の中央値"], rr))
w("")
w("- **Mouth Gag 以外の 14 クラスは、インスタンス数も写るフレームも術具 bbox と同じ**（tool_seg の Tool15 部分は術具 bbox の box ごとにマスクを付けたものと読める）。"
  "Mouth Gag だけが tool_seg に 1 件も無い")
w("- 件数が同じでも IoU ≥ 0.5 で対応がつかない box がある。対応の IoU の中央値も 1 にならず、tool_seg の外接矩形は元の box とは一致しない\n")

h(3, "2.2", "tool_seg の未注釈フレーム")
gap_ts = ~has["tool_seg"]
nbx = np.array([len(s_) for s_ in vis_bbox])
rr = []
for v in videos:
    m = vid == v
    rr.append([v, f"{m.sum():,}", f"{(m & gap_ts).sum():,}", pct((m & gap_ts).sum() / m.sum()), f"{(m & gap_ts & (nbx > 0)).sum():,}"])
rr.append(["**計**", f"{N:,}", f"{gap_ts.sum():,}", pct(gap_ts.mean()), f"{(gap_ts & (nbx > 0)).sum():,}"])
D.details(f"動画ごとの tool_seg 未注釈フレーム（{gap_ts.sum():,} フレーム）",
          table(["動画", "フレーム", "tool_seg 未注釈", "%", "うち術具 bbox の Mouth Gag が写る"], rr))
mg_extra = mg_only - ts_none
assert all(TSN[a["category_id"]] not in T for x in mg_extra for a in A["tool_seg"][x])
w(f"- tool_seg が未注釈の {len(ts_none)} フレームは、術具 bbox の術具が **Mouth Gag だけ**のフレーム {(gap_ts & (nbx > 0)).sum()} と、"
  f"術具 bbox が 0 個のフレーム {(gap_ts & (nbx == 0)).sum()} でできている。Mouth Gag は tool_seg に無いクラスなので、"
  "注釈が漏れたのではなく tool_seg に描くものが無いフレームである")
w(f"- 術具 bbox が Mouth Gag だけか 0 個のフレームは {len(mg_only)} あり、残りの {len(mg_extra)} には Tool15 外のクラスだけが tool_seg にある")
w("- 動画 05 の未注釈が多いのは、Mouth Gag だけが写るフレームが多いため（表の右端の列）\n")

# ---------- §3 工程との関係 ----------
h(2, "3", "工程との関係")
w(f"母集団: 術具 bbox のある {N:,} フレーム（工程ラベルは全フレームにある）。工程の列は参照順\n")
h(3, "3.1", "工程ごとの被覆")
cov_all = collections.Counter(r["phase"] for r in csv_rows)
rr = []
for j in range(nP):
    m = ph == j
    rr.append([phn(j), f"{cov_all[CAN[j]]:,}", f"{m.sum():,}", pct(m.sum() / cov_all[CAN[j]])]
              + [pct((m & has[k]).sum() / cov_all[CAN[j]]) for k in TYPES] + [pct((m & all3).sum() / cov_all[CAN[j]])])
rr.append(["**計**", f"{len(csv_rows):,}", f"{N:,}", pct(N / len(csv_rows))]
          + [pct(has[k].sum() / len(csv_rows)) for k in TYPES] + [pct(all3.sum() / len(csv_rows))])
w("工程 CSV の行に対する割合 %\n")
w(table(["工程", "工程 CSV の行", "術具 bbox のフレーム", "術具 bbox %", "hand_seg %", "tool_seg %", "hand_tool_seg %", "3 種すべて %"], rr))
w("")
low = sorted(range(nP), key=lambda j: (ph == j).sum() / cov_all[CAN[j]])[:3]
w(f"- HTS の被覆は術具 bbox の被覆を超えない（HTS は術具 bbox のあるフレームにしか付かない。{ref('0.2')}）。"
  f"被覆の低い工程は {'、'.join(f'{CAN[j]}（術具 bbox {pct((ph == j).sum() / cov_all[CAN[j]])}%）' for j in low)}")
w(f"- 術具 bbox のあるフレームを分母にした値は {ref('3.2')}\n")

h(3, "3.2", "工程ごとの欠け（術具 bbox のあるフレームを分母に）")
rr = []
for j in range(nP):
    m = ph == j
    rr.append([phn(j), f"{m.sum():,}", f"{(m & ~has['hand_seg']).sum():,}", f"{(m & ~has['tool_seg']).sum():,}",
               rate((m & ~has["tool_seg"]).sum(), m.sum()), f"{(m & lm).sum():,}", rate((m & lm).sum(), m.sum()),
               rate(ph_match[j, 0], ph_match[j, 1])])
rr.append(["**計**", f"{N:,}", f"{(~has['hand_seg']).sum():,}", f"{(~has['tool_seg']).sum():,}", pct((~has['tool_seg']).mean()),
           f"{lm.sum():,}", pct(lm.mean()), rate(ph_match[:, 0].sum(), ph_match[:, 1].sum())])
w(table(["工程", "フレーム", "hand_seg 未注釈", "tool_seg 未注釈", "%", "hand_tool_seg 未注釈（loss_mask）", "%",
         "tool_seg のあるフレームで術具 bbox の box に対応がある %"], rr))
w("")
lm_sets = collections.Counter(vis_bbox[i] for i in np.where(lm)[0])
lm_only = sum(n for s_, n in lm_sets.items() if s_ <= {"Mouth Gag", "Skewer"})
top_ts_gap = sorted(range(nP), key=lambda j: -(((ph == j) & ~has["tool_seg"]).sum() / max(1, (ph == j).sum())))[:3]
w(f"- **hand_tool_seg の未注釈（loss_mask）{lm.sum()} フレームは、hand_seg で自分の手が写らないフレームと完全に一致する**。"
  "hand_tool_seg は自分の手とその手が持つ術具でできているので、自分の手が写らなければ注釈は作られない")
w(f"- README（`hand_tool_seg/README.md` §4・§8）はこの欠落を「Mouth Gag / Skewer を含むフレームの構造的な除外」と説明しているが、"
  f"loss_mask のうち術具 bbox の術具が Mouth Gag・Skewer だけ（または 0 個）のフレームは {lm_only}（{pct(lm_only / lm.sum())}%）にとどまる。"
  "上位の組み合わせ: " + "、".join(f"{' + '.join(sorted(s_)) or '（術具なし）'} {n}" for s_, n in lm_sets.most_common(4)))
w(f"- tool_seg の未注釈（術具 bbox が Mouth Gag だけか 0 個のフレーム、{ref('2.2')}）の割合が高い工程: "
  + "、".join(f"{CAN[j]} {rate(((ph == j) & ~has['tool_seg']).sum(), (ph == j).sum())}%" for j in top_ts_gap)
  + "。disinfection の術具 bbox のあるフレームは術具が 0 個")
w("- 右端の列は、tool_seg のあるフレームで、術具 bbox の box（Mouth Gag を含む全クラス）のうち同じクラスの tool_seg インスタンスと対応がつく割合。"
  "Mouth Gag の多い工程ほど下がる\n")

h(3, "3.3", "tool_seg だけにあるクラス × 工程")
PFs = {n: np.array([sum(1 for i in np.where(ph == j)[0] if n in vis_seg[i]) for j in range(nP)]) for n in TS_NAMES}
m_ts = has["tool_seg"]
nts = np.array([(m_ts & (ph == j)).sum() for j in range(nP)])
EXT = sorted([n for n in TS_NAMES if n not in T and PFs[n].sum()], key=lambda n: (int(PFs[n].argmax()), -PFs[n].max() / PFs[n].sum()))
rr = []
for n in EXT:
    j0 = int(PFs[n].argmax())
    rr.append([n, f"{PFs[n].sum():,}", f"{ts_vid[n]}/15"] + [pct(PFs[n][j] / PFs[n].sum()) for j in range(nP)]
              + [f"{phn(j0)} {rate(PFs[n][j0], nts[j0])}", f"{2 ** H(PFs[n]):.2f}"])
w(f"Tool15 外で母集団に現れる {len(EXT)} クラス。P(工程 | クラス)（写るフレーム基準、行で 100%）\n")
w(table(["クラス", "写るフレーム", "出現動画"] + [phn(j) for j in range(nP)] + ["最頻工程での在率 %", "実効工程数 2^H"], rr))
w("")
ext_spec = [n for n in EXT if PFs[n].max() / PFs[n].sum() >= 0.9]
w("- 最頻工程での在率の分母は、その工程の tool_seg のあるフレーム。実効工程数 = 2 の（P(工程 | クラス) のエントロピー）乗")
w("- 90% 以上が 1 つの工程に集まるクラス: " + "、".join(f"{n} → {CAN[int(PFs[n].argmax())]}" for n in ext_spec)
  + "。ただし多くは 1〜3 動画にしか出ない（出現動画の列）")
w(f"- Tool15 の 14 クラスは写るフレームが術具 bbox と同じ（{ref('2.1')}）なので、P(工程 | 術具) と在率は先行 EDA の "
  f"[§3.1]({MAIN}#s3-1)・[§3.3]({MAIN}#s3-3) と同じになる")
mg = np.array([sum(1 for i in np.where(m_ts & (ph == j))[0] if "Mouth Gag" in vis_bbox[i]) for j in range(nP)])
w("- Mouth Gag は術具 bbox では " + "、".join(f"{CAN[j]} {rate(mg[j], nts[j])}%" for j in range(nP) if nts[j] and mg[j] / nts[j] >= 0.3)
  + " のフレームに写る（分母は tool_seg のあるフレーム）が、tool_seg には 1 件も無い\n")

h(3, "3.4", "手のマスクの面積 × 工程")
rr = []
for j in range(nP):
    xs = [hand_cov[fids[i]] for i in np.where(ph == j)[0] if fids[i] in hand_cov]
    a_ = np.array(xs) if xs else np.zeros((0, 3))
    rr.append([phn(j), f"{len(xs):,}"] + ([f"{100 * a_[:, 0].mean():.1f}", f"{100 * np.median(a_[:, 0]):.1f}",
                                            f"{100 * a_[:, 1].mean():.1f}", f"{100 * a_[:, 2].mean():.1f}"]
                                           if len(xs) else ["—"] * 4))
a_ = np.array(list(hand_cov.values()))
rr.append(["**全体**", f"{len(a_):,}", f"{100 * a_[:, 0].mean():.1f}", f"{100 * np.median(a_[:, 0]):.1f}",
           f"{100 * a_[:, 1].mean():.1f}", f"{100 * a_[:, 2].mean():.1f}"])
w(table(["工程", "hand_seg のあるフレーム", "手が覆う画素 % の平均", "同・中央値", "自分の手 % の平均", "他者の手 % の平均"], rr))
w("")
w("- 手が覆う画素 = そのフレームの手のマスクの和集合が画像（1920×1080）に占める割合\n")

h(3, "3.5", "把持 × 工程")
m_ht = has["hand_tool_seg"]
rr = []
for j in list(range(nP)) + [None]:
    idx = np.where(m_ht & ((ph == j) if j is not None else True))[0]
    if not len(idx):
        rr.append([phn(j), 0] + ["—"] * 8)
        continue
    sd = np.array([held_sides[i] for i in idx])
    assert all(any(fp_state[i]) for i in idx)  # hand_tool_seg のあるフレームには必ず自分の手がある
    nh = np.array([len(held[fids[i]]) for i in idx])
    busy = (sd[:, 0] & sd[:, 1]) | sd[:, 2]
    rr.append([phn(j) if j is not None else "**全体**", f"{len(idx):,}", pct((nh > 0).mean()), pct(sd[:, 0].mean()),
               pct(sd[:, 1].mean()), pct(sd[:, 2].mean()), pct(busy.mean()), pct((nh == 0).mean()), f"{nh.mean():.2f}",
               pct(np.mean([held_sides[i][1] and not held_sides[i][0] and not held_sides[i][2] for i in idx]))])
w("分母は hand_tool_seg のあるフレーム（工程ごと。どのフレームにも自分の手が写る）。各列はその状態のフレームの %\n")
w(table(["工程", "フレーム", "何かを持つ", "左手で持つ", "右手で持つ", "両手で持つ", "両手がふさがる", "何も持たない",
         "把持術具 / フレーム", "右手だけで持つ"], rr))
w("")
w("- 両手がふさがる = 左手と右手がそれぞれ何かを持つ、または両手で 1 つを持つ。右手だけで持つ = 右手で持ち、左手・両手では持たない")
w(f"- 「持つ」は box の重なりから決まった量（{ref('0.3')}）\n")

h(3, "3.6", "工程ごとに持たれている術具のクラス")
rr = []
for j in range(nP):
    idx = np.where(m_ht & (ph == j))[0]
    cells = []
    for s in SIDES:
        c = collections.Counter(r["cls"] or "不明" for i in idx for r in held[fids[i]] if r["side"] == s)
        cells.append("、".join(f"{n} {rate(k, len(idx))}" for n, k in c.most_common(3)) or "—")
    rr.append([phn(j), f"{len(idx):,}"] + cells)
w("工程ごとの上位 3 クラス。数字はその工程の hand_tool_seg のあるフレームのうち、その側でそのクラスを持つ割合 %（1 フレームで同じ側が 2 つ持つことがあるので"
  "延べ数）\n")
w(table(["工程", "フレーム", "左手", "右手", "両手"], rr, ["l", "r", "l", "l", "l"]))
w("")

h(3, "3.7", "術具のクラスごとの把持")
C_ = np.where(m_ht & m_ts)[0]
hc = collections.defaultdict(collections.Counter)  # クラス -> 側 -> 件数（全 hand_tool フレーム）
for x, recs in held.items():
    for r in recs:
        hc[r["cls"] or "不明"][r["side"]] += 1
rr = []
DOMSIDE = {}
HCO = sorted(hc, key=lambda n: -sum(hc[n].values()))
for n in HCO:
    tot_n = sum(hc[n].values())
    visf = [i for i in C_ if n in vis_seg[i]]
    heldf = sum(1 for i in visf if n in held_cls[i])
    vh = collections.defaultdict(collections.Counter)
    for x, recs in held.items():
        for r in recs:
            if (r["cls"] or "不明") == n:
                vh[x.split("_")[0]][r["side"]] += 1
    dom_side = collections.Counter(c.most_common(1)[0][0] for c in vh.values())
    DOMSIDE[n] = (dom_side, len(vh))
    rr.append([n, grp(n) if n != "不明" else "", f"{tot_n:,}"] + [pct(hc[n][s] / tot_n) for s in SIDES]
              + [f"{len(visf):,}" if n != "不明" else "—", rate(heldf, len(visf)) if n != "不明" else "—", len(vh),
                 " / ".join(f"{dom_side[s]}" for s in SIDES)])
w(f"左の 4 列は hand_tool_seg のある全フレーム、「写るフレーム」と「把持率」は hand_tool_seg と tool_seg の両方があるフレーム（{len(C_):,}）で数える\n")
w(table(["クラス", "群", "把持の件数", "左 %", "右 %", "両手 %", "写るフレーム（tool_seg）", "把持率 %", "把持のある動画",
         "主に左 / 右 / 両手で持つ動画の数"], rr))
w("")
w("- 把持率 = そのクラスが tool_seg で写るフレームのうち、同じフレームでそのクラスが持たれている割合")
w("- 主に〜で持つ動画の数 = 動画ごとに、そのクラスの把持の件数が最も多い側を数えたもの")
w("- Mouth Gag と Suture, Suture Needle は tool_seg に無いので、写るフレームと把持率は測れない（—）。把持の件数は §0.3 の 4 段のうち術具 bbox・元の注釈との対応による\n")
rr = []
for n in [n for n in HCO if n != "不明"][:15]:
    cells = []
    for j in range(nP):
        visf = [i for i in C_ if ph[i] == j and n in vis_seg[i]]
        cells.append(rate(sum(1 for i in visf if n in held_cls[i]), len(visf)) if visf else "·")
    rr.append([n] + cells)
D.details("把持率 × 工程（把持の多い上位 15 クラス。· はその工程で写らない）", table(["クラス"] + [phn(j) for j in range(nP)], rr))

h(3, "3.8", "工程との情報量（注釈のあいだの参考値）")
w(f"母集団: hand_tool_seg と tool_seg の両方があるフレーム {len(C_):,}。モデルの結果ではなく注釈のあいだの関係である。"
  "把持は手と術具の注釈から導かれた量（§0.3）なので、術具の集合と独立な情報ではない\n")
phC = ph[C_]
vC = vid[C_]
Hph = H(np.bincount(phC, minlength=nP))


def info(vals):
    tab = collections.defaultdict(collections.Counter)
    for v_, p_ in zip(vals, phC):
        tab[v_][p_] += 1
    hc_ = sum(sum(c.values()) / len(vals) * H(list(c.values())) for c in tab.values())
    pred = np.zeros(len(vals), int)
    for v in videos:
        tr = vC != v
        t2 = collections.defaultdict(collections.Counter)
        for k_ in np.where(tr)[0]:
            t2[vals[k_]][phC[k_]] += 1
        maj = collections.Counter(phC[tr]).most_common(1)[0][0]
        for k_ in np.where(~tr)[0]:
            pred[k_] = t2[vals[k_]].most_common(1)[0][0] if vals[k_] in t2 else maj
    return len(tab), Hph - hc_, float((pred == phC).mean())


VARS = [
    ("自分・他者の手の在否（hand_seg、4 クラスの有無）", [hand_state[i] for i in C_]),
    ("把持の状態（左・右・両手のそれぞれで持つか）", [held_sides[i] for i in C_]),
    ("持たれている術具のクラスの集合（側を区別しない）", [held_cls[i] for i in C_]),
    ("持たれている術具の（側, クラス）の集合", [held_set[i] for i in C_]),
    ("写っている術具の集合（術具 bbox、Tool15）", [vis_bbox[i] for i in C_]),
    ("写っている術具の集合（tool_seg、31 クラス）", [vis_seg[i] for i in C_]),
    ("術具 bbox の集合 + 把持の（側, クラス）の集合", [(vis_bbox[i], held_set[i]) for i in C_]),
]
INFO = {}
rr = []
for name, vals in VARS:
    k_, I_, acc = info(vals)
    INFO[name] = (k_, I_, acc)
    rr.append([name, f"{k_:,}", f"{I_:.3f}", pct(I_ / Hph), pct(acc)])
maj = collections.Counter(phC).most_common(1)[0]
rr.append([f"（基準）常に最多工程（{CAN[maj[0]]}）", "1", "0", "0", pct(maj[1] / len(C_))])
w(table(["変数", "値の種類", "I(工程; 変数) [bit]", "I / H(工程) %", "動画一つ抜きの frame accuracy %"], rr, ["l", "r", "r", "r", "r"]))
w("")
w(f"- H(工程) = {Hph:.3f} bit。I は平滑化なしの plug-in 推定で、値の種類が多い変数ほど上振れする。種類数の違う変数どうしは右端の列で比べる")
w("- 動画一つ抜き = 1 動画を除いた 14 動画で「変数の値ごとの最多工程」を数え、除いた動画に当てはめる（未見の値は最多工程で埋める）。"
  f"先行 EDA [§3.10]({MAIN}#s3-10) と同じ規則\n")

h(3, "3.9", "工程の切り替わりと把持の変化")
order = sorted(np.where(m_ht)[0], key=lambda i: (frames[i]["clip"], csv_pos[fids[i]]))
adj = [(a, b) for a, b in zip(order, order[1:])
       if frames[a]["clip"] == frames[b]["clip"] and csv_pos[fids[b]] - csv_pos[fids[a]] == 1]
chg_p = np.array([ph[a] != ph[b] for a, b in adj])
chg_h = np.array([held_set[a] != held_set[b] for a, b in adj])
chg_v = np.array([vis_bbox[a] != vis_bbox[b] for a, b in adj])
w(table(["隣接フレームの対", "対の数", "把持の（側, クラス）集合が変わる %", "術具 bbox の集合が変わる %"],
        [[name, f"{m.sum():,}", pct((m & chg_h).sum() / m.sum()), pct((m & chg_v).sum() / m.sum())]
         for name, m in [("工程が変わる", chg_p), ("工程が同じ", ~chg_p)]]))
w("")
w("- 隣接 = 同じクリップの工程 CSV で連続する 2 行が、どちらも hand_tool_seg を持つ対\n")
pc = collections.Counter((ph[a], ph[b]) for (a, b), c in zip(adj, chg_p) if c)
rr = []
TRX = {}
for (pa, pb), c in pc.most_common(10):
    ap = [(a, b) for (a, b), cp in zip(adj, chg_p) if cp and ph[a] == pa and ph[b] == pb]
    ins = collections.Counter(t for a, b in ap for t in held_set[b] - held_set[a])
    out = collections.Counter(t for a, b in ap for t in held_set[a] - held_set[b])
    TRX[(pa, pb)] = (ins, out)
    rr.append([f"{CAN[pa]} → {CAN[pb]}", c, pct(sum(held_set[a] != held_set[b] for a, b in ap) / c),
               "、".join(f"{s}:{n}({k})" for (s, n), k in mc(ins, 3)) or "—",
               "、".join(f"{s}:{n}({k})" for (s, n), k in mc(out, 3)) or "—"])
w("工程の切り替わりの多い順（上位 10）\n")
w(table(["工程の切り替わり", "対の数", "把持が変わる %", "持ち始める（側:クラス、回数）", "手放す（側:クラス、回数）"], rr,
        ["l", "r", "r", "l", "l"]))
w("")

h(3, "3.10", "手術の進行度と把持")
bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0001]
bl = ["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"]
bi = np.digitize(np.array([prog[x] for x in fids]), bins) - 1
rr = []
for b in range(5):
    idx = np.where(m_ht & (bi == b))[0]
    sd = np.array([held_sides[i] for i in idx])
    rc = collections.Counter(r["cls"] or "不明" for i in idx for r in held[fids[i]] if r["side"] == "右")
    lc = collections.Counter(r["cls"] or "不明" for i in idx for r in held[fids[i]] if r["side"] == "左")
    rr.append([bl[b], f"{len(idx):,}", pct(sd.any(1).mean()), pct(sd[:, 0].mean()), pct(sd[:, 1].mean()), pct(sd[:, 2].mean()),
               "、".join(f"{n} {rate(k, len(idx))}" for n, k in rc.most_common(2)),
               "、".join(f"{n} {rate(k, len(idx))}" for n, k in lc.most_common(2))])
w(table(["進行度", "フレーム", "何かを持つ %", "左手 %", "右手 %", "両手 %", "右手の上位 2（%）", "左手の上位 2（%）"], rr,
        ["l", "r", "r", "r", "r", "r", "l", "l"]))
w("")
w("- 進行度 = 動画ごとに工程 CSV の全行を時系列に並べた順位を 0〜1 に正規化した値（先行 EDA と同じ）。分母は hand_tool_seg のあるフレーム\n")

h(3, "3.11", "術具のマスクと手のマスクの重なり × 工程")
rr = []
for j in list(range(nP)) + [None]:
    sel = [r for r in tool_touch if j is None or ph[r[0]] == j]
    if not sel:
        rr.append([phn(j), 0] + ["—"] * 6)
        continue
    o = np.array([r[2] for r in sel])
    t_ = np.array([r[3] for r in sel])
    hd = np.array([r[4] for r in sel])
    rr.append([phn(j) if j is not None else "**全体**", f"{len(sel):,}", pct((o | t_).mean()), pct(o.mean()), pct(t_.mean()),
               pct(hd.mean()), rate((o & hd).sum(), hd.sum()), pct((o & ~hd).mean())])
w(table(["工程", "tool_seg のインスタンス", "手と重なる %", "自分の手と重なる %", "他者の手と重なる %", "把持術具である %",
         "把持術具のうち自分の手と重なる %", "自分の手と重なるが把持術具でない %"], rr))
w("")
w("- 重なる = 術具のマスクと手（hand_seg）のマスクが 1 画素以上重なる。把持術具である = hand_tool_seg の把持術具のマスクと RLE まで同一")
w(f"- マスクは物体ごとに描かれるので、手と術具が接していても重ならないことがある（{ref('0.3')}）。重なりは接触の下限の目安で、"
  f"box で数えた手と術具の近さは先行 EDA [§4.3]({MAIN}#s4-3)\n")

# ---------- 付録 ----------
h(2, "A", "付録 A：既存の HTS 分析との対応")
two = {fn: sum(a["category_id"] == 5 for v in H_["hand_tool_seg"][fn]["ann"].values() for a in v) for fn in FILES}
w("既存の HTS の監査は「どのフレームに注釈があるか」を主に扱っている。本書はそれを正本（`data/annotations/egosurgery_hts/`）で数え直し、"
  "注釈の中身と工程の関係を加えた\n")
w(table(["既存の分析", "既存の値", "本書の値", "備考"], [
    ["`egosurgery_hts/*/build_report.md`（split ごとの件数）", "§1.1 の各行", "§1.1", "同じファイルを数えている"],
    ["`experiments/analysis/hts_coverage_2026-07-30/REPORT.md` 結論 2（術具 bbox に対する被覆）",
     "hand 15,397 / tool 14,967 / hand-tool 14,977",
     f"{has['hand_seg'].sum():,} / {has['tool_seg'].sum():,} / {has['hand_tool_seg'].sum():,}", "§0.2"],
    ["同 結論 3（工程に対する真の欠落）", "1,796", f"{len(phase_only):,}", "§0.2。術具 bbox の無い工程 CSV の行で、HTS の注釈も無い"],
    ["同 「3 タスク同時学習に使えるフレーム」（術具 bbox 内）", "14,570", f"{all3.sum():,}", "§0.2"],
    ["同 HTS 対象フレーム", "19,560", f"{len(uni):,}", "既存値は raw の `json_per_video` が列挙する画像。うち 64 枚は 3 種とも注釈が 0 件（2026-10-21 に raw の json_per_video で確認。本スクリプトでは数えない）。"
     "正本は注釈のある画像だけを載せるので、本書の値は注釈のあるフレームの和集合"],
    ["`hand_tool_seg/README.md` の Two Hands Tool", "train 952 / val 176 / test 333 / extra 560",
     " / ".join(f"{fn} {two[fn]}" for fn in FILES), "§1.4"],
    ["`experiments/analysis/hts_raw_provenance_2026-07-29/REPORT.md` C6（把持 ∧ 工程の共存）", "9,106",
     f"{has['hand_tool_seg'].sum():,}", "9,106 は `04_handtool/coco_splits_5cls` の画像数（5,668 + 2,094 + 1,344）。この版は val と test が入れ替わり、"
     "動画 03・14 が抜けている（hts_coverage_2026-07-30 結論 5）。"
     "正本の hand_tool_seg では術具 bbox のあるフレームすべてに工程があるので、注釈のあるフレーム数がそのまま共存数になる"],
    ["同 C4・Task3（SAM 由来）", "マスクは box からの SAM。把持 = 手のセグメンテーションと IoU 最大の術具",
     f"box の IoU 最大と {pct(der['box'] / der['n'])}%、マスクの IoU 最大と {pct(der['mask'] / der['n'])}% 一致",
     "§0.3。マスクの IoU では再現しない"],
    ["`hand_tool_seg/README.md` §4・§8（loss_mask の理由）", "Mouth Gag / Skewer による構造的な除外",
     f"自分の手が写らないフレームと完全に一致。Mouth Gag・Skewer だけのフレームは {pct(lm_only / lm.sum())}%", "§3.2"],
], ["l", "l", "l", "l"]))
w("")

h(2, "B", "付録 B：再現")
w("```bash\n.venv/bin/python docs/analysis_scripts/hts_phase_tool_annotation_stats.py\n```\n")
w("- 読み取り専用で、`data/` には書き込まない。pycocotools で RLE のまま面積・重なりを計算する。10 秒ほどで終わる")
w("- 引数で出力先を変えられる\n")

# ---------- 冒頭 ----------
head = []
hw = head.append
hw("# EgoSurgery-HTS 注釈の EDA：hand_seg・tool_seg・hand_tool_seg と工程・術具 bbox の関係（動画 01〜15）\n")
hw("- 生成: 集計スクリプト `docs/analysis_scripts/hts_phase_tool_annotation_stats.py`（読み取り専用。数値はすべて注釈からの実測で、推定・補完はしない）")
hw(f"- 対象: `data/annotations/egosurgery_hts/` の 3 種。工程・術具 bbox と突き合わせるのは術具 bbox のある {N:,} フレーム（動画 01〜15）")
hw(f"- 先行 EDA（術具・工程・手）は [`{MAIN}`]({MAIN})。手の在否と box での手–術具の近さはそちらにあり、本書はマスク・把持・工程の関係を扱う\n")
hw("## 目次\n")
rr = []
for lv, sid, title in [s for s in D.toc if s[0] == 2 and not s[1].isalpha()]:
    subs = [x for x in D.toc if x[0] == 3 and x[1].split(".")[0] == sid]
    rr.append([f"[{sid}. {title}](#{aid(sid)})",
               " · ".join(f"[{x[1]}](#{aid(x[1])}) {x[2].split('：')[0]}".replace("|", "\\|") for x in subs)])
rr.append(["付録", " · ".join(f"[{title}](#{aid(sid)})" for lv, sid, title in D.toc if sid.isalpha())])
hw(table(["部", "節"], rr, ["l", "l"]))
hw("")
hw("## 要点\n")


def side_rate(j, side):
    idx = np.where(m_ht & (ph == j))[0]
    return np.mean([held_sides[i][SIDES.index(side)] for i in idx]) if len(idx) else 0.0


def top_held(j, side, name_only=False):
    idx = np.where(m_ht & (ph == j))[0]
    c = collections.Counter(r["cls"] or "不明" for i in idx for r in held[fids[i]] if r["side"] == side)
    if not c:
        return None
    n, k = c.most_common(1)[0]
    return n if name_only else f"{n} {rate(k, len(idx))}%"


left_top = {CAN[j]: top_held(j, "左", True) for j in range(nP) if top_held(j, "左", True)}
right_top = {CAN[j]: top_held(j, "右", True) for j in range(nP) if top_held(j, "右", True)}
hd_ = TRX[(ci["hemostasis"], ci["dissection"])]


def hand_name(side):
    return side if side == "両手" else side + "手"


def busy_rate(j):
    idx = np.where(m_ht & (ph == j))[0]
    return np.mean([(held_sides[i][0] and held_sides[i][1]) or held_sides[i][2] for i in idx])


def none_rate(j):
    idx = np.where(m_ht & (ph == j))[0]
    return np.mean([len(held[fids[i]]) == 0 for i in idx])


V = [name for name, _ in VARS]
lr = {n: DOMSIDE[n] for n in ["Tweezers", "Scissors", "Bipolar Forceps", "Needle Holders"]}
hw(f"""**注釈の構造**（{ref('0')}・{ref('2')}）
1. **HTS で工程ラベルを持つのは、術具 bbox のある {N:,} フレームの分だけ**（うち {len(csv15 & uni):,} フレームに HTS の注釈がある）。
   工程だけのフレーム {len(phase_only):,}（disinfection は {sum(1 for r in csv_rows if r['phase'] == 'disinfection')} 行のうち {pv['disinfection']}）と
   extra のフレーム（{min(len(X[k]['imgs']) for k in TYPES):,}〜{max(len(X[k]['imgs']) for k in TYPES):,}）は、工程ラベルと HTS を同時には持たない（{ref('0.2')}）
2. 3 種は互いに独立ではない。hand_seg の手は先行 EDA の手（raw02）と同じ、hand_tool_seg の自分の手は hand_seg の自分の手と同じマスク。
   tool_seg の Tool15 部分は Mouth Gag を除く 14 クラスで術具 bbox とインスタンス数・写るフレームが完全に同じで、**Mouth Gag は tool_seg に 1 件も無い**（{ref('0.3')}・{ref('2.1')}）
3. 未注釈のフレームは中身で決まっている。tool_seg の未注釈 {len(ts_none)} は術具 bbox が Mouth Gag だけか 0 個のフレーム、
   hand_tool_seg の未注釈（loss_mask）{lm.sum()} は自分の手が写らないフレームと完全に一致する。README の「Mouth Gag / Skewer による除外」という説明に
   当てはまるのは loss_mask の {pct(lm_only / lm.sum())}% だけ（{ref('2.2')}・{ref('3.2')}）
4. **把持は box の重なりで決まっている。** 把持術具は同じ側の手と box の IoU が最大の術具と {pct(der['box'] / der['n'])}% 一致し、
   マスクの IoU が最大の術具とは {pct(der['mask'] / der['n'])}% しか一致しない（{ref('0.3')}）

**工程との関係**（{ref('3')}）
5. 工程 CSV の行のうち 3 種すべての注釈があるのは {pct(all3.sum() / len(csv_rows))}%。低いのは
   {'、'.join(f'{CAN[j]} {rate(((ph == j) & all3).sum(), cov_all[CAN[j]])}%' for j in sorted(range(nP), key=lambda j: ((ph == j) & all3).sum() / cov_all[CAN[j]])[:3])}
   （{ref('3.1')}）
6. tool_seg だけにある {len(EXT)} クラスは工程に強く偏る（{'、'.join(f'{n} → {CAN[int(PFs[n].argmax())]}' for n in ext_spec[:5])} など）が、
   多くは 1〜3 動画にしか出ない（{ref('3.3')}）
7. 両手の使い方が工程で違う。両手で 1 つを持つのは anesthesia {pct(side_rate(ci['anesthesia'], '両手'))}%・design {pct(side_rate(ci['design'], '両手'))}% に多く、
   closure は {pct(side_rate(ci['closure'], '両手'))}%。左右がともにふさがるのは incision・dissection・hemostasis で
   {pct(min(busy_rate(ci[p]) for p in ['incision', 'dissection', 'hemostasis']))}〜{pct(max(busy_rate(ci[p]) for p in ['incision', 'dissection', 'hemostasis']))}%。
   irrigation は何も持たないフレームが {pct(none_rate(ci['irrigation']))}%（{ref('3.5')}）
8. **右手の最多の術具は工程ごとに入れ替わり、左手の最多は""" + ("工程によらず陰性対照群" if all(v in NEGCTL for v in left_top.values())
                                                              else "工程によって陰性対照群以外") + f"""の術具。** 右手の最多は
   design {top_held(ci['design'], '右')}、anesthesia {top_held(ci['anesthesia'], '右')}、incision {top_held(ci['incision'], '右')}、
   dissection {top_held(ci['dissection'], '右')}、hemostasis {top_held(ci['hemostasis'], '右')}、closure {top_held(ci['closure'], '右')}。
   左手の最多は {'、'.join(f'{p} {n}' for p, n in left_top.items())}（{ref('3.6')}）
9. 持つ手は動画をまたいで安定している。主に左で持つ動画: Tweezers {lr['Tweezers'][0]['左']}/{lr['Tweezers'][1]}。主に右で持つ動画:
   Scissors {lr['Scissors'][0]['右']}/{lr['Scissors'][1]}、Bipolar Forceps {lr['Bipolar Forceps'][0]['右']}/{lr['Bipolar Forceps'][1]}、
   Needle Holders {lr['Needle Holders'][0]['右']}/{lr['Needle Holders'][1]}（{ref('3.7')}）
10. 動画一つ抜きで「値ごとの最多工程」を当てる規則では、持たれている（側, クラス）の集合 {pct(INFO[V[3]][2])}% が
    写っている術具の集合（術具 bbox）{pct(INFO[V[4]][2])}% より当たる。相互情報量は値の種類の多い後者が大きい
    （{INFO[V[4]][1]:.3f} 対 {INFO[V[3]][1]:.3f} bit）。
    把持の状態（左・右・両手で持つか）だけでは {pct(INFO[V[1]][2])}% で、常に {CAN[maj[0]]} と答える基準 {pct(maj[1] / len(C_))}% を下回る（{ref('3.8')}）
11. 工程が変わる隣接フレームの {pct((chg_p & chg_h).sum() / chg_p.sum())}% で把持が変わる（工程が同じなら {pct((~chg_p & chg_h).sum() / (~chg_p).sum())}%）。
    hemostasis → dissection で最も多く手放すのは {hand_name(mc(hd_[1], 1)[0][0][0])}の {mc(hd_[1], 1)[0][0][1]}、
    最も多く持ち始めるのは {hand_name(mc(hd_[0], 1)[0][0][0])}の {mc(hd_[0], 1)[0][0][1]}（{ref('3.9')}）
""")

open(OUT, "w").write("\n".join(head + D.md) + "\n")
print("wrote", OUT, len(head) + len(D.md))
