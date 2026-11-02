-- Fails when a current policy is stored more than once.
SELECT poliza_id, COUNT(*) AS n
FROM `${project}.core.fct_venta`
GROUP BY poliza_id
HAVING COUNT(*) > 1
