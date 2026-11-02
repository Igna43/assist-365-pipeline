"""Profile queries used to write analysis/resultados.md. Read-only."""

from __future__ import annotations

import json

from google.cloud import bigquery

from src.config import ROOT, Settings

QUERIES = {
    "por_plan": """
        SELECT nombre_plan, producto_id,
          SUM(polizas_emitidas) AS polizas,
          SUM(prima_emitida_usd) AS prima_usd,
          SUM(costo_siniestros_usd) AS costo_usd,
          SUM(siniestros_pagados) AS siniestros,
          SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad,
          SAFE_DIVIDE(SUM(siniestros_pagados), SUM(polizas_emitidas)) AS frecuencia,
          SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(siniestros_pagados)) AS severidad
        FROM `${project}.mart.siniestralidad_cohorte`
        GROUP BY nombre_plan, producto_id
        ORDER BY siniestralidad DESC
    """,
    "por_pais": """
        SELECT pais_emision,
          SUM(polizas_emitidas) AS polizas,
          SUM(prima_emitida_usd) AS prima_usd,
          SUM(costo_siniestros_usd) AS costo_usd,
          SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
        FROM `${project}.mart.siniestralidad_cohorte`
        GROUP BY pais_emision
        ORDER BY siniestralidad DESC
    """,
    "trimestre_pais": """
        WITH bounds AS (
          SELECT DATE_TRUNC(MAX(mes_emision), QUARTER) AS trimestre
          FROM `${project}.mart.siniestralidad_cohorte`
        )
        SELECT b.trimestre, m.pais_emision,
          SUM(m.prima_emitida_usd) AS prima_usd,
          SUM(m.costo_siniestros_usd) AS costo_usd,
          SAFE_DIVIDE(SUM(m.costo_siniestros_usd), SUM(m.prima_emitida_usd)) AS siniestralidad,
          SAFE_DIVIDE(SUM(m.siniestros_pagados), SUM(m.polizas_emitidas)) AS frecuencia,
          SAFE_DIVIDE(SUM(m.costo_siniestros_usd), SUM(m.siniestros_pagados)) AS severidad
        FROM `${project}.mart.siniestralidad_cohorte` m
        CROSS JOIN bounds b
        WHERE m.mes_emision >= b.trimestre
          AND m.mes_emision < DATE_ADD(b.trimestre, INTERVAL 3 MONTH)
        GROUP BY b.trimestre, m.pais_emision
        ORDER BY siniestralidad DESC
    """,
    "trimestre_plan": """
        WITH bounds AS (
          SELECT DATE_TRUNC(MAX(mes_emision), QUARTER) AS trimestre
          FROM `${project}.mart.siniestralidad_cohorte`
        )
        SELECT b.trimestre, m.nombre_plan,
          SUM(m.prima_emitida_usd) AS prima_usd,
          SUM(m.costo_siniestros_usd) AS costo_usd,
          SUM(m.costo_siniestros_usd) - SUM(m.prima_emitida_usd) AS perdida_usd,
          SAFE_DIVIDE(SUM(m.costo_siniestros_usd), SUM(m.prima_emitida_usd)) AS siniestralidad,
          SAFE_DIVIDE(SUM(m.siniestros_pagados), SUM(m.polizas_emitidas)) AS frecuencia,
          SAFE_DIVIDE(SUM(m.costo_siniestros_usd), SUM(m.siniestros_pagados)) AS severidad
        FROM `${project}.mart.siniestralidad_cohorte` m
        CROSS JOIN bounds b
        WHERE m.mes_emision >= b.trimestre
          AND m.mes_emision < DATE_ADD(b.trimestre, INTERVAL 3 MONTH)
        GROUP BY b.trimestre, m.nombre_plan
        ORDER BY perdida_usd DESC
    """,
    "por_trimestre": """
        SELECT DATE_TRUNC(mes_emision, QUARTER) AS trimestre,
          SUM(prima_emitida_usd) AS prima_usd,
          SUM(costo_siniestros_usd) AS costo_usd,
          SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
        FROM `${project}.mart.siniestralidad_cohorte`
        GROUP BY trimestre
        ORDER BY trimestre
    """,
    "anticipacion": """
        WITH claims AS (
          SELECT policy_id,
            COUNTIF(es_pagado) AS siniestros_pagados,
            SUM(IF(es_pagado, costo_usd, 0)) AS costo_usd
          FROM `${project}.core.fct_siniestro`
          GROUP BY policy_id
        )
        SELECT
          CASE
            WHEN anticipacion_dias < 0 THEN 'negativa'
            WHEN anticipacion_dias <= 2 THEN '0 a 2 dias'
            WHEN anticipacion_dias <= 14 THEN '3 a 14 dias'
            WHEN anticipacion_dias <= 45 THEN '15 a 45 dias'
            ELSE 'mas de 45 dias'
          END AS anticipacion,
          COUNT(*) AS polizas,
          SUM(v.prima_usd) AS prima_usd,
          SUM(IFNULL(c.siniestros_pagados, 0)) AS siniestros_pagados,
          SUM(IFNULL(c.costo_usd, 0)) AS costo_usd
        FROM `${project}.core.fct_venta` v
        LEFT JOIN claims c ON c.policy_id = v.poliza_id
        WHERE v.cuenta_como_emitida
        GROUP BY anticipacion
        ORDER BY anticipacion
    """,
    "fuera_de_vigencia": """
        SELECT
          COUNTIF(s.es_pagado) AS pagados,
          COUNTIF(s.es_pagado AND (s.occurred_on < v.inicio_vigencia OR s.occurred_on > v.fin_vigencia)) AS fuera,
          SUM(IF(s.es_pagado, s.costo_usd, 0)) AS costo_usd,
          SUM(IF(s.es_pagado AND (s.occurred_on < v.inicio_vigencia OR s.occurred_on > v.fin_vigencia), s.costo_usd, 0)) AS costo_fuera_usd
        FROM `${project}.core.fct_siniestro` s
        JOIN `${project}.core.fct_venta` v
          ON s.policy_id = v.poliza_id
    """,
    "tipo_vs_producto": """
        SELECT p.tipo AS tipo_producto, s.type AS tipo_siniestro,
          COUNTIF(s.es_pagado) AS pagados,
          SUM(IF(s.es_pagado, s.costo_usd, 0)) AS costo_usd
        FROM `${project}.core.fct_siniestro` s
        JOIN `${project}.core.fct_venta` v ON s.policy_id = v.poliza_id
        JOIN `${project}.core.dim_producto` p ON v.producto_id = p.producto_id
        WHERE v.cuenta_como_emitida
        GROUP BY tipo_producto, tipo_siniestro
        ORDER BY costo_usd DESC
    """,
    "canal": """
        WITH claims AS (
          SELECT policy_id, SUM(IF(es_pagado, costo_usd, 0)) AS costo_usd
          FROM `${project}.core.fct_siniestro`
          GROUP BY policy_id
        )
        SELECT v.canal_origen,
          COUNT(*) AS polizas,
          SUM(v.prima_usd) AS prima_usd,
          SUM(IFNULL(c.costo_usd, 0)) AS costo_usd
        FROM `${project}.core.fct_venta` v
        LEFT JOIN claims c ON c.policy_id = v.poliza_id
        WHERE v.cuenta_como_emitida
        GROUP BY v.canal_origen
        ORDER BY costo_usd DESC
    """,
    "huerfanos_y_fx": """
        SELECT
          (SELECT COUNT(*) FROM `${project}.core.fct_siniestro`) AS siniestros,
          (SELECT COUNT(*) FROM `${project}.core.fct_siniestro` s
            LEFT JOIN `${project}.core.fct_venta` v ON s.policy_id = v.poliza_id
            WHERE v.poliza_id IS NULL) AS siniestros_sin_poliza,
          (SELECT COUNT(*) FROM `${project}.core.fct_venta` WHERE cuenta_como_emitida AND fx_missing) AS emitidas_sin_fx,
          (SELECT COUNT(*) FROM `${project}.core.fct_siniestro` WHERE es_pagado AND costo_usd IS NULL) AS pagados_sin_usd,
          (SELECT COUNT(*) FROM `${project}.core.fct_venta`) AS polizas_vigentes_o_no,
          (SELECT COUNT(*) FROM `${project}.core.fct_venta` WHERE NOT cuenta_como_emitida) AS anuladas,
          (SELECT COUNT(*) FROM `${project}.raw.polizas` WHERE op = 'D') AS eventos_delete
    """,
    "demora_reporte": """
        SELECT
          APPROX_QUANTILES(dias_hasta_reporte, 4) AS cuartiles_dias,
          COUNTIF(dias_hasta_reporte < 0) AS reporte_antes_de_ocurrir,
          COUNTIF(reported_on IS NULL OR occurred_on IS NULL) AS fechas_invalidas
        FROM `${project}.core.fct_siniestro`
    """,
    "anuladas_con_pago": """
        SELECT COUNT(DISTINCT v.poliza_id) AS polizas_anuladas_con_pago,
          SUM(s.costo_usd) AS costo_usd
        FROM `${project}.core.fct_venta` v
        JOIN `${project}.core.fct_siniestro` s ON s.policy_id = v.poliza_id
        WHERE NOT v.cuenta_como_emitida AND s.es_pagado
    """,
    "canal_anticipacion": """
        WITH claims AS (
          SELECT policy_id, SUM(IF(es_pagado, costo_usd, 0)) AS costo_usd,
            COUNTIF(es_pagado AND costo_usd IS NOT NULL) AS siniestros
          FROM `${project}.core.fct_siniestro`
          GROUP BY policy_id
        )
        SELECT v.canal_origen,
          IF(v.anticipacion_dias <= 2, '0 a 2 dias', '3 dias o mas') AS anticipacion,
          COUNT(*) AS polizas,
          SUM(v.prima_usd) AS prima_usd,
          SUM(IFNULL(c.costo_usd, 0)) AS costo_usd,
          SUM(IFNULL(c.siniestros, 0)) AS siniestros
        FROM `${project}.core.fct_venta` v
        LEFT JOIN claims c ON c.policy_id = v.poliza_id
        WHERE v.cuenta_como_emitida AND NOT v.fx_missing
        GROUP BY v.canal_origen, anticipacion
        ORDER BY v.canal_origen, anticipacion
    """,
}


def main() -> None:
    settings = Settings.from_env(require_token=False)
    client = bigquery.Client(project=settings.project, location=settings.location)
    output = {}
    for name, sql in QUERIES.items():
        rows = list(client.query(sql.replace("${project}", settings.project)).result())
        output[name] = [dict(row) for row in rows]
        print(name, len(rows), flush=True)
    path = ROOT / "analysis" / "profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
