-- The 25 contracts receiving the most function calls in the last 30 days of the window.
SELECT
  receipt_receiver_account_id AS contract,
  COUNT(*)                    AS function_calls,
  COUNT(DISTINCT receipt_predecessor_account_id) AS distinct_predecessors
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN DATE_SUB(@end_date, INTERVAL 30 DAY) AND @end_date
  AND action_kind = 'FUNCTION_CALL'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 25;
