# Assist-365 — de la API al tablero

Pipeline que corre: API interna, archivos en Cloud Storage, BigQuery y un mart chico para Looker Studio. Proyecto `a365-de-imangini`.

## Arquitectura

```
API  ->  Python (reintentos)  ->  GCS NDJSON gzip
                                      |
                                      v
                               BigQuery raw
                                      |
                                      v
                         core (hechos y dimensiones)
                                      |
                                      v
                    mart.siniestralidad_cohorte  ->  Looker Studio
```

Cloud Scheduler dispara un Cloud Run Job todos los días a las 08:00, hora de Bogotá.

## Por qué la carga es un load job y no streaming

Hay 1.003.461 eventos de póliza. Un load job desde GCS es gratis, atómico y se puede repetir desde el archivo. El streaming insert cobra y tiene cupo por fila. Cada corrida escribe NDJSON, lo comprime y lo carga con esquema explícito.

Pólizas: la primera corrida trunca `raw.polizas`. Las siguientes hacen `MERGE` contra un stage, con clave `(poliza_id, updated_at, op)`.

Siniestros y catálogos: reemplazo completo. El siniestro no tiene cursor de cambios y son 139 mil filas.

## Qué hace la segunda corrida

- Pólizas: incremental. El watermark es el máximo `updated_at` ya cargado. Se manda `updated_since`. La API salta a la primera página que contiene un registro posterior, y esa página todavía trae filas viejas: el cliente descarta `updated_at` menor o igual al watermark. El `MERGE` hace idempotente un solapamiento.
- Siniestros, productos, agencias y tipo de cambio: se vuelven a traer enteros y se reemplaza la tabla cruda.
- Los hechos se reconstruyen siempre desde el log completo de eventos. Un `D` o un `U` tardío cambia la póliza vigente aunque el archivo del día sea chico.

## Grano

- `raw.polizas`: un evento de cambio (`op` I, U o D).
- `raw.siniestros`: un siniestro de la foto del día.
- `core.fct_venta`: una fila por póliza vigente. Gana el `updated_at` más nuevo y, en empate, `D` sobre `U` sobre `I`. Si el último `op` es `D`, la póliza no está.
- `core.fct_siniestro`: una fila por `claim_id`.
- `core.dim_producto`: una fila por `producto_id`.
- `core.dim_agencia`: una fila por `agencia_id`.
- `core.dim_tipo_cambio`: una fila por fecha y moneda, con la tasa usada ese día.
- `mart.siniestralidad_cohorte`: una fila por mes de emisión, país de emisión y producto. Solo columnas aditivas.

## Definiciones que el glosario no traía

Quedaron escritas también en `SKILL.md`.

- Prima emitida: prima en dólares de las pólizas cuyo estado vigente no es `ANULADA`. No hay campo de devolución, así que la anulada sale del denominador. La fecha de venta es `DATE(fecha_emision_utc)`.
- Costo de siniestros: monto solo si `status = PAGADO`. `RECHAZADO` y `EN_ANALISIS` no entran.
- Siniestralidad: cohorte de emisión, no calendario de ocurrencia. El siniestro pagado se cuelga del mes, país y plan de su póliza. Así "este trimestre" responde qué se vendió en el trimestre.
- Frecuencia: siniestros pagados / pólizas emitidas. Severidad: costo USD / siniestros pagados. En Looker y en el MCP el ratio es `SUM / SUM`, nunca un promedio de ratios.
- Dólares: `monto * factor_usd` con la moneda de la fila. La prima usa la fecha de emisión. El siniestro usa la fecha de ocurrencia.
- Las pólizas anuladas tampoco aportan sus siniestros al mart. Si no, el costo entraría y la prima no, y la siniestralidad se infla. Hay 287 pólizas anuladas con un pago, USD 144.639, fuera del ratio a propósito.

## Tipo de cambio

El calendario publicado tiene huecos: 5.124 filas son 732 fechas, no todos los días entre 2024-01-01 y 2026-10-30. `dim_tipo_cambio` arma un día por moneda y arrastra la última tasa (`carried_forward`). Después de la última fecha publicada la marca es `extrapolated_forward`. Sin eso, 215.219 pólizas emitidas se quedaban sin dólares aunque la fecha cayera adentro del rango.

## Tablero y bytes

Looker Studio lee solamente `mart.siniestralidad_cohorte`. Es una tabla, no una vista sobre los hechos. Tiene 2.304 filas.

```
bq query --dry_run --use_legacy_sql=false \
  'SELECT * FROM `a365-de-imangini.mart.siniestralidad_cohorte`'
```

Esa consulta procesa **217.152 bytes (0,21 MB)**. El tope del ejercicio es 50 MB.

Campos calculados, siempre con suma sobre suma:

- `Siniestralidad` = `SUM(costo_siniestros_usd) / SUM(prima_emitida_usd)`
- `Frecuencia` = `SUM(siniestros_pagados) / SUM(polizas_emitidas)`
- `Severidad` = `SUM(costo_siniestros_usd) / SUM(siniestros_pagados)`

Cuatro gráficos en una página, con filtro de fecha sobre `mes_emision` (default 2026-07-01 a 2026-09-30, el último trimestre con emisiones), país y plan:

1. Barras de siniestralidad por país.
2. Barras de siniestralidad por plan, con la prima emitida en la misma vista para que un plan chico no parezca el problema.
3. Dispersión: frecuencia en X, severidad en Y, plan como dimensión.
4. Serie mensual de siniestralidad.

El conector es el nativo de BigQuery, credenciales del dueño (`ignacio.mangini43@gmail.com`). El informe está guardado. El filtro de fecha del control queda fijo en 2026-07-01 a 2026-09-30. En ese trimestre el país con peor siniestralidad es Colombia.

Informe:

`https://lookerstudio.google.com/reporting/cf842e57-56b4-4775-88c9-0e8483b97352`

Hay que compartirlo con `gbarrientos@assist-365.com` desde Share (el acceso sigue restringido al dueño).

## Qué hay de raro en los datos

- Las fechas del siniestro mezclan `DD/MM/YYYY` y `YYYY-MM-DD`. La barra es día primero: hay valores con día mayor a 12.
- `amount.currency` a veces viene como `NaN`. Quedan 313 siniestros pagados sin dólares. No se inventó una moneda.
- 477 siniestros pagados traen monto negativo en el origen. El factor de cambio no es negativo. El neto los conserva, porque bajarían el costo si se tiran.
- `detail` tiene tres formas: claves en español, claves en inglés, o solo `proveedor`.
- La moneda de la póliza no coincide siempre con el país. La conversión usa la moneda de la fila.
- El mismo `poliza_id` aparece más de una vez en una página. El hecho se queda con el último evento. Hay 20.000 eventos `D`.
- `updated_since` no filtra por fila. La página del salto incluye registros anteriores al watermark.
- Hay `updated_at` en el futuro (el watermark de la primera carga quedó en 2027-02-10).
- 4.025 siniestros no matchean ninguna póliza vigente y no entran al mart.
- Equipaje Protegido paga sobre todo siniestros médicos. Está en `analysis/resultados.md`.

## Cómo correrlo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # A365_API_TOKEN no se commitea
python -m src.pipeline              # extract, load, model, tests
python -m src.pipeline --only transform
python -m src.pipeline --only test
pytest
python mcp_bigquery/answer_questions.py
```

El token vive en `.env` (gitignored) y se inyecta al Cloud Run Job al deployar. Secret Manager no está habilitado en el proyecto y esta cuenta no puede habilitar APIs.

```bash
bash infra/deploy.sh
```

Quedó desplegado el Cloud Run Job `a365-pipeline` en `us-central1` y el Cloud Scheduler `a365-pipeline-daily`. El cron es `0 8 * * *` en `America/Bogota` (próxima corrida 2026-11-03 08:00). El scheduler hace POST a `jobs/a365-pipeline:run` con el service account de Compute, que tiene `roles/run.invoker` sobre el job.

El job corre como `152941963971-compute@developer.gserviceaccount.com`, que ya tiene `roles/editor`. La cuenta del ejercicio no puede hacer `setIamPolicy` sobre el proyecto, así que la service account `a365-pipeline` no pudo recibir roles de BigQuery. Tiene `storage.objectAdmin` sobre el bucket. El token de la API entra como variable de entorno del job y no se commitea.

## Tests y CI

`tests/data/*.sql` devuelve filas solo cuando fallan. Corren al final del pipeline y tiran abajo el job. Cubren unicidad, dominios, el total de la API contra lo cargado, primas negativas, el signo del costo pagado, la bandera de tipo de cambio, las foreign keys y el grano del mart.

GitHub Actions (`.github/workflows/ci.yml`) corre `ruff` y `pytest`. No llama a la API y no tiene credenciales de GCP. Los tests de warehouse corren en la corrida, donde las credenciales ya están.

## Preguntas en lenguaje natural

`SKILL.md` es la capa semántica. El MCP `assist365-bigquery` expone `list_tables`, `describe_table` y `run_select` (un SELECT, tope de 1 GB). Las cinco preguntas y la respuesta están en `analysis/preguntas.md`. Se contestaron llamando al MCP, no con el CLI de `bq` al lado.

## Resultados

El detalle está en `analysis/resultados.md`. En corto: el país no separa (39% en todos). Equipaje Protegido destruye margen (147,8%, pérdida de USD 659.948) y no es por frecuencia ni por monto: ambos están apenas debajo del portafolio. La compra con 0 a 2 días de anticipación tiene siniestralidad 63,7% contra 33,7% del resto, con el doble de frecuencia y la misma severidad.

## Con más tiempo

- Particionar el log de pólizas por día de ingesta y conservar fotos de siniestros, no solo la última.
- Un loss ratio de calendario al lado de la cohorte, para ver el desfase de maduración del trimestre abierto.
- dbt si el modelo crece y hace falta documentación de linaje dentro de la herramienta.
- El video de diez minutos queda para grabarlo sobre este repo.
