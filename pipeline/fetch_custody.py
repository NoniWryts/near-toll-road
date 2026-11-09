"""Custody reconciliation, one token on one chain: USDT on Tron.

Question: how much of the money NEAR Intents pays out is backed by a public withdrawal on NEAR, and how much is not?
A confidential swap runs inside the private shard, but its payout still lands on the destination chain as an ordinary
transfer (docs.intents.aurora.dev/confidential-intents: "the destination transaction, the destination asset and
amount, and the recipient remain public"). So we read both sides in full for a fixed window:

  NEAR side   every receipt on the bridged-USDT token contract `tron-d28a...omft.near` (NearBlocks, keyless).
              A public withdrawal is an `ft_transfer` from intents.near with memo `WITHDRAW_TO:<tron address>`.
  Tron side   every USDT (TRC-20) transfer out of the bridge's Tron hot wallet (TronGrid, keyless).
              The wallet was identified by looking up the Tron transfers behind sampled withdrawals.

analysis/custody.py then matches them. Both sides are complete for the window, not sampled.

Settings: CUSTODY_START / CUSTODY_END (UTC dates, inclusive, default 2026-10-24 / 2026-10-30)."""
from __future__ import annotations
import json, os, time
import pandas as pd
from .common import get_json, save, snapshot_dir

TOKEN = "tron-d28a265909efecdcee7c5028585214ea0b96f015.omft.near"
USDT_TRC20 = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
HOT_WALLETS = os.environ.get("CUSTODY_TRON_WALLETS", "TX5XiRXdyz7sdFwF5mnhT1QoGCpbkncpke").split(",")
START = pd.Timestamp(os.environ.get("CUSTODY_START", "2026-10-24"), tz="UTC")
END = pd.Timestamp(os.environ.get("CUSTODY_END", "2026-10-30"), tz="UTC") + pd.Timedelta(days=1)
NB = f"https://api.nearblocks.io/v1/account/{TOKEN}/receipts"
TG = "https://api.trongrid.io/v1/accounts/{}/transactions/trc20"


def _nb(cursor=None, per_page=250):
    p = {"per_page": per_page}
    if cursor:
        p["cursor"] = cursor
    time.sleep(1.5)
    return get_json(NB, p, retries=6)


def _rts(r):
    return pd.Timestamp(int(r["receipt_block"]["block_timestamp"]), unit="ns", tz="UTC")


def _find_cursor(target: pd.Timestamp) -> int:
    """Receipt ids grow with time; binary-search the id whose page starts just after `target` (newest first)."""
    top = _nb(None, 1)
    hi = int(top["txns"][0]["id"]) + 1
    lo = hi // 2
    for _ in range(30):
        if hi - lo < 20_000:
            break
        mid = (lo + hi) // 2
        t = _nb(mid, 1)["txns"]
        if not t or _rts(t[0]) < target:
            lo = mid
        else:
            hi = mid
    return hi


def near_side() -> pd.DataFrame:
    cur = _find_cursor(END + pd.Timedelta(hours=2))
    rows = []
    while True:
        d = _nb(cur)
        tx = d.get("txns") or []
        for r in tx:
            ts = _rts(r)
            for a in r.get("actions") or []:
                args = {}
                try:
                    args = json.loads(a.get("args") or "{}")
                except Exception:  # noqa: BLE001
                    pass
                rows.append({"receipt_id": r["receipt_id"], "tx_hash": r["transaction_hash"], "ts": ts,
                             "predecessor": r["predecessor_account_id"], "receiver": r["receiver_account_id"],
                             "method": a.get("method"), "amount": str(args.get("amount", "")),
                             "memo": str(args.get("memo") or ""), "receiver_id": str(args.get("receiver_id") or ""),
                             "ok": bool((r.get("receipt_outcome") or {}).get("status"))})
        cur = d.get("cursor")
        if not tx or not cur or _rts(tx[-1]) < START - pd.Timedelta(hours=2):
            break
    return pd.DataFrame(rows)


def tron_side() -> pd.DataFrame:
    rows = []
    for w in HOT_WALLETS:
        params = {"only_from": "true", "contract_address": USDT_TRC20, "limit": 200,
                  "min_timestamp": int((START - pd.Timedelta(hours=2)).timestamp() * 1000),
                  "max_timestamp": int((END + pd.Timedelta(hours=4)).timestamp() * 1000)}
        while True:
            d = get_json(TG.format(w), params, retries=6)
            for t in d.get("data") or []:
                rows.append({"wallet": w, "tron_tx": t["transaction_id"], "from": t["from"], "to": t["to"],
                             "value": str(t["value"]), "ts": pd.Timestamp(int(t["block_timestamp"]), unit="ms", tz="UTC")})
            fp = (d.get("meta") or {}).get("fingerprint")
            if not fp:
                break
            params["fingerprint"] = fp
            time.sleep(0.4)
    return pd.DataFrame(rows)


def main():
    snap = snapshot_dir(os.environ.get("SNAPSHOT_DATE", "2026-11-01"))
    n = near_side()
    save(snap, "custody_near_receipts", n, NB,
         f"every receipt on {TOKEN}, {START.date()} to {(END - pd.Timedelta(days=1)).date()} (+2h margins)")
    t = tron_side()
    save(snap, "custody_tron_outflows", t, TG.format(",".join(HOT_WALLETS)),
         f"every USDT transfer out of {HOT_WALLETS}, same window (+2h/+4h margins)")
    print(f"near receipts {len(n)}, tron outflows {len(t)}")


if __name__ == "__main__":
    main()
