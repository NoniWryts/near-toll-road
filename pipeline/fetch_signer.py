"""Chain Signatures usage: a time-boxed sample of recent receipts to v1.signer (the MPC contract), via NearBlocks.
v1.signer has ~26M lifetime receipts, so we sample the most recent pages and extrapolate a daily rate; the sample
window and size are recorded so the extrapolation is reproducible and visibly approximate."""
import os, time
import pandas as pd
from .common import get_json, save, yocto

BASE = "https://api.nearblocks.io/v1/account/v1.signer"
PAGES = int(os.environ.get("SIGNER_PAGES", "40"))


def _headers():
    k = os.environ.get("NEARBLOCKS_API_KEY")
    return {"Authorization": f"Bearer {k}"} if k else None


def run(snap):
    total = get_json(f"{BASE}/txns/count", headers=_headers())["txns"][0]
    rows, cursor = [], None
    for _ in range(PAGES):
        params = {"per_page": 250}
        if cursor:
            params["cursor"] = cursor
        d = get_json(f"{BASE}/txns", params, headers=_headers())
        t = d.get("txns", [])
        for x in t:
            act = (x.get("actions") or [{}])[0]
            rows.append({"receipt_id": x["receipt_id"], "block_timestamp_ns": int(x["block_timestamp"]),
                         "predecessor": x.get("predecessor_account_id"), "method": act.get("method"),
                         "gas_burnt": (x.get("receipt_outcome") or {}).get("gas_burnt"), "status": (x.get("receipt_outcome") or {}).get("status")})
        cursor = d.get("cursor")
        if not t or not cursor:
            break
        time.sleep(1.0)
    df = pd.DataFrame(rows).drop_duplicates("receipt_id")
    df["ts"] = pd.to_datetime(df.block_timestamp_ns, unit="ns")
    span_days = (df.ts.max() - df.ts.min()).total_seconds() / 86400
    save(snap, "signer_sample", df, f"{BASE}/txns",
         f"most recent {len(df)} receipts spanning {span_days*24:.1f} hours; lifetime receipt count {total['count']}",
         {"lifetime_receipts": int(total["count"]), "sample_span_days": span_days})
