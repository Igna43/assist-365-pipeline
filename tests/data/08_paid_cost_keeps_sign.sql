-- Fails when a paid USD cost flips the sign of the source amount or uses a non-positive FX rate.
-- Negative source amounts are kept: the feed contains them, and the net paid cost should include them.
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
