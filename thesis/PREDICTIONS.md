# Pre-registered predictions

Written 2026-11-04, before the outcomes are known. Each call has a date, a threshold, the exact metric that settles
it, and what a miss means for the thesis. `python -m checks.predictions` computes every metric from the latest
snapshot and writes `reports/tables/predictions.csv` with status PENDING until the settle date, then HIT or MISS.
This file is frozen: the commit that adds it and its sha256 (in `thesis/PREDICTIONS.sha256`) are the timestamp.
Any later edit to a threshold shows up in `git log -p thesis/PREDICTIONS.md`.

Anchor: snapshot `2026-11-01`, data through 2026-10-30, mainnet block 222,583,497.

| id | call | settles on | metric (exact) | anchor today | threshold |
| --- | --- | --- | --- | --- | --- |
| P1 | HSP-029 is live in the protocol: validators have adopted the upgrade that lowers the issuance cap | 2027-03-31 | NEAR RPC `EXPERIMENTAL_protocol_config` (finality final): `max_inflation_rate` is no longer `[1, 40]`, or realised issuance (trailing-30d total-supply change, annualised, NearBlocks) is below 2.40% | `[1, 40]`, protocol 86; realised 2.46% | cap changed **or** realised < 2.40% |
| P2 | NEAR keeps a larger share of Intents fees | data through 2027-03-31 | trailing-90d captured revenue / gross fees, DefiLlama `fees/near-intents` (dailyRevenue / dailyFees) | 27.0% | >= 30.0% |
| P3 | Buybacks cover more of issuance | data through 2027-03-31 | 90-day NEAR swept from `intents.near` to `buybacks.multisignature.near` (successful TRANSFER receipts) / 90-day NEAR issued (total-supply change) | 12.0% | >= 15.0% |

## What a miss means

- **P1 miss**: governance passed but the chain did not change. The supply side of the thesis rests on a vote, not on the protocol; the breakeven table keeps 2.5% as the base case.
- **P2 miss**: the near.com share is not growing fast enough to lift margin. The bull row in `scenarios_2030.csv` (40% capture) loses its support.
- **P3 miss**: even with P1 and P2, buybacks are not catching issuance. Kill criterion 2 in `THESIS.md` (coverage below 25% at end-2027 with HSP-029 in force) becomes the likely outcome.

## Why these three

They are the three links in the toll-road chain that can be checked from public data without a key: the denominator
(issuance, P1), the margin (capture, P2) and the result (coverage, P3). Volume is deliberately not predicted: it is
the most market-driven input and a volume call would mostly be a price call.
