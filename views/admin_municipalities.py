"""Municipality detail and comparison view for administrators."""

# views/admin_municipalities.py — Vista detallada por municipalidad

import streamlit as st
import pandas as pd
from components.ui import page_header, kpi_card, nivel_badge, alert_box
from components.charts import radar_ejes, historico_lineas, comparacion_servicios_bar
from data.db_layer import get_ranking, get_municipalidad_data
from data.indicators import clasificar_nivel

def show():
    """Render the administrator municipality-detail page.

    The page lets the user select one or two municipalities, then renders KPI
    cards, comparative charts, service summaries, and a CSV export in
    Streamlit.
    """

    page_header("Análisis por Municipalidad", "Consulte el detalle de cualquier municipalidad del país", "🏛️")

    ranking = get_ranking()
    df = pd.DataFrame(ranking)

    col1, col2 = st.columns([2, 1])
    with col1:
        nombres = [m["municipalidad"] for m in ranking]
        seleccionada = st.selectbox("Seleccione una municipalidad", nombres, key="admin_muni_sel")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        comparar = st.checkbox("Comparar con otra municipalidad", key="comparar_check")

    muni_sel2 = None
    if comparar:
        otros = [n for n in nombres if n != seleccionada]
        muni_sel2 = st.selectbox("Segunda municipalidad para comparar", otros, key="admin_muni_sel2")

    # Obtener datos con posición real desde el ranking ya cargado
    data = next((m for m in ranking if m["municipalidad"] == seleccionada), None)
    if not data:
        st.error("No se encontraron datos.")
        return

    data2 = next((m for m in ranking if m["municipalidad"] == muni_sel2), None) if muni_sel2 else None

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card(f"{data['puntaje_pct']}%", f"Puntaje — {seleccionada}", color_borde="#1A3A6B")
    with c2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-value" style="font-size:1.1rem">{nivel_badge(data['nivel'])}</div>
            <div class="kpi-label" style="margin-top:0.5rem">Nivel de madurez</div>
        </div>""", unsafe_allow_html=True)
    with c3: kpi_card(f"#{data['posicion']}", "Posición nacional")
    with c4: kpi_card(data["region"], "Región", color_borde="#E87722")

    if data2:
        st.markdown("##### Comparación")
        cc1, cc2, cc3 = st.columns(3)
        diff = data["score_total"] - data2["score_total"]
        with cc1: kpi_card(f"{data2['puntaje_pct']}%", f"Puntaje — {muni_sel2}", color_borde="#6B7A90")
        with cc2:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-value" style="font-size:1.1rem">{nivel_badge(data2['nivel'])}</div>
                <div class="kpi-label" style="margin-top:0.5rem">Nivel {muni_sel2}</div>
            </div>""", unsafe_allow_html=True)
        with cc3:
            color_diff = "#28A745" if diff >= 0 else "#DC3545"
            kpi_card(
                f"{'+'if diff>=0 else ''}{diff*100:.1f}pts",
                f"{seleccionada} vs {muni_sel2}",
                color_borde=color_diff
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficas ──────────────────────────────────────────────────────────────
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("##### Radar por servicio")
        servicios = data.get("servicios", {})
        nombres_cortos = {
            "Recolección, depósito y tratamiento de residuos sólidos": "Recolección",
            "Aseo de vías y sitios públicos":   "Aseo Vías",
            "Urbanismo e infraestructura":      "Urbanismo",
            "Red vial cantonal":                "Red Vial",
            "Servicios sociales y complementarios": "Ss. Sociales",
            "Servicios educativos, culturales y deportivos": "Educativos",
            "Alcantarillado pluvial":            "Alcantarillado",
            "Agua potable":                     "Agua Potable",
            "Zona Marítimo Terrestre":           "ZMT",
            "Seguridad y vigilancia":            "Seguridad",
        }
        servicios_cortos = {nombres_cortos.get(k, k[:15]): v for k, v in servicios.items()}
        if servicios_cortos:
            fig_radar = radar_ejes(servicios_cortos, seleccionada)
            if data2:
                serv2_cortos = {nombres_cortos.get(k, k[:15]): v for k, v in data2["servicios"].items()}
                # Agregar segunda línea al radar
                import plotly.graph_objects as go
                cats2 = list(serv2_cortos.keys())
                vals2 = [v * 100 for v in serv2_cortos.values()]
                vals2_c = vals2 + [vals2[0]]
                cats2_c = cats2 + [cats2[0]]
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals2_c, theta=cats2_c, fill="toself",
                    fillcolor="rgba(232,119,34,0.12)",
                    line=dict(color="#E87722", width=2),
                    name=muni_sel2,
                ))
                fig_radar.update_layout(showlegend=True)
            st.plotly_chart(fig_radar, use_container_width=True)

    with col_der:
        st.markdown("##### Evolución histórica")
        hist = data.get("historial", [])
        if hist:
            historial_dict = {str(2022 + i): s for i, s in enumerate(hist)}
            historial_dict["2025"] = data["score_total"]
            fig_hist = historico_lineas(historial_dict, seleccionada)

            if data2:
                hist2 = data2.get("historial", [])
                if hist2:
                    hist2_dict = {str(2022 + i): s for i, s in enumerate(hist2)}
                    hist2_dict["2025"] = data2["score_total"]
                    import plotly.graph_objects as go
                    anos2 = list(hist2_dict.keys())
                    vals2 = [v * 100 for v in hist2_dict.values()]
                    fig_hist.add_trace(go.Scatter(
                        x=anos2, y=vals2,
                        mode="lines+markers",
                        line=dict(color="#E87722", width=2, dash="dash"),
                        marker=dict(size=7, color="#E87722"),
                        name=muni_sel2,
                    ))
                    fig_hist.update_layout(showlegend=True)
            st.plotly_chart(fig_hist, use_container_width=True)

    # ── Detalle por servicio ──────────────────────────────────────────────────
    st.markdown("##### Comparación por servicio")
    from data.db_layer import get_scores_por_servicio_nacional
    prom_nacional = get_scores_por_servicio_nacional()
    fig_serv = comparacion_servicios_bar(servicios, prom_nacional)
    st.plotly_chart(fig_serv, use_container_width=True)

    # ── Tabla de indicadores simulada ────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### Resumen de servicios")
    rows = []
    for serv, score in servicios.items():
        nivel_s = clasificar_nivel(score)
        rows.append({
            "Servicio": serv[:50],
            "Puntaje (%)": round(score * 100, 1),
            "Nivel": nivel_s,
        })
    df_serv = pd.DataFrame(rows)
    st.dataframe(df_serv.set_index("Servicio"), use_container_width=True)

    # Exportar
    csv = df_serv.to_csv().encode("utf-8")
    st.download_button(f"📥 Descargar {seleccionada} CSV", data=csv,
                       file_name=f"IGSM_{seleccionada}_2025.csv", mime="text/csv")
