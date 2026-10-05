-- Conteos para demostrar la carga idempotente: deben ser iguales despues de cada ejecucion del ETL.
SELECT 'silver.lectura_5min' AS tabla, count(*) AS filas FROM silver.lectura_5min
UNION ALL
SELECT 'dwh.dim_dispositivo', count(*) FROM dwh.dim_dispositivo
UNION ALL
SELECT 'dwh.fact_energia_dia', count(*) FROM dwh.fact_energia_dia;

-- Resumen diario cargado
SELECT fecha, dispositivo_key, energia_kwh, lecturas_leidas, lecturas_validas, pct_datos_validos
FROM dwh.fact_energia_dia
ORDER BY fecha, dispositivo_key;
