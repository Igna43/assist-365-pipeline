# Preguntas de negocio

Resueltas contra `a365-de-imangini` llamando al MCP `assist365-bigquery` (`list_tables`, `describe_table`, `run_select`). Las definiciones están en `SKILL.md`.

## Herramientas

`list_tables`

```json
{
  "raw": [
    "agencias",
    "polizas",
    "productos",
    "siniestros",
    "tipo_cambio"
  ],
  "core": [
    "dim_agencia",
    "dim_producto",
    "dim_tipo_cambio",
    "fct_siniestro",
    "fct_venta"
  ],
  "mart": [
    "siniestralidad_cohorte"
  ],
  "ops": [
    "extract_counts",
    "pipeline_runs",
    "watermarks"
  ]
}
```

`describe_table` mart.siniestralidad_cohorte

```json
{
  "table": "mart.siniestralidad_cohorte",
  "num_rows": 2304,
  "num_bytes": 217152,
  "columns": [
    {
      "name": "mes_emision",
      "type": "DATE",
      "mode": "NULLABLE"
    },
    {
      "name": "pais_emision",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "producto_id",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "nombre_plan",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "tipo_producto",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "es_premium",
      "type": "BOOLEAN",
      "mode": "NULLABLE"
    },
    {
      "name": "polizas_emitidas",
      "type": "INTEGER",
      "mode": "NULLABLE"
    },
    {
      "name": "prima_emitida_usd",
      "type": "NUMERIC",
      "mode": "NULLABLE"
    },
    {
      "name": "siniestros_pagados",
      "type": "INTEGER",
      "mode": "NULLABLE"
    },
    {
      "name": "costo_siniestros_usd",
      "type": "NUMERIC",
      "mode": "NULLABLE"
    }
  ]
}
```

## ¿Cuál es la siniestralidad por plan, en dólares?

Herramienta: `run_select`

```sql
SELECT
              nombre_plan,
              producto_id,
              SUM(polizas_emitidas) AS polizas,
              SUM(prima_emitida_usd) AS prima_usd,
              SUM(costo_siniestros_usd) AS costo_usd,
              SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            GROUP BY nombre_plan, producto_id
            ORDER BY siniestralidad DESC
```

```json
{
  "job_id": "bfe8365c-3577-46f2-aafb-a67d032f7b4d",
  "total_bytes_processed": 148224,
  "row_count_returned": 12,
  "rows": [
    {
      "nombre_plan": "Equipaje Protegido",
      "producto_id": "PRD-11",
      "polizas": 43888,
      "prima_usd": "1379685.545426066",
      "costo_usd": "2039633.869831018",
      "siniestralidad": "1.478332419"
    },
    {
      "nombre_plan": "Estudiante Larga",
      "producto_id": "PRD-09",
      "polizas": 51390,
      "prima_usd": "2145290.170349797",
      "costo_usd": "2461680.461889703",
      "siniestralidad": "1.147481351"
    },
    {
      "nombre_plan": "Esencial 30",
      "producto_id": "PRD-01",
      "polizas": 117595,
      "prima_usd": "7361732.257827184",
      "costo_usd": "5989015.626488",
      "siniestralidad": "0.813533475"
    },
    {
      "nombre_plan": "Cancelacion Plus",
      "producto_id": "PRD-10",
      "polizas": 58404,
      "prima_usd": "4456277.921153173",
      "costo_usd": "2799015.649019372",
      "siniestralidad": "0.628106168"
    },
    {
      "nombre_plan": "Esencial 60",
      "producto_id": "PRD-02",
      "polizas": 95558,
      "prima_usd": "7944168.280906389",
      "costo_usd": "4765499.825389036",
      "siniestralidad": "0.599873978"
    },
    {
      "nombre_plan": "Senior 100",
      "producto_id": "PRD-07",
      "polizas": 43861,
      "prima_usd": "4716701.140310429",
      "costo_usd": "2245179.278734805",
      "siniestralidad": "0.476006262"
    },
    {
      "nombre_plan": "Clasico Plus 150",
      "producto_id": "PRD-04",
      "polizas": 66341,
      "prima_usd": "8969192.908733479",
      "costo_usd": "3342577.551088245",
      "siniestralidad": "0.37267317"
    },
    {
      "nombre_plan": "Corporativo Anual",
      "producto_id": "PRD-12",
      "polizas": 29399,
      "prima_usd": "4664330.927594167",
      "costo_usd": "1501839.25709746",
      "siniestralidad": "0.321983856"
    },
    {
      "nombre_plan": "Premium 250",
      "producto_id": "PRD-05",
      "polizas": 58351,
      "prima_usd": "10939264.852234014",
      "costo_usd": "3084588.680467274",
      "siniestralidad": "0.281974038"
    },
    {
      "nombre_plan": "Clasico 100",
      "producto_id": "PRD-03",
      "polizas": 102462,
      "prima_usd": "22044846.865376396",
      "costo_usd": "5342081.334674826",
      "siniestralidad": "0.242327895"
    },
    {
      "nombre_plan": "Premium Total 500",
      "producto_id": "PRD-06",
      "polizas": 36534,
      "prima_usd": "10075330.701992108",
      "costo_usd": "1944503.428228603",
      "siniestralidad": "0.192996487"
    },
    {
      "nombre_plan": "Senior Premium 200",
      "producto_id": "PRD-08",
      "polizas": 29386,
      "prima_usd": "9530994.917507276",
      "costo_usd": "1506339.446806795",
      "siniestralidad": "0.158046401"
    }
  ]
}
```

## ¿Cuál es la siniestralidad por país, en dólares?

Herramienta: `run_select`

```sql
SELECT
              pais_emision,
              SUM(polizas_emitidas) AS polizas,
              SUM(prima_emitida_usd) AS prima_usd,
              SUM(costo_siniestros_usd) AS costo_usd,
              SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            GROUP BY pais_emision
            ORDER BY siniestralidad DESC
```

```json
{
  "job_id": "2c66dfce-f4c0-42d5-89b4-d8878d11b59d",
  "total_bytes_processed": 101376,
  "row_count_returned": 6,
  "rows": [
    {
      "pais_emision": "CL",
      "polizas": 88284,
      "prima_usd": "11021147.069782235",
      "costo_usd": "4365557.65907187",
      "siniestralidad": "0.396107377"
    },
    {
      "pais_emision": "CO",
      "polizas": 131887,
      "prima_usd": "16922499.840581143",
      "costo_usd": "6683558.973703046",
      "siniestralidad": "0.394951044"
    },
    {
      "pais_emision": "AR",
      "polizas": 205521,
      "prima_usd": "25570784.39553829",
      "costo_usd": "10070297.300487387",
      "siniestralidad": "0.39382043"
    },
    {
      "pais_emision": "MX",
      "polizas": 175567,
      "prima_usd": "22868472.1426964",
      "costo_usd": "8985564.318521884",
      "siniestralidad": "0.392923684"
    },
    {
      "pais_emision": "BR",
      "polizas": 58884,
      "prima_usd": "8016906.706214554",
      "costo_usd": "3115012.518908296",
      "siniestralidad": "0.388555416"
    },
    {
      "pais_emision": "PE",
      "polizas": 73026,
      "prima_usd": "9828006.334597856",
      "costo_usd": "3801963.639022654",
      "siniestralidad": "0.386849938"
    }
  ]
}
```

## ¿Qué país está peor en el último trimestre con datos?

Herramienta: `run_select`

```sql
WITH bounds AS (
              SELECT DATE_TRUNC(MAX(mes_emision), QUARTER) AS trimestre
              FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            )
            SELECT
              b.trimestre,
              m.pais_emision,
              SUM(m.polizas_emitidas) AS polizas,
              SUM(m.prima_emitida_usd) AS prima_usd,
              SUM(m.costo_siniestros_usd) AS costo_usd,
              SAFE_DIVIDE(SUM(m.costo_siniestros_usd), SUM(m.prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte` AS m
            CROSS JOIN bounds AS b
            WHERE m.mes_emision >= b.trimestre
              AND m.mes_emision < DATE_ADD(b.trimestre, INTERVAL 3 MONTH)
            GROUP BY b.trimestre, m.pais_emision
            ORDER BY siniestralidad DESC
```

```json
{
  "job_id": "db556ef0-5d0d-4399-bca8-15dd0f9923d2",
  "total_bytes_processed": 119808,
  "row_count_returned": 6,
  "rows": [
    {
      "trimestre": "2026-07-01",
      "pais_emision": "CO",
      "polizas": 8209,
      "prima_usd": "989648.678042289",
      "costo_usd": "430973.21585662",
      "siniestralidad": "0.43548102"
    },
    {
      "trimestre": "2026-07-01",
      "pais_emision": "MX",
      "polizas": 11147,
      "prima_usd": "1425433.75741969",
      "costo_usd": "589208.101867176",
      "siniestralidad": "0.413353549"
    },
    {
      "trimestre": "2026-07-01",
      "pais_emision": "AR",
      "polizas": 12906,
      "prima_usd": "1506029.62541703",
      "costo_usd": "605044.598620776",
      "siniestralidad": "0.401748139"
    },
    {
      "trimestre": "2026-07-01",
      "pais_emision": "BR",
      "polizas": 3685,
      "prima_usd": "499070.249542388",
      "costo_usd": "191840.498121204",
      "siniestralidad": "0.384395781"
    },
    {
      "trimestre": "2026-07-01",
      "pais_emision": "PE",
      "polizas": 4532,
      "prima_usd": "621775.177097982",
      "costo_usd": "237608.232593195",
      "siniestralidad": "0.382144932"
    },
    {
      "trimestre": "2026-07-01",
      "pais_emision": "CL",
      "polizas": 5442,
      "prima_usd": "661896.759902221",
      "costo_usd": "251789.119129991",
      "siniestralidad": "0.380405426"
    }
  ]
}
```

## ¿Qué plan destruye margen, mirando la pérdida en dólares y la siniestralidad?

Herramienta: `run_select`

```sql
SELECT
              nombre_plan,
              producto_id,
              SUM(prima_emitida_usd) AS prima_usd,
              SUM(costo_siniestros_usd) AS costo_usd,
              SUM(costo_siniestros_usd) - SUM(prima_emitida_usd) AS perdida_usd,
              SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(prima_emitida_usd)) AS siniestralidad
            FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            GROUP BY nombre_plan, producto_id
            ORDER BY perdida_usd DESC
```

```json
{
  "job_id": "095ebf78-9c7c-4ade-9734-c75eb8aae67b",
  "total_bytes_processed": 129792,
  "row_count_returned": 12,
  "rows": [
    {
      "nombre_plan": "Equipaje Protegido",
      "producto_id": "PRD-11",
      "prima_usd": "1379685.545426066",
      "costo_usd": "2039633.869831018",
      "perdida_usd": "659948.324404952",
      "siniestralidad": "1.478332419"
    },
    {
      "nombre_plan": "Estudiante Larga",
      "producto_id": "PRD-09",
      "prima_usd": "2145290.170349797",
      "costo_usd": "2461680.461889703",
      "perdida_usd": "316390.291539906",
      "siniestralidad": "1.147481351"
    },
    {
      "nombre_plan": "Esencial 30",
      "producto_id": "PRD-01",
      "prima_usd": "7361732.257827184",
      "costo_usd": "5989015.626488",
      "perdida_usd": "-1372716.631339184",
      "siniestralidad": "0.813533475"
    },
    {
      "nombre_plan": "Cancelacion Plus",
      "producto_id": "PRD-10",
      "prima_usd": "4456277.921153173",
      "costo_usd": "2799015.649019372",
      "perdida_usd": "-1657262.272133801",
      "siniestralidad": "0.628106168"
    },
    {
      "nombre_plan": "Senior 100",
      "producto_id": "PRD-07",
      "prima_usd": "4716701.140310429",
      "costo_usd": "2245179.278734805",
      "perdida_usd": "-2471521.861575624",
      "siniestralidad": "0.476006262"
    },
    {
      "nombre_plan": "Corporativo Anual",
      "producto_id": "PRD-12",
      "prima_usd": "4664330.927594167",
      "costo_usd": "1501839.25709746",
      "perdida_usd": "-3162491.670496707",
      "siniestralidad": "0.321983856"
    },
    {
      "nombre_plan": "Esencial 60",
      "producto_id": "PRD-02",
      "prima_usd": "7944168.280906389",
      "costo_usd": "4765499.825389036",
      "perdida_usd": "-3178668.455517353",
      "siniestralidad": "0.599873978"
    },
    {
      "nombre_plan": "Clasico Plus 150",
      "producto_id": "PRD-04",
      "prima_usd": "8969192.908733479",
      "costo_usd": "3342577.551088245",
      "perdida_usd": "-5626615.357645234",
      "siniestralidad": "0.37267317"
    },
    {
      "nombre_plan": "Premium 250",
      "producto_id": "PRD-05",
      "prima_usd": "10939264.852234014",
      "costo_usd": "3084588.680467274",
      "perdida_usd": "-7854676.17176674",
      "siniestralidad": "0.281974038"
    },
    {
      "nombre_plan": "Senior Premium 200",
      "producto_id": "PRD-08",
      "prima_usd": "9530994.917507276",
      "costo_usd": "1506339.446806795",
      "perdida_usd": "-8024655.470700481",
      "siniestralidad": "0.158046401"
    },
    {
      "nombre_plan": "Premium Total 500",
      "producto_id": "PRD-06",
      "prima_usd": "10075330.701992108",
      "costo_usd": "1944503.428228603",
      "perdida_usd": "-8130827.273763505",
      "siniestralidad": "0.192996487"
    },
    {
      "nombre_plan": "Clasico 100",
      "producto_id": "PRD-03",
      "prima_usd": "22044846.865376396",
      "costo_usd": "5342081.334674826",
      "perdida_usd": "-16702765.53070157",
      "siniestralidad": "0.242327895"
    }
  ]
}
```

## En el plan que más margen destruye, ¿el problema es la frecuencia de siniestros o el monto promedio?

Herramienta: `run_select`

```sql
WITH by_plan AS (
              SELECT
                nombre_plan,
                SAFE_DIVIDE(SUM(siniestros_pagados), SUM(polizas_emitidas)) AS frecuencia,
                SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(siniestros_pagados)) AS severidad_usd,
                SUM(costo_siniestros_usd) - SUM(prima_emitida_usd) AS perdida_usd
              FROM `a365-de-imangini.mart.siniestralidad_cohorte`
              GROUP BY nombre_plan
            ),
            portafolio AS (
              SELECT
                SAFE_DIVIDE(SUM(siniestros_pagados), SUM(polizas_emitidas)) AS frecuencia,
                SAFE_DIVIDE(SUM(costo_siniestros_usd), SUM(siniestros_pagados)) AS severidad_usd
              FROM `a365-de-imangini.mart.siniestralidad_cohorte`
            )
            SELECT
              b.nombre_plan,
              b.frecuencia,
              p.frecuencia AS frecuencia_portafolio,
              SAFE_DIVIDE(b.frecuencia, p.frecuencia) AS frecuencia_vs_portafolio,
              b.severidad_usd,
              p.severidad_usd AS severidad_portafolio,
              SAFE_DIVIDE(b.severidad_usd, p.severidad_usd) AS severidad_vs_portafolio
            FROM by_plan AS b
            CROSS JOIN portafolio AS p
            WHERE b.nombre_plan = (
              SELECT nombre_plan FROM by_plan ORDER BY perdida_usd DESC LIMIT 1
            )
```

```json
{
  "job_id": "17cb73b4-da00-400e-ae66-6a3da70b2a38",
  "total_bytes_processed": 148224,
  "row_count_returned": 1,
  "rows": [
    {
      "nombre_plan": "Equipaje Protegido",
      "frecuencia": 0.1374635435654393,
      "frecuencia_portafolio": 0.14163583021104276,
      "frecuencia_vs_portafolio": 0.9705421527915176,
      "severidad_usd": "338.079540831",
      "severidad_portafolio": "356.518536731",
      "severidad_vs_portafolio": "0.948280401"
    }
  ]
}
```
