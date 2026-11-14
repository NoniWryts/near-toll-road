# Toll Road: does NEAR's fee switch pay for the chain?

*An investment thesis for NEAR Protocol (NEAR) built from on-chain data. Snapshot `2026-11-12`, data through 2026-11-10. Every number below is written by `thesis/render.py` from `reports/tables/`; nothing is typed by hand. Re-run `make report` and the text updates. Not investment advice.*

## 1. The claim, and what would falsify it

**Why this matters.** Every blockchain has to pay the computers that run it, and most pay by printing new coins. On Ethereum 93% of staking rewards are newly minted ETH, and on Solana over 90% (Bitwise, Q2 2026). Holders just own a slightly smaller share each month. NEAR printed 2.66 million new NEAR in the last 30 days too, but a fee on every Intents swap now buys NEAR back, so for once a product pays toward that bill and it can be measured. Owning NEAR is a bet on Intents growing, not on the fee switch as it stands; the kill criteria below say when we would walk away.

**Thesis.** NEAR has turned a cross-chain product, NEAR Intents, into a measurable revenue line for the token: a fee on every swap is converted to NEAR and swept on-chain into a buyback wallet. If that revenue grows to cover the value of new NEAR issuance, NEAR becomes one of the few Layer-1 tokens whose supply is paid for by a product rather than by holders. That is the long-term case.

**Where it stands today.** The mechanism is real and visible on-chain (ledger C01). It is also small: in the last 30 days NEAR bought back 290,497 NEAR against 2.66M NEAR issued, a coverage of **10.9%**. Issuance runs 9.2x buybacks. At the measured fee rate (15.9 bps of volume) and capture rate (30.4%), Intents would need **$630M of volume per day** to cover 2.5% issuance, versus $125M today, a 5.0x gap. HSP-029 passed on Nov 2, 2026 (ledger C20: 3.29M veNEAR for, 0 veNEAR against, turnout 62%). It does not cut issuance to 1.6% at once: after a 14-day timelock, a validator upgrade and a ~90-day buffer, the cap ramps down by about 3.75 bps a month for 24 months. At the end of 2027 the cap is near 2.13%, where breakeven is $536M per day; at the 1.6% end point (2029) it is $403M per day (3.2x today's volume).

**Kill criteria** (set now, before the data moves):
1. Trailing-90-day capture below 20% *and* 30-day volume below $120M/day at the end of Q2 2027: the flywheel thesis fails.
2. Buyback coverage of issuance still below 25% at the end of 2027 with HSP-029 in force: the token-value-accrual thesis fails even if the product succeeds.
3. Top-10 sender concentration of public Intents volume above 60% for two consecutive quarters: adoption is not broad (not yet measurable here, see §7).
4. A second settlement-layer exploit without full recovery, or MPC signer set below 10 independent operators.

## 2. Market catalyst

Crypto activity is fragmented across chains, and the next wave of users (wallets, agents, treasuries) wants outcomes, not routes. NEAR Intents sells that outcome: the user signs what they want, solvers compete to fill it, `intents.near` settles atomically across 35+ chains with no bridge. Three things happened in 2026 that make this measurable: the fee switch (Feb 23), Confidential Intents going GA (Jul 7), and the Bitwise spot ETF (NRR, Sep 29). The HSP-029 issuance vote closes Nov 2 and is the live catalyst for the next quarter.

### What the chain looked like before the buybacks

The fee switch went live on 2026-02-23; the first sweep reached the buyback wallet on 2026-04-23, 59 days later. Before it, the chain was already shrinking: active accounts fell from about 883k a day in January 2025 to 233k a day in the months before the switch (74% lower; transactions 47% lower). New NEAR was being printed at about 4.8% of supply a year until the inflation cap was halved in late October 2025, and about 2.4% after. Over the same months the NEAR price fell with the whole market (2025-11-13 to 2026-02-23: NEAR -58%, SOL -44%, ETH -42%); since the switch NEAR is +240% against SOL -3% and ETH +4% (to 2026-11-11). Buybacks so far total $4.9M against about $431M of NEAR traded on an average day, so we treat the rally as timing worth noting, not as proof that buybacks caused it. Issuance was halved and a reward app stopped in the same months, so this is a before-and-after description, not a causal estimate.

**Why a buyback was not possible earlier.** (1) There was no revenue to spend: Intents collected almost no fees until 2025-06-11, and NEAR's own cut was about $36 in total before November 2025 (DefiLlama). (2) The first fix chosen was a smaller printing press, not a buyer: a community proposal on 24 June 2025 argued that 5% a year was more than the network needed, and the cut to 2.5% took effect with the nearcore 2.9.0 upgrade in late October 2025. (3) Burning gas fees was too small to offset issuance: the same proposal put the burn at about 0.1% of supply a year; by our estimate (70% of gas fees burned) it covered only 2.8% of the value of new NEAR between November 2025 and the switch. We could not find a primary NEAR source stating why the buyback itself was chosen in February 2026, so that reading is ours. Data: `reports/tables/prebuyback_monthly.csv`, `analysis/prebuyback.py`.

## 3. Evidence: the flywheel in numbers

| | Trailing 30d | Lifetime |
|---|---|---|
| Intents volume | $3.76B ($125M/day) | $37.3B |
| Gross fees | $5.96M (15.9 bps) | $60.3M |
| Revenue captured by NEAR | $1.81M (capture 30.4%; 90d 27.1%) | $9.8M (capture 16.2%) |
| NEAR swept into buyback wallet | 290,497 NEAR ($1.27M) | 1,751,335 NEAR ($4.88M), 3,318 receipts since 2026-04-23 |
| NEAR issued | 2.66M NEAR ($11.9M), 2.47% annualised | |
| Buyback coverage of issuance | **10.9%** | |

September 2026 was the record month ($4.80B volume, capture 25%); October fell to $3.99B (-17%) while capture rose to 34%. In October the wallet received 297,257 NEAR against 2.73M issued.

What the buyback wallet actually holds: 2,254,502 NEAR, liquid, in a multisig. Zero is staked and zero is burned (ledger C02), although the tokenomics post describes repurchased NEAR as "staked or locked". The buyback wallet receives 70% of captured revenue; the remainder sits in the two Sputnik DAO fee wallets. Coverage in this thesis is therefore a comparison of flows, not a supply model. Net supply still grows at roughly 2.47% a year.

## 4. Competitive edge, as far as the data reaches

- **A product with a take rate.** Few L1s have a revenue line that is not gas. NEAR's base-layer gas fees were $0.13M in 30 days; Intents fees were $5.96M. The product earns more than the chain.
- **Distribution.** Volume comes through Brave, Ledger, Trust Wallet, Rabby, SwapKit and near.com. The capture rate has risen as near.com's own share grew (28% to 30.4% across October), which is the mechanism by which margin improves.
- **Confidential execution.** Roughly a tenth of all-time volume and most of recent growth ran through the confidential shard. This is NEAR-reported and not independently observable (ledger C12), so this thesis treats it as a product signal, not as audited volume.
- **Chain Signatures is real but internal.** About 14,263 sign requests a day reach the MPC contract, counted in full over 30 days in NEAR's BigQuery data, not estimated. 90% of them come from NEAR's own Intents bridge and FastAuth. The number of distinct accounts calling sign fell from about 179 a day in mid-October to about 92 a day in early November, so the same demand now comes from fewer callers. The "agents signing on any chain" story is not yet visible in who calls the contract.
- **It is the biggest venue of its kind that DefiLlama can see.** $3.73B of 30-day volume puts Intents at rank 1 of 35 when placed among DefiLlama's bridge aggregators (39% of that list; next LI.FI Bridge Aggregator $1.54B; 0x Bridge Aggregator $1.38B; SOCKET Protocol $0.86B) and rank 6 of 151 among swap aggregators (leader Jupiter Aggregator). Canonical bridges and exchanges are outside this comparison, and DefiLlama's own 30-day change for Intents is -19%.
- **Security budget.** 353 validators, 44.5% of supply staked, Nakamoto coefficient 9 at the one-third threshold, top-10 share 36%.

## 5. Valuation: what the market is paying for

At $3.38 NEAR's market cap is $4.44B. On annualised 30-day figures that is 61x Intents gross fees and 201x captured Intents revenue. On base-layer gas alone it is 2,717x fees (Ethereum 1,010x, Solana 234x, same DefiLlama definition). Headlines that quote a "56x fee multiple" use gross fees; the token only sees the captured share.

2030 scenarios (arithmetic on `params.yaml`, not forecasts): bear revenue $5M/yr covering 0.04x issuance, implied cap $0.10B; base $68M/yr, 0.90x, $2.73B (0.62x today); bull $229M/yr, 3.03x, $13.75B (3.10x today). The spread says what the current price assumes: sustained 35%+ volume growth with capture at or above 30%. The bear row is deliberately uncomfortable; a revenue-only valuation does not support today's price if the flywheel stalls.

## 6. Variant perception

The market prices NEAR as an "AI chain" narrative or as a generic alt-L1. The more useful lens is a settlement business with a visible P&L. That lens is less flattering today (coverage 10.9%) but it is the only one that can be checked monthly, and it is the one where NEAR's own governance is now acting: HSP-029, now passed, attacks the denominator (issuance), the near.com share attacks the numerator (capture).

## 7. Risks and honest limits

- **Issuance outruns buybacks** by 9.2x. Bought NEAR is held, not retired.
- **Volume is not users, but it is not one whale either.** A seeded sample of 37,750 `intents.near` transactions (14 hours across September and October) shows 71% of payout value signed by one-time accounts 1Click creates per quote, so the Explorer's "438,653 unique users" counts swaps, not people (ledger C21, FAIL). Measured on payout destinations instead, the top 10 receive 31% of value and the top 1 10% (HHI 177, unconcentrated). At least 27% of October's sampled payout value went to destinations also paid in September (a lower bound). Round-trip trading by non-market-maker signers is rare (1.0% of signer windows). Money inside Intents is concentrated at the other end: the top 5 transfer signers (solvers and pools) move 77% of value.
- **The confidential share is not measurable as a residual, but it can be bounded by custody.** The same 30-day total split 0% confidential on 2026-11-11 and 0% a week later, after the public series was revised (ledger C22): a residual absorbs missed data and private flow alike. So we reconciled custody instead. Confidential swaps must still pay out on the destination chain, so for USDT on Tron we read every payout from the bridge's Tron hot wallet and every public withdrawal on NEAR, 2026-11-03 to 2026-11-10. 100.0% of 18,276 payouts ($156.6M) match a public `intents.near` withdrawal (median fee 0.83 USDT, median delay 12 s); 0.0% ($0) left custody with no public record (ledger C23). So the bridge wallet pays out nothing that is not publicly withdrawn on NEAR. A confidential payout on this route must therefore either pass through a public NEAR withdrawal (the private shard hides the origin, not the withdrawal) or leave from a separate wallet we have not identified; we found no sign of one, since only 0 of 17,999 public withdrawals went unpaid by this wallet. Either way, the residual is not money leaving custody unseen through the main bridge. What stays invisible to every method is a confidential swap whose output never leaves Intents.
- **Base-layer activity was mostly one app.** In March, 62% of transactions went to `users.kaiching` accounts, signed by `hotwallet.kaiching` (about 2.2M a day). That sender explains about 78% of the fall from 3.48M to 0.73M daily transactions. October's largest groups are ref-finance.near 15%; jars-oracle.sweat 9%; intents.near 8%; spin.sweat 7%; hot.tg 6%. Network-level activity now: 663,839 transactions and 62,933 active accounts per day on average.
- **Developers are fewer.** Electric Capital counts 580 monthly-active NEAR developers (2026-11-04), down 26% in a year and 60% from four years ago, from a peak of 1,804 in 2022-05. Full-time developers held at 268 (+4% y/y), so the loss is in casual contributors. NEAR ranks 9 of 13 peer chains on all developers and 7 on full-time (ledger C19, FAIL).
- **October fell -17%** from the September record. One month is noise; two more would be a trend.
- **Oct 1, 2026 exploit**: $3.8M taken from the Omni deposit layer, returned in full, services paused for hours. Cross-chain settlement has an attack surface the L1 does not.
- **MPC and private shard trust.** Chain Signatures runs on 16 participants with threshold 11 (read from `v1.signer`); the confidential shard is permissioned.
- **Dashboard discrepancies.** revenue.near.org calls its figures "illustrative" and counts only sweeps from `intents.near`; the chain balance is higher (ledger C09).
- **BigQuery cross-check done, by hand.** The NEAR public BigQuery dataset is still fresh to 2026-11-10 (the March 2026 NEAR Lake deprecation did not stop it). Daily transactions and active accounts matched NearBlocks digit for digit on all 13 days compared. It also shows that only about 400 to 1,000 accounts a day send calls to `intents.near` while calls rose from about 55k to 100-300k a day, and that calls per $1M of volume swung from 600 to 2,400, so call counts are not used as a growth measure. Results are in `data/bigquery/`. The full 120-day series was not exported; only the compared days are stored.
- **Unverifiable from public data**: confidential TVL, NEAR AI inference staking, ETF holdings (ledger C12 to C14).

## 8. Claims ledger (10 PASS, 6 PARTIAL, 4 UNVERIFIABLE, 3 FAIL)

| id | status | claim | observed |
|---|---|---|---|
| C01 | PASS | Intents fees are being used to buy NEAR (buyback programme live since 2026-02-23) | 3318 automated TRANSFER receipts from intents.near, 1,751,335 NEAR, first on 2026-04-23 |
| C02 | FAIL | Repurchased NEAR is 'staked or locked' (tokenomics post wording) | wallet balance 2,254,502 NEAR; locked 0; delegated pools: 0 |
| C03 | PASS | Issuance runs ~6.0x buybacks (Ternullo, Bankless, Oct 6 2026) | trailing 30d: 2,663,857 NEAR issued vs 290,497 NEAR bought = 9.2x; coverage 10.9% |
| C04 | PASS | Lifetime fee capture 16.4% (NEAR Q3 update, Oct 6) | 16.2% = all-time captured revenue / all-time gross fees (DefiLlama series) |
| C05 | PASS | Trailing-30d fee capture 28.4% (Oct 6) | 30.4% for the 30 days to 2026-11-10 |
| C06 | PARTIAL | Q3 2026 Intents volume $10.4B (Nansen) | $9.79B Jul 1 - Sep 30 (DefiLlama daily) |
| C07 | PASS | Cumulative Intents volume above $32B | $37.3B all-time (DefiLlama) |
| C08 | PARTIAL | More than $8M captured for buybacks (Nansen Q3) | $4.88M = sweeps x daily price; wallet holds 2,254,502 NEAR ($7.6M today) |
| C09 | PARTIAL | revenue.near.org wallet figure equals the on-chain balance of the buyback wallet | dashboard 1,751,826 NEAR vs chain 2,254,502 NEAR (diff 502,676); sweeps from intents.near total 1,751,335 |
| C10 | PASS | Staking ratio ~46% (Bitwise, Oct 2026) | 44.5% = 583.2M staked / 1312M total supply |
| C11 | PARTIAL | ~403.0 active validators (CryptoTicker, Oct 18) | 353 in the current epoch |
| C12 | UNVERIFIABLE | Confidential Intents TVL ~$150M | no public contract state or indexer exposes the private shard |
| C13 | UNVERIFIABLE | >1M NEAR staked for NEAR AI inference (Oct 21) | no staking pool or contract account is named by NEAR AI |
| C14 | UNVERIFIABLE | Bitwise NRR holds ~16.84M NEAR (Oct 28) | fund page is not machine-readable without a browser; no on-chain custody address published |
| C15 | PARTIAL | HSP-029 text: staking ratio 42.71% at block 216,701,043 (Sep 22) | 44.46% at block 224224263 (Nov 1); direction: up |
| C16 | PASS | September 2026 was a record month ($4.80B) and October fell (~$3.99B) | Sep $4.80B, Oct $3.99B (-17.0%) |
| C17 | PASS | Chain Signatures is used in production (NEAR docs, Messari); scale and who uses it are not published | 14,263 sign calls/day, counted in full over 30 days (427,886 calls, NEAR BigQuery); 90% of sign calls come from NEAR's own bridge/FastAuth contracts; distinct callers fell from 179/day to 92/day |
| C18 | PASS | NEAR Intents is the largest cross-chain swap/bridge venue by volume (near.org and Intents team framing) | 30d volume $3.73B. Ranked against DefiLlama's bridge aggregators: 1 of 35 (next: LI.FI Bridge Aggregator $1.54B; 0x Bridge Aggregator $1.38B; SOCKET Protocol $0.86B). Against swap aggregators: 6 of 151 (leader Jupiter Aggregator $13.4B). Among DefiLlama's own Bridge-category venues: next Unit $2.13B; Maya Protocol $0.47B; TeleSwap $0.04B. Rank 18 of 1144 in the whole DEX-volume overview |
| C19 | FAIL | NEAR's developer ecosystem is growing (recurring ecosystem framing in NEAR Foundation posts) | Electric Capital monthly-active developers 580 on 2026-11-04 vs 789 a year earlier (-26%) and 1452 four years earlier (-60%); full-time 268 vs 257 (+4%); rank 9 of 13 peer chains, rank 7 on full-time |
| C20 | PASS | HSP-029 (issuance 2.5% -> 1.6% over 24 months) passed the House of Stake vote closing 2026-11-02 (The Defiant: 18 for, 1 against while live) | vote.dao proposal 29 status Timelock: for 3,287,729 veNEAR (32 votes), against 0 (1), abstain 1,071 (3); turnout 62.3% of 5,274,745 veNEAR (quorum 35%), approval 100.00% (threshold 66.67%) |
| C21 | FAIL | NEAR Intents served ~438,653 unique users in 30 days (Explorer feed as mirrored by nearstats.org) | 438,653 'users' for 438,776 swaps; on-chain sample: 71% of payout value signed by per-quote 64-hex accounts; 11,309 distinct payout destinations in 14,930 sampled payouts, top 10 destinations 31% of value (excluding bridge-routed payouts, 0%) |
| C22 | UNVERIFIABLE | A large share of Intents volume is confidential (NEAR revenue dashboard series; NearStats residual) | confidential residual 0% of 30-day volume as of 2026-11-11, 0% as of 2026-11-07, total unchanged |
| C23 | PARTIAL | Confidential swaps still settle on the destination chain as standard public transactions; only the origin and route are hidden | 100.0% of 18,276 USDT on Tron payouts ($156.6M, 2026-11-03 to 2026-11-10) traced to a public intents.near withdrawal; median bridge fee 0.83 USDT, median delay 12s |

## 9. Time horizon and how to re-check

Three pre-registered predictions with thresholds and a settle date of 2027-03-31 are in `thesis/PREDICTIONS.md` (frozen by hash); `make check` scores them.


Three to five years for the thesis; a quarterly re-run of `make refresh && make report` for the evidence. The HSP-029 vote has passed (C20); the next tests are the validator upgrade that activates it, and whether realised issuance (network page) starts to fall in 2027. `pipeline/fetch_hos.py` reads the proposal state from `vote.dao` on every refresh.
