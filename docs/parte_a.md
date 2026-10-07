# Parte A · Consulta

## Bloque 1 · Power BI y Grafana

### D1. ¿Qué es Grafana?

Grafana es una plataforma de visualización y monitoreo que consulta los datos donde están, sin copiarlos [1].
Sus componentes: los *data sources* conectan con la fuente (en SolarBI, PostgreSQL); un *panel* dibuja el
resultado de una consulta; un *dashboard* agrupa paneles y se guarda como JSON; las *variables* parametrizan
las consultas; el *alerting* evalúa reglas cada cierto tiempo y avisa por canales como correo o Slack [1].
Grafana OSS es gratuito, de código abierto y se instala y mantiene en servidor propio, como hace nuestro
`docker-compose.yml`. Grafana Cloud es el mismo producto alojado y operado por Grafana Labs, con plan gratuito
limitado y planes de pago [2].

### D2. Power BI vs. Grafana

| Criterio | Power BI | Grafana |
|---|---|---|
| Propósito principal | Inteligencia de negocios y análisis de indicadores [3] | Monitoreo y observabilidad de sistemas y equipos [1] |
| Usuario típico | Analista de negocio y directivo | Operador, ingeniero de planta o de operaciones |
| Conexión a los datos | Conectores; Import, DirectQuery o conexión en vivo [4] | *Data sources* que consultan en cada carga del panel [1] |
| Modelo semántico y lenguaje | Modelo con tablas, relaciones y medidas en DAX | Sin modelo propio: cada panel lleva su consulta (SQL, PromQL, etc.) |
| Actualización y tiempo real | Actualización programada con Import; DirectQuery casi en vivo [4] | Auto-refresh de segundos a minutos; pensado para datos recientes [1] |
| Alertas | Alertas de datos sobre tarjetas y medidores en el servicio [3] | Reglas de alerta nativas con puntos de contacto [1] |
| Licenciamiento y costo | Desktop gratuito; compartir en el servicio exige licencia de pago [3] | OSS gratuito (AGPL); Cloud y Enterprise de pago [2] |
| Control de acceso | Áreas de trabajo, roles y seguridad a nivel de fila (RLS) con Microsoft Entra ID [3] | Roles por organización (Viewer, Editor, Admin) y permisos por carpeta; RBAC avanzado en Enterprise y Cloud [1] |
| Despliegue | Desktop para autoría y servicio SaaS de Microsoft | Autoalojado (Docker, instalador) o Cloud |
| Versionado | `.pbix` binario o proyecto `.pbip` [5] | JSON exportable o provisioning por archivos [1] |

### D3. Dashboard operativo, analítico y estratégico

El operativo sigue el estado actual para actuar en minutos (operador); el analítico explora tendencias y causas
con filtros y periodos largos (analista); el estratégico resume pocos indicadores frente a metas para decidir
(directivo) [6].

| KPI | Tipo | Herramienta y motivo |
|---|---|---|
| Energía | Analítico | Power BI: se compara por día y periodo |
| Yield y Performance Ratio | Analítico | Power BI: medidas DAX sobre un modelo; el PR se normaliza con irradiación [7] |
| Ahorro (COP) | Estratégico | Power BI: usa tarifa parametrizable para el directivo |
| Disponibilidad y alarmas | Operativo | Grafana: alertas y datos recientes |
| % de datos válidos | Operativo y analítico | Grafana (panel *stat* con umbrales); Power BI para su tendencia |

### D4. Import, DirectQuery y actualización programada

*Import* copia los datos al modelo de Power BI y responde rápido; solo cambia cuando se actualiza. *DirectQuery*
no guarda datos: envía una consulta a la fuente en cada interacción, así que depende de su velocidad [4]. La
actualización programada (*scheduled refresh*) vuelve a importar en horas definidas, con un máximo diario según
la licencia [8]. En SolarBI usaríamos Import: la tabla diaria es pequeña, el ETL corre una vez al día y el
refresh puede lanzarse justo después. El auto-refresh de Grafana es distinto: el navegador repite las consultas
contra la base cada pocos segundos o minutos y no almacena nada [1].

### D5. Variables de Grafana frente a segmentadores de Power BI

Una variable de Grafana es un valor que se sustituye dentro del texto de la consulta antes de enviarla a la
base [9]. Un segmentador de Power BI no reescribe consultas: agrega un filtro que se propaga por las relaciones
del modelo y cambia el contexto de evaluación de las medidas DAX [3]. Para SolarBI, la variable `dispositivo`
se define así y se usa en los paneles:

```sql
SELECT dispositivo_key AS __value, nombre AS __text FROM dwh.dim_dispositivo ORDER BY 1
```

```sql
SELECT ts AS time, p_ac_kw FROM silver.lectura_5min
WHERE $__timeFilter(ts) AND dispositivo_id IN ($dispositivo) ORDER BY ts
```

Al elegir el dispositivo 1, Grafana envía `dispositivo_id IN (1)`; con varios, `IN (1,2)`.

## Bloque 2 · Gobernanza de datos

### G1. Data governance, data management y data quality

Para DAMA-DMBOK, la gobernanza de datos es el ejercicio de autoridad y control, con decisiones compartidas, sobre
la gestión de los activos de datos [10]. La *gestión de datos* (data management) es el conjunto de disciplinas que
planifica y ejecuta esa gestión: arquitectura, almacenamiento, integración, seguridad. La *calidad de datos* es una
de esas disciplinas y mide si el dato sirve para su uso [10]. En SolarBI: la gobernanza decide que una potencia
válida está entre 0 y 5,5 kW; la gestión implementa el ETL; la calidad reporta el 94,12 % de datos válidos.

### G2. Data owner, data steward y data custodian

El *data owner* responde por un dato ante la organización: decide su definición, uso y acceso. El *data steward*
lo administra a diario: mantiene definiciones, vigila su calidad y resuelve dudas. El *data custodian* lo resguarda
técnicamente: almacenamiento, respaldos, permisos y seguridad [10]. Propuesta para el equipo (es una asignación
nuestra, no una norma): el *product owner* es *owner* de los datos y KPIs; el *BI analyst* y el *data modeler* son
*stewards* (catálogo de KPIs y modelo estrella); el *data engineer* es *custodian* de PostgreSQL y del ETL.

### G3. Contrato de datos

Un *data contract* es un acuerdo escrito entre quien produce y quien consume los datos. Debe incluir: esquema
(columnas y tipos), unidades (kW, W/m², °C), frecuencia (5 minutos), zona horaria, responsable, niveles de calidad
(rangos y % mínimo de válidos) y una regla para avisar los cambios. Si la fuente cambia un campo sin avisar, el
tablero falla sin ruido. Ejemplo: si `p_ac_kw` pasara de kW a W, todas las lecturas superarían 5,5 y la regla de
rango las rechazaría; el % de datos válidos caería a casi 0 y el yield saldría vacío.

### G4. Fuente única de verdad y catálogo de KPIs

Una *single source of truth* es un único lugar autorizado donde vive cada dato o cálculo; los demás lo consumen sin
reescribirlo. El *catálogo de KPIs* es el registro donde se define cada indicador para que todos lo entiendan igual
[10].

| Campo | Yield | % de datos válidos |
|---|---|---|
| Fórmula | energía kWh ÷ potencia instalada kWp | lecturas válidas ÷ lecturas leídas × 100 |
| Unidad | kWh/kWp | % |
| Fuente | `dwh.fact_energia_dia` y `dwh.dim_dispositivo` | `dwh.fact_energia_dia` |
| Responsable | BI analyst (steward) | Data engineer (custodian) |
| Frecuencia | Diaria | Cada ejecución del ETL |

Si un KPI se calcula en DAX y en SQL por separado, las fórmulas pueden divergir (por ejemplo, promedio de
porcentajes frente a razón de sumas) y las dos herramientas mostrarían cifras distintas para el mismo indicador.

### G5. Ley 1581 de 2012

La ley define dato personal como cualquier información vinculada o que pueda asociarse a una o varias personas
naturales determinadas o determinables [11]. La telemetría de un inversor (potencia, irradiancia, temperatura) no
describe a una persona, así que no es personal. Si el tablero mostrara qué operador atendió cada alarma, sí lo
sería: identificaría a alguien y evaluaría su trabajo. Exigiría finalidad clara, autorización del titular, acceso
restringido y seguridad [11]. Postura del equipo: usar solo datos del equipo, no recolectar datos de personas sin
necesidad, y no subir credenciales al repositorio (`.env` excluido).

## Bloque 3 · Automatización de procesos ETL

### E1. ETL frente a ELT y capas Bronze, Silver y Gold

En ETL los datos se transforman antes de cargarse al destino; en ELT se cargan primero y se transforman dentro del
destino aprovechando su capacidad [12]. En SolarBI: la **extracción** deja `telemetria.csv` en Bronze sin
modificarlo; la **transformación** aplica las reglas de calidad y carga Silver (`silver.lectura_5min`); la
agregación diaria llena Gold (`dwh.fact_energia_dia`). Como pandas transforma antes de cargar, el flujo es ETL.
Power Query también extrae, transforma y carga al modelo, así que sí es una herramienta ETL, pero limitada al
modelo de Power BI: no orquesta ni gobierna capas externas.

### E2. Carga completa, incremental e idempotencia

La carga completa reemplaza todo el destino en cada corrida; la incremental procesa solo lo nuevo o modificado
[12]. Una carga es idempotente si ejecutarla una o varias veces deja el mismo resultado. En `fact_energia_dia` se
logra con la clave primaria `(fecha_key, dispositivo_key)` y un UPSERT [13]:

```sql
INSERT INTO dwh.fact_energia_dia (...) VALUES (...)
ON CONFLICT (fecha_key, dispositivo_key) DO UPDATE SET energia_kwh = EXCLUDED.energia_kwh, ...;
```

Si la fila existe se actualiza; si no, se inserta. Por eso, tras dos corridas, la tabla sigue con 3 filas.

### E3. Tres formas de automatizar un flujo

| | cron / Programador de tareas | Apache Airflow | Actualización programada de Power BI |
|---|---|---|---|
| Qué es | Programador del sistema operativo que lanza comandos a una hora [14] | Plataforma para definir, programar y monitorear flujos como DAGs de tareas en Python [15] | Función del servicio que vuelve a importar los datos al modelo [8] |
| Qué automatiza | Cualquier comando, por ejemplo `python etl/run_etl.py` | Un flujo completo con dependencias, reintentos y registro de ejecuciones | Solo la carga del modelo semántico, no el ETL |
| Cuándo conviene | Una tarea simple y periódica, como la de SolarBI | Varias tareas dependientes y necesidad de monitoreo | Mantener actualizados los informes ya publicados |

### E4. Actualización incremental en Power BI

Se crean dos parámetros de fecha reservados, `RangeStart` y `RangeEnd`, y se filtra la tabla con
`fecha >= RangeStart and fecha < RangeEnd`. Luego se define una política: cuánto histórico conservar y cuánto
reciente refrescar. Power BI divide la tabla en particiones y, en cada actualización, procesa solo las recientes
[16]. Vale la pena con tablas grandes e históricos largos. Con `fact_energia_dia` (3 filas) no aporta; sí podría
servir para `lectura_5min` cuando acumule meses de lecturas cada 5 minutos.

## Bloque 4 · Internet de las Cosas (IoT)

### I1. Arquitectura IoT por capas

Capas: **dispositivo** (inversor y sensores), **gateway o edge** (datalogger que lee los equipos y los reenvía),
**red y broker** (transporte, por ejemplo MQTT), **almacenamiento** (archivos y PostgreSQL) y **aplicación**
(Power BI y Grafana) [17]. En nuestra práctica el simulador reemplaza las tres primeras capas.

```
Inversor 5 kWp --> Gateway --> Broker MQTT --> [BRONZE] telemetria.csv (crudo)
                                                     |  reglas de calidad
                                                     v
                                               [SILVER] silver.lectura_5min --> Grafana (serie cada 5 min)
                                                     |  energía = p_ac_kw x 5/60
                                                     v
                                               [GOLD] dwh.fact_energia_dia --> Power BI (yield, ahorro)
```

### I2. MQTT

MQTT es un protocolo de mensajería *publish/subscribe*: los dispositivos publican en un *topic* y un *broker*
reparte cada mensaje a quienes se suscribieron, sin que se conozcan entre sí [18]. Los topics son jerárquicos,
separados por `/`. Hay tres niveles de QoS: 0, a lo sumo una vez; 1, al menos una vez (puede repetirse); 2,
exactamente una vez [18]. Jerarquía propuesta:

```
pascualbravo/solar/<sitio>/<dispositivo>/<variable>
pascualbravo/solar/bloque-a/inversor-1/p_ac_kw
pascualbravo/solar/bloque-a/inversor-1/irradiancia_wm2
```

Para telemetría usaríamos QoS 1; los posibles duplicados ya los absorbe la regla de duplicados (`ts` más
`dispositivo_id`).

### I3. Modbus, MQTT y OPC UA

| | Modbus (RTU/TCP) | MQTT | OPC UA |
|---|---|---|---|
| Modelo de comunicación | Cliente/servidor (maestro/esclavo) | Publish/subscribe con broker | Cliente/servidor y publish/subscribe [19] |
| Uso típico | Leer registros de inversores y medidores [20] | Enviar telemetría del gateway a la nube [18] | Integración industrial con modelo de información [19] |
| Formato de los datos | Registros numéricos de 16 bits | Carga libre (JSON, binario) | Nodos tipados con nombre, unidad y tipo [19] |
| Seguridad | Sin seguridad nativa; se protege la red | TLS y usuario/contraseña [18] | Cifrado, firma y certificados integrados [19] |

En inversores y medidores esperaríamos Modbus (RTU por RS-485 o TCP); MQTT, en el gateway hacia la nube.

### I4. Procesamiento por lotes y flujo continuo

En *batch* se procesan datos acumulados cada cierto tiempo; en *streaming*, cada dato al llegar [21]. Agregar la
telemetría de 5 minutos a un día **gana** menos volumen, consultas más rápidas y KPIs estables como energía y
yield. **Pierde** el detalle intradía: picos, nubosidad, fallas cortas y alarmas en tiempo real. Por eso Silver
conserva los 5 minutos. Grafana atiende mejor la granularidad de 5 minutos y la vigilancia reciente; Power BI,
la diaria y la analítica.

## Bloque 5 · Control de versiones

### V1. Git, GitHub y versionado de tableros

Git es un sistema de control de versiones distribuido que corre en el equipo; GitHub es una plataforma que aloja
repositorios remotos y añade colaboración [22]. Un *repository* guarda los archivos y su historial; un *commit*
es una instantánea con autor y mensaje; una *branch* es una línea paralela de trabajo; un *pull request* propone
fusionar una rama y permite revisarla [22]. Un `.pbix` es un archivo binario comprimido: Git no muestra qué
cambió ni puede fusionar versiones. El formato `.pbip` guarda el proyecto como carpeta de archivos de texto, con
diferencias legibles [5]. Un dashboard de Grafana se versiona exportando su JSON, como `grafana/dashboard.json`.

## Referencias

1. Grafana Labs. *Grafana documentation* (paneles, variables, alertas, fuentes de datos). https://grafana.com/docs/grafana/latest/
2. Grafana Labs. *Grafana Cloud* y *Grafana OSS*. https://grafana.com/products/cloud/ y https://grafana.com/oss/grafana/
3. Microsoft. *Power BI documentation*. https://learn.microsoft.com/power-bi/
4. Microsoft. *Dataset modes in the Power BI service* (Import y DirectQuery). https://learn.microsoft.com/power-bi/connect-data/service-dataset-modes-understand
5. Microsoft. *Power BI Desktop projects (PBIP)*. https://learn.microsoft.com/power-bi/developer/projects/projects-overview
6. Few, S. (2013). *Information Dashboard Design* (2.ª ed.). Analytics Press.
7. IEC 61724-1. *Photovoltaic system performance – Monitoring*. https://webstore.iec.ch/publication/33622
8. Microsoft. *Data refresh in Power BI*. https://learn.microsoft.com/power-bi/connect-data/refresh-data
9. Grafana Labs. *Variables*. https://grafana.com/docs/grafana/latest/dashboards/variables/
10. DAMA International. *DAMA-DMBOK: Data Management Body of Knowledge* (2.ª ed.). https://www.dama.org/cpages/body-of-knowledge
11. Congreso de Colombia. *Ley 1581 de 2012*, art. 3. https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981
12. Databricks. *Medallion architecture*. https://www.databricks.com/glossary/medallion-architecture
13. PostgreSQL. *INSERT … ON CONFLICT*. https://www.postgresql.org/docs/current/sql-insert.html
14. Microsoft. *Task Scheduler*. https://learn.microsoft.com/windows/win32/taskschd/task-scheduler-start-page
15. Apache Airflow. *Documentation*. https://airflow.apache.org/docs/
16. Microsoft. *Incremental refresh and real-time data for semantic models*. https://learn.microsoft.com/power-bi/connect-data/incremental-refresh-overview
17. Microsoft. *Azure IoT reference architecture*. https://learn.microsoft.com/azure/architecture/reference-architectures/iot
18. OASIS. *MQTT Version 5.0*. https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
19. OPC Foundation. *OPC Unified Architecture*. https://opcfoundation.org/about/opc-technologies/opc-ua/
20. Modbus Organization. *Modbus specifications*. https://modbus.org/specs.php
21. Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly.
22. Chacon, S. y Straub, B. *Pro Git*. https://git-scm.com/book
23. Empresas Públicas de Medellín E.S.P. (2026, 16 de septiembre). *Tarifas y Costo de Energía Eléctrica – Mercado Regulado, septiembre de 2026* [PDF]. https://www.epm.com.co/content/dam/epm/clientes-y-usuarios/energia/tarifas-energia/Tarifas%202026/9.PublicacionTarifasSeptiembre162026_ANT_OM.pdf (consultado el 6 de octubre de 2026). Tarifa usada en la Parte B (Power BI, medida `Ahorro COP`).
