"""Reusable Streamlit UI helpers for SIGAM views."""

# components/ui.py — Componentes reutilizables de UI para SIGAM

from pathlib import Path

import streamlit as st

from data.snapshot import SnapshotContext, current_snapshot
from data.snapshot_service import resolve_snapshot_period

def load_css():
    """Load the project stylesheet into the current Streamlit page.

    The function reads ``assets/style.css`` when it exists and injects it as
    unsafe HTML, which is the Streamlit mechanism used by the app for global
    styling.
    """

    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def page_header(titulo: str, subtitulo: str = "", icono: str = ""):
    """Render a standardized page header.

    Args:
        titulo: Main title shown in the header.
        subtitulo: Optional subtitle shown below the title.
        icono: Optional icon prefix for the title.
    """

    icono_html = f"{icono} " if icono else ""
    sub_html = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(f"""
    <div class="page-header">
        <h2>{icono_html}{titulo}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def kpi_card(valor, etiqueta: str, delta: str = "", delta_positivo: bool = True, color_borde: str = "#1A3A6B"):
    """Render a KPI card.

    Args:
        valor: Value displayed as the card headline.
        etiqueta: Label describing the metric.
        delta: Optional comparison text.
        delta_positivo: Whether the delta should use the positive style.
        color_borde: Top-border color used by the card.
    """

    delta_class = "kpi-delta-pos" if delta_positivo else "kpi-delta-neg"
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color:{color_borde}">
        <div class="kpi-value">{valor}</div>
        <div class="kpi-label">{etiqueta}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def nivel_badge(nivel: str) -> str:
    """Return the HTML badge for a maturity level.

    Args:
        nivel: Maturity level label.

    Returns:
        HTML span string with the CSS class for the level.
    """

    clases = {
        "Inicial":     "nivel-inicial",
        "Básico":      "nivel-basico",
        "Intermedio":  "nivel-intermedio",
        "Avanzado":    "nivel-avanzado",
        "Optimizando": "nivel-optimizando",
    }
    clase = clases.get(nivel, "nivel-basico")
    return f'<span class="{clase}">{nivel}</span>'

def mostrar_nivel(nivel: str):
    """Render a maturity-level badge in Streamlit.

    Args:
        nivel: Maturity level label.
    """

    st.markdown(nivel_badge(nivel), unsafe_allow_html=True)

def progress_steps(pasos: list, activo: int):
    """Render a horizontal step-progress indicator.

    Args:
        pasos: Step labels in display order.
        activo: Zero-based index of the current active step.
    """

    html = '<div class="step-container">'
    for i, paso in enumerate(pasos):
        if i < activo:
            circle_class = "step-circle complete"
            label_class = "step-label"
            icon = "✓"
        elif i == activo:
            circle_class = "step-circle active"
            label_class = "step-label active"
            icon = str(i + 1)
        else:
            circle_class = "step-circle"
            label_class = "step-label"
            icon = str(i + 1)

        html += f"""
        <div class="step">
            <div class="{circle_class}">{icon}</div>
            <div class="{label_class}">{paso}</div>
        </div>"""
        if i < len(pasos) - 1:
            html += '<div style="flex:0.3;border-top:2px solid #E8EDF4;margin-top:18px;"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def alert_box(mensaje: str, tipo: str = "info", icono: str = ""):
    """Render a styled alert message.

    Args:
        mensaje: Alert body text.
        tipo: Alert type key, such as ``info``, ``success``, ``warning``, or
            ``danger``.
        icono: Optional icon prefix.
    """

    tipos = {"info": "alert-info", "success": "alert-success", "warning": "alert-warning", "danger": "alert-danger"}
    clase = tipos.get(tipo, "alert-info")
    st.markdown(f'<div class="{clase}">{icono} {mensaje}</div>', unsafe_allow_html=True)


def snapshot_context_note(selected_label: str, latest_label: str) -> None:
    """Render a subtle note describing the selected and latest real periods.

    Args:
        selected_label: User-selected snapshot label.
        latest_label: Latest real loaded period label.
    """

    st.markdown(
        (
            f'<div class="snapshot-context"><strong>Mostrando datos del corte seleccionado:</strong> '
            f"{selected_label} · <strong>Última carga real disponible:</strong> {latest_label}</div>"
        ),
        unsafe_allow_html=True,
    )

def sidebar_logo():
    """Render the CGR logo in the Streamlit sidebar."""

    logo_path = Path(__file__).parent.parent / "assets" / "logo_cgr.svg"
    if logo_path.exists():
        st.image(str(logo_path), width=120)
    st.markdown("---")

def sidebar_muni(nombre_muni: str):
    """Render the municipal portal navigation bar.

    Args:
        nombre_muni: Municipality name displayed in the navigation bar.
    """

    paginas = [
        ("🏠", "Inicio",          "muni_home"),
        ("📋", "Formulario IGSM", "muni_form"),
        ("📊", "Resultados",      "muni_results"),
    ]
    pagina_actual = st.session_state.get("page", "muni_home")

    c0, c1, c2, c3, c_out = st.columns([3, 2, 2, 2, 1])
    with c0:
        st.markdown(
            f'<div style="color:#1A3A6B;font-weight:700;padding-top:0.4rem;">🏛️ {nombre_muni}</div>',
            unsafe_allow_html=True)
    for col, (icono, nombre, pagina) in zip([c1, c2, c3], paginas):
        with col:
            tipo = "primary" if pagina_actual == pagina else "secondary"
            if st.button(f"{icono} {nombre}", key=f"nav_{pagina}",
                         width="stretch", type=tipo):
                st.session_state["page"] = pagina
                st.rerun()
    with c_out:
        if st.button("🚪", key="logout", width="stretch", help="Cerrar sesión"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.query_params.clear()
            st.rerun()
    st.markdown('<hr style="margin:0.3rem 0 1rem 0;border-color:#E8EDF4;">', unsafe_allow_html=True)


def sidebar_admin():
    """Render the Contraloria administrator navigation bar."""

    paginas = [
        ("📊", "Dashboard",        "admin_dashboard"),
        ("🏛️", "Municipalidades",  "admin_municipalities"),
        ("🔬", "Análisis Avanzado","admin_analysis"),
        ("⚖️",  "Pesos",           "admin_weights"),
        ("📥", "Exportar",         "admin_export"),
    ]
    pagina_actual = st.session_state.get("page", "admin_dashboard")

    c0, c1, c2, c3, c4, c5, c_out = st.columns([2, 2, 2, 2, 2, 2, 1])
    with c0:
        st.markdown(
            '<div style="color:#1A3A6B;font-weight:700;padding-top:0.4rem;">📋 Contraloría CGR</div>',
            unsafe_allow_html=True)
    for col, (icono, nombre, pagina) in zip([c1, c2, c3, c4, c5], paginas):
        with col:
            tipo = "primary" if pagina_actual == pagina else "secondary"
            if st.button(f"{icono} {nombre}", key=f"nav_{pagina}",
                         width="stretch", type=tipo):
                st.session_state["page"] = pagina
                st.rerun()
    with c_out:
        if st.button("🚪", key="logout_admin", width="stretch", help="Cerrar sesión"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.query_params.clear()
            st.rerun()
    st.markdown('<hr style="margin:0.3rem 0 1rem 0;border-color:#E8EDF4;">', unsafe_allow_html=True)

def gauge_score(score: float, titulo: str = "IGSM"):
    """Render a circular gauge for an IGSM score.

    Args:
        score: IGSM score in the 0-1 range.
        titulo: Gauge title.
    """

    import plotly.graph_objects as go
    from data.indicators import clasificar_nivel, COLORES_NIVEL

    nivel = clasificar_nivel(score)
    color = COLORES_NIVEL.get(nivel, "#2196F3")
    pct = round(score * 100, 1)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title={"text": titulo, "font": {"size": 16, "color": "#1A2636"}},
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#6B7A90"},
            "bar":  {"color": color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#E8EDF4",
            "steps": [
                {"range": [0, 31],  "color": "#FDE8E8"},
                {"range": [31, 56], "color": "#FEF3C7"},
                {"range": [56, 76], "color": "#DBEAFE"},
                {"range": [76, 91], "color": "#D1FAE5"},
                {"range": [91, 100],"color": "#EDE9FE"},
            ],
            "threshold": {
                "line": {"color": color, "width": 4},
                "thickness": 0.75,
                "value": pct,
            },
        },
    ))
    fig.update_layout(
        height=220,
        margin=dict(t=40, b=10, l=20, r=20),
        paper_bgcolor="white",
        font_color="#1A2636",
    )
    st.plotly_chart(fig, width="stretch")


def month_year_selector(audience: str, municipality_code: str | None = None, key_prefix: str = "snapshot") -> SnapshotContext:
    """Render and persist a month-year selector in Streamlit.

    Args:
        audience: Consumer audience.
        municipality_code: Optional municipal scope.
        key_prefix: Session-state key prefix.

    Returns:
        Selected snapshot context.
    """

    current = current_snapshot(audience, municipality_code=municipality_code)
    default_year = st.session_state.get("snapshot_year", current.year)
    default_month = st.session_state.get("snapshot_month", current.month)
    resolved = resolve_snapshot_period(
        requested_year=int(default_year),
        requested_month=int(default_month),
    )
    selected_period = resolved["selected_period"]
    available_years = resolved["available_years"]

    if not resolved["has_data"]:
        st.info("No hay períodos cargados en la base de datos. Se usa el mes actual como referencia.")

    col_year, col_month = st.columns([1, 1])
    with col_year:
        selected_year = st.selectbox(
            "Año",
            available_years,
            index=available_years.index(selected_period["year"]),
            key=f"{key_prefix}_year",
            disabled=not resolved["has_data"],
        )

    month_names = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    months = [
        {"month": item["month"], "label": month_names[item["month"]]}
        for item in resolved["available_periods"]
        if item["year"] == selected_year
    ]
    requested_month_int = int(default_month)
    selected_month_default = (
        requested_month_int
        if any(item["month"] == requested_month_int for item in months)
        else months[-1]["month"]
    )

    with col_month:
        selected_month = st.selectbox(
            "Mes",
            months,
            index=next(
                (index for index, item in enumerate(months) if item["month"] == selected_month_default),
                0,
            ),
            format_func=lambda item: item["label"],
            key=f"{key_prefix}_month",
            disabled=not resolved["has_data"],
        )["month"]

    st.session_state["snapshot_year"] = selected_year
    st.session_state["snapshot_month"] = selected_month
    if resolved["latest_real_period"] is not None:
        snapshot_context_note(
            f"{selected_year:04d}-{selected_month:02d}",
            resolved["latest_real_period"]["label"],
        )
    return SnapshotContext(
        year=selected_year,
        month=selected_month,
        audience=audience,
        municipality_code=municipality_code,
    )
