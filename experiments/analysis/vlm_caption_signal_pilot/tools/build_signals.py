"""Task C: 生成済み記述の統計・伏せ字（甲・乙・丙）・文埋め込み・入れ替え信号の作成と検査。

vlm-venv で実行する（Qwen3-Embedding-0.6B の読み込みに transformers>=4.51 が必要なため）。
外部通信は一切行わない（HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, local_files_only=True）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import captions as cap  # noqa: E402
import redact as red  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot.shuffle_signals import make_mapping, mapping_stats, sorted_digest  # noqa: E402

STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
OUT = STORE / "vlm_caption_signal_pilot"
RUNTIME = Path("/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime")
EMB_MODEL = RUNTIME / "models/Qwen3-Embedding-0.6B"
EMB_DIM = 1024
ATTR_KEYS = (
    "visibility", "skin", "depth", "stitches", "spread",
    "bleeding", "wetness", "skin_color", "placed", "action", "target",
)
MODES = ("ko", "otsu", "hei")


def load_jsonl_dir(directory: Path) -> list[dict]:
    rows = []
    for part in sorted(directory.glob("part-*.jsonl")):
        rows.extend(json.loads(line) for line in part.read_text().splitlines())
    return rows


def embed_unique_texts(texts: list[str], batch_size: int = 128) -> dict[str, np.ndarray]:
    """一意の非空テキスト集合を Qwen3-Embedding-0.6B（指示文なし・last_token_pool・L2 正規化）で 1024 次元化する。"""
    import torch
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer

    unique = sorted({t for t in texts if t})
    if not unique:
        return {}
    tokenizer = AutoTokenizer.from_pretrained(str(EMB_MODEL), padding_side="left", local_files_only=True)
    model = AutoModel.from_pretrained(str(EMB_MODEL), dtype=torch.bfloat16, local_files_only=True).cuda().eval()

    def last_token_pool(last_hidden_states, attention_mask):
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        if left_padding:
            return last_hidden_states[:, -1]
        seq_len = attention_mask.sum(dim=1) - 1
        bs = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(bs, device=last_hidden_states.device), seq_len]

    result: dict[str, np.ndarray] = {}
    with torch.no_grad():
        for i in range(0, len(unique), batch_size):
            batch = unique[i:i + batch_size]
            enc = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt")
            enc = {k: v.to(model.device) for k, v in enc.items()}
            out = model(**enc)
            emb = last_token_pool(out.last_hidden_state, enc["attention_mask"]).float()
            emb = F.normalize(emb, p=2, dim=1).cpu().numpy().astype(np.float32)
            for txt, vec in zip(batch, emb, strict=True):
                result[txt] = vec
    return result


def build_attr_layout(choices: dict[str, list[str]]) -> tuple[list[dict], int]:
    layout = []
    offset = 0
    for key in ATTR_KEYS:
        vals = choices[key]
        layout.append({"key": key, "offset": offset, "dim": len(vals), "values": vals})
        offset += len(vals)
    assert offset == 55, f"expected 55 attr dims, got {offset}"
    return layout, offset


def encode_attrs(rec: dict | None, choices: dict[str, list[str]], attr_dim: int) -> tuple[np.ndarray, float]:
    vec = np.zeros(attr_dim, dtype=np.float32)
    if rec is None:
        return vec, 1.0  # parse_fail flag = 1.0
    offset = 0
    for key in ATTR_KEYS:
        vals = choices[key]
        val = rec["visibility"] if key == "visibility" else rec["attributes"].get(key)
        if val is not None:
            idx = vals.index(val)
            vec[offset + idx] = 1.0
        offset += len(vals)
    return vec, 0.0


def check_coverage(rows: list[dict], expected_ids: set[str]) -> dict:
    got = {r["frame"] for r in rows}
    return {
        "expected": len(expected_ids),
        "got": len(got),
        "missing": sorted(expected_ids - got),
        "extra": sorted(got - expected_ids),
        "exact_match": got == expected_ids and len(rows) == len(expected_ids),
    }


def main():
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "VLLM_NO_USAGE_STATS", "DO_NOT_TRACK"):
        os.environ[key] = "1"
    os.environ["WANDB_MODE"] = "offline"

    ap = argparse.ArgumentParser()
    ap.add_argument("--gen-dir", type=Path, required=True)
    ap.add_argument("--repeat-dir", type=Path, required=True)
    ap.add_argument("--batch-size", type=int, default=128)
    a = ap.parse_args()

    frozen_sha = (OUT / "frozen_prompt.sha256").read_text().strip()
    choices = cap.options()
    attr_layout, attr_dim = build_attr_layout(choices)
    vec_dim = 3 * EMB_DIM + attr_dim + 1
    assert vec_dim == 3128

    # 1. 生成結果の読み込み・被覆・プロンプト・test 検査
    expected_samples = cap.frames("generate")
    expected_by_split = {
        "train": sorted(p.stem for sp, p in expected_samples if sp == "train"),
        "val": sorted(p.stem for sp, p in expected_samples if sp == "val"),
    }
    expected_all = set(expected_by_split["train"]) | set(expected_by_split["val"])

    rows = load_jsonl_dir(a.gen_dir)
    cov = check_coverage(rows, expected_all)
    if not cov["exact_match"]:
        raise SystemExit(f"生成フレームの被覆が一致しない: {cov}")
    # 陽性対照 (§9 e): 記述を 1 件消した写しで欠け 1 件を出す
    cov_pos_ctrl = check_coverage(rows[:-1], expected_all)

    prompt_shas = sorted({r["prompt_sha256"] for r in rows})
    if prompt_shas != [frozen_sha]:
        raise SystemExit(f"本番出力の prompt_sha256 が固定値と不一致: {prompt_shas} vs {frozen_sha}")

    gen_videos = C.assert_no_test([r["frame"] for r in rows], "task_c/generate")
    # 陽性対照 (§9 j): 04 を混ぜた入力で共通 1 件を出す
    try:
        C.assert_no_test([r["frame"] for r in rows] + ["04_1_0001"], "task_c/pos_ctrl_04")
        pos_ctrl_04 = {"caught": False}
    except RuntimeError as exc:
        pos_ctrl_04 = {"caught": True, "message": str(exc), "overlap": sorted((set(gen_videos) | {"04"}) & C.TEST_VIDEOS)}

    row_by_frame = {r["frame"]: r for r in rows}

    # 2. 繰り返し一致（val 等間隔 50 枚）
    rep_rows = load_jsonl_dir(a.repeat_dir)
    rep_exact_raw = 0
    rep_exact_parsed = 0
    for rr in rep_rows:
        orig = row_by_frame[rr["frame"]]
        if rr["raw"] == orig["raw"]:
            rep_exact_raw += 1
        if rr["parsed"] == orig["parsed"]:
            rep_exact_parsed += 1

    # 3. 記述の統計 (§3.6) と伏せ字（甲・乙・丙）
    parse_errors = Counter(r["parse_error"] for r in rows if r["parse_error"])
    refusals = sum(1 for r in rows if r["refusal"])
    attr_dist = {k: Counter() for k in ATTR_KEYS}
    cannot_tell = Counter()
    raw_text_counts = {f: Counter() for f in cap.TEXT_FIELDS}
    for r in rows:
        p = r["parsed"]
        if p is None:
            continue
        for f in cap.TEXT_FIELDS:
            raw_text_counts[f][p[f]] += 1
        for k in ATTR_KEYS:
            v = p["visibility"] if k == "visibility" else p["attributes"][k]
            attr_dist[k][v] += 1
            if v == "cannot tell":
                cannot_tell[k] += 1

    redacted: dict[str, dict[str, dict | None]] = {m: {} for m in MODES}
    red_hit_counts = {m: Counter() for m in MODES}
    all_texts_to_embed: list[str] = []
    for m in MODES:
        for r in rows:
            rec, cnt = red.redact_record(r["parsed"], choices, m)
            redacted[m][r["frame"]] = rec
            red_hit_counts[m].update(cnt)
            if rec is not None:
                for f in cap.TEXT_FIELDS:
                    if rec[f]:
                        all_texts_to_embed.append(rec[f])

    # val 等間隔 20 件の記述（甲の伏せ字後）
    val_sorted = expected_by_split["val"]
    ex20_frames = cap.equidistant(val_sorted, 20)
    examples_20 = []
    for fid in ex20_frames:
        r = row_by_frame[fid]
        examples_20.append({
            "frame": fid,
            "video": r["video"],
            "parse_error": r["parse_error"],
            "ko_redacted": redacted["ko"][fid],
        })

    # タイミング統計
    seen_batch = {}
    for r in rows:
        bkey = (r["batch_seconds"], r["batch_size"])
        seen_batch[bkey] = seen_batch.get(bkey, 0) + 1
    gen_summary = json.loads((a.gen_dir / "summary.json").read_text())
    # 各 part ファイルの最初の行から batch_seconds を合算
    total_batch_sec = 0.0
    for part in sorted(a.gen_dir.glob("part-*.jsonl")):
        first = json.loads(part.read_text().splitlines()[0])
        total_batch_sec += float(first["batch_seconds"])

    caption_stats = {
        "gen_dir": str(a.gen_dir),
        "prompt_sha256": frozen_sha,
        "coverage": cov,
        "coverage_positive_control_drop1": {
            "missing_count": len(cov_pos_ctrl["missing"]),
            "exact_match": cov_pos_ctrl["exact_match"],
        },
        "videos": gen_videos,
        "test_overlap": sorted(set(gen_videos) & C.TEST_VIDEOS),
        "test_positive_control_04": pos_ctrl_04,
        "n_frames": len(rows),
        "n_train": len(expected_by_split["train"]),
        "n_val": len(expected_by_split["val"]),
        "parse_ok": len(rows) - sum(parse_errors.values()),
        "parse_error_count": sum(parse_errors.values()),
        "parse_error_breakdown": dict(parse_errors),
        "refusals": refusals,
        "cannot_tell_rate": {k: cannot_tell[k] / max(len(rows) - sum(parse_errors.values()), 1) for k in ATTR_KEYS},
        "attr_distribution": {k: dict(v) for k, v in attr_dist.items()},
        "text_uniqueness": {
            f: {
                "unique": len(raw_text_counts[f]),
                "total": sum(raw_text_counts[f].values()),
                "duplicate_entries": sum(raw_text_counts[f].values()) - len(raw_text_counts[f]),
                "top5": raw_text_counts[f].most_common(5),
            }
            for f in cap.TEXT_FIELDS
        },
        "redaction_hits": {m: dict(red_hit_counts[m]) for m in MODES},
        "redaction_prompt_check": red.check_prompt_choices(choices),
        "repeat_50": {
            "n": len(rep_rows),
            "exact_raw_match": rep_exact_raw,
            "exact_raw_rate": rep_exact_raw / max(len(rep_rows), 1),
            "exact_parsed_match": rep_exact_parsed,
            "exact_parsed_rate": rep_exact_parsed / max(len(rep_rows), 1),
        },
        "timing": {
            "total_batch_seconds": total_batch_sec,
            "seconds_per_frame": total_batch_sec / len(rows),
            "wall_seconds_summary": gen_summary.get("wall_seconds_this_invocation"),
        },
    }
    C.write_json(OUT / "caption_stats.json", caption_stats)
    C.write_json(OUT / "val_examples_20.json", examples_20)
    print(f"[build_signals] captions stats written: n={len(rows)}, parse_err={caption_stats['parse_error_count']}, "
          f"repeat_raw={caption_stats['repeat_50']['exact_raw_rate']:.4f}", flush=True)

    # 4. 文埋め込み（一意テキストを一括計算）
    print(f"[build_signals] embedding unique texts...", flush=True)
    emb_map = embed_unique_texts(all_texts_to_embed, batch_size=a.batch_size)
    norms = [float(np.linalg.norm(v)) for v in emb_map.values()]
    print(f"[build_signals] embedded {len(emb_map)} unique texts, norm min={min(norms):.6f} max={max(norms):.6f}", flush=True)

    # 5. 入れ替え対応表の検証・準備 (§4.3)
    mappings = {}
    mapping_meta = {}
    for split in ("train", "val"):
        fids = expected_by_split[split]
        prev_path = C.FIX_STORE / f"signals/shuffle/mapping_{split}.json"
        prev_mp = json.loads(prev_path.read_text())["mapping"]
        if set(prev_mp.keys()) == set(fids) and set(prev_mp.values()) == set(fids):
            mp = prev_mp
            source = str(prev_path)
            reused = True
        else:
            mp = make_mapping(fids, seed=42)
            source = "newly_generated_seed42"
            reused = False
        st = mapping_stats(mp)
        # 陽性対照: 恒等の並べ替えで不動点割合が 1.0
        ident = {f: f for f in fids}
        ident_st = mapping_stats(ident)
        mappings[split] = mp
        mapping_meta[split] = {
            "source": source,
            "reused_prev_mapping": reused,
            "videos": C.assert_no_test(fids, f"task_c/mapping_{split}"),
            **st,
            "identity_control_fixed_point_fraction": ident_st["fixed_point_fraction"],
        }

    # 6. 三通り（甲・乙・丙）の数値信号と入れ替え信号の作成・保存・検算
    sig_dir = OUT / "signals"
    sig_dir.mkdir(parents=True, exist_ok=True)
    zero_emb = np.zeros(EMB_DIM, dtype=np.float32)

    manifest = {
        "embedding_model": str(EMB_MODEL),
        "embedding_dim": EMB_DIM,
        "vec_dim": vec_dim,
        "vec_layout": [
            {"name": "wound_emb", "offset": 0, "dim": EMB_DIM},
            {"name": "tissue_action_emb", "offset": EMB_DIM, "dim": EMB_DIM},
            {"name": "surface_emb", "offset": 2 * EMB_DIM, "dim": EMB_DIM},
            {"name": "attributes_onehot", "offset": 3 * EMB_DIM, "dim": attr_dim, "fields": attr_layout},
            {"name": "parse_fail_flag", "offset": 3 * EMB_DIM + attr_dim, "dim": 1},
        ],
        "tok_shape": [4, EMB_DIM],
        "tok_layout": [
            {"index": 0, "name": "wound_emb", "dim": EMB_DIM},
            {"index": 1, "name": "tissue_action_emb", "dim": EMB_DIM, "hei_masked": True},
            {"index": 2, "name": "surface_emb", "dim": EMB_DIM},
            {"index": 3, "name": "attributes_and_flag_padded", "used_dim": attr_dim + 1, "dim": EMB_DIM},
        ],
        "embedding_norm_range": {"unique_texts": len(emb_map), "min": min(norms), "max": max(norms)},
        "mappings": mapping_meta,
        "files": {},
    }

    for mode in MODES:
        for split in ("train", "val"):
            fids = expected_by_split[split]
            n = len(fids)
            vec_arr = np.zeros((n, vec_dim), dtype=np.float32)
            tok_arr = np.zeros((n, 4, EMB_DIM), dtype=np.float32)
            mask_arr = np.ones((n, 4), dtype=bool)
            if mode == "hei":
                mask_arr[:, 1] = False

            for i, fid in enumerate(fids):
                rec = redacted[mode][fid]
                e0 = emb_map.get(rec["wound"], zero_emb) if rec is not None else zero_emb
                e1 = emb_map.get(rec["tissue_action"], zero_emb) if (rec is not None and mode != "hei") else zero_emb
                e2 = emb_map.get(rec["surface"], zero_emb) if rec is not None else zero_emb
                attr_vec, fail_flag = encode_attrs(rec, choices, attr_dim)

                vec_arr[i, 0:EMB_DIM] = e0
                vec_arr[i, EMB_DIM:2 * EMB_DIM] = e1
                vec_arr[i, 2 * EMB_DIM:3 * EMB_DIM] = e2
                vec_arr[i, 3 * EMB_DIM:3 * EMB_DIM + attr_dim] = attr_vec
                vec_arr[i, 3 * EMB_DIM + attr_dim] = fail_flag

                tok_arr[i, 0] = e0
                tok_arr[i, 1] = e1
                tok_arr[i, 2] = e2
                tok_arr[i, 3, :attr_dim] = attr_vec
                tok_arr[i, 3, attr_dim] = fail_flag

            assert np.isfinite(vec_arr).all() and np.isfinite(tok_arr).all()
            if mode == "hei":
                assert float(np.abs(vec_arr[:, EMB_DIM:2 * EMB_DIM]).max()) == 0.0
                # action (offset 3*1024 + 37..49) と target (49..55) も 0
                act_off = 3 * EMB_DIM + next(x["offset"] for x in attr_layout if x["key"] == "action")
                tgt_off = 3 * EMB_DIM + next(x["offset"] for x in attr_layout if x["key"] == "target")
                assert float(np.abs(vec_arr[:, act_off:act_off + 12]).max()) == 0.0
                assert float(np.abs(vec_arr[:, tgt_off:tgt_off + 6]).max()) == 0.0
                assert not mask_arr[:, 1].any()

            # 予測の信号保存
            vpath = sig_dir / f"vec_{mode}_{split}.npz"
            tpath = sig_dir / f"tok_{mode}_{split}.npz"
            vsha = C.save_signal(vpath, fids, vec_arr)
            tsha = C.save_signal(tpath, fids, tok_arr, mask=mask_arr)

            # 入れ替えの信号作成・保存・逆並べ替え検証
            mp = mappings[split]
            idx_of = {f: i for i, f in enumerate(fids)}
            perm_rows = [idx_of[mp[f]] for f in fids]
            inv_rows = [0] * n
            for i, p in enumerate(perm_rows):
                inv_rows[p] = i

            vec_shuf = vec_arr[perm_rows]
            tok_shuf = tok_arr[perm_rows]
            mask_shuf = mask_arr[perm_rows]
            assert np.array_equal(vec_shuf[inv_rows], vec_arr)
            assert np.array_equal(tok_shuf[inv_rows], tok_arr)
            assert np.array_equal(mask_shuf[inv_rows], mask_arr)

            v_sd_orig = sorted_digest(vec_arr, None)
            v_sd_shuf = sorted_digest(vec_shuf, None)
            assert v_sd_orig == v_sd_shuf

            vs_path = sig_dir / f"vec_{mode}_shuffle_{split}.npz"
            ts_path = sig_dir / f"tok_{mode}_shuffle_{split}.npz"
            vssha = C.save_signal(vs_path, fids, vec_shuf)
            tssha = C.save_signal(ts_path, fids, tok_shuf, mask=mask_shuf)

            manifest["files"][f"vec_{mode}_{split}"] = {
                "path": str(vpath), "sha256": vsha, "shape": list(vec_arr.shape), "n_frames": n,
                "videos": C.assert_no_test(fids, f"sig/vec_{mode}_{split}"),
                "sorted_digest": v_sd_orig,
            }
            manifest["files"][f"vec_{mode}_shuffle_{split}"] = {
                "path": str(vs_path), "sha256": vssha, "shape": list(vec_shuf.shape), "n_frames": n,
                "videos": C.assert_no_test(fids, f"sig/vec_{mode}_shuffle_{split}"),
                "sorted_digest": v_sd_shuf, "value_set_equal": v_sd_orig == v_sd_shuf,
                "inverse_exact_match": True, "differs_from_source": vssha != vsha,
            }
            manifest["files"][f"tok_{mode}_{split}"] = {
                "path": str(tpath), "sha256": tsha, "shape": list(tok_arr.shape), "n_frames": n,
                "mask_true_per_slot": mask_arr.sum(0).tolist(),
            }
            manifest["files"][f"tok_{mode}_shuffle_{split}"] = {
                "path": str(ts_path), "sha256": tssha, "shape": list(tok_shuf.shape), "n_frames": n,
                "mask_true_per_slot": mask_shuf.sum(0).tolist(), "inverse_exact_match": True,
                "differs_from_source": tssha != tsha,
            }

    C.write_json(OUT / "signals_manifest.json", manifest)
    print("[build_signals] DONE. All 24 signal files written and verified.", flush=True)


if __name__ == "__main__":
    main()
