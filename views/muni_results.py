"""Municipal results view."""

from __future__ import annotations

from collections import Counter
from html import escape

import pandas as pd
import streamlit as st

from components.charts import (
    distribucion_niveles_pie,
    historico_niveles_linea,
    madurez_servicios_horizontal,
)
from components.ui import kpi_card, month_year_selector, nivel_badge, page_header
from data.presentation_service import get_municipality_snapshot_view
from data.snapshot import AUDIENCE_MUNICIPAL


LEVEL_ORDER = ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]
LABEL_DESCRIPTIONS = [
    ("Necesitan actualización", "Datos viejos o incompletos que deben atenderse primero."),
    ("Inicial", "Servicios en madurez inicial."),
    ("Básico", "Servicios con avances base."),
    ("Intermedio", "Servicios funcionales con margen de mejora."),
    ("Avanzado", "Servicios fuertes que conviene sostener."),
    ("Optimizando", "Servicios destacados que deben mantenerse."),
]


def _normalize_priority_label(service: dict) -> str:
    """Return the public-facing priority label for a municipal service.

    Args:
        service: Municipal service row.

    Returns:
        Label used in the priority grid.
    """

    return "Necesitan actualización" if service["needs_update"] else service["level"]


def _build_service_level_distribution(services: list[dict]) -> dict[str, int]:
    """Build the municipal level distribution used by the donut chart.

    Args:
        services: Municipal services currently visible in the results view.

    Returns:
        Count of services per maturity level.
    """

    counts = Counter(service["level"] for service in services)
    return {level: counts[level] for level in LEVEL_ORDER if counts.get(level, 0) > 0}


def _build_service_maturity_frame(services: list[dict]) -> pd.DataFrame:
    """Build the municipal service dataframe for the maturity bar chart.

    Args:
        services: Municipal services currently visible in the results view.

    Returns:
        Dataframe aligned with ``madurez_servicios_horizontal`` expectations.
    """

    level_index = {level: index for index, level in enumerate(LEVEL_ORDER, start=1)}
    rows = [
        {
            "service_name": service["service_name"],
            "predominant_level": service["level"],
            "maturity_index": level_index.get(service["level"], 1),
            "maturity_label": service["level"],
        }
        for service in services
    ]
    return pd.DataFrame(rows)


def _render_priority_legend() -> None:
    """Render the compact legend for the municipal priority grid."""

    items = [
        """
        <span class="service-legend-item">
            <span class="service-pill service-pill-urgent">Necesitan actualización</span>
            Datos viejos o incompletos que deben atenderse primero.
        </span>
        """
    ]
    for label, description in LABEL_DESCRIPTIONS[1:]:
        items.append(
            f"""
            <span class="service-legend-item">
                {nivel_badge(label)}
                {escape(description)}
            </span>
            """
        )
    st.markdown(
        f'<div class="service-grid-legend service-grid-legend-wide">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def _render_priority_grid(services: list[dict]) -> None:
    """Render the municipal priority services as a simple card grid.

    Args:
        services: Priority-ordered services with UI labels.
    """

    if not services:
        st.info("No hay servicios disponibles para priorizar.")
        return

    columns = st.columns(3)
    for index, service in enumerate(services):
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="priority-grid-card">
                    <div class="priority-grid-label">{escape(service['display_label'])}</div>
                    <div class="priority-grid-title">{escape(service['service_name'])}</div>
                    <div class="priority-grid-meta">
                        {service['service_progress_pct']:.0f}% completo ·
                        {service['data_age_months'] if service['data_age_months'] is not None else '—'} mes(es)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_ranking_context(title: str, description: str, rows: list[dict]) -> None:
    """Render a compact ranking list highlighting the current municipality.

    Args:
        title: Ranking scope title.
        description: Short description of the ranking scope.
        rows: Ranking rows centered on the current municipality.
    """

    st.markdown(
        f"""
        <div class="ranking-list-card">
            <div class="service-status-title">{escape(title)}</div>
            <div class="service-status-meta">{escape(description)}</div>
        """,
        unsafe_allow_html=True,
    )
    if not rows:
        st.markdown('<div class="kanban-empty">No hay ranking disponible.</div></div>', unsafe_allow_html=True)
        return

    for row in rows:
        current_class = " ranking-current" if row["is_current"] else ""
        st.markdown(
            f"""
            <div class="ranking-row{current_class}">
                <div class="ranking-position">#{row['position']}</div>
                <div class="ranking-name">{escape(row['municipality_name'])}</div>
                <div class="ranking-level">{escape(row['level'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def show() -> None:
    """Render the municipality positioning and prioritization dashboard."""

    municipality_code = st.session_state.get("municipalidad_codigo") or st.session_state.get("muni_codigo")
    municipality_name = st.session_state.get("municipalidad", "Municipalidad")
    if not municipality_code:
        st.error("No se encontró el código de la municipalidad en la sesión.")
        return

    page_header(
        f"Resultados — {municipality_name}",
        "Revise su posición en los rankings y vea qué servicios deben mejorarse o actualizarse primero.",
        "📊",
    )
    snapshot = month_year_selector(
        AUDIENCE_MUNICIPAL,
        municipality_code=municipality_code,
        key_prefix="muni_results_snapshot",
    )
    view = get_municipality_snapshot_view(municipality_code, snapshot, AUDIENCE_MUNICIPAL)
    benchmark = view["benchmark_summary"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(view["level"], "Nivel vigente", color_borde="#1A3A6B")
    with c2:
        kpi_card(
            f"{benchmark['position_national']}/{benchmark['total_national']}" if benchmark["position_national"] else "—",
            "Ranking nacional",
            color_borde="#20C997",
        )
    with c3:
        kpi_card(
            f"{benchmark['position_province']}/{benchmark['total_province']}" if benchmark["position_province"] else "—",
            "Ranking provincial",
            color_borde="#E87722",
        )
    with c4:
        kpi_card(
            f"{benchmark['position_region']}/{benchmark['total_region']}" if benchmark["position_region"] else "—",
            "Ranking regional",
            color_borde="#6B7A90",
        )

    st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)
    st.markdown("##### Cómo va la municipalidad")
    rank_cols = st.columns(3)
    rank_cards = [
        (
            "Nacional",
            benchmark["reference_level_national"],
            benchmark["position_national"],
            benchmark["total_national"],
        ),
        (
            benchmark["province_name"] or "Provincia",
            benchmark["reference_level_province"],
            benchmark["position_province"],
            benchmark["total_province"],
        ),
        (
            benchmark["region_name"] or "Región",
            benchmark["reference_level_region"],
            benchmark["position_region"],
            benchmark["total_region"],
        ),
    ]
    for column, (label, reference_level, position, total) in zip(rank_cols, rank_cards):
        with column:
            st.markdown(
                f"""
                <div class="service-status-card service-status-card-compact">
                    <div class="service-status-title">{escape(label)}</div>
                    <div class="service-status-meta">Referencia más común: {escape(reference_level)}</div>
                    <div class="service-recommendation">
                        Posición actual: <strong>{f"{position}/{total}" if position else "Sin dato"}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("##### Resumen por servicios")
    summary_cols = st.columns([1, 1])
    service_distribution = _build_service_level_distribution(view["services"])
    service_maturity_df = _build_service_maturity_frame(view["services"])
    with summary_cols[0]:
        st.plotly_chart(
            distribucion_niveles_pie(service_distribution, height=360),
            width="stretch",
        )
    with summary_cols[1]:
        st.plotly_chart(
            madurez_servicios_horizontal(service_maturity_df, height=360),
            width="stretch",
        )

    st.markdown("##### Su posición en la lista")
    ranking_cols = st.columns(3)
    ranking_views = [
        (
            "Ranking nacional",
            "Su municipalidad aparece resaltada dentro de la lista nacional.",
            benchmark["national_ranking"],
        ),
        (
            f"Ranking provincial — {benchmark['province_name'] or 'Provincia'}",
            "Comparación con municipalidades de su misma provincia.",
            benchmark["province_ranking"],
        ),
        (
            f"Ranking regional — {benchmark['region_name'] or 'Región'}",
            "Comparación con municipalidades de su misma región.",
            benchmark["regional_ranking"],
        ),
    ]
    for column, (title, description, rows) in zip(ranking_cols, ranking_views):
        with column:
            _render_ranking_context(title, description, rows)

    st.markdown("##### Qué servicios conviene atender")
    _render_priority_legend()
    priority_services = []
    label_order = {label: index for index, (label, _) in enumerate(LABEL_DESCRIPTIONS)}
    for service in view["priority_services"]:
        display_label = _normalize_priority_label(service)
        priority_services.append({**service, "display_label": display_label})
    priority_services.sort(
        key=lambda item: (
            label_order.get(item["display_label"], 99),
            -item["priority_score"],
            item["service_name"],
        )
    )
    _render_priority_grid(priority_services)

    st.markdown("##### Evolución del nivel")
    history = view["history"]
    if len(history) < 2:
        st.info("Aún no hay suficientes períodos cargados para mostrar evolución municipal.")
    else:
        history_df = pd.DataFrame(history).rename(columns={"label": "Período", "level": "Nivel"})
        st.plotly_chart(historico_niveles_linea(history_df), width="stretch")
