"""収束基準で学習の長さを決める規則の試験。契約 T-2026-09-19-stage1-detector-towers-r2。

確かめるのは 3 つである。

1. 規則が prereg §2 のとおりに動く（停滞で一度だけ低下、再停滞で打ち切り）
2. **既定は一周目と同じ**（引数を付けなければ低下も打ち切りも起きない）
3. **塔ごとの分岐が無い**（規則の呼び出しが 1 箇所だけ）

`main.py` は torch と accelerate を読み込むため import しない。**構文木で読む。**
規則そのもの（`util/convergence.py`）は依存が無いので直に import して動かす。
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RELDETR = REPO / "third_party" / "Relation-DETR"
MAIN_PY = RELDETR / "main.py"


def _load_convergence():
    spec = importlib.util.spec_from_file_location(
        "reldetr_convergence", RELDETR / "util" / "convergence.py"
    )
    module = importlib.util.module_from_spec(spec)
    # dataclass は生成時に sys.modules を引くため、実行の前に登録しておく。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


convergence = _load_convergence()
PlateauSchedule = convergence.PlateauSchedule
CONTINUE, DECAY, STOP = convergence.CONTINUE, convergence.DECAY, convergence.STOP

# 停滞する並び。epoch 4 で最良 0.56 に達し、その後は更新しない。
PLATEAU = [0.30, 0.40, 0.50, 0.55, 0.56] + [0.55] * 12


def _run(sequence, **kwargs) -> PlateauSchedule:
    schedule = PlateauSchedule(**kwargs)
    for epoch, ap in enumerate(sequence):
        if schedule.observe(epoch, ap) == STOP:
            break
    return schedule


def test_decays_once_then_stops():
    """停滞 4 で低下し、低下の後の停滞 4 で打ち切る（prereg §2）。"""
    schedule = _run(PLATEAU, patience=4)
    assert schedule.best_epoch == 4
    assert schedule.decayed_epoch == 8
    assert schedule.stopped_epoch == 12


def test_patience_changes_the_timing_of_the_decay():
    """**陽性対照。** 停滞の epoch 数を変えると低下の時期が変わる。

    判定が空振りでないことの確認（完了判定 a の四列目）。同じ並びを与えて
    patience だけを動かし、低下と打ち切りの epoch が動くことを見る。
    """
    fast = _run(PLATEAU, patience=2)
    slow = _run(PLATEAU, patience=4)
    assert fast.decayed_epoch == 6 and fast.stopped_epoch == 8
    assert slow.decayed_epoch == 8 and slow.stopped_epoch == 12
    assert fast.decayed_epoch != slow.decayed_epoch


def test_improvement_resets_the_counter():
    """最良を更新すれば停滞は解ける。低下も打ち切りも起きない。"""
    rising = [0.10 * (i + 1) for i in range(12)]
    schedule = _run(rising, patience=4)
    assert schedule.decayed_epoch is None
    assert schedule.stopped_epoch is None
    assert schedule.best_epoch == 11


def test_the_decay_happens_only_once():
    """低下は一度だけ。二度目の停滞は打ち切りであって低下ではない。"""
    schedule = PlateauSchedule(patience=2)
    actions = [
        schedule.observe(i, ap) for i, ap in enumerate([0.5, 0.4, 0.4, 0.4, 0.4])
    ]
    assert actions == [CONTINUE, CONTINUE, DECAY, CONTINUE, STOP]
    assert actions.count(DECAY) == 1


def test_the_best_is_not_rolled_back_by_the_decay():
    """低下の後に最良を下回る値が続いても、最良はさかのぼらない。"""
    schedule = _run([0.60, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50], patience=4)
    assert schedule.best == pytest.approx(0.60)
    assert schedule.best_epoch == 0


def test_patience_must_be_positive():
    with pytest.raises(ValueError):
        PlateauSchedule(patience=0)


# --------------------------------------------------------------------------- #
# main.py の経路
# --------------------------------------------------------------------------- #
def _main_tree() -> ast.Module:
    return ast.parse(MAIN_PY.read_text(encoding="utf-8"))


def _argument_defaults() -> dict[str, object]:
    """`parse_args` が足した引数の既定値を構文木から読む。"""
    defaults: dict[str, object] = {}
    for node in ast.walk(_main_tree()):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        name = getattr(node.args[0], "value", None)
        if not isinstance(name, str) or not name.startswith("--"):
            continue
        keywords = {kw.arg: kw.value for kw in node.keywords}
        if "action" in keywords:
            defaults[name] = False  # store_true の既定
        elif "default" in keywords:
            defaults[name] = ast.literal_eval(keywords["default"])
    return defaults


def test_the_default_is_the_first_round():
    """**既定で一周目が再現する。** 引数を付けなければ収束基準は立たない。

    既定が off なら `schedule is None` の経路を通り、`lr_scheduler.step()` が
    毎 epoch 呼ばれ、epoch 数は config の値（一周目は 12）のままになる。
    """
    defaults = _argument_defaults()
    assert defaults["--convergence-schedule"] is False
    assert defaults["--max-epochs"] is None
    assert defaults["--plateau-patience"] == 4
    assert defaults["--plateau-factor"] == 0.1


def test_the_first_round_scheduler_still_steps_when_disabled():
    """既定の経路では config の lr_scheduler を毎 epoch 進める。

    `lr_scheduler.step()` が `schedule is None` の枝の中にあることを構文木で見る。
    """
    guarded = []
    for node in ast.walk(_main_tree()):
        if not isinstance(node, ast.If):
            continue
        source = ast.unparse(node.test)
        if source != "schedule is None":
            continue
        guarded.extend(
            ast.unparse(child) for child in node.body if isinstance(child, ast.Expr)
        )
    assert "lr_scheduler.step()" in guarded


def test_both_towers_take_the_same_path():
    """**塔ごとの分岐が無い。** 規則の生成も呼び出しも 1 箇所だけである。

    塔の違いは config ファイル（COCO 重みを読むか否か）だけで、学習の長さを
    決める経路は共有される。完了判定 a が求める「別々の分岐を通っていないこと」。
    """
    tree = _main_tree()
    constructions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "PlateauSchedule"
    ]
    observations = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "observe"
    ]
    assert len(constructions) == 1
    assert len(observations) == 1
