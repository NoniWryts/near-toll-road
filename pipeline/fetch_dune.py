"""Optional: official NEAR Intents Dune queries (dune.com/near/near-intents). Needs DUNE_API_KEY.
Without a key this step is skipped and recorded as skipped, nothing is fabricated."""
import os
import pandas as pd
from .common import get_json, save

QUERIES = {"intents_cumulative_volume": 5179085, "intents_tvl": 7586891, "intents_fees": 6162606, "intents_daily_by_asset": 5175131}


def run(snap):
    key = os.environ.get("DUNE_API_KEY")
    if not key:
        save(snap, "dune_skipped", {"reason": "DUNE_API_KEY not set", "queries": QUERIES}, "https://dune.com/near/near-intents")
        return
    for name, qid in QUERIES.items():
        d = get_json(f"https://api.dune.com/api/v1/query/{qid}/results", {"limit": 5000}, headers={"X-Dune-API-Key": key})
        rows = d.get("result", {}).get("rows", [])
        save(snap, f"dune_{name}", pd.DataFrame(rows), f"https://dune.com/queries/{qid}", "latest stored result of the official query")
