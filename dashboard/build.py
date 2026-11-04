"""Static dashboard: one self-contained HTML file built from reports/tables. Serve with `make serve`."""
from __future__ import annotations
import argparse, json, html
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pipeline.common import ROOT, latest_snapshot

T = ROOT / "reports" / "tables"
OUT = ROOT / "dashboard" / "index.html"
# categorical palette (validated, dataviz reference instance): blue, orange, aqua, yellow
C = {"1": "#2a78d6", "2": "#eb6834", "3": "#1baf7a", "4": "#eda100", "grid": "#e8e7e3", "text": "#0b0b0b", "muted": "#52514e"}
LAYOUT = dict(template="plotly_white", font=dict(family="Inter, system-ui, sans-serif", size=13, color=C["text"]),
              margin=dict(l=48, r=24, t=84, b=40), hovermode="x unified", legend=dict(orientation="h", y=1.04, x=0, yanchor="bottom"), title=dict(y=0.97, yanchor="top"),
              xaxis=dict(gridcolor=C["grid"], showgrid=False), yaxis=dict(gridcolor=C["grid"], zeroline=False))


def fig_html(fig, h=380):
    fig.update_layout(height=h, **LAYOUT)
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, config={"displaylogo": False, "responsive": True})


def money(x, d=1):
    if x is None or pd.isna(x): return "n/a"
    for s, v in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(x) >= v: return f"${x/v:,.{d}f}{s}"
    return f"${x:,.0f}"


def build():
    k = json.loads((T / "kpis.json").read_text())
    ms = json.loads((T / "model_summary.json").read_text())
    d = pd.read_csv(T / "intents_daily.csv", parse_dates=["date"]); d = d[d.date >= "2025-06-01"]
    m = pd.read_csv(T / "monthly.csv", parse_dates=["month"]); m = m[m.month >= "2026-01-01"]
    n = pd.read_csv(T / "network_daily.csv", parse_dates=["date"]); n = n[n.date >= "2025-06-01"]
    b = pd.read_csv(T / "buybacks_daily.csv", parse_dates=["date"])
    be = pd.read_csv(T / "breakeven.csv"); sens = pd.read_csv(T / "breakeven_sensitivity.csv")
    sc = pd.read_csv(T / "scenarios_2030.csv"); comps = pd.read_csv(T / "comps.csv"); led = pd.read_csv(ROOT / "thesis" / "claims_ledger.csv")
    v = pd.read_csv(T / "validators.csv")

    # 1 volume
    f1 = go.Figure(); f1.add_bar(x=d.date, y=d.volume_usd, name="Daily Intents volume (USD)", marker_color=C["1"], marker_line_width=0)
    f1.add_scatter(x=d.date, y=d.volume_30d / 30, name="30-day average", line=dict(color=C["2"], width=2))
    f1.update_layout(title="NEAR Intents volume, daily (DefiLlama; includes NEAR-reported confidential volume)")
    # 2 fees vs revenue monthly
    f2 = go.Figure()
    f2.add_bar(x=m.month, y=m.fees_usd, name="Gross fees", marker_color=C["1"], marker_line_width=0)
    f2.add_bar(x=m.month, y=m.revenue_usd, name="Captured by NEAR (all revenue wallets)", marker_color=C["3"], marker_line_width=0)
    f2.add_bar(x=m.month, y=m.usd_bought, name="Swept into buyback wallet (USD at daily price)", marker_color=C["2"], marker_line_width=0)
    f2.update_layout(barmode="group", title="Monthly: gross fees, captured revenue, buybacks (2026)")
    # 3 capture + fee rate (two charts, one axis each)
    f3 = go.Figure(); f3.add_scatter(x=d.date, y=d.capture_30d, name="Capture rate, trailing 30d", line=dict(color=C["1"], width=2))
    f3.add_scatter(x=d.date, y=d.capture_90d, name="Capture rate, trailing 90d", line=dict(color=C["3"], width=2))
    f3.update_layout(title="Fee capture rate (captured revenue / gross fees)", yaxis_tickformat=".0%")
    f3b = go.Figure(); f3b.add_scatter(x=d.date, y=d.fee_rate_bps_30d, name="Gross fee rate, bps of volume (30d)", line=dict(color=C["2"], width=2))
    f3b.update_layout(title="Gross fee rate on Intents volume (basis points, trailing 30d)")
    # 4 issuance vs buybacks (NEAR)
    mi = m.copy()
    f4 = go.Figure()
    f4.add_bar(x=mi.month, y=mi.issued_near, name="NEAR issued (total-supply change)", marker_color=C["4"], marker_line_width=0)
    f4.add_bar(x=mi.month, y=mi.near_bought, name="NEAR bought back (sweeps from intents.near)", marker_color=C["2"], marker_line_width=0)
    f4.update_layout(barmode="group", title="Issuance vs buybacks, NEAR per month (price-free)")
    # 5 cumulative buybacks
    f5 = go.Figure(); f5.add_scatter(x=b.date, y=b.near_cum, name="Cumulative NEAR bought", line=dict(color=C["2"], width=2), fill="tozeroy", fillcolor="rgba(235,104,52,0.12)")
    f5.update_layout(title=f"Cumulative NEAR swept into buybacks.multisignature.near ({k['buyback_sweeps_all']:,} receipts since {k['buyback_first_sweep']})")
    # 6 breakeven sensitivity heatmap (one hue sequential)
    for irate, title in ((0.025, "2.5% cap (today)"), (0.016, "1.6% (HSP-029)")):
        pass
    piv = sens[sens.issuance_rate == 0.025].pivot(index="capture_rate", columns="fee_rate_bps", values="breakeven_volume_usd_per_day") / 1e6
    f6 = go.Figure(go.Heatmap(z=piv.values, x=[f"{c} bps" for c in piv.columns], y=[f"{r:.0%}" for r in piv.index], colorscale="Blues",
                              text=[[f"${x:,.0f}M" for x in row] for row in piv.values], texttemplate="%{text}", hovertemplate="fee %{x}, capture %{y}: $%{z:,.0f}M/day<extra></extra>", colorbar_title="$M/day"))
    f6.update_layout(title=f"Breakeven volume per day at 2.5% issuance (today {money(ms['current_volume_usd_per_day'],0)}/day)",
                     xaxis_title="gross fee rate", yaxis_title="capture rate")
    piv2 = sens[sens.issuance_rate == 0.016].pivot(index="capture_rate", columns="fee_rate_bps", values="breakeven_volume_usd_per_day") / 1e6
    f6b = go.Figure(go.Heatmap(z=piv2.values, x=[f"{c} bps" for c in piv2.columns], y=[f"{r:.0%}" for r in piv2.index], colorscale="Blues",
                               text=[[f"${x:,.0f}M" for x in row] for row in piv2.values], texttemplate="%{text}", colorbar_title="$M/day"))
    f6b.update_layout(title="Same grid at 1.6% issuance (HSP-029 target)", xaxis_title="gross fee rate", yaxis_title="capture rate")
    # 7 network activity
    f7 = go.Figure(); f7.add_scatter(x=n.date, y=n.txns, name="Transactions / day", line=dict(color=C["1"], width=2))
    f7.update_layout(title="Transactions per day (NearBlocks). Step down in April 2026: cause not established; Nansen reports ~740k/day in Q3")
    f7b = go.Figure(); f7b.add_scatter(x=n.date, y=n.active_accounts, name="Active accounts / day", line=dict(color=C["3"], width=2))
    f7b.add_scatter(x=n.date, y=n.new_accounts, name="New accounts / day", line=dict(color=C["4"], width=2))
    f7b.update_layout(title="Active and new accounts per day (NearBlocks; accounts, not people)")
    # 8 validators
    vv = v.sort_values("stake_near", ascending=False).head(40)
    f8 = go.Figure(go.Bar(x=list(range(1, len(vv) + 1)), y=vv.stake_near / 1e6, marker_color=C["1"], marker_line_width=0,
                          hovertext=vv.account_id, hovertemplate="%{hovertext}: %{y:.2f}M NEAR<extra></extra>"))
    f8.update_layout(title=f"Stake by validator rank, top 40 of {k['validators']} (Nakamoto coefficient at 1/3: {k['nakamoto_coefficient_1_3']}; top-10 share {k['top10_stake_share']:.0%})",
                     xaxis_title="rank", yaxis_title="M NEAR staked")
    # 9 chain signatures callers
    f9 = None
    sp = T / "signer_callers.csv"
    if sp.exists() and "signer_sign_calls_per_day_est" in k:
        sc9 = pd.read_csv(sp).sort_values("share")
        f9 = go.Figure(go.Bar(x=sc9.share, y=sc9.caller, orientation="h", marker_color=C["1"], marker_line_width=0,
                              text=[f"{x:.0%}" for x in sc9.share], textposition="outside", hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
        f9.update_layout(title=f"Who calls Chain Signatures: share of ~{k['signer_sign_calls_per_day_est']:,.0f} sign calls/day (sample of {k['signer_sample_rows']:,} receipts, {k['signer_sample_hours']:.1f} h)",
                         xaxis_tickformat=".0%", margin=dict(l=220))
    # 10 developers, 11 cross-protocol
    f10 = f11 = f12 = None
    dp = T / "devs_monthly.csv"
    if dp.exists() and "dev_all" in k:
        dm = pd.read_csv(dp, parse_dates=["day"])
        order = ["NEAR", "Solana", "Sui", "Aptos", "Avalanche", "Polygon", "Arbitrum", "Base"]
        palette = {"NEAR": C["1"], "Solana": C["2"], "Sui": C["3"], "Aptos": C["4"]}
        f10 = go.Figure()
        for eco in order:
            e = dm[dm.ecosystem == eco]
            if e.empty: continue
            f10.add_scatter(x=e.day, y=e.all_devs, name=eco, line=dict(color=palette.get(eco, "#b8b7b3"), width=3 if eco == "NEAR" else 1.5))
        f10.update_layout(title=f"Monthly-active developers, NEAR vs peer chains (NEAR {k['dev_all']}, peak {k['dev_peak_all']} in {k['dev_peak_date'][:7]})")
        nm = dm[dm.ecosystem == "NEAR"]
        f12 = go.Figure()
        f12.add_scatter(x=nm.day, y=nm.all_devs, name="All active (>=1 commit, 28d)", line=dict(color=C["1"], width=2))
        f12.add_scatter(x=nm.day, y=nm.full_time_devs, name="Full-time (>=10 active days, 84d)", line=dict(color=C["3"], width=2))
        f12.add_scatter(x=nm.day, y=nm.exclusive_devs, name="Exclusive to NEAR", line=dict(color=C["2"], width=2))
        f12.update_layout(title=f"NEAR developers by commitment: casual contributors left, full-time held ({k['dev_full_time']} now vs {k['dev_full_time_1y_ago']} a year ago)")
    apth = T / "aggregators.csv"
    if apth.exists() and "xp_bridge_rank" in k:
        ag = pd.read_csv(apth)
        br = ag[ag.llama_category == "bridge_aggregator"].head(10).sort_values("total30d")
        colors = [C["1"] if "NEAR Intents" in n else "#b8b7b3" for n in br.displayName]
        f11 = go.Figure(go.Bar(x=br.total30d, y=br.displayName.str.replace(" (DefiLlama category: Bridge)", ""), orientation="h", marker_color=colors, marker_line_width=0,
                               text=[money(x) for x in br.total30d], textposition="outside", hovertemplate="%{y}: $%{x:,.0f}<extra></extra>"))
        f11.update_layout(title=f"30-day volume: NEAR Intents vs DefiLlama's bridge aggregators (rank {k['xp_bridge_rank']} of {k['xp_bridge_n']}; rank {k['xp_swap_rank']} of {k['xp_swap_n']} among swap aggregators)", margin=dict(l=200), xaxis_tickprefix="$")
    # tables
    def table(df, cols, fmt=None):
        fmt = fmt or {}
        h = "<table><thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cols) + "</tr></thead><tbody>"
        for _, r in df.iterrows():
            h += "<tr>" + "".join(f"<td>{html.escape('' if pd.isna(r[c]) else fmt.get(c, lambda x: str(x))(r[c]))}</td>" for c in cols) + "</tr>"
        return h + "</tbody></table>"
    be_v = be[be.deployment == "all_captured_revenue"]
    be_tab = table(be_v, ["issuance_scenario", "issuance_rate", "capture_scenario", "capture_rate", "breakeven_volume_usd_per_day", "coverage_at_current_volume", "volume_multiple_needed"],
                   {"issuance_rate": lambda x: f"{x:.2%}", "capture_rate": lambda x: f"{x:.1%}", "breakeven_volume_usd_per_day": lambda x: money(x, 0) + "/day",
                    "coverage_at_current_volume": lambda x: f"{x:.1%}", "volume_multiple_needed": lambda x: f"{x:.1f}x"})
    sc_tab = table(sc, ["scenario", "annual_volume_usd", "fee_rate_bps", "capture_rate", "annual_net_revenue_usd", "revenue_to_issuance", "revenue_multiple", "implied_market_cap_usd", "implied_price_usd", "implied_vs_today"],
                   {"annual_volume_usd": money, "capture_rate": lambda x: f"{x:.0%}", "annual_net_revenue_usd": money, "revenue_to_issuance": lambda x: f"{x:.2f}x",
                    "implied_market_cap_usd": money, "implied_price_usd": lambda x: f"${x:,.2f}", "implied_vs_today": lambda x: f"{x:.2f}x", "revenue_multiple": lambda x: f"{x:.0f}x"})
    comps_tab = table(comps, ["asset", "market_cap_usd", "chain_fees_30d", "chain_revenue_30d", "mcap_over_annualised_chain_fees", "mcap_over_annualised_chain_revenue"],
                      {"market_cap_usd": money, "chain_fees_30d": money, "chain_revenue_30d": money, "mcap_over_annualised_chain_fees": lambda x: f"{x:,.0f}x", "mcap_over_annualised_chain_revenue": lambda x: f"{x:,.0f}x"})
    led_tab = table(led, ["claim_id", "status", "claim", "observed", "limitation"])
    status_counts = led.status.value_counts().to_dict()
    tiles = [("NEAR price", f"${k['price_usd']:.2f}", f"market cap {money(k['market_cap_usd'])}"),
             ("Intents volume, 30d", money(k["intents_volume_30d"]), f"{money(k['intents_volume_30d']/30,0)}/day"),
             ("Gross fees, 30d", money(k["intents_fees_30d"]), f"{k['fee_rate_bps_30d']:.1f} bps of volume"),
             ("Captured revenue, 30d", money(k["intents_revenue_30d"]), f"capture {k['capture_30d']:.1%} (lifetime {k['capture_lifetime']:.1%})"),
             ("NEAR bought back, 30d", f"{k['buyback_near_30d']:,.0f}", f"{money(k['buyback_usd_30d'])}; wallet holds {k['buyback_wallet_balance_near']/1e6:.2f}M NEAR, 0 staked"),
             ("NEAR issued, 30d", f"{k['issued_near_30d']/1e6:.2f}M", f"{k['realized_issuance_annualised']:.2%} annualised"),
             ("Buyback coverage of issuance", f"{k['coverage_near_30d']:.1%}", "NEAR bought / NEAR issued, same 30 days"),
             ("Breakeven volume (2.5%)", money(ms["breakeven_measured_current_cap"], 0) + "/day", f"{money(ms['breakeven_measured_hsp029'],0)}/day at 1.6% (HSP-029 passed Nov 2; 1.6% reached ~2029)"),
             ("Staking ratio", f"{k['staking_ratio']:.1%}", f"{k['validators']} validators, Nakamoto {k['nakamoto_coefficient_1_3']}"),
             ("Claims ledger", " / ".join(str(status_counts.get(x, 0)) for x in ("PASS", "PARTIAL", "UNVERIFIABLE", "FAIL")), "PASS / PARTIAL / UNVERIFIABLE / FAIL")]
    tiles_html = "".join(f'<div class="tile"><div class="label">{html.escape(a)}</div><div class="value">{html.escape(b)}</div><div class="sub">{html.escape(c)}</div></div>' for a, b, c in tiles)
    sections = {
        "flywheel": ("Fee flywheel", "Volume → gross fees → revenue captured by NEAR → NEAR bought. Revenue is recognised when swept on-chain, so monthly totals are the comparable unit.",
                     f"{fig_html(f1)}{fig_html(f2)}<div class=\"grid2\">{fig_html(f3, 320)}{fig_html(f3b, 320)}</div>",
                     "reports/tables/intents_daily.csv, monthly.csv", "C04 C05 C06 C07 C16"),
        "issuance": ("Issuance vs buybacks", "NEAR terms, so price does not distort it. Bought NEAR sits in a multisig: not burned, not staked (ledger C02).",
                     f"{fig_html(f4)}{fig_html(f5, 300)}", "reports/tables/buybacks_daily.csv, network_daily.csv, monthly.csv", "C01 C02 C03 C08 C09"),
        "breakeven": ("Breakeven model", f"Volume per day at which captured revenue equals the value of new issuance. Inputs live in <code>params.yaml</code>; measured rows use the trailing-30d fee rate ({k['fee_rate_bps_30d']:.1f} bps) and capture ({k['capture_30d']:.1%}).",
                      f"{be_tab}<div class=\"grid2\">{fig_html(f6, 420)}{fig_html(f6b, 420)}</div>", "reports/tables/breakeven.csv, breakeven_sensitivity.csv, model_summary.json", "model identities in checks/test_model.py"),
        "network": ("Network fundamentals", "Base-layer activity and the security budget. Accounts are accounts, not people.",
                    f"{fig_html(f7, 300)}{fig_html(f7b, 300)}{fig_html(f8, 340)}", "reports/tables/network_daily.csv, validators.csv", "C10 C11 C15"),
        "signatures": ("Chain Signatures", "v1.signer is the MPC contract. Counts are calls, not value. Most of the demand is NEAR's own plumbing: the Intents bridge (omni.bridge, BTC and Zcash connectors) and FastAuth.",
                       fig_html(f9, 380) if f9 is not None else '<p class="note">no signer sample in this snapshot</p>', "reports/tables/signer_callers.csv", "C17"),
        "cross-protocol": ("Cross-protocol", "One volume definition (DefiLlama). Intents is filed by DefiLlama as a Bridge, so it is inserted into each aggregator list for ranking. Canonical bridges and CEX flows are not in these lists (paid endpoint).",
                           fig_html(f11, 400) if f11 is not None else '<p class="note">no aggregator data in this snapshot</p>', "reports/tables/aggregators.csv", "C18"),
        "developers": ("Developers", f"Electric Capital's open dataset counts public GitHub commits in repos mapped to each ecosystem. Private repos are invisible. Source: Electric Capital Open Dev Data, CC BY 4.0, snapshot {k.get('dev_as_of','')}. Ledger C19 is red: the all-developer count is down {k.get('dev_all_chg_1y', 0):+.0%} in a year while full-time is {k.get('dev_full_time_chg_1y', 0):+.0%}.",
                       (fig_html(f10, 380) if f10 is not None else '') + (fig_html(f12, 340) if f12 is not None else ''), "reports/tables/devs_peers.csv, devs_monthly.csv", "C19"),
        "valuation": ("Valuation and 2030 scenarios", "Chain-level gas fees and revenue from DefiLlama with one definition for all three. NEAR's product revenue (Intents) is in the tiles on the start page and is not in the chain row.",
                      f"{comps_tab}<div class=\"note\">2030 scenarios are arithmetic on the stated inputs, not forecasts. The bear row shows what a revenue-only valuation looks like if the flywheel stalls; it is deliberately uncomfortable.</div>{sc_tab}",
                      "reports/tables/comps.csv, scenarios_2030.csv", "none; these are our own numbers"),
        "ledger": ("Claims ledger", "Public claims re-tested against the snapshot. Full columns in <code>thesis/claims_ledger.csv</code>.", led_tab, "thesis/claims_ledger.csv", "all"),
        "predictions": ("Pre-registered predictions", "Three calls written on 2026-11-04 with dates and thresholds, frozen by hash in <code>thesis/PREDICTIONS.md</code>. Re-run <code>make check</code> after 2027-03-31 and each row turns HIT or MISS.",
                        table(pd.read_csv(T / "predictions.csv"), ["id", "call", "observed", "threshold", "settles", "status"]) if (T / "predictions.csv").exists() else "", "reports/tables/predictions.csv", "P1 P2 P3"),
    }
    order = ["index"] + list(sections)
    labels = {"index": "Start here", **{kk: v[0] for kk, v in sections.items()}}

    def nav(cur):
        return '<nav>' + "".join(f'<a href="{kk}.html"{" class=\"on\"" if kk == cur else ""}>{html.escape(labels[kk])}</a>' for kk in order) + '</nav>'

    head = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Toll Road: NEAR evidence dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
:root{{--bg:#fcfcfb;--ink:#0b0b0b;--muted:#52514e;--line:#e8e7e3;--accent:#2a78d6}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px 64px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:18px;margin:36px 0 8px;border-top:1px solid var(--line);padding-top:20px}}
.sub,.note{{color:var(--muted);font-size:13px}} .note{{margin:4px 0 12px}}
nav{{display:flex;flex-wrap:wrap;gap:4px 14px;margin:14px 0 6px;font-size:14px}} nav a{{color:var(--muted);text-decoration:none;padding:4px 0;border-bottom:2px solid transparent}} nav a.on{{color:var(--ink);border-color:var(--accent)}} nav a:hover{{color:var(--ink)}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin:18px 0}}
.tile{{border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:#fff}} .tile .label{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.tile .value{{font-size:22px;font-weight:600;margin:2px 0}} .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}} @media(max-width:860px){{.grid2{{grid-template-columns:1fr}}}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}} th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}} th{{color:var(--muted);font-weight:600}}
td:nth-child(2) {{white-space:nowrap}} .PASS{{color:#008300}} .FAIL{{color:#e34948}} .PARTIAL{{color:#c98500}} .UNVERIFIABLE{{color:#52514e}}
.verdict{{border-left:3px solid var(--accent);padding:4px 14px;margin:16px 0;background:#fff}}
</style></head><body><main>
<h1>Toll Road: does NEAR's fee switch pay for the chain?</h1>
<div class="sub">Snapshot {k['snapshot']} · data through {k['as_of_date']} · block {k['block_height']:,} · every number here is regenerated by <code>make report</code> from <code>data/snapshots/{k['snapshot']}/</code></div>"""
    foot = """<p class="sub">Sources: NearBlocks, NEAR RPC (FastNear), FastNear API, DefiLlama, CoinGecko, nearstats.org, revenue.near.org, Electric Capital Open Dev Data. Not investment advice.</p>
</main><script>document.querySelectorAll('td').forEach(td=>{if(['PASS','FAIL','PARTIAL','UNVERIFIABLE'].includes(td.textContent))td.classList.add(td.textContent)})</script></body></html>"""
    OUT.parent.mkdir(exist_ok=True)
    for name, (title, note, body, files, claims) in sections.items():
        (OUT.parent / f"{name}.html").write_text(head + nav(name) + f"<h2>{html.escape(title)}</h2><div class=\"note\">{note}</div>{body}"
                                                 + f"<p class=\"sub\">Tables: <code>{html.escape(files)}</code> · ledger rows: {html.escape(claims)}</p>" + foot)
    # start page: tiles, the verdict, and the evidence map
    verdict = (f"<div class=\"verdict\"><p><b>The mechanism is real and small.</b> In the last 30 days NEAR Intents moved {money(k['intents_volume_30d'])}, earned {money(k['intents_fees_30d'])} in fees, "
               f"and NEAR captured {money(k['intents_revenue_30d'])} of it ({k['capture_30d']:.0%}). {k['buyback_near_30d']:,.0f} NEAR was bought against {k['issued_near_30d']/1e6:.2f}M issued: coverage <b>{k['coverage_near_30d']:.1%}</b>. "
               f"Breakeven needs {money(ms['breakeven_measured_current_cap'],0)}/day of volume at 2.5% issuance ({money(ms['breakeven_measured_hsp029'],0)}/day at 1.6%), against {money(k['intents_volume_30d']/30,0)}/day today.</p>"
               f"<p>What is going right: Intents is the largest venue of its kind DefiLlama can see (rank {k.get('xp_bridge_rank','?')} of {k.get('xp_bridge_n','?')} bridge aggregators) and capture is rising. "
               f"What is going wrong: issuance outruns buybacks {k['issued_near_30d']/k['buyback_near_30d']:.0f}x, bought NEAR is held not retired, base-layer activity has fallen, and Electric Capital counts {k.get('dev_all','?')} active developers, down {abs(k.get('dev_all_chg_1y',0)):.0%} in a year. Both sides are in the ledger.</p></div>")
    emap = "<table><thead><tr><th>Question</th><th>Page</th><th>Table (reports/tables/)</th><th>Ledger rows</th></tr></thead><tbody>" + "".join(
        f"<tr><td>{html.escape(t)}</td><td><a href=\"{n}.html\">{html.escape(t)}</a></td><td><code>{html.escape(f)}</code></td><td>{html.escape(c)}</td></tr>" for n, (t, _, _, f, c) in sections.items()) + "</tbody></table>"
    index = head + nav("index") + f'<div class="tiles">{tiles_html}</div>' + verdict + "<h2>Evidence map</h2><div class=\"note\">Every page answers one question, cites the table it is drawn from and the ledger rows it supports. <code>make report</code> rebuilds all of it; <code>make check</code> re-tests the ledger.</div>" + emap + foot
    OUT.write_text(index)
    print(f"dashboard -> {OUT.parent}/ ({len(sections)+1} pages, index {OUT.stat().st_size/1e3:.0f} KB)")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--snapshot", default=None); ap.parse_args()
    build()


if __name__ == "__main__":
    main()
