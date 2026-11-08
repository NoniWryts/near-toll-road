# Toll Road: does NEAR's fee switch pay for the chain?

*An investment thesis for NEAR Protocol (NEAR) built from on-chain data. Snapshot `2026-11-01`, data through 2026-10-30. Every number below is written by `thesis/render.py` from `reports/tables/`; nothing is typed by hand. Re-run `make report` and the text updates. Not investment advice.*

## 1. The claim, and what would falsify it

**Thesis.** NEAR has turned a cross-chain product, NEAR Intents, into a measurable revenue line for the token: a fee on every swap is converted to NEAR and swept on-chain into a buyback wallet. If that revenue grows to cover the value of new NEAR issuance, NEAR becomes one of the few Layer-1 tokens whose supply is paid for by a product rather than by holders. That is the long-term case.

**Where it stands today.** The mechanism is real and visible on-chain (ledger C01). It is also small: in the last 30 days NEAR bought back 282,241 NEAR against 2.65M NEAR issued, a coverage of **10.6%**. Issuance runs 9.4x buybacks. At the measured fee rate (16.0 bps of volume) and capture rate (34.2%), Intents would need **$718M of volume per day** to cover 2.5% issuance, versus $130M today, a 5.5x gap. HSP-029 passed on Nov 2, 2026 (ledger C20: 3.29M veNEAR for, 0 veNEAR against, turnout 62%). It does not cut issuance to 1.6% at once: after a 14-day timelock, a validator upgrade and a ~90-day buffer, the cap ramps down by about 3.75 bps a month for 24 months. At the end of 2027 the cap is near 2.13%, where breakeven is $611M per day; at the 1.6% end point (2029) it is $459M per day (3.5x today's volume).

**Kill criteria** (set now, before the data moves):
1. Trailing-90-day capture below 20% *and* 30-day volume below $120M/day at the end of Q2 2027: the flywheel thesis fails.
2. Buyback coverage of issuance still below 25% at the end of 2027 with HSP-029 in force: the token-value-accrual thesis fails even if the product succeeds.
3. Top-10 sender concentration of public Intents volume above 60% for two consecutive quarters: adoption is not broad (not yet measurable here, see §7).
4. A second settlement-layer exploit without full recovery, or MPC signer set below 10 independent operators.

## 2. Market catalyst

Crypto activity is fragmented across chains, and the next wave of users (wallets, agents, treasuries) wants outcomes, not routes. NEAR Intents sells that outcome: the user signs what they want, solvers compete to fill it, `intents.near` settles atomically across 35+ chains with no bridge. Three things happened in 2026 that make this measurable: the fee switch (Feb 23), Confidential Intents going GA (Jul 7), and the Bitwise spot ETF (NRR, Sep 29). The HSP-029 issuance vote closes Nov 2 and is the live catalyst for the next quarter.

## 3. Evidence: the flywheel in numbers

| | Trailing 30d | Lifetime |
|---|---|---|
| Intents volume | $3.91B ($130M/day) | $35.9B |
| Gross fees | $6.26M (16.0 bps) | $58.0M |
| Revenue captured by NEAR | $2.14M (capture 34.2%; 90d 27.0%) | $9.2M (capture 15.9%) |
| NEAR swept into buyback wallet | 282,241 NEAR ($1.37M) | 1,641,664 NEAR ($4.47M), 3,073 receipts since 2026-04-23 |
| NEAR issued | 2.65M NEAR ($13.0M), 2.46% annualised | |
| Buyback coverage of issuance | **10.6%** | |

September 2026 was the record month ($4.80B volume, capture 25%); October fell to $3.91B (-19%) while capture rose to 34%. In October the wallet received 297,257 NEAR against 2.73M issued.

What the buyback wallet actually holds: 2,148,000 NEAR, liquid, in a multisig. Zero is staked and zero is burned (ledger C02), although the tokenomics post describes repurchased NEAR as "staked or locked". The buyback wallet receives 64% of captured revenue; the remainder sits in the two Sputnik DAO fee wallets. Coverage in this thesis is therefore a comparison of flows, not a supply model. Net supply still grows at roughly 2.46% a year.

## 4. Competitive edge, as far as the data reaches

- **A product with a take rate.** Few L1s have a revenue line that is not gas. NEAR's base-layer gas fees were $0.18M in 30 days; Intents fees were $6.26M. The product earns more than the chain.
- **Distribution.** Volume comes through Brave, Ledger, Trust Wallet, Rabby, SwapKit and near.com. The capture rate has risen as near.com's own share grew (28% to 34.2% across October), which is the mechanism by which margin improves.
- **Confidential execution.** Roughly a tenth of all-time volume and most of recent growth ran through the confidential shard. This is NEAR-reported and not independently observable (ledger C12), so this thesis treats it as a product signal, not as audited volume.
- **Chain Signatures is real but internal.** About 16,857 sign requests a day reach the MPC contract (extrapolated from a 3.5-hour sample of 7,489 receipts; 26.4M lifetime receipts). 92% of them come from NEAR's own Intents bridge and FastAuth. The "agents signing on any chain" story is not yet visible in who calls the contract.
- **It is the biggest venue of its kind that DefiLlama can see.** $3.86B of 30-day volume puts Intents at rank 1 of 30 when placed among DefiLlama's bridge aggregators (41% of that list; next LI.FI Bridge Aggregator $1.41B; 0x Bridge Aggregator $1.05B; SOCKET Protocol $0.96B) and rank 6 of 144 among swap aggregators (leader Jupiter Aggregator). Canonical bridges and exchanges are outside this comparison, and DefiLlama's own 30-day change for Intents is -41%.
- **Security budget.** 375 validators, 45.2% of supply staked, Nakamoto coefficient 9 at the one-third threshold, top-10 share 36%.

## 5. Valuation: what the market is paying for

At $4.38 NEAR's market cap is $5.74B. On annualised 30-day figures that is 75x Intents gross fees and 220x captured Intents revenue. On base-layer gas alone it is 2,574x fees (Ethereum 1,031x, Solana 210x, same DefiLlama definition). Headlines that quote a "56x fee multiple" use gross fees; the token only sees the captured share.

2030 scenarios (arithmetic on `params.yaml`, not forecasts): bear revenue $5M/yr covering 0.03x issuance, implied cap $0.10B; base $71M/yr, 0.73x, $2.85B (0.50x today); bull $239M/yr, 2.44x, $14.31B (2.49x today). The spread says what the current price assumes: sustained 35%+ volume growth with capture at or above 30%. The bear row is deliberately uncomfortable; a revenue-only valuation does not support today's price if the flywheel stalls.

## 6. Variant perception

The market prices NEAR as an "AI chain" narrative or as a generic alt-L1. The more useful lens is a settlement business with a visible P&L. That lens is less flattering today (coverage 10.6%) but it is the only one that can be checked monthly, and it is the one where NEAR's own governance is now acting: HSP-029, now passed, attacks the denominator (issuance), the near.com share attacks the numerator (capture).

## 7. Risks and honest limits

- **Issuance outruns buybacks** by 9.4x. Bought NEAR is held, not retired.
- **Volume is not users, but it is not one whale either.** A seeded sample of 44,500 `intents.near` transactions (17 hours across September and October) shows 70% of payout value signed by one-time accounts 1Click creates per quote, so the Explorer's "426,779 unique users" counts swaps, not people (ledger C21, FAIL). Measured on payout destinations instead, the top 10 receive 36% of value and the top 1 16% (HHI 314, unconcentrated). At least 36% of October's sampled payout value went to destinations also paid in September (a lower bound). Round-trip trading by non-market-maker signers is rare (0.8% of signer windows). Money inside Intents is concentrated at the other end: the top 5 transfer signers (solvers and pools) move 80% of value.
- **The confidential share is not measurable.** The same 30-day total split 41% confidential on 2026-10-31 and 0% a week later, after the public series was revised (ledger C22).
- **Base-layer activity was mostly one app.** In March, 62% of transactions went to `users.kaiching` accounts, signed by `hotwallet.kaiching` (about 2.1M a day). That sender explains about 77% of the fall from 3.48M to 0.73M daily transactions. October's largest groups are hot.tg 11%; ref-finance.near 10%; intents.near 9%; jars-oracle.sweat 7%; spin.sweat 7%. Network-level activity now: 715,881 transactions and 72,378 active accounts per day on average.
- **Developers are fewer.** Electric Capital counts 582 monthly-active NEAR developers (2026-10-24), down 28% in a year and 60% from four years ago, from a peak of 1,804 in 2022-05. Full-time developers held at 278 (+6% y/y), so the loss is in casual contributors. NEAR ranks 9 of 13 peer chains on all developers and 7 on full-time (ledger C19, FAIL).
- **October fell -19%** from the September record. One month is noise; two more would be a trend.
- **Oct 1, 2026 exploit**: $3.8M taken from the Omni deposit layer, returned in full, services paused for hours. Cross-chain settlement has an attack surface the L1 does not.
- **MPC and private shard trust.** Chain Signatures runs on 15 participants with threshold 10 (read from `v1.signer`); the confidential shard is permissioned.
- **Dashboard discrepancies.** revenue.near.org calls its figures "illustrative" and counts only sweeps from `intents.near`; the chain balance is higher (ledger C09).
- **BigQuery not run.** The track prompt points at the NEAR public BigQuery dataset. The three queries are in `sql/` and run with a GCP project; this snapshot used NearBlocks for the same daily series because docs.near.org notes the dataset's NEAR Lake source was deprecated on 2026-03-24, so recent dates need checking before they are trusted.
- **Unverifiable from public data**: confidential TVL, NEAR AI inference staking, ETF holdings (ledger C12 to C14).

## 8. Claims ledger (10 PASS, 5 PARTIAL, 4 UNVERIFIABLE, 3 FAIL)

| id | status | claim | observed |
|---|---|---|---|
| C01 | PASS | Intents fees are being used to buy NEAR (buyback programme live since 2026-02-23) | 3073 automated TRANSFER receipts from intents.near, 1,641,664 NEAR, first on 2026-04-23 |
| C02 | FAIL | Repurchased NEAR is 'staked or locked' (tokenomics post wording) | wallet balance 2,148,000 NEAR; locked 0; delegated pools: 0 |
| C03 | PASS | Issuance runs ~6.0x buybacks (Ternullo, Bankless, Oct 6 2026) | trailing 30d: 2,651,763 NEAR issued vs 282,241 NEAR bought = 9.4x; coverage 10.6% |
| C04 | PASS | Lifetime fee capture 16.4% (NEAR Q3 update, Oct 6) | 15.9% = all-time captured revenue / all-time gross fees (DefiLlama series) |
| C05 | PARTIAL | Trailing-30d fee capture 28.4% (Oct 6) | 34.2% for the 30 days to 2026-10-30 |
| C06 | PARTIAL | Q3 2026 Intents volume $10.4B (Nansen) | $9.79B Jul 1 - Sep 30 (DefiLlama daily) |
| C07 | PASS | Cumulative Intents volume above $32B | $35.9B all-time (DefiLlama) |
| C08 | PARTIAL | More than $8M captured for buybacks (Nansen Q3) | $4.47M = sweeps x daily price; wallet holds 2,148,000 NEAR ($9.4M today) |
| C09 | PARTIAL | revenue.near.org wallet figure equals the on-chain balance of the buyback wallet | dashboard 1,646,934 NEAR vs chain 2,148,000 NEAR (diff 501,066); sweeps from intents.near total 1,641,664 |
| C10 | PASS | Staking ratio ~46% (Bitwise, Oct 2026) | 45.2% = 591.9M staked / 1311M total supply |
| C11 | PASS | ~403.0 active validators (CryptoTicker, Oct 18) | 375 in the current epoch |
| C12 | UNVERIFIABLE | Confidential Intents TVL ~$150M | no public contract state or indexer exposes the private shard |
| C13 | UNVERIFIABLE | >1M NEAR staked for NEAR AI inference (Oct 21) | no staking pool or contract account is named by NEAR AI |
| C14 | UNVERIFIABLE | Bitwise NRR holds ~16.84M NEAR (Oct 28) | fund page is not machine-readable without a browser; no on-chain custody address published |
| C15 | PARTIAL | HSP-029 text: staking ratio 42.71% at block 216,701,043 (Sep 22) | 45.16% at block 222583497 (Nov 1); direction: up |
| C16 | PASS | September 2026 was a record month ($4.80B) and October fell (~$3.99B) | Sep $4.80B, Oct $3.91B (-18.5%) |
| C17 | PASS | Chain Signatures is used in production (NEAR docs, Messari); scale and who uses it are not published | ~16,857 sign calls/day (extrapolated from 7,489 receipts over 3.5 h); lifetime receipts 26,383,939; 92% of sign calls come from NEAR's own bridge/FastAuth contracts |
| C18 | PASS | NEAR Intents is the largest cross-chain swap/bridge venue by volume (near.org and Intents team framing) | 30d volume $3.86B. Ranked against DefiLlama's bridge aggregators: 1 of 30 (next: LI.FI Bridge Aggregator $1.41B; 0x Bridge Aggregator $1.05B; SOCKET Protocol $0.96B). Against swap aggregators: 6 of 144 (leader Jupiter Aggregator $13.4B). Among DefiLlama's own Bridge-category venues: next Unit $1.99B; Maya Protocol $0.53B; TeleSwap $0.04B. Rank 17 of 1100 in the whole DEX-volume overview |
| C19 | FAIL | NEAR's developer ecosystem is growing (recurring ecosystem framing in NEAR Foundation posts) | Electric Capital monthly-active developers 582 on 2026-10-24 vs 805 a year earlier (-28%) and 1453 four years earlier (-60%); full-time 278 vs 262 (+6%); rank 9 of 13 peer chains, rank 7 on full-time |
| C20 | PASS | HSP-029 (issuance 2.5% -> 1.6% over 24 months) passed the House of Stake vote closing 2026-11-02 (The Defiant: 18 for, 1 against while live) | vote.dao proposal 29 status Timelock: for 3,287,729 veNEAR (32 votes), against 0 (1), abstain 1,071 (3); turnout 62.3% of 5,274,745 veNEAR (quorum 35%), approval 100.00% (threshold 66.67%) |
| C21 | FAIL | NEAR Intents served ~426,779 unique users in 30 days (Explorer feed as mirrored by nearstats.org) | 426,779 'users' for 426,878 swaps; on-chain sample: 70% of payout value signed by per-quote 64-hex accounts; 9,952 distinct payout destinations in 17,468 sampled payouts, top 10 destinations 36% of value (excluding bridge-routed payouts, 33%) |
| C22 | UNVERIFIABLE | A large share of Intents volume is confidential (NEAR revenue dashboard series; NearStats residual) | confidential residual 41% of 30-day volume as of 2026-10-31, 0% as of 2026-11-07, total unchanged |

## 9. Time horizon and how to re-check

Three pre-registered predictions with thresholds and a settle date of 2027-03-31 are in `thesis/PREDICTIONS.md` (frozen by hash); `make check` scores them.


Three to five years for the thesis; a quarterly re-run of `make refresh && make report` for the evidence. The HSP-029 vote has passed (C20); the next tests are the validator upgrade that activates it, and whether realised issuance (network page) starts to fall in 2027. `pipeline/fetch_hos.py` reads the proposal state from `vote.dao` on every refresh.
