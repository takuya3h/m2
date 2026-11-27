"""Task D: config 差分・既定挙動（V→P・V→T）・恒等性・陽性対照・学習集合・信号出どころの一括検証。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-11-26-vlm-caption-signal-pilot"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot")
SIG = STORE / "signals"
OUT = STORE / "task_d"
OUT.mkdir(parents=True, exist_ok=True)

VENV_PY = str(ROOT / ".venv/bin/python")
DETR_BIN = "/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/detr-venv/bin"
DETR_PY = f"{DETR_BIN}/python"

DP_TYPES = ("D1-L2", "D2", "D3-L2")
PD_TYPES = ("P1", "P2L")
SCOPES = ("W1", "W2", "W3")
ARMS = ("empty", "vlm_ko", "vlm_otsu", "vlm_hei", "vlm_ko_shuf", "vlm_otsu_shuf", "vlm_hei_shuf")


def detr_env(gpu_id: int) -> dict:
    env = os.environ.copy()
    env.update({
        "PATH": f"{DETR_BIN}:{env.get('PATH', '')}",
        "CUDA_VISIBLE_DEVICES": str(gpu_id),
        "CUDA_HOME": "/usr/local/cuda",
        "TORCH_EXTENSIONS_DIR": "/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/torch-extensions",
        "EGO_BODY": str(STORE / "inputs"),
        "EGO_ROOT": str(ROOT / "data/raw/ego"),
        "EGO_ANN_DIR": str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
        "WANDB_MODE": "offline",
        "WANDB_DIR": str(STORE / "wandb"),
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'scripts'}",
    })
    return env


def dp_env(gpu_id: int) -> dict:
    (STORE / "wandb").mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": str(gpu_id),
        "WANDB_MODE": "offline",
        "WANDB_API_KEY": "offline",
        "WANDB_DIR": str(STORE / "wandb"),
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'scripts'}",
    })
    return env


def check_configs() -> dict:
    pairs = [
        ("P1", ROOT / "configs/stage2pilot/pd_film_d9.py", ROOT / "configs/stage2pilot/pd_film_d3128.py"),
        ("P2L", ROOT / "configs/stage2pilot/pd_clsbias_lin_d9.py", ROOT / "configs/stage2pilot/pd_clsbias_lin_d3128.py"),
    ]
    res = {}
    for name, a, b in pairs:
        la, lb = a.read_text().splitlines(), b.read_text().splitlines()
        diffs = [(i + 1, x, y) for i, (x, y) in enumerate(zip(la, lb)) if x != y]
        only_dim = (len(la) == len(lb) and len(diffs) == 1
                    and diffs[0][1].replace("signal_dim=9", "signal_dim=3128") == diffs[0][2])
        res[name] = {"orig": str(a), "new": str(b), "n_diff_lines": len(diffs),
                     "diffs": diffs, "only_signal_dim_changed": only_dim}
    return res


def check_v2p_default() -> dict:
    """SPEC §5.2: 前回の T→P の D2 予測-noCF・W1 を本契約の識別子で回し直し、記録と一致を示す。"""
    prefix = "vlm_caption_signal_pilot_dp_defaultchk"
    p1 = ROOT / "experiments/phase1"
    existing = sorted(p1.glob(f"{prefix}_*_D2_pred_noCF_ep4_seed42"))
    if existing and (existing[-1] / "metrics_ep4.json").exists():
        exp_dir = existing[-1]
    else:
        cmd = [
            VENV_PY, str(ROOT / "scripts/stage2pilot/dp_train.py"), "train",
            "--type", "D2", "--arm", "pred_noCF", "--seed", "42",
            "--fixed-epochs", "4", "--record-epochs", "4",
            "--task-id", TASK_ID, "--exp-prefix", prefix,
            "--ckpt-dir", str(STORE / "dp_ckpt"),
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT), env=dp_env(0), capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(f"V→P default check failed: {proc.stderr[-800:]}")
        exp_dir = None
        for line in proc.stdout.splitlines():
            if line.startswith("DP_RUN_COMPLETE "):
                exp_dir = Path(line.split()[1])
        assert exp_dir is not None

    prev_dir = p1 / "stage2fix_dp_024_D2_pred_noCF_ep4_seed42"
    prev_m = json.loads((prev_dir / "metrics.json").read_text())
    new_m = json.loads((exp_dir / "metrics.json").read_text())
    prev_p = np.load(prev_dir / "predictions/val_probs_best.npz")
    new_p = np.load(exp_dir / "predictions/val_probs_best.npz")
    max_prob_diff = max(float(np.abs(prev_p[k] - new_p[k]).max()) for k in prev_p.files)
    # 陽性対照: 1 値を 1e-6 ずらした写しで違いを拾う
    shifted = new_p[prev_p.files[0]].copy()
    shifted[0, 0] += 1e-6
    pos_diff = float(np.abs(prev_p[prev_p.files[0]] - shifted).max())
    return {
        "prev_run": prev_dir.name, "new_run": exp_dir.name,
        "prev_jaccard": prev_m["phase_jaccard"], "new_jaccard": new_m["phase_jaccard"],
        "jaccard_diff": abs(prev_m["phase_jaccard"] - new_m["phase_jaccard"]),
        "max_prob_diff": max_prob_diff,
        "exact_equal": (prev_m["phase_jaccard"] == new_m["phase_jaccard"] and max_prob_diff < 1e-6),
        "positive_control_1e-6_diff": pos_diff,
        "positive_control_detected": pos_diff >= 9e-7,
    }


def check_v2t_default() -> dict:
    """SPEC §5.2: P1・予測-noCF・W1 の 1 epoch smoke を train_t1b.py 直接実行（2回）vs v2t_wrap.py 実行で比較。"""
    import re
    old_sig = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final")
    tr, va = str(old_sig / "P0_train.npz"), str(old_sig / "P0_val.npz")
    cfg = str(ROOT / "configs/stage2pilot/pd_film_d9.py")
    results = {}
    for label, script in [("direct_train_t1b", str(ROOT / "scripts/train_t1b.py")),
                          ("direct_train_t1b_run2", str(ROOT / "scripts/train_t1b.py")),
                          ("wrapped_v2t_wrap", str(Path(__file__).resolve().parent / "v2t_wrap.py"))]:
        work = OUT / f"v2t_default_{label}"
        env = detr_env(1)
        env["T1B_MODEL_CFG"] = cfg
        env["T1B_WORK_DIR"] = str(work)
        env["V2T_RECORD_LOG"] = str(work / "v2t_wrap.json")
        if not (work / "t1b_result.json").exists():
            work.mkdir(parents=True, exist_ok=True)
            cmd = [
                DETR_PY, script,
                "--seed", "42", "--trainable", "film", "--lr", "1e-4", "--film-lr", "5e-4",
                "--task-id", TASK_ID, "--run-name", f"vlm_defaultchk_{label}",
                "--det-ckpt", str(C.DET_CKPT),
                "--signal-train", tr, "--signal-val", va,
                "--epochs", "1", "--fixed-epochs", "--amp", "bf16", "--smoke",
                "--save-predictions-all", "--ckpt-dir", str(work / "ckpt"), "--save-trainable-only",
                "--print-freq", "1",
            ]
            proc = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
            (work / "stdout.log").write_text(proc.stdout + "\n---STDERR---\n" + proc.stderr)
            if proc.returncode != 0:
                raise SystemExit(f"V→T default smoke {label} failed: {proc.stderr[-800:]}")
        res = json.loads((work / "t1b_result.json").read_text())
        losses = [float(re.search(r"L=([0-9.]+)", ln).group(1))
                  for ln in (work / "stdout.log").read_text().splitlines() if "[t1b][ep0 " in ln]
        init_preds = M.load_results(work / "predictions/val_inj_ep-1.json.gz")
        ep0_preds = M.load_results(work / "predictions/val_inj_ep0.json.gz")
        results[label] = {"res": res, "losses": losses, "init_preds": init_preds, "ep0_preds": ep0_preds}

    a, a2, b = results["direct_train_t1b"], results["direct_train_t1b_run2"], results["wrapped_v2t_wrap"]
    diff_init = M.max_output_diff(a["init_preds"], b["init_preds"])
    diff_ep0_wrap = M.max_output_diff(a["ep0_preds"], b["ep0_preds"])
    diff_ep0_direct2 = M.max_output_diff(a["ep0_preds"], a2["ep0_preds"])
    # 陽性対照: init 予測のスコアを 1 つ 1e-6 ずらした写しで検出
    shifted = [dict(x) for x in b["init_preds"]]
    shifted[0]["score"] = float(shifted[0]["score"]) + 1e-6
    pos_diff = M.max_output_diff(a["init_preds"], shifted)
    train_t1b_git_diff = subprocess.run(["git", "diff", "--", "scripts/train_t1b.py"],
                                        cwd=str(ROOT), capture_output=True, text=True).stdout
    return {
        "train_t1b_unchanged_in_git": len(train_t1b_git_diff.strip()) == 0,
        "direct_init_mAP": a["res"]["init_mAP"], "wrapped_init_mAP": b["res"]["init_mAP"],
        "direct_ep0_mAP": a["res"]["final_mAP"], "direct2_ep0_mAP": a2["res"]["final_mAP"],
        "wrapped_ep0_mAP": b["res"]["final_mAP"],
        "losses_direct1": a["losses"], "losses_direct2": a2["losses"], "losses_wrapped": b["losses"],
        "step0_loss_exact_equal": a["losses"][0] == b["losses"][0] == a2["losses"][0],
        "diff_init_preds_direct_vs_wrapped": diff_init,
        "diff_ep0_preds_direct_vs_wrapped": diff_ep0_wrap,
        "diff_ep0_preds_direct1_vs_direct2": diff_ep0_direct2,
        "exact_equal": (len(train_t1b_git_diff.strip()) == 0
                        and a["losses"][0] == b["losses"][0]
                        and a["res"]["init_mAP"] == b["res"]["init_mAP"]
                        and a["res"]["final_mAP"] == b["res"]["final_mAP"]
                        and diff_init["max_abs_score_diff"] == 0.0
                        and diff_init["max_abs_bbox_diff_px"] == 0.0
                        and diff_init["label_mismatch"] == 0),
        "positive_control_1e-6": pos_diff,
        "positive_control_detected": pos_diff["max_abs_score_diff"] > 0.0,
    }


def run_v2p_identity() -> dict:
    """V→P: 3 型 × 3 W × 7 腕 = 63 組の恒等性・陽性対照・信号出どころ検査。"""
    id_dir = OUT / "v2p_identity"
    id_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(typ, sc) for sc in SCOPES for typ in DP_TYPES]

    def worker(typ, sc, gpu):
        out_p = id_dir / f"{typ}_{sc}.json"
        if not out_p.exists():
            cmd = [
                VENV_PY, str(ROOT / "scripts/stage2pilot/dp_train.py"), "identity",
                "--type", typ, "--scope", sc, "--arms", *ARMS,
                "--vlm-dir", str(SIG), "--task-id", TASK_ID, "--out", str(out_p),
            ]
            proc = subprocess.run(cmd, cwd=str(ROOT), env=dp_env(gpu), capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"dp identity {typ} {sc} failed: {proc.stderr[-600:]}")
        return typ, sc, json.loads(out_p.read_text())

    summary = {"total": 0, "identity_max_diff": 0.0, "identity_all_zero": True,
               "pos_changed": 0, "pos_unchanged_empty_struct": 0, "pos_unexpected_unchanged": [],
               "provenance_violations": [], "scope_all_ok": True, "details": {}}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(worker, typ, sc, i % 2) for i, (typ, sc) in enumerate(jobs)]
        for fut in as_completed(futs):
            typ, sc, data = fut.result()
            prefix = "tok" if typ == "D3-L2" else "vec"
            expected_file = {
                "empty": [],
                "vlm_ko": [str(SIG / f"{prefix}_ko_val.npz")],
                "vlm_otsu": [str(SIG / f"{prefix}_otsu_val.npz")],
                "vlm_hei": [str(SIG / f"{prefix}_hei_val.npz")],
                "vlm_ko_shuf": [str(SIG / f"{prefix}_ko_shuffle_val.npz")],
                "vlm_otsu_shuf": [str(SIG / f"{prefix}_otsu_shuffle_val.npz")],
                "vlm_hei_shuf": [str(SIG / f"{prefix}_hei_shuffle_val.npz")],
            }
            for arm in ARMS:
                r = data[arm]
                summary["total"] += 1
                idiff = r["identity_max_abs_logit_diff"]
                pdiff = r["positive_max_abs_logit_diff"]
                summary["identity_max_diff"] = max(summary["identity_max_diff"], idiff)
                if idiff != 0.0:
                    summary["identity_all_zero"] = False
                if pdiff > 0.0:
                    summary["pos_changed"] += 1
                elif arm == "empty" and typ in ("D1-L2", "D3-L2"):
                    summary["pos_unchanged_empty_struct"] += 1
                else:
                    summary["pos_unexpected_unchanged"].append(f"{typ}/{sc}/{arm}")
                got_files = [x["path"] for x in r["signal_files"]]
                if got_files != expected_file[arm]:
                    summary["provenance_violations"].append({"key": f"{typ}/{sc}/{arm}", "expected": expected_file[arm], "got": got_files})
                if sc != "W1":
                    sc_chk = r["scope_check"]
                    if not (sc_chk["equal"] and not sc_chk["equal_with_one_outside_mixed"]):
                        summary["scope_all_ok"] = False
                summary["details"][f"{typ}|{sc}|{arm}"] = {
                    "dim": r["dim"], "id_diff": idiff, "pos_diff": pdiff,
                    "files": got_files,
                }
    return summary


def run_v2t_identity() -> dict:
    """V→T: 2 型 × 3 W の set_check（6 組）＋ 2 型 × 7 腕の identity（14 組）＋ perturb（14 組）。"""
    id_dir = OUT / "v2t_identity"
    id_dir.mkdir(parents=True, exist_ok=True)
    ref_preds = str(STORE / "identity/plain_val_preds.json.gz")
    cfg_map = {"P1": str(ROOT / "configs/stage2pilot/pd_film_d3128.py"),
               "P2L": str(ROOT / "configs/stage2pilot/pd_clsbias_lin_d3128.py")}
    tr_map = {"W1": "film", "W2": "w2", "W3": "all"}
    sig_map = {
        "empty": (str(SIG / "vec_ko_val.npz"), True),
        "vlm_ko": (str(SIG / "vec_ko_val.npz"), False),
        "vlm_otsu": (str(SIG / "vec_otsu_val.npz"), False),
        "vlm_hei": (str(SIG / "vec_hei_val.npz"), False),
        "vlm_ko_shuf": (str(SIG / "vec_ko_shuffle_val.npz"), False),
        "vlm_otsu_shuf": (str(SIG / "vec_otsu_shuffle_val.npz"), False),
        "vlm_hei_shuf": (str(SIG / "vec_hei_shuffle_val.npz"), False),
    }
    script = str(Path(__file__).resolve().parent / "v2t_identity.py")

    # 1. set_check (CPU, 6 組)
    set_checks = {}
    for typ in PD_TYPES:
        for sc in SCOPES:
            out_p = id_dir / f"setcheck_{typ}_{sc}.json"
            if not out_p.exists():
                cmd = [DETR_PY, script, "--type", typ, "--w", sc, "--trainable", tr_map[sc],
                       "--arm", "vlm_ko", "--cfg", cfg_map[typ], "--signal-val", sig_map["vlm_ko"][0],
                       "--no-eval", "--out", str(out_p)]
                proc = subprocess.run(cmd, cwd=str(ROOT), env=detr_env(0), capture_output=True, text=True)
                if proc.returncode != 0:
                    raise RuntimeError(f"v2t setcheck {typ} {sc} failed: {proc.stderr[-600:]}")
            set_checks[f"{typ}|{sc}"] = json.loads(out_p.read_text())["trainable_set"]

    # 2. identity (14 組) + perturb (14 組) を GPU 2 枚並列
    eval_jobs = [(typ, arm, pert) for typ in PD_TYPES for arm in ARMS for pert in (False, True)]
    gpu_q: Queue[int] = Queue()
    gpu_q.put(0)
    gpu_q.put(1)

    def run_eval(typ, arm, pert):
        gid = gpu_q.get()
        try:
            tag = "perturb" if pert else "identity"
            out_p = id_dir / f"{typ}_{arm}_{tag}.json"
            if not out_p.exists():
                sv, zc = sig_map[arm]
                cmd = [DETR_PY, script, "--type", typ, "--w", "W1", "--trainable", "film",
                       "--arm", arm, "--cfg", cfg_map[typ], "--signal-val", sv,
                       "--ref-preds", ref_preds, "--out", str(out_p)]
                if zc:
                    cmd.append("--zero-ctx")
                if pert:
                    cmd.append("--perturb")
                proc = subprocess.run(cmd, cwd=str(ROOT), env=detr_env(gid), capture_output=True, text=True)
                if proc.returncode != 0:
                    raise RuntimeError(f"v2t {tag} {typ} {arm} failed: {proc.stderr[-600:]}")
            return typ, arm, pert, json.loads(out_p.read_text())
        finally:
            gpu_q.put(gid)

    id_rows, pert_rows = {}, {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(run_eval, typ, arm, pert) for typ, arm, pert in eval_jobs]
        for fut in as_completed(futs):
            typ, arm, pert, data = fut.result()
            key = f"{typ}|{arm}"
            rec = {"AP": data["metrics"]["AP"], "target_AP": data["metrics"]["target_AP"],
                   "diff_vs_ref": data["diff_vs_ref"], "signal_val": data["signal_val"], "zero_ctx": data["zero_ctx"]}
            if pert:
                pert_rows[key] = rec
            else:
                id_rows[key] = rec

    id_all_zero = all(
        r["diff_vs_ref"]["max_abs_score_diff"] == 0.0
        and r["diff_vs_ref"]["max_abs_bbox_diff_px"] == 0.0
        and r["diff_vs_ref"]["label_mismatch"] == 0
        for r in id_rows.values()
    )
    pert_all_changed = all(
        r["diff_vs_ref"]["max_abs_score_diff"] > 0.0
        for r in pert_rows.values()
    )
    set_all_ok = all(ts["equal"] and not ts["equal_with_one_outside_mixed"] for ts in set_checks.values())
    return {
        "set_all_ok": set_all_ok,
        "set_checks_summary": {k: {"n_names": v["n_names"], "n_elements": v["n_elements"],
                                   "n_iface_elements": v["n_iface_elements"],
                                   "equal": v["equal"], "mixed_equal": v["equal_with_one_outside_mixed"]}
                               for k, v in set_checks.items()},
        "identity_count": len(id_rows), "identity_all_zero": id_all_zero,
        "perturb_count": len(pert_rows), "perturb_all_changed": pert_all_changed,
        "identity": id_rows, "perturb": pert_rows,
    }


def main():
    print("[Task D] 1/4 checking config diffs...", flush=True)
    cfgs = check_configs()
    print("[Task D] 2/4 checking default behaviors (V→P & V→T)...", flush=True)
    v2p_def = check_v2p_default()
    v2t_def = check_v2t_default()
    print("[Task D] 3/4 running V→P identity & positive controls (63 combos)...", flush=True)
    v2p_id = run_v2p_identity()
    print("[Task D] 4/4 running V→T setcheck, identity & positive controls (6 + 14 + 14)...", flush=True)
    v2t_id = run_v2t_identity()

    report = {
        "task_id": TASK_ID,
        "configs": cfgs,
        "v2p_default": v2p_def,
        "v2t_default": v2t_def,
        "v2p_identity": v2p_id,
        "v2t_identity": v2t_id,
        "gate_g4_pass": (
            all(c["only_signal_dim_changed"] for c in cfgs.values())
            and v2p_def["exact_equal"] and v2p_def["positive_control_detected"]
            and v2t_def["exact_equal"] and v2t_def["positive_control_detected"]
            and v2p_id["identity_all_zero"] and len(v2p_id["pos_unexpected_unchanged"]) == 0
            and len(v2p_id["provenance_violations"]) == 0 and v2p_id["scope_all_ok"]
            and v2t_id["set_all_ok"] and v2t_id["identity_all_zero"] and v2t_id["perturb_all_changed"]
        ),
    }
    C.write_json(OUT / "task_d_summary.json", report)
    print(json.dumps({
        "configs_ok": all(c["only_signal_dim_changed"] for c in cfgs.values()),
        "v2p_default_exact": v2p_def["exact_equal"],
        "v2t_default_exact": v2t_def["exact_equal"],
        "v2p_id_all_zero": v2p_id["identity_all_zero"],
        "v2p_pos_changed": f"{v2p_id['pos_changed']}/{v2p_id['total']} (struct_empty={v2p_id['pos_unchanged_empty_struct']})",
        "v2p_prov_viol": len(v2p_id["provenance_violations"]),
        "v2t_set_ok": v2t_id["set_all_ok"],
        "v2t_id_all_zero": v2t_id["identity_all_zero"],
        "v2t_pert_all_changed": v2t_id["perturb_all_changed"],
        "gate_g4_pass": report["gate_g4_pass"],
    }, ensure_ascii=False, indent=2), flush=True)
    if not report["gate_g4_pass"]:
        raise SystemExit("Gate G4 FAIL")


if __name__ == "__main__":
    main()
