"""Public citizen dashboard view for SIGAM."""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from components.charts import (
    comparador_servicios_nivel,
    distribucion_niveles_pie,
    historico_distribucion_niveles,
    madurez_servicios_horizontal,
    mapa_niveles_publico,
)
from components.ui import kpi_card, month_year_selector, page_header
from data.presentation_service import get_national_snapshot_view
from data.reporting_service import export_csv, export_pdf, pdf_export_status
from data.snapshot import AUDIENCE_PUBLIC
from data.text_utils import normalized_contains


CHART_HEIGHT = 360


def _img_b64(path: Path, mime: str = "image/png") -> str:
    """Encode an image file as a data URI.

    Args:
        path: Image file path.
        mime: MIME type to include in the data URI.

    Returns:
        Base64 data URI for embedding in HTML.
    """

    with open(path, "rb") as file:
        return f"data:{mime};base64,{base64.b64encode(file.read()).decode()}"


def _filter_public_rows(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter public municipality rows with tolerant text matching.

    Args:
        df: Municipality dataframe.
        query: Search query entered by the user.

    Returns:
        Filtered dataframe.
    """

    if not query:
        return df

    return df[
        df.apply(
            lambda row: normalized_contains(
                " ".join(
                    str(row[column] or "")
                    for column in ["municipalidad", "provincia", "region"]
                    if column in row
                ),
                query,
            ),
            axis=1,
        )
    ]


def _render_section_nav() -> None:
    """Render jump links for the single-page public overview."""

    st.markdown(
        """
        <div class="section-jump-nav">
            <a href="#resumen">Resumen</a>
            <a href="#territorio">Mapa territorial</a>
            <a href="#evolucion">Evolución</a>
            <a href="#comparador">Comparador</a>
            <a href="#descargas">Descargas</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_section_header(anchor: str, title: str, description: str) -> None:
    """Render a section title with an anchor for jump navigation.

    Args:
        anchor: HTML anchor id.
        title: Section title.
        description: Short supporting description.
    """

    st.markdown(
        f"""
        <div id="{anchor}" class="section-anchor"></div>
        <div class="section-block">
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show() -> None:
    """Render the public citizen-facing dashboard."""

    assets = Path(__file__).parent.parent / "assets"
    logo_cgr = assets / "logo_cgr.svg"
    logo_lead = assets / "logo_lead.png"
    cgr_src = _img_b64(logo_cgr, "image/svg+xml") if logo_cgr.exists() else ""
    lead_src = _img_b64(logo_lead, "image/png") if logo_lead.exists() else ""

    st.markdown(
        f"""
        <div class="landing-hero landing-hero-compact">
            <div class="landing-tag">SIGAM · Ciudadanía</div>
            <h1>Dashboard Público de Gestión Municipal</h1>
            <div class="landing-hero-copy">
                Consulte el nivel de madurez de las municipalidades, explore comparaciones territoriales
                y revise la evolución histórica del índice con datos públicos preparados para ciudadanía y prensa.
            </div>
            <div class="landing-hero-logos">
                <img src="{cgr_src}" alt="CGR" style="height:42px; filter:brightness(0) invert(1); opacity:0.92;">
                <div class="landing-hero-divider"></div>
                <img src="{lead_src}" alt="LEAD University" style="height:46px; filter:brightness(0) invert(1); opacity:0.92;">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page_header(
        "Consulta pública",
        "La navegación pública se limita a niveles de madurez, comparaciones no sensibles y análisis territorial e histórico.",
        "🔎",
    )
    _render_section_nav()
    snapshot = month_year_selector(AUDIENCE_PUBLIC, key_prefix="landing_snapshot")
    national = get_national_snapshot_view(snapshot, AUDIENCE_PUBLIC)

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card(national["total_municipalities"], "Municipalidades visibles", color_borde="#1A3A6B")
    with c2:
        predominant = max(national["distribution_by_level"], key=national["distribution_by_level"].get)
        kpi_card(predominant, "Nivel predominante", color_borde="#E87722")
    with c3:
        kpi_card(len(national["available_periods"]), "Períodos disponibles", color_borde="#20C997")

    st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)
    _render_section_header(
        "resumen",
        "Resumen",
        "Vea la distribución nacional del índice y ubique municipalidades con una búsqueda simple.",
    )
    chart_col, service_col = st.columns([1, 1])
    with chart_col:
        st.plotly_chart(
            distribucion_niveles_pie(national["distribution_by_level"], height=CHART_HEIGHT),
            width="stretch",
        )
    with service_col:
        st.markdown("##### Madurez por servicio")
        service_df = pd.DataFrame(national["service_summaries"])
        st.plotly_chart(
            madurez_servicios_horizontal(service_df, height=CHART_HEIGHT),
            width="stretch",
        )

    st.markdown("##### Buscar municipalidades")
    municipalities_df = pd.DataFrame(national["municipalities"])
    search = st.text_input(
        "Buscar municipalidades",
        key="landing_search",
        placeholder="Buscar municipalidad, provincia o región",
        label_visibility="collapsed",
    )
    filtered_df = _filter_public_rows(municipalities_df, search)
    st.caption(f"{len(filtered_df)} municipalidad(es) mostrada(s)")
    display_df = filtered_df.rename(
        columns={
            "municipalidad": "Municipalidad",
            "provincia": "Provincia",
            "region": "Región",
            "nivel": "Nivel",
        }
    )
    st.dataframe(display_df, width="stretch", hide_index=True)

    st.markdown("---")
    _render_section_header(
        "territorio",
        "Mapa territorial",
        "Filtre por región, provincia o nivel para explorar el panorama territorial de forma visual.",
    )
    map_df = pd.DataFrame(national["map_points"])
    map_filters = st.columns(3)
    with map_filters[0]:
        selected_region = st.selectbox(
            "Región",
            ["Todas"] + sorted(map_df["region"].dropna().unique().tolist()),
            key="public_map_region",
        )
    with map_filters[1]:
        selected_province = st.selectbox(
            "Provincia",
            ["Todas"] + sorted(map_df["provincia"].dropna().unique().tolist()),
            key="public_map_province",
        )
    with map_filters[2]:
        selected_level = st.selectbox(
            "Nivel",
            ["Todos"] + ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"],
            key="public_map_level",
        )

    filtered_map_df = map_df.copy()
    if selected_region != "Todas":
        filtered_map_df = filtered_map_df[filtered_map_df["region"] == selected_region]
    if selected_province != "Todas":
        filtered_map_df = filtered_map_df[filtered_map_df["provincia"] == selected_province]
    if selected_level != "Todos":
        filtered_map_df = filtered_map_df[filtered_map_df["nivel"] == selected_level]

    if filtered_map_df.empty:
        st.info("No hay municipalidades que coincidan con los filtros territoriales seleccionados.")
    else:
        st.plotly_chart(mapa_niveles_publico(filtered_map_df), width="stretch")
        st.dataframe(
            filtered_map_df.rename(
                columns={
                    "municipalidad": "Municipalidad",
                    "provincia": "Provincia",
                    "region": "Región",
                    "nivel": "Nivel",
                }
            )[["Municipalidad", "Provincia", "Región", "Nivel"]],
            width="stretch",
            hide_index=True,
        )

    st.markdown("---")
    _render_section_header(
        "evolucion",
        "Evolución",
        "Observe cómo cambia la distribución nacional de niveles entre períodos cargados.",
    )
    history = national["history"]
    if len(history) < 2:
        st.info("Aún no hay suficientes períodos cargados para mostrar evolución histórica pública.")
    else:
        st.plotly_chart(historico_distribucion_niveles(history), width="stretch")
        history_rows = []
        for item in history:
            history_rows.append(
                {
                    "Período": item["label"],
                    **{level: item["level_distribution"].get(level, 0) for level in national["distribution_by_level"]},
                }
            )
        st.dataframe(pd.DataFrame(history_rows), width="stretch", hide_index=True)

    st.markdown("---")
    _render_section_header(
        "comparador",
        "Comparador",
        "Compare varias municipalidades por servicio y vea su grado de madurez en un solo gráfico.",
    )
    candidates = national["comparison_candidates"]
    options = [item["municipalidad"] for item in candidates]
    selected_names = st.multiselect(
        "Seleccione municipalidades para comparar",
        options,
        default=options[:2] if len(options) >= 2 else options,
        max_selections=5,
        key="public_compare_selection",
    )
    selected_rows = [item for item in candidates if item["municipalidad"] in selected_names]
    if len(selected_rows) < 2:
        st.info("Seleccione al menos dos municipalidades para activar el comparador.")
    else:
        comparison_cards = st.columns(min(len(selected_rows), 3))
        for index, row in enumerate(selected_rows):
            with comparison_cards[index % len(comparison_cards)]:
                st.markdown(
                    f"""
                    <div class="mini-info-card">
                        <div class="mini-info-title">{row['municipalidad']}</div>
                        <div class="mini-info-meta">{row.get('provincia') or 'Sin provincia'} · {row.get('region') or 'Sin región'}</div>
                        <div class="mini-info-meta" style="margin-top:0.25rem;">Nivel actual: {row['nivel']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        service_rows = []
        for municipality in selected_rows:
            for service_name, level_name in municipality["service_levels"].items():
                service_rows.append(
                    {
                        "Municipalidad": municipality["municipalidad"],
                        "Servicio": service_name,
                        "Nivel": level_name,
                    }
                )
        service_df = pd.DataFrame(service_rows)
        st.plotly_chart(comparador_servicios_nivel(service_df), width="stretch")
        comparison_df = pd.DataFrame(selected_rows).rename(
            columns={
                "municipalidad": "Municipalidad",
                "provincia": "Provincia",
                "region": "Región",
                "nivel": "Nivel",
            }
        )
        st.dataframe(
            comparison_df[["Municipalidad", "Provincia", "Región", "Nivel"]],
            width="stretch",
            hide_index=True,
        )

    st.markdown("---")
    st.markdown('<div id="descargas"></div>', unsafe_allow_html=True)
    st.markdown("##### Descargas públicas")
    public_filters = {
        "search": search,
        "region": selected_region,
        "province": selected_province,
        "level": selected_level,
    }
    csv_bytes = export_csv(snapshot, AUDIENCE_PUBLIC)
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "📥 Descargar CSV público",
            data=csv_bytes,
            file_name=f"sigam_publico_{snapshot.label}.csv",
            mime="text/csv",
            width="stretch",
        )
    with d2:
        pdf_status = pdf_export_status()
        if pdf_status["available"]:
            try:
                pdf_bytes = export_pdf(snapshot, AUDIENCE_PUBLIC, filters=public_filters)
            except RuntimeError as exc:
                st.warning(str(exc))
            else:
                st.download_button(
                    "📄 Descargar PDF público",
                    data=pdf_bytes,
                    file_name=f"sigam_publico_{snapshot.label}.pdf",
                    mime="application/pdf",
                    width="stretch",
                )
        else:
            st.warning(
                "El PDF formal no está disponible en el entorno actual de Streamlit. "
                f"Instálelo con: `{pdf_status['recommended_install_command']}`. "
                f"Runtime activo: `{pdf_status['runtime_executable']}`."
   