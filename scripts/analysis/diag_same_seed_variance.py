#!/usr/bin/env python3
"""N1: 同一 seed の run が再現しない原因を特定する。

問い: 同じ seed の 2 run が違う結果を出すのは
      (a) 設定が違ったからか、(b) seed で制御できていない要素があるからか。

対象: b2a_det2phase_oracletool_003..008 (canonical seed 42/123/456 が 2 回ずつ)

config はネストした YAML なのでフラット化してキー単位で比較する。
比較できなかったキーは必ず列挙する (「差分なし」と書く前の必須確認)。

Usage:
    python3 scripts/analysis/diag_same_seed_variance.py --out $OUT
    python3 scripts/analysis/diag_same_seed_variance.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import tempfile

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_SEEDS = {"42", "123", "456"}

# N1-3 で探索する非決定性の制御項目
NONDET_PATTERNS = {
    "torch.manual_seed": r"torch\.manual_seed",
    "np.random.seed": r"np(?:umpy)?\.random\.seed",
    "random.seed": r"(?<!np\.)(?<!numpy\.)\brandom\.seed",
    "torch.cuda.manual_seed_all": r"torch\.cuda\.manual_seed_all",
    "torch.use_deterministic_algorithms": r"torch\.use_deterministic_algorithms",
    "cudnn.deterministic": r"cudnn\.deterministic",
    "cudnn.benchmark": r"cudnn\.benchmark",
    "DataLoader worker_init_fn": r"worker_init_fn",
    "DataLoader generator": r"\bgenerator\s*=",
    "DataLoader num_workers": r"num_workers",
    "DataLoader shuffle": r"shuffle\s*=",
    "PYTHONHASHSEED": r"PYTHONHASHSEED",
}
# 学習エントリポイント候補 (実在するものだけ走査)
TRAIN_SCRIPTS = [
    "scripts/train_b2a.py", "scripts/train_t1a.py", "scripts/train_haux.py",
    "scripts/train_s4_tecno.py", "src/egosurgery/engines/phase_trainer.py",
]


def flatten(d, prefix=""):
    """ネストした dict/list をキーパス単位でフラット化する。"""
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = d
    return out


def load_run(dirpath):
    """1 run のメタ情報を全て集める。読めないものは None を入れて記録する。"""
    run = os.path.basename(dirpath)
    info = {"run": run, "dir": os.path.relpath(dirpath, REPO),
            "seed": run.split("seed")[-1] if "seed" in run else "UNKNOWN",
            "unreadable": []}
    # config.yaml
    p = os.path.join(dirpath, "config.yaml")
    if os.path.exists(p):
        try:
            with open(p) as f:
                info["config"] = flatten(yaml.safe_load(f))
        except Exception as e:
            info["config"] = {}; info["unreadable"].append(f"config.yaml: {e}")
    else:
        info["config"] = {}; info["unreadable"].append("config.yaml: NOT FOUND")
    # 付随ファイル
    for name, key in [("command.sh", "command"), ("git_commit.txt", "git_commit"),
                      ("server.txt", "server"), ("notes.md", "notes")]:
        q = os.path.join(dirpath, name)
        if os.path.exists(q):
            try:
                info[key] = open(q).read().strip()
            except Exception as e:
                info[key] = None; info["unreadable"].append(f"{name}: {e}")
        else:
            info[key] = None; info["unreadable"].append(f"{name}: NOT FOUND")
    # metrics
    q = os.path.join(dirpath, "metrics.json")
    if os.path.exists(q):
        try:
            m = json.load(open(q))
            info["metrics"] = m
            info["val_acc"] = m.get("phase_accuracy")
            info["val_f1"] = m.get("phase_macro_f1")
            info["epoch"] = m.get("epoch")
            info["eval_recipe"] = flatten(m.get("eval_recipe", {}), "eval_recipe")
        except Exception as e:
            info["metrics"] = {}; info["unreadable"].append(f"metrics.json: {e}")
    info["mtime"] = os.path.getmtime(q) if os.path.exists(q) else None
    # command.sh の生成日時
    if info.get("command"):
        mm = re.search(r"生成日時:\s*(\S+)", info["command"])
        info["generated_at"] = mm.group(1) if mm else None
        cm = [ln for ln in info["command"].splitlines() if ln and not ln.startswith("#")]
        info["command_line"] = cm[-1] if cm else None
    return info


def diff_pair(a, b):
    """2 run の全項目差分。比較不能キーも返す。"""
    rows, incomparable = [], []
    # config
    ka, kb = set(a["config"]), set(b["config"])
    for k in sorted(ka | kb):
        va, vb = a["config"].get(k, "<ABSENT>"), b["config"].get(k, "<ABSENT>")
        if k not in ka or k not in kb:
            incomparable.append({"source": "config", "key": k,
                                 "reason": "片方に存在しない", "a": va, "b": vb})
            rows.append({"source": "config", "key": k, "a": va, "b": vb, "differs": True})
        elif va != vb:
            rows.append({"source": "config", "key": k, "a": va, "b": vb, "differs": True})
        else:
            rows.append({"source": "config", "key": k, "a": va, "b": vb, "differs": False})
    # eval_recipe
    ea, eb = a.get("eval_recipe", {}), b.get("eval_recipe", {})
    for k in sorted(set(ea) | set(eb)):
        va, vb = ea.get(k, "<ABSENT>"), eb.get(k, "<ABSENT>")
        rows.append({"source": "eval_recipe", "key": k, "a": va, "b": vb, "differs": va != vb})
    # スカラーのメタ
    for k in ("git_commit", "server", "generated_at", "command_line", "epoch"):
        va, vb = a.get(k), b.get(k)
        rows.append({"source": "meta", "key": k, "a": va, "b": vb, "differs": va != vb})
    for r in a["unreadable"]:
        incomparable.append({"source": "file", "key": r, "reason": f"A 側で読めない", "a": None, "b": None})
    for r in b["unreadable"]:
        incomparable.append({"source": "file", "key": r, "reason": f"B 側で読めない", "a": None, "b": None})
    return rows, incomparable


def variance_decomp(runs):
    """seed 平均間の分散 / 同一 seed 内の分散 / ICC。"""
    by_seed = {}
    for r in runs:
        if r["seed"] in CANONICAL_SEEDS and r.get("val_acc") is not None:
            by_seed.setdefault(r["seed"], []).append(r["val_acc"])
    reps = {s: v for s, v in by_seed.items() if len(v) > 1}
    if not reps:
        return {"status": "NO_REPLICATE", "n_seeds": len(by_seed),
                "seeds_with_replicates": 0}
    seed_means = [statistics.mean(v) for v in by_seed.values()]
    var_between = statistics.pvariance(seed_means) if len(seed_means) > 1 else 0.0
    within = []
    for s, v in reps.items():
        within.append(statistics.pvariance(v))
    var_within = statistics.mean(within)
    icc = var_between / (var_between + var_within) if (var_between + var_within) > 0 else None
    return {"status": "OK", "n_seeds": len(by_seed), "seeds_with_replicates": len(reps),
            "n_runs_used": sum(len(v) for v in by_seed.values()),
            "values_by_seed": by_seed,
            "var_between_seed": var_between, "var_within_seed": var_within,
            "sd_between_seed": var_between ** 0.5, "sd_within_seed": var_within ** 0.5,
            "icc": icc,
            "note": "母分散 (pvariance) を使用。n は values_by_seed を参照。"}


def scan_nondeterminism():
    found = {}
    for key, pat in NONDET_PATTERNS.items():
        hits = []
        for rel in TRAIN_SCRIPTS:
            p = os.path.join(REPO, rel)
            if not os.path.exists(p):
                continue
            for i, line in enumerate(open(p, errors="replace"), 1):
                if re.search(pat, line):
                    hits.append({"file": rel, "line": i, "text": line.strip()[:160]})
        found[key] = {"present": len(hits) > 0, "occurrences": hits}
    return found


def self_test() -> int:
    """検出できることを確認する (N1-5):
       (a) 1 キーだけ違う config ペア
       (b) 完全一致の config ペア
       (c) ネストが深い位置に差があるペア
    """
    ok = True

    def mk(cfg):
        return {"run": "r", "seed": "42", "config": flatten(cfg), "eval_recipe": {},
                "unreadable": [], "git_commit": "x", "server": "h", "generated_at": "t",
                "command_line": "c", "epoch": 1, "val_acc": 0.9}

    # (a) 1 キーだけ違う
    a = mk({"train": {"lr": 0.0005, "epochs": 50}, "seed": 42})
    b = mk({"train": {"lr": 0.0010, "epochs": 50}, "seed": 42})
    rows, inc = diff_pair(a, b)
    d = [r for r in rows if r["source"] == "config" and r["differs"]]
    if len(d) != 1 or d[0]["key"] != "train.lr":
        print(f"  [FAIL] 1 キー差分の検出: {d}"); ok = False
    else:
        print("  [OK]   1 キーだけ違う config ペアを検出 (train.lr)")

    # (b) 完全一致
    rows, inc = diff_pair(a, mk({"train": {"lr": 0.0005, "epochs": 50}, "seed": 42}))
    d = [r for r in rows if r["source"] == "config" and r["differs"]]
    if d:
        print(f"  [FAIL] 完全一致なのに差分を検出: {d}"); ok = False
    else:
        print("  [OK]   完全一致の config ペアを差分なしと判定")

    # (c) ネスト深部の差
    a2 = mk({"model": {"head": {"tecno": {"num_layers": 8}}}})
    b2 = mk({"model": {"head": {"tecno": {"num_layers": 10}}}})
    rows, inc = diff_pair(a2, b2)
    d = [r for r in rows if r["source"] == "config" and r["differs"]]
    if len(d) != 1 or d[0]["key"] != "model.head.tecno.num_layers":
        print(f"  [FAIL] ネスト深部の差分検出: {d}"); ok = False
    else:
        print("  [OK]   ネストが深い位置の差分を検出 (model.head.tecno.num_layers)")

    # (d) 片方に存在しないキーを「比較不能」として列挙できるか
    rows, inc = diff_pair(a, mk({"train": {"lr": 0.0005}}))
    if not any(i["source"] == "config" and i["key"] == "train.epochs" for i in inc):
        print(f"  [FAIL] 片側欠損キーを比較不能に列挙できない: {inc}"); ok = False
    else:
        print("  [OK]   片方にしか無いキーを比較不能として列挙")

    # (e) 分散分解: 重複が無ければ NO_REPLICATE
    v = variance_decomp([{"seed": "42", "val_acc": 0.9}, {"seed": "123", "val_acc": 0.8}])
    if v["status"] != "NO_REPLICATE":
        print(f"  [FAIL] 重複なしを NO_REPLICATE と判定できない: {v['status']}"); ok = False
    else:
        print("  [OK]   同一 seed の重複が無い系統を NO_REPLICATE と判定")

    # (f) 分散分解: 既知値
    v = variance_decomp([{"seed": "42", "val_acc": 0.90}, {"seed": "42", "val_acc": 0.92},
                         {"seed": "123", "val_acc": 0.80}, {"seed": "123", "val_acc": 0.82}])
    # seed 平均 0.91 / 0.81 -> between pvar = 0.0025, within pvar = 0.0001
    if abs(v["var_between_seed"] - 0.0025) > 1e-9 or abs(v["var_within_seed"] - 0.0001) > 1e-9:
        print(f"  [FAIL] 分散分解の既知値: between={v['var_between_seed']} within={v['var_within_seed']}")
        ok = False
    else:
        print(f"  [OK]   分散分解が既知値を再現 (ICC={v['icc']:.4f})")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out"); ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test が必要")
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    # ---- N1-1: 3 ペアの config 差分 ---------------------------------------- #
    runs = {}
    for d in sorted(glob.glob(os.path.join(REPO, "experiments/transfer/b2a_det2phase_oracletool_*"))):
        if os.path.isdir(d):
            info = load_run(d)
            runs[info["run"]] = info

    def find(seq):
        for k in runs:
            if f"_oracletool_{seq}_" in k:
                return runs[k]
        return None

    pairs = [("42", "004", "006"), ("123", "003", "007"), ("456", "005", "008")]
    pair_out, all_rows = {}, []
    for seed, sa, sb in pairs:
        ra, rb = find(sa), find(sb)
        if not ra or not rb:
            pair_out[seed] = {"status": "UNKNOWN", "reason": f"run が見つからない ({sa}/{sb})"}
            continue
        rows, inc = diff_pair(ra, rb)
        diffs = [r for r in rows if r["differs"]]
        pair_out[seed] = {
            "run_a": ra["run"], "run_b": rb["run"],
            "val_acc_a": ra.get("val_acc"), "val_acc_b": rb.get("val_acc"),
            "abs_diff": (abs(ra["val_acc"] - rb["val_acc"])
                         if ra.get("val_acc") is not None and rb.get("val_acc") is not None else None),
            "n_keys_compared": len(rows), "n_keys_differ": len(diffs),
            "differing_keys": [{"source": r["source"], "key": r["key"],
                                "a": r["a"], "b": r["b"]} for r in diffs],
            "incomparable_keys": inc,
            "n_incomparable": len(inc),
        }
        for r in rows:
            all_rows.append({"seed": seed, "run_a": ra["run"], "run_b": rb["run"], **r})

    with open(os.path.join(args.out, "csv", "n1_config_diff.csv"), "w") as f:
        f.write("seed,run_a,run_b,source,key,value_a,value_b,differs\n")
        for r in all_rows:
            f.write(f"{r['seed']},\"{r['run_a']}\",\"{r['run_b']}\",{r['source']},"
                    f"\"{r['key']}\",\"{r['a']}\",\"{r['b']}\",{r['differs']}\n")

    # ---- N1-2: 分散分解 (oracle-tool + 他系統) ------------------------------ #
    def classify(run):
        r = run.lower()
        if "oracletool" in r:
            return "oracle-tool"
        if r.startswith("s4_phase_baseline"):
            return "s4"
        if r.startswith("haux_"):
            return "h6"
        if r.startswith("b2a_"):
            return "b2a"
        if r.startswith("t1a_"):
            return "t1a"
        return "other"

    sysruns = {}
    for p in sorted(glob.glob(os.path.join(REPO, "experiments/**/metrics.json"), recursive=True)):
        d_dir = os.path.dirname(p)
        run = os.path.basename(d_dir)
        try:
            m = json.load(open(p))
        except Exception:
            continue
        if "phase_accuracy" not in m:
            continue
        cmd_p = os.path.join(d_dir, "command.sh")
        cmd = open(cmd_p).read() if os.path.exists(cmd_p) else ""
        if "--eval-test" in cmd:      # val のみ対象
            continue
        s = classify(run)
        sysruns.setdefault(s, []).append(
            {"run": run, "seed": run.split("seed")[-1] if "seed" in run else "UNKNOWN",
             "val_acc": m["phase_accuracy"]})

    decomp = {s: variance_decomp(v) for s, v in sysruns.items()
              if s in ("s4", "b2a", "t1a", "h6", "oracle-tool")}
    # 重要な但し書き: 系統プールは同一設定の反復ではなく、多数の派生 run を含む。
    # したがって sd_within は「非決定性」ではなく「設定差 + 非決定性」を混ぜて測っている。
    for s, v in decomp.items():
        if v["status"] != "OK":
            continue
        v["caveat"] = (
            f"この系統の val run は {v['n_runs_used']} 本あり、同一設定の反復ではなく "
            "派生 run (ablation・variant) を含む。したがって var_within_seed は "
            "『非決定性』ではなく『設定差 + 非決定性』を混合して測った値であり、"
            "純粋な再現性の指標としては解釈できない。"
            "設定が揃っていることを確認済みなのは oracle-tool の 3 ペアのみ (N1-1) で、"
            "そこでも host/commit が異なる。")
        v["pool_is_homogeneous"] = False
    with open(os.path.join(args.out, "csv", "n1_variance_decomp.csv"), "w") as f:
        f.write("system,status,n_seeds,seeds_with_replicates,n_runs_used,"
                "var_between_seed,var_within_seed,sd_between_seed,sd_within_seed,icc\n")
        for s, v in decomp.items():
            f.write(f"{s},{v['status']},{v.get('n_seeds')},{v.get('seeds_with_replicates')},"
                    f"{v.get('n_runs_used')},{v.get('var_between_seed')},{v.get('var_within_seed')},"
                    f"{v.get('sd_between_seed')},{v.get('sd_within_seed')},{v.get('icc')}\n")

    # ---- N1-3: 非決定性の制御 ---------------------------------------------- #
    nondet = scan_nondeterminism()

    # ---- N1-4: 判定 -------------------------------------------------------- #
    any_config_diff = any(p.get("n_keys_differ", 0) > 0 for p in pair_out.values()
                          if isinstance(p, dict) and "n_keys_differ" in p)
    # seed 制御があるか (最低限 torch.manual_seed)
    seed_controlled = nondet["torch.manual_seed"]["present"]
    determinism_controlled = (nondet["torch.use_deterministic_algorithms"]["present"]
                              or nondet["cudnn.deterministic"]["present"])
    # 判定表は 2 つを排他として扱うが、実測では両方の前提が同時に成立しうる。
    # §6 に従い、表に当てはめず観測された条件をすべて記録する。
    cond_config_diff = any_config_diff
    cond_uncontrolled = seed_controlled and not determinism_controlled
    if cond_config_diff and cond_uncontrolled:
        verdict = "CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM (両立)"
        consequence = (
            "判定表は 2 つを排他として扱うが、実測では両方が成立する。"
            "(1) ペアは別ホスト・別コミットであり同一条件の反復ではない → 混ぜずに分けて集計する必要がある。"
            "(2) seed は設定されているが決定性制御 (use_deterministic_algorithms / cudnn.deterministic / "
            "cuda.manual_seed_all / DataLoader の worker_init_fn・generator) が無い → "
            "条件を揃えても bit-exact 再現は保証されない。"
            "したがって『重複 run を独立反復として扱ってよい』とは言えず、"
            "同時に『条件を揃えれば再現する』とも言えない。")
    elif cond_config_diff:
        verdict = "CONFIG_DIFF"
        consequence = ("同一条件の反復ではない。3-seed 統計は維持できるが、run の同一性管理が必要")
    elif cond_uncontrolled:
        verdict = "UNCONTROLLED_NONDETERMINISM"
        consequence = ("これまでの MDE は過小評価。全実験の誤差評価をやり直す必要がある")
    else:
        verdict = "UNEXPLAINED"
        consequence = "観測された全パターンを列挙する"

    res = {
        "task": "N1_same_seed_variance",
        "N1_1_pair_diffs": pair_out,
        "N1_2_variance_decomposition": decomp,
        "N1_3_nondeterminism_controls": nondet,
        "N1_3_scanned_files": [p for p in TRAIN_SCRIPTS if os.path.exists(os.path.join(REPO, p))],
        "N1_4_verdict": verdict,
        "N1_4_consequence": consequence,
    }
    with open(os.path.join(args.out, "json", "n1_same_seed.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False, default=str)

    print("=== N1-1: 3 ペアの差分 ===")
    for seed, p in pair_out.items():
        if p.get("status") == "UNKNOWN":
            print(f"  seed {seed}: UNKNOWN"); continue
        print(f"  seed {seed}: {p['run_a'][-28:]} vs {p['run_b'][-28:]}")
        print(f"    val_acc {p['val_acc_a']:.6f} vs {p['val_acc_b']:.6f} (差 {p['abs_diff']:.6f})")
        print(f"    比較キー {p['n_keys_compared']} / 差分 {p['n_keys_differ']} / "
              f"比較不能 {p['n_incomparable']}")
        for d in p["differing_keys"]:
            print(f"      [{d['source']}] {d['key']}: {str(d['a'])[:40]} -> {str(d['b'])[:40]}")
    print("\n=== N1-2: 分散分解 ===")
    for s, v in decomp.items():
        if v["status"] == "NO_REPLICATE":
            print(f"  {s:12s} NO_REPLICATE (seed {v['n_seeds']} 種・重複なし)"); continue
        print(f"  {s:12s} seeds={v['n_seeds']} 重複あり={v['seeds_with_replicates']} "
              f"n={v['n_runs_used']} sd_between={v['sd_between_seed']:.6f} "
              f"sd_within={v['sd_within_seed']:.6f} ICC={v['icc']:.4f}")
    print("\n=== N1-3: 非決定性の制御 ===")
    for k, v in nondet.items():
        mark = "✓" if v["present"] else "✗"
        loc = (f"{v['occurrences'][0]['file']}:{v['occurrences'][0]['line']}"
               if v["occurrences"] else "—")
        print(f"  {mark} {k:36s} {loc}")
    print(f"\n=== N1 VERDICT: {verdict} ===\n  {consequence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
