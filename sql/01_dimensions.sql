-- dim_producto grain: one row per producto_id.
-- dim_agencia grain: one row per agencia_id.
-- dim_tipo_cambio grain: one row per fecha x moneda, from 2023-01-01 through 2028-01-01.
-- The source calendar skips days. Each gap, and any date after the last published
-- rate, carries forward the previous factor_usd. Dates before the first rate
-- use that first rate. is_published marks a day that actually arrived from the API.

CREATE OR REPLACE TABLE `${project}.core.dim_producto` AS
SELECT
  producto_id,
  nombre_plan,
  cobertura_max_usd,
  tipo,
  SAFE_CAST(es_premium AS INT64) = 1 AS es_premium
FROM `${project}.raw.productos`
QUALIFY ROW_NUMBER() OVER (PARTITION BY producto_id ORDER BY _ingested_at DESC) = 1;

CREATE OR REPLACE TABLE `${project}.core.dim_agencia` AS
SELECT
  agencia_id,
  nombre,
  pais,
  canal
FROM `${project}.raw.agencias`
QUALIFY ROW_NUMBER() OVER (PARTITION BY agencia_id ORDER BY _ingested_at DESC) = 1;

CREATE OR REPLACE TABLE `${project}.core.dim_tipo_cambio` AS
WITH published AS (
  SELECT fecha, moneda, ANY_VALUE(factor_usd) AS factor_usd
  FROM `${project}.raw.tipo_cambio`
  GROUP BY fecha, moneda
),
monedas AS (
  SELECT moneda, MIN(fecha) AS fecha_min, MAX(fecha) AS fecha_max
  FROM published
  GROUP BY moneda
),
spine AS (
  SELECT moneda, fecha_min, fecha_max, dia AS fecha
  FROM monedas
  CROSS JOIN UNNEST(GENERATE_DATE_ARRAY(DATE '2023-01-01', DATE '2028-01-01')) AS dia
),
filled AS (
  SELECT
    s.moneda,
    s.fecha,
    s.fecha_min,
    s.fecha_max,
    p.factor_usd IS NOT NULL AS is_published,
    COALESCE(
      LAST_VALUE(p.factor_usd IGNORE NULLS) OVER (
        PARTITION BY s.moneda
        ORDER BY s.fecha
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ),
      FIRST_VALUE(p.factor_usd IGNORE NULLS) OVER (
        PARTITION BY s.moneda
        ORDER BY s.fecha
        ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
      )
    ) AS factor_usd
  FROM spine AS s
  LEFT JOIN published AS p
    ON p.moneda = s.moneda
    AND p.fecha = s.fecha
)
SELECT
  moneda,
  fecha,
  fecha_min,
  fecha_max,
  factor_usd,
  is_published,
  CASE
    WHEN factor_usd IS NULL THEN 'missing'
    WHEN is_published THEN 'exact'
    WHEN fecha > fecha_max THEN 'extrapolated_forward'
    WHEN fecha < fecha_min THEN 'extrapolated_backward'
    ELSE 'carried_forward'
  END AS fx_source
FROM filled;
