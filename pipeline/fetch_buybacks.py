"""Every receipt touching buybacks.multisignature.near, via NearBlocks (cursor-paginated). This is the primary
record of NEAR purchased with Intents fees: automated TRANSFER receipts from intents.near."""
import os, time
import pandas as pd
from .common import get_json, save, yocto

BASE = "https://api.nearblocks.io/v1/account"
WALLET = "buybacks.multisignature.near"


def _headers():
    k = os.environ.get("NEARBLOCKS_API_KEY")
    return {"Authorization": f"Bearer {k}"} if k else None


def fetch_receipts(account: str, max_pages: int = 400):
    rows, cursor = [], None
    for _ in range(max_pages):
        params = {"per_page": 250}
        if cursor:
            params["cursor"] = cursor
        d = get_json(f"{BASE}/{account}/receipts", params, headers=_headers())
        txns = d.get("txns", [])
        for t in txns:
            act = (t.get("actions") or [{}])[0]
            rows.append({
                "receipt_id": t["receipt_id"], "tx_hash": t.get("transaction_hash"),
                "block_height": (t.get("receipt_block") or {}).get("block_height"),
                "block_timestamp_ns": int((t.get("receipt_block") or {}).get("block_timestamp") or 0),
                "predecessor": t.get("predecessor_account_id"), "receiver": t.get("receiver_account_id"),
                "action": act.get("action"), "method": act.get("method"),
                "deposit_near": yocto(act.get("deposit") or 0), "status": (t.get("receipt_outcome") or {}).get("status"),
            })
        cursor = d.get("cursor")
        if not txns or not cursor:
            break
        time.sleep(0.35)  # stay under the keyless rate limit
    df = pd.DataFrame(rows).drop_duplicates("receipt_id")
    df["date"] = pd.to_datetime(df["block_timestamp_ns"], unit="ns").dt.normalize()
    return df


def run(snap):
    df = fetch_receipts(WALLET)
    n_in = int(((df.receiver == WALLET) & (df.predecessor == "intents.near") & (df.action == "TRANSFER")).sum())
    save(snap, "buyback_receipts", df, f"{BASE}/{WALLET}/receipts",
         f"all receipts; {n_in} are TRANSFER from intents.near (the buyback sweeps)")
