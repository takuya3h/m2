"""REPORT.md の表を JSON から生成する（T-2026-11-02-bengio-andrew-env-survey）。数値は手で写さない。

    python3 -B make_tables.py > experiments/analysis/bengio_andrew_env_survey/report_tables.md
"""
import datetime
import json

D = "experiments/analysis/bengio_andrew_env_survey/"


def ts(t):
    return datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")


def p(*a):
    print(*a)


# --- B ---
b = json.load(open(D + "b/reldetr_compare.json"))
p("## 表 B-1 Relation-DETR のファイル単位の三分類（andrew main を基準、bengio main と比べる）\n")
p("| 分類 | 経路 | andrew バイト | bengio バイト | bengio の中身が third_party_snapshot/Bengio の tar に在るか |")
p("|---|---|---:|---:|---|")
for r in b["rows"]:
    s = r.get("snapshot")
    if s is None:
        snap = "—（bengio に無い）"
    elif s["same_content_same_path"]:
        snap = "在る（同じ経路・同じ中身）"
    elif s["same_content_any_path"]:
        snap = "在る（別の経路）: " + ", ".join(s["same_content_any_path"])
    else:
        snap = "**無い（揃えると失われる中身）**"
    p(f"| {r['class']} | `{r['path']}` | {r['andrew'][0] if r['andrew'] else '—'} | {r['bengio'][0] if r['bengio'] else '—'} | {snap} |")
c = b["counts"]
p(f"\n件数: andrew {c['andrew_files']}、bengio {c['bengio_files']}、和集合 {c['union']} = andrew だけ {c['andrew_only']} + bengio だけ {c['bengio_only']} + 中身が違う {c['differ']} + 同じ {c['same']}。")
o = b["overlay_vs_andrew"]
p(f"重ねの BODY と andrew main: andrew だけ {len(o['andrew_only'])}、BODY だけ {len(o['overlay_only'])}、違う {len(o['differ'])}、同じ {o['same']}。\n")
p("## 表 B-2 除外した最上位（件数・バイト数）\n")
p("| 最上位 | andrew | bengio main | bengio 重ねの BODY |")
p("|---|---|---|---|")
for k in sorted(set(b["excluded"]["andrew"]) | set(b["excluded"]["bengio"]) | set(b["excluded"]["overlay"])):
    f = lambda d: f"{d[k][0]} 件 {d[k][1]} B" if k in d else "無い"
    p(f"| `{k}` | {f(b['excluded']['andrew'])} | {f(b['excluded']['bengio'])} | {f(b['excluded']['overlay'])} |")
p("\n## 表 B-3 除外した最上位 `checkpoints` のファイル（両ホスト）\n")
p("| 経路 | andrew バイト | andrew sha256 | bengio バイト | bengio sha256 | 判定 |")
p("|---|---:|---|---:|---|---|")
ca, cb = b["checkpoints"]["andrew"], b["checkpoints"]["bengio"]
for k in sorted(set(ca) | set(cb)):
    a_, b_ = ca.get(k), cb.get(k)
    j = "一致" if a_ and b_ and a_[1] == b_[1] else "不一致"
    p(f"| `{k}` | {a_[0] if a_ else '—'} | {a_[1][:16] + '…' if a_ else '—'} | {b_[0] if b_ else '—'} | {b_[1][:16] + '…' if b_ else '—'} | {j} |")

# --- D ---
d = json.load(open(D + "d/data_compare.json"))
p("\n## 表 D-2 個別のファイル（両ホスト。sha256 は先頭 16 桁、全桁は `d/data_compare.json`）\n")
p("| 群 | 経路 | andrew バイト | andrew sha256 | bengio バイト | bengio sha256 | 判定 |")
p("|---|---|---:|---|---:|---|---|")
for r in d["files"]:
    a_, b_ = r["andrew"], r["bengio"]
    sa = (a_.get("sha256") or "")[:16] or "—"
    sb = (b_.get("sha256") or "")[:16] or "—"
    p(f"| {r['group']} | `{r['path']}` | {a_.get('bytes') if a_.get('exists') else '無い'} | {sa} | {b_.get('bytes') if b_.get('exists') else '無い'} | {sb} | {r['judge']} |")
p("\n## 表 D-3 ディレクトリ単位（件数・バイト数。中身の要約値は取っていない）\n")
p("| 経路 | andrew | bengio |")
p("|---|---|---|")
for k in d["dirs"]["andrew"]:
    f = lambda x: f"{x['files']} 件 {x['bytes']} B" if x.get("exists") else "無い"
    p(f"| `{k}` | {f(d['dirs']['andrew'][k])} | {f(d['dirs']['bengio'][k])} |")

# --- E ---
rows = []
import glob
for f in sorted(glob.glob(D + "e/leftovers_repo_[0-9][0-9].json")):
    rows += json.load(open(f))
other = json.load(open(D + "e/leftovers_other.json"))
top = json.load(open(D + "e/leftovers_repo_by_top.json"))
p("\n## 表 E-1 repo の作業ツリーの残り物（最上位ごと。experiments は二段目まで）\n")
p("| 最上位 | 件数 | バイト数（ファイルの合計） | 同期の対象（近似） |")
p("|---|---:|---:|---:|")
for k, v in top.items():
    p(f"| `{k}` | {v[0]} | {v[1]} | {v[2]} |")
p(f"| 計 | {sum(v[0] for v in top.values())} | {sum(v[1] for v in top.values())} | {sum(v[2] for v in top.values())} |")
p("\n## 表 E-2 repo の作業ツリーの残り物（experiments 以外の全件）\n")
p("種類: file・symlink・empty_dir。作った契約は経路に契約の識別子があるものだけ埋め、ほかは UNKNOWN（audit の E-2 で個別に手がかりを書く）。"
  "同期は repo の `.stignore` の近似照合（`tools/leftovers.py` の冒頭）。参照は記号リンクの先だけを機械で埋める。\n")
p("| 経路 | 種類 | バイト数 | 更新時刻（UTC） | 作った契約 | 参照 | 同期 |")
p("|---|---|---:|---|---|---|---|")
for r in rows:
    if r["path"].startswith("experiments/"):
        continue
    p(f"| `{r['path']}` | {r['type']} | {r['bytes']} | {ts(r['mtime'])} | {r['contract']} | {('→ `' + r['link'] + '`') if r['link'] else ''} | {'渡る' if r['synced'] else '渡らない'} |")
p("\n## 表 E-3 repo の作業ツリーの残り物（experiments の全件）\n")
p("| 経路 | 種類 | バイト数 | 更新時刻（UTC） | 参照 | 同期 |")
p("|---|---|---:|---|---|---|")
for r in rows:
    if r["path"].startswith("experiments/"):
        p(f"| `{r['path']}` | {r['type']} | {r['bytes']} | {ts(r['mtime'])} | {('→ `' + r['link'] + '`') if r['link'] else ''} | {'渡る' if r['synced'] else '渡らない'} |")
sizes = json.load(open(D + "e/sizes.json"))
for sec, title, prefix in (("slocal2", "`~/slocal2` 直下", "~/slocal2/"), ("home", "家の直下", "~/")):
    p(f"\n## 表 E-4 {title}の残り物\n")
    p("| 経路 | 種類 | バイト数（`du -sb --apparent-size`） | 更新時刻（UTC） | 同期 |")
    p("|---|---|---:|---|---|")
    for r in other[sec]:
        p(f"| `{prefix}{r['path']}` | {r['type']} | {sizes.get(prefix + r['path'], 'UNKNOWN')} | {ts(r['mtime'])} | {'渡る' if r['synced'] else '渡らない'} |")
tmp = other["tmp"]
from collections import Counter
def cat(n):
    for k in ("vscode-ipc-", "vscode-git-", "vscode-ssh-auth-sock-", "wandb_xpu-", "wandb-", "mcp-", "pymp-", "ssh-"):
        if n.startswith(k):
            return k + "*"
    return n
cc = Counter(cat(r["path"]) for r in tmp)
p("\n## 表 E-5 `/tmp` 直下の自分の残り物（名前の型ごと。全件は `e/leftovers_other.json` の tmp）\n")
p("| 名前（型） | 件数 | 種類 |")
p("|---|---:|---|")
for k, v in sorted(cc.items()):
    p(f"| `{k}` | {v} | {','.join(sorted({r['type'] for r in tmp if cat(r['path']) == k}))} |")
p(f"\n計 {len(tmp)} 件。")
