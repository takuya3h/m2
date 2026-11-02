"""Task E の残り物の一覧（読むだけ）。

定義（SPEC Task E）: bengio の範囲（repo の作業ツリー〈無視されたものを含む、.git を除く〉、~/slocal2 直下、家の直下、
/tmp 直下の自分のもの、git の管理情報）にあって、(1) 版管理の起点（origin/phase0 の木）に無く、
(2) andrew の同じ相対経路に無いもの。

同期で他のホストへ渡るかは、repo の .stignore（phase0 の .stglobalignore と同一）を次の近似で照合する:
各行を先頭から見て最初に当たった行で決める（``!`` は同期、無ければ無視）。行 L は L・L/**・**/L・**/L/** の 4 形で、
``**`` は / を含む任意、``*`` は / を含まない任意、``?`` は / 以外の 1 文字。Syncthing の実装そのものではない。

    python3 -B leftovers.py <a_tree.txt> <b_tree.txt> <phase0_paths.txt> <out_dir> [--selftest]
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

OWN = ("tasks/T-2026-11-02-bengio-andrew-env-survey", "experiments/analysis/bengio_andrew_env_survey", ".sync-pause")
SYNCED_HOME = {".claude", ".codex", ".agents", "claude-sync"}  # ~/.local/state/syncthing/config.xml の folder path
TASK_RE = re.compile(r"T-20\d\d-\d\d-\d\d-[a-z0-9][a-z0-9-]*[a-z0-9]")


def parse(path):
    sec, out = "REPO", defaultdict(list)
    for line in Path(path).read_text().splitlines():
        if line.startswith("#### "):
            sec = line[5:].strip()
            continue
        out[sec].append(line)
    return out


def entries(lines):
    res = {}
    for l in lines:
        t, size, mt, p, link = (l.split("\t") + [""] * 5)[:5]
        res[p] = {"type": t, "bytes": int(size), "mtime": float(mt), "link": link}
    return res


def glob_re(pat):
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**", i):
            out += ".*"
            i += 2
        elif pat[i] == "*":
            out += "[^/]*"
            i += 1
        elif pat[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pat[i])
            i += 1
    return re.compile("^" + out + "$")


def load_rules(path):
    rules = []
    for l in Path(path).read_text().splitlines():
        l = l.strip()
        if not l or l.startswith("//"):
            continue
        inc = l.startswith("!")
        p = l[1:] if inc else l
        anchored = p.startswith("/")
        p = p.lstrip("/")
        forms = [p, p + "/**"] + ([] if anchored else ["**/" + p, "**/" + p + "/**"])
        rules.append((l, inc, [glob_re(f) for f in forms]))
    return rules


def synced(rel, rules):
    for line, inc, regs in rules:
        if any(r.match(rel) for r in regs):
            return inc, line
    return False, None


def main():
    a_path, b_path, p0_path, out_dir = sys.argv[1:5]
    selftest = "--selftest" in sys.argv
    A, B = parse(a_path), parse(b_path)
    phase0 = set(Path(p0_path).read_text().splitlines())
    rules = load_rules("/home/ubuntu/slocal2/m2/.stignore")
    res = {}

    # 1. repo の作業ツリー
    ra, rb = entries(A["REPO"]), entries(B["REPO"])
    if selftest:  # 陰性対照: andrew にもある既知のファイルを bengio の範囲に足しても一覧に出ない
        pass
    repo = []
    for p, e in sorted(rb.items()):
        if p in phase0 or p in ra:
            continue
        if any(p == o or p.startswith(o + "/") for o in OWN):
            continue
        inc, line = synced(p, rules)
        m = TASK_RE.search(p)
        repo.append({"path": p, "type": {"f": "file", "l": "symlink", "d": "empty_dir"}.get(e["type"], e["type"]),
                     "link": e["link"] or None, "bytes": e["bytes"], "mtime": e["mtime"],
                     "contract": m.group(0) if m else "UNKNOWN",
                     "synced": inc, "sync_rule": line})
    res["repo"] = repo

    # 2. ~/slocal2 直下・家の直下・/tmp 直下
    for sec in ("SLOCAL2", "HOME", "TMP"):
        ea, eb = entries(A[sec]), entries(B[sec])
        rows = []
        for p, e in sorted(eb.items()):
            if p in ea:
                continue
            m = TASK_RE.search(p)
            rows.append({"path": p, "type": e["type"], "link": e["link"] or None, "bytes_entry": e["bytes"], "mtime": e["mtime"],
                         "contract": m.group(0) if m else "UNKNOWN",
                         "synced": sec == "HOME" and p in SYNCED_HOME})
        res[sec.lower()] = rows

    # 3. git の管理情報
    def wt(lines):
        return [l.split(" ", 1)[1] for l in lines if l.startswith("worktree ")]
    res["worktrees"] = {"bengio": wt(B["WORKTREES"]), "andrew": wt(A["WORKTREES"]),
                        "bengio_only": [w for w in wt(B["WORKTREES"]) if w not in wt(A["WORKTREES"])]}
    ex_a = [l for l in A["EXCLUDE"] if l.strip() and not l.startswith("#")]
    ex_b = [l for l in B["EXCLUDE"] if l.strip() and not l.startswith("#")]
    res["exclude"] = {"bengio": ex_b, "andrew": ex_a, "bengio_only": [l for l in ex_b if l not in ex_a]}
    br_a = {l.split("\t")[0]: l.split("\t") for l in A["BRANCHES"] if l}
    br_b = {l.split("\t")[0]: l.split("\t") for l in B["BRANCHES"] if l}
    res["branches_no_upstream"] = {
        "bengio": [v for v in br_b.values() if not v[1]],
        "bengio_only": [v for k, v in br_b.items() if not v[1] and k not in br_a]}

    if selftest:
        known = "README.md"  # 両ホストにあり、版管理下のもの
        hit_known = any(r["path"] == known for r in repo)
        print(json.dumps({"known_in_andrew_listed": hit_known,
                          "venv_symlink_listed": any(r["path"] == ".venv" for r in res["slocal2"]),
                          "bak_listed": any(r["path"] == "m2-git-info-exclude.bak-20261019" for r in res["home"])}))
        return
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    # 大きい repo の全件は 5 MB を超えないように分けて書く
    chunk, part, size = [], 0, 0
    for r in repo:
        chunk.append(r)
        size += len(json.dumps(r, ensure_ascii=False))
        if size > 4_000_000:
            Path(out_dir, f"leftovers_repo_{part:02d}.json").write_text(json.dumps(chunk, ensure_ascii=False))
            chunk, part, size = [], part + 1, 0
    Path(out_dir, f"leftovers_repo_{part:02d}.json").write_text(json.dumps(chunk, ensure_ascii=False))
    rest = {k: v for k, v in res.items() if k != "repo"}
    rest["repo_parts"] = part + 1
    rest["repo_count"] = len(repo)
    Path(out_dir, "leftovers_other.json").write_text(json.dumps(rest, ensure_ascii=False, indent=1))
    # 最上位ごとの件数とバイト数
    top = defaultdict(lambda: [0, 0, 0])
    for r in repo:
        k = r["path"].split("/")[0] if r["path"].split("/")[0] != "experiments" else "/".join(r["path"].split("/")[:2])
        top[k][0] += 1
        top[k][1] += r["bytes"] if r["type"] == "file" else 0
        top[k][2] += 1 if r["synced"] else 0
    Path(out_dir, "leftovers_repo_by_top.json").write_text(json.dumps(dict(sorted(top.items())), ensure_ascii=False, indent=1))
    print("repo", len(repo), "parts", part + 1)
    for k, v in sorted(top.items()):
        print(f"  {k}: n={v[0]} bytes={v[1]} synced={v[2]}")
    for sec in ("slocal2", "home", "tmp"):
        print(sec, [(r["path"], r["type"]) for r in res[sec]])
    print("worktrees", res["worktrees"]["bengio_only"])
    print("exclude bengio_only", res["exclude"]["bengio_only"])
    print("branches no upstream bengio_only", len(res["branches_no_upstream"]["bengio_only"]),
          [v[0] for v in res["branches_no_upstream"]["bengio_only"]][:40])


if __name__ == "__main__":
    main()
