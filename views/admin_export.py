"""Export view for the Contraloria portal."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import month_year_selector, page_header
from data.presentation_service import get_municipality_snapshot_view, get_national_snapshot_view
from data.reporting_service import export_csv, export_pdf
from data.snapshot import AUDIENCE_ADMIN


def show() -> None:
    """Render the export and report page."""

    page_header(
        "Exportar y reportes",
        "Descargue datasets internos por período, municipalidad y audiencia técnica de Contraloría.",
        "📥",
    )
    snapshot = month_year_selector(AUDIENCE_ADMIN, key_prefix="admin_export_snapshot")
    national = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)

    tabs = st.tabs(["Nacional", "Municipalidad"])
    with tabs[0]:
        csv_bytes = export_csv(snapshot, AUDIENCE_ADMIN)
        pdf_bytes = export_pdf(snapshot, AUDIENCE_ADMIN)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 Descargar CSV nacional",
                data=csv_bytes,
                file_name=f"sigam_admin_nacional_{snapshot.label}.csv",
                mime="text/csv",
                width="stretch",
            )
        with c2:
            st.download_button(
                "📄 Descargar PDF nacional",
                data=pdf_bytes,
                file_name=f"sigam_admin_nacional_{snapshot.label}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        preview = pd.DataFrame(
            [
                {
                    "Municipalidad": item["municipality"]["nombre"],
                    "Provincia": item["municipality"].get("provincia"),
                    "Región": item["municipality"].get("region"),
                    "Puntaje (%)": item["puntaje_pct"],
                    "Nivel": item["level"],
                    "Posición": item["position"],
                }
                for item in national["municipalities"]
            ]
        )
        st.dataframe(preview, width="stretch", hide_index=True)

    with tabs[1]:
        municipalities = sorted(
            [(item["municipality"]["nombre"], item["municipality"]["codigo"]) for item in national["municipalities"]],
            key=lambda item: item[0],
        )
        selected = st.selectbox("Municipalidad", municipalities, format_func=lambda item: item[0], key="admin_export_muni")
        municipal_view = get_municipality_snapshot_view(selected[1], snapshot, AUDIENCE_ADMIN)
        csv_bytes = export_csv(snapshot, AUDIENCE_ADMIN, {"municipality_code": selected[1]})
        pdf_bytes = export_pdf(snapshot, AUDIENCE_ADMIN, {"municipality_code": selected[1]})
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 Descargar CSV municipal",
                data=csv_bytes,
                file_name=f"sigam_admin_{selected[1]}_{snapshot.label}.csv",
                mime="text/csv",
                width="stretch",
            )
        with c2:
            st.download_button(
                "📄 Descargar PDF municipal",
                data=pdf_bytes,
                file_name=f"sigam_admin_{selected[1]}_{snapshot.label}.pdf",
                mime="application/pdf",
                width="stretch",
            )

        service_df = pd.DataFrame(
            [
                {
                    "Servicio": service["service_name"],
                    "Puntaje (%)": round(service["score"] * 100, 2),
                    "Nivel": service["level"],
                    "Estado operativo": service["operational_status"],
                    "Fecha actualización": service["update_date"].isoformat() if service["update_date"] else None,
                }
                for service in municipal_view["services"]
            ]
        )
        st.dataframe(service_df, width="stretch", hide_index=True)
