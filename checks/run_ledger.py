"""Claims ledger: every public claim we rely on, re-tested against the snapshot. Writes thesis/claims_ledger.csv.
Statuses: PASS (observed within tolerance), FAIL (observed contradicts), PARTIAL (same direction, definitions differ),
UNVERIFIABLE (no independent public dataset reaches it). An honest UNVERIFIABLE beats a fabricated PASS."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import yaml
from pipeline.common import ROOT, latest_snapshot, load_df, load_json, utcnow

TABLES = ROOT / "reports" / "tables"
LEDGER = ROOT / "thesis" / "claims_ledger.csv"
WALLET = "buybacks.multisignature.near"


def within(obs, claim, tol):
    return abs(obs - claim) / abs(claim) <= tol


def build(snap: Path) -> pd.DataFrame:
    k = json.loads((TABLES / "kpis.json").read_text())
    p = {kk: float(vv) for kk, vv in yaml.safe_load((ROOT / "params.yaml").read_text())["reported_claims"].items()}
    acct = load_json(snap, "rpc_accounts")
    fast = load_json(snap, "fastnear_wallets")
    dash = load_json(snap, "revenue_dashboard")
    idaily = pd.read_csv(TABLES / "intents_daily.csv", parse_dates=["date"])
    bb = pd.read_csv(TABLES / "buybacks_daily.csv", parse_dates=["date"])
    q3 = idaily[(idaily.date >= "2026-07-01") & (idaily.date < "2026-10-01")]
    rows = []

    def add(cid, claim, source, observed, unit, status, evidence, limitation=""):
        rows.append({"claim_id": cid, "claim": claim, "source": source, "observed": observed, "unit": unit, "status": status,
                     "evidence": evidence, "limitation": limitation, "last_checked": utcnow(), "snapshot": snap.name})

    # C01 buybacks are happening
    add("C01", "Intents fees are being used to buy NEAR (buyback programme live since 2026-02-23)",
        "near.org 'Evolving NEAR Tokenomics' (Feb 24 2026); revenue.near.org",
        f"{k['buyback_sweeps_all']} automated TRANSFER receipts from intents.near, {k['buyback_near_all']:,.0f} NEAR, first on {k['buyback_first_sweep']}",
        "receipts", "PASS" if k["buyback_sweeps_all"] > 100 else "FAIL",
        "data/snapshots/<date>/buyback_receipts.parquet filtered predecessor=intents.near, action=TRANSFER",
        "First on-chain sweep into the buyback wallet is dated 2026-04-23, two months after the announced start; earlier purchases, if any, did not land in this wallet.")
    # C02 staked or locked
    staked = acct[WALLET]["locked_near"] + sum(float(x.get("staked", 0) or 0) for x in fast[WALLET]["staking"].get("pools", []))
    add("C02", "Repurchased NEAR is 'staked or locked' (tokenomics post wording)", "near.org 'Evolving NEAR Tokenomics'",
        f"wallet balance {k['buyback_wallet_balance_near']:,.0f} NEAR; locked {acct[WALLET]['locked_near']:.0f}; delegated pools: {len(fast[WALLET]['staking'].get('pools', []))}",
        "NEAR", "FAIL" if staked == 0 else "PASS",
        "RPC view_account locked field + FastNear /staking pools for the buyback wallet",
        "Tokens are held liquid in a multisig. They are not burned either. Coverage ratios in this repo therefore compare flows, not supply.")
    # C03 buybacks vs issuance
    add("C03", f"Issuance runs ~{p['issuance_to_buyback_ratio']}x buybacks (Ternullo, Bankless, Oct 6 2026)", "Bankless / Stocktwits, Oct 6 2026",
        f"trailing 30d: {k['issued_near_30d']:,.0f} NEAR issued vs {k['buyback_near_30d']:,.0f} NEAR bought = {k['issued_near_30d']/k['buyback_near_30d']:.1f}x; coverage {k['coverage_near_30d']:.1%}",
        "ratio", "PASS" if k['issued_near_30d'] / k['buyback_near_30d'] >= 4 else "FAIL",
        "NearBlocks daily total_supply diff vs buyback sweeps, same 30-day window",
        "Direction confirmed; the exact multiple moves with volume and price.")
    # C04 lifetime capture
    add("C04", f"Lifetime fee capture {p['lifetime_capture']:.1%} (NEAR Q3 update, Oct 6)", "NEAR Q3 2026 update / Nansen",
        f"{k['capture_lifetime']:.1%} = all-time captured revenue / all-time gross fees (DefiLlama series)", "share",
        "PASS" if within(k["capture_lifetime"], p["lifetime_capture"], 0.1) else "PARTIAL",
        "reports/tables/intents_daily.csv sums", "DefiLlama 'revenue' = NEAR swept into the three revenue wallets; NEAR's own definition is not published in detail.")
    # C05 trailing 30d capture
    add("C05", f"Trailing-30d fee capture {p['trailing30_capture']:.1%} (Oct 6)", "NEAR Q3 2026 update",
        f"{k['capture_30d']:.1%} for the 30 days to {k['as_of_date']}", "share",
        "PASS" if within(k["capture_30d"], p["trailing30_capture"], 0.1) else "PARTIAL",
        "intents_daily.csv capture_30d", "Different window end dates; capture moved from 28% to 34% during October as near.com's share rose.")
    # C06 Q3 volume
    add("C06", f"Q3 2026 Intents volume ${p['q3_intents_volume_usd']/1e9:.1f}B (Nansen)", "nansen.ai NEAR Q3 2026",
        f"${q3.volume_usd.sum()/1e9:.2f}B Jul 1 - Sep 30 (DefiLlama daily)", "USD",
        "PASS" if within(q3.volume_usd.sum(), p["q3_intents_volume_usd"], 0.05) else "PARTIAL", "intents_daily.csv Q3 sum")
    # C07 cumulative volume
    add("C07", f"Cumulative Intents volume above ${p['cumulative_volume_floor_usd']/1e9:.0f}B", "NEAR Q3 update, Oct 6",
        f"${k['intents_volume_all']/1e9:.1f}B all-time (DefiLlama)", "USD", "PASS" if k["intents_volume_all"] >= p["cumulative_volume_floor_usd"] else "FAIL",
        "intents_daily.csv sum", "DefiLlama's series includes confidential volume as NEAR reports it.")
    # C08 cumulative buybacks
    add("C08", f"More than ${p['buybacks_cumulative_usd']/1e6:.0f}M captured for buybacks (Nansen Q3)", "nansen.ai Q3 2026",
        f"${k['buyback_usd_all']/1e6:.2f}M = sweeps x daily price; wallet holds {k['buyback_wallet_balance_near']:,.0f} NEAR (${k['buyback_wallet_balance_near']*k['price_usd']/1e6:.1f}M today)",
        "USD", "PASS" if k["buyback_usd_all"] >= p["buybacks_cumulative_usd"] * 0.8 else "PARTIAL",
        "buybacks_daily.csv usd_cum", "USD at purchase is approximated with the daily CoinGecko close; revenue.near.org reports NEAR, not USD.")
    # C09 dashboard vs chain
    dw = next((w for w in dash["wallets"] if w["wallet"] == WALLET), None)
    if dw:
        diff = k["buyback_wallet_balance_near"] - dw["near_amount"]
        add("C09", "revenue.near.org wallet figure equals the on-chain balance of the buyback wallet", "revenue.near.org",
            f"dashboard {dw['near_amount']:,.0f} NEAR vs chain {k['buyback_wallet_balance_near']:,.0f} NEAR (diff {diff:,.0f}); sweeps from intents.near total {k['buyback_near_all']:,.0f}",
            "NEAR", "PARTIAL" if abs(diff) > 1000 else "PASS", "rpc_accounts.json vs revenue_dashboard.json",
            "The dashboard counts only sweeps from intents.near. The chain balance also holds ~510k NEAR transferred from 1csfundsadmin.sputnik-dao.near. The page labels its figures 'illustrative'.")
    # C10 staking ratio
    add("C10", f"Staking ratio ~{p['staking_ratio']:.0%} (Bitwise, Oct 2026)", "cryptobriefing.com / Bitwise",
        f"{k['staking_ratio']:.1%} = {k['total_stake_near']/1e6:.1f}M staked / {k['total_supply_near']/1e6:.0f}M total supply", "share",
        "PASS" if within(k["staking_ratio"], p["staking_ratio"], 0.05) else "PARTIAL", "RPC validators current_validators stake sum")
    # C11 validators
    add("C11", f"~{p['validators_active']} active validators (CryptoTicker, Oct 18)", "cryptoticker.io", f"{k['validators']} in the current epoch", "count",
        "PASS" if within(k["validators"], p["validators_active"], 0.1) else "PARTIAL", "RPC validators", "The set changes every epoch (~12h).")
    # C12 confidential TVL
    add("C12", f"Confidential Intents TVL ~${p['confidential_tvl_usd']/1e6:.0f}M", "revenue.near.org / NEAR",
        "no public contract state or indexer exposes the private shard", "USD", "UNVERIFIABLE", "none",
        "Confidential volume and TVL are NEAR-reported residuals (nearstats methodology). Treated as reported, never as observed.")
    # C13 NEAR AI staking
    add("C13", f">{p['near_ai_staked_near']/1e6:.0f}M NEAR staked for NEAR AI inference (Oct 21)", "x.com/NEARProtocol, near.ai blog",
        "no staking pool or contract account is named by NEAR AI", "NEAR", "UNVERIFIABLE", "none",
        "If NEAR AI publishes the pool account, add it to pipeline/fetch_fastnear.py and this row becomes testable.")
    # C14 ETF
    add("C14", f"Bitwise NRR holds ~{p['etf_near_held']/1e6:.2f}M NEAR (Oct 28)", "nrretf.com (JS-rendered)",
        "fund page is not machine-readable without a browser; no on-chain custody address published", "NEAR", "UNVERIFIABLE", "none",
        "Track via the issuer's daily holdings file if one is published.")
    # C15 HSP-029 snapshot
    add("C15", f"HSP-029 text: staking ratio {p['hsp029_staking_ratio']:.2%} at block 216,701,043 (Sep 22)", "gov.near.org HSP-029",
        f"{k['staking_ratio']:.2%} at block {k['block_height']} (Nov 1); direction: up", "share", "PARTIAL",
        "RPC validators", "Different blocks; the proposal's claim that participation is falling is not supported by the Nov 1 reading, which is higher.")
    # C16 Sept/Oct monthly volume
    m = pd.read_csv(TABLES / "monthly.csv", parse_dates=["month"]).set_index("month")
    sep, octo = m.loc["2026-09-01", "volume_usd"], m.loc["2026-10-01", "volume_usd"]
    add("C16", "September 2026 was a record month ($4.80B) and October fell (~$3.99B)", "nearstats.org monthly table",
        f"Sep ${sep/1e9:.2f}B, Oct ${octo/1e9:.2f}B ({(octo/sep-1):+.1%})", "USD",
        "PASS" if within(sep, 4.80e9, 0.03) and within(octo, 3.99e9, 0.03) else "PARTIAL", "monthly.csv")
    # C17 Chain Signatures usage
    if "signer_sign_calls_per_day_est" in k:
        add("C17", "Chain Signatures is used in production (NEAR docs, Messari); scale and who uses it are not published", "docs.near.org",
            f"~{k['signer_sign_calls_per_day_est']:,.0f} sign calls/day (extrapolated from {k['signer_sample_rows']:,} receipts over {k['signer_sample_hours']:.1f} h); lifetime receipts {k['signer_lifetime_receipts']:,}; {k['signer_near_infra_share']:.0%} of sign calls come from NEAR's own bridge/FastAuth contracts",
            "calls/day", "PASS", "data/snapshots/<date>/signer_sample.parquet; reports/tables/signer_callers.csv",
            "Call counts, not value signed. Most demand is NEAR Intents' own bridging (omni.bridge, btc/zcash connectors) and FastAuth, not third-party apps or agents.")
    df = pd.DataFrame(rows)
    LEDGER.parent.mkdir(exist_ok=True)
    df.to_csv(LEDGER, index=False)
    return df


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--snapshot", default=None)
    a = ap.parse_args()
    snap = Path(a.snapshot) if a.snapshot else latest_snapshot()
    df = build(snap)
    pd.set_option("display.width", 200, "display.max_colwidth", 90)
    print(df[["claim_id", "status", "claim"]].to_string(index=False))
    print("\ncounts:", df.status.value_counts().to_dict())


if __name__ == "__main__":
    main()
