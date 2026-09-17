"""Validate selection rules without evaluating any test predictions."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from select_stage1_ptower import select  # noqa: E402


def row(candidate, jaccard, seconds, layers=6, accuracy=0.8):
    return {"candidate": candidate, "layers": layers, "mean_jaccard": jaccard,
            "mean_accuracy": accuracy, "fold_A_pstd": 0.03, "mean_seconds": seconds}


def test_simple_candidate_within_twenty_percent_and_no_test_dependency():
    rows = [row("B", 0.51, 10), row("A", 0.50, 12)]
    chosen, _ = select(rows)
    assert chosen["candidate"] == "A"
    enriched = [dict(r, test_jaccard=100 if r["candidate"] == "B" else -100) for r in rows]
    assert select(enriched)[0]["candidate"] == "A"
    rows[1]["mean_seconds"] = 12.01
    assert select(rows)[0]["candidate"] == "B"


def test_shorter_receptive_field_and_direction_gate():
    rows = [row("A", 0.51, 10, layers=8), row("A", 0.50, 10, layers=6)]
    assert select(rows)[0]["layers"] == 6
    rows[0]["mean_accuracy"] = 0.7
    with pytest.raises(ValueError, match="directions disagree"):
        select(rows)


def test_primary_winner_outside_seed_spread():
    assert select([row("B", 0.7, 100), row("A", 0.5, 1)])[0]["candidate"] == "B"


def test_same_candidate_and_receptive_field_prefers_steadier_seeds():
    # The 2026-09-17 amendment: a tie the A>C>B and shorter-RF rules cannot break.
    rows = [row("C", 0.51, 10, layers=8), row("C", 0.50, 10, layers=8)]
    rows[0]["fold_A_pstd"], rows[1]["fold_A_pstd"] = 0.09, 0.01
    chosen, reason = select(rows)
    assert chosen["mean_jaccard"] == 0.50 and "smaller fold A seed pstd" in reason
    # Both directions: the runner-up does not win when it is the noisier of the two.
    rows[0]["fold_A_pstd"], rows[1]["fold_A_pstd"] = 0.09, 0.095
    assert select(rows)[0]["mean_jaccard"] == 0.51
