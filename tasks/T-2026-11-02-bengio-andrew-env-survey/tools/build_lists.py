"""Task D の経路の一覧（lists.json）と、andrew へ渡す一覧を埋めた写しを作る（bengio の契約の置き場にだけ書く）。"""
import json
T = "tasks/T-2026-11-02-bengio-andrew-env-survey/tools/"
lock = json.load(open("experiments/analysis/tower_reselect_search_dlsta/image_input_lock.json"))
lock_paths = sorted({x["selected"] for x in lock} | {x["counterpart"] for x in lock if x["counterpart"]})
M = "data/processed/phase_manifest/"; MA = "data/processed/phase_manifest_all_phase/"
files = {
    "manifest": [d + f for d in (M, MA) for f in ("train.json", "val.json", "test.json", "phase_vocab.json")],
    "tool_ann": [f"data/annotations/egosurgery_tool/instances_{s}.json" for s in ("train", "val", "test")],
    "tool_folds": [f"data/annotations/egosurgery_tool_folds/{k}/instances_{s}.json" for k in "ABCDE" for s in ("train", "val", "test")]
                  + ["data/annotations/egosurgery_tool_folds/fold_report.json"],
    "splits": [f"data/splits/ego_{s}.txt" for s in ("train", "val", "test")] + ["docs/stage0/A1_fold_table.md"],
    "weights": ["data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth",
                "~/.cache/torch/hub/checkpoints/resnet50-0676ba61.pth",
                "~/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth"],
    "towers": [f"experiments/baselines/stage1_dtower_r2/dcoco_fold{k}_seed42/work/best_ap.pth" for k in "AB"]
              + [f"experiments/phase1/stage1_ptower_r3_{r}/checkpoints/best.pth" for r in ("005_ft_coco_lr0.0001_foldA_seed42", "008_ft_coco_lr0.0001_foldB_seed42")],
    "stage2": [p.replace("/home/ubuntu/", "~/") for p in json.load(open(T + "stage2_material_paths.json"))],
}
lists = {"lock_paths": lock_paths, "files": files, "blob_groups": ["tool_ann", "splits"],
         "dirs": ["data/raw/ego", "data/raw/OpenSurgery_Dataset/01_frames/initial_videos", "data/processed/stage1_features",
                  "data/annotations/egosurgery_hts", "data/annotations/egosurgery_tool_folds", "data/processed/phase_manifest",
                  "data/processed/phase_manifest_all_phase"]}
json.dump(lists, open(T + "lists.json", "w"))
src = open(T + "data_inventory.py").read()
k = src.index('if __name__ == "__main__":')
open("/tmp/claude-1000/-home-ubuntu-slocal2-m2/10c34735-1906-4fda-926f-fa66f418bb33/scratchpad/data_inventory_embedded.py", "w").write(
    src[:k] + "_EMBEDDED = " + json.dumps(lists) + "\n\n\n" + src[k:])
print(len(lock_paths), {g: len(v) for g, v in files.items()})
