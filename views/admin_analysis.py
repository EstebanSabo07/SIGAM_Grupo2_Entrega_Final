"""Advanced analytics view for the Contraloria portal."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import month_year_selector, page_header
from data.presentation_service import get_national_snapshot_view
from data.snapshot import AUDIENCE_ADMIN


def _build_analysis_frames(national: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the dataframes used by the advanced analysis tabs.

    Args:
        national: National admin snapshot view.

    Returns:
        Municipality and service analysis dataframes.
    """

    municipalities = national["municipalities"]
    municipality_rows = []
    service_rows = []
    for municipality in municipalities:
        age_values = [
            service["data_age_months"]
            for service in municipality["services"]
            if service["data_age_months"] is not None
        ]
        municipality_rows.append(
            {
                "Municipalidad": municipality["municipality"]["nombre"],
                "Región": municipality["municipality"].get("region"),
                "Provincia": municipality["municipality"].get("provincia"),
                "Promedio antigüedad (meses)": round(sum(age_values) / len(age_values), 2) if age_values else None,
                "Servicios con datos": len(age_values),
                "Puntaje (%)": municipality["puntaje_pct"],
                "Nivel": municipality["level"],
            }
        )
        for service in municipality["services"]:
            service_rows.append(
                {
                    "Municipalidad": municipality["municipality"]["nombre"],
                    "Región": municipality["municipality"].get("region"),
                    "Provincia": municipality["municipality"].get("provincia"),
                    "Servicio": service["service_name"],
                    "Eje": service["axis_name"],
                    "Puntaje (%)": round(service["score"] * 100, 2),
                    "Nivel": service["level"],
                    "Estado operativo": service["operational_status"],
                    "Antigüedad (meses)": service["data_age_months"],
                    "Fecha actualización": service["update_date"].isoformat() if service["update_date"] else None,
                }
            )

    municipality_df = pd.DataFrame(municipality_rows).sort_values(
        "Promedio antigüedad (meses)",
        ascending=False,
        na_position="last",
    )
    service_df = pd.DataFrame(service_rows)
    return municipality_df, service_df


def _render_data_freshness_tab(national: dict) -> None:
    """Render the current freshness and service detail analysis tab.

    Args:
        national: National admin snapshot view.
    """

    municipality_df, service_df = _build_analysis_frames(national)
    st.markdown("##### Promedio de antigüedad por municipalidad")
    st.dataframe(municipality_df, width="stretch", hide_index=True)

    st.markdown("##### Detalle por servicio")
    municipality_names = sorted(service_df["Municipalidad"].unique().tolist())
    selected_municipality = st.selectbox(
        "Municipalidad",
        municipality_names,
        key="admin_analysis_municipality",
    )
    detail_df = service_df[service_df["Municipalidad"] == selected_municipality].sort_values(
        ["Antigüedad (meses)", "Servicio"],
        ascending=[False, True],
        na_position="last",
    )
    service_filter = st.text_input(
        "Filtrar servicio",
        key="admin_analysis_service_filter",
        placeholder="Buscar servicio dentro de la municipalidad seleccionada",
    )
    if service_filter:
        detail_df = detail_df[
            detail_df["Servicio"].str.contains(service_filter, case=False, na=False)
            | detail_df["Eje"].str.contains(service_filter, case=False, na=False)
        ]
    st.dataframe(detail_df, width="stretch", hide_index=True)


def _render_ml_models_tab() -> None:
    """Render the placeholder tab for predictive and ML-focused modules."""

    st.markdown("##### Modelos predictivos y de clasificación")
    st.info(
        "Próximamente este espacio reunirá modelos de predicción, clasificación y detección de patrones para fortalecer el análisis del índice."
    )
    c1, c2, c3 = st.columns(3)
    cards = [
        (
            "Proyección del índice",
            "Estimar cómo podría evolucionar el nivel de madurez por municipalidad y por servicio en próximos cortes.",
        ),
        (
            "Clasificación de riesgo",
            "Priorizar municipalidades o servicios con mayor probabilidad de rezago, observación o deterioro operativo.",
        ),
        (
            "Patrones y anomalías",
            "Detectar comportamientos atípicos y señales territoriales útiles para auditoría y seguimiento estratégico.",
        ),
    ]
    for column, (title, description) in zip([c1, c2, c3], cards):
        with column:
            st.markdown(
                (
                    '<div class="mini-info-card">'
                    f'<div class="mini-info-title">{title}</div>'
                    f'<div class="mini-info-meta">{description}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def show() -> None:
    """Render the advanced analytics page."""

    page_header(
        "Análisis avanzado",
        "Panel de auditoría con análisis de vigencia y un espacio dedicado a futuros modelos predictivos sobre el índice.",
        "🔬",
    )
    snapshot = month_year_selector(AUDIENCE_ADMIN, key_prefix="admin_analysis_snapshot")
    national = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)
    tabs = st.tabs(["Vigencia y calidad de datos", "Modelos predictivos y ML"])
    with tabs[0]:
        _render_data_freshness_tab(national)
    with tabs[1]:
        _render_ml_models_tab()
