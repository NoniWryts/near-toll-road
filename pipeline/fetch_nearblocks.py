"""NearBlocks public API: daily network charts since 2020-07 and live stats. No key needed for these endpoints."""
import os
import pandas as pd
from .common import get_json, save

BASE = "https://api.nearblocks.io/v1"


def _headers():
    k = os.environ.get("NEARBLOCKS_API_KEY")
    return {"Authorization": f"Bearer {k}"} if k else None


def run(snap):
    charts = get_json(f"{BASE}/charts", headers=_headers())["charts"]
    df = pd.DataFrame(charts)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    num = [c for c in df.columns if c not in ("date",)]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # yocto -> NEAR for supply and volume columns
    for c in ("total_supply", "circulating_supply", "txn_volume", "txn_fee", "gas_fee"):
        if c in df:
            df[c] = df[c] / 1e24
    save(snap, "nearblocks_charts", df, f"{BASE}/charts",
         "daily series; supply, txn_volume, txn_fee converted from yocto to NEAR")
    stats = get_json(f"{BASE}/stats", headers=_headers())["stats"][0]
    save(snap, "nearblocks_stats", stats, f"{BASE}/stats", "live stats incl. total_supply (yocto), near_price, nodes_online")
