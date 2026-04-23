# SIGAM — Sistema Integrado de Gestión y Análisis Municipal

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Cloud_Run-blue)](https://cloud.google.com/run)

Plataforma web para la digitalización y automatización del **Índice de Gestión de Servicios Municipales (IGSM)** de la Contraloría General de la República de Costa Rica.

---

## 📋 Información académica

| Campo | Detalle |
|-------|---------|
| **Curso** | BBCD0001 – Análisis de Datos |
| **Profesor** | Dagoberto José Herrera Murillo |
| **Institución** | LEAD University |
| **Equipo** | Esteban Gutiérrez Saborío · Jason Corrau Madrigal · Robson Sthiffen Calvo Ortega |
| **Período** | 2025 |

---

## 🚀 Instalación y ejecución local

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

### Credenciales de demo

| Rol | Acceso |
|-----|--------|
| Municipalidad | Seleccionar municipio + código `1234` |
| Contraloría | Usuario `contraloria` / contraseña `cgr2025` |

---

## 🏗️ Estructura del proyecto

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
│   ├── indicators.py        ← Estructura IGSM completa (159 indicadores PT-228)
│   ├── calculation.py       ← Fórmula oficial CGR
│   ├── db_layer.py          ← Capa de integración SIGAM ↔ base de datos ORM
│   └── mock_data.py         ← Datos simulados (histórico y tendencias)
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
    ├── landing.py           ← Página pública
    ├── login.py             ← Autenticación
    ├── muni_home.py         ← Portal municipalidad
    ├── muni_form.py         ← Formulario IGSM (guarda en BD)
    ├── muni_results.py      ← Resultados municipales (desde BD)
    ├── admin_dashboard.py   ← Dashboard Contraloría (datos reales)
    ├── admin_municipalities.py
    ├── admin_analysis.py    ← Geo · Clústeres · SEM · Correlación
    ├── admin_weights.py     ← Gestión de pesos (persiste en BD)
    └── admin_export.py      ← Exportación y publicación
```

---

## 🗄️ Base de datos

La capa de datos usa **SQLAlchemy ORM** con un modelo dimensional:

| Tabla | Descripción |
|-------|-------------|
| `dm_municipality` | 84 municipalidades con provincia, región y coordenadas |
| `dm_axis` | 4 ejes de gestión IGSM |
| `dm_service` | 10 servicios municipales |
| `dm_stage` | 3 etapas: Planificación, Ejecución, Evaluación |
| `dm_indicator` | 159 indicadores oficiales (PT-228 CGR) |
| `fact_indicator_response` | Respuestas por municipalidad e indicador con timestamp |
| `fact_stage_weight` | Pesos de etapa con fecha de vigencia |
| `fact_maturity_threshold` | Umbrales de madurez con fecha de vigencia |

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

## 📊 Funcionalidades principales

- ✅ Formulario IGSM digital con 159 indicadores (replicación exacta CGR 2025, PT-228)
- ✅ Cálculo automático del índice con fórmula oficial
- ✅ 5 niveles de madurez: Inicial · Básico · Intermedio · Avanzado · Optimizando
- ✅ Validación de consistencia en tiempo real
- ✅ Detección de anomalías históricas (>15% variación)
- ✅ Carga de evidencias por indicador
- ✅ Dashboard nacional con ranking de 84 municipalidades (datos reales 2025)
- ✅ Análisis geoespacial (mapa interactivo)
- ✅ Análisis de clústeres (K-Means + PCA)
- ✅ Modelo de Ecuaciones Estructurales (SEM)
- ✅ Análisis de correlaciones por servicio
- ✅ Exportación CSV y Excel multi-hoja
- ✅ Simulador de pesos del índice (persiste en BD)
- ✅ Historial de respuestas por municipalidad con corte por fecha

---

## 🐳 Despliegue en Google Cloud Run

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

## 🔮 Integración futura

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
