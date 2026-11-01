"""Fill thesis/THESIS.template.md with numbers from reports/tables so no figure in the thesis is hand-typed."""
import argparse, json
from pathlib import Path
import pandas as pd
from pipeline.common import ROOT, latest_snapshot

T = ROOT / "reports" / "tables"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--snapshot", default=None); ap.parse_args()
    k = json.loads((T / "kpis.json").read_text()); ms = json.loads((T / "model_summary.json").read_text())
    m = pd.read_csv(T / "monthly.csv", parse_dates=["month"]).set_index("month")
    sc = pd.read_csv(T / "scenarios_2030.csv").set_index("scenario")
    led = pd.read_csv(ROOT / "thesis" / "claims_ledger.csv")
    comps = pd.read_csv(T / "comps.csv").set_index("asset")
    sep, octo = m.loc["2026-09-01"], m.loc["2026-10-01"]
    counts = led.status.value_counts().to_dict()
    ledger_md = "| id | status | claim | observed |\n|---|---|---|---|\n" + "\n".join(
        f"| {r.claim_id} | {r.status} | {r.claim} | {r.observed} |" for r in led.itertuples())
    vals = {
        "snapshot": k["snapshot"], "as_of": k["as_of_date"], "price": f"{k['price_usd']:.2f}", "mcap_b": f"{k['market_cap_usd']/1e9:.2f}",
        "vol30_b": f"{k['intents_volume_30d']/1e9:.2f}", "vol_day_m": f"{ms['current_volume_usd_per_day']/1e6:.0f}",
        "fees30_m": f"{k['intents_fees_30d']/1e6:.2f}", "rev30_m": f"{k['intents_revenue_30d']/1e6:.2f}",
        "fee_bps": f"{k['fee_rate_bps_30d']:.1f}", "cap30": f"{k['capture_30d']:.1%}", "cap90": f"{k['capture_90d']:.1%}", "cap_life": f"{k['capture_lifetime']:.1%}",
        "vol_all_b": f"{k['intents_volume_all']/1e9:.1f}", "fees_all_m": f"{k['intents_fees_all']/1e6:.1f}", "rev_all_m": f"{k['intents_revenue_all']/1e6:.1f}",
        "bb30_near": f"{k['buyback_near_30d']:,.0f}", "bb30_usd_m": f"{k['buyback_usd_30d']/1e6:.2f}", "bb_all_near": f"{k['buyback_near_all']:,.0f}",
        "bb_all_usd_m": f"{k['buyback_usd_all']/1e6:.2f}", "bb_sweeps": f"{k['buyback_sweeps_all']:,}", "bb_first": k["buyback_first_sweep"],
        "bb_balance": f"{k['buyback_wallet_balance_near']:,.0f}", "bb_share": f"{k['buyback_share_of_revenue_30d']:.0%}",
        "iss30_near_m": f"{k['issued_near_30d']/1e6:.2f}", "iss30_usd_m": f"{k['issued_usd_30d']/1e6:.1f}", "iss_rate": f"{k['realized_issuance_annualised']:.2%}",
        "cov30": f"{k['coverage_near_30d']:.1%}", "iss_x_bb": f"{k['issued_near_30d']/k['buyback_near_30d']:.1f}",
        "be_cap_m": f"{ms['breakeven_measured_current_cap']/1e6:,.0f}", "be_hsp_m": f"{ms['breakeven_measured_hsp029']/1e6:,.0f}",
        "be_bbonly_m": f"{ms['breakeven_measured_buyback_only_current_cap']/1e6:,.0f}",
        "be_mult": f"{ms['breakeven_measured_current_cap']/ms['current_volume_usd_per_day']:.1f}", "be_mult_hsp": f"{ms['breakeven_measured_hsp029']/ms['current_volume_usd_per_day']:.1f}",
        "sep_vol_b": f"{sep.volume_usd/1e9:.2f}", "oct_vol_b": f"{octo.volume_usd/1e9:.2f}", "oct_chg": f"{octo.volume_usd/sep.volume_usd-1:+.0%}",
        "sep_cap": f"{sep.capture_rate:.0%}", "oct_cap": f"{octo.capture_rate:.0%}", "oct_bb_near": f"{octo.near_bought:,.0f}", "oct_iss_near_m": f"{octo.issued_near/1e6:.2f}",
        "txns30": f"{k['txns_30d_avg']:,.0f}", "aa30": f"{k['active_accounts_30d_avg']:,.0f}", "gas30_m": f"{k['gas_fees_usd_30d']/1e6:.2f}",
        "stake_ratio": f"{k['staking_ratio']:.1%}", "validators": k["validators"], "nakamoto": k["nakamoto_coefficient_1_3"], "top10": f"{k['top10_stake_share']:.0%}",
        "n_pass": counts.get("PASS", 0), "n_partial": counts.get("PARTIAL", 0), "n_unver": counts.get("UNVERIFIABLE", 0), "n_fail": counts.get("FAIL", 0),
        "ledger_table": ledger_md,
        "cs_calls": f"{k.get('signer_sign_calls_per_day_est', 0):,.0f}", "cs_hours": f"{k.get('signer_sample_hours', 0):.1f}", "cs_rows": f"{k.get('signer_sample_rows', 0):,}",
        "cs_lifetime": f"{k.get('signer_lifetime_receipts', 0)/1e6:.1f}M", "cs_infra": f"{k.get('signer_near_infra_share', 0):.0%}",
        "near_mcap_fees_x": f"{comps.loc['near','mcap_over_annualised_chain_fees']:,.0f}", "eth_mcap_fees_x": f"{comps.loc['ethereum','mcap_over_annualised_chain_fees']:,.0f}",
        "sol_mcap_fees_x": f"{comps.loc['solana','mcap_over_annualised_chain_fees']:,.0f}",
        "near_mcap_rev_x": f"{comps.loc['near','mcap_over_annualised_chain_revenue']:,.0f}", "near_product_rev_x": f"{k['market_cap_usd']/(k['intents_revenue_30d']*365/30):,.0f}",
        "near_product_fees_x": f"{k['market_cap_usd']/(k['intents_fees_30d']*365/30):,.0f}",
        "bear_mcap_b": f"{sc.loc['bear','implied_market_cap_usd']/1e9:.2f}", "base_mcap_b": f"{sc.loc['base','implied_market_cap_usd']/1e9:.2f}", "bull_mcap_b": f"{sc.loc['bull','implied_market_cap_usd']/1e9:.2f}",
        "base_rev_m": f"{sc.loc['base','annual_net_revenue_usd']/1e6:.0f}", "bull_rev_m": f"{sc.loc['bull','annual_net_revenue_usd']/1e6:.0f}", "bear_rev_m": f"{sc.loc['bear','annual_net_revenue_usd']/1e6:.0f}",
        "base_cov": f"{sc.loc['base','revenue_to_issuance']:.2f}", "bull_cov": f"{sc.loc['bull','revenue_to_issuance']:.2f}", "bear_cov": f"{sc.loc['bear','revenue_to_issuance']:.2f}",
        "base_vs_today": f"{sc.loc['base','implied_vs_today']:.2f}", "bull_vs_today": f"{sc.loc['bull','implied_vs_today']:.2f}",
    }
    tpl = (ROOT / "thesis" / "THESIS.template.md").read_text()
    out = tpl
    for key, val in vals.items():
        out = out.replace("{{" + key + "}}", str(val))
    missing = [s for s in out.split("{{")[1:] if "}}" in s]
    if missing:
        raise SystemExit(f"unfilled placeholders: {[m.split('}}')[0] for m in missing]}")
    (ROOT / "thesis" / "THESIS.md").write_text(out)
    print("thesis/THESIS.md rendered")


if __name__ == "__main__":
    main()
