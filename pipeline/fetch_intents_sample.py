"""Volume quality: a seeded random sample of intents.near transactions, parsed down to the signed intents inside.

The Intents Explorer API (sender-level swaps) needs a partner JWT. Instead we read the chain: every settlement is an
`execute_intents` call whose arguments carry the user- and solver-signed messages (NEP-413 / ERC-191 / TIP-191),
each with a signer_id and a list of intents (token_diff, transfer, ft_withdraw, ...). NearBlocks serves these
transactions keylessly with a numeric cursor, so we jump to random cursors inside the window and take one page
(250 transactions, ~3 minutes of activity) at each. The seed, window and page count are recorded; re-running with
the same values reproduces the same cursors (the chain does not change, so the same pages come back).

Settings: INTENTS_PAGES (default 180), INTENTS_START / INTENTS_END (UTC dates, default 2026-09-01 / 2026-10-31),
INTENTS_SEED (default 20261108). Rate limit: ~1 request per 1.5 s, so the default takes about 8 minutes."""
from __future__ import annotations
import json, os, random, time
import pandas as pd
from .common import get_json, save

BASE = "https://api.nearblocks.io/v1/account/intents.near/txns-only"
PAGES = int(os.environ.get("INTENTS_PAGES", "180"))
START = pd.Timestamp(os.environ.get("INTENTS_START", "2026-09-01"), tz="UTC")
END = pd.Timestamp(os.environ.get("INTENTS_END", "2026-10-31"), tz="UTC") + pd.Timedelta(days=1)
SEED = int(os.environ.get("INTENTS_SEED", "20261108"))
WITHDRAW = {"ft_withdraw", "native_withdraw", "mt_withdraw", "nft_withdraw"}


def _headers():
    k = os.environ.get("NEARBLOCKS_API_KEY")
    return {"Authorization": f"Bearer {k}"} if k else None


def _page(cursor=None, per_page=250):
    p = {"per_page": per_page}
    if cursor:
        p["cursor"] = cursor
    return get_json(BASE, p, headers=_headers())


def _ts(x):
    return pd.Timestamp(int(x["block_timestamp"]), unit="ns", tz="UTC")


def _find_cursor(target: pd.Timestamp, lo: int, hi: int) -> int:
    """Binary search on the NearBlocks transaction id: smallest id whose page starts at or after `target`."""
    for _ in range(18):
        if hi - lo < 50_000:
            break
        mid = (lo + hi) // 2
        t = _page(mid, 1)["txns"]
        time.sleep(1.2)
        if not t or _ts(t[0]) < target:
            lo = mid
        else:
            hi = mid
    return hi


def unwrap(m):
    """Signed messages arrive JSON-encoded inside JSON, with a varying number of escape layers."""
    for _ in range(8):
        if not isinstance(m, str):
            return m
        try:
            m = json.loads(m)
            continue
        except Exception:  # noqa: BLE001
            pass
        m2 = m.replace('\\\\', '\\').replace('\\"', '"')
        if m2 == m:
            return None
        m = m2
    return m if isinstance(m, dict) else None


def parse_tx(x, page_no):
    rows = []
    for a in x.get("actions") or []:
        if a.get("method") != "execute_intents":
            continue
        try:
            args = json.loads(a.get("args") or "{}")
        except Exception:  # noqa: BLE001
            continue
        for s in args.get("signed", []):
            p = s.get("payload")
            m = unwrap(p.get("message") if isinstance(p, dict) else p)
            std = s.get("standard", "?")
            if not isinstance(m, dict):
                rows.append({"standard": std, "intent": "_unparsed"})
                continue
            for it in m.get("intents", []) or []:
                kind = it.get("intent")
                base = {"standard": std, "signer": m.get("signer_id"), "intent": kind}
                if kind == "token_diff":
                    for tok, amt in (it.get("diff") or {}).items():
                        rows.append({**base, "token": tok, "amount": str(amt)})
                elif kind == "transfer":
                    for tok, amt in (it.get("tokens") or {}).items():
                        rows.append({**base, "token": tok, "amount": str(amt), "dest": it.get("receiver_id")})
                elif kind in WITHDRAW:
                    memo = it.get("memo") or ""
                    dest = memo.split("WITHDRAW_TO:", 1)[1] if "WITHDRAW_TO:" in memo else it.get("receiver_id")
                    if kind == "mt_withdraw":
                        try:
                            inner = unwrap(it.get("msg")) or {}
                            dest = inner.get("receiver_id") or dest
                        except Exception:  # noqa: BLE001
                            pass
                        for tid, amt in zip(it.get("token_ids") or [], it.get("amounts") or []):
                            rows.append({**base, "token": f"nep245:{it.get('token')}:{tid}", "amount": str(amt), "dest": dest})
                    else:
                        if it.get("msg") and dest in ("omni.bridge.near",):
                            inner = unwrap(it.get("msg")) or {}
                            dest = inner.get("recipient") or inner.get("receiver_id") or dest
                        tok = it.get("token") or "wrap.near"
                        rows.append({**base, "token": f"nep141:{tok}", "amount": str(it.get("amount")), "dest": dest})
                else:
                    rows.append(base)
    for r in rows:
        r.update({"tx_hash": x["transaction_hash"], "ts": _ts(x), "tx_signer": x.get("signer_account_id"), "page": page_no})
    return rows


def run(snap):
    newest = _page(None, 1)["txns"][0]
    hi = int(newest["id"])
    lo = hi - 400 * 760_000  # ~400 days back at ~0.76M NearBlocks ids/day; searched, not assumed
    id_start = _find_cursor(START, lo, hi)
    id_end = _find_cursor(END, id_start, hi)
    rng = random.Random(SEED)
    cursors = sorted({rng.randrange(id_start, id_end) for _ in range(PAGES)})
    rows, pages = [], []
    for n, c in enumerate(cursors):
        try:
            t = _page(c)["txns"]
        except RuntimeError as e:
            pages.append({"page": n, "cursor": c, "txns": 0, "error": str(e)[:200]})
            continue
        if t:
            pages.append({"page": n, "cursor": c, "txns": len(t), "t_first": _ts(t[-1]), "t_last": _ts(t[0])})
        for x in t:
            rows.extend(parse_tx(x, n))
        time.sleep(1.5)
        if n % 20 == 0:
            print(f"  page {n+1}/{len(cursors)}: {len(rows):,} intent rows")
    df = pd.DataFrame(rows)
    pg = pd.DataFrame(pages)
    meta = {"seed": SEED, "pages_requested": PAGES, "pages_ok": int((pg.txns > 0).sum()), "window_start": str(START.date()),
            "window_end_exclusive": str(END.date()), "id_start": id_start, "id_end": id_end,
            "txns_sampled": int(pg.txns.sum()), "sampled_minutes": float(((pg.t_last - pg.t_first).dt.total_seconds() / 60).sum())}
    save(snap, "intents_sample", df, BASE, "seeded random pages of intents.near transactions, parsed to signed intents", meta)
    save(snap, "intents_sample_pages", pg, BASE, "one row per sampled page: cursor, size and time span", {"seed": SEED})
