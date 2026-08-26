"""R2 の素材: 動画の部分集合を種固定で選び直し、一つ抜き検証をやり直す。

**なぜ再学習が要るのか。** fold の間の相関は、学習側の 14 動画が重なることから生じる。
15 個の対の差だけを見ても、共有される成分と fold 固有の成分は分離できない。
分離するには、学習側が実際に違う状態を複数作って測るしかない。

**既存スクリプトは 1 バイトも変更しない。** 作業ディレクトリを足場へ移すことで、
台本が相対パスで読み込む共通ヘルパだけが、動画の部分集合を尊重する版に差し替わる。
足場のヘルパと原本の違いは clips() の 9 行だけである。
"""
import argparse, json, os, random, subprocess, sys
from pathlib import Path

REPO = Path("/home/ubuntu/slocal2/m2")


def subsets(n_videos, m, reps, seed):
    """種を固定して部分集合を選ぶ。同じ種なら同じ列が出る。"""
    rng = random.Random(seed)
    vids = [f"{i:02d}" for i in range(1, n_videos + 1)]
    return [sorted(rng.sample(vids, m)) for _ in range(reps)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dumper", required=True)
    ap.add_argument("--scaffold", required=True)
    ap.add_argument("--reps", type=int, default=24)
    ap.add_argument("--m", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    sets = subsets(15, a.m, a.reps, a.seed)
    out = {"script": a.script, "m": a.m, "reps": a.reps, "seed": a.seed,
           "subsets": sets, "replicates": []}
    tmp = Path(a.scaffold) / f"_rep_{Path(a.out).stem}.json"
    log = Path(a.scaffold) / f"_rep_{Path(a.out).stem}.log"
    for i, sub in enumerate(sets):
        env = dict(os.environ)
        env["LOVO_VIDEO_SUBSET"] = ",".join(sub)
        env["PYTHONPATH"] = str(REPO / "src")
        cmd = [sys.executable, a.dumper, str(REPO / a.script),
               "--out", str(tmp), "--log", str(log)]
        r = subprocess.run(cmd, cwd=a.scaffold, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            out["replicates"].append({"i": i, "subset": sub, "error": r.stderr[-800:]})
            print(f"rep {i} FAIL rc={r.returncode}", flush=True)
        else:
            out["replicates"].append({"i": i, "subset": sub,
                                      "folds": json.loads(tmp.read_text())["folds"]})
            print(f"rep {i} ok", flush=True)
        Path(a.out).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in out["replicates"] if "folds" in r)
    print(f"DONE {a.script} -> {a.out}  成功 {ok}/{a.reps}")


if __name__ == "__main__":
    main()
