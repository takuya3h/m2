"""EgoSurgery 注釈の EDA（読み取り専用）。術具・工程・手の注釈から md を 2 本書く。

本編: 動画 01〜15 の術具・工程・手 → docs/phase_tool_annotation_stats.md
別冊: 動画 17〜21 の工程 CSV       → docs/phase_annotation_stats_videos17-21.md
実行（リポジトリのルートで）:
  .venv/bin/python docs/analysis_scripts/phase_tool_annotation_stats.py [本編の出力先 [別冊の出力先]]
"""
import collections
import csv
import glob
import itertools
import json
import math
import os
import re
import sys

import numpy as np
from scipy.stats import rankdata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/docs/phase_tool_annotation_stats.md"
OUT2 = sys.argv[2] if len(sys.argv) > 2 else f"{ROOT}/docs/phase_annotation_stats_videos17-21.md"
ANN = f"{ROOT}/data/annotations"
JM = f"{ROOT}/data/processed/joint_manifest"
RAW_HAND = f"{ROOT}/data/raw/OpenSurgery_Dataset/02_hand/json_per_video"
SPLITS = ["train", "val", "test"]
TOOLS = json.load(open(f"{JM}/tool_categories.json"))
T = [TOOLS[str(i)] for i in range(15)]
TARGET = {"Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory"}
NEGCTL = {"Gauze", "Mouth Gag", "Suction Cannula", "Tweezers"}
# 参照順（標準の手術の流れ）。本書の工程の並びはすべてこれに揃える
CAN = ["disinfection", "design", "anesthesia", "incision", "dissection", "hemostasis", "irrigation", "closure",
       "dressing"]
ci = {p: i for i, p in enumerate(CAN)}
AB = {"disinfection": "DI", "design": "DE", "anesthesia": "AN", "incision": "IN", "dissection": "DS",
      "hemostasis": "HE", "irrigation": "IR", "closure": "CL", "dressing": "DR"}
RAW_HAND_NAMES = ["First Person's Left Hand", "First Person's Right Hand", "Other Person's Left Hand",
                  "Other Person's Right Hand"]
HN = ["自分の左手", "自分の右手", "他者の左手", "他者の右手"]


def bn(s):
    return os.path.splitext(os.path.basename(s))[0]


def grp(t):
    n = T[t]
    return "標的" if n in TARGET else ("陰性対照" if n in NEGCTL else "—")


# ---------- 読み込み ----------
frames = []  # 術具注釈のあるフレーム（動画 01〜15）
for s in SPLITS:
    d = json.load(open(f"{JM}/{s}.json"))
    for c in d["clips"]:
        for f in c["frames"]:
            frames.append(dict(split=s, video=c["video"], clip=c["clip_id"],
                               idx=int(f["frame"].rsplit("_", 1)[1]), fid=f["frame"],
                               phase=f["phase"], labels=list(f["tool_labels"]), boxes=list(f["boxes"])))
N = len(frames)
fidx = {f["fid"]: i for i, f in enumerate(frames)}


def load_rows(keep):
    """工程 CSV の行を (動画, クリップ番号, フレーム番号) の順に並べて返す。"""
    rows = []
    for p in sorted(glob.glob(f"{ANN}/egosurgery_phase/*.csv")):
        clip = os.path.basename(p)[:-4]
        if not keep(int(clip.split("_")[0])):
            continue
        for r in csv.DictReader(open(p)):
            rows.append(dict(video=clip.split("_")[0], clip=clip, cnum=int(clip.split("_")[1]),
                             idx=int(r["Frame"].rsplit("_", 1)[1]), fid=r["Frame"], phase=r["Phase"]))
    rows.sort(key=lambda r: (r["video"], r["cnum"], r["idx"]))
    pos = collections.Counter()
    for r in rows:
        r["pos"] = pos[r["clip"]]
        pos[r["clip"]] += 1
    return rows


csv_rows = load_rows(lambda v: v <= 15)
rows17 = load_rows(lambda v: v >= 17)
csv_pos = {r["fid"]: r["pos"] for r in csv_rows}
csv_phase = {r["fid"]: r["phase"] for r in csv_rows}
assert all(csv_phase[f["fid"]] == f["phase"] for f in frames)
assert set(csv_phase.values()) | {r["phase"] for r in rows17} <= set(CAN)

# 術具 box の座標（大きさ・位置・品質用）。manifest と同じ box であることを確かめる
B = []
for s in SPLITS:
    d = json.load(open(f"{ANN}/egosurgery_tool/instances_{s}.json"))
    assert {c["id"]: c["name"] for c in d["categories"]} == dict(enumerate(T))
    id2 = {im["id"]: im for im in d["images"]}
    assert {bn(im["file_name"]) for im in d["images"]} == {f["fid"] for f in frames if f["split"] == s}
    for a in d["annotations"]:
        im = id2[a["image_id"]]
        x, y, bw, bh = a["bbox"]
        B.append(dict(fid=bn(im["file_name"]), split=s, cat=a["category_id"], x=x, y=y, w=bw, h=bh,
                      W=im["width"], H=im["height"], area=a.get("area") or bw * bh, crowd=bool(a.get("iscrowd"))))
assert collections.Counter((b["fid"], b["cat"]) for b in B) == \
    collections.Counter((f["fid"], t) for f in frames for t in f["labels"])

# 手（raw02。2026-07-29 に正本と決めた版）。ファイル名で結合する。
# クリップごとの json は動画の全クリップの画像を並べ、box はそのクリップの分だけを持つ
hb = collections.defaultdict(list)  # fid -> [(手クラス 0〜3, bbox)]
raw_imgs, n_raw_box = set(), 0
for p in sorted(glob.glob(f"{RAW_HAND}/*/*.json")):
    d = json.load(open(p))
    assert {c["id"]: c["name"] for c in d["categories"]} == {i + 1: n for i, n in enumerate(RAW_HAND_NAMES)}
    m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
    raw_imgs |= set(m.values())
    for a in d["annotations"]:
        hb[m[a["image_id"]]].append((a["category_id"] - 1, a["bbox"]))
        n_raw_box += 1
assert all(f["fid"] in raw_imgs for f in frames)
n_hdup = sum(len(v) - len({(k, tuple(b)) for k, b in v}) for x, v in hb.items() if x in fidx)


def old_hand_agreement():
    """旧 EDA の手の出所（19 クラス版）と 4 クラス版で、手の box がファイル名で一致するフレームの割合。"""
    out = {}
    for s in SPLITS:
        h19 = json.load(open(f"{ANN}/egosurgery_tool_hand/instances_{s}.json"))
        h4 = json.load(open(f"{ANN}/egosurgery_tool_hand/{s}.json"))
        m19 = {im["id"]: bn(im["file_name"]) for im in h19["images"]}
        m4 = {im["id"]: bn(im["file_name"]) for im in h4["images"]}
        a19, a4 = collections.defaultdict(list), collections.defaultdict(list)
        for a in h19["annotations"]:
            if a["category_id"] >= 15:
                a19[m19[a["image_id"]]].append((a["category_id"] - 15, tuple(a["bbox"])))
        for a in h4["annotations"]:
            a4[m4[a["image_id"]]].append((a["category_id"] - 1, tuple(a["bbox"])))
        fr = set(m19.values())
        c4 = collections.Counter(k for v in a4.values() for k, _ in v)
        craw = collections.Counter(k for x in fr for k, _ in hb.get(x, []))
        out[s] = (sum(sorted(a19[x]) == sorted(a4[x]) for x in fr), len(fr), len(m4), c4 == craw)
    return out


# ---------- 基本行列 ----------
nP = len(CAN)
ph = np.array([ci[f["phase"]] for f in frames])
vid = np.array([f["video"] for f in frames])
spl = np.array([f["split"] for f in frames])
pres = np.zeros((N, 15), bool)
nbox = np.zeros((N, 15), int)
for i, f in enumerate(frames):
    for lab in f["labels"]:
        pres[i, lab] = True
        nbox[i, lab] += 1
ph_n = np.array([(ph == j).sum() for j in range(nP)])
PF = np.array([[pres[ph == j, t].sum() for j in range(nP)] for t in range(15)])  # 15x9 在フレーム数
BX = np.array([[nbox[ph == j, t].sum() for j in range(nP)] for t in range(15)])  # 15x9 box 数
tool_pf = PF.sum(1)
tool_bx = BX.sum(1)
videos = sorted({f["video"] for f in frames})
vsplit = {f["video"]: f["split"] for f in frames}
dom = PF.argmax(1)
TO = sorted(range(15), key=lambda t: (dom[t], -PF[t, dom[t]] / tool_pf[t]))  # 最頻工程の順 → 集中度の順
TC = sorted(range(15), key=lambda t: -tool_bx[t])  # box の多い順
SMALL = {j for j in range(nP) if ph_n[j] < 200}
hpres = np.zeros((N, 4), bool)
hcnt = np.zeros(N, int)
for i, f in enumerate(frames):
    for k, _ in hb.get(f["fid"], []):
        hpres[i, k] = True
    hcnt[i] = len(hb.get(f["fid"], []))


# ---------- 書式 ----------
def pct(x, d=1):
    if x == 0:
        return "0"
    s = f"{100 * x:.{d}f}"
    return f"<{10 ** -d:.{d}f}" if float(s) == 0 else s


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


def Hb(q):
    return 0.0 if q <= 0 or q >= 1 else -(q * math.log2(q) + (1 - q) * math.log2(1 - q))


def H(pv):
    pv = np.asarray(pv, float)
    pv = pv[pv > 0] / pv.sum()
    return float(-(pv * np.log2(pv)).sum())


def eff_weight(counts, beta=0.999):
    """effective number（Cui et al. 2019）の逆数を平均 1 に正規化した重み。"""
    wv = np.array([(1 - beta) / (1 - beta ** n) if n > 0 else 0.0 for n in counts])
    return wv / wv.sum() * len(wv)


def js(p, q):
    p, q = np.asarray(p, float) / np.sum(p), np.asarray(q, float) / np.sum(q)
    m = (p + q) / 2

    def kl(a, b):
        k = a > 0
        return float((a[k] * np.log2(a[k] / b[k])).sum())
    return (kl(p, m) + kl(q, m)) / 2


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


# ---------- 工程 CSV だけで決まる量（本編と別冊で共用） ----------
def segments(rows):
    """クリップ内で同じ工程が続く範囲 [(動画, クリップ, 工程, 行数)]。"""
    out = []
    for (v, c), g in itertools.groupby(rows, key=lambda r: (r["video"], r["clip"])):
        for k, gg in itertools.groupby(g, key=lambda r: r["phase"]):
            out.append((v, c, k, len(list(gg))))
    return out


def trans_matrix(segs):
    M = np.zeros((nP, nP), int)
    for a, b in zip(segs, segs[1:]):
        if a[1] == b[1]:
            M[ci[a[2]], ci[b[2]]] += 1
    return M


def temporal(rows):
    steps = same = bnd = 0
    nxt = collections.defaultdict(collections.Counter)
    strides, kinds = [], []
    for _, g in itertools.groupby(rows, key=lambda r: r["clip"]):
        g = list(g)
        ps = [r["phase"] for r in g]
        kinds.append(len(set(ps)))
        for i in range(1, len(ps)):
            steps += 1
            same += ps[i] == ps[i - 1]
            nxt[ps[i - 1]][ps[i]] += 1
        bnd += sum((i > 0 and ps[i] != ps[i - 1]) or (i < len(ps) - 1 and ps[i] != ps[i + 1]) for i in range(len(ps)))
        strides += [b["idx"] - a["idx"] for a, b in zip(g, g[1:])]
    st = np.array(strides)
    return dict(steps=steps, self=same / steps, boundary=bnd / len(rows),
                markov=sum(c.most_common(1)[0][1] for c in nxt.values()) / steps,
                allself=all(c.most_common(1)[0][0] == p for p, c in nxt.items()),
                st_med=int(np.median(st)), st_mode=collections.Counter(strides).most_common(1)[0][0],
                st_p90=sorted(strides)[int(0.9 * len(strides))], st_one=float((st == 1).mean()), st_max=int(st.max()),
                st_n=len(st), nclip=len(kinds), kinds=kinds)


def temporal_table(tm):
    rows = [
        ["隣り合う行が同じ工程である割合", pct(tm["self"]), f"{tm['steps']:,} 組（同じクリップ内）"],
        ["工程の境目にある行の割合", pct(tm["boundary"]), "前後どちらかの行と工程が違う行"],
        ["直前の工程から次の工程を当てる割合（1 次マルコフ）", pct(tm["markov"]),
         "最尤の次の工程はどの工程でも「同じ工程」" if tm["allself"] else "最尤の次の工程が自分以外になる工程がある"],
        ["行間のフレーム番号の差：中央値 / 最頻値 / 90% 点", f"{tm['st_med']} / {tm['st_mode']} / {tm['st_p90']}",
         f"差が 1 の割合 {pct(tm['st_one'])}%、最大 {tm['st_max']:,}"],
        ["1 クリップに現れる工程の種類", f"{np.mean(tm['kinds']):.1f}",
         f"範囲 {min(tm['kinds'])}〜{max(tm['kinds'])}、{tm['nclip']} クリップ"],
    ]
    return table(["指標", "値", "備考"], rows, ["l", "r", "l"])


def write_order(d, rows, sids, level, vlabel=None):
    """動画ごとの工程の並び（区間列・初出・指標・後戻り・順守率）を書き、要点用の値を返す。"""
    vrows = {v: list(g) for v, g in itertools.groupby(rows, key=lambda r: r["video"])}
    VV = sorted(vrows)
    vseq, vdisp, vclips = {}, {}, {}
    for v in VV:
        parts, merged = [], []
        for _, g in itertools.groupby(vrows[v], key=lambda r: r["clip"]):
            cs = [(k, len(list(gg))) for k, gg in itertools.groupby(r["phase"] for r in g)]
            parts.append(" → ".join(f"{AB[k]}{n}" for k, n in cs))
            for k, n in cs:
                if merged and merged[-1][0] == k:
                    merged[-1][1] += n
                else:
                    merged.append([k, n])
        vdisp[v], vseq[v], vclips[v] = " ‖ ".join(parts), merged, len(parts)
    lab = (lambda v: [v, vlabel[v]]) if vlabel else (lambda v: [v])
    labh = ["動画", "公式分割"] if vlabel else ["動画"]
    s1, s2, s3, s4, s5 = sids

    d.h(level, s1, "区間列（動画ごとに工程を時系列に並べたもの）")
    d.w("記号: " + "、".join(f"{AB[p]} = {p}" for p in CAN) + "。数字はその区間の工程 CSV の行数、‖ はクリップの境目\n")
    d.w(table(labh + ["行数", "区間列"], [lab(v) + [f"{len(vrows[v]):,}", vdisp[v]] for v in VV],
              ["l"] * len(labh) + ["r", "l"]))
    d.w("")
    d.w(f"- {ref(s2)} 以降は、クリップは番号の順に時系列でつながるとみなし、クリップをまたいで同じ工程が続く場合は 1 区間として数える\n")

    d.h(level, s2, "初出の順序（各工程が初めて現れる順）")
    rr, nmatch = [], 0
    fpos = {v: {} for v in VV}
    for v in VV:
        for i, (k, _) in enumerate(vseq[v]):
            fpos[v].setdefault(k, i)
        first = list(dict.fromkeys(k for k, _ in vseq[v]))
        agree = sum(ci[first[i]] < ci[first[j]] for i in range(len(first)) for j in range(i + 1, len(first)))
        ok = first == sorted(first, key=ci.get)
        nmatch += ok
        rr.append([v, " → ".join(AB[k] for k in first), "一致" if ok else "不一致",
                   f"{agree}/{len(first) * (len(first) - 1) // 2}", len(first)])
    d.w(table(["動画", "初出の順序", "参照順と", "初出の対の順守", "工程の種類"], rr, ["l", "l", "l", "r", "r"]))
    d.w("")
    d.w("- 初出の対の順守 = 初出の順序に現れる工程の対のうち、参照順と同じ前後関係の対の数 / 対の総数\n")
    rr = []
    for a in CAN:
        cells = []
        for b in CAN:
            both = [v for v in VV if a in fpos[v] and b in fpos[v]]
            cells.append("—" if a == b else (f"{sum(fpos[v][a] < fpos[v][b] for v in both)}/{len(both)}" if both else "·"))
        rr.append([a] + cells)
    d.details("初出の前後関係：行の工程が列の工程より先に初出する動画の数 / 両方がある動画の数",
              table(["先 ＼ 後"] + CAN, rr))

    d.h(level, s3, "動画ごとの並びの指標")
    rr = []
    after_k, n_close, noclose = 0, 0, []
    for v in VV:
        sq = vseq[v]
        tr = list(zip(sq, sq[1:]))
        back = sum(ci[b[0]] < ci[a[0]] for a, b in tr)
        hd = sum({a[0], b[0]} == {"dissection", "hemostasis"} for a, b in tr)
        kc = next((i for i, s_ in enumerate(sq) if s_[0] == "closure"), None)
        after = "—" if kc is None else sum(s_[0] not in ("closure", "dressing") for s_ in sq[kc + 1:])
        if kc is None:
            noclose.append((v, sq[-1][0]))
        else:
            n_close += 1
            after_k += after > 0
        rr.append(lab(v) + [vclips[v], len(sq), len({k for k, _ in sq}), len(tr), back,
                            pct(back / len(tr)) if tr else "—", hd, after, sq[0][0], sq[-1][0]])
    d.w(table(labh + ["クリップ数", "区間数", "工程の種類", "遷移数", "後戻りの遷移", "後戻り %",
                      "dissection⇄hemostasis の遷移", "最初の closure の後の closure・dressing 以外の区間",
                      "最初の工程", "最後の工程"], rr))
    d.w("")
    d.w(f"- 後戻り = 参照順で前にある工程への遷移（hemostasis → dissection を含む）。内訳は {ref(s4)}\n")
    rr = []
    for v in VV:
        cnt = collections.Counter(k for k, _ in vseq[v])
        rr.append([v] + [str(cnt[p]) for p in CAN] + [len(vseq[v])])
    rr.append(["**2 回以上の動画数**"] + [str(sum(collections.Counter(k for k, _ in vseq[v])[p] >= 2 for v in VV))
                                       for p in CAN] + [""])
    d.details("動画 × 工程：区間の数（同じ工程が何回に分かれて現れるか）", table(["動画"] + CAN + ["計"], rr))

    d.h(level, s4, "後戻りの遷移の内訳")
    bc, bv = collections.Counter(), collections.defaultdict(set)
    for v in VV:
        for a, b in zip(vseq[v], vseq[v][1:]):
            if ci[b[0]] < ci[a[0]]:
                bc[(a[0], b[0])] += 1
                bv[(a[0], b[0])].add(v)
    tot_tr = sum(len(vseq[v]) - 1 for v in VV)
    in_clip = int(trans_matrix(segments(rows)).sum())
    rr = [[f"{a} → {b}", n, pct(n / tot_tr), f"{len(bv[(a, b)])}/{len(VV)}", "、".join(sorted(bv[(a, b)]))]
          for (a, b), n in sorted(bc.items(), key=lambda x: (-x[1], x[0]))]
    rr.append(["**計**", sum(bc.values()), pct(sum(bc.values()) / tot_tr), "", ""])
    d.w(table(["遷移", "回数", "全遷移に対する %", "起きた動画", "動画"], rr, ["l", "r", "r", "r", "l"]))
    d.w("")
    d.w(f"- 全遷移 {tot_tr} 回 = 同じクリップ内の {in_clip} 回 + クリップをまたいで工程が変わる {tot_tr - in_clip} 回"
        "（クリップをまたいで同じ工程が続く箇所は遷移に数えない）\n")

    d.h(level, s5, "参照順の順守率：数え方による違い")

    def adherence(units):
        vals = []
        for i in range(nP):
            for j in range(i + 1, nP):
                both = [u for u in units.values() if CAN[i] in u and CAN[j] in u]
                if len(both) >= 3:
                    vals.append(sum(u[CAN[i]] < u[CAN[j]] for u in both) / len(both))
        return float(np.mean(vals)), len(vals)

    clip_med = {}
    for c, g in itertools.groupby(rows, key=lambda r: r["clip"]):
        g = list(g)
        clip_med[c] = {p: float(np.median([r["idx"] for r in g if r["phase"] == p])) for p in {r["phase"] for r in g}}
    vid_med = {v: {p: float(np.median([i for i, r in enumerate(vrows[v]) if r["phase"] == p]))
                   for p in {r["phase"] for r in vrows[v]}} for v in VV}
    fw = sum(ci[b[0]] > ci[a[0]] for v in VV for a, b in zip(vseq[v], vseq[v][1:]))
    adh = {}
    rr = []
    for key, name, units in [("clip", "クリップ単位・各工程のフレーム番号の中央値", clip_med),
                             ("video", "動画単位・各工程の時系列位置の中央値", vid_med),
                             ("first", "動画単位・各工程の初出の位置", fpos)]:
        adh[key] = adherence(units)
        rr.append([name, f"{adh[key][0]:.3f}", adh[key][1], len(units)])
    rr.append(["動画単位・区間の遷移のうち参照順で前向きの割合", f"{fw / tot_tr:.3f}", "—", f"{len(VV)}（{fw}/{tot_tr} 遷移）"])
    d.w(table(["数え方", "順守率", "対の数", "単位の数"], rr, ["l", "r", "r", "r"]))
    d.w("")
    d.w("- 上の 3 行は、参照順の 36 対のうち両方を含む単位が 3 以上ある対について、前後関係が参照順どおりの単位の割合を平均した値。"
        f"中央値や初出で比べる数え方は、工程の往復（{ref(s4)}）を見ない\n")
    return dict(VV=VV, nmatch=nmatch, adh=adh, fw=fw, tot_tr=tot_tr, back=sum(bc.values()),
                topback=[(a, b, n, len(bv[(a, b)])) for (a, b), n in sorted(bc.items(), key=lambda x: -x[1])[:3]],
                n_close=n_close, after_k=after_k, noclose=noclose, vseq=vseq)


def phase_seg_table(rows, prog=None):
    segs = segments(rows)
    rr = []
    for j in range(nP):
        ls = [s[3] for s in segs if s[2] == CAN[j]]
        if not ls:
            rr.append([CAN[j], 0, 0, "—", "—", "—"] + (["—", "—"] if prog else []))
            continue
        r = [CAN[j], len({s[0] for s in segs if s[2] == CAN[j]}), len(ls), f"{np.mean(ls):.1f}",
             f"{np.median(ls):.0f}", f"{min(ls)}–{max(ls)}"]
        if prog:
            pp = np.array(prog[CAN[j]])
            r += [f"{np.median(pp):.2f}", f"{np.percentile(pp, 25):.2f}–{np.percentile(pp, 75):.2f}"]
        rr.append(r)
    head = ["工程", "動画数", "区間数", "区間長の平均", "中央値", "範囲"] + (["進行度の中央値", "進行度の四分位範囲"] if prog else [])
    return table(head, rr)


def trans_table(M):
    rr = [[CAN[a]] + [str(M[a, b]) if M[a, b] else "·" for b in range(nP)] + [M[a].sum()] for a in range(nP)]
    return table(["遷移元 ＼ 遷移先"] + [AB[p] for p in CAN] + ["計"], rr)


# =====================================================================
# 本編
# =====================================================================
D = Doc()
w, h = D.w, D.h
cov_all = collections.Counter(r["phase"] for r in csv_rows)
n_csv15 = len({r["clip"] for r in csv_rows})
nz = int((pres.sum(1) == 0).sum())
nzh = int((hcnt == 0).sum())
ann_clips = {f["clip"] for f in frames}
miss = collections.Counter(r["clip"] for r in csv_rows if r["clip"] not in ann_clips)
n_phase_only = len(csv_rows) - N
sizes = collections.Counter((b["W"], b["H"]) for b in B)
assert len(sizes) == 1
W0, H0 = next(iter(sizes))
DIAG = math.hypot(W0, H0)

# ---------- §0 ----------
h(2, "0", "母集団・規模・定義")
h(3, "0.1", "入力と結合")
w(table(["データ", "ファイル", "本書での使い方"], [
    ["工程", f"`data/annotations/egosurgery_phase/<動画>_<クリップ>.csv`（動画 01〜15 の {n_csv15} 本）",
     f"{ref('2')} は全行。{ref('3')}〜{ref('5')} は術具注釈のあるフレームだけ"],
    ["術具", "`data/processed/joint_manifest/{train,val,test}.json`（工程と術具 box を frame_id で結合済み）",
     f"フレームごとの術具の在否と box 数（{ref('1')}・{ref('3')}・{ref('5')}）"],
    ["術具 box の座標", "`data/annotations/egosurgery_tool/instances_{train,val,test}.json`", f"box の大きさ・位置・品質（{ref('1.3')}・{ref('1.4')}・{ref('3.14')}）"],
    ["手", "`data/raw/OpenSurgery_Dataset/02_hand/json_per_video/<クリップ>/*.json`（raw02、4 クラス）",
     f"{ref('4')}。ファイル名（フレーム ID）で結合"],
], ["l", "l", "l"]))
w("")
w(f"- 結合の検査: manifest の工程ラベルは工程 CSV と全 {N:,} フレームで一致。manifest の術具ラベルは COCO の box と"
  "フレーム × クラスの件数まで一致。raw02 は術具注釈のある全フレームを画像として含む")
w("- 手の出所: 手の注釈は 2026-07-29 に raw02 を正本と決めている（`docs/experiment_log.md` の「タスク1: 正本＝raw02」）。"
  f"旧 EDA が使った 19 クラス版は使わない（理由と値の違いは {ref('C')}）\n")

h(3, "0.2", "母集団の層")
w(table(["層", "フレーム", "使う部"], [
    ["工程 CSV の行（動画 01〜15）", f"{len(csv_rows):,}", ref("2")],
    ["　うち術具注釈のあるフレーム（**主な母集団**）", f"**{N:,}**（{pct(N / len(csv_rows))}%）", "・".join(ref(x) for x in "1345")],
    ["　　うち術具 box が 0 個", f"{nz}", "在否の分母に入れ、box 数には寄与しない"],
    ["　　うち手 box が 0 個", f"{nzh}", "同上"],
    ["　うち術具注釈のないフレーム（工程だけ）", f"{n_phase_only:,}", ref("2.1")],
], ["l", "r", "l"]))
w("")
w(f"- 術具 box {int(nbox.sum()):,} 個、手 box {int(hcnt.sum()):,} 個（主な母集団の中）。工程 9 / 術具 15 / 手 4 クラス")
w("- **術具注釈の無いフレームは「術具なし」ではなく「未注釈」**なので主な母集団から外す。"
  + "、".join(f"クリップ {c}（{n} フレーム）" for c, n in sorted(miss.items())) + "は丸ごと術具未注釈")
w(f"- 動画 17〜21 は工程 CSV だけがあり術具・手の box が無い。別冊 [`{os.path.basename(OUT2)}`]({os.path.basename(OUT2)}) にまとめた\n")

h(3, "0.3", "公式 split ごとの規模")
rr = []
for s in SPLITS + ["計"]:
    m = np.ones(N, bool) if s == "計" else spl == s
    vs = sorted({v for v in videos if s == "計" or vsplit[v] == s})
    rr.append([s, f"{len(vs)}（{', '.join(vs)}）" if s != "計" else f"{len(vs)}",
               f"{sum(1 for r in csv_rows if r['video'] in vs):,}", f"{m.sum():,}", f"{int(nbox[m].sum()):,}",
               f"{nbox[m].sum() / m.sum():.2f}", int((pres[m].sum(1) == 0).sum()), f"{int(hcnt[m].sum()):,}",
               int((hcnt[m] == 0).sum())])
w(table(["split", "動画", "工程 CSV の行", "術具注釈のあるフレーム", "術具 box", "術具 box / フレーム", "術具 box 0 のフレーム",
         "手 box", "手 box 0 のフレーム"], rr, ["l", "l", "r", "r", "r", "r", "r", "r", "r"]))
w("")
w("- 公式 split は動画単位で、同じ動画のフレームが複数の split にまたがらない。現行の判定は動画単位の五分割で行うので、"
  f"split ごとの偏りは {ref('5')} に記述としてだけ置く\n")

h(3, "0.4", "用語と記号")
w(table(["記号", "意味"], [
    ["在フレーム", "その術具の box が 1 個以上あるフレーム（同じ術具が 2 本写っても 1 と数える）"],
    ["在率", "母集団のフレームのうち在フレームの割合"],
    ["P(工程 \\| 術具)", "その術具の在フレームのうち、各工程に属する割合（行で 100%）"],
    ["P(術具 \\| 工程)", "その工程のフレームのうち、その術具が写っている割合（工程ごとの在率。多ラベルなので工程内で合計は 100% にならない）"],
    ["工程内構成比", "その工程での術具の在フレーム数を全術具で合計し、各術具の占める割合（工程ごとに 100%）"],
    ["lift", "P(術具 \\| 工程) / P(術具)。1 より大きいほどその工程に偏る。0 はその工程で一度も出ない"],
    ["†", f"術具注釈のあるフレームが 200 未満の工程（{', '.join(CAN[j] + f' {ph_n[j]}' for j in sorted(SMALL))}）。割合は不安定"],
    ["群", "`context/conventions.md#det_groups` の標的群（5）・陰性対照群（4）"],
    ["区間", "同じクリップ内で同じ工程が連続する範囲。長さは工程 CSV の行数で数える（フレーム番号は欠番を含むため）"],
    ["進行度", "動画ごとに工程 CSV の全行を時系列に並べた順位を 0（開始）〜1（終了）に正規化した値"],
    ["参照順", " → ".join(CAN) + "（標準の手術の流れ）。本書の工程の列はすべてこの順"],
    ["工程の略号", "、".join(f"{AB[p]} = {p}" for p in CAN)],
    ["手", "「自分」はカメラを着けた術者、「他者」はそれ以外の人の手（raw02 の First Person / Other Person）"],
], ["l", "l"]))
w("")
w("- 術具の並びは §1 では box の多い順、§3 では最頻工程の順（同じ最頻工程の中ではその工程への集中度の高い順）\n")

# ---------- §1 術具 ----------
h(2, "1", "術具")
w(f"母集団: 術具注釈のある {N:,} フレーム、box {int(nbox.sum()):,} 個。術具は box の多い順\n")
h(3, "1.1", "術具ごとの件数と広がり")
ew_t = eff_weight(tool_bx)
rr = []
for t in TC:
    vb = collections.Counter({v: int(nbox[vid == v, t].sum()) for v in videos})
    top_v, top_n = vb.most_common(1)[0]
    rr.append([T[t], grp(t), f"{tool_bx[t]:,}", pct(tool_bx[t] / tool_bx.sum()), f"{tool_pf[t]:,}",
               pct(tool_pf[t] / N), f"{tool_bx[t] / tool_pf[t]:.2f}", f"{sum(n > 0 for n in vb.values())}/15",
               f"{top_v}（{pct(top_n / tool_bx[t])}）", phn(dom[t]), f"{ew_t[t]:.2f}"])
w(table(["術具", "群", "box", "box の構成比 %", "在フレーム", "在率 %", "box / 在フレーム", "出現動画",
         "box の最も多い動画（占有 %）", "最頻工程", "逆頻度の重み"], rr))
w("")
w(f"- box の最多 / 最少 = {T[TC[0]]} / {T[TC[-1]]} = {tool_bx[TC[0]] / tool_bx[TC[-1]]:.1f} 倍。"
  f"在フレームでは {tool_pf.max() / tool_pf.min():.1f} 倍")
w("- box / 在フレームが 1 を大きく超える術具は、同じフレームに 2 本以上写りやすい")
w("- 逆頻度の重み = effective number（β = 0.999）の逆数を 15 クラスの平均が 1 になるよう正規化した値（box 数から一意に決まる）\n")

h(3, "1.2", "1 フレームに写る術具の数")
kk = pres.sum(1)
kb = nbox.sum(1)
rr = [[k, f"{(kk == k).sum():,}", pct((kk == k).mean()), f"{(kb == k).sum():,}", pct((kb == k).mean())]
      for k in range(int(kb.max()) + 1)]
w(table(["k", "術具の種類が k のフレーム", "%", "box が k 個のフレーム", "%"], rr))
w("")
sets_all = collections.Counter(tuple(np.where(pres[i])[0]) for i in range(N))
w(f"- 種類数の平均 {kk.mean():.2f}（中央値 {np.median(kk):.0f}、最大 {kk.max()}）、box 数の平均 {kb.mean():.2f}"
  f"（中央値 {np.median(kb):.0f}、最大 {kb.max()}）。フレーム内の術具の組み合わせは {len(sets_all)} 通り（頻出の組み合わせは {ref('3.9')}）\n")

h(3, "1.3", "box の大きさと形")
rr = []
for s in SPLITS + ["計"]:
    bs = [b for b in B if s == "計" or b["split"] == s]
    c = collections.Counter("small" if b["area"] < 32 ** 2 else ("medium" if b["area"] < 96 ** 2 else "large") for b in bs)
    rr.append([s, f"{len(bs):,}"] + [f"{c[k]:,}（{pct(c[k] / len(bs))}）" for k in ["small", "medium", "large"]])
w(table(["split", "box", "small（< 32²）", "medium", "large（≥ 96²）"], rr, ["l", "r", "r", "r", "r"]))
w("")
w(f"- COCO の面積区分（`area` 欄。画像は全 box で {W0}×{H0}）。括弧内は %\n")
rr = []
for t in TC:
    bs = [b for b in B if b["cat"] == t]
    rel = np.array([b["w"] * b["h"] / (b["W"] * b["H"]) for b in bs])
    asp = np.array([b["w"] / b["h"] for b in bs if b["h"] > 0])
    trunc = np.mean([b["x"] <= 1 or b["y"] <= 1 or b["x"] + b["w"] >= b["W"] - 1 or b["y"] + b["h"] >= b["H"] - 1
                     for b in bs])
    rr.append([T[t], f"{100 * np.median(rel):.2f}", f"{100 * np.percentile(rel, 25):.2f}–{100 * np.percentile(rel, 75):.2f}",
               f"{np.median([b['w'] * b['h'] for b in bs]):,.0f}", f"{np.median(asp):.2f}",
               f"{np.percentile(asp, 25):.2f}–{np.percentile(asp, 75):.2f}", pct(trunc)])
w(table(["術具", "画像に対する面積の中央値 %", "同・四分位範囲 %", "面積の中央値 [px²]", "縦横比 w/h の中央値",
         "縦横比の四分位範囲", "画像端に接する box %"], rr))
w("")
w("- 縦横比の四分位範囲が広い術具は、写る向き（縦長・横長）が大きく変わる。画像端に接する = box の辺が画像の端から 1 px 以内\n")

h(3, "1.4", "box の位置と品質")
cx = np.array([(b["x"] + b["w"] / 2) / b["W"] for b in B if b["w"] > 0 and b["h"] > 0])
cy = np.array([(b["y"] + b["h"] / 2) / b["H"] for b in B if b["w"] > 0 and b["h"] > 0])
trunc_all = sum(b["x"] <= 1 or b["y"] <= 1 or b["x"] + b["w"] >= b["W"] - 1 or b["y"] + b["h"] >= b["H"] - 1 for b in B)
degen = sum(not (b["w"] > 0 and b["h"] > 0) for b in B)
oob = sum(b["x"] < 0 or b["y"] < 0 or b["x"] + b["w"] > b["W"] + 1 or b["y"] + b["h"] > b["H"] + 1 for b in B)
mid = ((cx >= 1 / 3) & (cx <= 2 / 3) & (cy >= 1 / 3) & (cy <= 2 / 3)).mean()
w(table(["項目", "値"], [
    ["box の中心の中央値（x, y。画像幅・高さで 0〜1 に正規化）", f"({np.median(cx):.2f}, {np.median(cy):.2f})"],
    ["中心が画像中央の 1/3 × 1/3 にある box", f"{pct(mid)}%"],
    ["画像端に接する box（辺が端から 1 px 以内）", f"{trunc_all:,}（{pct(trunc_all / len(B))}%）"],
    ["幅か高さが 0 以下の box", f"{degen}"],
    ["画像の外にはみ出す box（1 px を超える）", f"{oob}"],
    ["iscrowd の box", f"{sum(b['crowd'] for b in B)}"],
], ["l", "r"]))
w("")
gx, gy = np.digitize(cx, [1 / 3, 2 / 3 + 1e-12]), np.digitize(cy, [1 / 3, 2 / 3 + 1e-12])
w("box の中心の位置（画像を 3 × 3 に分けた各区画に入る box の %。y は画像の上から下）\n")
w(table(["", "左", "中央", "右"], [[lab_] + [pct(((gy == r) & (gx == c)).mean()) for c in range(3)]
                                 for r, lab_ in enumerate(["上", "中央", "下"])], ["l", "r", "r", "r"]))
w("")

h(3, "1.5", "術具どうしの共起")
CO = pres.T.astype(int) @ pres.astype(int)
pairs = [(a, b) for a in range(15) for b in range(a + 1, 15)]


def pmi(a, b):
    return math.log2(CO[a, b] * N / (tool_pf[a] * tool_pf[b])) if CO[a, b] else None


def pair_row(a, b):
    return [f"{T[a]} + {T[b]}", f"{CO[a, b]:,}", pct(CO[a, b] / tool_pf[a]), pct(CO[a, b] / tool_pf[b]),
            f"{pmi(a, b):.2f}" if CO[a, b] else "—"]


ph_ = ["組（A + B）", "共に写るフレーム", "P(B \\| A) %", "P(A \\| B) %", "PMI [bit]"]
w("**共に写るフレームの多い組（上位 10）**\n")
w(table(ph_, [pair_row(a, b) for a, b in sorted(pairs, key=lambda x: -CO[x])[:10]]))
w("")
w("**PMI の大きい組（上位 10）**\n")
w(table(ph_, [pair_row(a, b) for a, b in sorted([p for p in pairs if CO[p]], key=lambda x: -pmi(*x))[:10]]))
w("")
zero_pairs = [p for p in pairs if CO[p] == 0]
w(f"- PMI = log2(P(A, B) / (P(A) P(B)))、フレーム単位、母集団 {N:,} フレーム。0 より大きいと偶然より多く同時に写る")
w(f"- 一度も同じフレームに写らない組は {len(zero_pairs)} / {len(pairs)} 組\n")
D.details("PMI の全表（15 × 15。· は同じフレームに一度も写らない組）",
          table(["術具"] + [T[t] for t in TC], [[T[a]] + ["—" if a == b else (f"{pmi(min(a, b), max(a, b)):.2f}" if CO[a, b] else "·")
                                               for b in TC] for a in TC]))
D.details("共に写るフレーム数の全表（15 × 15。対角はその術具の在フレーム）",
          table(["術具"] + [T[t] for t in TC], [[T[a]] + [f"{CO[a, b]:,}" for b in TC] for a in TC]))

h(3, "1.6", "術具と動画の結びつき")
rr = []
for t in TC:
    rs = np.array([pres[vid == v, t].mean() for v in videos if pres[vid == v, t].any()])
    rr.append([T[t], grp(t), f"{len(rs)}/15", pct(rs.min()), pct(np.median(rs)), pct(rs.max())])
w("術具が写る動画の中での在率（動画ごとの在フレーム / その動画の注釈フレーム）\n")
w(table(["術具", "群", "出現動画", "最小 %", "中央値 %", "最大 %"], rr))
w("")
w("- 中央値が 90% を超える術具は、写る動画ではほぼ全編に写っている（工程よりも動画に結びつく）\n")
D.details("動画 × 術具：在フレーム数",
          table(["動画", "フレーム"] + [T[t] for t in TC],
                [[v, f"{(vid == v).sum():,}"] + [f"{pres[vid == v, t].sum():,}" for t in TC] for v in videos]))

# ---------- §2 工程 ----------
h(2, "2", "工程")
w(f"母集団: 動画 01〜15 の工程 CSV {n_csv15} 本の全 {len(csv_rows):,} 行（術具注釈の有無を問わない）。"
  "§2.1 の一部の列だけ術具注釈のあるフレームで数える\n")
h(3, "2.1", "工程の分布と術具注釈の被覆")
ew_p = eff_weight([cov_all[p] for p in CAN])
rr = []
for j in range(nP):
    rr.append([phn(j), f"{cov_all[CAN[j]]:,}", pct(cov_all[CAN[j]] / len(csv_rows)), f"{ph_n[j]:,}",
               pct(ph_n[j] / cov_all[CAN[j]]), f"{cov_all[CAN[j]] - ph_n[j]:,}",
               len({r["video"] for r in csv_rows if r["phase"] == CAN[j]}), f"{ew_p[j]:.2f}"])
rr.append(["**計**", f"{len(csv_rows):,}", "100", f"{N:,}", pct(N / len(csv_rows)), f"{n_phase_only:,}", 15, ""])
w(table(["工程", "工程 CSV の行", "%", "術具注釈もある", "被覆 %", "工程だけ（術具未注釈）", "出現動画", "逆頻度の重み"], rr))
w("")
mx, mn = max(CAN, key=cov_all.get), min(CAN, key=cov_all.get)
low = sorted(range(nP), key=lambda j: ph_n[j] / cov_all[CAN[j]])[:3]
w(f"- 最多 / 最少 = {mx} / {mn} = {cov_all[mx] / cov_all[mn]:.1f} 倍。closure と dissection で "
  f"{pct((cov_all['closure'] + cov_all['dissection']) / len(csv_rows))}%")
w(f"- **被覆は工程で大きく違う**（{'、'.join(f'{CAN[j]} {pct(ph_n[j] / cov_all[CAN[j]])}%' for j in low)}）。"
  "§3 以降の割合はすべて術具注釈のあるフレームの中での値で、手術全体の値ではない")
w(f"- 逆頻度の重みは {ref('1.1')} と同じ定義（工程 CSV の行数から）\n")

h(3, "2.2", "動画 × 工程")
rr = []
for v in sorted({r["video"] for r in csv_rows}):
    rs = [r for r in csv_rows if r["video"] == v]
    c = collections.Counter(r["phase"] for r in rs)
    rr.append([v, vsplit[v], "、".join(sorted({r["clip"] for r in rs}))] + [f"{c[p]:,}" if c[p] else "0" for p in CAN]
              + [f"{len(rs):,}"])
D.details("動画 × 工程：工程 CSV の行数（クリップと公式 split つき）",
          table(["動画", "公式分割", "クリップ"] + [AB[p] for p in CAN] + ["計"], rr,
                ["l", "l", "l"] + ["r"] * (nP + 1)))
rr = [[v, vsplit[v]] + [f"{((vid == v) & (ph == j)).sum():,}" for j in range(nP)] + [f"{(vid == v).sum():,}"]
      for v in videos]
D.details("動画 × 工程：術具注釈のあるフレーム数", table(["動画", "公式分割"] + [AB[p] for p in CAN] + ["計"], rr))

prog = {}
for v in sorted({r["video"] for r in csv_rows}):
    rs = [r for r in csv_rows if r["video"] == v]
    for i, r in enumerate(rs):
        prog[r["fid"]] = i / (len(rs) - 1)
ph_prog = collections.defaultdict(list)
for r in csv_rows:
    ph_prog[r["phase"]].append(prog[r["fid"]])

h(3, "2.3", "工程の区間")
w(phase_seg_table(csv_rows, ph_prog))
w("")
w("- 区間長の単位は工程 CSV の行数。closure は長い区間で、incision・hemostasis は短い区間に細切れに現れる\n")

h(3, "2.4", "工程の遷移")
TR = trans_matrix(segments(csv_rows))
w("区間の切り替わり（同じクリップ内）。行が遷移元、列が遷移先\n")
w(trans_table(TR))
w("")
top_tr = sorted(((TR[a, b], a, b) for a in range(nP) for b in range(nP) if TR[a, b]), reverse=True)[:5]
w(f"- 遷移の総数 {TR.sum()}。多い順に " + "、".join(f"{CAN[a]} → {CAN[b]} {n}" for n, a, b in top_tr) + "\n")

h(3, "2.5", "時間方向の続きやすさとサンプリング間隔")
tm15 = temporal(csv_rows)
w(temporal_table(tm15))
w("")
w("- 隣り合う行 = 同じクリップの工程 CSV で連続する 2 行。フレーム番号の差が 1 でない行間（欠番）も含む\n")

ORD = write_order(D, csv_rows, ["2.6", "2.7", "2.8", "2.9", "2.10"], 3, vsplit)

# ---------- §3 術具 × 工程 ----------
h(2, "3", "術具 × 工程")
w(f"母集団: 術具注釈のある {N:,} フレーム。術具は最頻工程の順\n")
h(3, "3.1", "P(工程 | 術具)：各術具が各工程にどの割合で出現するか（在フレーム基準、行で 100%）")
rr = [[T[t], f"{tool_pf[t]:,}"] + [pct(PF[t, j] / tool_pf[t]) for j in range(nP)] for t in TO]
rr.append(["（参考）全フレームの工程比", f"{N:,}"] + [pct(ph_n[j] / N) for j in range(nP)])
w(table(["術具", "在フレーム"] + [phn(j) for j in range(nP)], rr))
w("")
big = np.argsort(-ph_n)[:2]
w(f"- 最下行は工程そのものの比率。{CAN[big[0]]}（{pct(ph_n[big[0]] / N)}%）と {CAN[big[1]]}（{pct(ph_n[big[1]] / N)}%）が大きいため、"
  f"P(工程 | 術具) はどの術具でもこの 2 工程に寄りやすい。**偏りの強さは {ref('3.5')} の lift で見る**")
w(f"- box 基準の同じ表と生の件数は {ref('3.15')}\n")

h(3, "3.2", "術具ごとの工程の集中度")
rr = []
for t in TO:
    dist = PF[t] / tool_pf[t]
    order = np.argsort(-dist)
    hh = H(PF[t])
    rr.append([T[t], grp(t), phn(order[0]), pct(dist[order[0]]), phn(order[1]), pct(dist[order[1]]),
               pct(dist[order[0]] + dist[order[1]]), f"{hh:.2f}", f"{hh / math.log2(nP):.2f}", f"{2 ** hh:.2f}",
               int((dist >= 0.01).sum())])
w(table(["術具", "群", "1 位の工程", "%", "2 位の工程", "%", "上位 2 の計 %", "エントロピー [bit]", "正規化エントロピー",
         "実効工程数 2^H", "1% 以上の工程数"], rr))
w("")
w(f"- エントロピーは P(工程 | 術具) の分布のもの。最大は log2(9) = {math.log2(9):.2f} bit、正規化エントロピー = H / log2(9)。"
  "実効工程数が 1 に近いほど 1 工程に専属\n")

h(3, "3.3", "P(術具 | 工程)：各工程に現れる術具の分布（在率）")
rr = [[phn(j), f"{ph_n[j]:,}"] + [pct(PF[t, j] / ph_n[j]) for t in TO] for j in range(nP)]
rr.append(["（参考）全体", f"{N:,}"] + [pct(tool_pf[t] / N) for t in TO])
w(table(["工程", "フレーム"] + [T[t] for t in TO], rr))
w("")
w(f"- 各セルは独立で、工程内の合計は 100% にならない。工程内構成比（合計 100%）は {ref('3.15')}\n")

h(3, "3.4", "工程ごとの術具の数と顔ぶれ")
rr = []
for j in range(nP):
    m = ph == j
    k = pres[m].sum(1)
    rr.append([phn(j), f"{ph_n[j]:,}", f"{k.mean():.2f}"] + [pct((k == c).mean()) for c in range(4)] + [pct((k >= 4).mean())])
w(table(["工程", "フレーム", "術具の種類数 / フレーム（平均）", "0 種 %", "1 種 %", "2 種 %", "3 種 %", "4 種以上 %"], rr))
w("")
rr = []
for j in range(nP):
    m = ph == j
    rate = PF[:, j] / ph_n[j]
    top = np.argsort(-rate)[:3]
    rr.append([phn(j), f"{int(nbox[m].sum()):,}", f"{nbox[m].sum() / ph_n[j]:.2f}", int((PF[:, j] > 0).sum()),
               "、".join(f"{T[t]} {pct(rate[t])}" for t in top if rate[t] > 0) or "—",
               f"{H(PF[:, j]):.2f}" if PF[:, j].sum() else "—"])
w(table(["工程", "box", "box / フレーム", "出現する術具の種類", "在率の上位 3（%）", "構成比のエントロピー [bit]"], rr,
        ["l", "r", "r", "r", "l", "r"]))
w("")

h(3, "3.5", "lift = P(術具 | 工程) / P(術具)")
p_t = tool_pf / N
rr = []
for t in TO:
    cells = []
    for j in range(nP):
        L = (PF[t, j] / ph_n[j]) / p_t[t]
        cells.append("0" if PF[t, j] == 0 else (f"**{L:.2f}**" if L >= 2 else f"{L:.2f}"))
    rr.append([T[t], grp(t)] + cells)
w(table(["術具", "群"] + [phn(j) for j in range(nP)], rr))
w("")
w("- 太字は lift ≥ 2（その工程で全体平均の 2 倍以上の在率）。† の工程はフレームが少なく lift が振れやすい\n")

h(3, "3.6", "一度も共に現れない組（術具 × 工程の 0 セル）")
rr = []
for t in TO:
    zs = [CAN[j] for j in range(nP) if PF[t, j] == 0]
    rr.append([T[t], grp(t), len(zs), "、".join(zs) if zs else "（なし）"])
w(table(["術具", "群", "0 セル数", "現れない工程"], rr, ["l", "l", "r", "l"]))
w("")
w("- 母集団は術具注釈のあるフレームだけなので、「0」は「注釈のある範囲で観測されない」の意味\n")

h(3, "3.7", "術具ごとの相互情報量 I(術具の在否; 工程)")
Hph = H(ph_n)
rr = []
MI = {}
for t in TO:
    Ht = Hb(p_t[t])
    Hcond = sum(ph_n[j] / N * Hb(PF[t, j] / ph_n[j]) for j in range(nP))
    MI[t] = Ht - Hcond
    rr.append([T[t], grp(t), f"{Ht:.3f}", f"{Hcond:.3f}", f"{MI[t]:.3f}", pct(MI[t] / Ht) if Ht else "—", pct(MI[t] / Hph)])
w(table(["術具", "群", "H(在否) [bit]", "H(在否 \\| 工程) [bit]", "I [bit]", "I / H(在否) %", "I / H(工程) %"], rr))
w("")
w(f"- H(工程) = {Hph:.3f} bit（術具注釈のある {N:,} フレームの工程分布）。"
  "I / H(在否) は「工程を知ると在否の不確かさが何割減るか」、I / H(工程) は「在否を知ると工程の不確かさが何割減るか」")
w("- 平滑化なしの plug-in 推定（同じ母集団でのエントロピー上界は `docs/stage0/A5_entropy_bound.md`）\n")

h(3, "3.8", "工程どうしの術具の似かより")
vec = np.array([PF[:, j] / ph_n[j] for j in range(nP)])
nrm = np.linalg.norm(vec, axis=1)
COS = np.array([[vec[a] @ vec[b] / (nrm[a] * nrm[b]) if nrm[a] and nrm[b] else np.nan for b in range(nP)] for a in range(nP)])
rr = [[phn(a)] + ["—" if a == b or np.isnan(COS[a, b]) else (f"**{COS[a, b]:.2f}**" if COS[a, b] >= 0.7 else f"{COS[a, b]:.2f}")
                  for b in range(nP)] for a in range(nP)]
w(table(["工程"] + [AB[p] for p in CAN], rr))
w("")
cpairs = sorted(((COS[a, b], a, b) for a in range(nP) for b in range(a + 1, nP) if not np.isnan(COS[a, b])), reverse=True)
w("- 各工程の在率ベクトル（" + ref("3.3") + " の行、15 次元）どうしのコサイン類似度。1 に近いほど術具の顔ぶれだけでは区別しにくい。"
  "太字は 0.7 以上。disinfection は術具が一度も写らないので定義できない（—）")
w("- 大きい順に " + "、".join(f"{CAN[a]} ⇄ {CAN[b]} {c:.2f}" for c, a, b in cpairs[:4]) + "\n")

h(3, "3.9", "術具の組み合わせ")
sets = [tuple(np.where(pres[i])[0]) for i in range(N)]
set_ph = collections.defaultdict(collections.Counter)
for s_, p_ in zip(sets, ph):
    set_ph[s_][p_] += 1
rr = []
for s_, n in sets_all.most_common(12):
    j, c = set_ph[s_].most_common(1)[0]
    rr.append([" + ".join(T[t] for t in s_) if s_ else "（術具なし）", f"{n:,}", phn(j), pct(c / n)])
w("**全体で多い組み合わせ（上位 12）**\n")
w(table(["術具の組み合わせ（フレーム内の術具集合）", "フレーム", "最多の工程", "その工程の %"], rr, ["l", "r", "l", "r"]))
w("")
rr = []
for j in range(nP):
    idx = np.where(ph == j)[0]
    cnt = collections.Counter(sets[i] for i in idx)
    for r, (k, c) in enumerate(cnt.most_common(5)):
        rr.append([phn(j) if r == 0 else "", r + 1, " + ".join(T[t] for t in k) if k else "（術具なし）", f"{c:,}",
                   pct(c / len(idx))])
    rr.append(["", "", f"（異なる組み合わせの数: {len(cnt)}）", "", ""])
D.details("工程ごとの組み合わせ（上位 5）", table(["工程", "順位", "術具の組み合わせ", "フレーム", "工程内 %"], rr,
                                                   ["l", "r", "l", "r", "r"]))

h(3, "3.10", "正解の注釈どうしで相手をどこまで言い当てられるか（参考値）")
w("モデルの結果ではなく、**正解注釈のあいだの単純規則**の値である。時間文脈は使わない（フレーム単独）。\n")
w("**術具集合 → 工程**\n")
pred_in = np.array([set_ph[s_].most_common(1)[0][0] for s_ in sets])
pred_lo = np.zeros(N, int)
unseen = np.zeros(N, bool)
for v in videos:
    tr = vid != v
    tab = collections.defaultdict(collections.Counter)
    for i in np.where(tr)[0]:
        tab[sets[i]][ph[i]] += 1
    maj = collections.Counter(ph[tr]).most_common(1)[0][0]
    for i in np.where(~tr)[0]:
        if sets[i] in tab:
            pred_lo[i] = tab[sets[i]].most_common(1)[0][0]
        else:
            pred_lo[i] = maj
            unseen[i] = True
Hcond_set = sum(sum(c.values()) / N * H(list(c.values())) for c in set_ph.values())
maj_all = collections.Counter(ph).most_common(1)[0][0]


def recall(pred):
    return [((pred == j) & (ph == j)).sum() / ph_n[j] for j in range(nP)]


def jacc(pred):
    return [((pred == j) & (ph == j)).sum() / ((pred == j) | (ph == j)).sum() for j in range(nP)]


r_in, r_lo = recall(pred_in), recall(pred_lo)
j_in, j_lo = jacc(pred_in), jacc(pred_lo)
w(table(["規則", "frame accuracy %", "macro recall %", "macro Jaccard %", "備考"], [
    ["常に最多工程（" + CAN[maj_all] + "）", pct((ph == maj_all).mean()), pct(1 / nP), pct(ph_n[maj_all] / N / nP), "基準"],
    ["術具集合ごとの最多工程（同じデータで当てる）", pct((pred_in == ph).mean()), pct(np.mean(r_in)), pct(np.mean(j_in)),
     f"楽観的。異なる術具集合 {len(set_ph):,} 種"],
    ["同上・動画単位の一つ抜き（LOVO）", pct((pred_lo == ph).mean()), pct(np.mean(r_lo)), pct(np.mean(j_lo)),
     f"未見の集合 {int(unseen.sum()):,} フレーム（{pct(unseen.mean())}%）は学習側の最多工程で埋める"],
], ["l", "r", "r", "r", "l"]))
w("")
w(f"- 相互情報量 I(工程; 術具集合) = {Hph - Hcond_set:.3f} bit（H(工程) {Hph:.3f} bit の "
  f"{pct((Hph - Hcond_set) / Hph)}%。plug-in 推定で、集合の種類が多いぶん上振れする）")
w("- Jaccard・recall はプールしたフレームでの値で、プロジェクトの判定（動画単位・折り）とは数え方が違う\n")
D.details("工程ごとの recall と Jaccard",
          table(["工程", "フレーム", "recall %（同データ）", "Jaccard %（同データ）", "recall %（LOVO）", "Jaccard %（LOVO）"],
                [[phn(j), f"{ph_n[j]:,}", pct(r_in[j]), pct(j_in[j]), pct(r_lo[j]), pct(j_lo[j])] for j in range(nP)]))
w("**工程 → 術具の在否**\n")
w("スコア = 学習側で数えた P(術具 | 工程)。そのスコアで在否を順位づけたときの AUROC（0.5 が無情報）\n")
rr = []
AUC = {}
for t in TO:
    y = pres[:, t]
    s_in = np.array([PF[t, j] / ph_n[j] for j in ph])
    s_lo = np.zeros(N)
    for v in videos:
        tr = vid != v
        rate = {j: (pres[tr & (ph == j), t].sum() / max(1, (tr & (ph == j)).sum())) for j in range(nP)}
        s_lo[~tr] = [rate[j] for j in ph[~tr]]

    def auc(sc):
        r = rankdata(sc)
        npos, nneg = y.sum(), (~y).sum()
        return (r[y].sum() - npos * (npos + 1) / 2) / (npos * nneg)
    AUC[t] = (auc(s_in), auc(s_lo))
    rr.append([T[t], grp(t), f"{tool_pf[t]:,}", f"{AUC[t][0]:.3f}", f"{AUC[t][1]:.3f}"])
w(table(["術具", "群", "在フレーム", "AUROC（同データ）", "AUROC（LOVO）"], rr))
w("")

h(3, "3.11", "動画間の一貫性")
vph = {j: {vid[i] for i in np.where(ph == j)[0]} for j in range(nP)}
rr = []
for t in TO:
    cells = []
    for j in range(nP):
        k = len({vid[i] for i in np.where((ph == j) & pres[:, t])[0]})
        cells.append(f"{k}/{len(vph[j])}" if k else "0")
    rr.append([T[t], grp(t)] + cells)
w("術具 × 工程：その工程でその術具が写る動画の数 / その工程がある動画の数\n")
w(table(["術具", "群"] + [phn(j) for j in range(nP)], rr))
w("")
w("- 分母は術具注釈のあるフレームでその工程が 1 フレーム以上ある動画の数。分子は在フレームが 1 以上の動画の数\n")
rr = []
DOMV = {}
for t in TO:
    j = dom[t]
    rs = np.array([pres[(ph == j) & (vid == v), t].mean() for v in sorted(vph[j])])
    DOMV[t] = rs
    rr.append([T[t], grp(t), phn(j), len(rs), pct(PF[t, j] / ph_n[j]), pct(rs.min()), pct(np.median(rs)),
               pct(rs.max()), int((rs == 0).sum())])
w("最頻工程での在率の動画間のばらつき\n")
w(table(["術具", "群", "最頻工程", "動画数", "プールした在率 %", "最小 %", "中央値 %", "最大 %", "在率 0 の動画数"], rr))
w("")

h(3, "3.12", "手術の進行度と術具・工程")
for f in frames:
    f["prog"] = prog[f["fid"]]
bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0001]
bl = ["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"]
bi = np.digitize(np.array([f["prog"] for f in frames]), bins) - 1
rr = [[T[t], grp(t)] + [pct(pres[bi == b, t].mean()) for b in range(5)] for t in TO]
rr.append(["（フレーム数）", ""] + [f"{(bi == b).sum():,}" for b in range(5)])
w("進行度の区間ごとの術具の在率 %\n")
w(table(["術具", "群"] + bl, rr))
w("")
w("進行度の区間ごとの工程の比率 %（列で 100%）\n")
w(table(["工程"] + bl, [[phn(j)] + [pct(((bi == b) & (ph == j)).sum() / (bi == b).sum()) for b in range(5)]
                        for j in range(nP)]))
w("")

h(3, "3.13", "工程の切り替わりと術具集合の変化")
order = sorted(range(N), key=lambda i: (frames[i]["clip"], csv_pos[frames[i]["fid"]]))
adj = [(a, b) for a, b in zip(order, order[1:])
       if frames[a]["clip"] == frames[b]["clip"] and csv_pos[frames[b]["fid"]] - csv_pos[frames[a]["fid"]] == 1]
chg_p = np.array([ph[a] != ph[b] for a, b in adj])
chg_s = np.array([sets[a] != sets[b] for a, b in adj])
w(table(["隣接フレームの対", "対の数", "術具集合が変わる対", "術具集合が変わる %"],
        [[name, f"{m.sum():,}", f"{(m & chg_s).sum():,}", pct((m & chg_s).sum() / m.sum())]
         for name, m in [("工程が変わる", chg_p), ("工程が同じ", ~chg_p)]]))
w("")
w("- 隣接 = 同じクリップの工程 CSV で連続する 2 行が、どちらも術具注釈を持つ対（間に未注釈の行を挟む対は除く）。"
  f"工程の切り替わり {TR.sum()} 回（{ref('2.4')}）のうち {int(chg_p.sum())} 回がこの対で捉えられる\n")
pcnt = collections.Counter((ph[a], ph[b]) for (a, b), c in zip(adj, chg_p) if c)
pchg = collections.Counter((ph[a], ph[b]) for (a, b), c, s_ in zip(adj, chg_p, chg_s) if c and s_)
rr = []
SWAP = {}
for (a, b), c in sorted(pcnt.items(), key=lambda x: -x[1]):
    ap = [(a_, b_) for (a_, b_), cp in zip(adj, chg_p) if cp and ph[a_] == a and ph[b_] == b]
    ins = collections.Counter(t for a_, b_ in ap for t in set(sets[b_]) - set(sets[a_]))
    out = collections.Counter(t for a_, b_ in ap for t in set(sets[a_]) - set(sets[b_]))
    SWAP[(a, b)] = (c, ins, out)
    rr.append([f"{CAN[a]} → {CAN[b]}", c, pchg[(a, b)], pct(pchg[(a, b)] / c),
               "、".join(f"{T[t]}({n})" for t, n in ins.most_common(3)) or "—",
               "、".join(f"{T[t]}({n})" for t, n in out.most_common(3)) or "—"])
w(table(["工程の切り替わり", "対の数", "術具集合が変わる", "%", "現れる術具（上位 3、回数）", "消える術具（上位 3、回数）"],
        rr, ["l", "r", "r", "r", "l", "l"]))
w("")

h(3, "3.14", "工程ごとの box の大きさ")
rel_ph = collections.defaultdict(list)
for b in B:
    rel_ph[csv_phase[b["fid"]]].append(b["w"] * b["h"] / (b["W"] * b["H"]))
rr = []
for j in range(nP):
    v_ = np.array(rel_ph[CAN[j]])
    rr.append([phn(j), f"{len(v_):,}"] + ([f"{100 * v_.mean():.2f}", f"{100 * np.median(v_):.2f}",
                                            f"{100 * np.percentile(v_, 25):.2f}–{100 * np.percentile(v_, 75):.2f}"]
                                           if len(v_) else ["—", "—", "—"]))
w(table(["工程", "box", "画像に対する面積の平均 %", "中央値 %", "四分位範囲 %"], rr))
w("")
w("- 全術具の box をまとめた値。工程ごとに写る術具の顔ぶれが違うので、術具ごとの大きさ（§1.3）の違いも含む\n")

h(3, "3.15", "付表")
D.details("P(工程 | 術具)：box 基準（行で 100%）",
          table(["術具", "box"] + [phn(j) for j in range(nP)],
                [[T[t], f"{tool_bx[t]:,}"] + [pct(BX[t, j] / tool_bx[t]) for j in range(nP)] for t in TO]))
rr = [[T[t]] + [f"{PF[t, j]:,}" for j in range(nP)] + [f"{tool_pf[t]:,}"] for t in TO]
rr.append(["**工程のフレーム数**"] + [f"{ph_n[j]:,}" for j in range(nP)] + [f"{N:,}"])
D.details("生の在フレーム数（術具 × 工程）", table(["術具"] + [phn(j) for j in range(nP)] + ["計"], rr))
rr = [[T[t]] + [f"{BX[t, j]:,}" for j in range(nP)] + [f"{tool_bx[t]:,}"] for t in TO]
rr.append(["**計**"] + [f"{BX[:, j].sum():,}" for j in range(nP)] + [f"{tool_bx.sum():,}"])
D.details("生の box 数（術具 × 工程）", table(["術具"] + [phn(j) for j in range(nP)] + ["計"], rr))
for name, M in [("在フレーム基準", PF), ("box 基準", BX)]:
    rr = [[phn(j), f"{M[:, j].sum():,}"] + [pct(M[t, j] / M[:, j].sum()) if M[:, j].sum() else "—" for t in TO]
          for j in range(nP)]
    D.details(f"工程内構成比：{name}（工程ごとに 100%）", table(["工程", "総和"] + [T[t] for t in TO], rr))

# ---------- §4 手 ----------
h(2, "4", "手")
w(f"母集団: 術具注釈のある {N:,} フレーム。手の注釈は raw02（{ref('0.1')}）\n")
h(3, "4.1", "手の注釈の件数")
rr = []
for k in range(4):
    cnt = {s: sum(1 for i in np.where(spl == s)[0] for kk_, _ in hb.get(frames[i]["fid"], []) if kk_ == k) for s in SPLITS}
    rr.append([HN[k]] + [f"{cnt[s]:,}" for s in SPLITS] + [f"{sum(cnt.values()):,}", f"{hpres[:, k].sum():,}",
                                                            pct(hpres[:, k].mean())])
rr.append(["**計**"] + [f"{int(hcnt[spl == s].sum()):,}" for s in SPLITS] + [f"{int(hcnt.sum()):,}",
                                                                           f"{int((hcnt > 0).sum()):,}", pct((hcnt > 0).mean())])
w(table(["手のクラス", "train", "val", "test", "box 計", "写るフレーム", "在率 %"], rr))
w("")
out_clips = sorted({x.rsplit("_", 1)[0] for x in raw_imgs} - {r["clip"] for r in csv_rows})
w(f"- 計の行の「写るフレーム」は手が 1 つ以上写るフレーム。手 box が 0 個のフレームは {nzh}"
  "（手が写っていないのか未注釈なのかは注釈からは区別できない）。同じフレーム・クラス・座標の重複 box は "
  f"{n_hdup} 個（そのまま数える）")
w(f"- raw02 全体は {len(raw_imgs):,} 画像・手 box {n_raw_box:,} 個で、主な母集団の外のフレームも含む"
  f"（術具未注釈のフレーム、工程 CSV の無いクリップ {', '.join(out_clips)}）。本書はそのうち主な母集団の分だけを数える\n")

h(3, "4.2", "工程ごとの手")
rr = []
for j in list(range(nP)) + [None]:
    m = np.ones(N, bool) if j is None else ph == j
    own, oth = hpres[m, :2].any(1), hpres[m, 2:].any(1)
    rr.append([phn(j) if j is not None else "**全体**", f"{m.sum():,}", pct((hcnt[m] > 0).mean()), pct(own.mean()),
               pct(oth.mean())] + [pct(hpres[m, k].mean()) for k in range(4)]
              + [f"{hcnt[m].mean():.2f}", pct(((hcnt[m] > 0) & pres[m].any(1)).mean())])
w(table(["工程", "フレーム", "手あり %", "自分の手あり %", "他者の手あり %"] + [f"{x} %" for x in HN]
        + ["手の box / フレーム", "手と術具が同時に写る %"], rr))
w("")
w("- 各列は、その工程のフレームのうち該当する手が 1 つ以上写るフレームの割合\n")

h(3, "4.3", "手と術具の空間的な近さ")


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    u = a[2] * a[3] + b[2] * b[3] - inter
    return inter / u if u > 0 else 0.0


def cdist(a, b):
    return math.hypot(a[0] + a[2] / 2 - b[0] - b[2] / 2, a[1] + a[3] / 2 - b[1] - b[3] / 2)


maxiou, mind = [], []
n_tb = n_ov = n_near = 0
fcontact = np.zeros(N, bool)
for i, f in enumerate(frames):
    hs = [b for _, b in hb.get(f["fid"], [])]
    for tb in f["boxes"]:
        n_tb += 1
        if not hs:
            maxiou.append(0.0)
            continue
        mi_ = max(iou(tb, x) for x in hs)
        md_ = min(cdist(tb, x) for x in hs)
        maxiou.append(mi_)
        mind.append(md_)
        n_ov += mi_ > 0.1
        n_near += md_ < 0.15 * DIAG
        fcontact[i] |= mi_ > 0.1
maxiou = np.array(maxiou)
w(table(["項目", "値"], [
    ["術具 box", f"{n_tb:,}"],
    ["手と重なる術具 box（いずれかの手との IoU > 0.1）", f"{n_ov:,}（{pct(n_ov / n_tb)}%）"],
    ["手に近い術具 box（最も近い手との中心距離 < 0.15 × 画像の対角）", f"{n_near:,}（{pct(n_near / n_tb)}%）"],
    ["手との IoU の最大値の平均（手の無いフレームの box は 0）", f"{maxiou.mean():.3f}"],
    ["最も近い手までの中心距離の中央値（手のあるフレームの box）",
     f"{np.median(mind):.0f} px（対角の {np.median(mind) / DIAG:.3f}）"],
], ["l", "r"]))
w("")
edges = [(0, 0, "0（重ならない・手なし）"), (0, 0.1, "0 < IoU ≤ 0.1"), (0.1, 0.3, "0.1 < IoU ≤ 0.3"),
         (0.3, 0.5, "0.3 < IoU ≤ 0.5"), (0.5, 1.0, "0.5 < IoU")]
rr = []
for lo, hi, name in edges:
    m = maxiou == 0 if hi == 0 else (maxiou > lo) & (maxiou <= hi)
    rr.append([name, f"{m.sum():,}", pct(m.mean())])
w("術具 box ごとの、手との IoU の最大値の分布\n")
w(table(["IoU の最大値", "術具 box", "%"], rr))
w("")
rr = []
ftool = pres.any(1)
for j in range(nP):
    m = (ph == j) & ftool
    rr.append([phn(j), f"{m.sum():,}", pct(fcontact[m].mean()) if m.sum() else "—"])
w("工程ごとの、手と重なる術具があるフレームの割合（術具が 1 つ以上写るフレームが分母）\n")
w(table(["工程", "術具が写るフレーム", "手と重なる術具があるフレーム %"], rr))
w("")

# ---------- §5 公式 split ----------
h(2, "5", "公式 split")
w(f"母集団: 術具注釈のある {N:,} フレーム。公式 split（train / val / test）ごとの分布の記述で、"
  "現行の判定（動画単位の五分割）とは別の区切りである\n")
h(3, "5.1", "split × 工程")
rr = [[phn(j)] + [f"{((spl == s) & (ph == j)).sum():,}（{pct(((spl == s) & (ph == j)).sum() / (spl == s).sum())}）"
                  for s in SPLITS] for j in range(nP)]
w(table(["工程"] + [f"{s}（%）" for s in SPLITS], rr, ["l", "r", "r", "r"]))
w("")
zero_cells = [(CAN[j], s) for j in range(nP) for s in SPLITS if ((spl == s) & (ph == j)).sum() == 0]
w("- 術具注釈のあるフレームが 0 の組: " + ("、".join(f"{p} × {s}" for p, s in zero_cells) or "なし") + "\n")
h(3, "5.2", "split × 術具")
SB = {s: nbox[spl == s].sum(0) for s in SPLITS}
SV = {s: {t: len({v for v in videos if vsplit[v] == s and nbox[vid == v, t].sum() > 0}) for t in range(15)} for s in SPLITS}
rr = [[T[t], grp(t)] + [("**0**" if SB[s][t] == 0 else f"{SB[s][t]:,}") + f"（{SV[s][t]}）" for s in SPLITS] for t in TC]
w(table(["術具", "群"] + [f"{s} の box（出現動画）" for s in SPLITS], rr, ["l", "l", "r", "r", "r"]))
w("")
w("- box が 0 の組は太字。その split ではその術具のクラスごとの AP が定義できない\n")
h(3, "5.3", "split 間の分布のずれ")
SP = {s: [((spl == s) & (ph == j)).sum() for j in range(nP)] for s in SPLITS}
JS = {(a, b): (js(SB[a], SB[b]), js(SP[a], SP[b])) for a, b in [("train", "val"), ("train", "test"), ("val", "test")]}
w(table(["比較", "術具の box 分布", "工程の分布"], [[f"{a} ⇄ {b}", f"{x:.3f}", f"{y:.3f}"] for (a, b), (x, y) in JS.items()]))
w("")
w("- Jensen–Shannon ダイバージェンス（bit、0 で同じ分布、最大 1）。術具は box 数、工程は術具注釈のあるフレーム数の分布\n")

# ---------- 付録 ----------
OA = "`experiments/analysis/annotations_eda/REPORT.md`"
OD = "`experiments/analysis/dataset_eda/REPORT.md`"
h(2, "A", "付録 A：旧文書との対応")
w("本書は次の 3 文書をまとめ直したもの。旧文書は記録として元の場所に残してある。値はすべて本書のスクリプトで計算し直した\n")
w(f"- 旧 A = {OA}（2026-06-20。§1〜§27）")
w(f"- 旧 D = {OD}（§0〜§8）")
w("- 旧 S = 本ファイルの旧版（2026-10-20 作成。コミット前に本書へ統合した。§0〜§9）\n")
MAP = [
    ("A §0 要約・§5.3 解釈・§6 ドメイン特性まとめ", "要点", "書き直し。旧モデルに触れる文は外した"),
    ("A §1.1 ファイル構成", "0.1", "使うファイルだけ"),
    ("A §1.2 split と規模 / D §0 規模 / D §7 カバレッジ", "0.3", ""),
    ("A §1.3 フレーム共起 / A §20 ラベル濃度 / D §4 フレーム構成", "1.2", ""),
    ("A §2 術具 15 クラス分布 / D §1 術具クラス分布", "1.1", ""),
    ("A §2.1 bbox サイズ / A §24 検出難易度プロキシ", "1.3", "旧 A §2.1 は train だけ。本書は split ごとと計"),
    ("A §15 bbox 幾何・データ品質", "1.4", "サンプリング間隔は §2.5"),
    ("A §13 術具共起 / D §4b 術具ペア共起", "1.5", ""),
    ("A §10 クラス↔動画の集中度", "1.1・5.2", "出現動画・最も多い動画の占有"),
    ("A §4.1 工程分布 / D §2 工程分布 / A §25 工程だけのフレーム / S §1", "2.1", ""),
    ("A §4.2 区間 / D §5a / S §8.1", "2.3", ""),
    ("A §4.3 遷移 / D §5b / S §8.2", "2.4", ""),
    ("A §19 時間予測性 / A §15 サンプリング間隔 / D §5 工程数 / clip", "2.5", ""),
    ("A §21 工程順序の一貫性 / S §9", "2.6〜2.10", "§2.10 の先頭行が旧 A §21 の数え方"),
    ("A §5.2 / S §3.1", "3.1", ""),
    ("D §3b 工程特異性 / S §3.5", "3.2", "正規化エントロピーの列が旧 D §3b"),
    ("A §5.1 / D §3a / S §4.1", "3.3", "旧 D §3a は分母が違う（付録 C）"),
    ("S §4.4", "3.4", ""),
    ("S §5", "3.5〜3.7", ""),
    ("A §12 工程の混同度", "3.8", "全対の行列にした"),
    ("A §20 シーンテンプレート / S §4.5", "3.9", ""),
    ("S §6", "3.10", ""),
    ("S §7", "3.11・1.6・2.2", ""),
    ("S §8.3〜§8.5", "3.12・3.13", ""),
    ("A §24 工程別の術具スケール", "3.14", ""),
    ("S §3.2〜§3.4・§4.2〜§4.3", "3.15", ""),
    ("A §3 手 4 クラス / D §6 手", "4.1", "手の出所を raw02 に変えた（付録 C）"),
    ("A §14 手の解析 / A §22 手の左右・自他", "4.2", "同上"),
    ("A §18 手–術具の空間接触", "4.3", "同上"),
    ("A §9 split 間の分布シフト / D §7b", "5", ""),
    ("A §23 推奨クラス重み", "1.1・2.1", "「逆頻度の重み」の列。「推奨」としては載せず、件数から決まる値として載せた"),
]
w(table(["旧文書の節", "本書", "備考"], [[a, "要点" if b == "要点" else "・".join(ref(x) for x in b.replace("〜", "・").split("・"))
                                          if "〜" not in b else f"{ref(b.split('〜')[0])}〜{ref(b.split('〜')[1])}", c]
                                     for a, b, c in MAP], ["l", "l", "l"]))
w("")

h(2, "B", "付録 B：掲載しなかったもの")
w(table(["旧文書の節", "内容", "理由"], [
    ["A §11", "術具の在否から工程を当てる精度（公式 split）と、その解釈", "二塔・界面分離型より前の構成（B2a・T1a）と学習結果（S4 の精度）を前提にした分析。"
     f"注釈だけで決まる部分は {ref('3.10')}（動画一つ抜き）と {ref('3.7')} の相互情報量で置き換わる"],
    ["A §7・§16・§26", "研究上の含意・実験への示唆", "旧構成（B2a・T1a・S4・TeCNO）の結果と判断を前提にしている"],
    ["D §8", "STEP B（multitask 結合）への含意", "旧構成の設計判断。標的群・陰性対照群は現行の `context/conventions.md#det_groups` に従って各表の「群」列に載せた"],
    ["A §9〜§25 の「実験判断」", "各節末の設計上の判断", "同上。各節の注釈の集計値だけを残した"],
    ["A §8・§17・§27", "成果物一覧（図・CSV・JSON）", f"本書は md 1 本で完結させ、再現方法は {ref('D')} に置いた。旧文書の図は旧文書の場所に残っている"],
], ["l", "l", "l"]))
w("")

h(2, "C", "付録 C：旧文書と値が違う箇所")
AG = old_hand_agreement()
w(f"同じ母集団・同じ定義の値は旧文書と一致する（例: 術具 box の最多 / 最少 {tool_bx[TC[0]] / tool_bx[TC[-1]]:.1f} 倍、"
  f"工程の最多 / 最少 {cov_all[mx] / cov_all[mn]:.1f} 倍、隣り合う行が同じ工程である割合 {pct(tm15['self'])}%、"
  f"旧 A §21 の順守率 {ORD['adh']['clip'][0]:.3f}、画像端に接する box {pct(trunc_all / len(B))}%）。違うのは次の箇所である\n")
w(table(["箇所", "旧文書", "本書", "理由"], [
    ["手の注釈の出所（§4 全体）", "A §3・§14・§18・§22、D §6 は `egosurgery_tool_hand/` の手",
     f"raw02（{ref('0.1')}）",
     "2026-07-29 に raw02 を正本と決めた（`docs/experiment_log.md`）。"
     + ("手の box 数はクラス × split の単位で 4 クラス版と raw02 で同じだが、どのフレームに付くかが違う。" if all(AG[s][3] for s in SPLITS) else "")
     + "さらに A §14・§18・§22 が使った 19 クラス版 "
     "`instances_*.json` は手の box を画像 ID で結合しており、4 クラス版（`egosurgery_tool_hand/{split}.json`）とファイル名で照合すると手の box が一致するフレームは "
     + "、".join(f"{s} {pct(AG[s][0] / AG[s][1])}%（{AG[s][0]:,}/{AG[s][1]:,}）" for s in SPLITS) + "。4 クラス版は画像が "
     + "、".join(f"{s} {AG[s][1] - AG[s][2]}" for s in SPLITS if AG[s][1] != AG[s][2]) + " 枚少なく、その分だけ ID がずれる"],
    ["工程ごとの手あり率（§4.2）", "A §14 は dressing 0.10 など", f"dressing {pct((hcnt[ph == ci['dressing']] > 0).mean())}% など",
     "出所の違いに加え、A §14 は train の手だけを読み、val・test のフレームを「手なし」として分母に入れていた"],
    ["A §14 の「平均手数」", "手のクラスの種類数の平均", "§4.2 は手の box 数の平均", "定義を変えた"],
    ["術具の面積（§1.3）", "D §1 の「平均面積(px²)」", "「面積の中央値」", "D §1 の値は実装上は中央値だった（`np.median`）。値は同じ"],
    ["P(術具 \\| 工程)（§3.3）", f"D §3a は分母が box 1 個以上のフレーム（{N - nz:,}）", f"分母は術具注釈のある全フレーム（{N:,}）",
     f"box 0 個の {nz} フレームを含めるかの違い"],
    ["術具の無いフレーム", f"D §4 は {n_phase_only + nz:,}", f"工程だけ {n_phase_only:,}（§2.1）+ box 0 個 {nz}（§0.2）", "D §4 は 2 つを合わせて数えていた"],
    ["COCO の面積区分（§1.3）", "A §2.1 は train だけ", "split ごとと計", "train の行は旧値と同じ"],
], ["l", "l", "l", "l"]))
w("")

h(2, "D", "付録 D：再現")
w("```bash\n.venv/bin/python docs/analysis_scripts/phase_tool_annotation_stats.py\n```\n")
w(f"- 本書と別冊 [`{os.path.basename(OUT2)}`]({os.path.basename(OUT2)}) を書く。読み取り専用で、`data/` には書き込まない。数秒で終わる")
w("- 引数で出力先を変えられる（1 つ目が本書、2 つ目が別冊）\n")

# ---------- 冒頭（要点・目次・索引） ----------
hd = sum(TR[ci[a], ci[b]] for a, b in [("dissection", "hemostasis"), ("hemostasis", "dissection")])
head = []
hw = head.append
hw("# EgoSurgery 注釈の EDA：術具・工程・手（動画 01〜15）\n")
hw("- 生成: 集計スクリプト `docs/analysis_scripts/phase_tool_annotation_stats.py`（読み取り専用。数値はすべて注釈からの実測で、推定・補完はしない）")
hw(f"- 対象: 動画 01〜15。工程 CSV {n_csv15} 本（{len(csv_rows):,} 行）、そのうち術具注釈のある {N:,} フレーム（術具 box {int(nbox.sum()):,}、"
   f"手 box {int(hcnt.sum()):,}）")
hw(f"- 3 つの EDA 文書（{OA}、{OD}、本ファイルの旧版）を 1 本にまとめたもの。対応は {ref('A')}、載せなかった節は {ref('B')}")
hw(f"- 動画 17〜21 の工程 CSV は別冊 [`{os.path.basename(OUT2)}`]({os.path.basename(OUT2)})\n")
hw("## 目次\n")
parts = [s for s in D.toc if s[0] == 2 and not s[1].isalpha()]
rr = []
for lv, sid, title in parts:
    subs = [x for x in D.toc if x[0] == 3 and x[1].split(".")[0] == sid]
    rr.append([f"[{sid}. {title}](#{aid(sid)})",
               " · ".join(f"[{x[1]}](#{aid(x[1])}) {x[2].split('：')[0]}".replace("|", "\\|") for x in subs)])
rr.append(["付録", " · ".join(f"[{title}](#{aid(sid)})" for lv, sid, title in D.toc if sid.isalpha())])
hw(table(["部", "節"], rr, ["l", "l"]))
hw("")

hw("## 要点\n")
t_ = {n: T.index(n) for n in T}
sk, sy, sc, nh, bp = (t_[x] for x in ["Skewer", "Syringe", "Scalpel", "Needle Holders", "Bipolar Forceps"])
ds = [t for t in TO if PF[t, ci["dissection"]] / tool_pf[t] >= 0.75]
ds_lift = [(PF[t, ci["dissection"]] / ph_n[ci["dissection"]]) / p_t[t] for t in ds]
neg = [t for t in range(15) if T[t] in NEGCTL]
mg = t_["Mouth Gag"]
mg_rs = np.array([pres[vid == v, mg].mean() for v in videos if pres[vid == v, mg].any()])
ag = ORD
oth_ph = [hpres[ph == j, 2:].any(1).mean() for j in range(nP)]
hw(f"""**術具**（{ref('1')}）
1. 長い裾の分布。box の最多 / 最少は {T[TC[0]]} / {T[TC[-1]]} = {tool_bx[TC[0]] / tool_bx[TC[-1]]:.1f} 倍。1 フレームの術具は平均 {kk.mean():.2f} 種
   （最大 {kk.max()} 種）で、術具の無いフレームは {nz}（{ref('1.1')}・{ref('1.2')}）
2. box は大きく、画像端で切れやすい。COCO の large が {pct(sum(b['area'] >= 96 ** 2 for b in B) / len(B))}%、画像端に接する box が
   {pct(trunc_all / len(B))}%、中心が画像中央 1/9 にある box は {pct(mid)}% だけ（{ref('1.3')}・{ref('1.4')}）
3. Mouth Gag は {len(mg_rs)}/15 動画にだけ出て、その動画では注釈フレームの {pct(mg_rs.min())}〜{pct(mg_rs.max())}% に写る。
   工程よりも動画に結びつく術具（{ref('1.6')}）

**工程**（{ref('2')}）
4. closure と dissection で {pct((cov_all['closure'] + cov_all['dissection']) / len(csv_rows))}%、最多 / 最少 = {cov_all[mx] / cov_all[mn]:.1f} 倍。
   術具注釈の被覆は工程で偏る（{'、'.join(f'{CAN[j]} {pct(ph_n[j] / cov_all[CAN[j]])}%' for j in low)}。{ref('2.1')}）
5. 工程は行単位ではほとんど変わらない。隣り合う行の {pct(tm15['self'])}% が同じ工程で、境目の行は {pct(tm15['boundary'])}%（{ref('2.5')}）
6. 並びは大筋で参照順に沿うが往復が多い。初出の順序が参照順と一致するのは {ag['nmatch']}/{len(ag['VV'])} 動画、位置で比べた順守率は
   {min(a for a, _ in ag['adh'].values()):.3f}〜{max(a for a, _ in ag['adh'].values()):.3f}。一方、区間の遷移で参照順に前向きなのは
   {ag['fw']}/{ag['tot_tr']}（{ag['fw'] / ag['tot_tr']:.3f}）。後戻り {ag['back']} 回の多くは
   {'、'.join(f'{a} → {b} {n} 回（{k} 動画）' for a, b, n, k in ag['topback'])}。closure が現れる {ag['n_close']} 動画のうち
   {ag['after_k']} 動画で closure の後に別の工程へ戻る。closure の無い動画は {'、'.join(v for v, _ in ag['noclose'])}
   （{'、'.join(sorted({p for _, p in ag['noclose']}))} で終わる）（{ref('2.6')}〜{ref('2.10')}）

**術具 × 工程**（{ref('3')}）
7. ほぼ 1 工程に専属する術具がある（P(工程 | 術具)、{ref('3.1')}）。{T[nh]} → closure {pct(PF[nh, ci['closure']] / tool_pf[nh])}%、
   {T[sk]} → design {pct(PF[sk, ci['design']] / tool_pf[sk])}%、{T[bp]} → hemostasis {pct(PF[bp, ci['hemostasis']] / tool_pf[bp])}%、
   {T[sc]} → incision {pct(PF[sc, ci['incision']] / tool_pf[sc])}%、{T[sy]} → anesthesia {pct(PF[sy, ci['anesthesia']] / tool_pf[sy])}%。
   逆向きの在率（{ref('3.3')}）も anesthesia の {T[sy]} {pct(PF[sy, ci['anesthesia']] / ph_n[ci['anesthesia']])}%、
   incision の {T[sc]} {pct(PF[sc, ci['incision']] / ph_n[ci['incision']])}%、design の {T[sk]} {pct(PF[sk, ci['design']] / ph_n[ci['design']])}% と高い
8. dissection に専属の術具は無い。在フレームの 75% 以上が dissection にある {len(ds)} 術具（{'・'.join(T[t] for t in ds)}）は
   lift {min(ds_lift):.2f}〜{max(ds_lift):.2f} だが、dissection での在率は最大でも {pct(max(PF[t, ci['dissection']] for t in ds) / ph_n[ci['dissection']])}%（{ref('3.3')}・{ref('3.5')}）
9. 陰性対照群は工程をまたいで広く出る。実効工程数 {min(2 ** H(PF[t]) for t in neg):.2f}〜{max(2 ** H(PF[t]) for t in neg):.2f}
   （{ref('3.2')}）。{T[mg]} の動画一つ抜きの AUROC は {AUC[mg][1]:.3f}（{ref('3.10')}）
10. 術具の顔ぶれが似ていて区別しにくい工程の組は {'、'.join(f'{CAN[a]} ⇄ {CAN[b]}（{c:.2f}）' for c, a, b in cpairs[:2])}（{ref('3.8')}）。
    dissection ⇄ hemostasis は区間の遷移でも {hd} 回往復する（{ref('2.4')}）
11. 術具集合だけで工程はかなり決まる。集合ごとの最多工程を当てる規則で frame accuracy {pct((pred_in == ph).mean())}%（同じデータ）、
    {pct((pred_lo == ph).mean())}%（動画一つ抜き）。常に {CAN[maj_all]} と答える基準は {pct((ph == maj_all).mean())}%（{ref('3.10')}）
12. 工程が変わると術具集合もほぼ変わる。隣り合う注釈フレームで工程が変わる対の {pct((chg_p & chg_s).sum() / chg_p.sum())}% で
    術具集合が変わる（工程が同じ対では {pct((~chg_p & chg_s).sum() / (~chg_p).sum())}%。{ref('3.13')}）

**手**（{ref('4')}）
13. 手は {pct((hcnt > 0).mean())}% のフレームに写り、自分の手は {pct(hpres[:, :2].any(1).mean())}%、他者の手は {pct(hpres[:, 2:].any(1).mean())}%。
    他者の手の在率は工程で {pct(min(oth_ph))}〜{pct(max(oth_ph))}% と変わる（{ref('4.2')}）
14. 術具 box の {pct(n_ov / n_tb)}% が手と重なる（IoU > 0.1）（{ref('4.3')}）

**注意**
- 旧 EDA の手の値は出所の違う注釈から計算されていて、本書とは合わない（{ref('C')}）
- 公式 split では {'、'.join(f'{p} × {s}' for p, s in zero_cells)} の術具注釈フレームが 0（{ref('5.1')}）
""")

hw("## 知りたいことから引く\n")
hw(table(["知りたいこと", "節"], [
    ["ある術具はどの工程に出るか", f"{ref('3.1')}（割合）・{ref('3.5')}（偏り）・{ref('3.6')}（出ない工程）"],
    ["ある工程にはどの術具が写るか", f"{ref('3.3')}（在率）・{ref('3.4')}（数と顔ぶれ）・{ref('3.9')}（組み合わせ）"],
    ["術具と工程の結びつきの強さ", f"{ref('3.2')}・{ref('3.7')}・{ref('3.10')}"],
    ["結びつきは動画をまたいで安定か", f"{ref('3.11')}・{ref('1.6')}"],
    ["術具・工程の数の偏り", f"{ref('1.1')}・{ref('2.1')}"],
    ["工程の時間構造（区間・遷移・順序）", f"{ref('2.3')}〜{ref('2.10')}"],
    ["box の大きさ・位置・品質", f"{ref('1.3')}・{ref('1.4')}・{ref('3.14')}"],
    ["術具どうしの共起", f"{ref('1.5')}"],
    ["手の在否と手–術具の近さ", f"{ref('4.2')}・{ref('4.3')}"],
    ["公式 split ごとの偏り", f"{ref('5')}"],
], ["l", "l"]))
hw("")

open(OUT, "w").write("\n".join(head + D.md) + "\n")
print("wrote", OUT, len(head) + len(D.md))

# =====================================================================
# 別冊：動画 17〜21 の工程 CSV
# =====================================================================
E = Doc()
ew, eh = E.w, E.h
main = os.path.basename(OUT)
clips17 = sorted({r["clip"] for r in rows17}, key=lambda c: (c.split("_")[0], int(c.split("_")[1])))
v17 = sorted({r["video"] for r in rows17})
cov17 = collections.Counter(r["phase"] for r in rows17)

eh(2, "0", "対象のファイル")
rr = []
for c in clips17:
    g = [r for r in rows17 if r["clip"] == c]
    st = [b["idx"] - a["idx"] for a, b in zip(g, g[1:])]
    rr.append([c.split("_")[0], c, f"{len(g):,}", f"{g[0]['idx']}–{g[-1]['idx']}", sum(s > 1 for s in st),
               "、".join(AB[p] for p in CAN if any(r["phase"] == p for r in g))])
ew(table(["動画", "クリップ", "行数", "フレーム番号の範囲", "番号が飛ぶ箇所", "現れる工程"], rr, ["l", "l", "r", "r", "r", "l"]))
ew("")
gaps = {v: sorted(set(range(1, max(int(c.split("_")[1]) for c in clips17 if c.startswith(v + "_")) + 1))
                  - {int(c.split("_")[1]) for c in clips17 if c.startswith(v + "_")}) for v in v17}
ew(f"- 動画 {len(v17)} 本・クリップ {len(clips17)} 本・{len(rows17):,} 行。術具・手の box は無いので、工程だけで決まる量だけを載せる")
ew("- クリップ番号の欠け: " + ("、".join(f"動画 {v} はクリップ " + "・".join(f"{v}_{k}" for k in g) + " が無い"
                                      for v, g in gaps.items() if g) or "なし")
   + "。動画 17 はクリップ 1 本で、フレーム番号 " + f"{min(r['idx'] for r in rows17 if r['video'] == '17')} から始まる")
ew(f"- 工程の略号と参照順は本編と同じ（[本編 §0.4]({main}#{aid('0.4')})）\n")
bnd = []
for v in v17:
    cs = [c for c in clips17 if c.startswith(v + "_")]
    for a, b in zip(cs, cs[1:]):
        pa = [r for r in rows17 if r["clip"] == a][-1]["phase"]
        pb = [r for r in rows17 if r["clip"] == b][0]["phase"]
        bnd.append([v, f"{a} → {b}", pa, pb, "同じ工程" if pa == pb else ("前向き" if ci[pb] > ci[pa] else "**後戻り**")])
n_back_b = sum(r[4] == "**後戻り**" for r in bnd)
E.details(f"クリップの境目（{len(bnd)} か所。前のクリップの最後の工程 → 次のクリップの最初の工程）",
          table(["動画", "境目", "前の最後", "次の最初", "参照順で"], bnd, ["l", "l", "l", "l", "l"]))
ew(f"- クリップの境目 {len(bnd)} か所のうち {n_back_b} か所で、次のクリップの最初の工程が参照順で前に戻る。"
   "クリップ番号の順が時間の順と一致しない可能性がある\n")

eh(2, "1", "工程の分布（動画 01〜15 との比較）")
rr = [[p, f"{cov17[p]:,}", pct(cov17[p] / len(rows17)), len({r['video'] for r in rows17 if r['phase'] == p}),
       f"{cov_all[p]:,}", pct(cov_all[p] / len(csv_rows)), len({r['video'] for r in csv_rows if r['phase'] == p})] for p in CAN]
rr.append(["**計**", f"{len(rows17):,}", "100", len(v17), f"{len(csv_rows):,}", "100", 15])
ew(table(["工程", "17〜21 の行", "%", "出現動画", "01〜15 の行", "%", "出現動画"], rr))
ew("")
ew(f"- 分布のずれ（Jensen–Shannon ダイバージェンス）: {js([cov17[p] for p in CAN], [cov_all[p] for p in CAN]):.3f} bit\n")
rr = []
for v in v17:
    c = collections.Counter(r["phase"] for r in rows17 if r["video"] == v)
    rr.append([v] + [f"{c[p]:,}" if c[p] else "0" for p in CAN] + [f"{sum(c.values()):,}"])
E.details("動画 × 工程：行数", table(["動画"] + [AB[p] for p in CAN] + ["計"], rr))

eh(2, "2", "工程の区間")
ew(phase_seg_table(rows17))
ew("")
eh(2, "3", "工程の遷移")
TR17 = trans_matrix(segments(rows17))
ew("区間の切り替わり（同じクリップ内）。行が遷移元、列が遷移先\n")
ew(trans_table(TR17))
ew("")
ew(f"- 遷移の総数 {TR17.sum()}\n")
eh(2, "4", "時間方向の続きやすさとサンプリング間隔")
tm17 = temporal(rows17)
ew(table(["指標", "17〜21", "01〜15"], [
    ["隣り合う行が同じ工程である割合 %", pct(tm17["self"]), pct(tm15["self"])],
    ["工程の境目にある行の割合 %", pct(tm17["boundary"]), pct(tm15["boundary"])],
    ["直前の工程から次の工程を当てる割合 %（1 次マルコフ）", pct(tm17["markov"]), pct(tm15["markov"])],
    ["行間のフレーム番号の差：中央値 / 最頻値 / 90% 点", f"{tm17['st_med']} / {tm17['st_mode']} / {tm17['st_p90']}",
     f"{tm15['st_med']} / {tm15['st_mode']} / {tm15['st_p90']}"],
    ["行間のフレーム番号の差が 1 の割合 %", pct(tm17["st_one"]), pct(tm15["st_one"])],
    ["1 クリップに現れる工程の種類（平均）", f"{np.mean(tm17['kinds']):.1f}", f"{np.mean(tm15['kinds']):.1f}"],
], ["l", "r", "r"]))
ew("")
ORD17 = write_order(E, rows17, ["5", "6", "7", "8", "9"], 2)

hd17 = []
hw = hd17.append
hw("# EgoSurgery 工程注釈の EDA（動画 17〜21）\n")
hw("- 生成: 集計スクリプト `docs/analysis_scripts/phase_tool_annotation_stats.py`（本編と同じスクリプト。読み取り専用）")
hw(f"- 対象: `data/annotations/egosurgery_phase/` のうち動画 17〜21 の工程 CSV {len(clips17)} 本（{len(rows17):,} 行）")
hw(f"- 本編（動画 01〜15、術具・工程・手）は [`{main}`]({main})\n")
hw("## 目次\n")
hw(" · ".join(f"[{sid}. {title.split('（')[0]}](#{aid(sid)})" for _, sid, title in E.toc) + "\n")
hw("## 要点\n")
hw(f"""1. 動画 {len(v17)} 本・クリップ {len(clips17)} 本・{len(rows17):,} 行（動画 01〜15 の {pct(len(rows17) / len(csv_rows))}% の量）。
   クリップ番号に欠けがあり（{'、'.join(f'動画 {v}: ' + '・'.join(f'{v}_{k}' for k in g) for v, g in gaps.items() if g)}）、
   動画 17 は途中のフレーム番号から始まる 1 クリップだけ。クリップの境目 {len(bnd)} か所のうち {n_back_b} か所で参照順が前に戻る（{ref('0')}）。
   **クリップを番号順につないだ並び（{ref('5')}〜{ref('9')}）は、時間の順になっていない可能性がある**
2. 工程の分布は 01〜15 と違う（{ref('1')}）。dissection {pct(cov17['dissection'] / len(rows17))}%（01〜15 は {pct(cov_all['dissection'] / len(csv_rows))}%）、
   closure {pct(cov17['closure'] / len(rows17))}%（同 {pct(cov_all['closure'] / len(csv_rows))}%）
3. 隣り合う行が同じ工程である割合は {pct(tm17['self'])}%（01〜15 は {pct(tm15['self'])}%）。行間のフレーム番号の差が 1 の割合は
   {pct(tm17['st_one'])}%（同 {pct(tm15['st_one'])}%）（{ref('4')}）
4. 初出の順序が参照順と一致するのは {ORD17['nmatch']}/{len(ORD17['VV'])} 動画。区間の遷移のうち参照順に前向きなのは
   {ORD17['fw']}/{ORD17['tot_tr']}（{ORD17['fw'] / ORD17['tot_tr']:.3f}。01〜15 は {ORD['fw'] / ORD['tot_tr']:.3f}）（{ref('6')}・{ref('9')}）
""")
open(OUT2, "w").write("\n".join(hd17 + E.md) + "\n")
print("wrote", OUT2, len(hd17) + len(E.md))
