"""Municipal portal home view."""

# views/muni_home.py — Página de inicio del portal municipal

import streamlit as st
from components.ui import page_header, kpi_card, nivel_badge, alert_box, gauge_score
from components.charts import historico_lineas, comparacion_servicios_bar, radar_ejes
from data.db_layer import get_ranking

def show():
    """Render the municipal home page.

    The page reads the active municipality from Streamlit session state, shows
    submission status, score KPIs, history, service charts, and navigation to
    the IGSM form.
    """

    nombre = st.session_state.get("municipalidad", "Municipalidad")
    ranking = get_ranking()
    data = next((m for m in ranking if m["municipalidad"] == nombre), None)

    if not data:
        st.error("No se encontraron datos para esta municipalidad.")
        return

    page_header(
        f"Bienvenido, {nombre}",
        f"Período 2025 · Posición #{data['posicion']} de 84 · {data['region']}",
        "🏛️"
    )

    # ── Pasos del proceso ──────────────────────────────────────────────────────
    estado = data.get("estado_envio", "Pendiente")
    st.markdown("#### Estado del período 2025")
    col_pasos = st.columns(4)
    pasos = [
        ("✅", "Ingresaste al sistema"),
        ("📋" if estado == "Pendiente" else "✅", "Completar formulario"),
        ("📎" if estado == "Pendiente" else "✅", "Cargar evidencias"),
        ("📤" if estado == "Pendiente" else "✅", "Enviar a CGR"),
    ]
    for i, (icono, texto) in enumerate(pasos):
        with col_pasos[i]:
            completado = estado == "Enviado" or i == 0
            color = "#28A745" if completado else "#ADB5BD"
            st.markdown(f"""
            <div style="text-align:center; padding:0.8rem; background:white; border-radius:8px;
                        border:2px solid {color}; height:90px; display:flex; flex-direction:column;
                        align-items:center; justify-content:center;">
                <div style="font-size:1.4rem">{icono}</div>
                <div style="font-size:0.75rem; color:{color}; font-weight:600; margin-top:0.3rem">{texto}</div>
            </div>
            """, unsafe_allow_html=True)

    if estado == "Pendiente":
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📋  Iniciar / Continuar Formulario IGSM 2025", type="primary", use_container_width=False):
            st.session_state["page"] = "muni_form"
            st.rerun()
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        alert_box("Tu formulario del período 2025 ya fue enviado a la Contraloría. Puedes consultar tus resultados.", "success", "✅")

    st.markdown("---")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.markdown("#### Tu desempeño IGSM 2025")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(f"{data['puntaje_pct']}%", "Puntaje IGSM", color_borde="#1A3A6B")
    with c2:
        st.markdown(f"""<div class="kpi-card" style="border-top-color:#E87722">
            <div class="kpi-value">{nivel_badge(data['nivel'])}</div>
            <div class="kpi-label" style="margin-top:0.5rem">Nivel de madurez</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        kpi_card(f"#{data['posicion']}", "Posición nacional", color_borde="#20C997")
    with c4:
        # Cambio vs historial
        hist = data.get("historial", [])
        if hist:
            delta_val = data["score_total"] - hist[-1]
            delta_str = f"{'▲' if delta_val >= 0 else '▼'} {abs(delta_val*100):.1f}pts vs 2024"
            kpi_card(f"{hist[-1]*100:.1f}%", "Puntaje 2024", delta=delta_str, delta_positivo=(delta_val >= 0), color_borde="#ADB5BD")
        else:
            kpi_card("—", "Puntaje anterior")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficas ──────────────────────────────────────────────────────────────
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.markdown("##### Medidor IGSM")
        gauge_score(data["score_total"], "Puntaje IGSM 2025")

        st.markdown("##### Evolución histórica")
        hist = data.get("historial", [])
        if hist:
            historial_dict = {}
            for i, score in enumerate(hist):
                ano = str(2022 + i)
                historial_dict[ano] = score
            historial_dict["2025"] = data["score_total"]
            fig_hist = historico_lineas(historial_dict, nombre)
            st.plotly_chart(fig_hist, use_container_width=True)

    with col_der:
        st.markdown("##### Desempeño por servicio")
        servicios = data.get("servicios", {})
        if servicios:
            fig_serv = comparacion_servicios_bar(servicios)
            st.plotly_chart(fig_serv, use_container_width=True)

    # ── Etapas ────────────────────────────────────────────────────────────────
    st.markdown("##### Puntaje por etapa de gestión")
    etapas = data.get("etapas", {})
    if etapas:
        cols_e = st.columns(3)
        etapa_info = {
            "Planificación": ("📌", "50% del índice", "#1A3A6B"),
            "Ejecución":     ("⚙️",  "30% del índice", "#E87722"),
            "Evaluación":    ("📈", "20% del índice", "#20C997"),
        }
        for i, (etapa, score) in enumerate(etapas.items()):
            icono, peso, color = etapa_info.get(etapa, ("", "", "#1A3A6B"))
            with cols_e[i]:
                kpi_card(f"{score*100:.1f}%", f"{icono} {etapa}", delta=peso, delta_positivo=True, color_borde=color)
