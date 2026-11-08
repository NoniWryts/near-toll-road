"""Volume quality (blueprint Q1, Q2, Q6-Q11) from the two seeded samples and the nearstats readings.

Definitions
- payout: a signed ft_withdraw / native_withdraw / mt_withdraw intent; the user-facing leg that leaves Intents.
  Its destination (WITHDRAW_TO memo, or receiver) is the closest on-chain proxy for an end user.
- fill: a signed `transfer` intent; in the 1Click flow this is a solver paying a per-quote deposit account.
- per-quote account: a 64-hex implicit account. 1Click creates one per quote, so counting signers counts quotes,
  not people. Concentration is therefore measured on payout destinations.
- USD values use 1Click spot prices at fetch time (one price scale for every row); shares, not totals, are the output.
"""
from __future__ import annotations
import json
import re
import numpy as np
import pandas as pd
from pipeline.common import load_df, load_json, ROOT

T = ROOT / "reports" / "tables"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
BRIDGE_ROUTES = {"omni.bridge.near", "bridge-refuel.hot.tg"}


def _kind(acct: str | None) -> str:
    if not acct:
        return "unknown"
    if HEX64.match(acct):
        return "per-quote implicit (64-hex)"
    if acct.startswith("0x") and len(acct) == 42:
        return "EVM address"
    return "named NEAR account"


def conc(values: pd.Series) -> dict:
    v = values.sort_values(ascending=False)
    tot = v.sum()
    if tot <= 0 or len(v) == 0:
        return {}
    s = v / tot
    return {"n": int(len(v)), "top1": float(s.iloc[:1].sum()), "top5": float(s.iloc[:5].sum()), "top10": float(s.iloc[:10].sum()),
            "top20": float(s.iloc[:20].sum()), "hhi": float((s ** 2).sum() * 10_000)}


def value(df: pd.DataFrame, tokens: pd.DataFrame) -> pd.DataFrame:
    px = tokens.set_index("assetId")[["decimals", "price", "symbol", "blockchain"]]
    d = df.join(px, on="token")
    amt = pd.to_numeric(d.amount, errors="coerce").abs()
    d["usd"] = amt / (10.0 ** d.decimals) * d.price
    return d


def build(snap) -> dict:
    k = {}
    try:
        s = load_df(snap, "intents_sample")
        pages = load_df(snap, "intents_sample_pages")
        tokens = load_df(snap, "oneclick_tokens")
        meta = json.loads((snap / "manifest.json").read_text())["files"]["intents_sample.parquet"]
    except (FileNotFoundError, KeyError):
        return k
    s = s.copy(); s["ts"] = pd.to_datetime(s.ts, utc=True); s["month"] = s.ts.dt.strftime("%Y-%m")
    v = value(s[s.token.notna()], tokens)
    priced = v.usd.notna()
    k["vq_rows"] = int(len(s)); k["vq_txns"] = int(meta.get("txns_sampled", pages.txns.sum())); k["vq_pages"] = int(meta.get("pages_ok", (pages.txns > 0).sum()))
    k["vq_sampled_hours"] = float(meta.get("sampled_minutes", 0)) / 60
    k["vq_window"] = f"{meta.get('window_start')} to {meta.get('window_end_exclusive')} (exclusive)"
    k["vq_priced_share"] = float(priced.mean()) if len(v) else 0.0
    mix = s.intent.value_counts(normalize=True)
    mix.rename_axis("intent").reset_index(name="share").to_csv(T / "vq_intent_mix.csv", index=False)

    pay = v[v.intent.isin(["ft_withdraw", "native_withdraw", "mt_withdraw", "nft_withdraw"]) & priced].copy()
    fills = v[(v.intent == "transfer") & priced].copy()
    k["vq_payouts"] = int(len(pay)); k["vq_payout_usd"] = float(pay.usd.sum())
    # Q6 concentration of payout value by destination, and by signer.
    # Payouts routed through a bridge contract carry the real recipient inside a message; they are excluded from
    # the end-user view and their share is reported instead.
    bridged = pay.dest.isin(BRIDGE_ROUTES)
    k["vq_bridge_route_share"] = float(pay[bridged].usd.sum() / pay.usd.sum()) if len(pay) else 0.0
    pay_all = pay
    pay = pay[~bridged]
    by_dest = pay.groupby("dest").usd.sum()
    c = conc(by_dest); k.update({f"vq_dest_{a}": b for a, b in c.items()})
    by_signer = pay_all.groupby("signer").usd.sum()
    c = conc(by_signer); k.update({f"vq_signer_{a}": b for a, b in c.items()})
    kinds = pay_all.assign(kind=pay_all.signer.map(_kind)).groupby("kind").usd.sum()
    kinds = (kinds / kinds.sum()).sort_values(ascending=False)
    kinds.rename_axis("signer_kind").reset_index(name="share_of_payout_usd").to_csv(T / "vq_signer_kinds.csv", index=False)
    k["vq_perquote_share"] = float(kinds.get("per-quote implicit (64-hex)", 0.0))
    top = by_dest.sort_values(ascending=False).head(20).reset_index()
    top.columns = ["destination", "usd"]
    top["share"] = top.usd / by_dest.sum()
    top["destination"] = top.destination.astype(str).str.slice(0, 10) + "…"  # truncated: these are addresses, not names
    top.to_csv(T / "vq_top_destinations.csv", index=False)
    # payout chains and assets
    ch = pay_all.groupby("blockchain").usd.sum(); (ch / ch.sum()).sort_values(ascending=False).rename_axis("chain").reset_index(name="share").to_csv(T / "vq_payout_chains.csv", index=False)
    sym = pay_all.groupby("symbol").usd.sum(); (sym / sym.sum()).sort_values(ascending=False).head(12).rename_axis("asset").reset_index(name="share").to_csv(T / "vq_payout_assets.csv", index=False)
    k["vq_stable_share"] = float(sym[sym.index.isin(["USDT", "USDC", "USDT0", "DAI", "USD1", "USDe"])].sum() / sym.sum()) if sym.sum() else 0.0
    # Q7 repeat use: Sep destinations seen again in Oct (count and value), a lower bound under sampling
    months = sorted(pay.month.unique())
    if len(months) >= 2:
        a, b = months[-2], months[-1]
        da, db = set(pay[pay.month == a].dest), set(pay[pay.month == b].dest)
        both = da & db
        k["vq_repeat_months"] = f"{a} -> {b}"
        k["vq_repeat_count_share"] = len(both) / len(db) if db else 0.0
        bv = pay[pay.month == b]
        k["vq_repeat_value_share"] = float(bv[bv.dest.isin(both)].usd.sum() / bv.usd.sum()) if len(bv) else 0.0
        # how often does any destination appear twice inside one month's sample (also a lower bound)
        cnt = pay[pay.month == b].groupby("dest").size()
        k["vq_multi_in_month_value_share"] = float(bv[bv.dest.isin(cnt[cnt > 1].index)].usd.sum() / bv.usd.sum())
    days = (pd.Timestamp(meta.get("window_end_exclusive")) - pd.Timestamp(meta.get("window_start"))).days if meta.get("window_start") else 61
    k["vq_sample_fraction_time"] = k["vq_sampled_hours"] / (days * 24) if days else 0.0
    # Q8 self-trade heuristic on token_diff legs: one signer, inside one ~3-minute page, swaps A->B and B->A.
    # (Seeing a token on both sides alone is not enough: routing A->B->C also does that.)
    td = v[v.intent == "token_diff"].copy()
    td["amt"] = pd.to_numeric(td.amount, errors="coerce")
    legs = td.groupby(["page", "signer", "tx_hash"]).apply(
        lambda g: (tuple(sorted(g[g.amt < 0].token)), tuple(sorted(g[g.amt > 0].token))), include_groups=False).reset_index(name="pair")
    def _round(g):
        pairs = set(g.pair)
        return any((b, a) in pairs for a, b in pairs if a and b)
    flags = legs.groupby(["page", "signer"]).apply(_round, include_groups=False)
    flagged = flags[flags].reset_index()[["page", "signer"]]
    td_signers = legs.groupby(["page", "signer"]).size()
    k["vq_selftrade_signer_pages"] = int(len(flagged)); k["vq_tokendiff_signer_pages"] = int(len(td_signers))
    k["vq_selftrade_share"] = float(len(flagged) / len(td_signers)) if len(td_signers) else 0.0
    # persistent signers (seen in 20+ of the random pages) are market makers/solvers; the rest approximate users
    pages_per = td.groupby("signer").page.nunique()
    persistent = set(pages_per[pages_per >= 20].index)
    k["vq_persistent_tokendiff_signers"] = int(len(persistent))
    ts_ = td_signers.reset_index()
    nonp = ts_[~ts_.signer.isin(persistent)]
    fl_np = flagged[~flagged.signer.isin(persistent)]
    k["vq_selftrade_share_nonpersistent"] = float(len(fl_np) / len(nonp)) if len(nonp) else 0.0
    k["vq_persistent_share_of_tokendiff_pages"] = float(1 - len(nonp) / len(ts_)) if len(ts_) else 0.0
    k["vq_tokendiff_share_of_rows"] = float((s.intent == "token_diff").mean())
    # Q11 solver concentration on fills
    fs = fills.groupby("signer").usd.sum()
    c = conc(fs); k.update({f"vq_solver_{a}": b for a, b in c.items()})
    sol = (fs / fs.sum()).sort_values(ascending=False).head(10).rename_axis("solver").reset_index(name="share_of_fill_usd")
    sol.to_csv(T / "vq_solvers.csv", index=False)
    k["vq_top_solver"] = str(sol.solver.iloc[0]) if len(sol) else ""
    # Q9 channel proxies: who submits the settlement transaction (relayer), and nearstats referral/affiliate split
    rel = s.drop_duplicates("tx_hash").tx_signer.value_counts(normalize=True).head(8)
    rel.rename_axis("tx_submitter").reset_index(name="share_of_txns").to_csv(T / "vq_submitters.csv", index=False)
    k["vq_submitter_intents_share"] = float(rel.get("intents.near", 0.0))
    try:
        ns = load_json(snap, "nearstats_summary")["intents"]
        aff = pd.DataFrame(ns.get("topAffiliates", [])); ref = pd.DataFrame(ns.get("topReferrals", []))
        win = ns["timeframes"]["24h"]
        for name, d in (("affiliate", aff), ("referral", ref)):
            if len(d):
                d.to_csv(T / f"vq_channels_{name}.csv", index=False)
        if len(aff):
            k["vq_top_affiliate"] = str(aff.sort_values("volumeUsd", ascending=False).id.iloc[0])
            k["vq_top_affiliate_ratio_next"] = float(aff.sort_values("volumeUsd", ascending=False).volumeUsd.iloc[0] / aff.sort_values("volumeUsd", ascending=False).volumeUsd.iloc[1])
    except (FileNotFoundError, KeyError):
        pass
    # Q10 confidential share: the residual between two NEAR-run series, read twice a week apart
    reads = []
    for name in ("nearstats_summary", "nearstats_summary_recheck"):
        try:
            ns = load_json(snap, name)["intents"]
        except (FileNotFoundError, KeyError):
            continue
        tb = ns["totalsBreakdown"]
        tot = ns["totals"]["volume30dUsd"]; pub = tb["public"]["volume30dUsd"]; conf = tb["confidential"]["volume30dUsd"]
        reads.append({"reading": name, "as_of": tb.get("asOfDate"), "alignment": tb.get("alignment"), "total_30d": tot, "public_tiles_30d": pub,
                      "confidential_residual_30d": conf, "confidential_share": conf / tot if tot else None,
                      "explorer_swaps_30d_usd": ns["timeframes"]["30d"]["volumeUsd"], "explorer_swaps_30d_count": ns["timeframes"]["30d"]["swapCount"],
                      "explorer_unique_users_30d": ns["timeframes"]["30d"]["uniqueUsers"]})
    if reads:
        r = pd.DataFrame(reads); r.to_csv(T / "vq_confidential_reads.csv", index=False)
        k["vq_conf_share_first"] = float(r.confidential_share.iloc[0]); k["vq_conf_asof_first"] = str(r.as_of.iloc[0])
        k["vq_conf_share_last"] = float(r.confidential_share.iloc[-1]); k["vq_conf_asof_last"] = str(r.as_of.iloc[-1])
        k["vq_explorer_swaps_30d_usd"] = float(r.explorer_swaps_30d_usd.iloc[0]); k["vq_explorer_swaps_30d_count"] = int(r.explorer_swaps_30d_count.iloc[0])
        k["vq_explorer_unique_users_30d"] = int(r.explorer_unique_users_30d.iloc[0])
        k["vq_explorer_share_of_total"] = float(r.explorer_swaps_30d_usd.iloc[0] / r.total_30d.iloc[0])
    k.update(blocks(snap))
    return k


def _group(acct: str) -> str:
    parts = str(acct).split(".")
    return ".".join(parts[-2:]) if len(parts) > 2 else str(acct)


def blocks(snap) -> dict:
    """Q1 and Q2: transaction mix by receiver in sampled blocks, scaled to NearBlocks daily counts per window."""
    try:
        t = load_df(snap, "block_sample_txns"); b = load_df(snap, "block_sample_blocks")
    except FileNotFoundError:
        return {}
    n = pd.read_csv(T / "network_daily.csv", parse_dates=["date"])
    out, k = [], {}
    rng = np.random.default_rng(7)
    for w in t.window.unique():
        a, z = w.split(":")
        daily = float(n[(n.date >= a) & (n.date <= z)].txns.mean())
        x = t[t.window == w].assign(group=lambda d: d.receiver.map(_group), signer_group=lambda d: d.signer.map(_group))
        sh = x.group.value_counts(normalize=True)
        # block bootstrap for a 90% interval on the top groups
        hs = b[b.window == w].height.values
        per = x.groupby(["height", "group"]).size().unstack(fill_value=0).reindex(hs, fill_value=0)
        boots = []
        for _ in range(300):
            idx = rng.choice(len(hs), len(hs))
            m = per.iloc[idx].sum(); boots.append(m / m.sum())
        bt = pd.DataFrame(boots)
        for g_, s_ in sh.head(12).items():
            lo, hi = (bt[g_].quantile([0.05, 0.95]) if g_ in bt else (np.nan, np.nan))
            out.append({"window": w, "receiver_group": g_, "share": s_, "share_p05": lo, "share_p95": hi,
                        "est_txns_per_day": s_ * daily, "window_txns_per_day": daily, "sampled_blocks": len(hs), "sampled_txns": len(x),
                        "top_signer_group": x[x.group == g_].signer_group.value_counts().index[0]})
    df = pd.DataFrame(out); df.to_csv(T / "block_mix.csv", index=False)
    ws = sorted(df.window.unique())
    if len(ws) >= 2:
        pre, post = df[df.window == ws[0]], df[df.window == ws[-1]]
        drop = pre.window_txns_per_day.iloc[0] - post.window_txns_per_day.iloc[0]
        top_pre = pre.iloc[0]
        post_same = post[post.receiver_group == top_pre.receiver_group].est_txns_per_day.sum()
        k.update({"blk_pre_window": ws[0], "blk_post_window": ws[-1], "blk_pre_daily": float(pre.window_txns_per_day.iloc[0]),
                  "blk_post_daily": float(post.window_txns_per_day.iloc[0]), "blk_top_pre_group": str(top_pre.receiver_group),
                  "blk_top_pre_share": float(top_pre.share), "blk_top_pre_signer": str(top_pre.top_signer_group),
                  "blk_top_pre_daily": float(top_pre.est_txns_per_day), "blk_top_pre_post_daily": float(post_same),
                  "blk_drop_explained": float((top_pre.est_txns_per_day - post_same) / drop) if drop > 0 else None,
                  "blk_post_top": "; ".join(f"{r.receiver_group} {r.share:.0%}" for r in post.head(5).itertuples())})
    return k
