# Risk register

| # | Risk | Evidence | Monitor |
|---|---|---|---|
| R1 | Issuance exceeds buybacks; bought NEAR held, not retired | ledger C02, C03 | monthly coverage in `reports/tables/monthly.csv` |
| R2 | Volume concentration / incentive-driven flow | sampled: top-10 payout destinations ~36% of value, HHI ~314; round trips rare outside market makers; transfer signers concentrated (top 5 ~80%) | `reports/tables/vq_*.csv`, re-sample each quarter |
| R3 | Capture depends on near.com share; partner channels keep most fees | capture 16% lifetime vs 34% 30d | capture_30d vs capture_90d divergence |
| R4 | Cross-chain settlement exploits (Oct 1 2026, $3.8M, returned) | The Block, CoinDesk, NEAR postmortem | incident log |
| R5 | MPC signer concentration (16 participants, threshold 11 per `v1.signer` state, Nov 2026) and permissioned private shard | `mpc_state.json` | participant count per quarter |
| R6 | Governance execution: HSP-029 needs validator upgrade after the vote | gov.near.org | realized issuance vs 1.6% path |
| R7 | Competitive standardisation (ERC-7683 solvers, LI.FI, Across) | public | NEAR Intents share of cross-chain volume (DefiLlama bridges/aggregators) |
| R8 | Reported figures that cannot be verified (confidential TVL, AI staking, ETF holdings) | ledger C12-C14 | keep UNVERIFIABLE until a public source exists |
| R9 | Price-driven optics: USD coverage improves when NEAR falls | model | always show NEAR-terms coverage first |
| R10 | Network activity step change: daily transactions fell from ~3.5M (March) to ~0.73M (October) 2026; ~77% of the fall is one sender, `hotwallet.kaiching`, paying `users.kaiching` accounts | `reports/tables/block_mix.csv` | block sample each quarter |
