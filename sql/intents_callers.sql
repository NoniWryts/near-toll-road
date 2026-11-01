-- Who calls the Intents verifier contract. Signers are keys on accounts; predecessors are the accounts (often
-- solver or distribution-channel contracts) that issued the receipt. Neither is "users", but both bound it.
SELECT
  ra.block_date,
  COUNT(*)                                            AS function_calls,
  COUNT(DISTINCT ra.receipt_predecessor_account_id)   AS distinct_predecessors,
  COUNT(DISTINCT t.signer_account_id)                 AS distinct_signers
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions` ra
JOIN `bigquery-public-data.crypto_near_mainnet_us.receipt_origin_transaction` ro
  ON ro.receipt_id = ra.receipt_id
JOIN `bigquery-public-data.crypto_near_mainnet_us.transactions` t
  ON ro.originated_from_transaction_hash = t.transaction_hash
 AND t.block_date BETWEEN DATE_SUB(@end_date, INTERVAL 121 DAY) AND @end_date
WHERE ra.block_date BETWEEN DATE_SUB(@end_date, INTERVAL 120 DAY) AND @end_date
  AND ra.action_kind = 'FUNCTION_CALL'
  AND ra.receipt_receiver_account_id = 'intents.near'
GROUP BY 1
ORDER BY 1;
