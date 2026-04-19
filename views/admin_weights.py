"""Stage-weight management view for the Contraloria portal."""

# views/admin_weights.py — Gestión de pesos del índice IGSM

import streamlit as st
import pandas as pd
from components.ui import page_header, alert_box
from data.indicators import PESOS_ETAPA
from data.db_layer import get_weights, save_weights

def show():
    """Render the IGSM weight management page.

    The page loads effective weights into Streamlit session state, provides
    controls for saving new stage weights, simulates ranking impact, and renders
    the local version history.
    """

    page_header("Gestión de Pesos", "Configure los pesos del índice IGSM y simule el impacto en el ranking", "⚖️")

    # Estado de pesos en sesión — carga pesos vigentes desde BD
    if "pesos_etapa" not in st.session_state:
        try:
            st.session_state["pesos_etapa"] = get_weights()
        except Exception:
            st.session_state["pesos_etapa"] = dict(PESOS_ETAPA)
    if "historial_pesos" not in st.session_state:
        st.session_state["historial_pesos"] = [
            {"version": "v1.0", "fecha": "01/01/2023", "Planificación": 0.50, "Ejecución": 0.30, "Evaluación": 0.20, "descripcion": "Pesos originales CGR"},
            {"version": "v2.0", "fecha": "01/01/2024", "Planificación": 0.50, "Ejecución": 0.30, "Evaluación": 0.20, "descripcion": "Sin cambios"},
            {"version": "v3.0", "fecha": "01/01/2025", "Planificación": 0.50, "Ejecución": 0.30, "Evaluación": 0.20, "descripcion": "Pesos vigentes 2025"},
        ]

    tab1, tab2, tab3 = st.tabs(["⚖️ Pesos por Etapa", "🔮 Simulador", "📋 Historial de versiones"])

    # ─── TAB 1: PESOS ────────────────────────────────────────────────────────
    with tab1:
        st.markdown("##### Pesos actuales por etapa de gestión")
        alert_box(
            "Los pesos determinan cuánto contribuye cada etapa al puntaje IGSM. "
            "La suma de los tres pesos debe ser igual a 100%.",
            "info", "ℹ️"
        )

        pesos = st.session_state["pesos_etapa"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""<div class="sigam-card" style="text-align:center; border-top:3px solid #1A3A6B">
                <div style="font-size:1.5rem">📌</div>
                <div style="font-size:1.3rem; font-weight:700; color:#1A3A6B">50%</div>
                <div style="font-size:0.8rem; color:#6B7A90">PLANIFICACIÓN</div>
                <div style="font-size:0.75rem; margin-top:0.3rem">Instrumento normativo, plan de gestión, diagnóstico</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""<div class="sigam-card" style="text-align:center; border-top:3px solid #E87722">
                <div style="font-size:1.5rem">⚙️</div>
                <div style="font-size:1.3rem; font-weight:700; color:#E87722">30%</div>
                <div style="font-size:0.8rem; color:#6B7A90">EJECUCIÓN</div>
                <div style="font-size:0.75rem; margin-top:0.3rem">Cobertura, recursos ejecutados, operación del servicio</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown("""<div class="sigam-card" style="text-align:center; border-top:3px solid #20C997">
                <div style="font-size:1.5rem">📈</div>
                <div style="font-size:1.3rem; font-weight:700; color:#20C997">20%</div>
                <div style="font-size:0.8rem; color:#6B7A90">EVALUACIÓN</div>
                <div style="font-size:0.75rem; margin-top:0.3rem">Satisfacción, plan de mejora, implementación</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### Modificar pesos (requiere justificación)")
        alert_box("Cualquier cambio en los pesos quedará registrado en el historial de versiones y será auditado.", "warning", "⚠️")

        p_plan = st.slider("Planificación (%)", 20, 70, int(pesos["Planificación"] * 100), 5, key="w_plan")
        p_ejec = st.slider("Ejecución (%)",     10, 50, int(pesos["Ejecución"]    * 100), 5, key="w_ejec")
        p_eval = st.slider("Evaluación (%)",    10, 40, int(pesos["Evaluación"]   * 100), 5, key="w_eval")

        suma = p_plan + p_ejec + p_eval
        if suma != 100:
            alert_box(f"La suma actual es {suma}%. Debe ser exactamente 100%.", "danger", "❌")
        else:
            alert_box(f"✅ Suma correcta: {suma}%", "success")

        justificacion = st.text_area(
            "Justificación técnica del cambio",
            placeholder="Explique el motivo del ajuste de pesos...",
            key="w_justif",
        )

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("💾 Guardar nueva versión", type="primary", use_container_width=True, disabled=(suma != 100)):
                if not justificacion.strip():
                    alert_box("Debe ingresar una justificación.", "danger", "❌")
                else:
                    nuevos = {
                        "Planificación": p_plan / 100,
                        "Ejecución":     p_ejec / 100,
                        "Evaluación":    p_eval / 100,
                    }
                    # Persistir en BD
                    try:
                        from datetime import date
                        save_weights(nuevos["Planificación"], nuevos["Ejecución"], nuevos["Evaluación"])
                    except Exception as e:
                        st.warning(f"No se pudo guardar en BD: {e}")
                    st.session_state["pesos_etapa"] = nuevos
                    version_nueva = f"v{len(st.session_state['historial_pesos']) + 1}.0"
                    from datetime import date
                    st.session_state["historial_pesos"].append({
                        "version": version_nueva,
                        "fecha": date.today().strftime("%d/%m/%Y"),
                        "Planificación": p_plan / 100,
                        "Ejecución":     p_ejec / 100,
                        "Evaluación":    p_eval / 100,
                        "descripcion": justificacion[:80],
                    })
                    st.success(f"✅ Pesos actualizados. Versión {version_nueva} guardada en la base de datos.")
        with col_g2:
            if st.button("🔄 Restaurar pesos originales CGR", use_container_width=True):
                st.session_state["pesos_etapa"] = dict(PESOS_ETAPA)
                st.success("Pesos restaurados a valores originales (50/30/20).")

    # ─── TAB 2: SIMULADOR ────────────────────────────────────────────────────
    with tab2:
        st.markdown("##### Simulador de impacto en el ranking")
        st.caption("Vea cómo cambiaría el ranking nacional si se modificaran los pesos de las etapas.")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1: sim_plan = st.number_input("Plan (%)", 20, 70, 50, 5, key="sim_plan")
        with col_s2: sim_ejec = st.number_input("Ejec (%)", 10, 50, 30, 5, key="sim_ejec")
        with col_s3: sim_eval = st.number_input("Eval (%)", 10, 40, 20, 5, key="sim_eval")

        sim_suma = sim_plan + sim_ejec + sim_eval
        if sim_suma != 100:
            alert_box(f"Suma: {sim_suma}% (debe ser 100%)", "danger", "❌")
        else:
            from data.db_layer import get_ranking
            ranking = get_ranking()

            # Recalcular con nuevos pesos
            pesos_sim = {"Planificación": sim_plan/100, "Ejecución": sim_ejec/100, "Evaluación": sim_eval/100}

            resultados_sim = []
            for m in ranking:
                etapas = m.get("etapas", {})
                score_sim = sum(etapas.get(et, 0) * p for et, p in pesos_sim.items())
                resultados_sim.append({
                    "municipalidad": m["municipalidad"],
                    "score_original": m["score_total"],
                    "score_simulado": round(score_sim, 4),
                    "posicion_original": m["posicion"],
                })

            resultados_sim.sort(key=lambda x: x["score_simulado"], reverse=True)
            for i, r in enumerate(resultados_sim):
                r["posicion_simulada"] = i + 1
                r["cambio"] = r["posicion_original"] - r["posicion_simulada"]

            df_sim = pd.DataFrame(resultados_sim[:20])
            df_sim["Variación"] = df_sim["cambio"].apply(
                lambda x: f"▲ {x}" if x > 0 else (f"▼ {abs(x)}" if x < 0 else "—")
            )
            df_sim["Puntaje orig."] = (df_sim["score_original"] * 100).round(1)
            df_sim["Puntaje sim."]  = (df_sim["score_simulado"]  * 100).round(1)

            st.dataframe(
                df_sim[["municipalidad", "posicion_original", "posicion_simulada", "Variación", "Puntaje orig.", "Puntaje sim."]].rename(columns={
                    "municipalidad": "Municipalidad",
                    "posicion_original": "Pos. actual",
                    "posicion_simulada": "Pos. simulada",
                }),
                use_container_width=True, height=380
            )

    # ─── TAB 3: HISTORIAL ────────────────────────────────────────────────────
    with tab3:
        st.markdown("##### Historial de versiones de pesos")
        historial = st.session_state["historial_pesos"]

        for v in reversed(historial):
            vigente = v == historial[-1]
            bg = "#EBF5FB" if vigente else "white"
            badge = '<span style="background:#1A3A6B;color:white;padding:2px 8px;border-radius:10px;font-size:0.75rem">VIGENTE</span>' if vigente else ""
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid #E8EDF4; border-radius:8px;
                        padding:1rem 1.3rem; margin-bottom:0.5rem">
                <div style="display:flex; justify-content:space-between; align-items:center">
                    <strong>{v['version']}</strong> {badge}
                    <span style="color:#6B7A90; font-size:0.85rem">{v['fecha']}</span>
                </div>
                <div style="color:#4A5568; font-size:0.85rem; margin:0.3rem 0">
                    Plan: <strong>{int(v['Planificación']*100)}%</strong> ·
                    Ejec: <strong>{int(v['Ejecución']*100)}%</strong> ·
                    Eval: <strong>{int(v['Evaluación']*100)}%</strong>
                </div>
                <div style="color:#6B7A90; font-size:0.8rem; font-style:italic">{v['descripcion']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Exportar historial
        df_hist = pd.DataFrame(historial)
        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar historial CSV", data=csv,
                           file_name="historial_pesos_IGSM.csv", mime="text/csv")
