import json
import pandas as pd
from pipeline.common import ROOT, latest_snapshot

T = ROOT / "reports" / "tables"


def test_snapshot_manifest_has_provenance():
    snap = latest_snapshot()
    m = json.loads((snap / "manifest.json").read_text())
    for name, meta in m["files"].items():
        assert meta["source"].startswith("http") or meta["source"].startswith("pipeline"), name
        assert meta["fetched_at"] and meta["sha256"]


def test_intents_daily_has_no_gaps_in_2026():
    d = pd.read_csv(T / "intents_daily.csv", parse_dates=["date"])
    d = d[d.date >= "2026-01-01"]
    assert (d.date.diff().dropna() == pd.Timedelta(days=1)).all()
    assert (d.fees_usd <= d.volume_usd).all()
    # revenue is recognised when swept into the wallets, fees when charged, so compare per month not per day
    m = d.set_index("date").resample("MS")[["fees_usd", "revenue_usd"]].sum()
    assert (m.revenue_usd <= m.fees_usd).all()


def test_buyback_cumulative_is_monotonic():
    b = pd.read_csv(T / "buybacks_daily.csv")
    assert b.near_cum.is_monotonic_increasing


def test_total_supply_is_monotonic():
    n = pd.read_csv(T / "network_daily.csv", parse_dates=["date"])
    n = n[n.date >= "2026-01-01"]  # early-history rows in the NearBlocks series contain restatements
    assert n.total_supply.is_monotonic_increasing
