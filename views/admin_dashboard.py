"""National dashboard view for the Contraloria portal."""

# views/admin_dashboard.py — Dashboard nacional de la Contraloría

import streamlit as st
import pandas as pd
from components.ui import page_header, kpi_card, nivel_badge
from components.charts import (
    ranking_bar_chart, distribucion_niveles_pie,
    comparacion_servicios_bar, heatmap_region_servicio, scatter_dispersion
)
from data.db_layer import get_ranking, get_estadisticas_nacionales, get_scores_por_servicio_nacional, get_historial_nacional

def show():
    """Render the national IGSM dashboard.

    The page loads ranking and national statistics, renders KPI cards, charts,
    filters, a complete ranking table, and a CSV download button in Streamlit.
    """

    page_header("Dashboard Nacional IGSM 2025", "Contraloría General de la República · Visión general del sector municipal", "📊")

    ranking = get_ranking()
    stats   = get_estadisticas_nacionales()
    df      = pd.DataFrame(ranking)

    # ── KPIs globales ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card(stats["total_municipalidades"], "Municipalidades", color_borde="#1A3A6B")
    with c2: kpi_card(stats["enviados"], "Formularios enviados", delta=f"{stats['pct_participacion']}% participación", delta_positivo=True, color_borde="#28A745")
    with c3: kpi_card(stats["pendientes"], "Pendientes", color_borde="#DC3545")
    with c4: kpi_card(f"{stats['promedio_nacional']*100:.1f}%", "Promedio nacional", color_borde="#2196F3")
    with c5:
        nivel_pred = max(stats["distribucion_niveles"], key=stats["distribucion_niveles"].get)
        kpi_card(nivel_pred, "Nivel predominante", color_borde="#FD7E14")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Distribución de niveles ──────────────────────────────────────────────
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.markdown("##### Distribución por nivel de madurez")
        fig_pie = distribucion_niveles_pie(stats["distribucion_niveles"])
        st.plotly_chart(fig_pie, use_container_width=True)

        # Tabla resumen de niveles
        orden = ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]
        dist  = stats["distribucion_niveles"]
        for nivel in orden:
            n = dist.get(nivel, 0)
            pct = round(n / 84 * 100, 1)
            color = {"Inicial": "#DC3545", "Básico": "#FD7E14", "Intermedio": "#2196F3",
                     "Avanzado": "#20C997", "Optimizando": "#7B2FBE"}.get(nivel, "#1A3A6B")
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding:0.4rem 0.8rem; margin-bottom:0.2rem; border-radius:6px; background:#FAFBFD">
                <span style="color:{color}; font-weight:600">{nivel}</span>
                <span><strong>{n}</strong> municipalidades <span style="color:#6B7A90">({pct}%)</span></span>
            </div>
            """, unsafe_allow_html=True)

    with col_der:
        st.markdown("##### Promedio por servicio (nacional)")
        prom_servicios = get_scores_por_servicio_nacional()
        nombres_cortos = {
            "Recolección, depósito y tratamiento de residuos sólidos": "Recolección Residuos",
            "Aseo de vías y sitios públicos":                          "Aseo de Vías",
            "Urbanismo e infraestructura":                             "Urbanismo",
            "Red vial cantonal":                                       "Red Vial",
            "Servicios sociales y complementarios":                    "Servicios Sociales",
            "Servicios educativos, culturales y deportivos":           "Educativos/Culturales",
        }
        for serv, score in list(prom_servicios.items())[:6]:
            nombre_c = nombres_cortos.get(serv, serv[:30])
            nivel_s  = _nivel(score)
            color_s  = {"Inicial": "#DC3545", "Básico": "#FD7E14", "Intermedio": "#2196F3",
                        "Avanzado": "#20C997", "Optimizando": "#7B2FBE"}.get(nivel_s, "#1A3A6B")
            pct = round(score * 100, 1)
            st.markdown(f"""
            <div style="margin-bottom:0.5rem">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:2px">
                    <span>{nombre_c}</span><strong style="color:{color_s}">{pct}%</strong>
                </div>
                <div style="background:#E8EDF4; border-radius:4px; height:8px">
                    <div style="background:{color_s}; width:{pct}%; height:8px; border-radius:4px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Ranking con filtros ───────────────────────────────────────────────────
    st.markdown("##### Ranking nacional")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        regiones   = ["Todas"] + sorted(df["region"].unique().tolist())
        filtro_reg = st.selectbox("Región", regiones, key="f_region")
    with col_f2:
        provincias  = ["Todas"] + sorted(df["provincia"].unique().tolist())
        filtro_prov = st.selectbox("Provincia", provincias, key="f_prov")
    with col_f3:
        niveles_f  = ["Todos"] + ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]
        filtro_niv = st.selectbox("Nivel", niveles_f, key="f_nivel")
    with col_f4:
        top_n = st.slider("Mostrar top", 10, 84, 20, key="f_top")

    df_f = df.copy()
    if filtro_reg  != "Todas":  df_f = df_f[df_f["region"]   == filtro_reg]
    if filtro_prov != "Todas":  df_f = df_f[df_f["provincia"] == filtro_prov]
    if filtro_niv  != "Todos":  df_f = df_f[df_f["nivel"]     == filtro_niv]

    fig_ranking = ranking_bar_chart(df_f, top_n=min(top_n, len(df_f)))
    st.plotly_chart(fig_ranking, use_container_width=True)

    st.markdown("---")

    # ── Heatmap región × servicio ────────────────────────────────────────────
    st.markdown("##### Puntaje promedio por región y servicio")
    fig_heat = heatmap_region_servicio(df)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # ── Tabla completa ────────────────────────────────────────────────────────
    st.markdown("##### Tabla completa")
    buscar = st.text_input("🔍 Buscar municipalidad", key="buscar_tabla")
    df_tabla = df_f.copy()
    if buscar:
        df_tabla = df_tabla[df_tabla["municipalidad"].str.contains(buscar, case=False)]

    df_display = df_tabla[["posicion", "municipalidad", "provincia", "region", "puntaje_pct", "nivel", "estado_envio"]].copy()
    df_display.columns = ["#", "Municipalidad", "Provincia", "Región", "Puntaje (%)", "Nivel", "Estado"]
    st.dataframe(df_display.set_index("#"), use_container_width=True, height=350)

    # Exportar
    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar tabla CSV", data=csv, file_name="IGSM_2025_ranking.csv",
                       mime="text/csv")


def _nivel(score: float) -> str:
    """Classify a score into a maturity level.

    Args:
        score: IGSM score in the 0-1 range.

    Returns:
        Maturity level label.
    """

    from data.indicators import clasificar_nivel
    return clasificar_nivel(score)
