# SIGAM — Sistema Integrado de Gestión y Análisis Municipal

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)](https://streamlit.io)
[![Firebase](https://img.shields.io/badge/Auth-Firebase-orange)](https://firebase.google.com)
[![Cloud Run](https://img.shields.io/badge/Deploy-Google_Cloud_Run-blue)](https://cloud.google.com/run)

Plataforma web para la digitalización y automatización del **Índice de Gestión de Servicios Municipales (IGSM)** de la Contraloría General de la República de Costa Rica.

🌐 **App en producción:** https://sigam-669552465701.us-central1.run.app
-  **Referencia técnica (Sphinx):** https://estebansabo07.github.io/SIGAM_Grupo2_Entrega_Final/

---

## Información académica

| Campo | Detalle |
|-------|---------|
| **Curso** | BBCD0001 – Análisis de Datos |
| **Profesor** | Dagoberto José Herrera Murillo |
| **Institución** | LEAD University |
| **Equipo** | Esteban Gutiérrez Saborío · Jason Corrau Madrigal · Robson Sthiffen Calvo Ortega |
| **Período** | 2025 |

---

## Instalación y ejecución local

### Requisitos
- Python 3.11+
- pip

### Pasos

```bash
git clone https://github.com/EstebanSabo07/SIGAM_Grupo2_Entrega_Final.git
cd SIGAM_Grupo2_Entrega_Final
pip install -r requirements.txt
python -m database.init_db
python -m database.import_source_baseline
streamlit run main.py
```

La aplicación abre en `http://localhost:8501`

### Credenciales de acceso

| Rol | Acceso |
|-----|--------|
| Municipalidad | Seleccionar municipio en el dropdown + código `1234` |
| Contraloría | `admin1sigam@gmail.com` / `123456` |

---

## Funcionalidades

- ✅ Formulario IGSM digital con 159 indicadores (replicación exacta PT-228 CGR 2025)
- ✅ Cálculo automático del IGSM: `0.50×Plan + 0.30×Ejec + 0.20×Eval`
- ✅ 5 niveles de madurez: Inicial · Básico · Intermedio · Avanzado · Optimizando
- ✅ Ranking nacional de 84 municipalidades con datos reales (Heredia #1 · Puerto Jiménez #84)
- ✅ Validación de consistencia lógica de respuestas en tiempo real
- ✅ Detección de anomalías históricas (variación >15%)
- ✅ Dashboard nacional con KPIs, distribución por nivel y heatmap región × servicio
- ✅ Análisis por municipalidad con comparación, radar por servicio e historial
- ✅ Análisis geoespacial (mapa interactivo de Costa Rica)
- ✅ Análisis de clústeres (K-Means + PCA)
- ✅ Correlaciones por servicio y modelo SEM
- ✅ Exportación Excel multi-hoja (nacional e individual por municipalidad)
- ✅ Simulador de pesos del índice
- ✅ Autenticación Firebase para panel de Contraloría
- ✅ Desplegado en Google Cloud Run

---

## Despliegue en Google Cloud Run

```bash
gcloud run deploy sigam \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --port 8080
```

El `entrypoint.sh` inicializa automáticamente la base de datos desde los CSV fuente al arrancar.

---

## Licencia

Proyecto académico — LEAD University / CGR Costa Rica · 2025
