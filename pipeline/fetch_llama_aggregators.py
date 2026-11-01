"""DefiLlama cross-protocol comparison: every swap aggregator and bridge aggregator it tracks, plus the whole
DEX-volume overview, all with DefiLlama's one volume definition. NEAR Intents (slug near-intents) is filed by DefiLlama
under the DEX overview with category "Bridge", not in the aggregator lists, so analysis ranks it against each list."""
import pandas as pd
from .common import get_json, save

API = "https://api.llama.fi"
KEEP = ["name", "displayName", "category", "total24h", "total7d", "total30d", "total30DaysAgo", "total1y", "totalAllTime",
        "change_1m", "change_30dover30d", "chains", "methodologyURL"]


def run(snap):
    frames = []
    for cat, ep in (("swap_aggregator", "aggregators"), ("bridge_aggregator", "bridge-aggregators"), ("dex_overview", "dexs")):
        j = get_json(f"{API}/overview/{ep}", {"excludeTotalDataChart": "true", "excludeTotalDataChartBreakdown": "true"})
        d = pd.DataFrame(j["protocols"])
        d = d.reindex(columns=KEEP)
        d["llama_category"] = cat
        d["n_chains"] = d.chains.apply(lambda c: len(c) if isinstance(c, list) else 0)
        d["chains"] = d.chains.apply(lambda c: ",".join(c) if isinstance(c, list) else "")
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["rank_30d"] = df.groupby("llama_category")["total30d"].rank(ascending=False, method="min")
    save(snap, "llama_aggregators", df, f"{API}/overview/{{aggregators,bridge-aggregators}}",
         "DefiLlama aggregator, bridge-aggregator and DEX-overview volume rankings; near-intents sits in dex_overview, category Bridge",
         {"n_swap_aggregators": int((df.llama_category == "swap_aggregator").sum()),
          "n_bridge_aggregators": int((df.llama_category == "bridge_aggregator").sum()),
          "n_dex_overview": int((df.llama_category == "dex_overview").sum())})
