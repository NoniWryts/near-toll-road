# Risk register

| # | Risk | Evidence | Monitor |
|---|---|---|---|
| R1 | Issuance exceeds buybacks; bought NEAR held, not retired | ledger C02, C03 | monthly coverage in `reports/tables/monthly.csv` |
| R2 | Volume concentration / incentive-driven flow | not measurable without Explorer API token | add `pipeline/fetch_intents_explorer.py` when a token is available |
| R3 | Capture depends on near.com share; partner channels keep most fees | capture 16% lifetime vs 34% 30d | capture_30d vs capture_90d divergence |
| R4 | Cross-chain settlement exploits (Oct 1 2026, $3.8M, returned) | The Block, CoinDesk, NEAR postmortem | incident log |
| R5 | MPC signer concentration (17 participants, threshold 11) and permissioned private shard | contract state, NEAR docs | participant count per quarter |
| R6 | Governance execution: HSP-029 needs validator upgrade after the vote | gov.near.org | realized issuance vs 1.6% path |
| R7 | Competitive standardisation (ERC-7683 solvers, LI.FI, Across) | public | NEAR Intents share of cross-chain volume (DefiLlama bridges/aggregators) |
| R8 | Reported figures that cannot be verified (confidential TVL, AI staking, ETF holdings) | ledger C12-C14 | keep UNVERIFIABLE until a public source exists |
| R9 | Price-driven optics: USD coverage improves when NEAR falls | model | always show NEAR-terms coverage first |
| R10 | Network activity step change: NearBlocks daily transactions fell from ~4M to ~0.8M/day in April 2026; cause (bot traffic ending, or a counting change) not established | `reports/tables/network_daily.csv` | compare with Nansen signer-based series each quarter |
