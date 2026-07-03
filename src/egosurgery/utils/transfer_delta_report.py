"""haux / taux 系統の Δ_phase 集計・paired-σ 判定の共通ロジック（単一情報源）。

`scripts/report_haux_results.py`（系統① 手情報→工程）と
`scripts/report_taux_results.py`（系統② region-token 補助→工程）が共有する集計本体。
paired-σ の判定式を 1 箇所に集約し、手法間で判定基準がぶれないようにする
（研究インテグリティ: 平均値の手打ち・暗算を根絶し、metrics.json の生値のみから機械生成）。

Δ の定義（§固定値・S4 base 分母は定数）:
  Δ_acc(seed)      = phase_accuracy(seed)  − 0.8986   （S4 base phase accuracy）
  Δ_macroF1(seed)  = phase_macro_f1(seed)  − 0.709    （S4 base 公式 macro-F1）

paired-σ 判定（§10.1 / analyze_phase_coupling.py の対応差ロジックと同一）:
  各手法の per-seed Δ について
    mean(Δ)   = statistics.mean(Δ over seeds)
    σ         = statistics.pstdev(Δ over seeds)   （母標準偏差）
    |mean|/σ
    同符号     = 全 seed の Δ が同符号
  ``|mean(Δ)| > σ`` かつ ``同符号`` のとき ✓（有意）、それ以外 ×。
  seed が 1 個以下なら σ が定義できず判定不能（n/a(n<2)）。

なお base は定数のため σ(Δ) は σ(metric)（各手法の per-seed 実測値の母標準偏差）に等しい。
判定に使う σ は「その手法自身の per-seed ばらつき」であり、base seed の ±0.0028 ではない。
"""

from __future__ import annotations

import json
import re
import statistics as st
from pathlib import Path

# S4 base 分母（固定値）。全 Δ はこれに対して計算する。
BASE_ACC = 0.8986
BASE_MACRO_F1 = 0.709

# 実験フォルダ名 {step}_{seq:03d}_{description}_seed{seed}。
# step==description（haux/taux は _method_tag をそのまま使う）ため、
# 手法(step tag) = 先頭から最初の _NNN_ の直前まで。seed は末尾 _seed\d+。
_DIR_RE = re.compile(r"^(?P<method>.+?)_(?P<seq>\d{3})_.+_seed(?P<seed>\d+)$")


def _parse_dirname(name: str) -> tuple[str, int, int] | None:
    """フォルダ名を (method, seq, seed) に分解。合致しなければ None。"""
    m = _DIR_RE.match(name)
    if not m:
        return None
    return m.group("method"), int(m.group("seq")), int(m.group("seed"))


def scan_methods(transfer_dir: Path, family_prefix: str) -> dict[str, dict[int, dict]]:
    """``experiments/transfer`` 配下の ``{family_prefix}_*`` を走査して集計素材を返す。

    Returns:
        ``{method: {seed: {"acc": float, "macro_f1": float, "seq": int, "dir": str}}}``。
        同一 (method, seed) が複数あれば seq 最大（最新の再実行）を採用する。
        metrics.json が無い / 壊れている / 必須指標が欠落しているフォルダは黙って除外。
    """
    methods: dict[str, dict[int, dict]] = {}
    if not transfer_dir.exists():
        return methods
    prefix = f"{family_prefix}_"
    for child in sorted(transfer_dir.iterdir()):
        if not child.is_dir() or not child.name.startswith(prefix):
            continue
        parsed = _parse_dirname(child.name)
        if parsed is None:
            continue
        method, seq, seed = parsed
        metrics_path = child / "metrics.json"
        if not metrics_path.exists():
            continue
        try:
            data = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        acc = data.get("phase_accuracy")
        f1 = data.get("phase_macro_f1")
        if not isinstance(acc, (int, float)) or isinstance(acc, bool):
            continue
        if not isinstance(f1, (int, float)) or isinstance(f1, bool):
            continue
        seed_map = methods.setdefault(method, {})
        prev = seed_map.get(seed)
        # 同一 seed の重複は seq 最大（最新再実行）を採用。
        if prev is None or seq >= prev["seq"]:
            seed_map[seed] = {
                "acc": float(acc),
                "macro_f1": float(f1),
                "seq": seq,
                "dir": child.name,
            }
    return methods


def _stat(deltas: list[float]) -> dict:
    """per-seed Δ のリストから paired-σ 判定量を計算する（§10.1）。"""
    n = len(deltas)
    mean_d = st.mean(deltas) if n else 0.0
    sigma = st.pstdev(deltas) if n else 0.0  # 母標準偏差（n=1 → 0.0）
    same_sign = n >= 1 and (
        all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
    )
    if n < 2:
        significant = False
        verdict = "n/a(n<2)"
    else:
        # |mean| > σ かつ 全 seed 同符号 のときのみ有意（符号反転の見落とし防止）。
        significant = same_sign and (abs(mean_d) > sigma)
        verdict = "✓" if significant else "×"
    if sigma > 0:
        ratio_s = f"{abs(mean_d) / sigma:.2f}"
    else:
        ratio_s = "∞" if abs(mean_d) > 0 else "0"
    return {
        "n": n,
        "mean": mean_d,
        "sigma": sigma,
        "same_sign": same_sign,
        "significant": significant,
        "verdict": verdict,
        "ratio_s": ratio_s,
    }


def summarize_method(seed_map: dict[int, dict]) -> dict:
    """1 手法分の集計。acc / macro_f1 それぞれの per-seed Δ と paired-σ 判定を返す。"""
    seeds = sorted(seed_map)
    acc_vals = [seed_map[s]["acc"] for s in seeds]
    f1_vals = [seed_map[s]["macro_f1"] for s in seeds]
    acc_deltas = [v - BASE_ACC for v in acc_vals]
    f1_deltas = [v - BASE_MACRO_F1 for v in f1_vals]
    return {
        "seeds": seeds,
        "acc_vals": acc_vals,
        "f1_vals": f1_vals,
        "acc_deltas": acc_deltas,
        "f1_deltas": f1_deltas,
        "acc_stat": _stat(acc_deltas),
        "f1_stat": _stat(f1_deltas),
    }


def _per_seed_cell(seeds: list[int], vals: list[float], deltas: list[float]) -> str:
    """per-seed セル: ``42=0.9021(+0.35pp)`` の空白区切り（Δ は pp 表示）。"""
    parts = [
        f"{s}={v:.4f}({d * 100:+.2f})"
        for s, v, d in zip(seeds, vals, deltas)
    ]
    return " ".join(parts) if parts else "—"


def _metric_table(methods_summ: list[tuple[str, dict]], which: str) -> list[str]:
    """acc または macro_f1 の markdown 表を行リストで返す。"""
    stat_key = "acc_stat" if which == "acc" else "f1_stat"
    val_key = "acc_vals" if which == "acc" else "f1_vals"
    delta_key = "acc_deltas" if which == "acc" else "f1_deltas"
    lines = [
        "| 手法 (step tag) | seeds (n) | per-seed 生値(Δpp) | Δ mean±σ (pp) | \\|Δ\\|/σ | 同符号 | 有意(paired-σ) |",
        "|---|---|---|---|---|---|---|",
    ]
    for method, summ in methods_summ:
        stat = summ[stat_key]
        seeds = summ["seeds"]
        cell = _per_seed_cell(seeds, summ[val_key], summ[delta_key])
        seeds_s = "/".join(str(s) for s in seeds) + f" (n={stat['n']})"
        mean_pp = stat["mean"] * 100
        sigma_pp = stat["sigma"] * 100
        mean_sd = f"{mean_pp:+.2f}±{sigma_pp:.2f}"
        same = "✓" if stat["same_sign"] else "×"
        lines.append(
            f"| `{method}` | {seeds_s} | {cell} | {mean_sd} | "
            f"{stat['ratio_s']} | {same} | {stat['verdict']} |"
        )
    return lines


def render_markdown(family_prefix: str, aux_label: str, methods: dict) -> str:
    """集計結果を REPORT.md 本文（markdown 文字列）に整形する。"""
    title = f"# {family_prefix} 系統 Δ_phase 集計レポート"
    header = [
        title,
        "",
        f"対象: {aux_label}",
        "",
        f"走査元: `experiments/transfer/{family_prefix}_*`（metrics.json 直読み・手打ち介入なし）。",
        "",
        "分母（S4 base・固定値）: phase accuracy = **0.8986** / 公式 macro-F1 = **0.709**。",
        "各手法の per-seed Δ = (実測 − base)。σ は per-seed Δ の母標準偏差 "
        "(`statistics.pstdev`)。",
        "判定（§10.1）: `|mean(Δ)| > σ` かつ 全 seed 同符号 のとき ✓（有意）。"
        "seed<2 は判定不能 (n/a)。pp = ×100 表示。",
        "",
    ]

    if not methods:
        header.append(
            f"## 該当実験なし\n\n"
            f"`experiments/transfer/` に `{family_prefix}_*` の完了済み実験"
            f"（metrics.json に phase_accuracy / phase_macro_f1 を持つもの）が"
            f"見つかりませんでした（0 件）。実験を実行後に再生成してください。"
        )
        return "\n".join(header) + "\n"

    methods_summ = [(m, summarize_method(methods[m])) for m in sorted(methods)]

    body: list[str] = []
    body.append(f"## phase accuracy Δ（vs base 0.8986）")
    body.append("")
    body += _metric_table(methods_summ, "acc")
    body.append("")
    body.append(f"## phase macro-F1 Δ（vs base 0.709）")
    body.append("")
    body += _metric_table(methods_summ, "f1")
    body.append("")

    # 有意（✓）手法の要約。
    sig_acc = [m for m, s in methods_summ if s["acc_stat"]["significant"]]
    sig_f1 = [m for m, s in methods_summ if s["f1_stat"]["significant"]]
    body.append("## 有意判定サマリ")
    body.append("")
    body.append(
        f"- accuracy で有意(✓): {', '.join('`' + m + '`' for m in sig_acc) or 'なし'}"
    )
    body.append(
        f"- macro-F1 で有意(✓): {', '.join('`' + m + '`' for m in sig_f1) or 'なし'}"
    )
    body.append("")
    n_dirs = sum(len(v) for v in methods.values())
    body.append(
        f"（集計: {len(methods)} 手法 / 実験フォルダ {n_dirs} 件。"
        f"同一 (手法, seed) の重複は最新 seq を採用。）"
    )

    return "\n".join(header + body) + "\n"


def build_report(
    family_prefix: str,
    aux_label: str,
    transfer_dir: Path,
    out_path: Path,
) -> int:
    """走査 → markdown 生成 → REPORT.md 書き出し。手法数を返す（0 = 該当なし）。

    Args:
        family_prefix: ``haux`` / ``taux``。
        aux_label: レポート冒頭に載せる系統の説明。
        transfer_dir: ``experiments/transfer``。
        out_path: 出力する REPORT.md のパス。

    Returns:
        集計できた手法数（0 件なら 0）。
    """
    methods = scan_methods(transfer_dir, family_prefix)
    md = render_markdown(family_prefix, aux_label, methods)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    if not methods:
        print(f"[{family_prefix}] 0件: {transfer_dir}/{family_prefix}_* に該当実験なし")
        print(f"[{family_prefix}] 該当なしレポートを書き出し -> {out_path}")
        return 0

    n_dirs = sum(len(v) for v in methods.values())
    print(
        f"[{family_prefix}] {len(methods)} 手法 / {n_dirs} 実験フォルダ を集計 "
        f"-> {out_path}"
    )
    for method in sorted(methods):
        summ = summarize_method(methods[method])
        a, f = summ["acc_stat"], summ["f1_stat"]
        print(
            f"  {method}: n={a['n']} "
            f"acc Δ={a['mean'] * 100:+.2f}±{a['sigma'] * 100:.2f}pp[{a['verdict']}] "
            f"f1 Δ={f['mean'] * 100:+.2f}±{f['sigma'] * 100:.2f}pp[{f['verdict']}]"
        )
    return len(methods)
