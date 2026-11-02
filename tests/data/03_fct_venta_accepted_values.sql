-- Fails when a required policy attribute is null or outside the known domain.
SELECT poliza_id, estado, pais_emision, moneda
FROM `${project}.core.fct_venta`
WHERE poliza_id IS NULL
  OR estado IS NULL
  OR pais_emision IS NULL
  OR moneda IS NULL
  OR estado NOT IN ('EMITIDA', 'VIGENTE', 'VENCIDA', 'ANULADA')
  OR pais_emision NOT IN ('AR', 'MX', 'CO', 'CL', 'PE', 'BR')
  OR moneda NOT IN ('ARS', 'BRL', 'CLP', 'COP', 'MXN', 'PEN', 'USD')
