import math
from models.breakeven import breakeven_volume, coverage


def test_breakeven_identity():
    bv, iss = breakeven_volume(total_supply=1.31e9, issuance_rate=0.025, price=4.0, fee_rate_bps=15, capture_rate=0.3)
    assert math.isclose(iss, 1.31e9 * 0.025 / 365 * 4.0)
    assert math.isclose(bv * 15 / 1e4 * 0.3, iss)


def test_coverage_is_one_at_breakeven():
    bv, _ = breakeven_volume(1.31e9, 0.016, 4.0, 15, 0.3)
    assert math.isclose(coverage(bv, 1.31e9, 0.016, 4.0, 15, 0.3), 1.0)


def test_lower_issuance_lowers_breakeven():
    a, _ = breakeven_volume(1.31e9, 0.025, 4.0, 15, 0.3)
    b, _ = breakeven_volume(1.31e9, 0.016, 4.0, 15, 0.3)
    assert b < a
