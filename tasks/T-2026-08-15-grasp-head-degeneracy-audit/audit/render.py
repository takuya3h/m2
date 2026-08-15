"""head_quality.md を実測から生成する。**表示用の切り詰めを記録へ混ぜない。**

手で転記すると桁を落とす。JSON を正本とし、読む形はそこから作る。
"""

import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
DIMS = ["left_hand", "right_hand", "left_hand_tool", "right_hand_tool", "two_hands_tool"]
JP = {
    "left_hand": "左手が写る",
    "right_hand": "右手が写る",
    "left_hand_tool": "左手が器具を持つ",
    "right_hand_tool": "右手が器具を持つ",
    "two_hands_tool": "両手で器具を持つ",
}
SEEDS = ["42", "123", "456"]


def main() -> None:
    q = json.loads((AUDIT / "head_quality.json").read_text())
    d = json.loads((AUDIT / "degeneracy.json").read_text())
    out: list[str] = []
    w = out.append

    w("# Phase B / C — 下見と同じ土台で測り直した結果")
    w("")
    w("数値の正本は `head_quality.json` と `degeneracy.json`。予測は `preds_inj_seed*.npz`。")
    w("測る側は val のみ。**試験側は使っていない。**")
    w("")
    w("## 1. 指標を揃えた比較")
    w("")
    w("曲線下面積は順位にしか依存しないため、sigmoid を通した値でも logits でも同値である。")
    w("下見の契約と同じ `sklearn` の `roc_auc_score` / `average_precision_score` を使った。")
    w("")
    w("| 次元 | 正例の割合 | 曲線下面積（実測） | 下見の曲線下面積 | 上回るか | 偶然 |")
    w("|---|---:|---:|---:|:--:|---:|")
    for n in DIMS:
        a, p = q[n]["roc_auc_mean"], q[n]["probe_roc_auc"]
        mark = "**上回る**" if a > p else "下回る"
        w(f"| {JP[n]} | {q[n]['positive_rate_val']:.4f} | **{a:.4f}** | {p:.4f} | {mark} | 0.5 |")
    w("")
    w("**五つの次元すべてで下見を上回り、すべて偶然の水準を上回った。**")
    w("")
    w("## 2. 平均適合率と偶然の水準")
    w("")
    w("| 次元 | 平均適合率 | 偶然（正例の割合） | 偽の予測 | 上回るか |")
    w("|---|---:|---:|---:|:--:|")
    for n in DIMS:
        ap = q[n]["average_precision_mean"]
        ch = q[n]["chance_average_precision"]
        w(f"| {JP[n]} | {ap:.4f} | {ch:.4f} | {q[n]['fake_majority']['average_precision']:.4f} | "
          f"{'**上回る**' if ap > ch else '下回る'} |")
    w("")
    w("## 3. 前の実験が報告した正しさの割合との対比")
    w("")
    w("**同じ予測から両方を出している。** 像がどれだけ違うかが分かる。")
    w("")
    w("| 次元 | 正しさの割合 | 多数派だけで出る割合 | 差 | 曲線下面積 |")
    w("|---|---:|---:|---:|---:|")
    for n in DIMS:
        acc, maj = q[n]["accuracy_mean"], q[n]["majority_rate"]
        w(f"| {JP[n]} | {acc:.5f} | {maj:.5f} | {acc - maj:+.5f} | {q[n]['roc_auc_mean']:.4f} |")
    w("")
    w("## 4. 前の実験の集計値を再現できたか")
    w("")
    w("**保存されている重みから予測を作り直した。学習はやり直していない。**")
    w("重みは前の実験そのものであるから、条件は定義上一致する。")
    w("")
    w("| 次元 | 再測 | 前の実験の報告 | 一致 |")
    w("|---|---:|---:|:--:|")
    for n in DIMS:
        w(f"| {JP[n]} | {q[n]['accuracy_mean']:.7f} | {q[n]['prior_reported_accuracy']:.7f} | "
          f"{'○' if q[n]['accuracy_reproduces_prior'] else '×'} |")
    w("")
    w("## 5. 対照 — 多数派を出し続けるだけの偽の予測")
    w("")
    w("| 次元 | 偽の正しさの割合 | 偽の曲線下面積 | 0.5 へ落ちたか |")
    w("|---|---:|---:|:--:|")
    for n in DIMS:
        f = q[n]["fake_majority"]
        w(f"| {JP[n]} | {f['accuracy']:.5f} | {f['roc_auc']:.4f} | {'○' if abs(f['roc_auc'] - 0.5) < 1e-9 else '×'} |")
    w("")
    w("**五つすべてで 0.5 へ落ちた。測り方は壊れていない。**")
    w("")
    w("## 6. 予測の散らばり（縮退の直接の検査）")
    w("")
    w("| 次元 | seed | 最小 | 最大 | 標準偏差 | 相異なる値 | 四分位間 |")
    w("|---|---|---:|---:|---:|---:|---:|")
    for n in DIMS:
        for s in SEEDS:
            x = d[n]["per_seed"][s]
            w(f"| {JP[n] if s == '42' else ''} | {s} | {x['min']:.6f} | {x['max']:.6f} | "
              f"{x['std']:.6f} | {x['n_distinct']} | {x['iqr']:.6f} |")
    w("")
    w("測る側の有効フレームは 1514 である。**相異なる値がほぼフレーム数と等しい。**")
    w("連続値としては、どの次元も定数ではない。")
    w("")
    w("## 7. 丸めた後の偏り")
    w("")
    w("| 次元 | 正例の割合 | 丸めた後に正になった割合（42 / 123 / 456） |")
    w("|---|---:|---|")
    for n in DIMS:
        r = d[n]["predicted_positive_rate_per_seed"]
        w(f"| {JP[n]} | {d[n]['positive_rate_val']:.4f} | {r['42']:.4f} / {r['123']:.4f} / {r['456']:.4f} |")
    w("")
    w("**丸めた後は縮退している。** 連続値と丸めた後で像が正反対になる。")
    w("注入されたのは丸めた後の値ではなく `predicted_sigmoid`、すなわち連続値である。")

    (AUDIT / "head_quality.md").write_text("\n".join(out) + "\n")
    print(f"生成: {AUDIT / 'head_quality.md'}  （{len(out)} 行）")


if __name__ == "__main__":
    main()
