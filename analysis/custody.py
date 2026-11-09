"""Custody reconciliation: separate confidential payouts from coverage gaps, for USDT on Tron.

Method
- Every USDT transfer out of the bridge's Tron hot wallet is a payout from NEAR Intents' custody.
- Every public withdrawal is an `ft_transfer` from intents.near to the bridged-USDT contract with memo
  `WITHDRAW_TO:<tron address>`.
- Match each Tron payout to one public withdrawal: same recipient, Tron amount at most the NEAR amount and no more
  than a bridge fee below it (5 USDT + 0.2%), sent between 2 minutes before and 3 hours after the NEAR receipt.
  Matching is one-to-one, closest in time first. A second pass with a 24-hour window labels late payouts.

Reading
- matched payout          public on both chains: an ordinary withdrawal.
- late match              public on both chains, paid out after a long delay.
- no public withdrawal    money left custody with no record on NEAR: the upper bound on confidential payouts
                          (or internal moves such as cold-storage sweeps) on this route.
- NEAR withdrawal with no Tron payout   a payout from another wallet, or one still pending: a coverage gap on our side.

A residual (reported total minus observed) cannot tell confidential volume from missed data. This can, for one route.
Payouts that never leave NEAR (a confidential swap whose output stays inside Intents) are invisible to any method.
"""
from __future__ import annotations
import pandas as pd
from pipeline.common import load_df, ROOT

T = ROOT / "reports" / "tables"
DEC = 1e6  # USDT has 6 decimals on both chains


def _match(tron: pd.DataFrame, near: pd.DataFrame, before: pd.Timedelta, after: pd.Timedelta) -> pd.DataFrame:
    c = tron.reset_index().merge(near.reset_index(), left_on="to", right_on="dest", suffixes=("_t", "_n"))
    c["fee"] = c.amt_n - c.amt_t
    c["lag_s"] = (c.ts_t - c.ts_n).dt.total_seconds()
    c = c[(c.fee >= -1e-9) & (c.fee <= 5 + 0.002 * c.amt_n) & (c.lag_s >= -before.total_seconds()) & (c.lag_s <= after.total_seconds())]
    c = c.assign(score=c.lag_s.abs() + 60 * c.fee).sort_values("score")
    used_t, used_n, out = set(), set(), []
    for r in c.itertuples():
        if r.index_t in used_t or r.index_n in used_n:
            continue
        used_t.add(r.index_t); used_n.add(r.index_n)
        out.append((r.index_t, r.index_n, r.fee, r.lag_s))
    return pd.DataFrame(out, columns=["t", "n", "fee", "lag_s"])


def build(snap) -> dict:
    p_n, p_t = snap / "custody_near_receipts.parquet", snap / "custody_tron_outflows.parquet"
    if not (p_n.exists() and p_t.exists()):
        return {}
    rec = load_df(snap, "custody_near_receipts")
    tron = load_df(snap, "custody_tron_outflows").drop_duplicates("tron_tx")
    w = rec[(rec.method == "ft_transfer") & rec.memo.str.startswith("WITHDRAW_TO:") & rec.ok].copy()
    w["dest"] = w.memo.str.slice(12)
    w["amt"] = w.amount.astype(float) / DEC
    w = w.drop_duplicates("receipt_id").rename(columns={"ts": "ts"})
    tron["amt"] = tron.value.astype(float) / DEC
    # interior window: whole UTC days fully covered by both fetches
    start = max(w.ts.min(), tron.ts.min()).ceil("D")
    end = min(w.ts.max(), tron.ts.max()).floor("D")
    ti = tron[(tron.ts >= start) & (tron.ts < end)].copy()
    ni = w[(w.ts >= start - pd.Timedelta(hours=24)) & (w.ts < end)].copy()

    m1 = _match(ti, ni, pd.Timedelta(minutes=2), pd.Timedelta(hours=3))
    ti["status"] = "no public withdrawal"
    ti.loc[m1.t, "status"] = "matched"
    ti.loc[m1.t, "fee"] = m1.fee.values; ti.loc[m1.t, "lag_s"] = m1.lag_s.values
    rest_t, rest_n = ti[ti.status != "matched"], ni.drop(index=m1.n)
    m2 = _match(rest_t, rest_n, pd.Timedelta(minutes=2), pd.Timedelta(hours=24))
    ti.loc[m2.t, "status"] = "late match (3-24h)"
    ti.loc[m2.t, "fee"] = m2.fee.values; ti.loc[m2.t, "lag_s"] = m2.lag_s.values
    n_in = ni[(ni.ts >= start) & (ni.ts < end - pd.Timedelta(hours=3))]
    n_unpaid = n_in.drop(index=[i for i in list(m1.n) + list(m2.n) if i in n_in.index])

    T.mkdir(parents=True, exist_ok=True)
    ti["date"] = ti.ts.dt.floor("D").dt.date
    daily = ti.pivot_table(index="date", columns="status", values="amt", aggfunc="sum", fill_value=0.0)
    for col in ("matched", "late match (3-24h)", "no public withdrawal"):
        if col not in daily:
            daily[col] = 0.0
    daily["payouts"] = ti.groupby("date").size()
    daily["public_withdrawals"] = n_in.assign(date=n_in.ts.dt.floor("D").dt.date).groupby("date").size()
    daily = daily.reset_index()
    daily.to_csv(T / "custody_daily.csv", index=False)
    ti[ti.status != "matched"][["ts", "tron_tx", "to", "amt", "status", "lag_s"]].sort_values("amt", ascending=False).to_csv(T / "custody_unmatched.csv", index=False)
    n_unpaid[["ts", "tx_hash", "dest", "amt"]].sort_values("amt", ascending=False).to_csv(T / "custody_unpaid_withdrawals.csv", index=False)

    tot = ti.amt.sum()
    by = ti.groupby("status").amt.agg(["sum", "count"])
    get = lambda s, c: float(by.loc[s, c]) if s in by.index else 0.0
    mt = ti[ti.status == "matched"]
    return {
        "cust_route": "USDT on Tron",
        "cust_wallets": ",".join(sorted(tron.wallet.unique())),
        "cust_start": str(start.date()), "cust_end": str((end - pd.Timedelta(days=1)).date()), "cust_days": int((end - start).days),
        "cust_payouts_n": int(len(ti)), "cust_payouts_usd": float(tot),
        "cust_matched_usd": get("matched", "sum"), "cust_matched_n": int(get("matched", "count")),
        "cust_late_usd": get("late match (3-24h)", "sum"), "cust_late_n": int(get("late match (3-24h)", "count")),
        "cust_nopublic_usd": get("no public withdrawal", "sum"), "cust_nopublic_n": int(get("no public withdrawal", "count")),
        "cust_public_share": float((get("matched", "sum") + get("late match (3-24h)", "sum")) / tot) if tot else None,
        "cust_nopublic_share": float(get("no public withdrawal", "sum") / tot) if tot else None,
        "cust_fee_median": float(mt.fee.median()) if len(mt) else None,
        "cust_lag_median_s": float(mt.lag_s.median()) if len(mt) else None,
        "cust_lag_p95_s": float(mt.lag_s.quantile(0.95)) if len(mt) else None,
        "cust_near_withdrawals_n": int(len(n_in)), "cust_near_withdrawals_usd": float(n_in.amt.sum()),
        "cust_near_unpaid_n": int(len(n_unpaid)), "cust_near_unpaid_usd": float(n_unpaid.amt.sum()),
        "cust_withdraw_predecessors": ",".join(sorted(w.predecessor.unique())),
    }
