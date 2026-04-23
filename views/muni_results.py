"""Municipal results view."""

# views/muni_results.py — Resultados del municipio

import streamlit as st
from components.ui import page_header, kpi_card, nivel_badge, alert_box
from components.charts import radar_ejes, historico_lineas, comparacion_servicios_bar
from data.db_layer import get_ranking
from data.indicators import clasificar_nivel

def show():
    """Render the municipal IGSM results page.

    The page reads the active municipality from Streamlit session state, shows
    summary KPIs, service detail, historical analysis, anomaly alerts, and CSV
    download controls.
    """

    nombre = st.session_state.get("municipalidad", "Municipalidad")
    ranking = get_ranking()
    data = next((m for m in ranking if m["municipalidad"] == nombre), None)

    if not data:
        st.error("No se encontraron resultados.")
        return

    page_header(f"Resultados IGSM — {nombre}", "Análisis detallado de su desempeño 2025", "📊")

    tab1, tab2, tab3 = st.tabs(["📋 Resumen General", "🔍 Detalle por Servicio", "📈 Análisis Histórico"])

    # ─── TAB 1: RESUMEN ───────────────────────────────────────────────────────
    with tab1:
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card(f"{data['puntaje_pct']}%", "Puntaje IGSM")
        with c2:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-value" style="font-size:1.2rem">{nivel_badge(data['nivel'])}</div>
                <div class="kpi-label" style="margin-top:0.5rem">Nivel de Madurez</div>
            </div>""", unsafe_allow_html=True)
        with c3: kpi_card(f"#{data['posicion']}", "Posición Nacional")
        with c4: kpi_card(data["provincia"], "Provincia", color_borde="#E87722")

        st.markdown("<br>", unsafe_allow_html=True)

        # Descripción del nivel
        nivel = data["nivel"]
        descripciones = {
            "Inicial":     ("0–31%", "#DC3545", "La municipalidad muestra una gestión incipiente, con procesos poco estandarizados y ausencia de planificación sistemática."),
            "Básico":      ("31–56%", "#FD7E14", "Existe una gestión elemental de los servicios con algunos instrumentos de planificación, aunque con importantes brechas en ejecución y evaluación."),
            "Intermedio":  ("56–76%", "#2196F3", "La municipalidad cuenta con procesos de gestión establecidos y en funcionamiento, con avances significativos en planificación."),
            "Avanzado":    ("76–91%", "#20C997", "Se observa una gestión sólida y sistemática con alta cobertura y mecanismos de evaluación activos."),
            "Optimizando": ("91–100%", "#7B2FBE", "Gestión de excelencia con mejora continua, alta cobertura y procesos optimizados en todos los servicios."),
        }
        rango, color, desc = descripciones.get(nivel, ("", "#1A3A6B", ""))
        st.markdown(f"""
        <div style="background:#FAFBFD; border:1px solid #E8EDF4; border-left:4px solid {color};
                    border-radius:8px; padding:1rem 1.3rem; margin-bottom:1rem">
            <strong style="color:{color}">{nivel}</strong>
            <span style="color:#6B7A90; font-size:0.85rem"> · Rango {rango}</span><br>
            <span style="color:#1A2636; font-size:0.9rem">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

        # Etapas
        st.markdown("##### Puntaje por etapa de gestión")
        etapas = data.get("etapas", {})
        ce1, ce2, ce3 = st.columns(3)
        etapa_info = {
            "Planificación": (ce1, "#1A3A6B", "50% del índice", "📌"),
            "Ejecución":     (ce2, "#E87722",  "30% del índice", "⚙️"),
            "Evaluación":    (ce3, "#20C997",  "20% del índice", "📈"),
        }
        for etapa, score in etapas.items():
            col, color, peso, icono = etapa_info[etapa]
            with col:
                kpi_card(f"{score*100:.1f}%", f"{icono} {etapa}", delta=peso, delta_positivo=True, color_borde=color)

        # Posición en ranking (contexto)
        st.markdown("---")
        st.markdown("##### Tu posición en el ranking nacional")
        pos = data["posicion"]
        munis_vecinas = []
        for m in ranking:
            if abs(m["posicion"] - pos) <= 3 and m["municipalidad"] != nombre:
                munis_vecinas.append(m)

        for m in sorted(munis_vecinas + [data], key=lambda x: x["posicion"]):
            es_yo = m["municipalidad"] == nombre
            bg = "#EBF5FB" if es_yo else "white"
            peso = "700" if es_yo else "400"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding:0.5rem 1rem; border:1px solid {'#2196F3' if es_yo else '#E8EDF4'};
                        border-radius:6px; margin-bottom:0.3rem; background:{bg}">
                <span style="font-weight:{peso}">#{m['posicion']} {m['municipalidad']}</span>
                <span>{nivel_badge(m['nivel'])}&nbsp;<strong>{m['puntaje_pct']}%</strong></span>
            </div>
            """, unsafe_allow_html=True)

    # ─── TAB 2: DETALLE ───────────────────────────────────────────────────────
    with tab2:
        st.markdown("##### Puntaje por servicio")
        servicios = data.get("servicios", {})

        for serv_nombre, score in servicios.items():
            nivel_s = clasificar_nivel(score)
            color_s = {
                "Inicial": "#DC3545", "Básico": "#FD7E14",
                "Intermedio": "#2196F3", "Avanzado": "#20C997", "Optimizando": "#7B2FBE"
            }.get(nivel_s, "#1A3A6B")

            with st.expander(f"{serv_nombre}  ·  {score*100:.0f}%  ·  {nivel_s}"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    pct = score * 100
                    st.markdown(f"""
                    <div style="background:#F0F4F8; border-radius:6px; height:12px; margin:0.5rem 0">
                        <div style="background:{color_s}; width:{pct}%; height:12px; border-radius:6px"></div>
                    </div>
                    <span style="color:{color_s}; font-weight:600">{pct:.1f}%</span>
                    &nbsp;·&nbsp;{nivel_badge(nivel_s)}
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(nivel_badge(nivel_s), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Comparación por servicio vs promedio nacional")
        from data.db_layer import get_scores_por_servicio_nacional
        prom_nacional = get_scores_por_servicio_nacional()
        fig = comparacion_servicios_bar(servicios, prom_nacional)
        st.plotly_chart(fig, use_container_width=True)

    # ─── TAB 3: HISTÓRICO ────────────────────────────────────────────────────
    with tab3:
        hist = data.get("historial", [])
        if hist:
            historial_dict = {str(2022 + i): s for i, s in enumerate(hist)}
            historial_dict["2025"] = data["score_total"]

            st.markdown("##### Evolución histórica del IGSM")
            fig_hist = historico_lineas(historial_dict, nombre)
            st.plotly_chart(fig_hist, use_container_width=True)

            # Tabla histórica
            st.markdown("##### Detalle por período")
            for ano, score in historial_dict.items():
                nivel_h = clasificar_nivel(score)
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:0.5rem 1rem;
                            border:1px solid #E8EDF4; border-radius:6px; margin-bottom:0.3rem; background:white">
                    <strong>{ano}</strong>
                    <span>{nivel_badge(nivel_h)}&nbsp;<strong>{score*100:.1f}%</strong></span>
                </div>
                """, unsafe_allow_html=True)

            # Análisis de anomalías
            from data.calculation import detectar_anomalia_historica
            anos_ordenados = list(historial_dict.values())
            anomalia = detectar_anomalia_historica(data["score_total"], anos_ordenados[:-1])
            if anomalia["es_anomalia"]:
                alert_box(anomalia["mensaje"], "warning", "⚠️")
            else:
                alert_box(anomalia["mensaje"], "success", "✅")
        else:
            alert_box("No hay datos históricos disponibles para esta municipalidad.", "info", "ℹ️")

    # ── Botón descarga ────────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.button("📥 Descargar reporte PDF", use_container_width=True, help="Disponible cuando se integre el backend")
    with col2:
        import pandas as pd
        df_export = pd.DataFrame([{
            "Municipalidad": data["municipalidad"],
            "Puntaje": data["puntaje_pct"],
            "Nivel": data["nivel"],
            "Posición": data["posicion"],
            **{f"Servicio_{k[:20]}": round(v*100, 1) for k, v in data["servicios"].items()},
        }])
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("📊 Descargar datos CSV", data=csv, file_name=f"IGSM_{nombre}_2025.csv",
                           mime="text/csv", use_container_width=True)
