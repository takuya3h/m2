#!/usr/bin/env python
"""検出側 run の永続成果物レイアウト（``experiments/transfer/<run_name>/``）の共通ヘルパ。

背景（このモジュールが存在する理由）:
    検出側トレーナ（``train_t1b.py`` 系）の成果物は長らく ``/tmp`` にしか残らず、
    再起動・tmpfs 掃除で消えていた。その結果 eval-only の追認が反復的に実行不能になり、
    ckpt 不在 seed の恒等代替・test 未実施・失敗機序の推測どまり、といった実害が出た。
    ここでは **保存先を永続化**し、さらに **per-image の検出結果（predictions）** を
    既定で残すことで、ckpt が失われても AP 以外の解析（FP/FN 内訳・工程別品質・
    定性可視化）が後から可能な状態を担保する。

設計上の制約:
    - ``train_t1b.py`` は ``.venv-relation-detr``（``egosurgery`` 未導入）で動く。
      よって本モジュールは **標準ライブラリのみ**に依存する（``yaml`` は任意・遅延）。
    - 既存の学習・評価ロジックには触れない。保存先と保存物の追加だけを担う。

ディレクトリ規約（工程側 ExperimentManager と同一）::

    experiments/transfer/<run_name>/
      checkpoints/      best_t1b.pth 等
      predictions/      {split}_{tag}_ep{N}.json[.gz] / {split}_{tag}_best.json[.gz]
      logs/             val_metrics_by_epoch.json, eval_meta.json, *.log
      config.yaml  command.sh  git_commit.txt  metrics.json
      per_class_ap.json  notes.md  server.txt

predictions は COCO detection results 形式::

    [{"image_id": int, "category_id": int, "bbox": [x, y, w, h], "score": float}, ...]

CLI（証跡の検証用・両 venv で動く）::

    python scripts/run_artifacts.py --verify-init-identity <run_inj> <run_ctrl>
    python scripts/run_artifacts.py --show <run_name>
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shlex
import socket
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# EGO_BODY は train_t1b.py と同じ規約（リポジトリ root の上書き用）。
PROJECT_ROOT = Path(os.environ.get("EGO_BODY", Path(__file__).resolve().parents[1]))
TRANSFER_ROOT = PROJECT_ROOT / "experiments" / "transfer"

# setup で必ず作る空サブディレクトリ（ExperimentManager の _SUBDIRS と揃える）。
SUBDIRS = ("checkpoints", "predictions", "logs")

# eval recipe の検出数上限（config: select_box_nums_for_evaluation=300）と同一。
# score 閾値での足切りは AP を再現不能にするので行わず、この上限のみで容量を抑える。
EVAL_TOPK = 300

# logs/ 配下で git 追跡対象にしているファイル名（.gitignore の例外と一致させること）。
EPOCH_LOG_NAME = "val_metrics_by_epoch.json"


def eval_meta_name(split: str) -> str:
    """評価メタのファイル名。split 毎に分ける（val と test で上書きし合わないため）。"""
    return f"eval_meta_{split}.json"


# --------------------------------------------------------------------------- #
# run ディレクトリの解決
# --------------------------------------------------------------------------- #
def resolve_run_dir(run_name: str, work_dir: str | os.PathLike | None = None) -> Path:
    """run ディレクトリを決める。

    Args:
        run_name: 既定レイアウト時のディレクトリ名（``experiments/transfer/<run_name>``）。
        work_dir: 明示指定（後方互換の ``T1B_WORK_DIR`` 等）。相対パスは
            リポジトリ root 基準で解決する（``os.chdir`` 後でも誤配置しないため）。

    Returns:
        run ディレクトリの絶対 :class:`~pathlib.Path`（未作成）。
    """
    if work_dir:
        p = Path(work_dir)
        return p if p.is_absolute() else (PROJECT_ROOT / p)
    return TRANSFER_ROOT / run_name


def ensure_layout(run_dir: str | os.PathLike) -> Path:
    """run ディレクトリと規約サブディレクトリを作成して返す。"""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (run_dir / sub).mkdir(exist_ok=True)
    return run_dir


def checkpoints_dir(run_dir: str | os.PathLike) -> Path:
    return Path(run_dir) / "checkpoints"


def predictions_dir(run_dir: str | os.PathLike) -> Path:
    return Path(run_dir) / "predictions"


def logs_dir(run_dir: str | os.PathLike) -> Path:
    return Path(run_dir) / "logs"


def run_dir_for_checkpoint(ckpt: str | os.PathLike, fallback_run_name: str) -> Path:
    """ckpt の所属 run ディレクトリを返す（判別できなければ fallback の run を使う）。

    ``experiments/transfer/<run>/checkpoints/x.pth`` から来た ckpt の評価結果は、
    その run の ``predictions/`` に置くのが自然。S0-frozen のような run 外の ckpt や
    旧レイアウトの ckpt は、評価専用の run ディレクトリへ落とす。
    """
    p = Path(ckpt).resolve()
    if p.parent.name == "checkpoints" and p.parent.parent.parent == TRANSFER_ROOT.resolve():
        return p.parent.parent
    return TRANSFER_ROOT / fallback_run_name


def find_checkpoint(run_dir: str | os.PathLike, name: str = "best_t1b.pth") -> Path | None:
    """``checkpoints/<name>`` を優先し、無ければ旧 flat レイアウトを探す。

    旧 run（``/tmp/t1b_*/best_t1b.pth`` のように run 直下に置かれたもの）を
    評価し直せる状態を保つための後方互換パス。
    """
    run_dir = Path(run_dir)
    for cand in (run_dir / "checkpoints" / name, run_dir / name):
        if cand.exists():
            return cand
    return None


# --------------------------------------------------------------------------- #
# predictions の保存・読み込み
# --------------------------------------------------------------------------- #
def predictions_name(
    split: str, tag: str, *, epoch: int | None = None, best: bool = False, compress: bool = True
) -> str:
    """predictions のファイル名を組み立てる。

    ``tag`` には注入条件（``inj`` / ``ctrl``）を必ず入れる。後から
    「どちらの run の予測か」がファイル名だけで判別できることが解析の前提。

    Examples:
        >>> predictions_name("val", "inj", epoch=-1, compress=False)
        'val_inj_ep-1.json'
        >>> predictions_name("test", "ctrl", best=True, compress=False)
        'test_ctrl_best.json'
    """
    stem = f"{split}_{tag}_best" if best else f"{split}_{tag}_ep{epoch}"
    return stem + (".json.gz" if compress else ".json")


def truncate_topk(results: list, topk: int = EVAL_TOPK) -> list:
    """image_id ごとに score 上位 ``topk`` 件へ打ち切る。

    eval recipe と同一の上限（300）なので通常は恒等変換になる。score 閾値による
    足切りは AP を再現不能にするため一切行わない。打ち切りが起きない限り入力の
    並び順をそのまま保つ（再評価との差異要因を作らない）。
    """
    if topk is None or topk <= 0:
        return list(results)
    by_img: dict = defaultdict(list)
    for r in results:
        by_img[r["image_id"]].append(r)
    if all(len(v) <= topk for v in by_img.values()):
        return list(results)  # 打ち切り不要 → 原順序を保持
    kept = []
    for img_id in by_img:
        rows = by_img[img_id]
        if len(rows) > topk:
            rows = sorted(rows, key=lambda r: -float(r["score"]))[:topk]
        kept.extend(rows)
    return kept


def save_predictions(
    run_dir: str | os.PathLike,
    results: list,
    *,
    split: str,
    tag: str,
    epoch: int | None = None,
    best: bool = False,
    topk: int = EVAL_TOPK,
    compress: bool = True,
) -> Path:
    """COCO detection results を ``predictions/`` に保存してパスを返す。"""
    out_dir = predictions_dir(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / predictions_name(split, tag, epoch=epoch, best=best, compress=compress)
    payload = json.dumps(truncate_topk(results, topk), ensure_ascii=False)
    if compress:
        # mtime=0 で決定的な gzip にする（同一内容 → 同一バイト列 → sha256 比較が意味を持つ）。
        with gzip.GzipFile(filename="", mode="wb", fileobj=path.open("wb"), mtime=0) as f:
            f.write(payload.encode("utf-8"))
    else:
        path.write_text(payload, encoding="utf-8")
    return path


def load_predictions(path: str | os.PathLike) -> list:
    """``.json`` / ``.json.gz`` のどちらでも predictions を読む。"""
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def find_predictions(
    run_dir: str | os.PathLike, split: str, tag: str, *, epoch: int | None = None, best: bool = False
) -> Path | None:
    """gzip / 非 gzip のどちらで保存されていても predictions を見つける。"""
    d = predictions_dir(run_dir)
    for compress in (True, False):
        p = d / predictions_name(split, tag, epoch=epoch, best=best, compress=compress)
        if p.exists():
            return p
    return None


def sha256_of(path: str | os.PathLike) -> str:
    """ファイルの SHA-256（16進）。predictions の同一性検証に使う。"""
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def predictions_sha256(path: str | os.PathLike) -> str:
    """predictions の **中身** の SHA-256（圧縮形式に依存しない）。

    gzip の有無で値が変わらないよう、展開後の JSON テキストに対して取る。
    inj / ctrl の init 予測が完全一致することの証明に使う。
    """
    payload = json.dumps(load_predictions(path), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# ログ・証跡ファイル
# --------------------------------------------------------------------------- #
def save_epoch_log(run_dir: str | os.PathLike, payload: dict) -> Path:
    """epoch 別 val 指標（overall mAP + per-class AP + best_epoch）を ``logs/`` に残す。

    ckpt が失われても、コミット済みログだけで init 比較・絶対値検証を完遂できる
    状態にすることが目的。したがってこのファイルは git 追跡対象にする
    （``.gitignore`` に明示的な例外を置いてある）。
    """
    path = logs_dir(ensure_layout(run_dir)) / EPOCH_LOG_NAME
    _dump_json(path, payload)
    return path


def save_eval_meta(run_dir: str | os.PathLike, payload: dict) -> Path:
    """評価対象の image_id 一覧など、predictions を自己完結させるメタ情報を残す。

    これが無いと「どの画像集合で AP を出したか」が predictions から復元できず、
    後の再評価が元の数値と一致しない（例: smoke の ``--limit`` 付き評価）。
    """
    path = logs_dir(ensure_layout(run_dir)) / eval_meta_name(payload["split"])
    _dump_json(path, payload)
    return path


def load_eval_meta(run_dir: str | os.PathLike, split: str) -> dict | None:
    """評価メタを読む。旧名 ``eval_meta.json``（split 非分割）も拾う。"""
    d = logs_dir(run_dir)
    for name in (eval_meta_name(split), "eval_meta.json"):
        p = d / name
        if p.exists():
            meta = json.loads(p.read_text(encoding="utf-8"))
            if meta.get("split") == split:
                return meta
    return None


def write_evidence(
    run_dir: str | os.PathLike,
    *,
    config: dict | None = None,
    notes: str | None = None,
    server_name: str | None = None,
) -> None:
    """``command.sh`` / ``git_commit.txt`` / ``server.txt`` / ``config.yaml`` / ``notes.md`` を書く。

    ExperimentManager が工程側で自動化しているのと同じ証跡セットを、
    別 venv で動く検出側トレーナからも残せるようにした最小実装。
    """
    run_dir = ensure_layout(run_dir)
    ts = datetime.now().astimezone().isoformat(timespec="seconds")

    argv = " ".join(shlex.quote(a) for a in sys.argv)
    (run_dir / "command.sh").write_text(
        "#!/usr/bin/env bash\n"
        "# 自動生成: この run を起動したコマンドの記録\n"
        f"# 生成日時: {ts}\n"
        f"python {argv}\n",
        encoding="utf-8",
    )
    (run_dir / "git_commit.txt").write_text(_git_commit() + "\n", encoding="utf-8")
    (run_dir / "server.txt").write_text(
        (server_name or resolve_server_name()) + "\n", encoding="utf-8"
    )
    if config is not None:
        _write_config_yaml(run_dir / "config.yaml", config)
    if notes is not None:
        (run_dir / "notes.md").write_text(notes, encoding="utf-8")


def write_metrics(run_dir: str | os.PathLike, metrics: dict) -> Path:
    path = ensure_layout(run_dir) / "metrics.json"
    _dump_json(path, metrics)
    return path


def write_per_class_ap(run_dir: str | os.PathLike, per_class: dict) -> Path:
    path = ensure_layout(run_dir) / "per_class_ap.json"
    _dump_json(path, per_class)
    return path


# --------------------------------------------------------------------------- #
# ホスト名付きパス（マルチサーバ運用の所在明示）
# --------------------------------------------------------------------------- #
def resolve_server_name() -> str:
    """``egosurgery.utils.server_name.resolve_server_name`` と同じ規則（stdlib 版）。"""
    env = os.environ.get("SERVERNAME") or os.environ.get("EGOSURGERY_SERVER_NAME")
    if env:
        return str(env).strip().lower()
    return socket.gethostname().split(".")[0].lower()


def host_path(path: str | os.PathLike) -> str:
    """``<host>:<絶対パス>`` 形式。どのサーバー上の成果物かを一意に示す。"""
    return f"{resolve_server_name()}:{Path(path).resolve()}"


def artifact_paths(run_dir: str | os.PathLike) -> dict:
    """run の成果物パス（ホスト名付き絶対パス）をまとめて返す。

    Notion 実験Run台帳の Artifacts 記録用。存在しないサブディレクトリは含めない。
    """
    run_dir = Path(run_dir).resolve()
    out = {"run_dir": host_path(run_dir)}
    for sub in SUBDIRS:
        p = run_dir / sub
        if p.is_dir():
            out[sub] = host_path(p)
    return out


# --------------------------------------------------------------------------- #
# 内部ヘルパ
# --------------------------------------------------------------------------- #
def _dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _write_config_yaml(path: Path, config: dict) -> None:
    """設定を YAML で保存する。``yaml`` が無い環境では JSON で代替する（YAML 上位互換）。"""
    try:
        import yaml

        path.write_text(
            yaml.safe_dump(config, allow_unicode=True, sort_keys=True), encoding="utf-8"
        )
    except Exception:
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def verify_init_identity(run_a: Path, run_b: Path, split: str = "val") -> dict:
    """2 つの run（通常 inj / ctrl）の init 予測が完全一致するか検証する。

    注入層は zero-init=恒等なので、warm-start 直後（epoch=-1）の予測は phase context
    の有無によらず一致しなければならない。一致していれば「対照との差は注入の学習に
    のみ由来する」という比較の前提が実測で裏づけられる。
    """
    out = {"split": split, "runs": [str(run_a), str(run_b)]}
    paths = []
    for run, tag in ((run_a, "inj"), (run_b, "ctrl")):
        p = find_predictions(run, split, tag, epoch=-1)
        if p is None:
            out["status"] = "missing"
            out["missing"] = str(run)
            return out
        paths.append(p)
    digests = [predictions_sha256(p) for p in paths]
    out["sha256"] = dict(zip(("inj", "ctrl"), digests))
    out["identical"] = digests[0] == digests[1]
    out["status"] = "ok"
    for run, key in ((run_a, "inj"), (run_b, "ctrl")):
        log = logs_dir(run) / EPOCH_LOG_NAME
        if log.exists():
            out.setdefault("init_mAP", {})[key] = json.loads(log.read_text()).get("init", {}).get(
                "mAP"
            )
    return out


def _main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="run 成果物レイアウトのユーティリティ。")
    ap.add_argument("--verify-init-identity", nargs=2, metavar=("RUN_INJ", "RUN_CTRL"),
                    help="2 run の init 予測 SHA-256 が一致するか検証する")
    ap.add_argument("--split", default="val")
    ap.add_argument("--show", metavar="RUN", help="run の成果物パス（ホスト名付き）を表示")
    args = ap.parse_args()

    if args.show:
        print(json.dumps(artifact_paths(resolve_run_dir(args.show)), indent=2, ensure_ascii=False))
        return 0
    if args.verify_init_identity:
        a, b = (resolve_run_dir(x, work_dir=x if os.sep in x else None)
                for x in args.verify_init_identity)
        res = verify_init_identity(a, b, args.split)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res.get("identical") else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
