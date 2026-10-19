"""工程から検出（PD）の界面の新しい型（非公式 T-2026-10-19-stage2-pilot-four-new-types、SPEC §3.1・§3.2）。

.venv-relation-detr で、cwd と sys.path に third_party/Relation-DETR を置いて使う（pd_model.py と同じ）。
受け取り手は D*-COCO 折り A seed 42（relation_detr_resnet50_egosurgery.py と同じ構成）。D* の重みは凍結する（W1）。
界面の重みの名前はすべて ``phase_iface`` で始まる（train_t1b.py の ``"phase" in name`` で選ばれる）。

    dec_xattn  decoder の全層の各層の出力（FFN の後、その層の出力から box を精緻化する計算の前）に
               h ← h + tanh(α_l) × W_out Attn(W_q LN(h), 工程の token, 工程の token) を足す。工程の token は
               信号 → 32（入力適合層）→ 4 × 64。attention は 4 ヘッド（ヘッドあたり 16）。α_l は層ごとのスカラーで 0 から。
               decoder を通るすべての query（学習時の denoising と hybrid の経路を含む）に当てる
    extra_q    decoder に追加の query を 30 個足す。内容 e_i + W_c a(t)、参照 box sigmoid(u_i + W_b a(t))、a(t) は入力適合層の出力。
               自己注意は「元の query は追加の query を参照しない。追加の query は元と追加の両方を参照する」。
               元の query の出力が塔単独と同じであることを構成で保つため、元の経路は D* のまま回し（mask を張った
               一つの計算にすると行列積の形が変わって丸めが変わり得る）、追加の query だけを、各層で元の query の
               その層の入力を key と value に加えて別に回す。位置関係の埋め込み（Relation-DETR）は、追加の query の行について
               元と追加の両方の box との間で D* と同じ式で作る。追加の出力のクラス logit に学習する定数（初期値 −10）を足す。
               最終の検出は元と追加の出力の和集合から D* の後処理（上位 300、NMS なし、確信度の下限なし）で取る。
               学習では元の query の損失を使わず、追加の query だけを見落としの box に D* と同じ照合と損失
               （HybridSetCriterion、各層の補助の損失つき）で当てる。元の経路は勾配を持たせずに回す

界面の初期化は大域の乱数の流れから切り離す（torch.random.fork_rng と固定の種）。腕ごとに入力適合層の入力の次元が
違っても（正解予測-CF は 18）、界面の他の部分の初期値と、その後の学習の乱数（データの並び）が腕の間で同じになる。
入力適合層は最後に作る。
"""
from __future__ import annotations

import contextlib
import json
import math

import torch
from models.bricks.position_encoding import get_sine_pos_embed
from models.detectors.relation_detr import RelationDETR
from torch import nn
from util.misc import inverse_sigmoid

INTERFACES = ("dec_xattn", "extra_q")
INIT_SEED = 20261019


class PhaseDecoderXAttn(nn.Module):
    """SPEC §3.1 の部分層の集まり。層 l の部分層は norm[l]・q[l]・out[l]・alpha[l]。token の生成は全層で共有。"""

    def __init__(self, sig_dim: int, hidden: int, num_layers: int, a_dim: int = 32, n_tok: int = 4,
                 d: int = 64, heads: int = 4):
        super().__init__()
        self.n_tok, self.d, self.heads = n_tok, d, heads
        self.token = nn.Linear(a_dim, n_tok * d)
        self.norm = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(num_layers)])
        self.q = nn.ModuleList([nn.Linear(hidden, d) for _ in range(num_layers)])
        self.out = nn.ModuleList([nn.Linear(d, hidden) for _ in range(num_layers)])
        self.alpha = nn.Parameter(torch.zeros(num_layers))
        self.adapter = nn.Linear(sig_dim, a_dim)

    def tokens(self, ctx):                       # (B, S) → (B, n_tok, heads, d / heads)
        return self.token(self.adapter(ctx)).view(ctx.shape[0], self.n_tok, self.heads, self.d // self.heads)

    def forward(self, layer: int, h, ctx):        # h (B, Q, hidden)
        tok = self.tokens(ctx)
        b, q_len, _ = h.shape
        q = self.q[layer](self.norm[layer](h)).view(b, q_len, self.heads, self.d // self.heads)
        att = torch.einsum("bqhd,bthd->bhqt", q, tok) / math.sqrt(self.d // self.heads)
        w = torch.softmax(att, dim=-1)
        o = torch.einsum("bhqt,bthd->bqhd", w, tok).reshape(b, q_len, self.d)
        return h + torch.tanh(self.alpha[layer]) * self.out[layer](o)


class PhaseExtraQueries(nn.Module):
    """SPEC §3.2 の追加の query。e_i（埋め込み）、u_i（参照 box の logit）、W_c・W_b（a(t) の線形写像）、入力適合層、スコアの定数。"""

    def __init__(self, sig_dim: int, hidden: int, n_extra: int = 30, a_dim: int = 32, score_init: float = -10.0):
        super().__init__()
        self.n_extra = n_extra
        self.embed = nn.Parameter(torch.empty(n_extra, hidden))
        self.box = nn.Parameter(torch.empty(n_extra, 4))
        nn.init.normal_(self.embed)               # D* の tgt_embed と同じ初期化
        nn.init.normal_(self.box)                 # 学習する参照 box（nn.Embedding の既定と同じ正規分布）
        self.content = nn.Linear(a_dim, hidden)
        self.box_lin = nn.Linear(a_dim, 4)
        self.score = nn.Parameter(torch.tensor(float(score_init)))
        self.adapter = nn.Linear(sig_dim, a_dim)

    def init_queries(self, ctx):                  # → 内容 (B, n, hidden)、参照 box (B, n, 4)
        a = self.adapter(ctx)
        content = self.embed[None] + self.content(a)[:, None]
        ref = torch.sigmoid(self.box[None] + self.box_lin(a)[:, None])
        return content, ref


class RelationDETRStage2Four(RelationDETR):
    """RelationDETR に SPEC §3.1 か §3.2 の界面を一つ足した検出器。信号は forward の前に set_phase_context(ctx) で渡す。"""

    def __init__(self, *args, interface: str, signal_dim: int, num_classes: int = 15, num_queries: int = 900,
                 **kwargs) -> None:
        super().__init__(*args, num_classes=num_classes, num_queries=num_queries, **kwargs)
        if interface not in INTERFACES:
            raise ValueError(interface)
        self.interface = interface
        self.signal_dim = int(signal_dim)
        self.num_main_queries = int(num_queries)
        self._phase_ctx = None
        dec = self.transformer.decoder
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(INIT_SEED)
            if interface == "dec_xattn":
                self.phase_iface = PhaseDecoderXAttn(signal_dim, dec.embed_dim, dec.num_layers)
            else:
                self.phase_iface = PhaseExtraQueries(signal_dim, dec.embed_dim)
        if interface == "dec_xattn":
            for i, layer in enumerate(dec.layers):
                layer.register_forward_hook(self._xattn_hook(i))
        # extra_q の検査用の切り替え（既定は SPEC の定義どおり）
        self.xq_unmasked = False                  # True: 元と追加を一つの計算で回し、元の query も追加を参照する（陽性対照）
        self.xq_output = "union"                  # union（SPEC の最終の検出）/ orig（元の出力だけ）/ extra（追加の出力だけ）
        self.xq_last = None                       # 直前の評価の logit と box（寄与の解析用）

    def set_phase_context(self, ctx) -> None:
        self._phase_ctx = ctx

    def gate_values(self):
        """ゲートを持つ型（dec_xattn）の層ごとの tanh(α_l)。extra_q はスコアの定数を返す。"""
        if self.interface == "dec_xattn":
            return {"tanh_alpha": [float(v) for v in torch.tanh(self.phase_iface.alpha.detach()).cpu()]}
        return {"score_const": float(self.phase_iface.score.detach())}

    # --- §3.1 decoder-xattn ---
    def _xattn_hook(self, layer_idx):
        def hook(module, args, output):
            if self._phase_ctx is None:
                return output
            return self.phase_iface(layer_idx, output, self._phase_ctx.to(output.device))
        return hook

    # --- §3.2 extra-queries ---
    def forward(self, images, targets=None):
        if self.interface != "extra_q":
            return super().forward(images, targets)
        original_image_sizes = self.query_original_sizes(images)
        if self.training:
            if targets is None or targets[0]["labels"].ndim != 2:
                raise RuntimeError("extra_q の学習には見落としの印つきの labels（N, 2）が要る（--missed-set）")
            targets = [{**t, "labels": t["labels"][:, 0], "missed": t["labels"][:, 1].bool()} for t in targets]
        images, targets, mask = self.preprocess(images, targets)
        ctx = self._phase_ctx
        if ctx is None:
            raise RuntimeError("extra_q は set_phase_context が要る")
        ctx = ctx.to(images.tensors.device)
        content, ref = self.phase_iface.init_queries(ctx)          # 界面の側。学習では勾配を持つ
        grad_ctx = torch.no_grad() if self.training else contextlib.nullcontext()
        with grad_ctx:
            orig_cls, orig_box, cap = self._orig_pass(images, mask, content, ref)
        if self.xq_unmasked:
            e_cls, e_box = orig_cls[:, :, self.num_main_queries:], orig_box[:, :, self.num_main_queries:]
            orig_cls, orig_box = orig_cls[:, :, :self.num_main_queries], orig_box[:, :, :self.num_main_queries]
        else:
            e_cls, e_box = self._extra_pass(cap, content, ref)
        if self.training:
            miss = [{"boxes": t["boxes"][t["missed"]], "labels": t["labels"][t["missed"]]} for t in targets]
            output = {"pred_logits": e_cls[-1], "pred_boxes": e_box[-1],
                      "aux_outputs": self._set_aux_loss(e_cls, e_box)}
            loss_dict = self.criterion(output, miss)
            weight_dict = self.criterion.weight_dict
            return {k: v * weight_dict[k] for k, v in loss_dict.items() if k in weight_dict}
        self.xq_last = {"orig_logits": orig_cls[-1], "orig_boxes": orig_box[-1],
                        "extra_logits": e_cls[-1], "extra_boxes": e_box[-1]}
        if self.xq_output == "orig":
            logits, boxes = orig_cls[-1], orig_box[-1]
        elif self.xq_output == "extra":
            logits, boxes = e_cls[-1], e_box[-1]
        else:
            logits, boxes = torch.cat([orig_cls[-1], e_cls[-1]], 1), torch.cat([orig_box[-1], e_box[-1]], 1)
        return self.postprocessor({"pred_logits": logits, "pred_boxes": boxes}, original_image_sizes)

    def _orig_pass(self, images, mask, content, ref):
        """D* の経路（評価と同じ。denoising と hybrid なし）を回し、decoder の各層の入力を記録する。
        content と ref は陽性対照（xq_unmasked）のときだけ使う。"""
        dec = self.transformer.decoder
        cap = {"layers": []}

        def dec_pre(module, args, kwargs):
            cap.update({k: kwargs[k] for k in ("value", "key_padding_mask", "reference_points", "spatial_shapes",
                                               "level_start_index", "valid_ratios")})
            if self.xq_unmasked:                  # 陽性対照: 追加の query を元の列に連結し、mask なしで一つの計算にする
                kwargs = dict(kwargs)
                kwargs["query"] = torch.cat([kwargs["query"], content.to(kwargs["query"].dtype)], 1)
                kwargs["reference_points"] = torch.cat([kwargs["reference_points"], ref], 1)
                return args, kwargs
            return None

        def layer_pre(module, args, kwargs):
            cap["layers"].append((kwargs["query"], kwargs["query_pos"]))

        handles = [dec.register_forward_pre_hook(dec_pre, with_kwargs=True)]
        handles += [layer.register_forward_pre_hook(layer_pre, with_kwargs=True) for layer in dec.layers]
        was_training = self.transformer.training
        self.transformer.train(False)             # 評価の経路（hybrid なし）。dropout は 0 で BN は凍結なので数値は同じ
        try:
            multi_levels = self.get_multi_levels(images, mask)
            out = self.transformer(*multi_levels, None, None, attn_mask=None)
        finally:
            self.transformer.train(was_training)
            for h in handles:
                h.remove()
        cls, box = out[0], out[1]                 # (層, B, query, クラス) と (層, B, query, 4)
        if self.xq_unmasked:
            n = self.num_main_queries
            cls = torch.cat([cls[:, :, :n], cls[:, :, n:] + self.phase_iface.score], dim=2)
        cap["orig_boxes"] = box
        return cls, box, cap

    def _extra_pass(self, cap, content, ref):
        """追加の query を、D* の decoder の重みで層ごとに回す。自己注意の key と value は元の query のその層の入力と追加の query。"""
        dec = self.transformer.decoder
        value, kpm = cap["value"], cap["key_padding_mask"]
        valid_ratio_scale = torch.cat([cap["valid_ratios"], cap["valid_ratios"]], -1)[:, None]
        h, outs_cls, outs_box = content, [], []
        pos_relation, prev_box = None, None
        for li, layer in enumerate(dec.layers):
            q_orig, pos_orig = cap["layers"][li]
            ref_in = ref.detach()[:, :, None] * valid_ratio_scale
            pos = dec.ref_point_head(get_sine_pos_embed(ref_in[:, :, 0, :], dec.embed_dim // 2))
            pos = pos * dec.query_scale(h) if li != 0 else pos
            qk = h + pos
            h2 = layer.self_attn(query=qk, key=torch.cat([(q_orig + pos_orig).to(qk.dtype), qk], 1),
                                 value=torch.cat([q_orig.to(h.dtype), h], 1), attn_mask=pos_relation,
                                 need_weights=False)[0]
            h = layer.norm2(h + layer.dropout2(h2))
            h2 = layer.cross_attn(query=h + pos, reference_points=ref_in, value=value,
                                  spatial_shapes=cap["spatial_shapes"], level_start_index=cap["level_start_index"],
                                  key_padding_mask=kpm)
            h = layer.norm1(h + layer.dropout1(h2))
            h = layer.forward_ffn(h)
            cls = dec.class_head[li](dec.norm(h)) + self.phase_iface.score
            box = (dec.bbox_head[li](dec.norm(h)) + inverse_sigmoid(ref)).sigmoid()
            outs_cls.append(cls)
            outs_box.append(box)
            if li == dec.num_layers - 1:
                break
            # 位置関係の埋め込み（D* と同じ式）: 行は追加の query の前の層の box（最初は参照 box）、列は元と追加のこの層の box
            src = prev_box if li >= 1 else ref
            tgt = torch.cat([cap["orig_boxes"][li].to(box.dtype), box], 1)
            pos_relation = dec.position_relation_embedding(src, tgt).flatten(0, 1)
            prev_box = box
            ref = (dec.bbox_head[li](h) + inverse_sigmoid(ref.detach())).sigmoid()
        return torch.stack(outs_cls), torch.stack(outs_box)


def load_missed_ids(path) -> set[int]:
    return set(json.loads(open(path).read())["missed_ann_ids"])


def build_missed_train_loader(ego_root: str, ann_dir: str, missed_ids: set[int]):
    """train_t1b.build_det_loader(train=True) と同じ読み込み（detr の増強、縦横比の群、batch 2、worker 4）で、
    labels を（クラス, 見落としの印）の 2 列にしたもの。増強の SanitizeBoundingBox は labels を box と同じ並びで落とす。"""
    from datasets.coco import CocoDetection
    from torch.utils import data
    from transforms import presets
    from util.collate_fn import collate_fn
    from util.group_by_aspect_ratio import GroupedBatchSampler, create_aspect_ratio_groups

    class CocoDetectionMissed(CocoDetection):
        def load_image_and_target(self, item: int):
            image, target = super().load_image_and_target(item)
            image_id = self.get_image_id(item)
            anns = [a for a in self.coco.loadAnns(self.coco.getAnnIds([image_id]))
                    if "iscrowd" not in a or a["iscrowd"] == 0]
            # ConvertCocoPolysToMask と同じ規則で残る注釈（幅と高さが正。画像の外は切り詰め）
            w, h = self.coco.imgs[image_id]["width"], self.coco.imgs[image_id]["height"]
            kept = []
            for a in anns:
                x0, y0, bw, bh = a["bbox"]
                x1, y1 = min(max(x0 + bw, 0), w), min(max(y0 + bh, 0), h)
                x0, y0 = min(max(x0, 0), w), min(max(y0, 0), h)
                if y1 > y0 and x1 > x0:
                    kept.append(a["id"] in missed_ids)
            flags = torch.tensor(kept, dtype=torch.int64)
            assert len(flags) == len(target["labels"]), (image_id, len(flags), len(target["labels"]))
            target["labels"] = torch.stack([target["labels"], flags], 1) if len(flags) else \
                torch.zeros((0, 2), dtype=torch.int64)
            return image, target

    ds = CocoDetectionMissed(img_folder=ego_root, ann_file=f"{ann_dir}/instances_train.json",
                             transforms=presets.detr, train=True)
    group_ids = create_aspect_ratio_groups(ds, k=3)
    bs = GroupedBatchSampler(data.RandomSampler(ds), group_ids, 2)
    return data.DataLoader(ds, batch_sampler=bs, num_workers=4, collate_fn=collate_fn, pin_memory=True)  # nosemgrep
