DECLARE end_date DATE DEFAULT DATE '2026-11-10';
SELECT receipt_predecessor_account_id AS caller, COUNT(*) AS sign_calls
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date BETWEEN DATE_SUB(end_date, INTERVAL 29 DAY) AND end_date
  AND receipt_receiver_account_id = 'v1.signer'
  AND action_kind = 'FUNCTION_CALL'
  AND JSON_VALUE(args, '$.method_name') = 'sign'
GROUP BY 1 ORDER BY 2 DESC LIMIT 30;
