-- Base-chain activity per day. Partition filter on block_date keeps the scan small.
SELECT
  block_date,
  COUNT(*)                            AS transactions,
  COUNT(DISTINCT signer_account_id)   AS unique_signers,
  COUNT(DISTINCT receiver_account_id) AS unique_receivers
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions`
WHERE block_date BETWEEN DATE_SUB(@end_date, INTERVAL 120 DAY) AND @end_date
GROUP BY 1
ORDER BY 1;
