-- Falla si una póliza vigente quedó guardada más de una vez.
SELECT poliza_id, COUNT(*) AS n
FROM `${project}.core.fct_venta`
GROUP BY poliza_id
HAVING COUNT(*) > 1
