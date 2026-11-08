"""Derive the analytical tables and headline KPIs from a snapshot. Everything downstream reads these."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from pipeline.common import load_df, load_json, latest_snapshot, ROOT

TABLES = ROOT / "reports" / "tables"
WALLET = "buybacks.multisignature.near"


def intents_daily(snap: Path) -> pd.DataFrame:
    df = load_df(snap, "llama_intents_daily").copy()
    df = df[df.date < df.date.max()]  # drop the partial current day
    df["fee_rate_bps"] = 1e4 * df.fees_usd / df.volume_usd
    df["capture_rate"] = df.revenue_usd / df.fees_usd
    for w in (30, 90):
        df[f"volume_{w}d"] = df.volume_usd.rolling(w).sum()
        df[f"fees_{w}d"] = df.fees_usd.rolling(w).sum()
        df[f"revenue_{w}d"] = df.revenue_usd.rolling(w).sum()
        df[f"capture_{w}d"] = df[f"revenue_{w}d"] / df[f"fees_{w}d"]
        df[f"fee_rate_bps_{w}d"] = 1e4 * df[f"fees_{w}d"] / df[f"volume_{w}d"]
    return df


def buybacks_daily(snap: Path, price: pd.DataFrame) -> pd.DataFrame:
    b = load_df(snap, "buyback_receipts")
    sweeps = b[(b.receiver == WALLET) & (b.predecessor == "intents.near") & (b.action == "TRANSFER") & (b.status == True)]
    d = sweeps.groupby("date").agg(near_bought=("deposit_near", "sum"), sweeps=("receipt_id", "count")).reset_index()
    idx = pd.date_range(d.date.min(), d.date.max())
    d = d.set_index("date").reindex(idx, fill_value=0).rename_axis("date").reset_index()
    d = d.merge(price[["date", "price_usd"]], on="date", how="left")
    d["price_usd"] = d.price_usd.ffill()
    d["usd_bought"] = d.near_bought * d.price_usd
    d["near_cum"] = d.near_bought.cumsum()
    d["usd_cum"] = d.usd_bought.cumsum()
    return d


def issuance_daily(snap: Path, price: pd.DataFrame) -> pd.DataFrame:
    c = load_df(snap, "nearblocks_charts")[["date", "total_supply", "circulating_supply", "txns", "active_accounts",
                                            "new_accounts", "txn_fee_usd", "txn_fee", "active_contracts", "new_contracts"]].copy()
    c["issued_near"] = c.total_supply.diff()
    c = c.merge(price[["date", "price_usd"]], on="date", how="left")
    c["issued_usd"] = c.issued_near * c.price_usd
    return c


def validators(snap: Path, total_supply: float) -> dict:
    v = load_df(snap, "rpc_validators").sort_values("stake_near", ascending=False)
    tot = float(v.stake_near.sum())
    cs = v.stake_near.cumsum()
    return {"validators": int(len(v)), "total_stake_near": tot, "staking_ratio": tot / total_supply,
            "nakamoto_coefficient_1_3": int((cs < tot / 3).sum() + 1), "top10_stake_share": float(v.stake_near.head(10).sum() / tot),
            "top20_stake_share": float(v.stake_near.head(20).sum() / tot)}


def signer(snap: Path) -> dict:
    """Chain Signatures usage from the v1.signer sample; extrapolated, labelled as such."""
    try:
        d = load_df(snap, "signer_sample")
    except FileNotFoundError:
        return {}
    import json as _json
    meta = _json.loads((snap / "manifest.json").read_text())["files"]["signer_sample.parquet"]
    span = (d.ts.max() - d.ts.min()).total_seconds() / 86400
    sign = d[d.method == "sign"]
    shares = sign.predecessor.value_counts(normalize=True)
    infra = ["omni.bridge.near", "fast-auth.near", "btc-connector.bridge.near", "zcash-connector.bridge.near"]
    top = shares.head(8).reset_index(); top.columns = ["caller", "share"]
    top.to_csv(TABLES / "signer_callers.csv", index=False)
    return {"signer_lifetime_receipts": meta["lifetime_receipts"], "signer_sample_rows": int(len(d)), "signer_sample_hours": span * 24,
            "signer_sign_calls_per_day_est": float(len(sign) / span), "signer_receipts_per_day_est": float(len(d) / span),
            "signer_near_infra_share": float(shares.reindex(infra).fillna(0).sum()), "signer_top_caller": str(shares.index[0]),
            "signer_top_caller_share": float(shares.iloc[0])}


def developers(snap: Path) -> dict:
    """Electric Capital monthly-active developers: NEAR vs peers, same definition for all."""
    try:
        d = load_df(snap, "opendevdata_mads")
    except FileNotFoundError:
        return {}
    d = d.copy(); d["day"] = pd.to_datetime(d.day)
    last_day = d.day.max()
    peers = d[d.day == last_day].sort_values("all_devs", ascending=False)[
        ["ecosystem", "day", "all_devs", "exclusive_devs", "multichain_devs", "full_time_devs", "part_time_devs", "one_time_devs", "devs_2y_plus", "num_commits"]]
    peers["rank"] = range(1, len(peers) + 1)
    peers.to_csv(TABLES / "devs_peers.csv", index=False)
    # month-end series since 2021 for the chart
    me = d.set_index("day").groupby("ecosystem")[["all_devs", "exclusive_devs", "full_time_devs"]].resample("ME").last().reset_index()
    me = me[me.day >= "2021-01-01"]
    me.to_csv(TABLES / "devs_monthly.csv", index=False)
    n = d[d.ecosystem == "NEAR"].set_index("day").sort_index()
    cur = n.iloc[-1]
    def at(dt):
        return n.loc[:dt].iloc[-1]
    y1, y2, y4 = at(last_day - pd.DateOffset(years=1)), at(last_day - pd.DateOffset(years=2)), at(last_day - pd.DateOffset(years=4))
    peak = n.all_devs.idxmax()
    return {"dev_as_of": str(last_day.date()), "dev_all": int(cur.all_devs), "dev_exclusive": int(cur.exclusive_devs),
            "dev_full_time": int(cur.full_time_devs), "dev_2y_plus": int(cur.devs_2y_plus),
            "dev_all_1y_ago": int(y1.all_devs), "dev_all_2y_ago": int(y2.all_devs), "dev_all_4y_ago": int(y4.all_devs),
            "dev_full_time_1y_ago": int(y1.full_time_devs), "dev_full_time_4y_ago": int(y4.full_time_devs),
            "dev_all_chg_1y": float(cur.all_devs / y1.all_devs - 1), "dev_all_chg_4y": float(cur.all_devs / y4.all_devs - 1),
            "dev_full_time_chg_1y": float(cur.full_time_devs / y1.full_time_devs - 1),
            "dev_peak_all": int(n.all_devs.max()), "dev_peak_date": str(peak.date()),
            "dev_rank_all": int(peers.set_index("ecosystem").loc["NEAR", "rank"]), "dev_peers_n": int(len(peers)),
            "dev_rank_full_time": int((peers.full_time_devs > cur.full_time_devs).sum() + 1)}


def cross_protocol(snap: Path) -> dict:
    """NEAR Intents against every swap aggregator and bridge aggregator DefiLlama tracks, one volume definition.
    DefiLlama files Intents under its DEX overview (category Bridge), so we insert that row into each list and rank it."""
    try:
        a = load_df(snap, "llama_aggregators")
    except FileNotFoundError:
        return {}
    a = a[a.total30d.fillna(0) > 0].copy()
    ni = a[(a.llama_category == "dex_overview") & (a.name == "NEAR Intents")]
    if ni.empty:
        return {}
    ni = ni.iloc[0]
    k = {"xp_intents_vol30": float(ni.total30d), "xp_intents_chg_1m_llama": float(ni.change_1m) if pd.notna(ni.change_1m) else None,
         "xp_intents_llama_category": str(ni.category)}
    dex = a[a.llama_category == "dex_overview"].sort_values("total30d", ascending=False).reset_index(drop=True)
    k["xp_dex_overview_rank"] = int(dex.index[dex.name == "NEAR Intents"][0] + 1); k["xp_dex_overview_n"] = int(len(dex))
    bridges = dex[dex.category.isin(["Bridge", "Cross Chain Bridge"])]
    k["xp_bridge_cat_next"] = "; ".join(f"{o.displayName} ${o.total30d/1e9:.2f}B" for o in bridges[bridges.name != "NEAR Intents"].head(3).itertuples())
    frames = []
    for cat, tag in (("bridge_aggregator", "bridge"), ("swap_aggregator", "swap")):
        c = a[a.llama_category == cat].copy()
        row = ni.copy(); row["llama_category"] = cat; row["displayName"] = "NEAR Intents (DefiLlama category: Bridge)"
        c = pd.concat([c, row.to_frame().T], ignore_index=True)
        c["total30d"] = c.total30d.astype(float)
        c = c.sort_values("total30d", ascending=False).reset_index(drop=True)
        c["rank_30d"] = c.index + 1
        c["share_of_list_30d"] = c.total30d / c.total30d.sum()
        frames.append(c)
        r = c[c.name == "NEAR Intents"].iloc[0]
        k[f"xp_{tag}_rank"] = int(r.rank_30d); k[f"xp_{tag}_n"] = int(len(c)); k[f"xp_{tag}_share"] = float(r.share_of_list_30d)
        others = c[c.name != "NEAR Intents"].head(3)
        k[f"xp_{tag}_next"] = "; ".join(f"{o.displayName} ${o.total30d/1e9:.2f}B" for o in others.itertuples())
        k[f"xp_{tag}_leader"] = str(c.iloc[0].displayName); k[f"xp_{tag}_leader_vol30"] = float(c.iloc[0].total30d)
    out = pd.concat(frames, ignore_index=True)
    cols = ["llama_category", "rank_30d", "displayName", "total24h", "total7d", "total30d", "total30DaysAgo", "change_1m", "totalAllTime", "n_chains", "share_of_list_30d"]
    out[cols].to_csv(TABLES / "aggregators.csv", index=False)
    return k


def build(snap: Path) -> dict:
    TABLES.mkdir(parents=True, exist_ok=True)
    cg = load_df(snap, "coingecko_daily")
    near_px = cg[cg.coin == "near"].sort_values("date")
    idaily = intents_daily(snap)
    bb = buybacks_daily(snap, near_px)
    iss = issuance_daily(snap, near_px)
    acct = load_json(snap, "rpc_accounts")
    stats = load_json(snap, "nearblocks_stats")
    total_supply = float(stats["total_supply"]) / 1e24
    last = idaily.iloc[-1]
    w = 30
    bb30 = bb[bb.date > bb.date.max() - pd.Timedelta(days=w)]
    iss30 = iss[iss.date > iss.date.max() - pd.Timedelta(days=w)]
    rev30 = float(last["revenue_30d"])
    kpis = {
        "snapshot": snap.name,
        "as_of_date": str(idaily.date.max().date()),
        "price_usd": float(near_px.price_usd.iloc[-1]),
        "market_cap_usd": float(near_px.market_cap_usd.iloc[-1]),
        "total_supply_near": total_supply,
        "circulating_supply_near": float(stats["circulating_supply"]) / 1e24,
        "intents_volume_30d": float(last["volume_30d"]), "intents_fees_30d": float(last["fees_30d"]), "intents_revenue_30d": rev30,
        "intents_volume_all": float(idaily.volume_usd.sum()), "intents_fees_all": float(idaily.fees_usd.sum()),
        "intents_revenue_all": float(idaily.revenue_usd.sum()),
        "fee_rate_bps_30d": float(last["fee_rate_bps_30d"]), "capture_30d": float(last["capture_30d"]),
        "capture_90d": float(last["capture_90d"]), "capture_lifetime": float(idaily.revenue_usd.sum() / idaily.fees_usd.sum()),
        "buyback_near_30d": float(bb30.near_bought.sum()), "buyback_usd_30d": float(bb30.usd_bought.sum()),
        "buyback_near_all": float(bb.near_bought.sum()), "buyback_usd_all": float(bb.usd_bought.sum()),
        "buyback_sweeps_all": int(bb.sweeps.sum()), "buyback_first_sweep": str(bb[bb.sweeps > 0].date.min().date()),
        "buyback_share_of_revenue_30d": float(bb30.usd_bought.sum() / rev30) if rev30 else None,
        "buyback_wallet_balance_near": acct[WALLET]["amount_near"], "buyback_wallet_locked_near": acct[WALLET]["locked_near"],
        "issued_near_30d": float(iss30.issued_near.sum()), "issued_usd_30d": float(iss30.issued_usd.sum()),
        "realized_issuance_annualised": float(iss30.issued_near.sum() * 365 / w / total_supply),
        "coverage_near_30d": float(bb30.near_bought.sum() / iss30.issued_near.sum()),
        "coverage_usd_30d": float(bb30.usd_bought.sum() / iss30.issued_usd.sum()),
        "txns_30d_avg": float(iss30.txns.mean()), "active_accounts_30d_avg": float(iss30.active_accounts.mean()),
        "new_accounts_30d_avg": float(iss30.new_accounts.mean()), "gas_fees_usd_30d": float(iss30.txn_fee_usd.sum()),
        "block_height": acct[WALLET]["block_height"],
    }
    kpis.update(validators(snap, total_supply))
    kpis.update(signer(snap))
    kpis.update(developers(snap))
    kpis.update(cross_protocol(snap))
    from analysis import volume_quality
    kpis.update(volume_quality.build(snap))
    # monthly table
    m = idaily.set_index("date").resample("MS")[["volume_usd", "fees_usd", "revenue_usd"]].sum()
    m["fee_rate_bps"] = 1e4 * m.fees_usd / m.volume_usd
    m["capture_rate"] = m.revenue_usd / m.fees_usd
    bm = bb.set_index("date").resample("MS")[["near_bought", "usd_bought"]].sum()
    im = iss.set_index("date").resample("MS")[["issued_near", "issued_usd"]].sum()
    monthly = m.join(bm, how="left").join(im, how="left").reset_index().rename(columns={"date": "month"})
    monthly["coverage_near"] = monthly.near_bought / monthly.issued_near
    # comps
    chain = load_json(snap, "llama_chain_fees")
    comps = []
    for coin, slug in (("near", "near"), ("ethereum", "ethereum"), ("solana", "solana")):
        px = cg[cg.coin == coin].sort_values("date").iloc[-1]
        row = {"asset": coin, "market_cap_usd": float(px.market_cap_usd), "chain_fees_30d": chain[slug]["fees_30d"],
               "chain_revenue_30d": chain[slug]["revenue_30d"]}
        if coin == "near":
            row["product_fees_30d"] = kpis["intents_fees_30d"]; row["product_revenue_30d"] = rev30
        comps.append(row)
    comps = pd.DataFrame(comps)
    comps["mcap_over_annualised_chain_fees"] = comps.market_cap_usd / (comps.chain_fees_30d * 365 / 30)
    comps["mcap_over_annualised_chain_revenue"] = comps.market_cap_usd / (comps.chain_revenue_30d * 365 / 30)
    idaily.to_csv(TABLES / "intents_daily.csv", index=False)
    bb.to_csv(TABLES / "buybacks_daily.csv", index=False)
    iss.to_csv(TABLES / "network_daily.csv", index=False)
    monthly.to_csv(TABLES / "monthly.csv", index=False)
    comps.to_csv(TABLES / "comps.csv", index=False)
    load_df(snap, "rpc_validators").to_csv(TABLES / "validators.csv", index=False)
    (TABLES / "kpis.json").write_text(json.dumps(kpis, indent=1))
    return kpis


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--snapshot", default=None)
    a = ap.parse_args()
    snap = Path(a.snapshot) if a.snapshot else latest_snapshot()
    k = build(snap)
    for key in ("as_of_date", "price_usd", "intents_volume_30d", "fee_rate_bps_30d", "capture_30d", "buyback_near_30d",
                "issued_near_30d", "coverage_near_30d", "staking_ratio", "nakamoto_coefficient_1_3"):
        print(f"{key:32s} {k[key]}")


if __name__ == "__main__":
    main()
