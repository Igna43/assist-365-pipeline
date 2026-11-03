-- Falla si una póliza emitida no tiene prima en dólares y no quedó marcada como tipo de cambio faltante.
SELECT poliza_id, moneda, fecha_emision, fx_source
FROM `${project}.core.fct_venta`
WHERE cuenta_como_emitida
  AND prima_usd IS NULL
  AND fx_missing IS NOT TRUE
