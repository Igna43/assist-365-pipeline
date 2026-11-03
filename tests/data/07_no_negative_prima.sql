-- Falla si una prima es negativa.
SELECT poliza_id, prima_local, prima_usd
FROM `${project}.core.fct_venta`
WHERE prima_local < 0
  OR prima_usd < 0
