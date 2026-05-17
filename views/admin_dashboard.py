"""National dashboard view for the Contraloria portal."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.charts import distribucion_niveles_pie, evolucion_puntaje_region, ranking_bar_chart
from components.ui import kpi_card, month_year_selector, page_header
from data.presentation_service import get_national_snapshot_view
from data.snapshot import AUDIENCE_ADMIN


def show() -> None:
    """Render the national IGSM dashboard."""

    page_header(
        "Dashboard nacional",
        "Contraloría General de la República · consulta interna con puntajes, niveles y estado operativo por mes de corte.",
        "📊",
    )
    snapshot = month_year_selector(AUDIENCE_ADMIN, key_prefix="admin_dashboard_snapshot")
    national = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)
    rows = national["municipalities"]
    df = pd.DataFrame(
        [
            {
                "codigo": row["municipality"]["codigo"],
                "municipalidad": row["municipality"]["nombre"],
                "provincia": row["municipality"].get("provincia"),
                "region": row["municipality"].get("region"),
                "score_total": row["score_total"],
                "puntaje_pct": row["puntaje_pct"],
                "nivel": row["level"],
                "posicion": row["position"],
                "servicios_observados": sum(
                    1 for service in row["services"] if service["operational_status"] == "Observado"
                ),
            }
            for row in rows
        ]
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(national["total_municipalities"], "Municipalidades", color_borde="#1A3A6B")
    with c2:
        kpi_card(f"{national['average_score'] * 100:.1f}%", "Promedio nacional", color_borde="#2196F3")
    with c3:
        predominant = max(national["distribution_by_level"], key=national["distribution_by_level"].get)
        kpi_card(predominant, "Nivel predominante", color_borde="#E87722")
    with c4:
        kpi_card(national["operational_status_distribution"].get("Observado", 0), "Servicios observados", color_borde="#DC3545")

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    chart_col, service_col = st.columns([1.1, 1])
    with chart_col:
        st.markdown("##### Distribución por nivel")
        st.plotly_chart(
            distribucion_niveles_pie(national["distribution_by_level"]),
            width="stretch",
        )
    with service_col:
        st.markdown("##### Promedio por servicio")
        service_df = pd.DataFrame(national["service_summaries"]).rename(
            columns={
                "service_name": "Servicio",
                "predominant_level": "Nivel predominante",
                "puntaje_pct": "Puntaje (%)",
            }
        )
        st.dataframe(service_df[["Servicio", "Nivel predominante", "Puntaje (%)"]], width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("##### Ranking nacional")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        selected_region = st.selectbox("Región", ["Todas"] + sorted(df["region"].dropna().unique().tolist()))
    with filter_col2:
        selected_level = st.selectbox("Nivel", ["Todos", "Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"])
    with filter_col3:
        top_n = st.slider("Top", 10, max(10, len(df)), min(20, len(df)))

    df_filtered = df.copy()
    if selected_region != "Todas":
        df_filtered = df_filtered[df_filtered["region"] == selected_region]
    if selected_level != "Todos":
        df_filtered = df_filtered[df_filtered["nivel"] == selected_level]
    df_filtered = df_filtered.sort_values("score_total", ascending=False)

    st.plotly_chart(ranking_bar_chart(df_filtered, top_n=min(top_n, len(df_filtered))), width="stretch")

    st.markdown("##### Evolución del puntaje por región")
    regional_history_df = pd.DataFrame(national["regional_history"]).rename(
        columns={
            "period_label": "Período",
            "region": "Región",
            "puntaje_pct": "Puntaje (%)",
        }
    )
    if regional_history_df.empty:
        st.info("Aún no hay suficientes períodos cargados para mostrar evolución regional.")
    else:
        st.plotly_chart(evolucion_puntaje_region(regional_history_df), width="stretch")

    st.markdown("##### Tabla completa")
    search = st.text_input("Buscar municipalidad", key="admin_dashboard_search")
    if search:
        df_filtered = df_filtered[df_filtered["municipalidad"].str.contains(search, case=False)]
    st.dataframe(
        df_filtered.rename(
            columns={
                "codigo": "Código",
                "municipalidad": "Municipalidad",
                "provincia": "Provincia",
                "region": "Región",
                "puntaje_pct": "Puntaje (%)",
                "nivel": "Nivel",
                "posicion": "Posición",
                "servicios_observados": "Servicios observados",
            }
        ),
        width="stretch",
        hide_index=True,
    )
