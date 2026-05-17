"""Municipal portal home view."""

from __future__ import annotations

from html import escape

import streamlit as st

from components.ui import kpi_card, month_year_selector, page_header
from data.presentation_service import get_municipality_snapshot_view
from data.reporting_service import active_runtime_executable, export_csv, export_pdf, pdf_export_available
from data.snapshot import AUDIENCE_MUNICIPAL


STATUS_ORDER = {"Urgente": 0, "Próximo a vencer": 1, "Al día": 2}


def _pill_class(status: str) -> str:
    """Return the CSS class for a freshness pill.

    Args:
        status: Freshness status label.

    Returns:
        CSS class name.
    """

    if status == "Al día":
        return "service-pill service-pill-ok"
    if status == "Próximo a vencer":
        return "service-pill service-pill-soon"
    return "service-pill service-pill-urgent"


def _open_service_form(service_code: str) -> None:
    """Open the municipal form focused on a specific service.

    Args:
        service_code: Target service code.
    """

    st.session_state["form_current_service"] = service_code
    st.session_state["form_pending_service"] = None
    st.session_state["page"] = "muni_form"
    st.rerun()


def _render_service_legend() -> None:
    """Render the compact legend shown above the municipal service grid."""

    st.markdown(
        """
        <div class="service-grid-legend">
            <span class="service-legend-item">
                <span class="service-pill service-pill-urgent">Urgente</span>
                Datos viejos o incompletos.
            </span>
            <span class="service-legend-item">
                <span class="service-pill service-pill-soon">Próximo a vencer</span>
                Requiere revisión pronta.
            </span>
            <span class="service-legend-item">
                <span class="service-pill service-pill-ok">Al día</span>
                Información vigente.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_service_grid(services: list[dict]) -> None:
    """Render the clickable municipal service grid ordered by urgency.

    Args:
        services: Municipal services already enriched for the UI.
    """

    if not services:
        st.info("No hay servicios disponibles para mostrar.")
        return

    ordered_services = sorted(
        services,
        key=lambda item: (
            STATUS_ORDER.get(item["freshness_status"], 99),
            -item["priority_score"],
            item["service_name"],
        ),
    )
    columns = st.columns(3)
    for index, service in enumerate(ordered_services):
        progress_width = min(max(service["service_progress_pct"], 0), 100)
        status_class = _pill_class(service["freshness_status"])
        age_label = service["data_age_months"] if service["data_age_months"] is not None else "—"
        update_date = service["update_date"] or "Sin registros"
        with columns[index % 3]:
            st.markdown('<div class="service-grid-hitbox">', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="service-grid-card">
                    <div class="service-grid-card-top">
                        <div class="service-grid-title">{escape(service['service_name'])}</div>
                        <span class="{status_class}">{escape(service['freshness_status'])}</span>
                    </div>
                    <div class="service-grid-meta">
                        <span>{service['service_progress_pct']:.0f}% completo</span>
                        <span>{age_label} mes(es)</span>
                        <span>{escape(update_date)}</span>
                    </div>
                    <div class="service-progress-track">
                        <div class="service-progress-fill" style="width:{progress_width:.0f}%"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                " ",
                key=f"service_grid::{service['service_code']}",
                width="stretch",
                help=f"Abrir {service['service_name']}",
            ):
                _open_service_form(service["service_code"])
            st.markdown("</div>", unsafe_allow_html=True)


def show() -> None:
    """Render the municipal home page."""

    municipality_code = st.session_state.get("municipalidad_codigo") or st.session_state.get("muni_codigo")
    municipality_name = st.session_state.get("municipalidad", "Municipalidad")
    if not municipality_code:
        st.error("No se encontró el código de la municipalidad en la sesión.")
        return

    page_header(
        f"Portal municipal — {municipality_name}",
        "Revise la vigencia y completitud de cada servicio, y entre directo al formulario para actualizarlo.",
        "🏛️",
    )
    snapshot = month_year_selector(
        AUDIENCE_MUNICIPAL,
        municipality_code=municipality_code,
        key_prefix="muni_home_snapshot",
    )
    view = get_municipality_snapshot_view(municipality_code, snapshot, AUDIENCE_MUNICIPAL)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(view["level"], "Nivel vigente", color_borde="#1A3A6B")
    with c2:
        kpi_card(f"{view['completion_pct']:.1f}%", "Completitud global", color_borde="#20C997")
    with c3:
        kpi_card(view["services_up_to_date"], "Servicios al día", color_borde="#20C997")
    with c4:
        kpi_card(view["services_urgent"], "Servicios urgentes", color_borde="#DC3545")

    st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)
    st.markdown("##### Estado de actualización de servicios")
    st.markdown('<div class="section-gap-sm"></div>', unsafe_allow_html=True)
    _render_service_legend()
    _render_service_grid(view["priority_services"])

    st.markdown("---")
    st.markdown("##### Descargas")
    csv_bytes = export_csv(snapshot, AUDIENCE_MUNICIPAL, {"municipality_code": municipality_code})
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "📥 Descargar CSV municipal",
            data=csv_bytes,
            file_name=f"sigam_municipal_{municipality_code}_{snapshot.label}.csv",
            mime="text/csv",
            width="stretch",
        )
    with d2:
        if pdf_export_available():
            try:
                pdf_bytes = export_pdf(snapshot, AUDIENCE_MUNICIPAL, {"municipality_code": municipality_code})
            except RuntimeError as exc:
                st.warning(str(exc))
            else:
                st.download_button(
                    "📄 Descargar PDF municipal",
                    data=pdf_bytes,
                    file_name=f"sigam_municipal_{municipality_code}_{snapshot.label}.pdf",
                    mime="application/pdf",
                    width="stretch",
                )
        else:
            st.warning(
                "El PDF formal no está disponible en el entorno actual de Streamlit. "
                f"Instale `reportlab` en ese intérprete para habilitar esta descarga. "
                f"Runtime activo: `{active_runtime_executable()}`."
            )
