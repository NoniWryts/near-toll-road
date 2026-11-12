# Toll Road: does NEAR's fee switch pay for the chain?

A long-term investment thesis for NEAR Protocol, built so that every number can be re-derived from the repo. NEAR Hackathon 2026, track `thesis` (Investment Thesis).

**Live dashboard:** https://noniwryts.github.io/near-toll-road/ (the `dashboard/` folder, served from the `gh-pages` branch; no install needed).

**Why this matters.** Every blockchain has to pay the computers that run it, and most pay by printing new coins. On Ethereum 93% of staking rewards are newly minted ETH, and on Solana over 90% (Bitwise, Q2 2026). Holders just own a slightly smaller share each month. NEAR prints about 2.7M new NEAR a month too, but since February 2026 a fee on every NEAR Intents swap is turned into NEAR and sent to a buyback wallet, so for once a chain's own product pays toward that bill and it can be measured. Owning NEAR is therefore a bet on Intents growing, not on the fee switch as it stands. The kill criteria in the thesis say when we would walk away.

**The question.** Since February 2026 a cut of every NEAR Intents swap is converted to NEAR and swept on-chain into a buyback wallet. Does that revenue cover the value of new NEAR issuance, and what would have to be true for it to?

**The answer today** (snapshot 2026-11-12, data to 2026-11-10): the mechanism is real and small. Buybacks covered about 11% of issuance over the last 30 days. Intents needs roughly 5.0x today's volume at today's fee and capture rates to break even at 2.5% issuance, or 3.2x if HSP-029 cuts issuance to 1.6%. Bought NEAR is held in a multisig, not staked or burned. The full argument, the evidence and the kill criteria are in [`thesis/THESIS.md`](thesis/THESIS.md).

Everything is regenerated from committed, dated snapshots. No API keys are needed to reproduce the report.

## Do X, see Y

| Do | See |
|---|---|
| `make setup` | dependencies installed (pandas, pyarrow, plotly, pyyaml, requests, pytest) |
| `make report` | `reports/tables/*.csv`, `dashboard/*.html` (13 pages), `thesis/THESIS.md` and `thesis/claims_ledger.csv` rebuilt from `data/snapshots/2026-11-01/` in under a minute |
| `make check` | the 23-row claims ledger re-verified (10 PASS, 6 PARTIAL, 4 UNVERIFIABLE, 3 FAIL) and 23 tests passing. C19 is red because Electric Capital's data shows fewer NEAR developers, not more. C02 is red on purpose: the tokenomics post says bought NEAR is "staked or locked"; the wallet shows 0 staked |
| `python -m checks.predictions` | three pre-registered calls (HSP-029 live in protocol, 90d capture >= 30%, 90d buyback coverage >= 15%, all by 2027-03-31) scored PENDING/HIT/MISS; the file is frozen by sha256 |
| `make serve` then open http://localhost:5300 (or the live copy on GitHub Pages) | the start page tells the thesis as a nine-step story you click through (or read as one page): traffic, the toll, printing vs buying back, the coverage trend, a scenario model with sliders, whether the volume is real, seven ranked risks, frozen predictions, and a claim tester that checks any metric against the snapshot in the browser. Twelve evidence pages behind it: fee flywheel, buybacks, breakeven heatmaps, network, Chain Signatures, peers, developers, volume quality, risks, valuation, the full claims ledger, predictions |
| edit `params.yaml` (e.g. `capture_rate: 0.5`), `make model` | `reports/tables/breakeven.csv` and the printed breakeven volume move |
| `make refresh` | today's data pulled from NearBlocks, NEAR RPC, FastNear, DefiLlama, CoinGecko, nearstats and revenue.near.org into `data/snapshots/<today>/` with a `manifest.json` (source URL, fetch time, sha256, row count); keyed sources (Dune) skip cleanly |
| `python -m pipeline.fetch_signer` | a time-boxed sample of `v1.signer` receipts (Chain Signatures): who calls `sign`, how often; `SIGNER_PAGES` sets the sample size |
| `python -m pipeline.fetch_opendevdata` | Electric Capital's `eco_mads.parquet` (77 MB, cached in `data/raw/`) reduced to 13 peer chains in `opendevdata_mads.parquet` |
| `python -m pipeline.fetch_llama_aggregators` | DefiLlama's swap-aggregator, bridge-aggregator and DEX-overview lists, 1,816 rows, the comparison set for Intents |
| `python -m pipeline.fetch_hos` | HSP-029's live state from the `vote.dao` contract over RPC: status, for/against/abstain in veNEAR, turnout (ledger C20) |
| `python -m pipeline.fetch_intents_sample` | 180 seeded random pages of `intents.near` transactions (Sep to Oct 2026), parsed to signed intents: the source for concentration, repeat use, self-trade and solver figures on the Volume quality page. About 30 minutes on the keyless rate limit |
| `python -m pipeline.fetch_block_sample` | 150 seeded random blocks each from March and October 2026 (neardata.xyz), counted by receiver: what makes up daily transactions and what disappeared in April |
| `python -m pipeline.fetch_buybacks` | every receipt that ever touched `buybacks.multisignature.near`, 3,119 rows, the primary record behind the buyback numbers |

## What is in the repo

```
params.yaml                 every model assumption; "measured" = taken from the snapshot at run time
pipeline/                   one fetcher per source; fetch_all.py writes a dated snapshot + manifest
data/snapshots/2026-11-01/  parquet + JSON exactly as fetched (raw HTML of revenue.near.org included)
analysis/build.py           derived tables and KPIs (reports/tables/)
models/breakeven.py         breakeven volume, coverage, sensitivity grid, 2030 scenarios
checks/run_ledger.py        the claims ledger: public claims re-tested against the snapshot
checks/test_*.py            pytest: ledger integrity, model identities, data quality
dashboard/build.py          static HTML pages from the tables (Plotly); story.py builds the start page, theme.py the shared style
thesis/THESIS.template.md   the thesis with {{placeholders}}; render.py fills them
thesis/methodology.md       definitions and source hierarchy
thesis/risk_register.md     risks with the metric that monitors each
```

## Headline evidence (30 days to 2026-11-10)

| Metric | Value | Where it comes from |
|---|---|---|
| Intents volume | $3.76B ($125M/day) | DefiLlama `dexs/near-intents` |
| Gross fees | $5.96M, 15.9 bps of volume | DefiLlama `fees/near-intents` |
| Revenue captured by NEAR | $1.81M, capture 30.4% (lifetime 16.2%) | DefiLlama revenue = NEAR swept into the three revenue wallets |
| NEAR bought back | 290,497 NEAR ($1.27M) | 3,318 TRANSFER receipts from `intents.near` since 2026-04-23 (NearBlocks; sweeps after 1 Nov from FastNear) |
| NEAR issued | 2.66M NEAR, 2.47% annualised | NearBlocks daily `total_supply` difference |
| Coverage | 10.9% | the two rows above |
| Breakeven volume | $630M/day at 2.5%; $536M/day at the end-2027 ramp point (2.13%); $403M/day at 1.6% (2029) | `models/breakeven.py` |
| HSP-029 | passed Nov 2, 2026: 3.29M veNEAR for, 0 against, 1,071 abstain, turnout 62% (status Timelock) | `vote.dao` via RPC, ledger C20 |
| Staking | 44.5% of supply, 353 validators, Nakamoto coefficient 9 | NEAR RPC `validators` |
| Chain Signatures | about 14.3k `sign` calls/day counted in full over 30 days, about 90% from NEAR's own bridge and FastAuth contracts | NEAR BigQuery, run by hand on 2026-11-12 (`data/bigquery/signer_*.csv`) |
| Before the buybacks | active accounts fell 74% from January 2025 to the months before the fee switch; issuance was halved in Nov 2025; Intents paid NEAR about $36 before Nov 2025, so there was nothing to buy with; NEAR fell with SOL and ETH before the switch and has outrun them since (timing, not proof of cause) | `analysis/prebuyback.py`, `reports/tables/prebuyback_monthly.csv`, THESIS section 2 |
| Intents vs peers | rank 1 of 30 bridge aggregators (39% of list volume); rank 6 of 151 swap aggregators | DefiLlama overview lists, one volume definition |
| Volume quality | top 10 payout destinations hold 31% of sampled value (HHI 177), with Omni bridge payouts traced to their final recipient on Solana, Zcash, Bitcoin and other chains; 71% of payouts are signed by per-quote accounts, so Explorer "unique users" count swaps; round trips 1.0% outside market makers | `pipeline/fetch_intents_sample.py`, ledger C21 |
| Confidential vs coverage gap | all 18,276 USDT payouts ($156.6M) from the bridge's Tron wallet, 3-10 Nov, matched one-to-one to a public `intents.near` withdrawal (1 late); 0 left custody unseen | NEAR withdrawals from BigQuery (`sql/custody_withdrawals.sql`, run by hand), Tron side from TronGrid via `pipeline/fetch_custody.py`, `analysis/custody.py`, ledger C22-C23 |
| April 2026 step-down | ~77% of the fall from 3.48M to 0.73M daily transactions is one sender, `hotwallet.kaiching` | `pipeline/fetch_block_sample.py` |
| Developers | 580 monthly-active (down 26% y/y, 60% from 2022), 268 full-time (+4% y/y); rank 9 of 13 peer chains | Electric Capital Open Dev Data |

## Honest limits

- Confidential Intents volume and TVL are NEAR-reported; no public indexer sees the private shard. The volume series here includes them as reported. The custody check bounds unseen payouts on one route (USDT on Tron, one week); other routes are not reconciled, and confidential output that stays inside Intents is invisible to any method.
- On 2026-11-12 NearBlocks rate-limited its API from this environment, so the Chain Signatures calls and the custody withdrawals were counted from NEAR's public BigQuery dataset instead (queries in `sql/`, results in `data/bigquery/`); the buyback history was extended with FastNear for sweeps after 1 November, and the 51 overlapping sweeps matched exactly. BigQuery does not expose whether a withdrawal succeeded, so every withdrawal is treated as successful.
- Sender-level figures come from a 1.2% time sample of `intents.near` transactions, not the full Explorer feed; repeat-use figures are lower bounds. Payouts routed through `omni.bridge.near` are counted at their final recipient, read from the withdrawal message.
- NEAR AI inference staking and the Bitwise ETF holdings are marked UNVERIFIABLE because no public, machine-readable source exists.
- Developer counts cover public GitHub commits in repos Electric Capital maps to NEAR; private and non-GitHub work is invisible.
- The cross-protocol ranking uses DefiLlama's lists only. Canonical bridges (Across, Stargate, Wormhole, CCTP) sit behind a paid endpoint and exchange flows are not counted.
- revenue.near.org labels its own figures "illustrative"; the ledger records where it and the chain differ.

## Optional sources

- **NEAR BigQuery public dataset**: queries in `sql/`. Run by hand on 2026-11-12: daily transactions and active accounts match NearBlocks exactly on all 13 days compared; Intents has only about 400 to 1,000 distinct calling accounts a day; results in `data/bigquery/`. Not needed for the rebuild.
- **Dune**: `DUNE_API_KEY` enables `pipeline/fetch_dune.py`.
- **Intents Explorer API**: partner JWT in `.env` would unlock sender-level data; see `thesis/methodology.md` known gaps.

## Sources

NearBlocks API, NEAR RPC via FastNear, FastNear API, DefiLlama (NEAR Intents adapter, chain fee adapters), CoinGecko, nearstats.org, revenue.near.org, NEAR Q2 2026 State of NEAR, NEAR Q3 update (Oct 6), Nansen NEAR Q3 2026, HSP-029 (gov.near.org), Electric Capital Open Dev Data (CC BY 4.0, snapshot 20261101T130318). Licence: MIT for code; data files carry their sources' terms.
