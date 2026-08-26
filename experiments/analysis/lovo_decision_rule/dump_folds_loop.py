"""ループの各周回で結果を捨てる台本から、fold ごとの素の値を取り出す。

受容野や凍結源の台本は LAGSETS / SRCS のループを回し、**周回ごとに r0/r1 を上書きする。**
実行後の名前空間には最後の 1 周分しか残らない。

台本は各周回の末尾で print を呼ぶ。**その瞬間の名前空間には、その周回の値が揃っている。**
そこで名前空間へ自前の print を置き、呼ばれた時点の入れ物を写し取る。
**台本は 1 バイトも変更しない。** print が globals 経由で解決されることだけを使う。
"""
import argparse, builtins, copy, io, json, sys

METRIC_KEY = "phase_accuracy"


def is_fold_map(v):
    """{vid: {metric: float}} の形か。"""
    if not isinstance(v, dict) or not v:
        return False
    for inner in v.values():
        if not isinstance(inner, dict) or METRIC_KEY not in inner:
            return False
    return True


def is_nested(v):
    """{key: {vid: {metric: float}}} の形か。"""
    if not isinstance(v, dict) or not v:
        return False
    return all(is_fold_map(inner) for inner in v.values())


def label_of(ns, counter):
    parts = []
    for k in ("name", "tag", "kind"):
        v = ns.get(k)
        if isinstance(v, str) and v:
            parts.append(v)
    return " ".join(parts) if parts else f"周回{counter}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()

    src = open(a.script, encoding="utf-8").read()
    ns = {"__name__": "__main__", "__file__": a.script}
    buf = io.StringIO()
    snaps = []          # (label, varname, subkey|None, {vid: metrics})
    state = {"n": 0}

    def hook(*args, **kw):
        state["n"] += 1
        lbl = label_of(ns, state["n"])
        for var, val in list(ns.items()):
            if var.startswith("__"):
                continue
            if is_fold_map(val):
                snaps.append((lbl, var, None, copy.deepcopy(val)))
            elif is_nested(val):
                for sub, inner in val.items():
                    snaps.append((lbl, var, str(sub), copy.deepcopy(inner)))
        builtins.print(*args, **kw)

    ns["print"] = hook
    saved = sys.stdout
    sys.stdout = buf
    try:
        exec(compile(src, a.script, "exec"), ns)
    finally:
        sys.stdout = saved
        open(a.log, "w", encoding="utf-8").write(buf.getvalue())

    # 同じ周回で print が複数回呼ばれると同じ入れ物を何度も拾う。中身で畳む。
    folds = {}
    for lbl, var, sub, val in snaps:
        arm = f"{lbl}|{var}" + (f"|{sub}" if sub is not None else "")
        clean = {str(v): {k: x for k, x in m.items() if isinstance(x, (int, float))}
                 for v, m in val.items()}
        prev = folds.get(arm)
        if prev is not None and prev != clean:
            # 同名で中身が違うなら周回が衝突している。番号を付けて両方残す。
            i = 2
            while f"{arm}#{i}" in folds and folds[f"{arm}#{i}"] != clean:
                i += 1
            arm = f"{arm}#{i}"
        folds[arm] = clean
    vids = sorted({v for m in folds.values() for v in m})
    json.dump({"script": a.script, "vids": vids, "folds": folds},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    builtins.print(f"OK {a.script} -> {a.out}  arms={len(folds)} vids={len(vids)}")


if __name__ == "__main__":
    main()
