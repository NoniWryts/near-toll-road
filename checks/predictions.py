"""Settle the pre-registered predictions in thesis/PREDICTIONS.md against the latest snapshot.
Writes reports/tables/predictions.csv. Status is PENDING before the settle date, then HIT or MISS. Thresholds here
must match PREDICTIONS.md; checks/test_predictions.py fails if the frozen file's hash changes."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from pipeline.common import ROOT, latest_snapshot, load_json, utcnow

T = ROOT / "reports" / "tables"
SETTLE = pd.Timestamp("2027-03-31")


def window(df, col, end, days):
    return df[(df.date > end - pd.Timedelta(days=days)) & (df.date <= end)][col].sum()


def build(snap: Path) -> pd.DataFrame:
    k = json.loads((T / "kpis.json").read_text())
    i = pd.read_csv(T / "intents_daily.csv", parse_dates=["date"])
    b = pd.read_csv(T / "buybacks_daily.csv", parse_dates=["date"])
    n = pd.read_csv(T / "network_daily.csv", parse_dates=["date"])
    pc = load_json(snap, "rpc_protocol_config")
    end = min(i.date.max(), b.date.max(), n.date.max(), SETTLE)
    settled = end >= SETTLE
    cap90 = window(i, "revenue_usd", end, 90) / window(i, "fees_usd", end, 90)
    cov90 = window(b, "near_bought", end, 90) / window(n, "issued_near", end, 90)
    realised = window(n, "issued_near", end, 30) * 365 / 30 / float(n[n.date <= end].total_supply.iloc[-1])
    cap_changed = list(pc["max_inflation_rate"]) != [1, 40]
    rows = [
        ("P1", "HSP-029 live in the protocol", f"max_inflation_rate {pc['max_inflation_rate']} (protocol {pc['protocol_version']}); realised issuance {realised:.2%}",
         cap_changed or realised < 0.024, "cap != [1,40] or realised < 2.40%"),
        ("P2", "Trailing-90d capture rate", f"{cap90:.1%}", cap90 >= 0.30, ">= 30.0%"),
        ("P3", "90-day buyback coverage of issuance", f"{cov90:.1%}", cov90 >= 0.15, ">= 15.0%"),
    ]
    df = pd.DataFrame([{"id": a, "call": c, "observed": o, "threshold": t, "data_through": str(end.date()), "settles": str(SETTLE.date()),
                        "status": ("HIT" if met else "MISS") if settled else ("PENDING (on track)" if met else "PENDING"),
                        "snapshot": snap.name, "checked_at": utcnow()} for a, c, o, met, t in rows])
    df.to_csv(T / "predictions.csv", index=False)
    return df


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--snapshot", default=None); a = ap.parse_args()
    snap = Path(a.snapshot) if a.snapshot else latest_snapshot()
    print(build(snap)[["id", "observed", "threshold", "status"]].to_string(index=False))


if __name__ == "__main__":
    main()
