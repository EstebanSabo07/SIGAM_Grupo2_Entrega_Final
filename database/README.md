# Capa de Datos ORM del IGSM

Este paquete contiene la capa de datos SQLAlchemy para la aplicacion Streamlit SIGAM / IGSM. El ORM almacena directamente el modelo de negocio: municipalidades, ejes, servicios, etapas, indicadores, respuestas de indicadores, pesos de etapa y umbrales de madurez.

El desarrollo local usa SQLite de forma predeterminada. Para despliegues en la nube o produccion, configure `DATABASE_URL` con una cadena de conexion PostgreSQL.

## Inicio rapido

Instale primero las dependencias del proyecto:

```powershell
python -m pip install -r requirements.txt
```

Cree la base de datos local de desarrollo:

```powershell
# Base SQLite local en database/igsm_dev.sqlite3
python -m database.init_db
```

Este comando crea el esquema ORM y carga datos de referencia como municipalidades, ejes, servicios, etapas, indicadores, pesos de etapa y umbrales de madurez.

Para PostgreSQL u otra base de datos en la nube, defina `DATABASE_URL` antes de ejecutar el mismo inicializador:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@host:5432/dbname"
python -m database.init_db
```

## Importacion del baseline fuente

Las filas oficiales del baseline se cargan desde `database/source/dictionary.csv` y `database/source/igsm_2025_results_long.csv`.

Valide los CSV y los conteos esperados sin escribir en la base de datos:

```powershell
python -m database.import_source_baseline --dry-run
```

Cargue los datos del baseline en la base configurada:

```powershell
python -m database.import_source_baseline --period 2025
```

El importador crea filas en `fact_indicator_response` solo para respuestas numericas. De forma predeterminada, al ejecutar la importacion de nuevo se reemplazan los hechos del baseline anterior para la misma marca temporal, por lo que el proceso es idempotente y no duplica respuestas.

Para conservar intactos los hechos existentes del baseline, use:

```powershell
python -m database.import_source_baseline --period 2025 --skip-existing
```

Con PostgreSQL o una base en la nube, ejecute el mismo comando despues de definir `DATABASE_URL`:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@host:5432/dbname"
python -m database.import_source_baseline --period 2025
```

Ejecute `python -m database.init_db` antes de importar el baseline para asegurar que los pesos y umbrales de referencia esten presentes.

## Higiene del repositorio

No se deben confirmar archivos de base de datos generados, como `database/igsm_dev.sqlite3`, `*.sqlite`, `*.sqlite3` o `*.db`. La base debe poder reproducirse desde el codigo ORM, los helpers de siembra y los CSV fuente. Esto evita binarios obsoletos, conflictos de merge y datos locales o de prueba dentro de Git.

## Modelo de datos

El esquema en `database/data_model.sql` documenta el modelo dimensional y de hechos. El ORM conserva esos nombres de tablas y columnas.

### Tablas

- `dm_municipality`: una fila por municipalidad. Guarda codigo municipal, nombre, provincia, region, latitud y longitud.
- `dm_axis`: eje de gestion IGSM. El modelo actual tiene 3 ejes.
- `dm_service`: definiciones de servicios bajo cada eje. El baseline actual tiene 10 servicios.
- `dm_municipality_diversified_service`: servicios diversificados aplicables por municipalidad. La llave primaria combina `municipality_id` y `service_id`.
- `dm_stage`: etapas globales IGSM. El modelo actual tiene 3 filas: `Planificación`, `Ejecución` y `Evaluación`.
- `dm_indicator`: definiciones de indicadores. Cada indicador apunta a un servicio y una etapa global.
- `fact_indicator_response`: respuestas numericas de indicadores. Cada fila representa municipalidad, indicador, valor y marca temporal de respuesta.
- `fact_stage_weight`: pesos de etapa con fecha de vigencia para `Planificación`, `Ejecución` y `Evaluación`.
- `fact_maturity_threshold`: umbrales de madurez con fecha de vigencia para `Inicial`, `Básico`, `Intermedio`, `Avanzado` y `Optimizando`.

## Compatibilidad con proveedor de identidad

El ORM no implementa inicio de sesion, sesiones de usuario, contrasenas, hashes de credenciales, refresh tokens ni codigos de acceso municipal. Es compatible con un proveedor de identidad externo, como SSO institucional, Google/IAM, Auth0, Firebase Auth, Azure AD o cualquier proveedor OIDC/OAuth2, o con un proveedor interno implementado en la capa de aplicacion.

Los consumidores deben autenticar a los usuarios antes de llamar funciones del repositorio y pasar solo el contexto de municipalidad o rol que necesite la aplicacion. La capa de base de datos se mantiene enfocada en los datos de negocio del IGSM.

## API publica del repositorio

El modulo `database.repositories` expone funciones enfocadas en persistir y suministrar datos ORM. Los calculos de
score, nivel, ranking, promedios o detalle metodologico IGSM deben hacerse fuera del ORM, usando `data.calculation`.

- Busquedas de municipalidades y referencias: `list_municipalities`, `get_municipality_by_code`, `get_municipality_by_name`, `get_municipality_names`, `list_municipalities_by_region`.
- Metadatos IGSM: `get_services_for_municipality`, `get_indicators_for_service`.
- Pesos y umbrales: `get_latest_stage_weights`, `get_latest_maturity_thresholds`, `get_current_stage_weights`, `save_stage_weights`, `get_current_maturity_thresholds`.
- Respuestas: `submit_indicator_responses`, `get_latest_responses_for_municipality`, `get_latest_indicator_responses`.
- Completitud de datos: `get_national_statistics`, `get_municipality_completion_statistics`.

Las consultas de respuestas y completitud reciben `end_date` como fecha de corte inclusiva. La capa ORM responde con los
datos mas recientes a esa fecha, no con agregados por anno calendario. `get_national_statistics` y
`get_municipality_completion_statistics` miden completitud de respuestas a esa fecha.
La completitud cuenta pares unicos municipalidad-indicador; si una municipalidad envia multiples respuestas para el
mismo indicador antes de la fecha de corte, eso cuenta como una sola respuesta recibida.

## Configuracion

Defina `DATABASE_URL` para cambiar de base de datos:

- SQLite local predeterminada: `sqlite:///database/igsm_dev.sqlite3`
- PostgreSQL: `postgresql+psycopg://user:password@host:5432/dbname`

Los mismos modelos ORM funcionan para desarrollo con SQLite y produccion en PostgreSQL o nube.
