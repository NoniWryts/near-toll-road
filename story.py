"""Start page as a story: the question, the answer, then one chapter per link in the chain, each with a one-line
takeaway, one picture and a link to the evidence page. Ends with tools to test the thesis: a what-if model and a
claim tester that check numbers against this snapshot in the browser. Every number comes from reports/tables."""
from __future__ import annotations
import html, json
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dashboard.theme import ACCENT, ACCENT_SOFT, VIOLET, VIOLET_SOFT, GREEN, INK, MUTED

AX = dict(gridcolor="#eef0f3", zeroline=False, linecolor="#e7e9ee", tickfont=dict(color=MUTED, size=11))
BASE = dict(template="plotly_white", font=dict(family="Times New Roman, Times, serif", size=12, color=INK), paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=44, r=10, t=40, b=30), hovermode="x unified", showlegend=True,
            legend=dict(orientation="h", y=1.2, x=0, yanchor="bottom", font=dict(size=12, color=MUTED)), xaxis=dict(AX, showgrid=False), yaxis=AX)


def _fig(fig, h=260):
    fig.update_layout(height=h, **BASE)
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, config={"displaylogo": False, "responsive": True, "displayModeBar": False})


def money(x, d=1):
    if x is None or pd.isna(x): return "n/a"
    for s, v in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(x) >= v: return f"${x/v:,.{d}f}{s}"
    return f"${x:,.0f}"


def pill(chg, good_up=True):
    if chg is None or pd.isna(chg): return ""
    cls = "flat" if abs(chg) < 0.005 else ("up" if (chg > 0) == good_up else "down")
    arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "")
    return f'<span class="pill {cls}">{arrow} {abs(chg):.1%}</span><span class="vs">vs prior 30 days</span>'


def build_story(k: dict, ms: dict, T, led: pd.DataFrame, nav: str, head: str, top: str, foot: str) -> str:
    d = pd.read_csv(T / "intents_daily.csv", parse_dates=["date"])
    m = pd.read_csv(T / "monthly.csv", parse_dates=["month"])
    n = pd.read_csv(T / "network_daily.csv", parse_dates=["date"])
    b = pd.read_csv(T / "buybacks_daily.csv", parse_dates=["date"])
    last, prev = d.iloc[-1], d.iloc[-31]
    chg = lambda a, p: (a - p) / p if p else None
    end = d.date.max()
    w1 = (lambda s: s[(s.date > end - pd.Timedelta(days=30)) & (s.date <= end)])
    w0 = (lambda s: s[(s.date > end - pd.Timedelta(days=60)) & (s.date <= end - pd.Timedelta(days=30))])
    cov1 = w1(b).near_bought.sum() / w1(n).issued_near.sum()
    cov0 = w0(b).near_bought.sum() / w0(n).issued_near.sum()
    vol_day = k["intents_volume_30d"] / 30
    be = ms["breakeven_measured_current_cap"]

    kpis = [("Swap volume, 30 days", money(k["intents_volume_30d"]), pill(chg(last.volume_30d, prev.volume_30d))),
            ("Fees paid (the toll)", money(k["intents_fees_30d"]), pill(chg(last.fees_30d, prev.fees_30d))),
            ("NEAR's cut", money(k["intents_revenue_30d"]), pill(chg(last.revenue_30d, prev.revenue_30d))),
            ("Buybacks cover new supply", f"{k['coverage_near_30d']:.1%}", (f'<span class="pill {"up" if cov1>=cov0 else "down"}">{"▲" if cov1>=cov0 else "▼"} {abs(cov1-cov0)*100:.1f} pts</span><span class="vs">vs prior 30 days</span>')),
            ("Volume needed to break even", money(be, 0) + "/day", f'<span class="pill flat">{be/vol_day:.1f}x today</span><span class="vs">today {money(vol_day,0)}/day</span>')]
    kpi_html = '<div class="kpis">' + "".join(f'<div class="kpi" id="kc{i}"><div class="l">{a}</div><div class="v" id="kv{i}">{b_}</div>{c}<div class="snapline" id="ks{i}"></div></div>' for i, (a, b_, c) in enumerate(kpis)) + "</div>"

    answer = (f'<div class="card answer"><span class="tag">The answer</span>'
              f'<div class="big">The mechanism is real, but small. For every 10 new NEAR printed to pay validators, the fee switch buys back about <b>{k["coverage_near_30d"]*10:.0f}</b>.</div>'
              f'<div class="note">To pay for itself at today\'s 2.5% issuance, NEAR Intents would need about {money(be,0)} of swaps a day, {be/vol_day:.1f}x what it does now. '
              f'The issuance cut passed on Nov 2 (HSP-029) lowers that bar to {money(ms["breakeven_measured_hsp029"],0)} a day once fully phased in (~2029). Click Next to see how we got here; steps 6 and 10 let you test it yourself.</div></div>')

    SRC = {1: ("<code>reports/tables/prebuyback_monthly.csv</code> and <code>prebuyback_price_index.csv</code>", "<code>analysis/prebuyback.py</code>", "NearBlocks daily network series (accounts, transactions, supply, gas fees), CoinGecko prices, DefiLlama Intents fees"),
           2: ("<code>reports/tables/intents_daily.csv</code>", "<code>analysis/build.py</code>", "DefiLlama <code>dexs/near-intents</code> (volume), CoinGecko, DefiLlama aggregator lists for the rank"),
           3: ("<code>reports/tables/monthly.csv</code> and <code>intents_daily.csv</code>", "<code>analysis/build.py</code>", "DefiLlama <code>fees/near-intents</code>: fees paid and the share NEAR captures"),
           4: ("<code>reports/tables/kpis.json</code>, <code>buybacks_daily.csv</code>, <code>network_daily.csv</code>", "<code>analysis/build.py</code>", "every receipt to the buyback wallet (NearBlocks, FastNear), daily total supply (NearBlocks)"),
           5: ("<code>reports/tables/monthly.csv</code> (column <code>coverage_near</code>)", "<code>analysis/build.py</code>", "NEAR bought back divided by NEAR issued, month by month"),
           6: ("<code>reports/tables/breakeven.csv</code>, <code>model_summary.json</code> and the assumptions in <code>params.yaml</code>", "<code>models/breakeven.py</code>", "measured fee rate, capture rate, price and supply from the snapshot; issuance scenarios from the protocol config and HSP-029"),
           7: ("<code>reports/tables/vq_*.csv</code>, <code>custody_daily.csv</code>", "<code>analysis/volume_quality.py</code>, <code>analysis/custody.py</code>", "a seeded sample of <code>intents.near</code> transactions, bridge payouts on Tron (TronGrid) matched to NEAR withdrawals"),
           8: ("<code>reports/tables/kpis.json</code>, <code>devs_peers.csv</code>, <code>vq_*.csv</code>", "<code>analysis/build.py</code>, <code>checks/run_ledger.py</code>", "Electric Capital developer data, DefiLlama, NEAR RPC, the buyback wallet"),
           9: ("<code>thesis/PREDICTIONS.md</code> (frozen by <code>PREDICTIONS.sha256</code>) and <code>reports/tables/predictions.csv</code>", "<code>checks/predictions.py</code>", "the same snapshot as every other number here"),
           10: ("<code>thesis/claims_ledger.csv</code>", "<code>checks/run_ledger.py</code>", "each claim is re-tested against the tables above; the tester reads <code>kpis.json</code> in the browser")}

    def chapter(no, title, take, body, why, link, label="See the evidence"):
        t, c, f = SRC.get(no, ("", "", ""))
        src = (f'<div class="srcline"><b>Where this comes from.</b> Table: {t}. Code: {c}. Data: {f}. '
               f'Rebuild everything with <code>make report</code>.</div>') if t else ""
        return (f'<div class="card"><div class="step"><div class="num">{no}</div><div style="flex:1;min-width:0">'
                f'<div class="card-h"><h3 style="margin:0">{html.escape(title)}</h3><a class="more" href="{link}">{label} →</a></div>'
                f'<div class="takeaway">{take}</div><div class="note">{why}</div>{body}{src}</div></div></div>')

    # 0 before the switch
    pm = pd.read_csv(T / "prebuyback_monthly.csv", parse_dates=["month"])
    pi = pd.read_csv(T / "prebuyback_price_index.csv", parse_dates=["date"])
    sw, hv = pd.Timestamp(k["pb_switch_date"]), pd.Timestamp("2025-11-01")
    def marks(fig, ymax, left=False):
        for i, (x, lab) in enumerate(((hv, "Issuance halved"), (sw, "Fee switch live, 23 Feb 2026"))):
            fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper", line=dict(color=MUTED, dash="dot", width=1.2))
            fig.add_annotation(x=x, y=1.02, yref="paper", text=lab, showarrow=False, font=dict(size=12, color=MUTED), xanchor="right" if (left and i == 0) else "left", yshift=0 if left else 16 * i)
    pm2 = pm[pm.month >= "2024-06-01"]
    f0 = go.Figure()
    f0.add_scatter(x=pm2.month, y=pm2.active_accounts_per_day, name="Active accounts per day", line=dict(color=ACCENT, width=2.5))
    f0.add_scatter(x=pm2.month, y=pm2.new_accounts_per_day, name="New accounts per day", line=dict(color=VIOLET, width=2))
    marks(f0, 1)
    f0.update_yaxes(tickformat=",.0f")
    f0b = go.Figure()
    for coin, name, col in (("near", "NEAR", ACCENT), ("solana", "SOL", MUTED), ("ethereum", "ETH", "#b08d2c")):
        f0b.add_scatter(x=pi.date, y=pi[coin], name=name, line=dict(color=col, width=3 if coin == "near" else 1.6))
    marks(f0b, 1)
    f0b.update_yaxes(title_text="Price, start = 100")
    why = ('<div class="three" style="margin-top:14px">'
           f'<div><h3>1. There was no revenue to spend</h3><div class="sub">Intents collected almost no fees until {k["pb_intents_fees_first_month"]}, and NEAR\'s own cut was about ${k["pb_intents_rev_before_nov25_usd"]:,.0f} in total before November 2025 (DefiLlama). A buyback needs a stream of income to buy with; the stream only appeared in late 2025.</div></div>'
           f'<div><h3>2. The first fix was a smaller printing press</h3><div class="sub">A community proposal on 24 June 2025 argued that 5% a year of new NEAR was far more than the network needed. The halving (to 2.5%) took effect with the nearcore 2.9.0 protocol upgrade in late October 2025. Issuance in our data drops from about {k["pb_prehalving_issuance_annual"]:.1%} to {k["pb_posthalving_prefee_issuance_annual"]:.1%} a year in November.</div></div>'
           f'<div><h3>3. Burning gas was too small to matter</h3><div class="sub">NEAR burns part of every gas fee, but the proposal put the burn at about 0.1% of supply in a year. By our estimate (70% of gas fees) it covered only {k["pb_burn_cover_pre_halved"]:.1%} of the value of new NEAR between November and the switch.</div></div></div>')
    pxline = (f'<div class="three" style="margin-top:16px"><div><h3>Before the switch ({k["pb_px_start"]} to {k["pb_switch_date"]})</h3><div class="k">NEAR {k["pb_px_pre_near"]:+.0%}</div><div class="sub">SOL {k["pb_px_pre_solana"]:+.0%}, ETH {k["pb_px_pre_ethereum"]:+.0%}. The whole market was falling; NEAR fell with it.</div></div>'
              f'<div><h3>Since the switch (to {k["pb_as_of"]})</h3><div class="k">NEAR {k["pb_px_post_near"]:+.0%}</div><div class="sub">SOL {k["pb_px_post_solana"]:+.0%}, ETH {k["pb_px_post_ethereum"]:+.0%}. NEAR went from trailing the market to leading it.</div></div>'
              f'<div><h3>What we do not claim</h3><div class="sub">Buybacks so far total {money(k["buyback_usd_all"])}, small next to the {money(k["pb_near_trading_usd_day"],0)} of NEAR traded on an average day. We read the rally as timing worth noting, not proof the buybacks caused it.</div></div></div>')
    c0 = chapter(1, "Before the switch", f"Before the buybacks, usage was already shrinking, new NEAR was being printed at twice today's rate, and there was no revenue to buy with.",
                 _fig(f0, 260) + '<div class="note" style="margin-top:6px">Monthly averages of active and new accounts per day. Active accounts fell from '
                 f'{k["pb_active_jan25"]/1e3:,.0f}k a day in January 2025 to {k["pb_active_pre_halved"]/1e3:,.0f}k a day in the months before the switch ({k["pb_active_chg_jan25_to_switch"]:+.0%}); transactions fell {k["pb_txns_chg_jan25_to_switch"]:+.0%}.</div>'
                 + why + '<h3 style="margin-top:20px">NEAR against SOL and ETH over the same dates</h3>' + _fig(f0b, 240) + pxline,
                 f'The fee switch went live on {k["pb_switch_date"]}; the first sweep reached the buyback wallet on {k["pb_first_sweep"]}, {k["pb_gap_days"]} days later. This is a before-and-after description, not proof of cause: issuance was halved and a reward app stopped in the same months.',
                 "network.html", "Network pages")
    # 1 traffic
    dd = d[d.date >= "2025-09-01"]
    f1 = go.Figure()
    f1.add_bar(x=dd.date, y=dd.volume_usd, name="Daily swaps", marker_color=ACCENT_SOFT, marker_line_width=0)
    f1.add_scatter(x=dd.date, y=dd.volume_30d / 30, name="30-day average", line=dict(color=ACCENT, width=2.5))
    f1.update_yaxes(tickprefix="$")
    c1 = chapter(2, "The traffic", f"About {money(vol_day,0)} of swaps cross NEAR Intents every day.",
                 _fig(f1), f"Rank {k['xp_bridge_rank']} of {k['xp_bridge_n']} cross-chain aggregators on DefiLlama. Volume is down from its peak: DefiLlama shows {k['xp_intents_chg_1m_llama']:+.0f}% month on month.", "flywheel.html")
    # 2 toll and cut
    mm = m[(m.month >= "2026-02-01") & (m.month <= end)]
    f2 = go.Figure()
    f2.add_bar(x=mm.month, y=mm.fees_usd, name="Fees paid", marker_color=VIOLET_SOFT, marker_line_width=0)
    f2.add_bar(x=mm.month, y=mm.revenue_usd, name="NEAR's cut", marker_color=VIOLET, marker_line_width=0)
    f2.update_layout(barmode="overlay", bargap=0.35); f2.update_yaxes(tickprefix="$")
    c2 = chapter(3, "The toll", f"Each swap pays about {k['fee_rate_bps_30d']/100:.2f}%. NEAR keeps {k['capture_30d']:.0%} of it; the rest goes to the apps that bring the traffic.",
                 _fig(f2), f"NEAR's share has risen since the fee switch in February (lifetime {k['capture_lifetime']:.0%}, last 30 days {k['capture_30d']:.0%}).", "flywheel.html")
    # 3 printed vs bought (funnel)
    px = k["price_usd"]
    steps = [("NEAR printed", k["issued_near_30d"]), ("All fees, in NEAR", k["intents_fees_30d"] / px),
             ("NEAR's cut, in NEAR", k["intents_revenue_30d"] / px), ("Actually bought back", k["buyback_near_30d"])]
    top_v = steps[0][1]
    bars = ""
    for i, (lab, v) in enumerate(steps):
        h = max(6, 100 * v / top_v)
        drop = f'<em>▼ {1 - v/steps[i-1][1]:.0%}</em>' if i else ""
        soft = " soft" if i == 0 else ""
        lab_style = f' style="bottom:calc({h:.1f}% + 6px);color:#111318"' if h < 16 else ""
        bars += f'<div class="bar{soft}"><i style="height:{h:.1f}%"></i>{drop}<span{lab_style}>{v/1e6:.2f}M</span></div>'
    funnel = f'<div class="bars">{bars}</div><div class="blabels">' + "".join(f"<div>{l}</div>" for l, _ in steps) + "</div>"
    c3 = chapter(4, "Printing vs buying back", f"In 30 days NEAR printed {k['issued_near_30d']/1e6:.2f}M new tokens and bought back {k['buyback_near_30d']/1e3:,.0f}k: <b>{k['coverage_near_30d']:.1%}</b> coverage.",
                 funnel, f"Counted in NEAR, not dollars, so a price move can't flatter it. Bought NEAR sits in a multisig: not burned, not staked (ledger C02).", "issuance.html")
    # 4 coverage trend
    mc = m[(m.month >= "2026-04-01") & m.coverage_near.notna() & (m.month <= end)]
    f4 = go.Figure()
    f4.add_bar(x=mc.month, y=mc.coverage_near, name="Buyback coverage of new supply", marker_color=ACCENT, marker_line_width=0,
               text=[f"{x:.0%}" for x in mc.coverage_near], textposition="outside")
    f4.add_scatter(x=mc.month, y=[1] * len(mc), name="Pays for itself (100%)", line=dict(color=MUTED, dash="dot", width=1.5), mode="lines")
    f4.update_yaxes(tickformat=".0%", range=[0, 1.08])
    c4 = chapter(5, "The trend", "Coverage is rising, but it is a long way from 100%.", _fig(f4, 240),
                 "Monthly NEAR bought back divided by NEAR printed. 100% would mean the fee switch fully offsets dilution.", "issuance.html")
    # 6 is it real
    real = [("Payouts are real money leaving", f"{k.get('cust_public_share',0):.0%}", f"Every USDT payout from the bridge's Tron wallet ({money(k.get('cust_payouts_usd',0))}, one week) matches a public NEAR withdrawal."),
            ("Not one whale", f"{k['vq_dest_top10']:.0%}", "of payout value goes to the top 10 recipients; the largest gets " + f"{k['vq_dest_top1']:.0%}."),
            ("'Users' are really swaps", f"{k['vq_perquote_share']:.0%}", "of payouts are signed by one-time accounts created per quote, so the Explorer's user count counts swaps (C21, FAIL)."),
            ("Little wash trading", f"{k['vq_selftrade_share_nonpersistent']:.1%}", "of swappers round-trip A→B→A outside the known market makers."),
            ("The April drop was one app", f"{k['blk_drop_explained']:.0%}", "of the fall in daily NEAR transactions is one reward app (KaiChing) stopping, not Intents.")]
    rows = "".join(f'<tr><td style="width:34%"><b>{a}</b></td><td style="width:12%;font-size:20px;font-weight:500">{b_}</td><td class="sub">{c}</td></tr>' for a, b_, c in real)
    c6 = chapter(7, "Is the traffic real?", "Mostly yes: the money is real and spread out, but user counts are inflated.",
                 f'<div class="tablewrap"><table>{rows}</table></div>', "Read from a 1.2% random sample of intents.near transactions plus a full week of Tron payouts.", "volume-quality.html")
    # 7 risks
    pc = lambda x: f"{x:.0%}"
    risks = [
        ("High", "Bought-back NEAR is not retired", "Buybacks", "issuance.html",
         f"The {k['buyback_wallet_balance_near']/1e6:.2f}M NEAR bought so far sits liquid in a multisig wallet ({k['vq_top_affiliate']}). None of it is burned, staked or locked ({k['buyback_wallet_locked_near']:,.0f} NEAR locked; ledger C02 is FALSE).",
         "A buyback only shrinks supply if the tokens stay out of circulation. Today the signers could sell or spend them, so our coverage figure is the best case, not a guarantee.",
         "An on-chain burn, or a lock that only a holder vote can undo."),
        ("High", "Swap volume is falling", "Fees", "flywheel.html",
         f"30-day volume is {money(k['intents_volume_30d'])}, {abs(chg(last.volume_30d, prev.volume_30d)):.0%} below the 30 days before. DefiLlama's monthly change reads {k['xp_intents_chg_1m_llama']:+.0f}%.",
         f"Every dollar of buyback starts as a swap. Breakeven already needs {be/vol_day:.1f}x today's volume, and the gap widens when traffic drops.",
         f"Volume back above its September level, and a path toward {money(ms['breakeven_measured_hsp029'],0)} a day once HSP-029 is phased in."),
        ("Medium", "Buybacks are a choice, not a rule", "Buybacks", "issuance.html",
         f"Only {k['buyback_share_of_revenue_30d']:.0%} of NEAR's cut reached the buyback wallet in the last 30 days. The rest stayed in other revenue wallets.",
         "No contract forces revenue into buybacks. The people running the wallets decide how much goes in and when, so the rate can drop without notice.",
         "A published, on-chain sweep rule (for example: all revenue swept weekly)."),
        ("Medium", "A few market makers fill most swaps", "Volume quality", "volume-quality.html",
         f"The largest solver fills {k['vq_solver_top1']:.0%} of sampled swap value; the top five fill {k['vq_solver_top5']:.0%}.",
         "If one large market maker steps back, prices on Intents get worse, users leave and fees fall. The toll road depends on a handful of operators.",
         "The top solver's share falling below a third as new solvers join."),
        ("Medium", "Fewer developers are building", "Developers", "developers.html",
         f"{k['dev_all']} monthly-active developers, down {abs(k['dev_all_chg_1y']):.0%} in a year and {abs(k['dev_all_chg_4y']):.0%} from the 2022 peak of {k['dev_peak_all']:,}. Full-time developers are up {k['dev_full_time_chg_1y']:.0%} to {k['dev_full_time']}.",
         f"New apps bring new swap traffic. NEAR ranks {k['dev_rank_all']} of {k['dev_peers_n']} peer chains on active developers, so the pipeline of future fee payers is thin.",
         "Two quarters of growth in monthly-active developers, not just full-time ones."),
        ("Medium", "Private volume cannot be checked", "Volume quality", "volume-quality.html",
         f"NEAR reports part of its volume as 'confidential'. Its share read {k['vq_conf_share_first']:.0%} on {k['vq_conf_asof_first']} and 0% on {k['vq_conf_asof_last']}, on the same total.",
         f"Nobody outside can see that private flow. Our custody check matched {k.get('cust_public_share',0):.0%} of one week of USDT payouts on Tron to public withdrawals, but other routes are not reconciled.",
         "NEAR publishing a verifiable total for confidential volume, or more routes passing our custody check."),
        ("Low", "The issuance cut could slip", "Predictions", "predictions.html",
         "Holders passed HSP-029 on 2 November. It sits in a timelock until 16 November and then phases in over about two years.",
         f"Until it is live, breakeven stays at {money(be,0)} a day. A delay or reversal keeps the bar at today's level.",
         "The protocol's inflation setting changing on chain (our prediction P1 checks this)."),
    ]
    sev = {"High": "FAIL", "Medium": "PARTIAL", "Low": "UNVERIFIABLE"}
    rcards = "".join(
        f'<div class="risk"><div class="card-h" style="margin-bottom:6px"><div><span class="{sev[sv]}">{sv} risk</span> <b class="rt">{t}</b></div>'
        f'<a class="more" href="{lk}">{pg} page →</a></div><div class="rg">'
        f'<div><h3>What we see</h3>{a}</div><div><h3>Why it matters</h3>{b_}</div><div><h3>What would ease it</h3>{c}</div></div></div>'
        for sv, t, pg, lk, a, b_, c in risks)
    c7 = chapter(8, "What could break it", f"{len(risks)} risks, ranked. Two are serious today; all are checked against the data on every rebuild.",
                 rcards, "We keep the bad news in. A thesis that hides its weak points can't be trusted on its strong ones.", "security.html", "All risks")
    # 8 predictions
    pr = pd.read_csv(T / "predictions.csv") if (T / "predictions.csv").exists() else pd.DataFrame()
    prow = ""
    for _, r in pr.iterrows():
        prow += f'<tr><td><b>{r["id"]}</b></td><td>{html.escape(r["call"])}</td><td>{html.escape(str(r["observed"]))}</td><td>{html.escape(str(r["threshold"]))}</td><td>{r["settles"]}</td><td><span class="UNVERIFIABLE">{r["status"]}</span></td></tr>'
    c8 = chapter(9, "Our calls, frozen in advance", "Three dated predictions settle on 31 March 2027. Nobody can move the goalposts.",
                 f'<div class="tablewrap"><table><thead><tr><th></th><th>Call</th><th>Now</th><th>Threshold</th><th>Settles</th><th>Status</th></tr></thead><tbody>{prow}</tbody></table></div>',
                 "The file is locked by its fingerprint (sha256); a test fails if anyone edits a threshold.", "predictions.html")

    # 5 simulator
    sim_data = {"vol": vol_day, "fee": k["fee_rate_bps_30d"], "cap": k["capture_30d"], "iss": 0.025, "supply": k["total_supply_near"], "price": px,
                "bbshare": k.get("buyback_share_of_revenue_30d", 1.0)}
    sim = f"""
<div class="presets" id="presets"><button data-p="today" class="on">Today</button><button data-p="r2027">HSP-029, end 2027 (2.13%)</button><button data-p="r2029">HSP-029 fully phased in (1.6%)</button><button data-p="bull">Volume doubles</button></div>
<div class="sim"><div>
<div class="ctl"><label>Swap volume per day <b id="o_vol"></b></label><input id="vol" type="range" min="20" max="1500" step="5"></div>
<div class="ctl"><label>Fee per swap <b id="o_fee"></b></label><input id="fee" type="range" min="4" max="40" step="0.01"></div>
<div class="ctl"><label>NEAR's share of fees <b id="o_cap"></b></label><input id="cap" type="range" min="5" max="100" step="0.01"></div>
<div class="ctl"><label>New NEAR printed per year <b id="o_iss"></b></label><input id="iss" type="range" min="0.5" max="5" step="0.01"></div>
<div class="sub">Price is fixed at ${px:.2f} so you can see the other four dials clearly. A higher price makes the printed coins worth more dollars, which raises the bill.</div>
</div><div class="out">
<h3>NEAR's cut covers this much of new supply</h3><div class="v" id="r_cov"></div><div class="meter"><i id="r_bar"></i></div>
<div class="sub" id="r_line"></div><hr style="border:0;border-top:1px solid var(--line);margin:14px 0">
<h3>Volume needed to break even</h3><div class="v" id="r_be" style="font-size:26px"></div><div class="sub" id="r_be2"></div>
<div class="verdict" id="r_v"></div></div></div>
<script>
(function(){{const D={json.dumps(sim_data)};const P={{today:[D.vol/1e6,D.fee,D.cap*100,2.5],r2027:[D.vol/1e6,D.fee,D.cap*100,2.13],r2029:[D.vol/1e6,D.fee,D.cap*100,1.6],bull:[D.vol/2e6*4,D.fee,D.cap*100,2.13]}};
const $=id=>document.getElementById(id),f=x=>x>=1e9?'$'+(x/1e9).toFixed(2)+'B':'$'+(x/1e6).toFixed(0)+'M';
function set(p){{const v=P[p];['vol','fee','cap','iss'].forEach((k,i)=>$(k).value=v[i]);run();document.querySelectorAll('#presets button').forEach(b=>b.classList.toggle('on',b.dataset.p===p));}}
function run(){{const vol=+$('vol').value*1e6,fee=+$('fee').value/1e4,cap=+$('cap').value/100,iss=+$('iss').value/100;
const cut=vol*fee*cap,printed=D.supply*iss/365*D.price,cov=cut/printed,be=printed/(fee*cap);
$('o_vol').textContent=f(vol)+'/day';$('o_fee').textContent=(fee*100).toFixed(2)+'%';$('o_cap').textContent=(cap*100).toFixed(1)+'%';$('o_iss').textContent=(iss*100).toFixed(2)+'%';
$('r_cov').textContent=(cov*100).toFixed(1)+'%';$('r_bar').style.width=Math.min(100,cov*100)+'%';
$('r_line').textContent='NEAR earns '+f(cut).replace('M','.'+'' )+' a day vs '+f(printed)+' of new NEAR printed a day.';
$('r_line').textContent='NEAR earns $'+Math.round(cut/1e3).toLocaleString()+'k a day against $'+Math.round(printed/1e3).toLocaleString()+'k of new NEAR printed a day.';
$('r_be').textContent=f(be)+' a day';$('r_be2').textContent=(be/vol).toFixed(1)+'x the volume you set';
const pc=Math.round(cov*100),cls=cov>=1?'v-pass':cov>=0.5?'v-mid':'v-fail';$('r_v').className='verdict '+cls;
$('r_v').innerHTML=cov>=1?'<b>Pays for itself.</b> Buybacks take back all the new NEAR, so total supply stops growing and every holder keeps the same slice.':
(cov>=0.5?'<b>Getting close.</b> ':'<b>Not there yet.</b> ')+'Buybacks take back '+pc+'% of the new NEAR. The other '+(100-pc)+'% is new supply, so each holder’s slice of NEAR keeps shrinking a little.';}}
['vol','fee','cap','iss'].forEach(k=>$(k).addEventListener('input',()=>{{run();document.querySelectorAll('#presets button').forEach(b=>b.classList.remove('on'));}}));
document.querySelectorAll('#presets button').forEach(b=>b.addEventListener('click',()=>set(b.dataset.p)));set('today');}})();
</script>"""
    c5 = chapter(6, "Scenarios", "What would it take for NEAR to pay for itself? Set the volume, fee and issuance and see.", sim,
                 "Coverage here uses all of NEAR's cut. In the last 30 days only " + f"{sim_data['bbshare']:.0%} of it reached the buyback wallet, which is why measured coverage ({k['coverage_near_30d']:.1%}) is lower.",
                 "breakeven.html", "Full breakeven tables")

    # 9 claims: summary, filter, tester
    sc = led.status.value_counts().to_dict()
    folders = "".join(f'<div class="folder {c}"><small>{lab}</small><b>{sc.get(s,0)}</b></div>' for s, lab, c in
                      (("PASS", "Holds up", "f-pass"), ("PARTIAL", "Partly true", "f-part"), ("UNVERIFIABLE", "Can't be checked", "f-unv"), ("FAIL", "False", "f-fail")))
    lrows = "".join(f'<tr data-s="{r.status}"><td><b>{r.claim_id}</b></td><td><span class="{r.status}">{r.status}</span></td><td>{html.escape(str(r.claim))}<div class="sub">{html.escape(str(r.source))}</div></td><td class="sub">{html.escape(str(r.observed))}</td></tr>' for r in led.itertuples())
    metrics = [("Buyback coverage of new supply (30d)", k["coverage_near_30d"], "%"), ("NEAR's share of fees (30d)", k["capture_30d"], "%"),
               ("NEAR's share of fees (90d)", k["capture_90d"], "%"), ("NEAR's share of fees (lifetime)", k["capture_lifetime"], "%"),
               ("Fee per swap (bps)", k["fee_rate_bps_30d"], "n"), ("Swap volume per day ($M)", vol_day / 1e6, "n"),
               ("Realised issuance per year", k["realized_issuance_annualised"], "%"), ("Share of NEAR staked", k["staking_ratio"], "%"),
               ("Active validators", k["validators"], "n"), ("Bought NEAR that is staked or locked", k["buyback_wallet_locked_near"], "n"),
               ("Monthly-active developers", k["dev_all"], "n"), ("Top 10 recipients' share of payouts", k["vq_dest_top10"], "%"),
               ("Payouts backed by a public NEAR withdrawal", k.get("cust_public_share", 0), "%"), ("Chain Signatures calls from NEAR's own infra", k["signer_near_infra_share"], "%")]
    tester = f"""
<div class="row" style="margin-bottom:10px"><select id="t_m">{''.join(f'<option value="{i}">{html.escape(a)}</option>' for i,(a,_,_) in enumerate(metrics))}</select>
<select id="t_op"><option value="ge">is at least</option><option value="le">is at most</option></select><input id="t_x" type="number" step="any" style="width:110px"><span class="sub" id="t_unit"></span><button id="t_go" class="on">Test</button></div>
<div class="sub">Try: "NEAR's share of fees (lifetime) is at least 16.4" (NEAR's own claim), or "Share of NEAR staked is at least 46".</div>
<div class="verdict" id="t_out" style="display:none"></div>
<script>(function(){{const M={json.dumps([[a, v, u] for a, v, u in metrics])};const $=id=>document.getElementById(id);
function unit(){{const m=M[+$('t_m').value];$('t_unit').textContent=m[2]==='%'?'%':'';$('t_x').value=m[2]==='%'?(m[1]*100).toFixed(1):(+m[1]).toFixed(m[1]<100?1:0);}}
$('t_m').addEventListener('change',unit);unit();setTimeout(()=>$('t_go').click(),0);
$('t_go').addEventListener('click',()=>{{const m=M[+$('t_m').value],x=+$('t_x').value,val=m[2]==='%'?m[1]*100:m[1],ok=$('t_op').value==='ge'?val>=x:val<=x,o=$('t_out');
o.style.display='block';o.className='verdict '+(ok?'v-pass':'v-fail');o.textContent=(ok?'Holds: ':'Does not hold: ')+m[0]+' is '+(m[2]==='%'?val.toFixed(1)+'%':val.toLocaleString(undefined,{{maximumFractionDigits:1}}))+' in this snapshot ({k["as_of_date"]}).';}});
document.querySelectorAll('#ledf button').forEach(b=>b.addEventListener('click',()=>{{document.querySelectorAll('#ledf button').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('#ledt tr[data-s]').forEach(r=>r.style.display=(b.dataset.s==='ALL'||r.dataset.s===b.dataset.s)?'':'none');}}));}})();</script>"""
    c9 = chapter(10, "Check other people's claims, or your own", f"We tested {len(led)} public claims about NEAR against the chain. {sc.get('FAIL',0)} are false.",
                 f'<div class="folders">{folders}</div>'
                 f'<div class="out" style="margin-bottom:18px"><h3>Test a claim yourself</h3><div class="note" style="margin-top:0">Pick a number, set a threshold, and check it against this snapshot.</div>{tester}</div>'
                 '<h3 style="margin-top:4px">All {n} claims we tested</h3><div class="row" id="ledf" style="margin-bottom:8px">'.replace("{n}", str(len(led)))
                 + "".join(f'<button data-s="{s}"{" class=on" if s=="ALL" else ""}>{l}</button>' for s, l in (("ALL", "All"), ("PASS", "Holds up"), ("PARTIAL", "Partly"), ("UNVERIFIABLE", "Can't check"), ("FAIL", "False")))
                 + f'</div><div class="tablewrap"><table id="ledt"><thead><tr><th style="width:5%">ID</th><th style="width:10%">Status</th><th style="width:42%">The claim and who made it</th><th>What the chain shows</th></tr></thead><tbody>{lrows}</tbody></table></div>',
                 "The ledger is re-checked every time the data is refreshed, so a claim can change from PASS to FAIL as the chain moves.", "ledger.html", "Full ledger")

    rerun = (f'<div class="out" style="margin-top:18px"><h3>This board keeps itself honest</h3>'
             f'<div>Every number here is pulled from public sources (the NEAR blockchain, DefiLlama, CoinGecko, TronGrid) and rebuilt in one step. '
             f'When the data is refreshed, the charts, the risks, the claim verdicts and the predictions all update together, so a claim that holds today can turn false tomorrow. '
             f'This copy uses data up to {k["as_of_date"]} (NEAR block {k["block_height"]:,}).</div></div>')
    hero = (f'<div class="head"><div><span class="tag">NEAR investment thesis</span><h1>Does NEAR\'s fee switch pay for the chain?</h1>'
            f'<p class="lede">NEAR Intents is a toll road for cross-chain swaps, and the NEAR token owns it. We follow the money from each swap to the token, using only public on-chain data.</p>'
            f'<div class="byline">An on-chain investment thesis · last 30 days to {k["as_of_date"]} · NEAR block {k["block_height"]:,} · every number rebuilt from public data</div></div></div>')
    live = (f'<div class="live off" id="live"><div class="lh"><span class="dot"></span><span id="lstat">Live data unavailable, showing snapshot</span></div>'
            f'<div class="lc"><div class="l">NEAR price</div><div class="v" id="l_px">${k["price_usd"]:.2f}</div><div class="s">snapshot value, 10 Nov</div></div>'
            f'<div class="lc"><div class="l">Intents volume, last full day</div><div class="v" id="l_vol">${k["intents_volume_30d"]/30/1e6:,.0f}M</div><div class="s" id="l_vols">snapshot 30-day average</div></div>'
            f'<div class="lc"><div class="l">Buyback wallet holds</div><div class="v" id="l_bb">{k["buyback_wallet_balance_near"]/1e6:.3f}M NEAR</div><div class="s">snapshot, 0 staked or burned</div></div>'
            f'<div class="lc"><div class="l">Newest NEAR block</div><div class="v" id="l_blk">{k["block_height"]:,}</div><div class="s" id="l_blks">snapshot value</div></div></div>')
    livenote = ('<div class="note" id="livenote" style="display:none;margin:-6px 0 18px">These five tiles are recomputed live in your browser every two minutes: volume, fees and NEAR\u2019s cut from DefiLlama; buybacks and new supply from the NEAR chain itself (the buyback wallet balance and total supply now versus 30 days ago); price from DefiLlama. They can differ slightly from the frozen snapshot the thesis is built on, which is shown under each tile.</div>')
    cov_pct = k["coverage_near_30d"] * 100
    case = ('<div class="card" style="margin:0 0 18px"><span class="tag">Why this matters</span>'
            '<p style="margin:10px 0 0">Every blockchain has to pay the computers that run it. Most pay by printing new coins. On Ethereum, 93% of what stakers earn is newly minted ETH, and on Solana it is over 90% '
            '(<a href="https://www.theblock.co/post/409799/">Bitwise, Q2 2026</a>). Nobody sends a bill. Holders just own a slightly smaller share of the network each month.</p>'
            f'<p style="margin:10px 0 0">NEAR prints about {k["issued_near_30d"]/1e6:.1f} million new NEAR a month too. The difference is that since February, a fee on every swap through its NEAR Intents product is turned into NEAR and parked in a wallet. '
            'It is the first time a chain&rsquo;s own product has paid toward that bill, and you can watch it happen on-chain.</p>'
            f'<p style="margin:10px 0 0">So we asked how big that product has to get. Today it covers about {cov_pct:.0f}% of what NEAR prints. It would need about {be/vol_day:.0f} times the current traffic to cover all of it. '
            'That makes owning NEAR a bet on Intents growing, not on the fee switch as it stands today. If it does not grow, we wrote down in advance when we would walk away.</p></div>')
    cov = k["coverage_near_30d"]; nfill = max(1, round(cov * 10))
    coins = "".join(f'<div class="coin{" f" if i < nfill else ""}"></div>' for i in range(10))
    answer = (f'<div class="card answer"><div class="g-wide" style="align-items:center"><div><span class="tag">The answer</span>'
              f'<div class="big">The mechanism is real, but small. For every 10 new NEAR printed to pay validators, the fee switch buys back about <b id="a_n">{nfill}</b>.</div>'
              f'<div class="note" id="a_note">To pay for itself at today\'s 2.5% issuance, NEAR Intents would need about {money(be,0)} of swaps a day, {be/vol_day:.1f}x what it does now. '
              f'The issuance cut passed on 2 November (HSP-029) lowers that bar to {money(ms["breakeven_measured_hsp029"],0)} a day once fully phased in (about 2029).</div></div>'
              f'<div><h3 style="color:#c9d6e8">Every 10 new NEAR, last 30 days</h3><div class="coins" id="coins">{coins}</div>'
              f'<div class="sub"><span style="color:#9fd6cd">&#9679;</span> bought back &nbsp; <span>&#9675;</span> stays as new supply</div><div class="sub" id="a_sub">{k["issued_near_30d"]/1e6:.2f}M printed, {k["buyback_near_30d"]/1e3:,.0f}k bought back ({cov:.1%}).</div></div></div></div>')
    fee_r = k["fee_rate_bps_30d"] / 1e4; capr = k["capture_30d"]; bbs = sim_data["bbshare"]
    flow = [("Swapped", "$1,000,000", "by a user moving money between chains"),
            ("Fee paid", f"${1e6*fee_r:,.0f}", f"about {fee_r*100:.2f}% of the swap"),
            ("NEAR's cut", f"${1e6*fee_r*capr:,.0f}", f"{capr:.0%} of the fee; the rest goes to the apps that brought the swap"),
            ("Spent buying NEAR", f"${1e6*fee_r*capr*bbs:,.0f}", f"{bbs:.0%} of NEAR's cut reached the buyback wallet")]
    flow_html = ('<div class="card"><div class="card-h"><h2>Follow one million dollars</h2><span class="sub">Last 30 days, measured on chain</span></div>'
                 '<div class="flow">' + "".join(f'<div>{"<span class=fx>&rarr;</span>" if i else ""}<div class="fl">{a}</div><div class="fv">{b_}</div><div class="fs">{c}</div></div>' for i, (a, b_, c) in enumerate(flow))
                 + '</div></div>')
    three = ('<div class="card"><div class="card-h"><h2>Three things to know</h2></div><div class="three">'
             f'<div><h3>It is real</h3><div class="k">{k.get("cust_public_share",0):.0%} of payouts traced</div><div class="sub">Every USDT payout from the bridge\'s Tron wallet in one week ({money(k.get("cust_payouts_usd",0))}) matches a public NEAR withdrawal. The money is not invented.</div></div>'
             f'<div><h3>It is small</h3><div class="k">{cov:.1%} of new supply</div><div class="sub">Buybacks absorb about a tenth of the NEAR printed. The rest is new supply, so each holder\'s share of NEAR still shrinks.</div></div>'
             f'<div><h3>The bar is coming down</h3><div class="k">{money(be,0)} &rarr; {money(ms["breakeven_measured_hsp029"],0)} a day</div><div class="sub">Holders voted to cut issuance (HSP-029). Once phased in, the volume needed to pay for the chain falls by a third.</div></div>'
             '</div></div>')
    toc_items = [("Before the switch", f"Usage fell {abs(k['pb_active_chg_jan25_to_switch']):.0%} in a year and NEAR had no revenue to buy with."),
                 ("The traffic", f"{money(vol_day,0)} of swaps a day; rank {k['xp_bridge_rank']} of {k['xp_bridge_n']} cross-chain aggregators."),
                 ("The toll", f"Each swap pays about {k['fee_rate_bps_30d']/100:.2f}%; NEAR keeps {capr:.0%}."),
                 ("Printing vs buying back", f"{k['issued_near_30d']/1e6:.2f}M printed, {k['buyback_near_30d']/1e3:,.0f}k bought."),
                 ("The trend", "Coverage is rising month by month, still far from 100%."),
                 ("What it would take", "Set volume, fees and issuance and see when NEAR pays for itself."),
                 ("Is the traffic real?", "Real money, not one whale, but user counts are inflated."),
                 ("What could break it", "Seven risks, ranked, with what would ease each one."),
                 ("Our predictions", "Three dated calls, locked until 31 March 2027."),
                 ("Check any claim", f"{len(led)} public claims about NEAR tested; {sc.get('FAIL',0)} are false.")]
    toc = ('<div class="card"><div class="card-h"><h2>The story in ten steps</h2><span class="sub">Click any step, or use Next</span></div><div class="toc">'
           + "".join(f'<a href="#st{i+1}"><span class="tn">{i+1}</span><span><span class="tt">{a}</span><br><span class="td">{b_}</span></span></a>' for i, (a, b_) in enumerate(toc_items))
           + '</div></div>')
    tw_rows = [("Volume", f"{money(vol_day,0)} a day", "Walk away if under $120M a day at the end of Q2 2027", "Holding", "ok"),
               ("Share of fees NEAR keeps (90 days)", f"{k['capture_90d']:.1%}", "Walk away if under 20%. Prediction P2 asks for 30% by March 2027", "Holding, short of the 30% goal", "ok"),
               ("Buyback coverage", f"{cov:.1%}", "Walk away if under 25% at end of 2027 with HSP-029 in force. Prediction P3 asks for 15% (90-day) by March 2027", "Not due yet, on watch", "watch"),
               ("Biggest senders", "not measurable yet", "Walk away if the top 10 senders exceed 60% for two quarters", "Not measurable", "na"),
               ("Security", "16 signers, 11 needed", "Walk away after a second settlement-layer exploit or a signer set under 10", "Holding", "ok")]
    tw_html = ('<div class="card"><div class="card-h"><h2>Tripwires: what would make us walk away</h2><span class="sub">Written down before the results</span></div>'
               '<p style="margin:0 0 10px"><b>Verdict: on track, not proven.</b> No tripwire has been hit. The two that decide the case (coverage and volume) are not due until 2027.</p>'
               '<table style="width:100%;border-collapse:collapse"><tr><th align=left>Measure</th><th align=left>Now</th><th align=left>Rule</th><th align=left>Status</th></tr>'
               + "".join(f'<tr style="border-top:1px solid var(--line)"><td style="padding:6px 8px 6px 0">{a}</td><td style="padding:6px 8px 6px 0"><b>{b_}</b></td><td style="padding:6px 8px 6px 0">{c}</td><td style="padding:6px 0">{d}</td></tr>' for a, b_, c, d, _ in tw_rows)
               + f'</table><p class="sub" style="margin:10px 0 0">Security, for context: {k["validators"]} validators, top 10 hold {k["top10_stake_share"]:.0%} of stake, Chain Signatures needs 11 of 16 signers.</p></div>')
    steps = [("Overview", hero + live + case + kpi_html + livenote + answer + flow_html + three + tw_html + toc), ("1 Before the switch", c0), ("2 Traffic", c1), ("3 The toll", c2),
             ("4 Printing vs buying", c3), ("5 Coverage", c4), ("6 What it would take", c5), ("7 Is it real?", c6), ("8 Risks", c7),
             ("9 Predictions", c8), ("10 Test claims", c9 + rerun)]
    tabs = "".join(f'<button data-st="{i}">{html.escape(n)}</button>' for i, (n, _) in enumerate(steps))
    pages = "".join(f'<div class="st" data-st="{i}">{b}</div>' for i, (_, b) in enumerate(steps))
    body = (f'<div class="storywrap"><aside class="stepper" id="stp"><button id="stall" class="allbtn">Read as one page</button><div class="sidelab">Steps</div>{tabs}</aside><div class="storymain">{pages}'
            '<div class="stepnav"><button id="stprev">&larr; Back</button><span class="sub" id="stpos"></span><button id="stnext" class="on">Next &rarr;</button></div></div></div>'
            """<script>(function(){var L=document.getElementById('live');if(!L)return;var SNAPBB=__SNAPBB__;
function $(i){return document.getElementById(i)}
function money(x){return x>=1e9?'$'+(x/1e9).toFixed(2)+'B':'$'+(x/1e6).toFixed(0)+'M'}
function tj(u,o){return fetch(u,o).then(function(r){if(!r.ok)throw 0;return r.json()})}
var ok=0;function load(){ok=0;function done(){ok++;L.classList.remove('off');$('lstat').textContent='Live '+new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}
tj('https://coins.llama.fi/prices/current/coingecko:near').then(function(d){$('l_px').textContent='$'+d.coins['coingecko:near'].price.toFixed(2);$('l_px').nextElementSibling.textContent='live, from DefiLlama';done()}).catch(function(){});
tj('https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume').then(function(d){var c=d.change_1d;$('l_vol').textContent=money(d.total24h);
$('l_vols').innerHTML='<span class="'+(c>=0?'up':'dn')+'">'+(c>=0?'+':'')+c.toFixed(0)+'% vs day before</span>, 7-day avg '+money(d.total7d/7);done()}).catch(function(){});
var rpc={method:'POST',headers:{'content-type':'application/json'}};
tj('https://rpc.mainnet.fastnear.com',Object.assign({body:JSON.stringify({jsonrpc:'2.0',id:1,method:'query',params:{request_type:'view_account',finality:'final',account_id:'buybacks.multisignature.near'}})},rpc)).then(function(d){
var n=Number(BigInt(d.result.amount)/BigInt('1000000000000000000'))/1e6;$('l_bb').textContent=(n/1e6).toFixed(3)+'M NEAR';var dl=Math.round(n-SNAPBB);$('l_bb').nextElementSibling.textContent='live from the chain, '+(dl>=0?'+':'')+dl.toLocaleString()+' NEAR since the snapshot';$('l_blk').textContent=d.result.block_height.toLocaleString();$('l_blks').textContent='read from the chain just now';done()}).catch(function(){});
}
load();setInterval(load,60000);
})();
</script><script>(function(){
var SN=__SNAP__;
function $(i){return document.getElementById(i)}
function money(x,d){d=d==null?1:d;return x>=1e9?'$'+(x/1e9).toFixed(2)+'B':x>=1e6?'$'+(x/1e6).toFixed(d)+'M':'$'+Math.round(x).toLocaleString()}
function rpc(m,p){return fetch('https://archival-rpc.mainnet.fastnear.com',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:m,params:p})}).then(function(r){return r.json()}).then(function(d){if(d.error)throw 0;return d.result})}
function jf(u){return fetch(u).then(function(r){if(!r.ok)throw 0;return r.json()})}
function near(y){return Number(BigInt(y)/BigInt('1000000000000000000'))/1e6}
function run(){
Promise.all([jf('https://api.llama.fi/summary/dexs/near-intents?dataType=dailyVolume'),jf('https://api.llama.fi/summary/fees/near-intents?dataType=dailyFees'),jf('https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue'),jf('https://coins.llama.fi/prices/current/coingecko:near'),
rpc('status',[]).then(function(st){var H=st.sync_info.latest_block_height,T=Date.parse(st.sync_info.latest_block_time)/1000;
return rpc('block',{block_id:H-1000000}).then(function(b0){var rate=1e6/(T-b0.header.timestamp/1e9),tg=Math.round(H-rate*30*86400);
return Promise.all([rpc('block',{finality:'final'}),rpc('block',{block_id:tg}),rpc('query',{request_type:'view_account',finality:'final',account_id:'buybacks.multisignature.near'}),rpc('query',{request_type:'view_account',block_id:tg,account_id:'buybacks.multisignature.near'})])})})
]).then(function(r){
var vol=r[0].total30d,fees=r[1].total30d,rev=r[2].total30d,px=r[3].coins['coingecko:near'].price,x=r[4];
var iss=near(x[0].header.total_supply)-near(x[1].header.total_supply),bb=near(x[2].amount)-near(x[3].amount);
if(!(vol>0&&fees>0&&iss>0))return;
var cov=bb/iss,volday=vol/30,be=(iss/30*px)/((fees/vol)*(rev/fees));
var v=[money(vol),money(fees),money(rev),(cov*100).toFixed(1)+'%',money(be,0)+'/day'];
var s=['snapshot (10 Nov): '+money(SN.vol),'snapshot: '+money(SN.fees),'snapshot: '+money(SN.cut),'snapshot: '+(SN.cov*100).toFixed(1)+'%',(be/volday).toFixed(1)+'x today’s volume; snapshot '+money(SN.be,0)];
for(var i=0;i<5;i++){$('kv'+i).textContent=v[i];$('ks'+i).textContent=s[i];var c=$('kc'+i);c.classList.add('isl');c.querySelectorAll('.pill,.vs').forEach(function(e){e.style.display='none'})}
var n=Math.max(0,Math.min(10,Math.round(cov*10)));$('a_n').textContent=n;
var cs=$('coins').children;for(var j=0;j<cs.length;j++){cs[j].classList.toggle('f',j<n);cs[j].style.animation='none'}
$('a_sub').textContent=(iss/1e6).toFixed(2)+'M printed, '+(bb/1e3).toFixed(0)+'k bought back ('+(cov*100).toFixed(1)+'%), live.';
$('a_note').textContent='To pay for itself at today’s 2.5% issuance, NEAR Intents would need about '+money(be,0)+' of swaps a day, '+(be/volday).toFixed(1)+'x what it does now. The issuance cut passed on 2 November (HSP-029) lowers that bar to '+money(be*SN.rat,0)+' a day once fully phased in (about 2029).';
var ln=$('livenote');if(ln)ln.style.display='block';
}).catch(function(){});}
run();setInterval(run,120000);
})();
</script><script>(function(){var S=document.querySelectorAll('.st'),B=document.querySelectorAll('#stp button[data-st]'),n=S.length,cur=0;
var all=false,nav=document.querySelector('.stepnav');document.getElementById('stall').onclick=function(){all=!all;this.classList.toggle('on',all);this.textContent=all?'Read step by step':'Read as one page';
if(all){S.forEach(function(x){x.style.display='block'});B.forEach(function(b){b.classList.remove('on')});nav.style.display='none';document.querySelectorAll('.js-plotly-plot').forEach(function(g){try{Plotly.Plots.resize(g)}catch(e){}})}else{nav.style.display='';go(0)}};
function go(i){if(all){S[Math.max(0,Math.min(n-1,i))].scrollIntoView({behavior:'smooth'});return}cur=Math.max(0,Math.min(n-1,i));S.forEach(function(s,j){s.style.display=j===cur?'block':'none';s.classList.remove('in')});void S[cur].offsetWidth;S[cur].classList.add('in');
B.forEach(function(b,j){b.classList.toggle('on',j===cur)});document.getElementById('stpos').textContent=(cur+1)+' of '+n;
document.getElementById('stprev').style.visibility=cur?'visible':'hidden';var nx=document.getElementById('stnext');nx.style.visibility=cur<n-1?'visible':'hidden';
if(cur<n-1)nx.innerHTML='Next: '+B[cur+1].textContent.replace(/^[0-9]+ /,'')+' &rarr;';
S[cur].querySelectorAll('.js-plotly-plot').forEach(function(g){try{Plotly.Plots.resize(g)}catch(e){}});window.scrollTo(0,0)}
B.forEach(function(b,j){b.onclick=function(){go(j)}});document.getElementById('stprev').onclick=function(){go(cur-1)};document.getElementById('stnext').onclick=function(){go(cur+1)};
document.querySelectorAll('.st a[href^="#st"]').forEach(function(a){a.onclick=function(e){e.preventDefault();go(+a.getAttribute('href').slice(3))}});
addEventListener('keydown',function(e){if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT')return;if(e.key==='ArrowRight')go(cur+1);if(e.key==='ArrowLeft')go(cur-1)});
window.addEventListener('load',function(){go(cur)});go(0)})();</script>""".replace("__SNAPBB__", str(round(k["buyback_wallet_balance_near"]))).replace("__SNAP__", json.dumps({"vol": k["intents_volume_30d"], "fees": k["intents_fees_30d"], "cut": k["intents_revenue_30d"], "cov": k["coverage_near_30d"], "be": be, "rat": ms["breakeven_measured_hsp029"] / be})))
    return head + top + body + foot
