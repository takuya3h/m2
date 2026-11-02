"""Task D の突き合わせ（読むだけ）。両ホストの data_inventory の出力と、記録（inputs_inventory.json、image_input_lock.json）を照合する。
--selftest: 記録の画像の一つの要約値を一文字変えた値と比べ、不一致になることを示す。"""
import json, sys
SP = sys.argv[1]
OUT = "experiments/analysis/bengio_andrew_env_survey/d/"
A = json.load(open(SP + "/andrew_data.json")); B = json.load(open(SP + "/bengio_data.json"))
inv = json.load(open("experiments/analysis/tower_reselect_search_dlsta/inputs_inventory.json"))
lock = json.load(open("experiments/analysis/tower_reselect_search_dlsta/image_input_lock.json"))
res = {}
# 画像: B1 と動画ごと
rec_b1 = next(i for i in inv["items"] if i["item"].startswith("B1"))
res["b1"] = {"andrew": {k: A["b1"][k] for k in ("count", "bytes", "sha256")}, "bengio": {k: B["b1"][k] for k in ("count", "bytes", "sha256")},
             "record": {"count": rec_b1["count"], "sha256": rec_b1["digest"], "note": rec_b1["note"]},
             "per_video_mismatch": {v: [A["b1"]["per_video"][v]["sha256"], B["b1"]["per_video"][v]["sha256"], inv["images_per_video"][v]["sha256"]]
                                    for v in A["b1"]["per_video"] if len({A["b1"]["per_video"][v]["sha256"], B["b1"]["per_video"][v]["sha256"], inv["images_per_video"][v]["sha256"]}) != 1}}
# 固定記録の 17,233 行（selected と counterpart）
def lock_check(img, flip=False):
    bad, n = [], 0
    for x in lock:
        for role in ("selected", "counterpart"):
            p = x[role]
            if not p: continue
            n += 1
            want = x["sha256"][role]
            if flip and n == 1: want = ("0" if want[0] != "0" else "1") + want[1:]
            if img.get(p) != want: bad.append([p, img.get(p), want])
    return n, bad
for h, D in (("andrew", A), ("bengio", B)):
    n, bad = lock_check(D["image_sha256"])
    res[f"lock_{h}"] = {"checked": n, "mismatch_or_missing": len(bad), "examples": bad[:5], "bytes": D["lock"]["bytes"], "missing": D["lock"]["missing"][:5]}
res["lock_selftest_flip_one"] = len(lock_check(B["image_sha256"], flip=True)[1])
res["image_host_mismatch"] = sorted(p for p in set(A["image_sha256"]) | set(B["image_sha256"]) if A["image_sha256"].get(p) != B["image_sha256"].get(p))
# 工程 CSV
ca = {e["path"].split("/")[-1]: e for e in A["phase_csv"]["files"]}; cb = {e["path"].split("/")[-1]: e for e in B["phase_csv"]["files"]}
res["phase_csv"] = {"andrew_files": len(ca), "bengio_files": len(cb), "rows_v15": [A["phase_csv"]["rows_v15"], B["phase_csv"]["rows_v15"]],
                    "phase_only_v15": [A["phase_csv"]["phase_only_v15"], B["phase_csv"]["phase_only_v15"]],
                    "differ": sorted(k for k in set(ca) | set(cb) if ca.get(k, {}).get("sha256") != cb.get(k, {}).get("sha256")),
                    "bytes": [sum(e["bytes"] for e in ca.values()), sum(e["bytes"] for e in cb.values())],
                    "git_blobs": {k: e.get("git_blob") for k, e in cb.items()}}
# 個別のファイル
rows = []
for g in B["files"]:
    for ea, eb in zip(A["files"][g], B["files"][g]):
        assert ea["path"].replace(A["root"], "") == eb["path"].replace(B["root"], "") or ea["path"] == eb["path"], (ea["path"], eb["path"])
        r = {"group": g, "path": eb["path"].replace("/home/ubuntu/", "~/"),
             "andrew": {k: ea.get(k) for k in ("exists", "is_link", "real", "bytes", "sha256", "git_blob", "images", "annotations", "missing_images", "frames", "missing_image_path")},
             "bengio": {k: eb.get(k) for k in ("exists", "is_link", "real", "bytes", "sha256", "git_blob", "images", "annotations", "missing_images", "frames", "missing_image_path")}}
        r["judge"] = ("一致" if ea.get("exists") and eb.get("exists") and ea["sha256"] == eb["sha256"] else
                      "両方に無い" if not ea.get("exists") and not eb.get("exists") else
                      "andrew だけ" if ea.get("exists") and not eb.get("exists") else
                      "bengio だけ" if eb.get("exists") and not ea.get("exists") else "不一致")
        rows.append(r)
res["files"] = rows
res["dirs"] = {"andrew": A["dirs"], "bengio": B["dirs"]}
if "--selftest" in sys.argv:
    print(json.dumps({"lock_selftest_flip_one": res["lock_selftest_flip_one"]}))
else:
    import os; os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(OUT + "data_compare.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res["b1"], ensure_ascii=False)[:600])
    for h in ("andrew", "bengio"): print(h, {k: v for k, v in res[f"lock_{h}"].items() if k != "examples"})
    print("selftest", res["lock_selftest_flip_one"], "image_host_mismatch", len(res["image_host_mismatch"]))
    print("phase_csv", {k: v for k, v in res["phase_csv"].items() if k != "git_blobs"})
    from collections import Counter
    print(Counter((r["group"], r["judge"]) for r in rows))
    for r in rows:
        if r["judge"] != "一致": print(r["judge"], r["group"], r["path"], r["andrew"].get("bytes"), r["bengio"].get("bytes"), r["bengio"].get("real") if r["bengio"].get("is_link") else "")
