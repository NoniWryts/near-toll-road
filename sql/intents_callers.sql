-- Who calls the Intents verifier contract each day (accounts that sent the call, and how many calls).
SELECT
  block_date,
  COUNT(*)                                          AS function_calls,
  COUNT(DISTINCT receipt_predecessor_account_id)    AS distinct_predecessors
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN DATE_SUB(@end_date, INTERVAL 120 DAY) AND @end_date
  AND action_kind = 'FUNCTION_CALL'
  AND receipt_receiver_account_id = 'intents.near'
GROUP BY 1
ORDER BY 1;
