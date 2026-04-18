# views/admin_export.py — Exportación de reportes y publicación del ranking

import streamlit as st
import pandas as pd
import io
from components.ui import page_header, alert_box
from data.mock_data import get_ranking, get_estadisticas_nacionales

def show():
    page_header("Exportar & Reportes", "Descargue datos, genere informes y publique el ranking oficial", "📥")

    ranking = get_ranking()
    stats   = get_estadisticas_nacionales()

    tab1, tab2, tab3 = st.tabs(["📊 Exportar datos", "📄 Generar informes", "🔒 Publicación oficial"])

    # ─── TAB 1: EXPORTAR DATOS ───────────────────────────────────────────────
    with tab1:
        st.markdown("##### Exportar ranking completo")

        df = pd.DataFrame(ranking)
        df_export = df[["posicion", "municipalidad", "provincia", "region",
                        "puntaje_pct", "nivel", "estado_envio"]].copy()
        df_export.columns = ["Posición", "Municipalidad", "Provincia", "Región",
                              "Puntaje (%)", "Nivel", "Estado Formulario"]

        col1, col2 = st.columns(2)
        with col1:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar CSV completo",
                data=csv,
                file_name="IGSM_2025_ranking_completo.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col2:
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_export.to_excel(writer, index=False, sheet_name="Ranking 2025")

                    # Hoja de estadísticas
                    df_stats = pd.DataFrame([{
                        "Total municipalidades": stats["total_municipalidades"],
                        "Formularios enviados": stats["enviados"],
                        "Participación (%)": stats["pct_participacion"],
                        "Promedio nacional (%)": round(stats["promedio_nacional"] * 100, 2),
                    }])
                    df_stats.to_excel(writer, index=False, sheet_name="Estadísticas")

                    # Hoja de scores por servicio
                    from data.mock_data import get_scores_por_servicio_nacional
                    prom_serv = get_scores_por_servicio_nacional()
                    df_serv = pd.DataFrame([{"Servicio": k, "Promedio nacional (%)": round(v*100, 2)} for k, v in prom_serv.items()])
                    df_serv.to_excel(writer, index=False, sheet_name="Promedios por servicio")

                output.seek(0)
                st.download_button(
                    "📊 Descargar Excel completo",
                    data=output,
                    file_name="IGSM_2025_reporte_completo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando Excel: {e}")

        st.markdown("---")
        st.markdown("##### Vista previa de los datos")
        st.dataframe(df_export.head(20), use_container_width=True)

        st.markdown("---")
        st.markdown("##### Exportar por filtros")
        c1, c2 = st.columns(2)
        with c1:
            region_exp = st.selectbox("Exportar por región", ["Todas"] + sorted(df["region"].unique().tolist()), key="exp_reg")
        with c2:
            nivel_exp = st.selectbox("Exportar por nivel", ["Todos", "Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"], key="exp_niv")

        df_filtrado = df.copy()
        if region_exp != "Todas": df_filtrado = df_filtrado[df_filtrado["region"] == region_exp]
        if nivel_exp  != "Todos":  df_filtrado = df_filtrado[df_filtrado["nivel"]  == nivel_exp]

        csv_f = df_filtrado[["posicion", "municipalidad", "puntaje_pct", "nivel"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            f"📥 Descargar {len(df_filtrado)} municipalidades",
            data=csv_f,
            file_name=f"IGSM_2025_{region_exp}_{nivel_exp}.csv",
            mime="text/csv",
        )

    # ─── TAB 2: INFORMES ─────────────────────────────────────────────────────
    with tab2:
        st.markdown("##### Generar informe por municipalidad")
        alert_box("La generación de PDF individual requiere integración con Google Cloud. Disponible en producción.", "info", "ℹ️")

        nombres_all = [m["municipalidad"] for m in ranking]
        muni_informe = st.selectbox("Seleccione la municipalidad", nombres_all, key="muni_inf")

        data_m = next((m for m in ranking if m["municipalidad"] == muni_informe), None)
        if data_m:
            st.markdown(f"""
            <div class="sigam-card">
                <strong>{muni_informe}</strong><br>
                Puntaje: <strong>{data_m['puntaje_pct']}%</strong> ·
                Nivel: <strong>{data_m['nivel']}</strong> ·
                Posición: <strong>#{data_m['posicion']}</strong>
            </div>
            """, unsafe_allow_html=True)

            # Exportar datos del municipio como CSV
            serv = data_m.get("servicios", {})
            rows = [{"Servicio": k, "Puntaje (%)": round(v*100, 1)} for k, v in serv.items()]
            df_muni = pd.DataFrame(rows)
            csv_m = df_muni.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"📥 Descargar reporte {muni_informe} CSV",
                data=csv_m,
                file_name=f"Informe_{muni_informe.replace(' ','_')}_IGSM_2025.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("##### Informe resumen nacional")
        resumen_data = {
            "Indicador": [
                "Total municipalidades evaluadas",
                "Formularios enviados",
                "Participación (%)",
                "Promedio nacional IGSM (%)",
                "Puntaje máximo (%)",
                "Puntaje mínimo (%)",
                "Nivel predominante",
                "En nivel Inicial",
                "En nivel Básico",
                "En nivel Intermedio",
                "En nivel Avanzado",
                "En nivel Optimizando",
            ],
            "Valor 2025": [
                84, stats["enviados"], stats["pct_participacion"],
                round(stats["promedio_nacional"]*100, 2),
                round(stats["max_score"]*100, 2),
                round(stats["min_score"]*100, 2),
                "Básico (68%)",
                stats["distribucion_niveles"].get("Inicial", 0),
                stats["distribucion_niveles"].get("Básico", 0),
                stats["distribucion_niveles"].get("Intermedio", 0),
                stats["distribucion_niveles"].get("Avanzado", 0),
                stats["distribucion_niveles"].get("Optimizando", 0),
            ],
        }
        df_resumen = pd.DataFrame(resumen_data)
        st.dataframe(df_resumen.set_index("Indicador"), use_container_width=True)
        csv_res = df_resumen.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar resumen", data=csv_res, file_name="Resumen_IGSM_2025.csv", mime="text/csv")

    # ─── TAB 3: PUBLICACIÓN ──────────────────────────────────────────────────
    with tab3:
        st.markdown("##### Control de publicación del ranking oficial")
        alert_box(
            "La publicación oficial congela el ranking y lo hace visible para todas las municipalidades. "
            "Esta acción no puede deshacerse sin una nueva publicación.",
            "warning", "⚠️"
        )

        publicado = st.session_state.get("ranking_publicado", False)
        fecha_pub = st.session_state.get("fecha_publicacion", "—")

        if publicado:
            st.markdown(f"""
            <div class="alert-success">
                ✅ <strong>Ranking publicado el {fecha_pub}</strong><br>
                Las 84 municipalidades pueden consultar su posición y puntaje oficial.
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Despublicar (nueva revisión)", type="secondary"):
                st.session_state["ranking_publicado"] = False
                st.rerun()
        else:
            st.markdown("""
            <div class="alert-warning">
                ⏳ <strong>El ranking no ha sido publicado oficialmente.</strong><br>
                Las municipalidades solo pueden ver su propio progreso, no el ranking comparativo.
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### Verificación previa a la publicación")
            completados = stats["enviados"]
            total = stats["total_municipalidades"]
            pct = stats["pct_participacion"]

            st.markdown(f"""
            <div style="padding:1rem; background:#F0F4F8; border-radius:8px; margin:1rem 0">
                <div style="margin-bottom:0.5rem">
                    {completados}/{total} municipalidades han enviado su formulario ({pct}% participación)
                </div>
                <div style="background:#E8EDF4; height:10px; border-radius:5px">
                    <div style="background:#1A3A6B; width:{pct}%; height:10px; border-radius:5px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            confirmar = st.checkbox("Confirmo que he revisado todos los formularios y deseo publicar el ranking oficial 2025")

            if st.button("🔓 Publicar Ranking Oficial 2025", type="primary", disabled=not confirmar):
                from datetime import date
                st.session_state["ranking_publicado"] = True
                st.session_state["fecha_publicacion"] = date.today().strftime("%d/%m/%Y")
                st.success("🎉 Ranking publicado exitosamente. Las municipalidades ya pueden ver sus resultados comparativos.")
                st.rerun()
