#!/usr/bin/env bash
# efros の工程塔の三つの run と特徴キャッシュを、読むだけで andrew の版管理の外へ写す（非公式 T-2026-10-18-stage2-pilot-folda）。
# efros 側で走るのは sha256sum と rsync の送り出しだけ。両端の sha256 と、efros 側の写す前後の sha256 を残す。
set -euo pipefail
ST="${1:?写し先}"
LIST=(
  experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42
  experiments/phase1/stage1_ptower_20_008_features_coco_lr0.0001_foldA_seed42
  experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42
  data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42
)
SSH=(ssh -o BatchMode=yes)
remote_sha() {
  "${SSH[@]}" efros "cd ~/slocal2/m2 && find ${LIST[*]} -type f -print0 | sort -z | xargs -0 sha256sum" 2>/dev/null
}
mkdir -p "$ST"
cd "$ST"
remote_sha > efros_sha256_before.txt
for p in "${LIST[@]}"; do
  mkdir -p "$p"
  rsync -a -e "ssh -o BatchMode=yes" "efros:slocal2/m2/$p/" "$p/" 2> >(grep -v 'Identity file' >&2)
done
find "${LIST[@]}" -type f -print0 | sort -z | xargs -0 sha256sum > andrew_copy_sha256.txt
remote_sha > efros_sha256_after.txt
echo "efros files: $(wc -l < efros_sha256_before.txt)  copy files: $(wc -l < andrew_copy_sha256.txt)"
cmp -s efros_sha256_before.txt efros_sha256_after.txt && echo "efros before==after: yes" || echo "efros before==after: NO"
cmp -s efros_sha256_before.txt andrew_copy_sha256.txt && echo "efros==copy: yes" || echo "efros==copy: NO"
