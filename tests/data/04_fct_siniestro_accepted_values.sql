-- Falla si el estado, el tipo o una moneda conocida del siniestro está fuera del dominio de origen.
-- Una moneda nula sí se permite: el feed manda NaN y acá se guarda como null.
SELECT claim_id, status, type, amount_currency
FROM `${project}.core.fct_siniestro`
WHERE claim_id IS NULL
  OR status IS NULL
  OR type IS NULL
  OR status NOT IN ('PAGADO', 'RECHAZADO', 'EN_ANALISIS')
  OR type NOT IN ('MEDICO', 'CANCELACION', 'EQUIPAJE', 'DEMORA')
  OR (
    amount_currency IS NOT NULL
    AND amount_currency NOT IN ('ARS', 'BRL', 'CLP', 'COP', 'MXN', 'PEN', 'USD')
  )
