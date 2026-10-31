"""案 B の把持の地図の読み込み（非公式 T-2026-10-31-grasp-pilot-probe、SPEC §3.2・Task D-2）。

.venv-relation-detr で、train_t1b.py の import の後（cwd と sys.path に third_party/Relation-DETR がある状態）で使う。

train_t1b.build_det_loader と同じ読み込み（train は detr の増強、縦横比の群、batch 2、worker 4。val は増強なし、batch 1）に、
target["grasp_map"]（(5, H, W) の uint8。SPEC §3.2 のチャネルの並び）を足す。

地図を画像と同じ幾何の変換に従わせる方法:
    presets.detr の変換の列（反転、拡大縮小、切り出し、型と正規化）を、最後の SanitizeBoundingBox を除いてそのまま使い、
    地図を datapoints.Mask として画像・枠・ラベルと**同じ一度の呼び出し**に入れる。乱数の引き方は入力の空間の大きさだけで決まるため、
    空の腕（地図が全 0）と正解の腕で同じ変換が掛かる。Mask の大きさの変更は最近傍。チャネルの意味は反転で入れ替えない。
    SanitizeBoundingBox は Mask を枠と同じ並びで間引くため、地図を入れずに画像・枠・ラベルだけに当てる（元の列と同じ位置、同じ引数）。
評価時の大きさの変更（短辺 800・長辺 1333）と詰め物は検出器の中で行うため、地図はモデルの側で合わせる（pd_grasp_model）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402

MODES = ("zero", "gt", "gt_flip", "pred", "gt_pred")   # gt_flip は Task D-3 の対照だけに使う（腕ではない）
# pred と gt_pred は契約 T-2026-11-01-grasp-pilot-g で足した。G の予測の地図は 270×480 の uint8（round(p × 255)）で保存してあり、
# 画像の大きさへ双線形で戻して uint8（0〜255）のまま変換に通す。値の尺度（1/255）は型の channel_scale で戻す。
# gt_pred は [正解の 5（0 と 1）, 予測の 5（0〜255）] の 10 チャネル。


class PredView:
    """予測の地図の見取り（json: maps = (N, 5, 270, 480) の uint8 の .npy、frame_ids = 行の並び、mapping = 入れ替えの対応 or null）。

    フレーム f の地図 = maps[行(mapping[f] if mapping else f)]。入れ替えの腕は mapping で行を引き替える（地図そのものは写さない）。
    """

    def __init__(self, path):
        import json
        d = json.loads(Path(path).read_text())
        self.path, self.maps_path = str(path), d["maps"]
        self.row = {f: i for i, f in enumerate(d["frame_ids"])}
        self.mapping = d.get("mapping")
        self._maps = None

    def get(self, stem, shape):
        if self._maps is None:                      # worker ごとに開く
            self._maps = np.load(self.maps_path, mmap_mode="r")
        src = self.mapping[stem] if self.mapping else stem
        m = torch.from_numpy(np.ascontiguousarray(self._maps[self.row[src]])).float()[None]
        m = torch.nn.functional.interpolate(m, size=tuple(shape), mode="bilinear", align_corners=False)[0]
        return m.round().clamp(0, 255).to(torch.uint8).numpy()


def make_dataset_class():
    from datasets.coco import CocoDetection
    from transforms import v2 as T
    from transforms.v2 import SanitizeBoundingBox
    from util import datapoints

    class GraspMapCocoDetection(CocoDetection):
        def __init__(self, *args, mode: str, index: G.HTSIndex, pred_view=None, **kwargs):
            super().__init__(*args, **kwargs)
            if mode not in MODES:
                raise ValueError(mode)
            if (mode in ("pred", "gt_pred")) != (pred_view is not None):
                raise ValueError(f"pred_view は mode pred・gt_pred のときだけ渡す: {mode}")
            self.mode = mode
            self.index = index
            self.pred = PredView(pred_view) if pred_view is not None else None
            self._geo = self._sanitize = None
            if self._transforms is not None:
                steps = list(self._transforms.transforms)
                assert isinstance(steps[-1], SanitizeBoundingBox), steps[-1]
                assert not any(isinstance(s, SanitizeBoundingBox) for s in steps[:-1])
                self._geo = T.Compose(steps[:-1])
                self._sanitize = steps[-1]

        def stem(self, image_id):
            return Path(self.coco.imgs[image_id]["file_name"]).stem

        def grasp_map(self, image_id, shape):
            if self.mode == "zero":
                return np.zeros((len(G.MAP_CHANNELS),) + tuple(shape), np.uint8)
            if self.mode == "pred":
                return self.pred.get(self.stem(image_id), shape)
            if self.mode == "gt_pred":
                gt = self.index.map_channels(self.stem(image_id))
                assert gt.shape[1:] == tuple(shape), (gt.shape, shape)
                return np.concatenate([gt, self.pred.get(self.stem(image_id), shape)], 0)
            m = self.index.map_channels(self.stem(image_id))
            assert m.shape[1:] == tuple(shape), (m.shape, shape)
            return m

        def data_augmentation(self, image, target):
            image = datapoints.Image(image)
            boxes = datapoints.BoundingBox(target["boxes"], format=datapoints.BoundingBoxFormat.XYXY,
                                           spatial_size=image.shape[-2:])
            labels = target["labels"]
            gmap = datapoints.Mask(torch.from_numpy(self.grasp_map(target["image_id"], image.shape[-2:])))
            if self._transforms is not None:
                image, boxes, gmap, labels = self._geo(image, boxes, gmap, labels)
                image, boxes, labels = self._sanitize(image, boxes, labels)
            gm = gmap.as_subclass(torch.Tensor)
            if self.mode == "gt_flip":
                gm = gm.flip(-1)                    # 対照: 変換の後の地図を左右に反転させる（Task D-3）
            target["grasp_map"] = gm.contiguous()    # CocoDetection.__getitem__ がこの target を deepcopy して返す
            return image.data, boxes.data, labels

    return GraspMapCocoDetection


def build_grasp_loader(ego_root: str, ann_dir: str, train: bool, mode: str, index=None, shuffle_seed=None, pred_view=None):
    """train_t1b.build_det_loader と同じ形の DataLoader（地図つき）。"""
    from torch.utils import data
    from transforms import presets
    from util.collate_fn import collate_fn
    from util.group_by_aspect_ratio import GroupedBatchSampler, create_aspect_ratio_groups

    cls = make_dataset_class()
    index = index or G.HTSIndex(("train", "val"))
    ann = "instances_train.json" if train else "instances_val.json"
    ds = cls(img_folder=ego_root, ann_file=f"{ann_dir}/{ann}", transforms=presets.detr if train else None,
             train=train, mode=mode, index=index, pred_view=pred_view)
    params = dict(num_workers=4, collate_fn=collate_fn, pin_memory=True)  # nosemgrep
    if train:
        group_ids = create_aspect_ratio_groups(ds, k=3)
        bs = GroupedBatchSampler(data.RandomSampler(ds), group_ids, 2)
        return data.DataLoader(ds, batch_sampler=bs, **params)
    return data.DataLoader(ds, 1, shuffle=False, **params)
