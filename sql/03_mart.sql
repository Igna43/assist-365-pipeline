-- mart.siniestralidad_cohorte grain: one row per emission month, issuing country, and product.
-- Metrics are additive. Siniestralidad, frecuencia, and severidad are SUM / SUM
-- at query time, never an average of ratios.
--
-- Cohort rule: a paid claim is attributed to the policy's emission month, country,
-- and plan. Cancelled policies (estado ANULADA) are outside prima emitida, and
-- their claims are outside the cost, so the ratio stays on the same population.
-- Prima emitida uses the FX rate on the emission date. Claim cost uses the rate
-- on the occurrence date. Only status PAGADO enters the cost.

CREATE OR REPLACE TABLE `${project}.mart.siniestralidad_cohorte` AS
WITH ventas AS (
  SELECT
    mes_emision,
    pais_emision,
    producto_id,
    COUNT(*) AS polizas_emitidas,
    SUM(prima_usd) AS prima_emitida_usd
  FROM `${project}.core.fct_venta`
  WHERE cuenta_como_emitida
    AND NOT fx_missing
    AND mes_emision IS NOT NULL
  GROUP BY mes_emision, pais_emision, producto_id
),
siniestros AS (
  SELECT
    v.mes_emision,
    v.pais_emision,
    v.producto_id,
    COUNTIF(s.es_pagado AND s.costo_usd IS NOT NULL) AS siniestros_pagados,
    SUM(IF(s.es_pagado, s.costo_usd, 0)) AS costo_siniestros_usd
  FROM `${project}.core.fct_siniestro` AS s
  INNER JOIN `${project}.core.fct_venta` AS v
    ON s.policy_id = v.poliza_id
  WHERE v.cuenta_como_emitida
    AND NOT v.fx_missing
    AND v.mes_emision IS NOT NULL
  GROUP BY v.mes_emision, v.pais_emision, v.producto_id
)
SELECT
  v.mes_emision,
  v.pais_emision,
  v.producto_id,
  p.nombre_plan,
  p.tipo AS tipo_producto,
  p.es_premium,
  v.polizas_emitidas,
  v.prima_emitida_usd,
  IFNULL(s.siniestros_pagados, 0) AS siniestros_pagados,
  IFNULL(s.costo_siniestros_usd, 0) AS costo_siniestros_usd
FROM ventas AS v
LEFT JOIN siniestros AS s
  USING (mes_emision, pais_emision, producto_id)
LEFT JOIN `${project}.core.dim_producto` AS p
  USING (producto_id);
