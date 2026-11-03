-- Falla si un costo pagado en dólares invierte el signo del monto de origen o usa un tipo de cambio no positivo.
-- Los montos negativos del origen se conservan: el feed los trae, y el costo pagado neto tiene que incluirlos.
SELECT claim_id, amount_value, fx_factor, costo_usd
FROM `${project}.core.fct_siniestro`
WHERE es_pagado
  AND costo_usd IS NOT NULL
  AND (
    fx_factor IS NULL
    OR fx_factor <= 0
    OR (amount_value < 0 AND costo_usd > 0)
    OR (amount_value > 0 AND costo_usd < 0)
  )
