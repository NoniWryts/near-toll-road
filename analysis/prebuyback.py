"""The chain before the buybacks: what NEAR looked like when nothing bought the issuance back, and why a revenue-funded
buyback was not possible earlier. Compares the six months before the Intents fee switch (went live 2026-02-23) with
the period since, from the same daily network series, and prices NEAR against SOL and ETH over the same dates.

Reading: this is a before/after description, not a causal estimate. Several things moved at once (issuance was halved
in October 2025; one reward app stopped in April 2026, see Volume quality). Each is called out where it matters."""
from __future__ import annotations
import pandas as pd
from pipeline.common import load_df, ROOT

T = ROOT / "reports" / "tables"
SWITCH = pd.Timestamp("2026-02-23")        # fee switch go-live reported by NEAR; first on-chain sweep is later (see kpis)
PRE_START = pd.Timestamp("2025-08-23")     # six months before the switch
HALVING = pd.Timestamp("2025-11-01")       # max inflation 5% -> 2.5% (nearcore 2.9.0, protocol 81, voted end Oct 2025)
BURN_SHARE = 0.70                          # share of gas fees burned by the protocol (NEAR docs); used only for the burn estimate


def build(snap) -> dict:
    n = pd.read_csv(T / "network_daily.csv", parse_dates=["date"])
    cg = load_df(snap, "coingecko_daily")
    idaily = pd.read_csv(T / "intents_daily.csv", parse_dates=["date"])
    end = n.date.max()
    n = n[n.date >= "2024-06-01"].copy()
    n["month"] = n.date.dt.to_period("M").dt.to_timestamp()
    g = n.groupby("month").agg(txns_per_day=("txns", "mean"), active_accounts_per_day=("active_accounts", "mean"),
                                new_accounts_per_day=("new_accounts", "mean"), issued_near=("issued_near", "sum"),
                                issued_usd=("issued_usd", "sum"), gas_fee_usd=("txn_fee_usd", "sum"),
                                supply=("total_supply", "last"), price_usd=("price_usd", "mean")).reset_index()
    g["burned_usd_est"] = BURN_SHARE * g.gas_fee_usd
    g["burn_cover"] = g.burned_usd_est / g.issued_usd.where(g.issued_usd > 0)
    iv = idaily.assign(month=idaily.date.dt.to_period("M").dt.to_timestamp()).groupby("month").volume_usd.sum().rename("intents_volume_usd")
    g = g.merge(iv, on="month", how="left")
    g.to_csv(T / "prebuyback_monthly.csv", index=False)

    pre = n[(n.date >= PRE_START) & (n.date < SWITCH)]
    post = n[(n.date >= SWITCH) & (n.date <= end)]
    pre_h = n[(n.date >= HALVING) & (n.date < SWITCH)]                     # after the halving, before the switch
    peak = n[(n.date >= "2025-01-01") & (n.date < "2025-02-01")]            # a reference month a year before the switch
    k = {}
    for tag, w in (("pre", pre), ("post", post)):
        k[f"pb_{tag}_txns_day"] = float(w.txns.mean())
        k[f"pb_{tag}_active_day"] = float(w.active_accounts.mean())
        k[f"pb_{tag}_new_day"] = float(w.new_accounts.mean())
        k[f"pb_{tag}_issued_near_day"] = float(w.issued_near.mean())
    k["pb_pre_issuance_annual"] = float(pre.issued_near.sum() / (pre.date.nunique()) * 365 / pre.total_supply.iloc[0])
    k["pb_post_issuance_annual"] = float(post.issued_near.sum() / post.date.nunique() * 365 / post.total_supply.iloc[0])
    k["pb_prehalving_issuance_annual"] = float(n[(n.date >= PRE_START) & (n.date < HALVING)].issued_near.mean() * 365 / pre.total_supply.iloc[0])
    k["pb_posthalving_prefee_issuance_annual"] = float(pre_h.issued_near.mean() * 365 / pre_h.total_supply.iloc[0])
    k["pb_gas_usd_day_pre_halved"] = float(pre_h.txn_fee_usd.mean())
    k["pb_issued_usd_day_pre_halved"] = float(pre_h.issued_usd.mean())
    k["pb_burn_cover_pre_halved"] = float(BURN_SHARE * pre_h.txn_fee_usd.sum() / pre_h.issued_usd.sum())
    k["pb_burn_cover_post"] = float(BURN_SHARE * post.txn_fee_usd.sum() / post.issued_usd.sum())
    k["pb_active_chg_jan25_to_switch"] = float(pre_h.active_accounts.mean() / peak.active_accounts.mean() - 1)
    k["pb_txns_chg_jan25_to_switch"] = float(pre_h.txns.mean() / peak.txns.mean() - 1)
    k["pb_active_jan25"] = float(peak.active_accounts.mean())
    k["pb_txns_jan25"] = float(peak.txns.mean())
    k["pb_active_pre_halved"] = float(pre_h.active_accounts.mean())
    k["pb_txns_pre_halved"] = float(pre_h.txns.mean())
    k["pb_switch_date"] = str(SWITCH.date())
    # first on-chain sweep
    b = pd.read_csv(T / "buybacks_daily.csv", parse_dates=["date"])
    first = b[b.near_bought > 0].date.min()
    k["pb_first_sweep"] = str(first.date())
    k["pb_gap_days"] = int((first - SWITCH).days)
    # price: NEAR vs SOL and ETH
    p = cg.pivot(index="date", columns="coin", values="price_usd").sort_index()
    at = lambda d: p.loc[:pd.Timestamp(d)].iloc[-1]
    s0, s1, s2 = at(p.index.min()), at(SWITCH - pd.Timedelta(days=1)), at(end)
    for coin in ("near", "solana", "ethereum"):
        k[f"pb_px_pre_{coin}"] = float(s1[coin] / s0[coin] - 1)
        k[f"pb_px_post_{coin}"] = float(s2[coin] / s1[coin] - 1)
    vol = cg[(cg.coin == "near") & (cg.date >= SWITCH)].volume_usd
    k["pb_near_trading_usd_day"] = float(vol.mean())
    k["pb_intents_fees_first_month"] = str(idaily[idaily.fees_usd > 1000].date.min().date())
    k["pb_intents_rev_first_month"] = str(idaily[idaily.revenue_usd > 1000].date.min().date())
    k["pb_intents_rev_before_nov25_usd"] = float(idaily[idaily.date < "2025-11-01"].revenue_usd.sum())
    k["pb_intents_fees_before_switch_usd"] = float(idaily[idaily.date < SWITCH].fees_usd.sum())
    k["pb_px_start"] = str(p.index.min().date())
    k["pb_as_of"] = str(end.date())
    pr = (p / p.loc[p.index.min()] * 100).reset_index()
    pr.to_csv(T / "prebuyback_price_index.csv", index=False)
    return k
