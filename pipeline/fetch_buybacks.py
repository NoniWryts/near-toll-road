"""Every receipt touching buybacks.multisignature.near, via NearBlocks (cursor-paginated). This is the primary
record of NEAR purchased with Intents fees: automated TRANSFER receipts from intents.near."""
import os, time
import pandas as pd
from .common import get_json, post_json, save, yocto

BASE = "https://api.nearblocks.io/v1/account"
WALLET = "buybacks.multisignature.near"


def _headers():
    k = os.environ.get("NEARBLOCKS_API_KEY")
    return {"Authorization": f"Bearer {k}"} if k else None


def fetch_receipts(account: str, max_pages: int = 400, known: set | None = None, per_page: int = 250):
    rows, cursor = [], None
    for _ in range(max_pages):
        params = {"per_page": per_page}
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
        if known is not None and txns and all(t["receipt_id"] in known for t in txns):
            break  # reached receipts already held from an earlier snapshot
        if not txns or not cursor:
            break
        time.sleep(0.35)  # stay under the keyless rate limit
    df = pd.DataFrame(rows).drop_duplicates("receipt_id")
    df["date"] = pd.to_datetime(df["block_timestamp_ns"], unit="ns").dt.normalize()
    return df


FASTNEAR_TX = "https://tx.main.fastnear.com"


def fetch_sweeps_fastnear(since_ns: int) -> pd.DataFrame:
    """Sweeps newer than `since_ns` read from FastNear's transaction index: each buyback is an `intents.near`
    native_withdraw event whose receiver is the wallet; the amount is in the event log (yoctoNEAR)."""
    import json
    hashes, token = {}, None
    while True:
        body = {"account_id": WALLET, "limit": 200, "is_descending": True}
        if token:
            body["resume_token"] = token
        d = post_json(f"{FASTNEAR_TX}/v0/account", body)
        rows = d.get("account_txs", [])
        for r in rows:
            if int(r["tx_block_timestamp"]) > since_ns:
                hashes[r["transaction_hash"]] = int(r["tx_block_timestamp"])
        token = d.get("resume_token")
        if not rows or not token or min(int(r["tx_block_timestamp"]) for r in rows) <= since_ns:
            break
        time.sleep(0.2)
    out, hs = [], list(hashes)
    for i in range(0, len(hs), 20):
        d = post_json(f"{FASTNEAR_TX}/v0/transactions", {"tx_hashes": hs[i:i + 20]})
        for t in d.get("transactions", []):
            h = t["transaction"]["hash"] if "hash" in t["transaction"] else None
            for r in t.get("receipts", []):
                eo = r["execution_outcome"]
                for lg in eo["outcome"].get("logs", []):
                    if not lg.startswith("EVENT_JSON:") or "native_withdraw" not in lg:
                        continue
                    ev = json.loads(lg[len("EVENT_JSON:"):])
                    for x in ev.get("data", []):
                        if x.get("receiver_id") == WALLET:
                            out.append({"receipt_id": f"fastnear:{eo['id']}", "tx_hash": h or t["transaction"].get("hash"),
                                        "block_height": eo["block_height"], "block_timestamp_ns": int(eo["block_timestamp"]),
                                        "predecessor": "intents.near", "receiver": WALLET, "action": "TRANSFER", "method": None,
                                        "deposit_near": yocto(x["amount"]), "status": True})
        time.sleep(0.2)
    return pd.DataFrame(out)


def run(snap):
    """Full history when run on its own. If NearBlocks refuses the full pull (rate limit), sweeps newer than the latest earlier
    snapshot's copy are read from FastNear and appended: receipts are immutable, so old rows never change."""
    try:
        if os.environ.get("BUYBACKS_INCREMENTAL"):
            raise RuntimeError("incremental mode requested")
        df = fetch_receipts(WALLET)
    except RuntimeError:
        from .common import SNAPSHOTS, load_df
        prev = [d for d in sorted(SNAPSHOTS.glob("20*")) if d != snap and (d / "buyback_receipts.parquet").exists()]
        if not prev:
            raise
        old = load_df(prev[-1], "buyback_receipts")
        new = fetch_sweeps_fastnear(int(old.block_timestamp_ns.max()))
        df = pd.concat([new, old]).drop_duplicates("receipt_id")
        df["date"] = pd.to_datetime(df["block_timestamp_ns"], unit="ns").dt.normalize()
    n_in = int(((df.receiver == WALLET) & (df.predecessor == "intents.near") & (df.action == "TRANSFER")).sum())
    save(snap, "buyback_receipts", df, f"{BASE}/{WALLET}/receipts",
         f"all receipts; {n_in} are TRANSFER from intents.near (the buyback sweeps)")
