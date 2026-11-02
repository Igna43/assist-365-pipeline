-- Fails when the latest full claims extract does not match the API total.
WITH latest AS (
  SELECT api_total, loaded_rows
  FROM `${project}.ops.extract_counts`
  WHERE resource = 'siniestros'
  QUALIFY ROW_NUMBER() OVER (ORDER BY extracted_at DESC) = 1
)
SELECT api_total, loaded_rows
FROM latest
WHERE api_total IS NULL
  OR loaded_rows IS NULL
  OR api_total != loaded_rows
