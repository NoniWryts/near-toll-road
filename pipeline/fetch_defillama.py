"""DefiLlama: NEAR Intents daily volume, gross fees, captured revenue; chain-level fee comparables."""
import pandas as pd
from .common import get_json, save

API = "https://api.llama.fi"


def _series(d, col):
    return pd.DataFrame(d.get("totalDataChart", []), columns=["ts", col])


def run(snap):
    fees = get_json(f"{API}/summary/fees/near-intents", {"dataType": "dailyFees"})
    rev = get_json(f"{API}/summary/fees/near-intents", {"dataType": "dailyRevenue"})
    hold = get_json(f"{API}/summary/fees/near-intents", {"dataType": "dailyHoldersRevenue"})
    vol = get_json(f"{API}/summary/dexs/near-intents")
    df = _series(vol, "volume_usd").merge(_series(fees, "fees_usd"), on="ts", how="outer") \
        .merge(_series(rev, "revenue_usd"), on="ts", how="outer").merge(_series(hold, "holders_revenue_usd"), on="ts", how="outer")
    df["date"] = pd.to_datetime(df["ts"], unit="s")
    df = df.sort_values("date").drop(columns="ts")[["date", "volume_usd", "fees_usd", "revenue_usd", "holders_revenue_usd"]]
    save(snap, "llama_intents_daily", df, f"{API}/summary/{{dexs,fees}}/near-intents",
         "fees = protocol + affiliate fee on swaps; revenue = NEAR swept into revenue wallets (DefiLlama methodology)",
         {"methodology": fees.get("methodology"), "methodologyURL": fees.get("methodologyURL"),
          "totals_fees": {k: fees.get(k) for k in ("total24h", "total7d", "total30d", "totalAllTime")},
          "totals_revenue": {k: rev.get(k) for k in ("total24h", "total7d", "total30d", "totalAllTime")},
          "totals_volume": {k: vol.get(k) for k in ("total24h", "total7d", "total30d", "totalAllTime")}})
    comps = {}
    for slug in ("near", "ethereum", "solana"):
        f = get_json(f"{API}/summary/fees/{slug}", {"dataType": "dailyFees"})
        r = get_json(f"{API}/summary/fees/{slug}", {"dataType": "dailyRevenue"})
        comps[slug] = {"fees_30d": f.get("total30d"), "fees_7d": f.get("total7d"), "fees_all": f.get("totalAllTime"),
                       "revenue_30d": r.get("total30d"), "revenue_7d": r.get("total7d"), "revenue_all": r.get("totalAllTime"),
                       "methodology": f.get("methodology")}
    save(snap, "llama_chain_fees", comps, f"{API}/summary/fees/{{near,ethereum,solana}}",
         "chain base-layer fees and revenue (gas), same DefiLlama definitions across the three")
