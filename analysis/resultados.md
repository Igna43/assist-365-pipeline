# Resultados

Números de la cohorte de emisión, en dólares. Prima emitida excluye pólizas `ANULADA`. El costo incluye solo siniestros `PAGADO`. El siniestro se atribuye al mes, país y plan de la póliza. Los ratios son `SUM / SUM` sobre `mart.siniestralidad_cohorte`.

La corrida completa dejó 1.003.461 eventos de póliza y 138.962 siniestros, ambos iguales al total que declara la API. El modelo deja 780.000 pólizas vigentes (733.169 emitidas, no anuladas).

## Siniestralidad por plan

| Plan | Pólizas | Prima USD | Costo USD | Siniestralidad |
| --- | ---: | ---: | ---: | ---: |
| Equipaje Protegido | 43.888 | 1.379.686 | 2.039.634 | 147,8% |
| Estudiante Larga | 51.390 | 2.145.290 | 2.461.680 | 114,7% |
| Esencial 30 | 117.595 | 7.361.732 | 5.989.016 | 81,4% |
| Cancelacion Plus | 58.404 | 4.456.278 | 2.799.016 | 62,8% |
| Esencial 60 | 95.558 | 7.944.168 | 4.765.500 | 60,0% |
| Senior 100 | 43.861 | 4.716.701 | 2.245.179 | 47,6% |
| Clasico Plus 150 | 66.341 | 8.969.193 | 3.342.578 | 37,3% |
| Corporativo Anual | 29.399 | 4.664.331 | 1.501.839 | 32,2% |
| Premium 250 | 58.351 | 10.939.265 | 3.084.589 | 28,2% |
| Clasico 100 | 102.462 | 22.044.847 | 5.342.081 | 24,2% |
| Premium Total 500 | 36.534 | 10.075.331 | 1.944.503 | 19,3% |
| Senior Premium 200 | 29.386 | 9.530.995 | 1.506.339 | 15,8% |

Solo dos planes pierden plata: Equipaje Protegido (USD 659.948) y Estudiante Larga (USD 316.390). El resto tiene costo menor que la prima.

## Siniestralidad por país

| País | Prima USD | Costo USD | Siniestralidad |
| --- | ---: | ---: | ---: |
| CL | 11.021.147 | 4.365.558 | 39,6% |
| CO | 16.922.500 | 6.683.559 | 39,5% |
| AR | 25.570.784 | 10.070.297 | 39,4% |
| MX | 22.868.472 | 8.985.564 | 39,3% |
| BR | 8.016.907 | 3.115.013 | 38,9% |
| PE | 9.828.006 | 3.801.964 | 38,7% |

El país casi no mueve la siniestralidad. La diferencia entre el peor y el mejor es un punto.

## Último trimestre con emisiones

El mes de emisión más nuevo del mart cae en el trimestre que empieza el 2026-07-01. El cuarto trimestre de 2026 todavía no tiene mes de emisión.

| País | Siniestralidad | Frecuencia | Severidad USD |
| --- | ---: | ---: | ---: |
| CO | 43,5% | 14,8% | 355 |
| MX | 41,3% | 14,2% | 373 |
| AR | 40,2% | 14,5% | 323 |
| BR | 38,4% | 13,6% | 381 |
| PE | 38,2% | 14,0% | 374 |
| CL | 38,0% | 13,3% | 347 |

Colombia está peor en ese trimestre. Otra vez el rango entre países es chico.

En el mismo trimestre, Equipaje Protegido sigue siendo el plan que destruye margen: siniestralidad 146,0% y pérdida de USD 37.134. Estudiante Larga pierde USD 31.955 (124,9%).

## Frecuencia o monto

En Equipaje Protegido la frecuencia es 13,7% y en el portafolio 14,2% (0,97 veces). La severidad es USD 338 contra USD 357 del portafolio (0,95 veces). No es un problema de frecuencia ni de monto promedio. El plan está barato: cobra como equipaje y paga como el resto.

El 74,9% del costo pagado de Equipaje Protegido es un siniestro `MEDICO`, no `EQUIPAJE`.

## Insight

La anticipación de compra parte el negocio en dos, y nadie la estaba mirando.

Las pólizas emitidas con 0 a 2 días de anticipación al viaje tienen siniestralidad de 63,7%. El resto, 33,7%. La frecuencia es 22,7% contra 12,2%. La severidad es casi la misma: USD 360 contra USD 354. El problema de esa cohorte es la frecuencia, no el monto.

Son el 18,7% de las pólizas emitidas y concentran el 30,3% del costo pagado. Pasa en todos los canales. En Meta, la compra de último momento llega a 80,3% de siniestralidad, y aun comprando con más de dos días Meta queda en 43,4%, por encima del resto de los canales.

El Director Comercial puede actuar sin un modelo nuevo: revisar el precio o el score de la venta con menos de tres días de anticipación, y mirar Meta aparte.
