-- Fails when an emitted policy has no USD premium and was not flagged as missing FX.
SELECT poliza_id, moneda, fecha_emision, fx_source
FROM `${project}.core.fct_venta`
WHERE cuenta_como_emitida
  AND prima_usd IS NULL
  AND fx_missing IS NOT TRUE
