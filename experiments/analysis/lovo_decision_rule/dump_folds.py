"""既存の LOVO スクリプトを改変せずに走らせ、fold ごとの素の値を取り出す。

報告書 §3 の表は要約値しか残していない（fold ごとの値が残るのは §3.9 の acc/edit のみ）。
非独立を踏まえた判定則は fold ごとの対の差を要する。したがって素の値を復元する。

**既存スクリプトは 1 バイトも変更しない。** source をそのまま exec し、
実行後の名前空間から `res` と `vids` を読むだけである。
"""
import argparse, io, json, sys, contextlib
from pathlib import Path


def normalize(res, vids):
    """{arm: {vid: metrics}} へ揃える。台本ごとに向きと入れ物が違う。"""
    out = {}
    keys = list(res.keys())
    vid_first = bool(keys) and set(str(k) for k in keys) == set(str(v) for v in vids)
    if vid_first:
        for v in keys:
            for arm, m in res[v].items():
                out.setdefault(str(arm), {})[str(v)] = m
    else:
        for arm in keys:
            for v, m in res[arm].items():
                out.setdefault(str(arm), {})[str(v)] = m
    clean = {}
    for arm, per_vid in out.items():
        clean[arm] = {}
        for v, m in per_vid.items():
            if isinstance(m, list):
                names = [k for k in m[0] if isinstance(m[0][k], (int, float))]
                m = {k: sum(r[k] for r in m) / len(m) for k in names}
            clean[arm][v] = {k: v2 for k, v2 in m.items() if isinstance(v2, (int, float))}
    assert clean, "res が空"
    return clean


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("script_args", nargs="*")
    a = ap.parse_args()

    src = Path(a.script).read_text(encoding="utf-8")
    ns = {"__name__": "__main__", "__file__": a.script}
    saved = sys.argv
    sys.argv = [a.script] + a.script_args
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(src, a.script, "exec"), ns)
    finally:
        sys.argv = saved
        Path(a.log).write_text(buf.getvalue(), encoding="utf-8")

    if "res" not in ns or "vids" not in ns:
        raise SystemExit(f"UNSUPPORTED: {a.script} は res/vids を持たない（別扱いが要る）")
    payload = {
        "script": a.script,
        "script_args": a.script_args,
        "vids": [str(v) for v in ns["vids"]],
        "folds": normalize(ns["res"], ns["vids"]),
    }
    Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {a.script} -> {a.out}  arms={len(payload['folds'])} vids={len(payload['vids'])}")


if __name__ == "__main__":
    main()
