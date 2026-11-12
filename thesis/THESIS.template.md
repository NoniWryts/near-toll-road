# Toll Road: does NEAR's fee switch pay for the chain?

*An investment thesis for NEAR Protocol (NEAR) built from on-chain data. Snapshot `{{snapshot}}`, data through {{as_of}}. Every number below is written by `thesis/render.py` from `reports/tables/`; nothing is typed by hand. Re-run `make report` and the text updates. Not investment advice.*

## 1. The claim, and what would falsify it

**Thesis.** NEAR has turned a cross-chain product, NEAR Intents, into a measurable revenue line for the token: a fee on every swap is converted to NEAR and swept on-chain into a buyback wallet. If that revenue grows to cover the value of new NEAR issuance, NEAR becomes one of the few Layer-1 tokens whose supply is paid for by a product rather than by holders. That is the long-term case.

**Where it stands today.** The mechanism is real and visible on-chain (ledger C01). It is also small: in the last 30 days NEAR bought back {{bb30_near}} NEAR against {{iss30_near_m}}M NEAR issued, a coverage of **{{cov30}}**. Issuance runs {{iss_x_bb}}x buybacks. At the measured fee rate ({{fee_bps}} bps of volume) and capture rate ({{cap30}}), Intents would need **${{be_cap_m}}M of volume per day** to cover 2.5% issuance, versus ${{vol_day_m}}M today, a {{be_mult}}x gap. HSP-029 passed on Nov 2, 2026 (ledger C20: {{hos_for_m}}M veNEAR for, {{hos_against}} against, turnout {{hos_turnout}}). It does not cut issuance to 1.6% at once: after a 14-day timelock, a validator upgrade and a ~90-day buffer, the cap ramps down by about 3.75 bps a month for 24 months. At the end of 2027 the cap is near {{ramp_2027}}, where breakeven is ${{be_ramp_m}}M per day; at the 1.6% end point (2029) it is ${{be_hsp_m}}M per day ({{be_mult_hsp}}x today's volume).

**Kill criteria** (set now, before the data moves):
1. Trailing-90-day capture below 20% *and* 30-day volume below $120M/day at the end of Q2 2027: the flywheel thesis fails.
2. Buyback coverage of issuance still below 25% at the end of 2027 with HSP-029 in force: the token-value-accrual thesis fails even if the product succeeds.
3. Top-10 sender concentration of public Intents volume above 60% for two consecutive quarters: adoption is not broad (not yet measurable here, see §7).
4. A second settlement-layer exploit without full recovery, or MPC signer set below 10 independent operators.

## 2. Market catalyst

Crypto activity is fragmented across chains, and the next wave of users (wallets, agents, treasuries) wants outcomes, not routes. NEAR Intents sells that outcome: the user signs what they want, solvers compete to fill it, `intents.near` settles atomically across 35+ chains with no bridge. Three things happened in 2026 that make this measurable: the fee switch (Feb 23), Confidential Intents going GA (Jul 7), and the Bitwise spot ETF (NRR, Sep 29). The HSP-029 issuance vote closes Nov 2 and is the live catalyst for the next quarter.

### What the chain looked like before the buybacks

The fee switch went live on {{pb_switch}}; the first sweep reached the buyback wallet on {{pb_first_sweep}}, {{pb_gap}} days later. Before it, the chain was already shrinking: active accounts fell from about {{pb_active_jan25}} a day in January 2025 to {{pb_active_pre}} a day in the months before the switch ({{pb_active_chg}} lower; transactions {{pb_txns_chg}} lower). New NEAR was being printed at about {{pb_iss_before}} of supply a year until the inflation cap was halved in late October 2025, and about {{pb_iss_after}} after. Over the same months the NEAR price fell with the whole market ({{pb_px_start}} to {{pb_switch}}: NEAR {{pb_pre_near}}, SOL {{pb_pre_sol}}, ETH {{pb_pre_eth}}); since the switch NEAR is {{pb_post_near}} against SOL {{pb_post_sol}} and ETH {{pb_post_eth}} (to {{pb_as_of}}). Buybacks so far total {{pb_bb_usd}} against about {{pb_trading}} of NEAR traded on an average day, so we treat the rally as timing worth noting, not as proof that buybacks caused it. Issuance was halved and a reward app stopped in the same months, so this is a before-and-after description, not a causal estimate.

**Why a buyback was not possible earlier.** (1) There was no revenue to spend: Intents collected almost no fees until {{pb_fees_first}}, and NEAR's own cut was about {{pb_rev_before}} in total before November 2025 (DefiLlama). (2) The first fix chosen was a smaller printing press, not a buyer: a community proposal on 24 June 2025 argued that 5% a year was more than the network needed, and the cut to 2.5% took effect with the nearcore 2.9.0 upgrade in late October 2025. (3) Burning gas fees was too small to offset issuance: the same proposal put the burn at about 0.1% of supply a year; by our estimate (70% of gas fees burned) it covered only {{pb_burn_cover}} of the value of new NEAR between November 2025 and the switch. We could not find a primary NEAR source stating why the buyback itself was chosen in February 2026, so that reading is ours. Data: `reports/tables/prebuyback_monthly.csv`, `analysis/prebuyback.py`.

## 3. Evidence: the flywheel in numbers

| | Trailing 30d | Lifetime |
|---|---|---|
| Intents volume | ${{vol30_b}}B (${{vol_day_m}}M/day) | ${{vol_all_b}}B |
| Gross fees | ${{fees30_m}}M ({{fee_bps}} bps) | ${{fees_all_m}}M |
| Revenue captured by NEAR | ${{rev30_m}}M (capture {{cap30}}; 90d {{cap90}}) | ${{rev_all_m}}M (capture {{cap_life}}) |
| NEAR swept into buyback wallet | {{bb30_near}} NEAR (${{bb30_usd_m}}M) | {{bb_all_near}} NEAR (${{bb_all_usd_m}}M), {{bb_sweeps}} receipts since {{bb_first}} |
| NEAR issued | {{iss30_near_m}}M NEAR (${{iss30_usd_m}}M), {{iss_rate}} annualised | |
| Buyback coverage of issuance | **{{cov30}}** | |

September 2026 was the record month (${{sep_vol_b}}B volume, capture {{sep_cap}}); October fell to ${{oct_vol_b}}B ({{oct_chg}}) while capture rose to {{oct_cap}}. In October the wallet received {{oct_bb_near}} NEAR against {{oct_iss_near_m}}M issued.

What the buyback wallet actually holds: {{bb_balance}} NEAR, liquid, in a multisig. Zero is staked and zero is burned (ledger C02), although the tokenomics post describes repurchased NEAR as "staked or locked". The buyback wallet receives {{bb_share}} of captured revenue; the remainder sits in the two Sputnik DAO fee wallets. Coverage in this thesis is therefore a comparison of flows, not a supply model. Net supply still grows at roughly {{iss_rate}} a year.

## 4. Competitive edge, as far as the data reaches

- **A product with a take rate.** Few L1s have a revenue line that is not gas. NEAR's base-layer gas fees were ${{gas30_m}}M in 30 days; Intents fees were ${{fees30_m}}M. The product earns more than the chain.
- **Distribution.** Volume comes through Brave, Ledger, Trust Wallet, Rabby, SwapKit and near.com. The capture rate has risen as near.com's own share grew (28% to {{cap30}} across October), which is the mechanism by which margin improves.
- **Confidential execution.** Roughly a tenth of all-time volume and most of recent growth ran through the confidential shard. This is NEAR-reported and not independently observable (ledger C12), so this thesis treats it as a product signal, not as audited volume.
- **Chain Signatures is real but internal.** About {{cs_calls}} sign requests a day reach the MPC contract (extrapolated from a {{cs_hours}}-hour sample of {{cs_rows}} receipts; {{cs_lifetime}} lifetime receipts). {{cs_infra}} of them come from NEAR's own Intents bridge and FastAuth. The "agents signing on any chain" story is not yet visible in who calls the contract.
- **It is the biggest venue of its kind that DefiLlama can see.** ${{xp_vol30_b}}B of 30-day volume puts Intents at rank {{xp_bridge_rank}} of {{xp_bridge_n}} when placed among DefiLlama's bridge aggregators ({{xp_bridge_share}} of that list; next {{xp_bridge_next}}) and rank {{xp_swap_rank}} of {{xp_swap_n}} among swap aggregators (leader {{xp_swap_leader}}). Canonical bridges and exchanges are outside this comparison, and DefiLlama's own 30-day change for Intents is {{xp_chg_llama}}.
- **Security budget.** {{validators}} validators, {{stake_ratio}} of supply staked, Nakamoto coefficient {{nakamoto}} at the one-third threshold, top-10 share {{top10}}.

## 5. Valuation: what the market is paying for

At ${{price}} NEAR's market cap is ${{mcap_b}}B. On annualised 30-day figures that is {{near_product_fees_x}}x Intents gross fees and {{near_product_rev_x}}x captured Intents revenue. On base-layer gas alone it is {{near_mcap_fees_x}}x fees (Ethereum {{eth_mcap_fees_x}}x, Solana {{sol_mcap_fees_x}}x, same DefiLlama definition). Headlines that quote a "56x fee multiple" use gross fees; the token only sees the captured share.

2030 scenarios (arithmetic on `params.yaml`, not forecasts): bear revenue ${{bear_rev_m}}M/yr covering {{bear_cov}}x issuance, implied cap ${{bear_mcap_b}}B; base ${{base_rev_m}}M/yr, {{base_cov}}x, ${{base_mcap_b}}B ({{base_vs_today}}x today); bull ${{bull_rev_m}}M/yr, {{bull_cov}}x, ${{bull_mcap_b}}B ({{bull_vs_today}}x today). The spread says what the current price assumes: sustained 35%+ volume growth with capture at or above 30%. The bear row is deliberately uncomfortable; a revenue-only valuation does not support today's price if the flywheel stalls.

## 6. Variant perception

The market prices NEAR as an "AI chain" narrative or as a generic alt-L1. The more useful lens is a settlement business with a visible P&L. That lens is less flattering today (coverage {{cov30}}) but it is the only one that can be checked monthly, and it is the one where NEAR's own governance is now acting: HSP-029, now passed, attacks the denominator (issuance), the near.com share attacks the numerator (capture).

## 7. Risks and honest limits

- **Issuance outruns buybacks** by {{iss_x_bb}}x. Bought NEAR is held, not retired.
- **Volume is not users, but it is not one whale either.** A seeded sample of {{vq_txns}} `intents.near` transactions ({{vq_hours}} hours across September and October) shows {{vq_perquote}} of payout value signed by one-time accounts 1Click creates per quote, so the Explorer's "{{vq_users}} unique users" counts swaps, not people (ledger C21, FAIL). Measured on payout destinations instead, the top 10 receive {{vq_top10}} of value and the top 1 {{vq_top1}} (HHI {{vq_hhi}}, unconcentrated). At least {{vq_repeat_val}} of October's sampled payout value went to destinations also paid in September (a lower bound). Round-trip trading by non-market-maker signers is rare ({{vq_selftrade}} of signer windows). Money inside Intents is concentrated at the other end: the top 5 transfer signers (solvers and pools) move {{vq_solver5}} of value.
- **The confidential share is not measurable as a residual, but it can be bounded by custody.** The same 30-day total split {{vq_conf_first}} confidential on {{vq_conf_first_date}} and {{vq_conf_last}} a week later, after the public series was revised (ledger C22): a residual absorbs missed data and private flow alike. So we reconciled custody instead. Confidential swaps must still pay out on the destination chain, so for {{cust_route}} we read every payout from the bridge's Tron hot wallet and every public withdrawal on NEAR, {{cust_start}} to {{cust_end}}. {{cust_public}} of {{cust_n}} payouts ({{cust_usd}}) match a public `intents.near` withdrawal (median fee {{cust_fee}} USDT, median delay {{cust_lag}} s); {{cust_nopublic}} ({{cust_nopublic_usd}}) left custody with no public record (ledger C23). So the bridge wallet pays out nothing that is not publicly withdrawn on NEAR. A confidential payout on this route must therefore either pass through a public NEAR withdrawal (the private shard hides the origin, not the withdrawal) or leave from a separate wallet we have not identified; we found no sign of one, since only {{cust_unpaid}} public withdrawals went unpaid by this wallet. Either way, the residual is not money leaving custody unseen through the main bridge. What stays invisible to every method is a confidential swap whose output never leaves Intents.
- **Base-layer activity was mostly one app.** In March, {{blk_share}} of transactions went to `{{blk_group}}` accounts, signed by `{{blk_signer}}` (about {{blk_daily}} a day). That sender explains about {{blk_explained}} of the fall from {{blk_pre}} to {{blk_post}} daily transactions. October's largest groups are {{blk_post_top}}. Network-level activity now: {{txns30}} transactions and {{aa30}} active accounts per day on average.
- **Developers are fewer.** Electric Capital counts {{dev_all}} monthly-active NEAR developers ({{dev_as_of}}), down {{dev_chg_1y}} in a year and {{dev_chg_4y}} from four years ago, from a peak of {{dev_peak}} in {{dev_peak_month}}. Full-time developers held at {{dev_full_time}} ({{dev_ft_chg_1y}} y/y), so the loss is in casual contributors. NEAR ranks {{dev_rank}} of {{dev_peers_n}} peer chains on all developers and {{dev_rank_ft}} on full-time (ledger C19, FAIL).
- **October fell {{oct_chg}}** from the September record. One month is noise; two more would be a trend.
- **Oct 1, 2026 exploit**: $3.8M taken from the Omni deposit layer, returned in full, services paused for hours. Cross-chain settlement has an attack surface the L1 does not.
- **MPC and private shard trust.** Chain Signatures runs on 15 participants with threshold 10 (read from `v1.signer`); the confidential shard is permissioned.
- **Dashboard discrepancies.** revenue.near.org calls its figures "illustrative" and counts only sweeps from `intents.near`; the chain balance is higher (ledger C09).
- **BigQuery cross-check done, by hand.** The NEAR public BigQuery dataset is still fresh to 2026-11-10 (the March 2026 NEAR Lake deprecation did not stop it). Daily transactions and active accounts matched NearBlocks digit for digit on all 13 days compared. It also shows that only about 400 to 1,000 accounts a day send calls to `intents.near` while calls rose from about 55k to 100-300k a day, and that calls per $1M of volume swung from 600 to 2,400, so call counts are not used as a growth measure. Results are in `data/bigquery/`. The full 120-day series was not exported; only the compared days are stored.
- **Unverifiable from public data**: confidential TVL, NEAR AI inference staking, ETF holdings (ledger C12 to C14).

## 8. Claims ledger ({{n_pass}} PASS, {{n_partial}} PARTIAL, {{n_unver}} UNVERIFIABLE, {{n_fail}} FAIL)

{{ledger_table}}

## 9. Time horizon and how to re-check

Three pre-registered predictions with thresholds and a settle date of 2027-03-31 are in `thesis/PREDICTIONS.md` (frozen by hash); `make check` scores them.


Three to five years for the thesis; a quarterly re-run of `make refresh && make report` for the evidence. The HSP-029 vote has passed (C20); the next tests are the validator upgrade that activates it, and whether realised issuance (network page) starts to fall in 2027. `pipeline/fetch_hos.py` reads the proposal state from `vote.dao` on every refresh.
