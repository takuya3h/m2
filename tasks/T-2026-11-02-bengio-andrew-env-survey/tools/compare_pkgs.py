"""Task C-1 の比較（読むだけ）。importlib.metadata の「名前==版」の列を両ホストで比べる。--selftest で一行を書き換えた写しを入れる。"""
import json, sys
S = "experiments/analysis/bengio_andrew_env_survey/start/"
out = {}
for venv, f in [(".venv", "reldetr_main_venv.json"), (".venv-relation-detr", "reldetr_main.json")]:
    a = json.load(open(S + "andrew_" + f))["venv"]["package_list"]
    b = list(json.load(open(S + "bengio_" + f))["venv"]["package_list"])
    if "--selftest" in sys.argv:
        b[0] = b[0] + ".post999"
    da = {l.split("==")[0]: l.split("==")[1] for l in a}; db = {l.split("==")[0]: l.split("==")[1] for l in b}
    out[venv] = {"andrew": len(a), "bengio": len(b),
                 "andrew_only": sorted(set(da) - set(db)), "bengio_only": sorted(set(db) - set(da)),
                 "version_differ": {k: [da[k], db[k]] for k in sorted(set(da) & set(db)) if da[k] != db[k]}}
print(json.dumps(out, ensure_ascii=False))
