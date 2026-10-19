"""工程から検出（PD）の界面つき検出塔（非公式 T-2026-10-18-stage2-pilot-folda、SPEC §3）。

.venv-relation-detr で、cwd と sys.path に third_party/Relation-DETR を置いて使う。
受け取り手は D*-COCO 折り A seed 42（relation_detr_resnet50_egosurgery.py と同じ構成）。
界面の重みの名前はすべて ``phase_iface`` で始まる（train_t1b.py の ``"phase" in name`` で選ばれる）。

    P1   film        既存の FiLM（relation_detr_phasefilm.PhaseFiLM）。C5 に (1 + γ) × x + β
    P2L  clsbias_lin 信号 → 15 の線形（bias つき、零初期化）を decoder 各層のクラス logit に足す。15 クラスすべて
    P2F  clsbias_fix 学習なし。バイアス = Bᵀ × 信号（B は 9 × 15 の固定表、buffer）。足す場所は P2L と同じ
    P3   query       信号 → 256 の線形（零初期化）を、decoder の主経路の object query（900）の内容ベクトルに足す

全型で最後の層を零初期化し、学習前の出力が塔単独と一致する（P2F は B を零にしたとき一致）。
信号は forward の前に ``set_phase_context(ctx)``（B, 信号の次元）で渡す。None なら界面は何もしない。
"""
from __future__ import annotations

import torch
from models.detectors.relation_detr import RelationDETR
from models.detectors.relation_detr_phasefilm import PhaseFiLM
from torch import nn
from torch.nn import functional as NF

INTERFACES = ("film", "clsbias_lin", "clsbias_fix", "query")


class RelationDETRStage2Pilot(RelationDETR):
    """RelationDETR に SPEC §3 の PD の界面を一つ足した検出器。"""

    def __init__(self, *args, interface: str, signal_dim: int, num_classes: int = 15,
                 c5_dim: int = 2048, film_hidden: int = 64, embed_dim: int = 256,
                 num_queries: int = 900, **kwargs) -> None:
        super().__init__(*args, num_classes=num_classes, num_queries=num_queries, **kwargs)
        if interface not in INTERFACES:
            raise ValueError(interface)
        self.interface = interface
        self.signal_dim = int(signal_dim)
        self.num_main_queries = int(num_queries)
        self._phase_ctx = None
        if interface == "film":
            self.phase_iface = PhaseFiLM(num_phases=signal_dim, dim=c5_dim, hidden=film_hidden)
        elif interface == "clsbias_lin":
            self.phase_iface = nn.Linear(signal_dim, num_classes)
        elif interface == "query":
            self.phase_iface = nn.Linear(signal_dim, embed_dim)
        if interface in ("clsbias_lin", "query"):
            nn.init.zeros_(self.phase_iface.weight)
            nn.init.zeros_(self.phase_iface.bias)
        if interface == "clsbias_fix":
            # B[工程, 術具]。学習しない。既定は零（恒等）。set_fixed_table で表を入れる
            self.register_buffer("phase_iface_table", torch.zeros(signal_dim, num_classes))
        if interface in ("clsbias_lin", "clsbias_fix"):
            self.transformer.register_forward_hook(self._clsbias_hook)
        if interface == "query":
            self.transformer.decoder.register_forward_pre_hook(self._query_pre_hook, with_kwargs=True)

    def set_phase_context(self, ctx) -> None:
        self._phase_ctx = ctx

    def set_fixed_table(self, table) -> None:
        """P2F の B（工程 × 術具）を入れる。"""
        table = torch.as_tensor(table, dtype=self.phase_iface_table.dtype)
        assert table.shape == self.phase_iface_table.shape, table.shape
        self.phase_iface_table.copy_(table)

    # --- P1: C5 の FiLM（relation_detr_phasefilm.RelationDETRPhaseFiLM.get_multi_levels と同じ） ---
    def get_multi_levels(self, images, mask):
        multi_level_feats = self.backbone(images.tensors)
        if self.interface == "film" and self._phase_ctx is not None:
            if isinstance(multi_level_feats, dict):
                keys = list(multi_level_feats.keys())
                multi_level_feats[keys[-1]] = self.phase_iface(multi_level_feats[keys[-1]], self._phase_ctx)
            else:
                multi_level_feats = list(multi_level_feats)
                multi_level_feats[-1] = self.phase_iface(multi_level_feats[-1], self._phase_ctx)
        multi_level_feats = self.neck(multi_level_feats)

        def interp_mask(size):
            return NF.interpolate(mask[None], size=size)[0].to(torch.bool)

        multi_level_masks = [interp_mask(feat.shape[-2:]) for feat in multi_level_feats]
        multi_level_pos_embeds = [self.position_embedding(m) for m in multi_level_masks]
        return multi_level_feats, multi_level_masks, multi_level_pos_embeds

    # --- P2L / P2F: decoder 各層のクラス logit（relation_detr_phaseclsbias と同じ場所） ---
    def class_bias(self, ctx):
        if self.interface == "clsbias_lin":
            return self.phase_iface(ctx)
        return ctx @ self.phase_iface_table.to(ctx.dtype)

    def _clsbias_hook(self, module, inputs, output):
        if self._phase_ctx is None:
            return output
        b = self.class_bias(self._phase_ctx).unsqueeze(1)          # (B, 1, C)
        oc = output[0]
        if isinstance(oc, (list, tuple)):
            new_oc = type(oc)(x + b for x in oc)
        else:
            new_oc = oc + b.unsqueeze(0)                            # (L, B, Q, C)
        return (new_oc,) + tuple(output[1:])

    # --- P3: decoder の主経路の object query の内容ベクトル ---
    def _query_pre_hook(self, module, args, kwargs):
        # hybrid の経路（学習時だけ、skip_relation=True）には足さない。denoising の query は
        # 主経路の前に連結されているので、末尾の num_main_queries 個（object query）だけに足す
        if self._phase_ctx is None or kwargs.get("skip_relation", False):
            return None
        query = kwargs["query"]
        delta = self.phase_iface(self._phase_ctx).to(query.dtype)    # (B, 256)
        n = self.num_main_queries
        head, tail = query[:, :-n], query[:, -n:] + delta[:, None, :]
        kwargs = dict(kwargs)
        kwargs["query"] = torch.cat([head, tail], 1) if head.shape[1] else tail
        return args, kwargs


def w2_parameter_names(model) -> list[str]:
    """検出塔の W2: decoder の最終層と、その層のクラスと box のヘッド（SPEC §3）。

    全層で共有の decoder.norm と、最初の段の候補選択に使う encoder_*_head は含めない。
    """
    last = model.transformer.decoder.num_layers - 1
    prefixes = (f"transformer.decoder.layers.{last}.", f"transformer.decoder.class_head.{last}.",
                f"transformer.decoder.bbox_head.{last}.")
    return [n for n, _ in model.named_parameters() if n.startswith(prefixes)]
