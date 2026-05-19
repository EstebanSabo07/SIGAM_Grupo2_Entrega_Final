# SIGAM — Sistema Integrado de Gestión y Análisis Municipal

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Cloud_Run-blue)](https://cloud.google.com/run)

Plataforma web para la digitalización y automatización del **Índice de Gestión de Servicios Municipales (IGSM)** de la Contraloría General de la República de Costa Rica.

---

##  Información académica

| Campo | Detalle |
|-------|---------|
| **Curso** | BBCD0001 – Análisis de Datos |
| **Profesor** | Dagoberto José Herrera Murillo |
| **Institución** | LEAD University |
| **Equipo** | Esteban Gutiérrez Saborío · Jason Corrau Madrigal · Robson Sthiffen Calvo Ortega |
| **Período** | 2025 |

---

##  Instalación y ejecución local

### Requisitos
- Python 3.11+
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/EstebanSabo07/Proyecto-An-lisis-de-datos---Grupo-2-.git
cd Proyecto-An-lisis-de-datos---Grupo-2-

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Inicializar la base de datos local (SQLite)
python -m database.init_db
python -m database.import_source_baseline --period 2025

# 4. Ejecutar
streamlit run main.py
```

La aplicación abre en `http://localhost:8501`

### Nota sobre el PDF formal

La exportación PDF pública y municipal usa `reportlab` y depende del **mismo intérprete de Python que ejecuta Streamlit**. Para evitar que salga un PDF degradado o inválido:

```bash
# Recomendado: usar el mismo Python para instalar dependencias y arrancar Streamlit
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

Si en su equipo `streamlit` apunta a otro entorno distinto, verifique primero qué ejecutable está usando y luego instale `reportlab` en ese mismo entorno.

```bash
where streamlit
python -c "import sys, reportlab; print(sys.executable); print(reportlab.__version__)"
```

En esta máquina, el launcher detectado de Streamlit apunta al runtime de Microsoft Store. Si mantiene ese launcher, instale el backend PDF formal allí:

```bash
"C:\Users\Jason\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\pip.exe" install reportlab
```

### Accesos de demo

| Rol | Acceso |
|-----|--------|
| Ciudadanía | `http://localhost:8501` |
| Municipalidad | `http://localhost:8501/?portal=municipal` |
| Contraloría | `http://localhost:8501/?portal=admin` |

---

##  Estructura del proyecto

```
SIGAM/
├── main.py                  ← Punto de entrada y enrutador
├── requirements.txt
├── Dockerfile               ← Google Cloud Run
├── assets/
│   ├── style.css
│   ├── logo_cgr.svg
│   └── logo_lead.png
├── data/
│   ├── municipalities.py    ← 84 municipalidades con coordenadas
│   ├── indicators.py        ← Metadatos de transición y clasificación de niveles
│   ├── calculation.py       ← Fórmula oficial CGR
│   ├── snapshot.py          ← Contexto Mes-Año y audiencias
│   ├── catalog_service.py   ← Árbol Eje → Servicio → Etapa desde ORM
│   ├── response_service.py  ← Lectura y guardado versionado por sección
│   ├── scoring_service.py   ← Cálculo de snapshots y estados operativos
│   ├── presentation_service.py ← View-models por audiencia
│   └── reporting_service.py ← Exportaciones CSV/PDF por snapshot
├── database/                ← ORM SQLAlchemy (dimensional + hechos)
│   ├── models.py            ← Tablas: dm_municipality, dm_indicator, fact_*
│   ├── repositories.py      ← API de persistencia y consulta
│   ├── session.py           ← Engine y session_scope
│   ├── config.py            ← DATABASE_URL (SQLite local / PostgreSQL prod)
│   ├── init_db.py           ← Creación de esquema y datos de referencia
│   ├── import_source_baseline.py ← Carga de resultados CGR 2025
│   ├── seed.py              ← Siembra de pesos y umbrales
│   ├── data_model.sql       ← Documentación del esquema dimensional
│   └── source/
│       ├── dictionary.csv              ← Catálogo de indicadores
│       └── igsm_2025_results_long.csv  ← 8 840 respuestas reales CGR 2025
├── components/
│   ├── ui.py                ← Componentes reutilizables
│   └── charts.py            ← Visualizaciones Plotly
└── views/
    ├── landing.py           ← Dashboard ciudadano público
    ├── login.py             ← Acceso privado oculto
    ├── muni_home.py         ← Portal municipalidad
    ├── muni_form.py         ← Formulario navegable con guardado explícito
    ├── muni_results.py      ← Resultados municipales sin puntajes sensibles
    ├── admin_dashboard.py   ← Dashboard Contraloría (datos reales)
    ├── admin_municipalities.py
    ├── admin_analysis.py    ← Geo · Clústeres · SEM · Correlación
    ├── admin_weights.py     ← Gestión de pesos (persiste en BD)
    └── admin_export.py      ← Exportación y publicación
```

---

##  Base de datos

La capa de datos usa **SQLAlchemy ORM** con un modelo dimensional:

| Tabla | Descripción |
|-------|-------------|
| `dm_municipality` | 84 municipalidades con provincia, región y coordenadas |
| `dm_axis` | 4 ejes de gestión IGSM |
| `dm_service` | 10 servicios municipales |
| `dm_stage` | 3 etapas: Planificación, Ejecución, Evaluación |
| `dm_indicator` | 159 indicadores oficiales (PT-228 CGR) |
| `fact_indicator_response` | Respuestas por municipalidad e indicador con timestamp |
| `fact_indicator_evidence` | Evidencias asociadas a cada versión de respuesta |
| `fact_stage_weight` | Pesos de etapa con fecha de vigencia |
| `fact_maturity_threshold` | Umbrales de madurez con fecha de vigencia |
| `fact_service_review_status` | Estados de revisión/observación por servicio |

**Desarrollo local:** SQLite en `database/igsm_dev.sqlite3`  
**Producción:** PostgreSQL via variable de entorno `DATABASE_URL`

```bash
# Usar PostgreSQL
export DATABASE_URL="postgresql+psycopg://user:password@host:5432/dbname"
python -m database.init_db
python -m database.import_source_baseline --period 2025
```

Los datos del baseline incluyen **8 840 respuestas reales** del informe CGR 2025 (84 municipalidades × 159 indicadores menos municipalidades con servicios diversificados no aplicables).

---

##  Funcionalidades principales

- ✅ Snapshot mensual con filtro `Mes-Año` y última respuesta vigente al cierre del mes
- ✅ Dashboard ciudadano público sin login
- ✅ Accesos privados ocultos para municipalidades y Contraloría
- ✅ Formulario navegable por `Eje → Servicio → Etapa`
- ✅ Guardado explícito por sección, sin autoguardado
- ✅ Historial de respuestas versionado por indicador
- ✅ Estados operativos por servicio
- ✅ Confidencialidad de puntajes para ciudadanía y municipalidades
- ✅ Exportación CSV/PDF por audiencia
- ✅ Simulador de pesos del índice (persiste en BD)

---

##  Despliegue en Google Cloud Run

```bash
# Build y deploy
gcloud run deploy sigam \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars DATABASE_URL="postgresql+psycopg://user:password@host:5432/dbname"
```

---

##  Integración futura

| Componente | Tecnología | Estado |
|------------|-----------|--------|
| Autenticación | Firebase Authentication / Auth0 | 🔜 Pendiente |
| Base de datos en nube | Cloud SQL (PostgreSQL) | 🔜 Pendiente |
| Analítica avanzada | BigQuery | 🔜 Pendiente |
| Archivos y evidencias | Cloud Storage | 🔜 Pendiente |
| Integración CGR | Envío digital de informes | 🔜 Pendiente |

---

## 📄 Licencia

Proyecto académico — LEAD University / CGR Costa Rica · 2025
