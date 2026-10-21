"""A-5: 無視された未追跡のうち origin/phase0 に同じ経路が在るものを、中身の一致で分ける（読み取りだけ）。
方法1: phase0 の木 − 索引 → 実在 → check-ignore。方法2: ls-files --others --ignored を全列挙して木と突き合わせる。
中身は `git cat-file --filters <base>:<path>`（切り替えで書かれる内容）と手元のバイト列を比べる。"""
import os, subprocess, sys, time
base = sys.argv[1] if len(sys.argv) > 1 else "origin/phase0"
def z(*a): return [p for p in subprocess.run(["git", *a], capture_output=True, check=True).stdout.decode().split("\0") if p]
t0 = time.time()
tree = set(z("ls-tree", "-r", "-z", "--name-only", base))
index = set(z("ls-files", "-z"))
cand = sorted(p for p in tree - index if os.path.lexists(p) and not os.path.isdir(p))
ign1 = set()
if cand:
    out = subprocess.run(["git", "check-ignore", "-z", "--stdin", "--no-index"], input="\0".join(cand).encode(), capture_output=True).stdout.decode()
    ign1 = {p for p in out.split("\0") if p}
t1 = time.time()
ign2 = set(z("ls-files", "-z", "--others", "--ignored", "--exclude-standard")) & tree
t2 = time.time()
same, diff = [], []
for p in sorted(ign1):
    want = subprocess.run(["git", "cat-file", "--filters", f"{base}:{p}"], capture_output=True, check=True).stdout
    with open(p, "rb") as f:
        (same if f.read() == want else diff).append(p)
print(f"base={base} tree={len(tree)} index={len(index)} candidates(tree-index, exists)={len(cand)}")
print(f"method1 ignored&in_base={len(ign1)} ({t1-t0:.2f}s)  method2 ignored&in_base={len(ign2)} ({t2-t1:.2f}s)  agree={ign1==ign2}")
print(f"same={len(same)} diff={len(diff)}")
for p in diff: print("DIFF", p)
for p in same: print("SAME", p)
