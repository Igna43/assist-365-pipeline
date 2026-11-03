-- Falla si un atributo obligatorio de la póliza es nulo o está fuera del dominio conocido.
SELECT poliza_id, estado, pais_emision, moneda
FROM `${project}.core.fct_venta`
WHERE poliza_id IS NULL
  OR estado IS NULL
  OR pais_emision IS NULL
  OR moneda IS NULL
  OR estado NOT IN ('EMITIDA', 'VIGENTE', 'VENCIDA', 'ANULADA')
  OR pais_emision NOT IN ('AR', 'MX', 'CO', 'CL', 'PE', 'BR')
  OR moneda NOT IN ('ARS', 'BRL', 'CLP', 'COP', 'MXN', 'PEN', 'USD')
