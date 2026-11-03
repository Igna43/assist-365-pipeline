-- Falla si la última extracción completa de pólizas no coincide con la cantidad de eventos de la API.
-- Las corridas incrementales se saltean: x-total-count sigue siendo el total global, no el delta.
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
