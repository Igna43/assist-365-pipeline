-- Fails when a non-null agency id is not in the agency catalog.
SELECT v.poliza_id, v.agencia_id
FROM `${project}.core.fct_venta` AS v
LEFT JOIN `${project}.core.dim_agencia` AS a
  ON v.agencia_id = a.agencia_id
WHERE v.agencia_id IS NOT NULL
  AND a.agencia_id IS NULL
