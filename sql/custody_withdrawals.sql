-- Public withdrawals of bridged USDT-on-Tron from NEAR Intents, 2 Nov to 11 Nov 2026 (UTC).
-- A public withdrawal is an ft_transfer on the token contract whose memo starts with WITHDRAW_TO:<tron address>.
WITH d AS (
  SELECT
    receipt_id,
    block_timestamp_utc AS ts,
    receipt_predecessor_account_id AS predecessor,
    JSON_VALUE(args, '$.method_name') AS method,
    SAFE_CONVERT_BYTES_TO_STRING(FROM_BASE64(JSON_VALUE(args, '$.args_base64'))) AS a
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
  WHERE block_date BETWEEN DATE '2026-11-02' AND DATE '2026-11-11'
    AND receipt_receiver_account_id = 'tron-d28a265909efecdcee7c5028585214ea0b96f015.omft.near'
    AND action_kind = 'FUNCTION_CALL'
)
SELECT
  receipt_id, ts, predecessor, method,
  JSON_VALUE(a, '$.amount') AS amount,
  JSON_VALUE(a, '$.memo') AS memo,
  JSON_VALUE(a, '$.receiver_id') AS receiver_id
FROM d
WHERE method = 'ft_transfer' AND JSON_VALUE(a, '$.memo') LIKE 'WITHDRAW_TO:%'
ORDER BY ts;
