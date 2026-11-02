-- Fails when the latest full policy extract does not match the API event count.
-- Incremental runs are skipped: x-total-count stays the global total, not the delta.
WITH latest AS (
  SELECT mode, api_total, loaded_rows
  FROM `${project}.ops.extract_counts`
  WHERE resource = 'polizas'
  QUALIFY ROW_NUMBER() OVER (ORDER BY extracted_at DESC) = 1
)
SELECT mode, api_total, loaded_rows
FROM latest
WHERE mode = 'full'
  AND (
    api_total IS NULL
    OR loaded_rows IS NULL
    OR api_total != loaded_rows
  )
