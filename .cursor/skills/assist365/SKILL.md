---
name: assist365
description: Responde preguntas comerciales de Assist-365 contra BigQuery (siniestralidad, prima, frecuencia y severidad). Usar cuando pregunten por planes, países, margen, siniestros o el warehouse a365-de-imangini.
---

# Assist-365 — capa semántica

Warehouse `a365-de-imangini`. Consultar con el MCP `assist365-bigquery` (`list_tables`, `describe_table`, `run_select`). Un solo `SELECT`. No usar DML. `run_select` corta en 1 GB.

Para métricas de negocio usar `mart.siniestralidad_cohorte`. Usar `core` solo si la pregunta no entra en el grano del mart (anticipación, vigencia, canal, detalle del siniestro). No escanear `raw` para responder una pregunta comercial.

Los ratios se calculan con `SUM / SUM` sobre columnas aditivas. Nunca promediar siniestralidades ya calculadas.

## Glosario

- **Prima emitida.** Lo que se cobra por una póliza vendida. En este modelo es `prima_usd` de las pólizas cuyo estado vigente no es `ANULADA`. No hay un campo de devolución, así que la anulada sale del denominador. La fecha de la venta es `DATE(fecha_emision_utc)`.
- **Costo de siniestros.** Lo que efectivamente se pagó. Solo `status = PAGADO`. `RECHAZADO` y `EN_ANALISIS` no entran al costo.
- **Siniestralidad (loss ratio).** Costo de siniestros dividido prima emitida, en dólares y sobre la misma población. Es de cohorte de emisión: el siniestro pagado se atribuye al mes de emisión, al país de emisión y al plan de su póliza. Filtrar "este trimestre" responde qué se vendió en ese trimestre, no qué se pagó por fecha de ocurrencia.
- **Frecuencia.** Siniestros pagados / pólizas emitidas.
- **Severidad.** Costo USD de siniestros pagados / cantidad de siniestros pagados. Es el monto promedio.
- **Anticipación de compra.** Días entre la emisión y `inicio_vigencia`. Vive en `core.fct_venta.anticipacion_dias`, no en el mart.
- **Destruye margen.** El plan con mayor `SUM(costo_siniestros_usd) - SUM(prima_emitida_usd)`. La siniestralidad sola puede inflar un plan chico. La pérdida en dólares dice qué plan se lleva la plata.

## Tipo de cambio

`monto_local * factor_usd` de `core.dim_tipo_cambio`, con la moneda de la fila (no la del país: no siempre coinciden). La prima usa la fecha de emisión. El siniestro usa la fecha de ocurrencia. El calendario publicado saltea días. `dim_tipo_cambio` arrastra la última tasa conocida (`carried_forward`) y, después de la última fecha publicada, la marca `extrapolated_forward`. Si no hay tasa, `fx_missing` es verdadero y el monto en dólares es nulo. Esas filas no entran al mart.

## Tablas

### `mart.siniestralidad_cohorte`

Grano: un renglón por `mes_emision` × `pais_emision` × `producto_id`.

Columnas aditivas: `polizas_emitidas`, `prima_emitida_usd`, `siniestros_pagados`, `costo_siniestros_usd`. También trae `nombre_plan`, `tipo_producto`, `es_premium` para no mezclar fuentes en el tablero.

Esta es la única tabla que debe leer Looker Studio. Un `SELECT *` tiene que quedar muy por debajo de 50 MB.

### `core.fct_venta`

Grano: una fila por póliza vigente. Es el último evento de `raw.polizas` ordenado por `updated_at` descendente, y en empate `D` > `U` > `I`. Si el último `op` es `D`, la póliza no está.

`cuenta_como_emitida` es falso cuando `estado = ANULADA`.

### `core.fct_siniestro`

Grano: una fila por `claim_id`. `es_pagado` marca `PAGADO`. `costo_usd` es nulo si no está pagado. `dias_hasta_reporte` es `reported_on - occurred_on`. Las fechas del origen vienen mezcladas (`DD/MM/YYYY` y `YYYY-MM-DD`); en el fact ya están en `DATE`.

### `core.dim_producto`

Grano: una fila por `producto_id`. `nombre_plan`, `tipo` (`MEDICO`, `LARGA`, `CANCELACION`, `EQUIPAJE`, `CORPORATIVO`), `cobertura_max_usd`, `es_premium`.

### `core.dim_agencia`

Grano: una fila por `agencia_id`. `nombre`, `pais`, `canal`.

## Cómo responder

1. Si la pregunta es siniestralidad, país, plan, trimestre, frecuencia o severidad, consultar el mart.
2. Agregar con `SUM` y dividir con `SAFE_DIVIDE`.
3. El último trimestre con datos es el trimestre calendario de `MAX(mes_emision)`, no el trimestre de hoy si el mart todavía no lo tiene.
4. Decir el supuesto cuando la pregunta dependa de una definición que el glosario original no traía (anuladas fuera, solo pagados, cohorte de emisión).
5. Responder con los números en dólares y nombrar el plan o el país.

Patrón de siniestralidad por plan:

```sql
SELECT
  nombre_plan,
  SUM(prima_emitida_usd) AS prima_usd,
  SUM(costo_siniestros_usd) AS costo_usd,
  SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
FROM `a365-de-imangini.mart.siniestralidad_cohorte`
GROUP BY nombre_plan
ORDER BY siniestralidad DESC
```

Patrón de frecuencia contra severidad:

```sql
SELECT
  nombre_plan,
  SAFE_DIVIDE(SUM(siniestros_pagados), SUM(polizas_emitidas)) AS frecuencia,
  SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(siniestros_pagados)) AS severidad_usd
FROM `a365-de-imangini.mart.siniestralidad_cohorte`
GROUP BY nombre_plan
```
