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
