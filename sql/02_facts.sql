-- fct_venta grain: one row per current policy (latest event).
-- Order: updated_at DESC, then D > U > I, then ingestion time.
-- A policy whose latest op is D is not a current policy and is dropped.
--
-- fct_siniestro grain: one row per claim_id.
-- costo_usd is populated only when status = PAGADO (what was actually paid).
-- FX is monto * factor_usd from core.dim_tipo_cambio, which carries the last
-- published rate across gaps and past the end of the source calendar.

CREATE OR REPLACE TABLE `${project}.core.fct_venta`
CLUSTER BY poliza_id AS
WITH ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY poliza_id
      ORDER BY
        updated_at DESC,
        CASE op WHEN 'D' THEN 3 WHEN 'U' THEN 2 WHEN 'I' THEN 1 ELSE 0 END DESC,
        _ingested_at DESC
    ) AS rn
  FROM `${project}.raw.polizas`
),
current_policy AS (
  SELECT *
  FROM ranked
  WHERE rn = 1
    AND IFNULL(op, '') != 'D'
)
SELECT
  p.poliza_id,
  p.cliente_id,
  p.producto_id,
  p.agencia_id,
  p.pais_emision,
  p.canal_origen,
  p.fecha_emision_utc,
  DATE(p.fecha_emision_utc) AS fecha_emision,
  DATE_TRUNC(DATE(p.fecha_emision_utc), MONTH) AS mes_emision,
  p.inicio_vigencia,
  p.fin_vigencia,
  DATE_DIFF(p.inicio_vigencia, DATE(p.fecha_emision_utc), DAY) AS anticipacion_dias,
  p.prima AS prima_local,
  p.moneda,
  p.estado,
  p.op,
  p.updated_at,
  p.estado != 'ANULADA' AS cuenta_como_emitida,
  fx.factor_usd AS fx_factor,
  IFNULL(fx.fx_source, 'missing') AS fx_source,
  IFNULL(fx.fx_source, 'missing') = 'missing' AS fx_missing,
  p.prima * fx.factor_usd AS prima_usd
FROM current_policy AS p
LEFT JOIN `${project}.core.dim_tipo_cambio` AS fx
  ON fx.moneda = p.moneda
  AND fx.fecha = DATE(p.fecha_emision_utc);

CREATE OR REPLACE TABLE `${project}.core.fct_siniestro`
CLUSTER BY claim_id AS
WITH deduped AS (
  SELECT *
  FROM `${project}.raw.siniestros`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY claim_id ORDER BY _ingested_at DESC) = 1
)
SELECT
  s.claim_id,
  s.policy_id,
  s.occurred_at_raw,
  s.reported_at_raw,
  s.occurred_on,
  s.reported_on,
  DATE_DIFF(s.reported_on, s.occurred_on, DAY) AS dias_hasta_reporte,
  s.type,
  s.status,
  s.amount_value,
  s.amount_currency,
  s.detail,
  s.status = 'PAGADO' AS es_pagado,
  fx.factor_usd AS fx_factor,
  IFNULL(fx.fx_source, 'missing') AS fx_source,
  IFNULL(fx.fx_source, 'missing') = 'missing'
    OR s.amount_currency IS NULL
    OR s.occurred_on IS NULL AS fx_missing,
  IF(s.status = 'PAGADO', s.amount_value * fx.factor_usd, NULL) AS costo_usd
FROM deduped AS s
LEFT JOIN `${project}.core.dim_tipo_cambio` AS fx
  ON fx.moneda = s.amount_currency
  AND fx.fecha = s.occurred_on;
