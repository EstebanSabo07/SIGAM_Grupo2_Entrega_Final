"""Advanced analytics view for the Contraloria portal."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import month_year_selector, page_header
from data.presentation_service import get_national_snapshot_view
from data.snapshot import AUDIENCE_ADMIN


def show() -> None:
    """Render the advanced analytics page."""

    page_header(
        "Análisis avanzado",
        "Panel de auditoría para identificar qué tan antiguos son los datos por municipalidad y por servicio.",
        "🔬",
    )
    snapshot = month_year_selector(AUDIENCE_ADMIN, key_prefix="admin_analysis_snapshot")
    national = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)
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
                "Servicios con dato": len(age_values),
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
