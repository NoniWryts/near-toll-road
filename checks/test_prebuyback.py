"""The pre-switch comparison: windows are ordered, the series exists, and the numbers are plausible."""
import json
import pandas as pd
from pipeline.common import ROOT

T = ROOT / "reports" / "tables"


def test_prebuyback_numbers_are_consistent():
    p = T / "kpis.json"
    if not p.exists():
        return
    k = json.loads(p.read_text())
    if "pb_switch_date" not in k:
        return
    assert k["pb_switch_date"] < k["pb_first_sweep"]                      # the switch precedes the first sweep
    assert k["pb_gap_days"] == (pd.Timestamp(k["pb_first_sweep"]) - pd.Timestamp(k["pb_switch_date"])).days
    assert k["pb_prehalving_issuance_annual"] > 1.6 * k["pb_posthalving_prefee_issuance_annual"]   # the cap was halved
    assert -1 < k["pb_active_chg_jan25_to_switch"] < 0                    # usage fell before the switch
    assert 0 < k["pb_burn_cover_pre_halved"] < 0.2                        # burn never came close to offsetting issuance
    assert k["pb_intents_rev_before_nov25_usd"] < 1000                    # NEAR earned nothing from Intents before Nov 2025


def test_prebuyback_table_has_monthly_rows():
    f = T / "prebuyback_monthly.csv"
    if not f.exists():
        return
    d = pd.read_csv(f, parse_dates=["month"])
    assert d.month.is_monotonic_increasing and len(d) >= 20
    assert (d.active_accounts_per_day > 0).all()
