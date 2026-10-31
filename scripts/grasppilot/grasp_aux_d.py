"""案 D の補助の頭（非公式 T-2026-11-01-grasp-pilot-d、SPEC §3.2・§3.3）。

third_party を変えず、検出器とデータセットの派生をここに置く（`pd_grasp_model.py` と同じ作法）。

- ``attach_grasp_head(model, weight, ...)``: 元の模型設定が作った ``RelationDETR`` の型を
  ``RelationDETRGraspAux`` に差し替え、補助の頭（256 → 4 の線形）を足す。頭の初期値は専用の
  ``torch.Generator`` から作り、大域の乱数を動かさない（元の模型と同じ乱数の流れを保つ）
- 学習時だけ、主経路の decoder の最終層の出力（``class_head[-1]`` の入力の最初の発火。denoising の
  query を除いた末尾 ``num_queries`` 個）と、最終層の照合（criterion の最初の呼び出しの最初の B 回の
  matcher）を取り、対応づいた枠で 4 値の交差エントロピーを平均する。全損失 = 検出の損失 + weight × 補助損失
- 推論（eval）は元の ``RelationDETR.forward`` と同じ（補助の頭を使わない）
- ``GraspTargetCoco``: 学習データの枠ごとに q を運ぶ。注釈の並びの番号を ``category_id`` に埋めて
  変換を通し（変換は値を見ないので乱数の消費も出力も元と同じ）、変換の後に残った枠の q を引く。
  左右反転された画像では q の左手と右手を入れ替える（利用者の決定 2026-11-01）
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

ENC = 1000  # category_id = 注釈の番号 × ENC + クラス。クラスは 15 未満
N_STATES = 4  # 左手・右手・両手・なし
HEAD_SEED = 20261101


def param_digest(module: nn.Module, prefix_skip: tuple[str, ...] = ()) -> str:
    h = hashlib.sha256()
    for k, v in sorted(module.state_dict().items()):
        if prefix_skip and k.startswith(prefix_skip):
            continue
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().float().numpy().tobytes())
    return h.hexdigest()


def load_q_table(path):
    """npz（ann_ids (N,)、q (N, 4)）→ {COCO の注釈 id: q}。"""
    d = np.load(path)
    ids = d["ann_ids"].astype(np.int64)
    q = d["q"].astype(np.float32)
    assert q.shape == (len(ids), N_STATES), q.shape
    assert len(set(ids.tolist())) == len(ids), "注釈 id が重複している"
    return {int(a): q[i] for i, a in enumerate(ids)}


class RelationDETRGraspAux(nn.Module):
    """``RelationDETR`` の実体の ``__class__`` をこの型に差し替えて使う（MRO で元の型を継ぐ）。"""

    def _init_grasp(self, weight: float, steplog: str | None):
        g = torch.Generator().manual_seed(HEAD_SEED)
        head = torch.nn.utils.skip_init(nn.Linear, self.transformer.embed_dim, N_STATES)
        bound = 1.0 / float(self.transformer.embed_dim) ** 0.5
        with torch.no_grad():
            head.weight.uniform_(-bound, bound, generator=g)
            head.bias.uniform_(-bound, bound, generator=g)
        self.grasp_head = head
        self.grasp_weight = float(weight)
        self.grasp_steplog = steplog
        self._grasp_step = 0
        self._grasp_fh = None

    # ---- 読み込みの記録（COCO の重みを読んだことの証拠。main.py が呼ぶ util.utils.load_state_dict の内側） ----
    def load_state_dict(self, state_dict, strict=True, *args, **kwargs):
        before = param_digest(self, ("grasp_head",))
        res = super().load_state_dict(state_dict, strict, *args, **kwargs)
        after = param_digest(self, ("grasp_head",))
        if self.grasp_steplog:
            rec = {"event": "load_state_dict", "n_keys": len(state_dict), "digest_before": before,
                   "digest_after": after, "changed": before != after,
                   "missing": list(res.missing_keys), "unexpected": list(res.unexpected_keys)}
            p = Path(self.grasp_steplog).with_name("load_record.jsonl")
            with p.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return res

    def _log(self, rec):
        """1 歩 1 行。行ごとに書き出す（学習の終わりを模型は知らないので、ためずに書く）。"""
        if not self.grasp_steplog:
            return
        if self._grasp_fh is None:
            self._grasp_fh = open(self.grasp_steplog, "a", buffering=1)
        self._grasp_fh.write(json.dumps(rec) + "\n")

    def forward(self, images, targets=None):
        if not self.training or targets is None:
            return super().forward(images, targets)
        cap = {"feat": None, "crit": None, "match": [], "n_feat_calls": 0, "n_crit_calls": 0}
        bsz = len(targets)

        def feat_hook(_m, inp):
            cap["n_feat_calls"] += 1
            if cap["feat"] is None:
                cap["feat"] = inp[0]

        def crit_hook(_m, args):
            cap["n_crit_calls"] += 1
            if cap["crit"] is None:
                cap["crit"] = args

        def match_hook(_m, _args, out):
            if cap["n_crit_calls"] == 1 and len(cap["match"]) < bsz:
                cap["match"].append(out)

        hooks = [self.transformer.decoder.class_head[-1].register_forward_pre_hook(feat_hook),
                 self.criterion.register_forward_pre_hook(crit_hook),
                 self.criterion.matcher.register_forward_hook(match_hook)]
        try:
            loss_dict = super().forward(images, targets)
        finally:
            for h in hooks:
                h.remove()
        output, ptargets = cap["crit"]
        nq = output["pred_logits"].shape[1]
        feat = cap["feat"][:, -nq:]
        indices = cap["match"]
        assert len(indices) == bsz, (len(indices), bsz)
        src = torch.cat([s for s, _ in indices]).to(feat.device)
        bidx = torch.cat([torch.full_like(s, i) for i, (s, _) in enumerate(indices)]).to(feat.device)
        q = torch.cat([t["grasp_q"][j.to(t["grasp_q"].device)] for t, (_, j) in zip(ptargets, indices)])
        with torch.autocast(device_type=feat.device.type, enabled=False):
            if len(src):
                logits = self.grasp_head(feat[bidx, src].float())
                ce = -(q.float() * F.log_softmax(logits, -1)).sum(-1).mean()
                acc = float((logits.argmax(-1) == q.argmax(-1)).float().mean())
            else:
                ce = self.grasp_head.weight.sum() * 0.0 + feat.float().sum() * 0.0
                acc = float("nan")
        loss_dict["loss_grasp"] = ce * self.grasp_weight
        self._log({"step": self._grasp_step, "ce": float(ce.detach()), "acc": acc, "n_matched": int(len(src)),
                   "n_gt": int(sum(len(t["labels"]) for t in ptargets)), "weight": self.grasp_weight,
                   "n_flipped_imgs": int(sum(int(t["grasp_flipped"]) for t in ptargets)),
                   "n_feat_calls": cap["n_feat_calls"], "feat_len": int(cap["feat"].shape[1]), "nq": int(nq)})
        self._grasp_step += 1
        if getattr(self, "_grasp_keep_last", False):  # 試走の確かめだけ（本番は計算グラフを持ち越さない）
            self._grasp_last = {"indices": indices, "output": output, "targets": ptargets, "ce": ce, "feat": feat}
        return loss_dict


def attach_grasp_head(model: nn.Module, weight: float, steplog: str | None = None) -> nn.Module:
    base = type(model)
    model.__class__ = type("RelationDETRGraspAux", (RelationDETRGraspAux, base), {})
    model._init_grasp(weight, steplog)
    return model


def _flip_probe_class():
    from transforms import v2 as T

    class FlipProbe(T.RandomHorizontalFlip):
        """元と同じ乱数で反転し、反転したかを記録する（``_get_params`` は反転するときだけ呼ばれる）。"""
        flipped = False

        def forward(self, *inputs):
            self.flipped = False
            return super().forward(*inputs)

        def _get_params(self, flat_inputs):
            self.flipped = True
            return super()._get_params(flat_inputs)

    return FlipProbe


def wrap_flip(transform):
    """Compose の最上段の RandomHorizontalFlip を FlipProbe に替える。替えた実体（無ければ None）を返す。"""
    from transforms import v2 as T

    FlipProbe = _flip_probe_class()
    probe = None
    if isinstance(transform, T.Compose):
        new = []
        for t in transform.transforms:
            if type(t) is T.RandomHorizontalFlip:
                assert probe is None, "反転が二つある"
                probe = FlipProbe(p=t.p)
                new.append(probe)
            else:
                new.append(t)
        transform = type(transform)(new)
    return transform, probe


def grasp_dataset_class():
    from datasets.coco import CocoDetection

    class GraspTargetCoco(CocoDetection):
        def __init__(self, img_folder, ann_file, transforms=None, train=False, q_table=None, swap_on_flip=True):
            super().__init__(img_folder, ann_file, transforms=transforms, train=train)
            self._transforms, self._flip = wrap_flip(self._transforms)
            assert self._flip is not None, "presets.detr に反転が無い"
            self.q_path = q_table
            self.q_table = load_q_table(q_table) if q_table else None
            self.swap_on_flip = swap_on_flip

        def load_image_and_target(self, item: int):
            image_id = self.get_image_id(item)
            image_name = self.coco.loadImgs([image_id])[0]["file_name"]
            image = self.load_image(image_name)
            anns = self.coco.loadAnns(self.coco.getAnnIds([image_id]))
            enc = [dict(a, category_id=j * ENC + int(a["category_id"])) for j, a in enumerate(anns)]
            image, target = self.prepare((image, dict(image_id=image_id, annotations=enc)))
            return image, target, anns

        def __getitem__(self, item):
            from util.misc import deepcopy

            image, target, anns = self.load_image_and_target(item)
            image, target["boxes"], enc = self.data_augmentation(image, target)
            flipped = bool(self._flip.flipped)
            enc = torch.as_tensor(enc, dtype=torch.int64)
            target["labels"] = enc % ENC
            ann_ids = torch.as_tensor([int(anns[j]["id"]) for j in (enc // ENC).tolist()], dtype=torch.int64)
            if self.q_table is None:
                q = torch.full((len(ann_ids), N_STATES), 1.0 / N_STATES)
            else:
                q = torch.as_tensor(np.stack([self.q_table[int(a)] for a in ann_ids.tolist()])
                                    if len(ann_ids) else np.zeros((0, N_STATES), np.float32))
                if flipped and self.swap_on_flip:
                    q = q[:, [1, 0, 2, 3]]
            target["grasp_q"] = q.float()
            target["grasp_ann_id"] = ann_ids
            target["grasp_flipped"] = torch.tensor(flipped)
            return deepcopy(image), deepcopy(target)

    return GraspTargetCoco


def env_settings() -> dict:
    """腕を区別する設定（起動の環境変数）。3 腕で違ってよいのは weight と targets だけ。"""
    return {"weight": float(os.environ["GRASP_AUX_WEIGHT"]),
            "targets": os.environ.get("GRASP_TARGETS") or None,
            "steplog": os.environ.get("GRASP_STEPLOG") or None,
            "swap_on_flip": os.environ.get("GRASP_SWAP_ON_FLIP", "1") == "1"}
