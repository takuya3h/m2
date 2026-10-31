#!/usr/bin/env python
"""T1b Phase→Det トレーナー（MT4MTL-KD-style §4.6 双方向の Phase→Det 半分・①予測相互作用 L3）。

凍結 S4 工程モデルの per-frame 事後分布（phase context, 9-d）を条件に、Relation-DETR の C5 を
**FiLM 注入**して検出を学習する。**s0_016（=S0-frozen seed42）から warm-start**し、FiLM は
zero-init=恒等なので warm-start 直後は S0-frozen と一致 → fine-tune で phase 変調を学習する。
Δ_detection=(T1b − S0-frozen 0.7051)。§4.6 の注入効果分離のため `--zero-ctx`（context を 0 に
固定した同スケジュール fine-tune）対照を用意する。

注入機構（§4.6・プロトコルは共通、差分は注入のみ→清潔な ablation）:
  --inject film      : C5 を FiLM 変調（§4.6 下限・既定。RelationDETRPhaseFiLM）
  --inject ca        : decoder cross-attention に c_phase token を注入（§4.6 primary。RelationDETRPhaseCrossAttn）
  --inject camt      : 真の query-selective・multi-token CA（phase を P prototype token に展開。RelationDETRPhaseCrossAttnMT）

学習対象（warm-start fine-tune の範囲）:
  --trainable film   : 注入層(phase_*)のみ学習（最速・最純粋な注入効果。検出器は凍結）
  --trainable all    : 注入層 + 検出器全体を fine-tune（容量大・対照必須）

入力:
  data/processed/phase_context/relation_detr_seed42/{split}_phasectx.npz（frame_ids, ctx=(N,9)）
  検出: data/annotations/egosurgery_tool/instances_{train,val}.json + data/raw/ego
  warm-start init: data/external/weights/relation_detr_s0frozen_init_seed42.pth（= s0_016）

成果物（永続・工程側 ExperimentManager と同一規約）:
  experiments/transfer/<run_name>/
    checkpoints/best_t1b.pth / predictions/{split}_{inj|ctrl}_{ep-1,best}.json.gz
    logs/val_metrics_by_epoch.json / config.yaml / command.sh / git_commit.txt
    metrics.json / per_class_ap.json / t1b_result.json / server.txt
  ※ 旧実装は /tmp に出していたため再起動で消え、eval-only の追認が反復的に不能になった。
     predictions を既定 on にしてあるのは、ckpt が失われても per-image 解析（FP/FN 内訳・
     工程別品質・定性可視化）を後から実行できる状態を担保するため。

実行（.venv-relation-detr, cwd=third_party/Relation-DETR）:
  source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda
  python /abs/scripts/train_t1b.py --seed 42 --epochs 6
  python /abs/scripts/train_t1b.py --smoke           # 数 step・warm-start mAP 検証
  python /abs/scripts/train_t1b.py --zero-ctx ...     # §4.6 対照（注入効果分離）
  python /abs/scripts/train_t1b.py --run-name t1b_camt_seed42_inj ...  # 保存先を明示
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

BODY = Path(os.environ.get("EGO_BODY", Path(__file__).resolve().parents[1]))
RELDETR = BODY / "third_party" / "Relation-DETR"
# os.chdir(RELDETR) 後でも scripts/ の兄弟モジュールを import できるよう絶対パスで通す。
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RELDETR))
os.chdir(RELDETR)

import run_artifacts as ra  # noqa: E402  (sys.path 追加後に import する必要がある)

PHASECTX_DIR = BODY / "data/processed/phase_context/relation_detr_seed42"
S0FROZEN_INIT = BODY / "data/external/weights/relation_detr_s0frozen_init_seed42.pth"
EGO_ROOT = os.environ.get("EGO_ROOT", str(BODY / "data/raw/ego"))
ANN_DIR = os.environ.get("EGO_ANN_DIR", str(BODY / "data/annotations/egosurgery_tool"))
MODEL_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py"
MODEL_CFG_CA = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_ca.py"
MODEL_CFG_CAMT = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_camt.py"
MODEL_CFG_HC = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_hc.py"
MODEL_CFG_CLSBIAS = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_clsbias.py"
NUM_PHASES = 9


def load_phase_ctx(split: str) -> dict:
    """frame_id -> ctx(9,) float32。検出 image_id とは file_name の stem で突き合わせる。"""
    d = np.load(PHASECTX_DIR / f"{split}_phasectx.npz")
    ctx_all = d["ctx"]
    return {str(fid): ctx_all[i].astype(np.float32) for i, fid in enumerate(d["frame_ids"])}


def load_oracle_phase_ctx(split: str) -> dict:
    """§18.4 L1-2 oracle-phase: phase_manifest から GT label を読み、frame_id -> one-hot(9)。

    実用上の S4 TeCNO 予測（softmax 出力）の代わりに **完全に正確な phase 情報**を注入する。
    これで mAP が改善しなければ phase→det 機構非依存性が最終確定（phase 推定誤差ではなく
    phase 情報そのものが det に貢献しないことを実証）。
    """
    man_path = BODY / "data" / "processed" / "phase_manifest" / f"{split}.json"
    man = json.loads(man_path.read_text())
    out: dict[str, np.ndarray] = {}
    for clip in man["clips"]:
        for fr in clip["frames"]:
            fid = str(fr["frame"])
            lbl = int(fr["label"])
            v = np.zeros(NUM_PHASES, dtype=np.float32)
            v[lbl] = 1.0
            out[fid] = v
    return out


def load_both_phase_ctx(split: str) -> dict:
    """正解 one-hot(9) ⊕ 予測事後(9) = 18-d。参照入力四段の「正解 ⊕ 予測」段。

    連結順は **正解 → 予測** に固定する。frame_id が食い違えば Fail Loud（補完しない）。
    """
    o = load_oracle_phase_ctx(split)
    r = load_phase_ctx(split)
    diff = set(o) ^ set(r)
    if diff:
        raise KeyError(f"[t1b] 正解と予測で frame_id が食い違う: {len(diff)} 件 ({split})")
    return {fid: np.concatenate([o[fid], r[fid]]).astype(np.float32) for fid in o}


def resolve_phase_ctx_loader(source: str):
    """`--phase-source` の値から ctx loader 関数を返す。'real'=S4 予測、'oracle'=GT one-hot、
    'both'=正解 ⊕ 予測（18-d）。"""
    if source == "oracle":
        return load_oracle_phase_ctx
    if source == "both":
        return load_both_phase_ctx
    return load_phase_ctx


def load_signal_npz(path) -> dict:
    """frame_id -> 信号（float32）。``np.savez(frame_ids=, x=)`` の形（scripts/stage2pilot/common.save_signal）。

    `--signal-train/--signal-val` を渡したときだけ使う（契約 T-2026-10-18-stage2-pilot-folda）。
    次元は 9 に限らない（正解 ⊕ 予測の 18 など）。
    """
    d = np.load(path)
    x = d["x"].astype(np.float32)  # d["x"] は参照のたびに全体を読み直すので一度だけ読む
    return {str(fid): x[i] for i, fid in enumerate(d["frame_ids"])}


def resolve_ctx_sources(args):
    """(train の ctx, val の ctx, 次元) を返す。既定は従来どおり `--phase-source` の loader（9 次元）。"""
    if args.signal_train or args.signal_val:
        if not (args.signal_train and args.signal_val):
            raise SystemExit("[t1b] --signal-train と --signal-val は両方渡す")
        tr, va = load_signal_npz(args.signal_train), load_signal_npz(args.signal_val)
        dims = {v.shape[0] for v in tr.values()} | {v.shape[0] for v in va.values()}
        if len(dims) != 1:
            raise SystemExit(f"[t1b] 信号の次元が揃わない: {dims}")
        return tr, va, dims.pop()
    loader = resolve_phase_ctx_loader(args.phase_source)
    return loader("train"), loader("val"), NUM_PHASES


def build_imgid_to_ctx(coco, ctx_by_frame: dict, dim: int = NUM_PHASES):
    """coco.imgs[image_id].file_name の stem を frame_id とみなし image_id->ctx を作る。

    欠落（検出 frame に phase ctx 無し）は zero ctx（=恒等 FiLM）で fail-safe。件数を返す。
    """
    imgid_to_ctx, miss = {}, 0
    for image_id, info in coco.imgs.items():
        fid = Path(info["file_name"]).stem
        ctx = ctx_by_frame.get(fid)
        if ctx is None:
            ctx = np.zeros(dim, dtype=np.float32)
            miss += 1
        imgid_to_ctx[image_id] = ctx
    return imgid_to_ctx, miss


def build_det_loader(train: bool):
    from datasets.coco import CocoDetection
    from torch.utils import data
    from transforms import presets
    from util.collate_fn import collate_fn
    from util.group_by_aspect_ratio import (
        GroupedBatchSampler,
        create_aspect_ratio_groups,
    )

    ann = "instances_train.json" if train else "instances_val.json"
    ds = CocoDetection(img_folder=EGO_ROOT, ann_file=f"{ANN_DIR}/{ann}",
                       transforms=presets.detr if train else None, train=train)
    params = dict(num_workers=4, collate_fn=collate_fn, pin_memory=True)
    if train:
        group_ids = create_aspect_ratio_groups(ds, k=3)
        bs = GroupedBatchSampler(data.RandomSampler(ds), group_ids, 2)
        return data.DataLoader(ds, batch_sampler=bs, **params)
    return data.DataLoader(ds, 1, shuffle=False, **params)


def detector_ckpt(seed: int) -> Path:
    """seed 対応の **学習済み 15クラス検出器**（s0_016/017/018 = warm-start 元・分母 S0-frozen 源）。

    注意: data/external/weights/relation_detr_s0frozen_init_seed42.pth は COCO(91class)初期化で
    別物（B1 が 12ep 学習する出発点）。T1b は収束済み検出器から warm-start するのでこちらを使う。
    """
    return RELDETR / f"checkpoints/incoming/seed{seed}/best_ap.pth"


def resolve_detector_ckpt(seed: int, override=None) -> Path:
    """`--det-ckpt` を渡したときだけそれを使う。既定は従来どおり ``detector_ckpt(seed)``。"""
    return Path(override) if override else detector_ckpt(seed)


def build_model(device, seed: int, model_cfg: str = MODEL_CFG, ckpt_override=None):
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict
    model = Config(model_cfg).model
    ck = resolve_detector_ckpt(seed, ckpt_override)
    if not ck.exists():
        raise FileNotFoundError(f"学習済み検出器 ckpt が無い: {ck}（s0_01{{6,7,8}} を転送せよ）")
    ckpt = load_checkpoint(str(ck))
    if isinstance(ckpt, dict) and "model" in ckpt:
        ckpt = ckpt["model"]
    load_state_dict(model, ckpt)  # phase_film は missing → zero-init 維持（=恒等）
    print(f"[t1b] warm-start from {ck}")
    return model.to(device)


def register_classes(model, det_loader):
    from util.misc import encode_labels
    coco = det_loader.dataset.coco
    cat_ids = list(range(max(coco.cats.keys()) + 1))
    classes = tuple(coco.cats.get(c, {"name": "none"})["name"] for c in cat_ids)
    model.register_buffer("_classes_", torch.tensor(encode_labels(classes)))


def ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx: bool, dim: int = NUM_PHASES):
    """det バッチの targets（image_id 付き）→ (B,dim) phase context。zero_ctx 対照は 0。"""
    B = len(targets)
    if zero_ctx:
        return torch.zeros(B, dim, device=device)
    rows = [imgid_to_ctx.get(int(t["image_id"]), np.zeros(dim, dtype=np.float32))
            for t in targets]
    return torch.from_numpy(np.stack(rows)).to(device)


@torch.no_grad()
def eval_detection(model, loader, imgid_to_ctx, device, zero_ctx, limit=None,
                   collect_predictions=False, dim: int = NUM_PHASES):
    """val 検出評価。``collect_predictions=True`` のときだけ per-image 予測も返す。

    戻り値の arity を既定では変えない（既存呼び出しは無改変で動く）。
    ``collect_predictions=True`` では ``(mAP, per_class, preds)`` を返し、``preds`` は
    ``{"results": COCO detection results, "image_ids": 評価対象 image_id 列}``。
    ``results`` は **AP 算出に実際に使われた実体そのもの**（``CocoEvaluator.accumulate()``
    が ``predictions["bbox"]`` を COCO results 形式へ変換して保持する）なので、
    これを保存して再評価すれば mAP が bit-exact に再現する。
    """
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    model.eval()
    coco = get_coco_api_from_dataset(loader.dataset)
    evaluator = CocoEvaluator(coco, ["bbox"])
    for i, (images, targets) in enumerate(loader):
        if limit is not None and i >= limit:
            break
        images = [img.to(device) for img in images]
        model.set_phase_context(ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx, dim))
        if hasattr(model, "set_grasp_maps"):  # 案 B の地図（契約 T-2026-10-31-grasp-pilot-probe）。持たない検出器では何もしない
            model.set_grasp_maps([t["grasp_map"] for t in targets])
        outputs = model(images)
        outputs = [{k: v.to("cpu") for k, v in t.items()} for t in outputs]
        evaluator.update({t["image_id"]: o for t, o in zip(targets, outputs)})
    evaluator.synchronize_between_processes()
    evaluator.accumulate()
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        evaluator.summarize()
    bbox = evaluator.coco_eval["bbox"]
    cat_names = [c["name"] for c in coco.loadCats(coco.getCatIds())]
    prec = bbox.eval["precision"]
    per_class = {}
    for ci, name in enumerate(cat_names):
        vals = prec[:, :, ci, 0, 2]
        vals = vals[vals > -1]
        per_class[name] = float(vals.mean()) if vals.size else float("nan")
    if not collect_predictions:
        return float(bbox.stats[0]), per_class
    preds = {
        "results": evaluator.predictions["bbox"],
        "image_ids": sorted({int(i) for i in evaluator.img_ids}),
    }
    return float(bbox.stats[0]), per_class, preds


def set_trainable(model, mode: str):
    """warm-start fine-tune の範囲。film=注入層(phase_*)のみ学習（残り凍結）/ all=全 fine-tune。

    注入層は FiLM の ``phase_film.*`` / CA の ``phase_embed|phase_attn|phase_norm.*`` を ``phase`` で一括選択
    （base 検出器に ``phase`` を含む param は無いので film/ca どちらでも安全）。
    w2=注入層 + decoder の最終層とその層のクラスと box のヘッド（契約 T-2026-10-18-stage2-pilot-folda の W2）。
    """
    if mode == "film":
        for name, p in model.named_parameters():
            p.requires_grad_("phase" in name)
    elif mode == "w2":
        from stage2pilot.pd_model import w2_parameter_names
        w2 = set(w2_parameter_names(model))
        for name, p in model.named_parameters():
            p.requires_grad_("phase" in name or name in w2)
    # mode == "all" は config の freeze_indices(backbone) 以外すべて学習（既定の requires_grad）。


def frozen_digest(model) -> str:
    """学習しない重みと、注入層以外の buffer の要約値（学習の前後で同じであることの確認用）。"""
    import hashlib
    trainable = {n for n, p in model.named_parameters() if p.requires_grad}
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        if k in trainable or k.startswith("phase"):
            continue
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().float().numpy().tobytes())
    return h.hexdigest()


def gate_record(model) -> dict:
    """ゲートを持つ界面（契約 T-2026-10-19-stage2-pilot-four-new-types の pd_four）のゲートの値。持たない検出器では空。"""
    return {"gates": model.gate_values()} if hasattr(model, "gate_values") else {}


def trainable_state(model) -> dict:
    """学習対象の重みと注入層の buffer だけの state（`--save-trainable-only`）。"""
    names = {n for n, p in model.named_parameters() if p.requires_grad}
    state = {k: v.detach().cpu() for k, v in model.state_dict().items()
             if k in names or k.startswith("phase")}
    return state


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    if args.missed_set:
        # 契約 T-2026-10-19-stage2-pilot-four-new-types の extra_q。labels に見落としの印を足した train の読み込み（同じ増強）
        from stage2pilot.pd_four import build_missed_train_loader, load_missed_ids
        det_train = build_missed_train_loader(EGO_ROOT, ANN_DIR, load_missed_ids(args.missed_set))
    elif args.grasp_map:
        # 契約 T-2026-10-31-grasp-pilot-probe の案 B。同じ読み込み・同じ増強に、画像と同じ変換を掛けた把持の地図を足す
        from grasppilot import grasp_signals as grasp_g
        from grasppilot.pd_grasp import build_grasp_loader
        grasp_index = grasp_g.HTSIndex(("train", "val"))
        det_train = build_grasp_loader(EGO_ROOT, ANN_DIR, True, args.grasp_map, grasp_index)
    else:
        det_train = build_det_loader(train=True)
    if args.grasp_map:
        det_val = build_grasp_loader(EGO_ROOT, ANN_DIR, False, args.grasp_map, grasp_index)
    else:
        det_val = build_det_loader(train=False)
    model_cfg = {"ca": MODEL_CFG_CA, "camt": MODEL_CFG_CAMT, "hc": MODEL_CFG_HC,
                 "clsbias": MODEL_CFG_CLSBIAS}.get(args.inject, MODEL_CFG)
    # 明示 override（T1B_WORK_DIR / T1B_RUN_NAME と同じ作法）。phase ctx の次元を変える段
    # （正解 ⊕ 予測 = 18-d）で num_phases 違いの model config を指すために要る。
    model_cfg = os.environ.get("T1B_MODEL_CFG") or model_cfg
    model = build_model(device, args.seed, model_cfg, ckpt_override=args.det_ckpt)
    register_classes(model, det_train)
    set_trainable(model, args.trainable)
    frozen_before = frozen_digest(model) if args.save_trainable_only else None
    if args.fixed_table:
        model.set_fixed_table(np.asarray(json.loads(Path(args.fixed_table).read_text())["B"], dtype=np.float32))

    if args.grasp_map:
        if args.signal_train or args.signal_val:
            raise SystemExit("[t1b] --grasp-map は --signal-train・--signal-val と組み合わせない")
        ctx_train_src, ctx_val_src, ctx_dim = {}, {}, 1  # 案 B の検出器は信号を使わない（地図だけ）
    else:
        ctx_train_src, ctx_val_src, ctx_dim = resolve_ctx_sources(args)
    ctx_tr = build_imgid_to_ctx(det_train.dataset.coco, ctx_train_src, ctx_dim)
    ctx_va = build_imgid_to_ctx(det_val.dataset.coco, ctx_val_src, ctx_dim)
    imgid_to_ctx_tr, miss_tr = ctx_tr
    imgid_to_ctx_va, miss_va = ctx_va
    if args.signal_train and (miss_tr or miss_va):
        raise SystemExit(f"[t1b] 信号の無い検出フレームがある（train {miss_tr} / val {miss_va}）。補完しない")

    if args.eval_only:
        args.epochs = 0  # 学習しない（学習対象の無い型の評価）。学習前の評価だけを残す
    else:
        from optimizer import param_dict
        groups = param_dict.finetune_t1b(model, lr=args.lr, film_lr=args.film_lr)
        opt = torch.optim.AdamW(groups, lr=args.lr, weight_decay=1e-4, betas=(0.9, 0.999))
    # TF32。**既定 off では設定に触れない**（触れること自体が既定値の再確認になり、
    # 将来 torch の既定が変わったときに挙動が固定されてしまうため）。
    if args.tf32:
        torch.backends.cuda.matmul.allow_tf32 = True
    # 自動混合精度。既定 no では autocast を張らず scaler も作らないため、経路は従来と同一。
    amp_dtype = {"bf16": torch.bfloat16, "fp16": torch.float16}.get(args.amp)
    scaler = torch.cuda.amp.GradScaler() if args.amp == "fp16" else None
    # 止め方。既定は従来どおり固定 epoch と epochs-2 での学習率低下。`--patience` を渡したときだけ
    # 学習率を一定に保ち、val mAP が patience epoch 改善しなければ止める（上限は --epochs）。
    # 固定の学習率低下と早期打ち切りを組み合わせない（契約 T-2026-10-18-stage2-pilot-folda の止め方の規則）。
    if args.fixed_epochs and (args.patience is not None or args.eval_only):
        raise SystemExit("[t1b] --fixed-epochs は --patience・--eval-only と組み合わせない")
    if args.eval_only or args.patience is not None or args.fixed_epochs:
        sched = None
    else:
        sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=[max(args.epochs - 2, 1)], gamma=0.1)

    det_steps_per_ep = len(det_train)
    if args.smoke:
        args.epochs = 1
        det_steps_cap = 6
    else:
        det_steps_cap = None

    # 成果物は experiments/transfer/<run_name>/ に永続化する（旧: /tmp → 消失して
    # eval-only の追認が反復的に不能になっていた）。T1B_WORK_DIR は明示 override として存置。
    variant = "ctrl" if args.zero_ctx else "inj"
    run_name = (args.run_name or os.environ.get("T1B_RUN_NAME")
                or f"t1b_{args.inject}_{args.trainable}_{variant}_seed{args.seed}")
    work = ra.resolve_run_dir(run_name, work_dir=os.environ.get("T1B_WORK_DIR"))
    ra.ensure_layout(work)
    save_preds = not args.no_save_predictions
    compress_preds = not args.predictions_no_gzip
    n_phase = sum(p.numel() for n, p in model.named_parameters() if p.requires_grad and "phase" in n)
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[t1b] seed={args.seed} inject={args.inject} trainable={args.trainable} zero_ctx={args.zero_ctx} "
          f"det_steps/ep={det_steps_per_ep} phase_params={n_phase} total_trainable={n_train} "
          f"miss_ctx(tr/va)={miss_tr}/{miss_va} work={work}", flush=True)
    ra.write_evidence(work, config={
        "run_name": run_name, "variant": variant, "seed": args.seed, "inject": args.inject,
        "trainable": args.trainable, "zero_ctx": bool(args.zero_ctx), "epochs": args.epochs,
        "amp": args.amp, "tf32": bool(args.tf32),
        "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
        "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
        "lr": args.lr, "film_lr": args.film_lr, "phase_source": args.phase_source,
        "model_cfg": model_cfg, "smoke": bool(args.smoke),
        # 契約 (tasks/<task_id>/spec.yaml) と run を結ぶ鍵。harvester は最上位を読む。
        "task_id": args.task_id,
        "rare_slots": os.environ.get("T1B_RARE_SLOTS"),
        "warm_start_ckpt": str(resolve_detector_ckpt(args.seed, args.det_ckpt)),
        "eval": {"split": "val", "topk": ra.EVAL_TOPK,
                 "note": "score 閾値の足切りなし（eval recipe = score_thr 0.0 系）"},
        **({"stage2pilot": {
            "det_ckpt": args.det_ckpt, "ann_dir": ANN_DIR, "signal_train": args.signal_train,
            "signal_val": args.signal_val, "signal_dim": ctx_dim, "fixed_table": args.fixed_table,
            "eval_only": bool(args.eval_only), "patience": args.patience, "max_epochs": args.epochs,
            "best_excludes_init": bool(args.best_excludes_init), "ckpt_dir": args.ckpt_dir,
            "save_trainable_only": bool(args.save_trainable_only),
            "phase_params": n_phase, "total_trainable": n_train,
            **({"fixed_epochs": True, "result_selection": "final_epoch"} if args.fixed_epochs else {}),
            **({"missed_set": args.missed_set} if args.missed_set else {}),
            **({"grasp_map": args.grasp_map} if args.grasp_map else {}),
        }} if (args.det_ckpt or args.signal_train or args.patience is not None or args.eval_only) else {}),
    })

    # warm-start 健全性: 学習前 mAP（FiLM zero-init 恒等 → S0-frozen 水準のはず）
    init_map, init_per_class, init_preds = eval_detection(
        model, det_val, imgid_to_ctx_va, device, args.zero_ctx,
        limit=20 if args.smoke else None, collect_predictions=True, dim=ctx_dim)
    init_pred_path = None
    if save_preds:
        # init（warm-start 恒等点）の予測は必須。恒等性の検証と init 比較の絶対値解析に要る。
        init_pred_path = ra.save_predictions(
            work, init_preds["results"], split="val", tag=variant, epoch=-1,
            compress=compress_preds)
        ra.save_eval_meta(work, {
            "split": "val", "ann_file": f"{ANN_DIR}/instances_val.json",
            "image_ids": init_preds["image_ids"], "topk": ra.EVAL_TOPK,
            "select_box_nums_for_evaluation": 300, "score_thr": 0.0,
            "limit": 20 if args.smoke else None,
        })
    print(f"[t1b] warm-start init mAP={init_map:.4f} (S0-frozen 水準なら warm-start+恒等 OK)", flush=True)
    if args.assert_init_map is not None and abs(init_map - args.assert_init_map) > args.assert_init_tol:
        print(f"[t1b][PREFLIGHT-FAIL] init mAP={init_map:.4f} != "
              f"{args.assert_init_map}±{args.assert_init_tol} → warm-start/zero-init恒等が壊れている。"
              f"中断（設定ドリフト・捏造防止）。", flush=True)
        sys.exit(3)

    phase_named = [(n, p) for n, p in model.named_parameters() if "phase" in n]
    phase_grad_seen = False
    best = {"mAP": init_map, "epoch": -1, "per_class_coco_map": {}}
    if args.best_excludes_init and not args.eval_only:
        # 最良の時点を学習した epoch の中から選ぶ（学習前の恒等点は候補にしない）
        best = {"mAP": -math.inf, "epoch": -1, "per_class_coco_map": {}}
    stale, stopped_at = 0, None
    # epoch 別 per_class を全保存（frozen 検出器で best-overall が動かない/空になる不具合の回避。
    # inj/ctrl を同一 final epoch で公平比較するため。init(epoch=-1) も含める）。
    per_epoch = [{"epoch": -1, "mAP": init_map, "per_class_coco_map": init_per_class, **gate_record(model)}]
    for epoch in range(args.epochs):
        model.train()
        from util.collate_fn import DataPrefetcher
        prefetcher = DataPrefetcher(det_train, device)
        n_steps = det_steps_cap or det_steps_per_ep
        ep_start = time.perf_counter()
        for step in range(n_steps):
            batch = prefetcher.next()
            if batch is None:
                break
            images, targets = batch
            model.set_phase_context(ctx_for_targets(targets, imgid_to_ctx_tr, device, args.zero_ctx, ctx_dim))
            if args.grasp_map:
                model.set_grasp_maps([t["grasp_map"] for t in targets])
            if amp_dtype is None:
                loss_dict = model(images, targets)
                loss = sum(loss_dict.values())
            else:
                with torch.autocast("cuda", dtype=amp_dtype):
                    loss_dict = model(images, targets)
                    loss = sum(loss_dict.values())
            opt.zero_grad()
            if scaler is None:
                loss.backward()
            else:
                scaler.scale(loss).backward()
                scaler.unscale_(opt)  # 勾配の刈り込みは尺度を戻してから当てる
            if not phase_grad_seen and any(
                    p.grad is not None and p.grad.abs().sum() > 0 for _, p in phase_named):
                phase_grad_seen = True
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 0.1)
            if scaler is None:
                opt.step()
            else:
                scaler.step(opt)
                scaler.update()
            if step % args.print_freq == 0:
                rate = (step + 1) / max(time.perf_counter() - ep_start, 1e-6)
                eta = (det_steps_per_ep - step) / max(rate, 1e-6) / 60
                print(f"[t1b][ep{epoch} {step}/{det_steps_per_ep}] L={float(loss):.3f} "
                      f"{rate:.1f}it/s eta_ep={eta:.0f}m", flush=True)
            if not math.isfinite(float(loss)):
                print("[t1b] loss not finite, stop")
                sys.exit(1)
        if sched is not None:
            sched.step()

        mAP, per_class, preds = eval_detection(
            model, det_val, imgid_to_ctx_va, device, args.zero_ctx,
            limit=20 if args.smoke else None, collect_predictions=True, dim=ctx_dim)
        print(f"[t1b][ep{epoch}] val mAP={mAP:.4f}", flush=True)
        per_epoch.append({"epoch": epoch, "mAP": mAP, "per_class_coco_map": per_class, **gate_record(model)})
        if save_preds and args.save_predictions_all:
            ra.save_predictions(work, preds["results"], split="val", tag=variant, epoch=epoch,
                                compress=compress_preds)
        # --fixed-epochs: 最良の回を選ばず、最後の epoch の状態を結果にする（checkpoint と予測もその状態）
        chosen = epoch == args.epochs - 1 if args.fixed_epochs else mAP > best["mAP"]
        if chosen:
            best = {"mAP": mAP, "epoch": epoch, "per_class_coco_map": per_class}
            stale = 0
            ckpt_dir = Path(args.ckpt_dir) if args.ckpt_dir else ra.checkpoints_dir(work)
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            torch.save({"model": trainable_state(model) if args.save_trainable_only else model.state_dict(),
                        "epoch": epoch, "seed": args.seed}, ckpt_dir / "best_t1b.pth")
            if save_preds:
                # best epoch の予測は必須（ckpt が失われても per-image 解析を可能にする）。
                ra.save_predictions(work, preds["results"], split="val", tag=variant, best=True,
                                    compress=compress_preds)
        else:
            stale += 1
        if args.patience is not None and stale >= args.patience:
            stopped_at = epoch
            print(f"[t1b] val mAP が {args.patience} epoch 改善しないため ep{epoch} で止める", flush=True)
            break

    # frozen 検出器では init を超える epoch が無いことがあり、その場合 best ckpt も
    # best predictions も生成されない（= 過去に「ckpt 不在 seed を恒等代替」が必要になった原因）。
    # best==init であることを **隠さず明示**したうえで、best predictions は必ず出力する。
    # init ckpt 自体は warm-start ckpt から決定的に再構成できる（注入層 zero-init=恒等）ため
    # 187MB/run を重複保存しない。
    best_is_init = best["epoch"] == -1
    if save_preds and best_is_init:
        ra.save_predictions(work, init_preds["results"], split="val", tag=variant, best=True,
                            compress=compress_preds)

    final_eval = per_epoch[-1]  # 最終 epoch（inj/ctrl 同一学習量での公平比較用）
    result = {
        "seed": args.seed, "inject": args.inject, "trainable": args.trainable, "zero_ctx": args.zero_ctx,
        "epochs": args.epochs, "lr": args.lr, "film_lr": args.film_lr,
        "init_mAP": init_map, "best_epoch": best["epoch"], "mAP": best["mAP"],
        "per_class_coco_map": best.get("per_class_coco_map", {}),
        "init_per_class_coco_map": init_per_class,
        "final_epoch": final_eval["epoch"], "final_mAP": final_eval["mAP"],
        "final_per_class_coco_map": final_eval["per_class_coco_map"],
        "per_epoch_eval": per_epoch,
        "best_is_init": best_is_init, "run_dir": str(work),
        **({"result_selection": "final_epoch"} if args.fixed_epochs else {}),
        **({"frozen_digest_before": frozen_before, "frozen_digest_after": frozen_digest(model)}
           if args.save_trainable_only else {}),
        **({"early_stopped_epoch": stopped_at, "epochs_run": len(per_epoch) - 1,
            "reached_epoch_cap": stopped_at is None and len(per_epoch) - 1 == args.epochs}
           if args.patience is not None else {}),
        "denominator": "S0-frozen 0.7051±0.0052", "delta_note": "Δ_detection=(T1b − S0-frozen)",
    }
    (work / "t1b_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    # --- 永続ログ・証跡（ckpt が失われてもコミット済みログだけで解析を完遂できる状態にする） ---
    epoch_log = {
        "run_name": run_name, "variant": variant, "split": "val",
        "seed": args.seed, "inject": args.inject, "trainable": args.trainable,
        "zero_ctx": bool(args.zero_ctx), "epochs": args.epochs,
        "init": {"epoch": -1, "mAP": init_map, "per_class_coco_map": init_per_class},
        # inj / ctrl の init 完全一致（注入層 zero-init=恒等）を後から照合するための指紋。
        "init_predictions_sha256": (
            ra.predictions_sha256(init_pred_path) if init_pred_path else None),
        "init_predictions_file": (init_pred_path.name if init_pred_path else None),
        "best_epoch": best["epoch"], "best_mAP": best["mAP"],
        # True = 学習で init を超えず best ckpt が存在しない（best predictions は init の複製）。
        "best_is_init": best_is_init,
        "best_checkpoint": (None if best_is_init
                            else str(ra.checkpoints_dir(work) / "best_t1b.pth")),
        "final_epoch": final_eval["epoch"], "final_mAP": final_eval["mAP"],
        "epochs_eval": per_epoch,
    }
    ra.save_epoch_log(work, epoch_log)
    ra.write_metrics(work, {
        "mAP": best["mAP"], "init_mAP": init_map, "epoch": best["epoch"],
        "final_mAP": final_eval["mAP"], "final_epoch": final_eval["epoch"],
        "delta_detection": best["mAP"] - init_map,
        "best_is_init": best_is_init,
        **({"result_selection": "final_epoch"} if args.fixed_epochs else {}),
        "artifacts": ra.artifact_paths(work),
    })
    ra.write_per_class_ap(work, best.get("per_class_coco_map", {}))
    print(f"[t1b] DONE best@ep{best['epoch']} mAP={best['mAP']:.4f} (init {init_map:.4f}) -> {work}")
    if not args.smoke:
        # 工程側 finalize() と対称: 完了した検出 run の証跡を自動 commit + push（fail-safe）。
        _autosync_evidence(work, run_name, args.seed, best["mAP"])
    if args.smoke:
        ok = phase_grad_seen and (init_map > 0.5)  # 注入層に勾配 + warm-start mAP 健全
        print(f"[t1b][smoke] phase_grad={phase_grad_seen} init_mAP={init_map:.4f} "
              f"=> {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 2)


def _autosync_evidence(work: Path, run_name: str, seed: int, m_ap: float) -> None:
    """完了した検出 run の証跡を git_autosync CLI で自動 commit + push する（fail-safe）。

    工程側 ``ExperimentManager.finalize()`` と対称の配線。``exp/*`` ブランチ + deploy key
    構成時のみ実際に push し、それ以外は no-op。``git_autosync.py`` は top-level が stdlib のみで
    ファイル直実行できるため、egosurgery 未導入の ``.venv-relation-detr`` からでも動く
    （内部の egosurgery import は guarded）。predictions/checkpoints は ``.gitignore`` で除外
    されるため public repo には載らず、追跡対象の証跡テキスト（config.yaml/metrics.json/
    per_class_ap.json/notes.md/logs/val_metrics_by_epoch.json 等）だけが同期される。
    同一ホストで並列 seed が走る場合の git index 競合は flock で直列化する（cross-host は
    各自別ブランチへ push するため無関係）。CLI 自体が常に exit 0・非送出なので学習は止めない。
    """
    import fcntl
    import subprocess

    cli = BODY / "src" / "egosurgery" / "utils" / "git_autosync.py"
    if not cli.exists():
        return
    lock_fh = None
    try:
        try:
            lock_fh = open(BODY / ".git" / "egosurgery-autosync.lock", "w")
            fcntl.flock(lock_fh, fcntl.LOCK_EX)  # 同一ホストの並列 run を直列化
        except OSError:
            lock_fh = None  # ロック不可でも続行（直列化は best-effort）
        subprocess.run(
            [sys.executable, str(cli), str(work),
             "--step", "T1b", "--description", run_name, "--seed", str(seed),
             "--category", "transfer", "--exp-id", run_name,
             "--metric-name", "mAP", "--metric-value", f"{m_ap:.6f}"],
            check=False,
        )
    except Exception as exc:  # 自動同期の失敗を学習完了に漏らさない
        print(f"[t1b] auto-sync skipped (non-fatal): {exc!r}", flush=True)
    finally:
        if lock_fh is not None:
            try:
                fcntl.flock(lock_fh, fcntl.LOCK_UN)
                lock_fh.close()
            except OSError:
                pass


def parse_args():
    p = argparse.ArgumentParser(description="T1b Phase->Det FiLM trainer (warm-start fine-tune).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--film-lr", type=float, default=5e-4)
    p.add_argument("--trainable", choices=["film", "all", "w2"], default="all")
    p.add_argument("--inject", choices=["film", "ca", "camt", "hc", "clsbias"], default="film",
                   help="phase 注入機構: film(§4.6下限・C5 FiLM) / ca(§4.6 primary・decoder cross-attn) / "
                        "hc(§7.2 H-C-v1 = ca + per-frame entropy gate)")
    p.add_argument("--zero-ctx", action="store_true", help="§4.6 対照: phase context を 0 固定で fine-tune")
    p.add_argument(
        "--phase-source",
        choices=["real", "oracle", "both"],
        default="real",
        help="§18.4 L1-2: phase context のソース。real=S4 TeCNO 予測（既定）/ "
        "oracle=phase_manifest からの GT one-hot（注入の上限を測定）",
    )
    p.add_argument("--run-name", default=None,
                   help="成果物の保存先 experiments/transfer/<run_name>/。省略時は "
                        "t1b_{inject}_{trainable}_{inj|ctrl}_seed{seed}（環境変数 T1B_RUN_NAME でも指定可）")
    p.add_argument("--no-save-predictions", action="store_true",
                   help="per-image predictions を保存しない（既定は保存する）")
    p.add_argument("--save-predictions-all", action="store_true",
                   help="init/best だけでなく全 epoch の predictions を保存する（容量大）")
    p.add_argument("--predictions-no-gzip", action="store_true",
                   help="predictions を gzip せず素の .json で保存する")
    p.add_argument("--task-id", type=str, default="",
                   help="契約の識別子。config.yaml の最上位へ書き出し、run と指示書を結ぶ。")
    p.add_argument("--print-freq", type=int, default=200)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--assert-init-map", type=float, default=None,
                   help="warm-start init mAP がこの値±tol から外れたら中断（恒等性・ドリフト検査）")
    p.add_argument("--assert-init-tol", type=float, default=0.02)
    p.add_argument("--tf32", action="store_true",
                   help="行列積で TF32 を許す（torch の既定は False。畳み込み側の cudnn は既定で True）。"
                        "既定 off ではこの設定に触れないため、経路は従来と同一")
    # 以下は契約 T-2026-10-18-stage2-pilot-folda で足した。**どれも渡さなければ従来の経路のまま**
    p.add_argument("--det-ckpt", default=None,
                   help="受け取り手の検出器 checkpoint。既定は従来どおり checkpoints/incoming/seed{seed}/best_ap.pth")
    p.add_argument("--signal-train", default=None,
                   help="train の信号 npz（frame_ids, x）。--signal-val と組で渡す。既定は --phase-source の経路")
    p.add_argument("--signal-val", default=None, help="val の信号 npz（frame_ids, x）")
    p.add_argument("--fixed-table", default=None,
                   help="学習しない型（clsbias_fix）の表 B を持つ json（キー B）。既定は表を入れない（零＝恒等）")
    p.add_argument("--eval-only", action="store_true",
                   help="学習せず学習前の評価だけを残す（学習対象の無い型）")
    p.add_argument("--patience", type=int, default=None,
                   help="渡すと学習率を一定にし、val mAP が patience epoch 改善しなければ止める（上限 --epochs）。"
                        "既定は従来どおり固定 epoch と epochs-2 での学習率低下")
    p.add_argument("--best-excludes-init", action="store_true",
                   help="最良の時点を学習した epoch から選ぶ（学習前の恒等点を候補にしない）")
    p.add_argument("--ckpt-dir", default=None,
                   help="best_t1b.pth の置き場。既定は従来どおり run の checkpoints/")
    p.add_argument("--save-trainable-only", action="store_true",
                   help="best_t1b.pth に学習対象の重みと注入層の buffer だけを入れる")
    # 契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle で足した。渡さなければ従来の経路のまま
    p.add_argument("--fixed-epochs", action="store_true",
                   help="--epochs の回数を止めずに学習し、最後の epoch の状態を結果にする（最良の回を選ばない）。"
                        "学習率は一定。metrics.json・per_class_ap.json・best_t1b.pth・val の best の予測は"
                        "最後の epoch の状態になり、result_selection=final_epoch を記録する")
    p.add_argument("--amp", default="no", choices=("no", "bf16", "fp16"),
                   help="学習の順伝播の数値精度。既定 no は従来どおりの単精度で、"
                        "経路も従来と同一（autocast を張らない）。bf16/fp16 は自動混合精度。"
                        "fp16 は GradScaler による勾配の尺度調整を伴う。**評価は常に単精度で行う**")
    # 契約 T-2026-10-19-stage2-pilot-four-new-types で足した。渡さなければ従来の経路のまま
    p.add_argument("--grasp-map", default=None, choices=("zero", "gt"),
                   help="契約 T-2026-10-31-grasp-pilot-probe の案 B。把持の地図（zero は全 0、gt は正解）を画像と同じ変換で読み、"
                        "検出器の set_grasp_maps に渡す。渡さなければ従来の経路のまま")
    p.add_argument("--missed-set", default=None,
                   help="extra_q の学習に使う見落としの集合の json（キー missed_ann_ids）。train の labels に見落としの印を足す")
    return p.parse_args()


if __name__ == "__main__":
    main()
