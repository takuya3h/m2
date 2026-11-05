"""起動の設定の照合（Task A-6）。手本（dlsta 探索の 0 番の run の command.sh）と本契約の再現台本を比べる。

差の全行を書き、許した違い（§4: 経路・GPU の番号・ポート・seed・置き場・``NCCL_P2P_DISABLE=1``・本契約の識別子。
置き場と識別子を渡す ``TOWER_SEARCH_*`` を含む）を正規化した後に一致するかを判定する。

    python compare_launch.py <再現台本の置き場（SCR）> <out.json> [--selftest]
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PHASE = ROOT / "experiments/phase1/stage1_ptower_search"
TEMPLATE_DET = ROOT / "experiments/baselines/stage1_dtower_search/point00_dcoco_foldA_seed42/command.sh"
DLSTA_SCR = "/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta"
HEADS = ["003_P15_A_L6_w0.0_h30", "004_P15_A_L8_w0.0_h30", "005_P15_B_L6_w0.0_h30", "006_P15_B_L6_w0.0_h60",
         "007_P15_C_L6_w0.15_h30", "008_P15_C_L6_w0.3_h30", "009_P15_B_L8_w0.0_h30", "010_P15_B_L8_w0.0_h60",
         "011_P15_C_L8_w0.15_h30", "012_P15_C_L8_w0.3_h30"]
ADDED = re.compile(r"^export (NCCL_P2P_DISABLE=1|TOWER_SEARCH_(TASK|SCRATCH|PHASE_PUBLISH|STEP_LOG)=.*)$")


def normalize(text, scr):
    out = []
    for line in text.splitlines():
        if ADDED.match(line):
            continue  # 許した違い（追加した環境変数）
        line = line.replace("/home/ubuntu/local/m2", "<ROOT>").replace(str(ROOT), "<ROOT>")
        for root in (DLSTA_SCR, str(scr)):
            # 置き場のディレクトリは丸ごと <SCR> に、ファイルを指す経路はファイル名だけ残す
            line = re.sub(re.escape(root) + r"[^\s]*",
                          lambda m: "<SCR>/" + m.group(0).rsplit("/", 1)[1] if "." in m.group(0).rsplit("/", 1)[1]
                          else "<SCR>", line)
        line = re.sub(r"(CUDA_VISIBLE_DEVICES=)[0-9,]*", r"\1<GPU>", line)
        line = re.sub(r"(--master_port=|--main_process_port )[0-9]+", r"\1<PORT>", line)
        line = re.sub(r"(--seed )[0-9]+", r"\1<SEED>", line)
        line = re.sub(r" seed=[0-9]+(?=\s|$)", "", line)
        out.append(line)
    return out


def pairs(scr):
    t = lambda n: TEMPLATE_PHASE / f"stage1_ptower_search_{n}_foldA_point00_seed42/command.sh"  # noqa: E731
    rows = []
    for seed in (42, 123):
        w = scr / "phase" / f"seed{seed}"
        rows.append((f"phase{seed}_finetune", t("001_ft_coco_lr0.0001"), w / "finetune.command.sh"))
        rows.append((f"phase{seed}_extract", t("002_features_coco_lr0.0001"), w / "extract.command.sh"))
        rows += [(f"phase{seed}_head{i:02d}", t(h), w / f"head{i:02d}/train.command.sh") for i, h in enumerate(HEADS)]
    rows += [(f"det{label}_train", TEMPLATE_DET, scr / "detector" / label / "train.command.sh")
             for label in ("42a", "42b", "123")]
    return rows


def main():
    scr, out = Path(sys.argv[1]), Path(sys.argv[2])
    selftest = "--selftest" in sys.argv
    result = []
    for name, template, mine in pairs(scr):
        a, b = template.read_text(), mine.read_text()
        if selftest and name == "phase42_finetune":
            a = a.replace("workers=4", "workers=2")
        raw = [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), "template", "bengio", lineterm="")
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        na, nb = normalize(a, scr), normalize(b, scr)
        rest = [l for l in difflib.unified_diff(na, nb, "template", "bengio", lineterm="")
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        result.append({"run": name, "template": str(template.relative_to(ROOT)), "raw_diff": raw,
                       "after_allowed": rest, "same_except_allowed": not rest})
    if selftest:
        print(json.dumps({r["run"]: r["same_except_allowed"] for r in result if r["run"] == "phase42_finetune"}))
        return
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(sum(r["same_except_allowed"] for r in result), "/", len(result))
    for r in result:
        if not r["same_except_allowed"]:
            print(r["run"], r["after_allowed"])


if __name__ == "__main__":
    main()
