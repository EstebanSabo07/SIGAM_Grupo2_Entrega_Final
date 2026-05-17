"""Municipality detail and comparison view for administrators."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.charts import comparador_madurez_servicios_heatmap
from components.ui import month_year_selector, page_header
from data.presentation_service import get_admin_municipality_comparison_view, get_national_snapshot_view
from data.snapshot import AUDIENCE_ADMIN


def show() -> None:
    """Render the administrator municipality comparison page."""

    page_header(
        "Municipalidades",
        "Compare varias municipalidades, revise su madurez por servicio y audite el estado de actualización.",
        "🏛️",
    )
    snapshot = month_year_selector(AUDIENCE_ADMIN, key_prefix="admin_muni_snapshot")
    national = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)
    municipalities = sorted(
        [(item["municipality"]["nombre"], item["municipality"]["codigo"]) for item in national["municipalities"]],
        key=lambda item: item[0],
    )
    options_by_name = {name: code for name, code in municipalities}
    default_names = [name for name, _ in municipalities[:2]]
    selected_names = st.multiselect(
        "Municipalidades a comparar",
        [name for name, _ in municipalities],
        default=default_names,
        max_selections=5,
        placeholder="Agregue una o varias municipalidades",
        key="admin_muni_selection",
    )

    if not selected_names:
        st.info("Seleccione al menos una municipalidad para activar la comparativa.")
        return

    comparison = get_admin_municipality_comparison_view(
        snapshot,
        [options_by_name[name] for name in selected_names],
    )

    selected_df = pd.DataFrame(comparison["selected_municipalities"]).rename(
        columns={
            "municipalidad": "Municipalidad",
            "provincia": "Provincia",
            "region": "Región",
            "puntaje_pct": "Puntaje (%)",
            "nivel": "Nivel",
            "posicion": "Posición nacional",
        }
    )
    st.markdown("##### Municipalidades seleccionadas")
    st.dataframe(selected_df, width="stretch", hide_index=True)

    st.markdown("##### Comparación rápida de madurez por servicio")
    heatmap_df = pd.DataFrame(comparison["service_heatmap_rows"])
    if heatmap_df.empty:
        st.info("No hay servicios comparables para las municipalidades seleccionadas.")
    else:
        st.plotly_chart(comparador_madurez_servicios_heatmap(heatmap_df), width="stretch")

    st.markdown("##### Puntaje por eje y servicio")
    score_df = pd.DataFrame(comparison["service_score_table"])
    st.dataframe(score_df, width="stretch", hide_index=True)

    st.markdown("##### Cantidad de servicios por estado de actualización")
    status_df = pd.DataFrame(comparison["update_status_counts"])
    st.dataframe(status_df, width="stretch", hide_index=True)
