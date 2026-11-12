# BigQuery results (run by hand in the console, 2026-11-12)

Run in the BigQuery web console against `bigquery-public-data.crypto_near_mainnet_us`, window ending 2026-11-10
(queries in `sql/`). The dataset is fresh to 2026-11-10, so the March 2026 NEAR Lake deprecation did not stop it.

- `q1_check_vs_nearblocks.csv`: 13 days across July to November (including spike days). Transactions and unique signers
  equal NearBlocks `txns` and `active_accounts` on every day, digit for digit. These are the days compared, not the full 120.
- `q2_intents_callers_selected.csv`: selected days of function calls to `intents.near` and distinct sending accounts.
  Callers stay at about 400 to 1,000 a day (peak 2,726 on 2026-09-20) while calls rose from about 55k to 100-300k.
- `q3_top_receivers_30d.csv`: top 25 contracts by function calls, 2026-10-11 to 2026-11-10.

Reading: calls are not value. Calls per $1M of Intents volume were about 1,050 (25 Aug), 600 (21 Sep), 770 (8 Oct) and
2,400 (5 Nov), so rising call counts do not mean rising fee-paying volume. The thesis uses dollar volume and fees.
