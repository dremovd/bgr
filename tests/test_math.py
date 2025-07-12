import csv
import math
from pathlib import Path
import pytest

import generate_page as gp


def test_wilson_manual_example():
    n, S = 100, 800
    z = gp.DEFAULT_Z
    R = S / n
    p = (R - 1) / 9.0
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    expected = 1 + 9 * (centre - adj) / denom
    assert gp.wilson_lower_bound_10pt(n, S, z) == pytest.approx(expected)


def test_wilson_zero_votes():
    assert gp.wilson_lower_bound_10pt(0, 0) == 0.0


def test_weighted_score_matches_manual():
    csv_path = Path("2025-06-18T11-00-01.csv")
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)  # first game in file
    n = int(row["Users rated"])
    avg = float(row["Average"])
    S = n * avg
    z = gp.DEFAULT_Z
    expected = gp.wilson_lower_bound_10pt(
        n + gp.PRIOR_VOTES,
        S + gp.PRIOR_VOTES * gp.PRIOR_RATING,
        z,
    )
    assert gp.weighted_score(n, S) == pytest.approx(expected)


def test_status_labels():
    assert gp.status_for_rank(10) == ("🔥", "Bestseller")
    assert gp.status_for_rank(500) == ("🔎", "Rare find")
    assert gp.status_for_rank(2000) == ("💎", "Hidden gem")
