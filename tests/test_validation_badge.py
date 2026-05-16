"""Tests for ui/validation_badge — pure classification logic.

The Qt widget itself is exercised end-to-end via scripts/smoke_simulation_tab.py;
here we lock down the classification rules.
"""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.ui.validation_badge import (
    ANCHOR_V,
    FAIL_THRESHOLD,
    WARN_THRESHOLD,
    classify_deviation,
)


def test_anchor_value_is_ok() -> None:
    r = classify_deviation(ANCHOR_V)
    assert r.state == "ok"
    assert r.deviation_percent == pytest.approx(0.0, abs=1e-9)
    assert r.symbol == "✓"


def test_within_5pct_is_ok() -> None:
    # 1.60 · 1.04 = 1.664 → within 5 %
    assert classify_deviation(ANCHOR_V * 1.04).state == "ok"
    assert classify_deviation(ANCHOR_V * 0.96).state == "ok"


def test_between_5_and_15pct_is_warn() -> None:
    # 1.60 · 1.10 = 1.76 → 10 % off
    r = classify_deviation(ANCHOR_V * 1.10)
    assert r.state == "warn"
    assert r.symbol == "⚠"
    assert WARN_THRESHOLD * 100 < r.deviation_percent < FAIL_THRESHOLD * 100


def test_beyond_15pct_is_fail() -> None:
    # 1.60 · 1.20 = 1.92 → 20 % off
    r = classify_deviation(ANCHOR_V * 1.20)
    assert r.state == "fail"
    assert r.symbol == "✗"


def test_bernt_2016_band_endpoints_classify_as_warn() -> None:
    """Bernt's reported band 1.50–1.70 V → endpoints are exactly at ~6.25 %.

    That puts them in the 'warn' bucket (5–15 %), which is the honest
    answer — they sit at the edge of the cited literature spread.
    """
    assert classify_deviation(1.50).state == "warn"
    assert classify_deviation(1.70).state == "warn"


def test_classify_handles_nan() -> None:
    r = classify_deviation(float("nan"))
    assert r.state == "fail"


@pytest.mark.parametrize("v", [-1.0, 0.0])
def test_classify_handles_non_positive(v: float) -> None:
    r = classify_deviation(v)
    assert r.state == "fail"


def test_deviation_percent_matches_fraction() -> None:
    r = classify_deviation(1.80)
    assert r.deviation_percent == pytest.approx(r.deviation_fraction * 100.0)


def test_thresholds_are_consistent_with_ux_vision() -> None:
    """UX-VISION §6.4 declares 5 % / 15 % bucket boundaries — keep them."""
    assert WARN_THRESHOLD == 0.05
    assert FAIL_THRESHOLD == 0.15


def test_deviation_is_finite_for_realistic_voltages() -> None:
    for v in (1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2):
        r = classify_deviation(v)
        assert math.isfinite(r.deviation_fraction)
        assert r.deviation_fraction >= 0.0
