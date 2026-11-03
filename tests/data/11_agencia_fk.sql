-- Falla si una agencia informada no está en el catálogo de agencias.
SELECT v.poliza_id, v.agencia_id
FROM `${project}.core.fct_venta` AS v
LEFT JOIN `${project}.core.dim_agencia` AS a
  ON v.agencia_id = a.agencia_id
WHERE v.agencia_id IS NOT NULL
  AND a.agencia_id IS NULL
