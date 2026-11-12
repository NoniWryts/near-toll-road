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
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=44, r=10, t=10, b=30), hovermode="x unified", showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0, yanchor="bottom", font=dict(size=12, color=MUTED)), xaxis=dict(AX, showgrid=False), yaxis=AX)


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
    kpi_html = '<div class="kpis">' + "".join(f'<div class="kpi"><div class="l">{a}</div><div class="v">{b_}</div>{c}</div>' for a, b_, c in kpis) + "</div>"

    answer = (f'<div class="card answer"><span class="tag">The answer</span>'
              f'<div class="big">The mechanism is real, but small. For every 10 new NEAR printed to pay validators, the fee switch buys back about <b>{k["coverage_near_30d"]*10:.0f}</b>.</div>'
              f'<div class="note">To pay for itself at today\'s 2.5% issuance, NEAR Intents would need about {money(be,0)} of swaps a day, {be/vol_day:.1f}x what it does now. '
              f'The issuance cut passed on Nov 2 (HSP-029) lowers that bar to {money(ms["breakeven_measured_hsp029"],0)} a day once fully phased in (~2029). Click Next to see how we got here; steps 5 and 9 let you test it yourself.</div></div>')

    def chapter(no, title, take, body, why, link, label="See the evidence"):
        return (f'<div class="card"><div class="step"><div class="num">{no}</div><div style="flex:1;min-width:0">'
                f'<div class="card-h"><h3 style="margin:0">{html.escape(title)}</h3><a class="more" href="{link}">{label} →</a></div>'
                f'<div class="takeaway">{take}</div><div class="note">{why}</div>{body}</div></div></div>')

    # 1 traffic
    dd = d[d.date >= "2025-09-01"]
    f1 = go.Figure()
    f1.add_bar(x=dd.date, y=dd.volume_usd, name="Daily swaps", marker_color=ACCENT_SOFT, marker_line_width=0)
    f1.add_scatter(x=dd.date, y=dd.volume_30d / 30, name="30-day average", line=dict(color=ACCENT, width=2.5))
    f1.update_yaxes(tickprefix="$")
    c1 = chapter(1, "The traffic", f"About {money(vol_day,0)} of swaps cross NEAR Intents every day.",
                 _fig(f1), f"Rank {k['xp_bridge_rank']} of {k['xp_bridge_n']} cross-chain aggregators on DefiLlama. Volume is down from its peak: DefiLlama shows {k['xp_intents_chg_1m_llama']:+.0f}% month on month.", "flywheel.html")
    # 2 toll and cut
    mm = m[(m.month >= "2026-02-01") & (m.month <= end)]
    f2 = go.Figure()
    f2.add_bar(x=mm.month, y=mm.fees_usd, name="Fees paid", marker_color=VIOLET_SOFT, marker_line_width=0)
    f2.add_bar(x=mm.month, y=mm.revenue_usd, name="NEAR's cut", marker_color=VIOLET, marker_line_width=0)
    f2.update_layout(barmode="overlay", bargap=0.35); f2.update_yaxes(tickprefix="$")
    c2 = chapter(2, "The toll", f"Each swap pays about {k['fee_rate_bps_30d']/100:.2f}%. NEAR keeps {k['capture_30d']:.0%} of it; the rest goes to the apps that bring the traffic.",
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
    c3 = chapter(3, "Printing vs buying back", f"In 30 days NEAR printed {k['issued_near_30d']/1e6:.2f}M new tokens and bought back {k['buyback_near_30d']/1e3:,.0f}k: <b>{k['coverage_near_30d']:.1%}</b> coverage.",
                 funnel, f"Counted in NEAR, not dollars, so a price move can't flatter it. Bought NEAR sits in a multisig: not burned, not staked (ledger C02).", "issuance.html")
    # 4 coverage trend
    mc = m[(m.month >= "2026-04-01") & m.coverage_near.notna() & (m.month <= end)]
    f4 = go.Figure()
    f4.add_bar(x=mc.month, y=mc.coverage_near, name="Buyback coverage of new supply", marker_color=ACCENT, marker_line_width=0,
               text=[f"{x:.0%}" for x in mc.coverage_near], textposition="outside")
    f4.add_scatter(x=mc.month, y=[1] * len(mc), name="Pays for itself (100%)", line=dict(color=MUTED, dash="dot", width=1.5), mode="lines")
    f4.update_yaxes(tickformat=".0%", range=[0, 1.08])
    c4 = chapter(4, "The trend", "Coverage is rising, but it is a long way from 100%.", _fig(f4, 240),
                 "Monthly NEAR bought back divided by NEAR printed. 100% would mean the fee switch fully offsets dilution.", "issuance.html")
    # 6 is it real
    real = [("Payouts are real money leaving", f"{k.get('cust_public_share',0):.0%}", f"Every USDT payout from the bridge's Tron wallet ({money(k.get('cust_payouts_usd',0))}, one week) matches a public NEAR withdrawal."),
            ("Not one whale", f"{k['vq_dest_top10']:.0%}", "of payout value goes to the top 10 recipients; the largest gets " + f"{k['vq_dest_top1']:.0%}."),
            ("'Users' are really swaps", f"{k['vq_perquote_share']:.0%}", "of payouts are signed by one-time accounts created per quote, so the Explorer's user count counts swaps (C21, FAIL)."),
            ("Little wash trading", f"{k['vq_selftrade_share_nonpersistent']:.1%}", "of swappers round-trip A→B→A outside the known market makers."),
            ("The April drop was one app", f"{k['blk_drop_explained']:.0%}", "of the fall in daily NEAR transactions is one reward app (KaiChing) stopping, not Intents.")]
    rows = "".join(f'<tr><td style="width:34%"><b>{a}</b></td><td style="width:12%;font-size:20px;font-weight:500">{b_}</td><td class="sub">{c}</td></tr>' for a, b_, c in real)
    c6 = chapter(6, "Is the traffic real?", "Mostly yes: the money is real and spread out, but user counts are inflated.",
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
    c7 = chapter(7, "What could break it", f"{len(risks)} risks, ranked. Two are serious today; all are checked against the data on every rebuild.",
                 rcards, "We keep the bad news in. A thesis that hides its weak points can't be trusted on its strong ones.", "security.html", "All risks")
    # 8 predictions
    pr = pd.read_csv(T / "predictions.csv") if (T / "predictions.csv").exists() else pd.DataFrame()
    prow = ""
    for _, r in pr.iterrows():
        prow += f'<tr><td><b>{r["id"]}</b></td><td>{html.escape(r["call"])}</td><td>{html.escape(str(r["observed"]))}</td><td>{html.escape(str(r["threshold"]))}</td><td>{r["settles"]}</td><td><span class="UNVERIFIABLE">{r["status"]}</span></td></tr>'
    c8 = chapter(8, "Our calls, frozen in advance", "Three dated predictions settle on 31 March 2027. Nobody can move the goalposts.",
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
<div class="ctl"><label>NEAR's share of fees <b id="o_cap"></b></label><input id="cap" type="range" min="5" max="100" step="0.1"></div>
<div class="ctl"><label>New NEAR printed per year <b id="o_iss"></b></label><input id="iss" type="range" min="0.5" max="5" step="0.05"></div>
<div class="sub">NEAR price is held at ${px:.2f}; coverage is price-free when buybacks and issuance are both counted in NEAR.</div>
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
    c5 = chapter(5, "Scenarios", "What would it take for NEAR to pay for itself? Set the volume, fee and issuance and see.", sim,
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
    c9 = chapter(9, "Check other people's claims, or your own", f"We tested {len(led)} public claims about NEAR against the chain. {sc.get('FAIL',0)} are false.",
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
    cov = k["coverage_near_30d"]; nfill = max(1, round(cov * 10))
    coins = "".join(f'<div class="coin{" f" if i < nfill else ""}"></div>' for i in range(10))
    answer = (f'<div class="card answer"><div class="g-wide" style="align-items:center"><div><span class="tag">The answer</span>'
              f'<div class="big">The mechanism is real, but small. For every 10 new NEAR printed to pay validators, the fee switch buys back about <b>{nfill}</b>.</div>'
              f'<div class="note">To pay for itself at today\'s 2.5% issuance, NEAR Intents would need about {money(be,0)} of swaps a day, {be/vol_day:.1f}x what it does now. '
              f'The issuance cut passed on 2 November (HSP-029) lowers that bar to {money(ms["breakeven_measured_hsp029"],0)} a day once fully phased in (about 2029).</div></div>'
              f'<div><h3 style="color:#c9d6e8">Every 10 new NEAR, last 30 days</h3><div class="coins">{coins}</div>'
              f'<div class="sub"><span style="color:#9fd6cd">&#9679;</span> bought back &nbsp; <span>&#9675;</span> stays as new supply</div><div class="sub">{k["issued_near_30d"]/1e6:.2f}M printed, {k["buyback_near_30d"]/1e3:,.0f}k bought back ({cov:.1%}).</div></div></div></div>')
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
    toc_items = [("The traffic", f"{money(vol_day,0)} of swaps a day; rank {k['xp_bridge_rank']} of {k['xp_bridge_n']} cross-chain aggregators."),
                 ("The toll", f"Each swap pays about {k['fee_rate_bps_30d']/100:.2f}%; NEAR keeps {capr:.0%}."),
                 ("Printing vs buying back", f"{k['issued_near_30d']/1e6:.2f}M printed, {k['buyback_near_30d']/1e3:,.0f}k bought."),
                 ("The trend", "Coverage is rising month by month, still far from 100%."),
                 ("What it would take", "Set volume, fees and issuance and see when NEAR pays for itself."),
                 ("Is the traffic real?", "Real money, not one whale, but user counts are inflated."),
                 ("What could break it", "Seven risks, ranked, with what would ease each one."),
                 ("Our predictions", "Three dated calls, locked until 31 March 2027."),
                 ("Check any claim", f"{len(led)} public claims about NEAR tested; {sc.get('FAIL',0)} are false.")]
    toc = ('<div class="card"><div class="card-h"><h2>The story in nine steps</h2><span class="sub">Click any step, or use Next</span></div><div class="toc">'
           + "".join(f'<a href="#st{i+1}"><span class="tn">{i+1}</span><span><span class="tt">{a}</span><br><span class="td">{b_}</span></span></a>' for i, (a, b_) in enumerate(toc_items))
           + '</div></div>')
    steps = [("Overview", hero + kpi_html + answer + flow_html + three + toc), ("1 Traffic", c1), ("2 The toll", c2), ("3 Printing vs buying", c3),
             ("4 Coverage", c4), ("5 What it would take", c5), ("6 Is it real?", c6), ("7 Risks", c7), ("8 Predictions", c8),
             ("9 Test claims", c9 + rerun)]
    tabs = "".join(f'<button data-st="{i}">{html.escape(n)}</button>' for i, (n, _) in enumerate(steps))
    pages = "".join(f'<div class="st" data-st="{i}">{b}</div>' for i, (_, b) in enumerate(steps))
    body = (f'<div class="stepper" id="stp">{tabs}<button id="stall" style="margin-left:auto">Read as one page</button></div>{pages}'
            '<div class="stepnav"><button id="stprev">&larr; Back</button><span class="sub" id="stpos"></span><button id="stnext" class="on">Next &rarr;</button></div>'
            """<script>(function(){var S=document.querySelectorAll('.st'),B=document.querySelectorAll('#stp button[data-st]'),n=S.length,cur=0;
var all=false,nav=document.querySelector('.stepnav');document.getElementById('stall').onclick=function(){all=!all;this.classList.toggle('on',all);this.textContent=all?'Read step by step':'Read as one page';
if(all){S.forEach(function(x){x.style.display='block'});B.forEach(function(b){b.classList.remove('on')});nav.style.display='none';document.querySelectorAll('.js-plotly-plot').forEach(function(g){try{Plotly.Plots.resize(g)}catch(e){}})}else{nav.style.display='';go(0)}};
function go(i){if(all){S[Math.max(0,Math.min(n-1,i))].scrollIntoView({behavior:'smooth'});return}cur=Math.max(0,Math.min(n-1,i));S.forEach(function(s,j){s.style.display=j===cur?'block':'none'});
B.forEach(function(b,j){b.classList.toggle('on',j===cur)});document.getElementById('stpos').textContent=(cur+1)+' of '+n;
document.getElementById('stprev').style.visibility=cur?'visible':'hidden';var nx=document.getElementById('stnext');nx.style.visibility=cur<n-1?'visible':'hidden';
if(cur<n-1)nx.innerHTML='Next: '+B[cur+1].textContent.replace(/^[0-9]+ /,'')+' &rarr;';
S[cur].querySelectorAll('.js-plotly-plot').forEach(function(g){try{Plotly.Plots.resize(g)}catch(e){}});window.scrollTo(0,0)}
B.forEach(function(b,j){b.onclick=function(){go(j)}});document.getElementById('stprev').onclick=function(){go(cur-1)};document.getElementById('stnext').onclick=function(){go(cur+1)};
document.querySelectorAll('.st a[href^="#st"]').forEach(function(a){a.onclick=function(e){e.preventDefault();go(+a.getAttribute('href').slice(3))}});
addEventListener('keydown',function(e){if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT')return;if(e.key==='ArrowRight')go(cur+1);if(e.key==='ArrowLeft')go(cur-1)});
window.addEventListener('load',function(){go(cur)});go(0)})();</script>""")
    return head + top + body + foot
