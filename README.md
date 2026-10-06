# SolarBI Pascual · Power BI y Grafana sobre los mismos datos

> One governed dataset, two views: Grafana for real-time operations and Power BI for business decisions.

## Integrantes

| Nombre completo | Usuario de GitHub |
|---|---|
| Daniela Montoya Quintero | @danielita2508 |
| Isaac Madera Jiménez | @IsaVonxz-type |

**Curso:** Inteligencia de Negocios · Grupo 50 · Semestre 2026-II
**Docente:** Ramiro Grisales Montoya
**Institución:** Institución Universitaria Pascual Bravo

## Descripción

Trabajo de consulta del proyecto de aula SolarBI Pascual. A partir de la telemetría simulada de un
inversor solar de 5 kWp se construye un flujo ETL por capas (Bronze, Silver, Gold) que carga en
PostgreSQL, y sobre esa misma base se publican dos vistas: un tablero en Power BI y un dashboard en
Grafana. El enfoque del grupo es calidad y desempeño: porcentaje de datos válidos, yield y ahorro.

## Estructura

```
├── docs/       PDF de la consulta
├── data/       bronze/ (crudo, no se modifica) y silver/ (limpio + reporte de calidad)
├── etl/        simulador.py, run_etl.py
├── sql/        tablas y consultas de verificación en PostgreSQL
├── powerbi/    archivo .pbix o proyecto .pbip
└── grafana/    dashboard.json exportado
```

## Cómo reproducir la práctica

Requisitos: Python 3.10 o superior y Docker Desktop (o un PostgreSQL y un Grafana OSS ya instalados).

1. Clonar el repositorio y crear el archivo de configuración local:

   ```bash
   git clone https://github.com/danielita2508/solarbi-montoya-jimenez.git
   cd solarbi-montoya-jimenez
   cp .env.example .env
   ```

   Editar `.env` y poner una contraseña propia. Este archivo no se sube al repositorio.

2. Instalar las dependencias de Python:

   ```bash
   pip install -r requirements.txt
   ```

3. Levantar PostgreSQL y Grafana:

   ```bash
   docker compose up -d
   ```

4. Ejecutar el flujo completo con un único comando:

   ```bash
   python etl/run_etl.py
   ```

   El comando lee Bronze (lo genera con el simulador solo si no existe), aplica las reglas de
   calidad, guarda Silver en `data/silver/` y carga `silver.lectura_5min`, `dwh.dim_dispositivo` y
   `dwh.fact_energia_dia`. Al final imprime el reporte de calidad y los conteos de cada tabla.

5. Ejecutarlo de nuevo: los conteos deben ser los mismos (carga idempotente). También se pueden
   consultar con `sql/02_verificacion.sql`.

6. Power BI: abrir el archivo de `powerbi/` y, si hace falta, cambiar el servidor a `localhost:5433`.

7. Grafana: entrar a <http://localhost:3000>, agregar PostgreSQL como data source (host
   `postgres:5432` si se usa Docker Compose) e importar `grafana/dashboard.json`.

## Reglas de calidad (Bronze → Silver)

Cada fila se rechaza por la primera regla que incumple, en este orden:

| # | Regla | Criterio |
|---|---|---|
| 1 | Duplicados | Misma combinación `ts` + `dispositivo_id`; se conserva la primera fila |
| 2 | Datos faltantes | Algún campo vacío |
| 3 | Rango físico | `p_ac_kw` entre 0 y 5,5 kW; `irradiancia_wm2` entre 0 y 1400 W/m²; `temp_modulo_c` entre −10 y 90 °C |

`pct_datos_validos` = filas válidas / filas leídas × 100.
Energía de cada intervalo = `p_ac_kw` × 5/60 h.

## Automatización

Expresión cron para lanzar el flujo todos los días a la medianoche:

```
0 0 * * * cd /ruta/al/repositorio && python etl/run_etl.py >> etl.log 2>&1
```

## Quién hizo qué

| Tarea | Responsable |
|---|---|
| _Por completar_ | _Por completar_ |
