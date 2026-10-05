"""ETL de SolarBI: Bronze (CSV crudo) -> Silver (lecturas limpias) -> Gold (resumen diario).

Uso:
    python etl/run_etl.py              flujo completo con carga en PostgreSQL
    python etl/run_etl.py --sin-carga  solo calidad y archivos de Silver (no necesita base de datos)
"""
import os
import sys
from pathlib import Path

import pandas as pd

import simulador

RAIZ = Path(__file__).resolve().parent.parent
BRONZE = simulador.BRONZE
SILVER = RAIZ / "data" / "silver" / "lectura_5min.csv"
REPORTE = RAIZ / "data" / "silver" / "reporte_calidad.csv"
ESQUEMA = RAIZ / "sql" / "01_esquema.sql"

COLUMNAS = ["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]
POTENCIA_KWP = 5.0
HORAS_INTERVALO = 5 / 60                       # cada lectura representa 5 minutos

# Rangos fisicos validos (regla 3)
P_AC_MAX = POTENCIA_KWP * 1.1                  # el inversor no entrega mas de ~110 % de su potencia
IRRADIANCIA_MAX = 1400                         # W/m2, por encima de la constante solar no es creible
TEMP_MIN, TEMP_MAX = -10, 90                   # grados C en el modulo


def leer_bronze():
    if not BRONZE.exists():                    # Bronze solo se genera si no existe; nunca se reescribe
        simulador.generar()
    df = pd.read_csv(BRONZE)
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    return df


def aplicar_calidad(bronze):
    """Marca cada fila con la primera regla que incumple, o 'valida'."""
    df = bronze.copy()
    df["estado"] = "valida"

    duplicado = df.duplicated(subset=["ts", "dispositivo_id"], keep="first")
    df.loc[duplicado, "estado"] = "duplicado"

    faltante = df[COLUMNAS].isna().any(axis=1) & (df["estado"] == "valida")
    df.loc[faltante, "estado"] = "faltante"

    en_rango = (
        df["p_ac_kw"].between(0, P_AC_MAX)
        & df["irradiancia_wm2"].between(0, IRRADIANCIA_MAX)
        & df["temp_modulo_c"].between(TEMP_MIN, TEMP_MAX)
    )
    df.loc[~en_rango & (df["estado"] == "valida"), "estado"] = "fuera_de_rango"
    return df


def reporte_calidad(marcado):
    leidas = len(marcado)
    conteo = marcado["estado"].value_counts()
    validas = int(conteo.get("valida", 0))
    filas = [
        ("filas_leidas", leidas),
        ("rechazadas_duplicado", int(conteo.get("duplicado", 0))),
        ("rechazadas_faltante", int(conteo.get("faltante", 0))),
        ("rechazadas_fuera_de_rango", int(conteo.get("fuera_de_rango", 0))),
        ("filas_validas", validas),
        ("pct_datos_validos", round(100 * validas / leidas, 2)),
    ]
    return pd.DataFrame(filas, columns=["metrica", "valor"])


def resumen_diario(marcado):
    df = marcado.dropna(subset=["ts"]).copy()
    df["fecha"] = df["ts"].dt.date
    df["es_valida"] = df["estado"] == "valida"
    df["energia_kwh"] = (df["p_ac_kw"] * HORAS_INTERVALO).where(df["es_valida"], 0.0)

    dia = df.groupby(["fecha", "dispositivo_id"], as_index=False).agg(
        energia_kwh=("energia_kwh", "sum"),
        lecturas_leidas=("es_valida", "size"),
        lecturas_validas=("es_valida", "sum"),
    )
    dia["energia_kwh"] = dia["energia_kwh"].round(3)
    dia["pct_datos_validos"] = (100 * dia["lecturas_validas"] / dia["lecturas_leidas"]).round(2)
    dia["fecha_key"] = dia["fecha"].map(lambda f: int(f.strftime("%Y%m%d")))
    return dia.rename(columns={"dispositivo_id": "dispositivo_key"})[
        ["fecha_key", "dispositivo_key", "fecha", "energia_kwh",
         "lecturas_leidas", "lecturas_validas", "pct_datos_validos"]
    ]


def filas(df):
    """Convierte el DataFrame a listas con tipos nativos de Python para psycopg2."""
    return df.astype(object).values.tolist()


def cargar(silver, dia):
    import psycopg2
    from dotenv import load_dotenv
    from psycopg2.extras import execute_values

    load_dotenv(RAIZ / ".env")
    con = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "solarbi"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )
    dispositivos = [(int(d), f"Inversor {int(d)}", POTENCIA_KWP)
                    for d in sorted(silver["dispositivo_id"].unique())]

    # Todo va en una transaccion. Los UPSERT sobre la clave primaria hacen la carga idempotente.
    with con, con.cursor() as cur:
        cur.execute(ESQUEMA.read_text(encoding="utf-8"))
        execute_values(cur, """
            INSERT INTO dwh.dim_dispositivo (dispositivo_key, nombre, potencia_kwp) VALUES %s
            ON CONFLICT (dispositivo_key) DO UPDATE SET
                nombre = EXCLUDED.nombre, potencia_kwp = EXCLUDED.potencia_kwp
        """, dispositivos)
        execute_values(cur, """
            INSERT INTO silver.lectura_5min
                (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c) VALUES %s
            ON CONFLICT (ts, dispositivo_id) DO UPDATE SET
                p_ac_kw = EXCLUDED.p_ac_kw,
                irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
                temp_modulo_c = EXCLUDED.temp_modulo_c
        """, filas(silver[COLUMNAS]))
        execute_values(cur, """
            INSERT INTO dwh.fact_energia_dia
                (fecha_key, dispositivo_key, fecha, energia_kwh,
                 lecturas_leidas, lecturas_validas, pct_datos_validos) VALUES %s
            ON CONFLICT (fecha_key, dispositivo_key) DO UPDATE SET
                fecha = EXCLUDED.fecha,
                energia_kwh = EXCLUDED.energia_kwh,
                lecturas_leidas = EXCLUDED.lecturas_leidas,
                lecturas_validas = EXCLUDED.lecturas_validas,
                pct_datos_validos = EXCLUDED.pct_datos_validos
        """, filas(dia))

        print("\nConteos en PostgreSQL despues de la carga:")
        for tabla in ("silver.lectura_5min", "dwh.dim_dispositivo", "dwh.fact_energia_dia"):
            cur.execute(f"SELECT count(*) FROM {tabla}")
            print(f"  {tabla:<24}{cur.fetchone()[0]:>6}")
    con.close()


def main():
    bronze = leer_bronze()
    marcado = aplicar_calidad(bronze)
    reporte = reporte_calidad(marcado)
    silver = marcado.loc[marcado["estado"] == "valida", COLUMNAS]
    dia = resumen_diario(marcado)

    SILVER.parent.mkdir(parents=True, exist_ok=True)
    silver.to_csv(SILVER, index=False)
    reporte.to_csv(REPORTE, index=False)

    print("Reporte de calidad (Bronze -> Silver):")
    for metrica, valor in reporte.itertuples(index=False):
        print(f"  {metrica:<28}{valor:>8g}")
    print("\nResumen diario (Gold):")
    print(dia.to_string(index=False))

    if "--sin-carga" not in sys.argv:
        cargar(silver, dia)


if __name__ == "__main__":
    main()
