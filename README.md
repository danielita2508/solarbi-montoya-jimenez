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

   Editar `.env` y poner una contraseña propia en `PGPASSWORD`. El usuario y la base ya vienen en
   el ejemplo (`solarbi`). Este archivo no se sube al repositorio y de dónde sale cada valor se
   explica en [Usuarios y contraseñas](#usuarios-y-contraseñas).

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

6. Power BI: abrir `powerbi/SolarBI.pbip` con Power BI Desktop (requiere activar en Opciones →
   Características de vista previa la opción de guardar con formato de proyecto de Power BI). Cuando
   pida credenciales de la base de datos PostgreSQL, usar `PGUSER` y `PGPASSWORD` del `.env`. Si
   hace falta, cambiar el servidor y la base en los parámetros `Servidor` y `BaseDatos`
   (`localhost:5433` y `solarbi` por defecto).

7. Grafana: entrar a <http://localhost:3000>. El data source de PostgreSQL y el dashboard
   `grafana/dashboard.json` se cargan solos al levantar Docker Compose (provisioning), con el
   usuario y la contraseña del `.env`. Los datos de ejemplo están entre el 5 y el 7 de octubre de
   2026, así que hay que ajustar el rango de tiempo del dashboard a esas fechas.

## Usuarios y contraseñas

El repositorio no trae ninguna contraseña: cada persona las define en su archivo `.env`, que se crea
copiando `.env.example` y no se sube a GitHub.

| Variable del `.env` | Qué es | De dónde sale |
|---|---|---|
| `PGUSER` | Usuario de PostgreSQL | Lo elige quien instala; el ejemplo trae `solarbi` |
| `PGPASSWORD` | Contraseña de ese usuario | La inventa quien instala; no hay una por defecto |
| `PGDATABASE` | Nombre de la base | El ejemplo trae `solarbi` |
| `PGHOST` y `PGPORT` | Dónde corre PostgreSQL | `localhost` y `5433` (puerto del contenedor publicado en el equipo) |

Quién usa esos valores:

- **Docker Compose** crea el usuario y la base de PostgreSQL con ellos, la primera vez que arranca.
- **El ETL** (`etl/run_etl.py`) los lee con `python-dotenv` para conectarse.
- **Grafana** los recibe como variables de entorno y los usa en el data source provisionado.
- **Power BI** no lee el `.env`: hay que escribir `PGUSER` y `PGPASSWORD` a mano en el cuadro de
  credenciales de la pestaña "Base de datos".

PostgreSQL solo aplica el usuario y la contraseña cuando crea el volumen `pgdata` por primera vez. Si
después se cambia `PGPASSWORD` en el `.env`, la base seguirá con la contraseña anterior. Para
empezar de cero, `docker compose down -v` borra los volúmenes (incluidos los datos y los ajustes
de Grafana); luego `docker compose up -d` y `python etl/run_etl.py` los vuelven a crear.

Grafana OSS tiene su propio usuario, independiente de PostgreSQL: en una instalación nueva es `admin`
con contraseña `admin`, y Grafana pide cambiarla en el primer ingreso.

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
| Simulador, ETL con reglas de calidad y carga idempotente, esquemas SQL | Daniela Montoya Quintero |
| `docker-compose.yml`, dashboard de Grafana, README inicial y medidas DAX documentadas | Daniela Montoya Quintero |
| Proyecto de Power BI (`.pbip`) con modelo, medidas y página de resumen | Isaac Madera Jiménez |
| Respuestas de la Parte A y referencias, incluida la tarifa de EPM | Isaac Madera Jiménez |
| Capturas de evidencia, reflexión y PDF de la consulta | Isaac Madera Jiménez |
