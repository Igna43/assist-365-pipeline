-- Falla si el producto de una póliza no está en el catálogo de productos.
SELECT v.poliza_id, v.producto_id
FROM `${project}.core.fct_venta` AS v
LEFT JOIN `${project}.core.dim_producto` AS p
  ON v.producto_id = p.producto_id
WHERE p.producto_id IS NULL
