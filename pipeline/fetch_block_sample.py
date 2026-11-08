"""Base-chain activity mix: a seeded random sample of whole NEAR blocks from neardata.xyz (FastNear's keyless block
archive), counted by transaction receiver and signer. Answers "which contracts make up daily transactions" and,
by comparing a window before the April 2026 step-down with one after it, "what disappeared".

Settings: BLOCK_WINDOWS (default "2026-03-01:2026-03-31,2026-10-01:2026-10-31"), BLOCKS_PER_WINDOW (default 150),
BLOCK_SEED (default 20261108). Shares from ~150 random blocks per window are estimates; the sample size is recorded."""
from __future__ import annotations
import os, random, time
import pandas as pd
from .common import get_json, save

BASE = "https://mainnet.neardata.xyz/v0/block"
WINDOWS = os.environ.get("BLOCK_WINDOWS", "2026-03-01:2026-03-31,2026-10-01:2026-10-31")
N = int(os.environ.get("BLOCKS_PER_WINDOW", "150"))
SEED = int(os.environ.get("BLOCK_SEED", "20261108"))


def _block(h):
    for k in range(6):  # skipped heights return null; step forward
        b = get_json(f"{BASE}/{h + k}")
        if b:
            return b
    return None


def _ts(b):
    return pd.Timestamp(int(b["block"]["header"]["timestamp_nanosec"]), unit="ns", tz="UTC")


def _height_at(t: pd.Timestamp, lo: int, hi: int) -> int:
    while hi - lo > 200:
        mid = (lo + hi) // 2
        b = _block(mid)
        if b is None or _ts(b) < t:
            lo = mid
        else:
            hi = mid
        time.sleep(0.1)
    return hi


def run(snap):
    last = get_json("https://mainnet.neardata.xyz/v0/last_block/final")
    top = int(last["block"]["header"]["height"])
    rng = random.Random(SEED)
    rows, blocks = [], []
    for w in WINDOWS.split(","):
        a, b = (pd.Timestamp(x, tz="UTC") for x in w.split(":"))
        b = b + pd.Timedelta(days=1)
        h0 = _height_at(a, top - 60_000_000, top)
        h1 = _height_at(b, h0, top)
        for h in sorted(rng.randrange(h0, h1) for _ in range(N)):
            blk = _block(h)
            if blk is None:
                continue
            ts = _ts(blk)
            n_tx = 0
            for sh in blk["shards"]:
                ch = sh.get("chunk") or {}
                for tx in ch.get("transactions", []) or []:
                    t = tx.get("transaction", tx)
                    rows.append({"window": w, "height": h, "ts": ts, "receiver": t.get("receiver_id"), "signer": t.get("signer_id"),
                                 "method": next((x.get("FunctionCall", {}).get("method_name") for x in t.get("actions", []) if isinstance(x, dict) and "FunctionCall" in x), None)})
                    n_tx += 1
            blocks.append({"window": w, "height": h, "ts": ts, "txns": n_tx})
            time.sleep(0.15)
        print(f"  {w}: heights {h0}-{h1}, {sum(1 for x in blocks if x['window'] == w)} blocks")
    save(snap, "block_sample_txns", pd.DataFrame(rows), BASE, "transactions in seeded random blocks, by receiver and signer",
         {"seed": SEED, "windows": WINDOWS, "blocks_per_window": N})
    save(snap, "block_sample_blocks", pd.DataFrame(blocks), BASE, "one row per sampled block", {"seed": SEED})
