"""Custody reconciliation: the matcher is one-to-one and the shares add up."""
import json
import pandas as pd
from analysis.custody import _match
from pipeline.common import ROOT

T = ROOT / "reports" / "tables"
ts = lambda s: pd.Timestamp(s, tz="UTC")


def test_matcher_pairs_fee_and_window_and_is_one_to_one():
    near = pd.DataFrame({"dest": ["TA", "TA", "TB", "TC"], "amt": [100.0, 100.0, 50.0, 10.0],
                         "ts": [ts("2026-10-30 10:00"), ts("2026-10-30 10:05"), ts("2026-10-30 10:00"), ts("2026-10-30 10:00")]})
    tron = pd.DataFrame({"to": ["TA", "TA", "TA", "TB", "TC"], "amt": [99.13, 99.13, 99.13, 50.5, 9.0],
                         "ts": [ts("2026-10-30 10:00:15"), ts("2026-10-30 10:05:10"), ts("2026-10-30 10:06"),
                                ts("2026-10-30 10:00:20"), ts("2026-10-30 16:00")]})
    m = _match(tron, near, pd.Timedelta(minutes=2), pd.Timedelta(hours=3))
    assert sorted(m.t) == [0, 1]                 # third TA payout has no withdrawal left: unmatched
    assert m.t.is_unique and m.n.is_unique
    assert 3 not in set(m.t)                      # paid more than was withdrawn: never a match
    assert 4 not in set(m.t)                      # six hours late: outside the first-pass window
    m2 = _match(tron.loc[[4]], near.loc[[3]], pd.Timedelta(minutes=2), pd.Timedelta(hours=24))
    assert list(m2.t) == [4]                      # the late pass picks it up


def test_custody_shares_add_up():
    p = T / "kpis.json"
    if not p.exists():
        return
    k = json.loads(p.read_text())
    if "cust_payouts_n" not in k:
        return
    assert k["cust_matched_n"] + k["cust_late_n"] + k["cust_nopublic_n"] == k["cust_payouts_n"]
    assert abs(k["cust_matched_usd"] + k["cust_late_usd"] + k["cust_nopublic_usd"] - k["cust_payouts_usd"]) < 1e-3
    assert abs(k["cust_public_share"] + k["cust_nopublic_share"] - 1) < 1e-9
    assert 0 < k["cust_fee_median"] < 5
