-- Esquemas y tablas de SolarBI. Se puede ejecutar varias veces sin error.
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

-- Silver: lecturas limpias cada 5 minutos
CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts              timestamp     NOT NULL,
    dispositivo_id  integer       NOT NULL,
    p_ac_kw         numeric(8,3)  NOT NULL,
    irradiancia_wm2 numeric(8,1)  NOT NULL,
    temp_modulo_c   numeric(5,1)  NOT NULL,
    PRIMARY KEY (ts, dispositivo_id)
);

-- Gold: dimension minima de dispositivos (la potencia instalada se usa para el yield)
CREATE TABLE IF NOT EXISTS dwh.dim_dispositivo (
    dispositivo_key integer       PRIMARY KEY,
    nombre          text          NOT NULL,
    potencia_kwp    numeric(6,2)  NOT NULL
);

-- Gold: resumen diario por dispositivo
CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha_key         integer       NOT NULL,   -- AAAAMMDD
    dispositivo_key   integer       NOT NULL REFERENCES dwh.dim_dispositivo (dispositivo_key),
    fecha             date          NOT NULL,
    energia_kwh       numeric(10,3) NOT NULL,
    lecturas_leidas   integer       NOT NULL,
    lecturas_validas  integer       NOT NULL,
    pct_datos_validos numeric(5,2)  NOT NULL,
    PRIMARY KEY (fecha_key, dispositivo_key)
);
