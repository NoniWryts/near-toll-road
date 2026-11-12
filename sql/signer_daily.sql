DECLARE end_date DATE DEFAULT DATE '2026-11-10';
SELECT block_date,
  COUNTIF(JSON_VALUE(args, '$.method_name') = 'sign') AS sign_calls,
  COUNT(DISTINCT IF(JSON_VALUE(args, '$.method_name') = 'sign', receipt_predecessor_account_id, NULL)) AS sign_callers,
  COUNT(*) AS all_calls
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN DATE_SUB(end_date, INTERVAL 29 DAY) AND end_date
  AND receipt_receiver_account_id = 'v1.signer'
  AND action_kind = 'FUNCTION_CALL'
GROUP BY 1 ORDER BY 1;
