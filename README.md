# Toll Road: does NEAR's fee switch pay for the chain?

A long-term investment thesis for NEAR Protocol, built so that every number can be re-derived from the repo. NEAR Hackathon 2026, track `thesis` (Investment Thesis).

**The question.** Since February 2026 a cut of every NEAR Intents swap is converted to NEAR and swept on-chain into a buyback wallet. Does that revenue cover the value of new NEAR issuance, and what would have to be true for it to?

**The answer today** (snapshot 2026-11-01): the mechanism is real and small. Buybacks covered about 11% of issuance over the last 30 days. Intents needs roughly 5.5x today's volume at today's fee and capture rates to break even at 2.5% issuance, or 3.5x if HSP-029 cuts issuance to 1.6%. Bought NEAR is held in a multisig, not staked or burned. The full argument, the evidence and the kill criteria are in [`thesis/THESIS.md`](thesis/THESIS.md).

Everything is regenerated from committed, dated snapshots. No API keys are needed to reproduce the report.

## Do X, see Y

| Do | See |
|---|---|
| `make setup` | dependencies installed (pandas, pyarrow, plotly, pyyaml, requests, pytest) |
| `make report` | `reports/tables/*.csv`, `dashboard/*.html` (10 pages), `thesis/THESIS.md` and `thesis/claims_ledger.csv` rebuilt from `data/snapshots/2026-11-01/` in under a minute |
| `make check` | the 20-row claims ledger re-verified (10 PASS, 5 PARTIAL, 3 UNVERIFIABLE, 2 FAIL) and 13 tests passing. C19 is red because Electric Capital's data shows fewer NEAR developers, not more. C02 is red on purpose: the tokenomics post says bought NEAR is "staked or locked"; the wallet shows 0 staked |
| `make serve` then open http://localhost:5300 | the dashboard, one page per question with an evidence map on the start page: KPI tiles, fee flywheel, issuance vs buybacks, breakeven heatmaps, network fundamentals, Chain Signatures callers, Intents vs every DefiLlama bridge and swap aggregator, developers vs peer chains, comparables, 2030 scenarios, the ledger |
| edit `params.yaml` (e.g. `capture_rate: 0.5`), `make model` | `reports/tables/breakeven.csv` and the printed breakeven volume move |
| `make refresh` | today's data pulled from NearBlocks, NEAR RPC, FastNear, DefiLlama, CoinGecko, nearstats and revenue.near.org into `data/snapshots/<today>/` with a `manifest.json` (source URL, fetch time, sha256, row count); keyed sources (Dune) skip cleanly |
| `python -m pipeline.fetch_signer` | a time-boxed sample of `v1.signer` receipts (Chain Signatures): who calls `sign`, how often; `SIGNER_PAGES` sets the sample size |
| `python -m pipeline.fetch_opendevdata` | Electric Capital's `eco_mads.parquet` (77 MB, cached in `data/raw/`) reduced to 13 peer chains in `opendevdata_mads.parquet` |
| `python -m pipeline.fetch_llama_aggregators` | DefiLlama's swap-aggregator, bridge-aggregator and DEX-overview lists, 1,816 rows, the comparison set for Intents |
| `python -m pipeline.fetch_hos` | HSP-029's live state from the `vote.dao` contract over RPC: status, for/against/abstain in veNEAR, turnout (ledger C20) |
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
dashboard/build.py          static HTML pages from the tables (Plotly); index.html is the start page and evidence map
thesis/THESIS.template.md   the thesis with {{placeholders}}; render.py fills them
thesis/methodology.md       definitions and source hierarchy
thesis/risk_register.md     risks with the metric that monitors each
```

## Headline evidence (30 days to 2026-10-30)

| Metric | Value | Where it comes from |
|---|---|---|
| Intents volume | $3.91B ($130M/day) | DefiLlama `dexs/near-intents` |
| Gross fees | $6.26M, 16.0 bps of volume | DefiLlama `fees/near-intents` |
| Revenue captured by NEAR | $2.14M, capture 34.2% (lifetime 15.9%) | DefiLlama revenue = NEAR swept into the three revenue wallets |
| NEAR bought back | 282,241 NEAR ($1.37M) | 3,073 TRANSFER receipts from `intents.near` since 2026-04-23 (NearBlocks) |
| NEAR issued | 2.65M NEAR, 2.46% annualised | NearBlocks daily `total_supply` difference |
| Coverage | 10.6% | the two rows above |
| Breakeven volume | $718M/day at 2.5%; $611M/day at the end-2027 ramp point (2.13%); $459M/day at 1.6% (2029) | `models/breakeven.py` |
| HSP-029 | passed Nov 2, 2026: 3.29M veNEAR for, 0 against, 1,071 abstain, turnout 62% (status Timelock) | `vote.dao` via RPC, ledger C20 |
| Staking | 45.2% of supply, 375 validators, Nakamoto coefficient 9 | NEAR RPC `validators` |
| Chain Signatures | ~16.9k `sign` calls/day, 92% from NEAR's own bridge and FastAuth contracts | sample of `v1.signer` receipts (NearBlocks) |
| Intents vs peers | rank 1 of 30 bridge aggregators (41% of list volume); rank 6 of 144 swap aggregators | DefiLlama overview lists, one volume definition |
| Developers | 582 monthly-active (down 28% y/y, 60% from 2022), 278 full-time (+6% y/y); rank 9 of 13 peer chains | Electric Capital Open Dev Data, 2026-10-24 |

## Honest limits

- Confidential Intents volume and TVL are NEAR-reported; no public indexer sees the private shard. The volume series here includes them as reported.
- Sender-level data (concentration, repeat use) needs the Intents Explorer partner token; it is a listed gap, not a filled one.
- NEAR AI inference staking and the Bitwise ETF holdings are marked UNVERIFIABLE because no public, machine-readable source exists.
- Developer counts cover public GitHub commits in repos Electric Capital maps to NEAR; private and non-GitHub work is invisible.
- The cross-protocol ranking uses DefiLlama's lists only. Canonical bridges (Across, Stargate, Wormhole, CCTP) sit behind a paid endpoint and exchange flows are not counted.
- revenue.near.org labels its own figures "illustrative"; the ledger records where it and the chain differ.

## Other entries

The same author also submits **Clearance** (AI Security & Defense track), a separate project with its own repository; the two share no code. Disclosed per rule Q-015.

## Optional sources

- **NEAR BigQuery public dataset**: queries in `sql/`, run by `pipeline/fetch_bigquery.py` when `GOOGLE_CLOUD_PROJECT` is set. Not needed for the rebuild.
- **Dune**: `DUNE_API_KEY` enables `pipeline/fetch_dune.py`.
- **Intents Explorer API**: partner JWT in `.env` would unlock sender-level data; see `thesis/methodology.md` known gaps.

## Sources

NearBlocks API, NEAR RPC via FastNear, FastNear API, DefiLlama (NEAR Intents adapter, chain fee adapters), CoinGecko, nearstats.org, revenue.near.org, NEAR Q2 2026 State of NEAR, NEAR Q3 update (Oct 6), Nansen NEAR Q3 2026, HSP-029 (gov.near.org), Electric Capital Open Dev Data (CC BY 4.0, snapshot 20261101T130318). Licence: MIT for code; data files carry their sources' terms.
