"""Breakeven and scenario model.

Core identities (all per day unless stated):
  issuance_usd        = total_supply * issuance_rate / 365 * price
  captured_usd        = volume * fee_rate * capture_rate
  buyback_usd         = captured_usd * buyback_share
  coverage            = buyback_usd / issuance_usd            (1.0 = buybacks match the value of new issuance)
  breakeven_volume    = issuance_usd / (fee_rate * capture_rate * buyback_share)
Nothing here assumes bought NEAR is burned. Coverage compares flows; it is not a supply model.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import yaml
from pipeline.common import ROOT, latest_snapshot

TABLES = ROOT / "reports" / "tables"


def load_params(kpis: dict) -> dict:
    p = yaml.safe_load((ROOT / "params.yaml").read_text())
    m = {"price_usd": kpis["price_usd"], "total_supply_near": kpis["total_supply_near"],
         "fee_rate_bps": kpis["fee_rate_bps_30d"], "capture_rate": kpis["capture_30d"],
         "buyback_share_of_revenue": kpis["buyback_share_of_revenue_30d"]}
    for k, v in m.items():
        if p.get(k) == "measured":
            p[k] = v
    if p["issuance_scenarios"].get("realized_trailing") == "measured":
        p["issuance_scenarios"]["realized_trailing"] = kpis["realized_issuance_annualised"]
    return p


def breakeven_volume(total_supply, issuance_rate, price, fee_rate_bps, capture_rate, buyback_share=1.0):
    issuance_usd_day = total_supply * issuance_rate / 365 * price
    take = fee_rate_bps / 1e4 * capture_rate * buyback_share
    return issuance_usd_day / take, issuance_usd_day


def coverage(volume_day, total_supply, issuance_rate, price, fee_rate_bps, capture_rate, buyback_share=1.0):
    bv, iss = breakeven_volume(total_supply, issuance_rate, price, fee_rate_bps, capture_rate, buyback_share)
    return volume_day / bv


def run(snap: Path) -> dict:
    kpis = json.loads((TABLES / "kpis.json").read_text())
    p = load_params(kpis)
    vol_day = kpis["intents_volume_30d"] / 30
    rows = []
    for iname, irate in p["issuance_scenarios"].items():
        for cname, crate in [("measured_30d", p["capture_rate"])] + list(p["capture_scenarios"].items()):
            for bname, bshare in (("all_captured_revenue", 1.0), ("buyback_wallet_only", p["buyback_share_of_revenue"])):
                bv, iss = breakeven_volume(p["total_supply_near"], irate, p["price_usd"], p["fee_rate_bps"], crate, bshare)
                rows.append({"issuance_scenario": iname, "issuance_rate": irate, "capture_scenario": cname, "capture_rate": crate,
                             "deployment": bname, "buyback_share": bshare, "fee_rate_bps": p["fee_rate_bps"],
                             "issuance_usd_per_day": iss, "breakeven_volume_usd_per_day": bv,
                             "current_volume_usd_per_day": vol_day, "coverage_at_current_volume": vol_day / bv,
                             "volume_multiple_needed": bv / vol_day})
    be = pd.DataFrame(rows)
    be.to_csv(TABLES / "breakeven.csv", index=False)
    # sensitivity grid: capture x fee rate, at HSP-029 and current cap
    grid = []
    for irate in (p["issuance_scenarios"]["current_cap"], p["issuance_scenarios"]["hsp029_target"]):
        for fr in (10, 12.5, 15, 17.5, 20):
            for cr in (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50):
                bv, _ = breakeven_volume(p["total_supply_near"], irate, p["price_usd"], fr, cr, 1.0)
                grid.append({"issuance_rate": irate, "fee_rate_bps": fr, "capture_rate": cr, "breakeven_volume_usd_per_day": bv})
    pd.DataFrame(grid).to_csv(TABLES / "breakeven_sensitivity.csv", index=False)
    # 2030 scenarios
    v = p["valuation"]; years = v["horizon_year"] - 2026
    annual_vol_2026 = vol_day * 365
    sc = []
    for s in ("bear", "base", "bull"):
        vol = annual_vol_2026 * (1 + v["volume_cagr"][s]) ** years
        rev = vol * v["fee_rate_bps"][s] / 1e4 * v["capture_rate"][s]
        supply = p["total_supply_near"] * (1 + v["issuance_rate"][s]) ** years
        iss_usd = supply * v["issuance_rate"][s] * p["price_usd"]  # at today's price, so coverage is price-neutral
        mcap = rev * v["revenue_multiple"][s]
        sc.append({"scenario": s, "year": v["horizon_year"], "annual_volume_usd": vol, "fee_rate_bps": v["fee_rate_bps"][s],
                   "capture_rate": v["capture_rate"][s], "annual_net_revenue_usd": rev, "issuance_rate": v["issuance_rate"][s],
                   "supply_near": supply, "issuance_value_usd_at_today_price": iss_usd, "revenue_to_issuance": rev / iss_usd,
                   "revenue_multiple": v["revenue_multiple"][s], "implied_market_cap_usd": mcap,
                   "implied_price_usd": mcap / supply, "today_market_cap_usd": kpis["market_cap_usd"],
                   "implied_vs_today": mcap / kpis["market_cap_usd"]})
    scen = pd.DataFrame(sc)
    scen.to_csv(TABLES / "scenarios_2030.csv", index=False)
    summary = {"params_used": p, "current_volume_usd_per_day": vol_day,
               "breakeven_measured_current_cap": float(be[(be.issuance_scenario == "current_cap") & (be.capture_scenario == "measured_30d") & (be.deployment == "all_captured_revenue")].breakeven_volume_usd_per_day.iloc[0]),
               "breakeven_measured_hsp029": float(be[(be.issuance_scenario == "hsp029_target") & (be.capture_scenario == "measured_30d") & (be.deployment == "all_captured_revenue")].breakeven_volume_usd_per_day.iloc[0]),
               "breakeven_measured_buyback_only_current_cap": float(be[(be.issuance_scenario == "current_cap") & (be.capture_scenario == "measured_30d") & (be.deployment == "buyback_wallet_only")].breakeven_volume_usd_per_day.iloc[0]),
               "coverage_observed_near_30d": kpis["coverage_near_30d"], "coverage_observed_usd_30d": kpis["coverage_usd_30d"]}
    (TABLES / "model_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    return summary


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--snapshot", default=None)
    a = ap.parse_args()
    snap = Path(a.snapshot) if a.snapshot else latest_snapshot()
    s = run(snap)
    p = s["params_used"]
    print(f"price ${p['price_usd']:.2f}  fee rate {p['fee_rate_bps']:.1f} bps  capture {p['capture_rate']:.1%}  buyback share {p['buyback_share_of_revenue']:.1%}")
    print(f"current Intents volume      ${s['current_volume_usd_per_day']/1e6:,.0f}M/day")
    print(f"breakeven, 2.5% cap          ${s['breakeven_measured_current_cap']/1e6:,.0f}M/day (all captured revenue)")
    print(f"breakeven, HSP-029 1.6%      ${s['breakeven_measured_hsp029']/1e6:,.0f}M/day")
    print(f"breakeven, buyback wallet only, 2.5%: ${s['breakeven_measured_buyback_only_current_cap']/1e6:,.0f}M/day")
    print(f"observed coverage 30d: {s['coverage_observed_near_30d']:.1%} (NEAR terms), {s['coverage_observed_usd_30d']:.1%} (USD)")


if __name__ == "__main__":
    main()
