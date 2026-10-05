# Power BI · conexión y medidas DAX

## Conexión (Obtener datos → Base de datos PostgreSQL)

- Servidor: `localhost:5433`
- Base de datos: `solarbi`
- Modo de conectividad: **Import**
- Credenciales: usuario `solarbi` y la contraseña del archivo `.env` (pestaña "Base de datos")
- Tablas a importar: `dwh.fact_energia_dia`, `dwh.dim_dispositivo` y, opcionalmente, `silver.lectura_5min`

Relación: `fact_energia_dia[dispositivo_key]` (muchos) → `dim_dispositivo[dispositivo_key]` (uno).

## Parámetro de tarifa

Modelado → Nuevo parámetro → Intervalo numérico, nombre `Tarifa`. Ajustar mínimo, máximo e
incremento y dejar como valor inicial la tarifa de energía en COP/kWh que consulten. Power BI crea
la tabla `Tarifa` y la medida `Tarifa Valor`.

**La tarifa debe tener fuente citada en el PDF** (por ejemplo, la tarifa publicada por el
comercializador de energía de la zona, con fecha de consulta). No usar un valor sin referencia.

## Medidas

```DAX
Energía kWh = SUM ( fact_energia_dia[energia_kwh] )

Potencia instalada kWp = SUM ( dim_dispositivo[potencia_kwp] )

Yield kWh/kWp = DIVIDE ( [Energía kWh], [Potencia instalada kWp] )

Ahorro COP = [Energía kWh] * [Tarifa Valor]

% Datos válidos =
DIVIDE (
    SUM ( fact_energia_dia[lecturas_validas] ),
    SUM ( fact_energia_dia[lecturas_leidas] )
)
```

## Visuales de la página

| Visual | Campo |
|---|---|
| Tarjeta | `Yield kWh/kWp` |
| Gráfico de columnas | Eje: `fact_energia_dia[fecha]`; valores: `Energía kWh` |
| Tarjeta | `Ahorro COP` (formato moneda, sin decimales) |
| Control deslizante | Parámetro `Tarifa` |
| Tarjeta (opcional) | `% Datos válidos` |

Valores de referencia con los datos actuales (3 días, 5 kWp): energía 80,055 kWh, yield 16,01
kWh/kWp, % válidos 94,12 %. Si Power BI muestra otra cosa, hay que revisar la relación.

## Guardado

Guardar como proyecto Power BI (`.pbip`) dentro de esta carpeta: Archivo → Guardar como → tipo
"Power BI Project". Requiere activar la vista previa en Opciones → Características de vista previa
→ "Guardar con formato de proyecto de Power BI (.pbip)". No se debe guardar la contraseña dentro
del archivo.
