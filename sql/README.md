# BigQuery queries (optional source)

The track prompt points at `bigquery-public-data.crypto_near_mainnet_us`. These queries are the base-chain activity
checks for this thesis. They are **not required** to rebuild the repo: the same series come keyless from NearBlocks
(`pipeline/fetch_nearblocks.py`) and the sender-level Intents view is a listed gap either way.

Run them with `GOOGLE_CLOUD_PROJECT=<your project> python -m pipeline.fetch_bigquery` (needs `google-cloud-bigquery`
and `gcloud auth application-default login`), or paste them into the BigQuery console. Every query filters on
`block_date`, which is the partition column, so each one scans a few GB at most (first 1 TB per month is free).

Caveat from docs.near.org: the NEAR Lake S3 source behind this dataset was deprecated on 2026-03-24; the dataset
"remains available" but check the NEAR Public Lakehouse repository for its ingestion status before trusting recent dates.
The pipeline records the max `block_date` returned in the manifest so a stale dataset shows up as a short series.

| file | answers | used for |
| --- | --- | --- |
| `daily_activity.sql` | transactions, unique signers and receivers per day | cross-check of NearBlocks `txns` and `active_accounts` (network page) |
| `intents_callers.sql` | distinct signers and predecessor accounts calling `intents.near` per day, plus calls | the closest public proxy for "how many accounts use Intents" without the Explorer token |
| `top_receivers.sql` | the 25 contracts receiving the most function calls in the window | what the base chain is actually used for, to explain the April 2026 step-down |
