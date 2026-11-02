"""Task B の比較（読むだけ）。andrew main を基準に bengio main と重ねの BODY を三分類し、
bengio の中身が third_party_snapshot/Bengio の tar に在るかをファイルごとに書く。"""
import hashlib, io, json, sys, tarfile
D = "experiments/analysis/bengio_andrew_env_survey/b/"

def classify(a, b):
    only_a = sorted(set(a) - set(b)); only_b = sorted(set(b) - set(a))
    diff = sorted(k for k in set(a) & set(b) if a[k][1] != b[k][1])
    same = sorted(k for k in set(a) & set(b) if a[k][1] == b[k][1])
    return only_a, only_b, diff, same

def snapshot_members(path):
    out = {}
    with tarfile.open(path) as t:
        for m in t.getmembers():
            if m.isfile():
                out[m.name] = hashlib.sha256(t.extractfile(m).read()).hexdigest()
    return out

def main(selftest=False):
    A = json.load(open(D + "andrew_main_files.json"))
    B = json.load(open(D + "bengio_main_files.json"))
    O = json.load(open(D + "bengio_overlay_files.json"))
    a, b, o = A["included"], B["included"], O["included"]
    if selftest:  # 陽性対照: 1 バイト変えた写し
        b = dict(b); k = sorted(set(a) & set(b))[0]; b[k] = [b[k][0], hashlib.sha256(b"x").hexdigest(), 0]
    only_a, only_b, diff, same = classify(a, b)
    snap = snapshot_members("third_party_snapshot/Bengio/Relation-DETR/project_files.tar.gz")
    snap_by_hash = {}
    for n, h in snap.items():
        snap_by_hash.setdefault(h, []).append(n)
    def norm(n):  # tar の名前の先頭（Relation-DETR/ など）を除いた候補
        return [n.split("/", i)[-1] for i in range(0, n.count("/") + 1)]
    def in_snapshot(rel, h):
        names = snap_by_hash.get(h, [])
        exact = [n for n in names if rel in norm(n)]
        return {"same_content_same_path": bool(exact), "same_content_any_path": names,
                "path_in_snapshot_other_content": [n for n in snap if rel in norm(n) and snap[n] != h]}
    rows = []
    for k in only_a: rows.append({"path": k, "class": "andrew_only", "andrew": a[k], "bengio": None})
    for k in only_b: rows.append({"path": k, "class": "bengio_only", "andrew": None, "bengio": b[k], "snapshot": in_snapshot(k, b[k][1])})
    for k in diff: rows.append({"path": k, "class": "differ", "andrew": a[k], "bengio": b[k], "snapshot": in_snapshot(k, b[k][1])})
    oa, ob, od, osame = classify(a, o)
    res = {"counts": {"andrew_files": len(a), "bengio_files": len(b), "union": len(set(a) | set(b)),
                      "andrew_only": len(only_a), "bengio_only": len(only_b), "differ": len(diff), "same": len(same)},
           "rows": rows,
           "overlay_vs_andrew": {"andrew_only": oa, "overlay_only": ob, "differ": od, "same": len(osame)},
           "snapshot_members": snap,
           "excluded": {"andrew": A["excluded"], "bengio": B["excluded"], "overlay": O["excluded"]},
           "checkpoints": {"andrew": A["hashed_excluded"], "bengio": B["hashed_excluded"],
                           "differ": sorted(k for k in set(A["hashed_excluded"]) | set(B["hashed_excluded"])
                                            if A["hashed_excluded"].get(k, [0, 0])[1] != B["hashed_excluded"].get(k, [0, 1])[1])}}
    return res

if __name__ == "__main__":
    st = "--selftest" in sys.argv
    r = main(st)
    if st:
        print(json.dumps(r["counts"]))
    else:
        json.dump(r, open(D + "reldetr_compare.json", "w"), ensure_ascii=False, indent=1)
        print(json.dumps(r["counts"]), json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in r["overlay_vs_andrew"].items()}))
        print("checkpoints differ:", r["checkpoints"]["differ"], len(r["checkpoints"]["andrew"]), len(r["checkpoints"]["bengio"]))
        print("snapshot members:", len(r["snapshot_members"]))
        for x in r["rows"]:
            s = x.get("snapshot", {})
            print(x["class"], x["path"], (x["andrew"] or [None])[0], (x["bengio"] or [None])[0],
                  "snap_same" if s.get("same_content_same_path") else ("snap_other_path" if s.get("same_content_any_path") else ("snap_path_other_content" if s.get("path_in_snapshot_other_content") else ("NOT_IN_SNAPSHOT" if s else ""))))
