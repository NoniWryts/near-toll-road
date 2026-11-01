"""CoinGecko free API: 365 days of daily price and market cap for NEAR, ETH, SOL."""
import time
import pandas as pd
from .common import get_json, save

API = "https://api.coingecko.com/api/v3/coins"


def run(snap):
    frames = []
    for cid in ("near", "ethereum", "solana"):
        d = get_json(f"{API}/{cid}/market_chart", {"vs_currency": "usd", "days": 365, "interval": "daily"})
        p = pd.DataFrame(d["prices"], columns=["ts", "price_usd"])
        m = pd.DataFrame(d["market_caps"], columns=["ts", "market_cap_usd"])
        v = pd.DataFrame(d["total_volumes"], columns=["ts", "volume_usd"])
        df = p.merge(m, on="ts").merge(v, on="ts")
        df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.normalize()
        df["coin"] = cid
        frames.append(df.drop(columns="ts"))
        time.sleep(2)
    out = pd.concat(frames).drop_duplicates(["coin", "date"], keep="last")
    save(snap, "coingecko_daily", out, f"{API}/{{near,ethereum,solana}}/market_chart", "daily close; last row is intraday")
