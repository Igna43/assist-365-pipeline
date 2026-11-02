-- Fails when a claim status, type, or known currency is outside the source domain.
-- A null currency is allowed: the feed emits NaN and we store that as null.
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
